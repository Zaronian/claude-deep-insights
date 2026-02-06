#!/usr/bin/env python3
"""
Claude Deep Insights — Stage 1: Preprocessing

Reads all Claude Code session JSONL files, extracts structured summaries,
and saves them as compact JSON files for efficient LLM-based facet analysis.

Usage:
    python3 preprocess.py [--output-dir DIR] [--session-dir DIR] [--force]

No external dependencies — stdlib only.
"""

import argparse
import json
import os
import glob
import sys
from datetime import datetime
from collections import Counter

# Configuration constants (PRD Section 5.1)
MAX_TEXT_PER_MESSAGE = 500       # chars per user/assistant message
MAX_TOOL_RESULT_CHARS = 200      # chars per tool result
MAX_CONVERSATION_EXCHANGES = 40  # max user+assistant pairs
MAX_TOOL_DETAILS = 30            # max tool calls with full details
MAX_FILES_TOUCHED = 30           # max file paths to record

DEFAULT_SESSION_DIR = os.path.expanduser('~/.claude/projects/')
DEFAULT_OUTPUT_DIR = './deep-insights-output/'


def extract_text_from_content(content, max_chars=MAX_TEXT_PER_MESSAGE):
    """Extract readable text from message content blocks."""
    if isinstance(content, str):
        return content[:max_chars]

    texts = []
    if isinstance(content, list):
        for block in content:
            if isinstance(block, str):
                texts.append(block[:max_chars])
            elif isinstance(block, dict):
                if block.get('type') == 'text':
                    texts.append(str(block.get('text', ''))[:max_chars])
                elif block.get('type') == 'thinking':
                    thinking = str(block.get('thinking', ''))
                    if thinking:
                        texts.append(f"[thinking: {thinking[:150]}...]")
    return ' '.join(texts)


def extract_tool_calls(content):
    """Extract tool call info from assistant content blocks."""
    tools = []
    if not isinstance(content, list):
        return tools

    for block in content:
        if isinstance(block, dict) and block.get('type') == 'tool_use':
            tool_info = {
                'name': block.get('name', 'unknown'),
            }
            inp = block.get('input', {})
            name = tool_info['name']

            if name in ('Read', 'Glob', 'Grep'):
                tool_info['target'] = str(
                    inp.get('file_path', inp.get('pattern', inp.get('path', '')))
                )[:MAX_TOOL_RESULT_CHARS]
            elif name in ('Edit', 'Write'):
                tool_info['target'] = str(inp.get('file_path', ''))[:MAX_TOOL_RESULT_CHARS]
            elif name == 'Bash':
                tool_info['command'] = str(inp.get('command', ''))[:MAX_TOOL_RESULT_CHARS]
            elif name == 'WebSearch':
                tool_info['query'] = str(inp.get('query', ''))[:MAX_TOOL_RESULT_CHARS]
            elif name == 'WebFetch':
                tool_info['url'] = str(inp.get('url', ''))[:MAX_TOOL_RESULT_CHARS]
            elif name == 'Task':
                tool_info['description'] = str(inp.get('description', ''))[:100]
                tool_info['subagent_type'] = str(inp.get('subagent_type', ''))
            elif name in ('TaskCreate', 'TaskUpdate'):
                tool_info['subject'] = str(
                    inp.get('subject', inp.get('status', ''))
                )[:100]

            tools.append(tool_info)
    return tools


def process_session(jsonl_path):
    """Process a single session JSONL file into a compact summary."""
    session_id = os.path.basename(jsonl_path).replace('.jsonl', '')
    project_dir = os.path.basename(os.path.dirname(jsonl_path))

    timestamps = []
    user_messages = []
    assistant_texts = []
    tool_usage = Counter()
    tool_details = []
    files_touched = set()
    models_used = set()
    total_input_tokens = 0
    total_output_tokens = 0
    has_summary = False
    git_branch = None
    lines_processed = 0
    lines_skipped = 0

    with open(jsonl_path, 'r', errors='replace') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                lines_skipped += 1
                continue

            lines_processed += 1
            msg_type = obj.get('type')
            timestamp = obj.get('timestamp')
            if timestamp:
                timestamps.append(timestamp)

            if not git_branch and obj.get('gitBranch'):
                git_branch = obj['gitBranch']

            if msg_type == 'summary':
                has_summary = True
                summary_text = obj.get('summary', '')
                if summary_text:
                    assistant_texts.append(
                        f"[CONTEXT SUMMARY: {str(summary_text)[:1000]}]"
                    )

            elif msg_type == 'user':
                content = obj.get('message', {}).get('content', '')
                text = extract_text_from_content(content, MAX_TEXT_PER_MESSAGE)
                if text.strip():
                    user_messages.append(text)

            elif msg_type == 'assistant':
                msg = obj.get('message', {})
                content = msg.get('content', [])

                model = msg.get('model', '')
                if model:
                    models_used.add(model)

                usage = msg.get('usage', {})
                total_input_tokens += usage.get('input_tokens', 0)
                total_output_tokens += usage.get('output_tokens', 0)

                text = extract_text_from_content(content, MAX_TEXT_PER_MESSAGE)
                if text.strip():
                    assistant_texts.append(text)

                tools = extract_tool_calls(content)
                for tool in tools:
                    tool_usage[tool['name']] += 1
                    target = tool.get('target', '')
                    if target and '/' in target:
                        files_touched.add(target)
                    if len(tool_details) < MAX_TOOL_DETAILS:
                        tool_details.append(tool)

    # Build compressed conversation flow
    conversation_flow = []
    user_idx = 0
    asst_idx = 0
    exchange_count = 0

    while user_idx < len(user_messages) and exchange_count < MAX_CONVERSATION_EXCHANGES:
        conversation_flow.append({
            "role": "user",
            "text": user_messages[user_idx]
        })
        user_idx += 1

        if asst_idx < len(assistant_texts):
            conversation_flow.append({
                "role": "assistant",
                "text": assistant_texts[asst_idx]
            })
            asst_idx += 1

        exchange_count += 1

    start_time = min(timestamps) if timestamps else None
    end_time = max(timestamps) if timestamps else None

    # Check for subagents
    session_dir = os.path.join(os.path.dirname(jsonl_path), session_id)
    subagent_dir = os.path.join(session_dir, 'subagents')
    subagent_count = 0
    if os.path.isdir(subagent_dir):
        subagent_count = len(glob.glob(os.path.join(subagent_dir, '*.jsonl')))

    summary = {
        "session_id": session_id,
        "project": project_dir,
        "start_time": start_time,
        "end_time": end_time,
        "git_branch": git_branch,
        "models_used": sorted(models_used),
        "stats": {
            "user_messages": len(user_messages),
            "assistant_responses": len(assistant_texts),
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "subagent_count": subagent_count,
            "had_context_compression": has_summary,
        },
        "tool_usage": dict(tool_usage.most_common()),
        "tool_details": tool_details,
        "files_touched": sorted(files_touched)[:MAX_FILES_TOUCHED],
        "conversation_flow": conversation_flow,
    }

    return summary, lines_skipped


def discover_sessions(session_dir):
    """Find all parent session JSONL files (not in subagents directories)."""
    parent_sessions = []
    for jsonl in glob.glob(os.path.join(session_dir, '**', '*.jsonl'), recursive=True):
        if '/subagents/' not in jsonl:
            parent_sessions.append(jsonl)
    parent_sessions.sort()
    return parent_sessions


def main():
    parser = argparse.ArgumentParser(
        description='Claude Deep Insights — Preprocess session data',
        epilog='Part of claude-deep-insights: https://github.com/zaronian/claude-deep-insights'
    )
    parser.add_argument(
        '--output-dir',
        default=DEFAULT_OUTPUT_DIR,
        help=f'Output directory for summaries (default: {DEFAULT_OUTPUT_DIR})'
    )
    parser.add_argument(
        '--session-dir',
        default=DEFAULT_SESSION_DIR,
        help=f'Claude Code session directory (default: {DEFAULT_SESSION_DIR})'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Re-process all sessions even if summaries already exist'
    )
    args = parser.parse_args()

    session_dir = os.path.expanduser(args.session_dir)
    output_dir = os.path.expanduser(args.output_dir)
    summaries_dir = os.path.join(output_dir, 'session_summaries')

    # Validate session directory
    if not os.path.isdir(session_dir):
        print(f"No Claude Code sessions found at {session_dir}")
        print("Have you used Claude Code? Sessions are stored in ~/.claude/projects/")
        sys.exit(0)

    # Create output directories
    os.makedirs(summaries_dir, exist_ok=True)

    # Discover sessions
    parent_sessions = discover_sessions(session_dir)

    if not parent_sessions:
        print(f"No session JSONL files found in {session_dir}")
        print("Have you used Claude Code? Sessions are stored in ~/.claude/projects/")
        sys.exit(0)

    # Compute total raw size
    total_raw_size = sum(os.path.getsize(p) for p in parent_sessions)
    project_dirs = set(os.path.basename(os.path.dirname(p)) for p in parent_sessions)

    print(f"Claude Deep Insights — Preprocessing")
    print(f"  Session directory: {session_dir}")
    print(f"  Output directory:  {output_dir}")
    print(f"  Projects found:    {len(project_dirs)}")
    print(f"  Sessions found:    {len(parent_sessions)}")
    print(f"  Raw data size:     {total_raw_size / (1024 * 1024):.1f} MB")
    print()

    # Process sessions
    all_summaries = []
    new_count = 0
    skipped_count = 0
    error_count = 0
    total_lines_skipped = 0

    for i, jsonl_path in enumerate(parent_sessions):
        session_id = os.path.basename(jsonl_path).replace('.jsonl', '')
        size_mb = os.path.getsize(jsonl_path) / (1024 * 1024)

        # Incremental mode: skip if summary already exists
        summary_path = os.path.join(summaries_dir, f"{session_id}.json")
        if not args.force and os.path.exists(summary_path):
            try:
                with open(summary_path) as f:
                    existing = json.load(f)
                all_summaries.append(existing)
                skipped_count += 1
                continue
            except (json.JSONDecodeError, KeyError):
                pass  # Re-process if existing summary is corrupt

        print(
            f"  [{i + 1}/{len(parent_sessions)}] "
            f"Processing {session_id[:12]}... ({size_mb:.1f}MB)",
            end='',
            flush=True
        )

        try:
            summary, lines_skipped = process_session(jsonl_path)
            total_lines_skipped += lines_skipped
            all_summaries.append(summary)
            new_count += 1

            with open(summary_path, 'w') as f:
                json.dump(summary, f, indent=2)

            out_size = os.path.getsize(summary_path)
            warn = f" ({lines_skipped} bad lines)" if lines_skipped else ""
            print(f" -> {out_size / 1024:.1f}KB{warn}")

        except Exception as e:
            error_count += 1
            print(f" ERROR: {e}")

    # Build and save manifest
    manifest = {
        "total_sessions": len(all_summaries),
        "generated_at": datetime.now().isoformat(),
        "sessions": [
            {
                "session_id": s["session_id"],
                "project": s["project"],
                "start_time": s["start_time"],
                "end_time": s["end_time"],
                "user_messages": s["stats"]["user_messages"],
                "models": s["models_used"],
                "subagent_count": s["stats"]["subagent_count"],
                "top_tools": list(s["tool_usage"].keys())[:5],
            }
            for s in all_summaries
        ]
    }

    manifest_path = os.path.join(output_dir, 'session_manifest.json')
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    # Print summary
    total_summary_size = sum(
        os.path.getsize(os.path.join(summaries_dir, f"{s['session_id']}.json"))
        for s in all_summaries
        if os.path.exists(os.path.join(summaries_dir, f"{s['session_id']}.json"))
    )

    print()
    print("=" * 50)
    print(f"  Preprocessing complete")
    print(f"  New:       {new_count} sessions processed")
    if skipped_count:
        print(f"  Skipped:   {skipped_count} sessions (already processed, use --force to redo)")
    if error_count:
        print(f"  Errors:    {error_count} sessions failed")
    if total_lines_skipped:
        print(f"  Bad lines: {total_lines_skipped} JSONL lines skipped (invalid JSON)")
    print(f"  Total:     {len(all_summaries)} sessions in manifest")
    print(f"  Raw size:  {total_raw_size / (1024 * 1024):.1f} MB")
    print(f"  Summary:   {total_summary_size / 1024:.1f} KB "
          f"({total_summary_size / (1024 * 1024):.2f} MB)")
    if total_raw_size > 0:
        compression = (1 - total_summary_size / total_raw_size) * 100
        print(f"  Reduction: {compression:.1f}%")
    print(f"  Output:    {output_dir}")
    print("=" * 50)


if __name__ == '__main__':
    main()
