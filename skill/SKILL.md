# /deep-insights

Generate a comprehensive analysis of all your Claude Code sessions with Opus-quality faceting.

Replaces the native `/insights` command with full-coverage analysis: every session preprocessed locally (zero token cost), analyzed with Opus, and rendered as a self-contained HTML report.

---

## Prerequisites Check

Before starting, verify:

1. **Python 3.8+** is available:
   ```bash
   python3 --version
   ```
   If not found, inform the user: "Python 3.8+ is required. Install it from python.org or via your package manager."

2. **Scripts are installed** at `~/.claude/deep-insights-scripts/`:
   - Check for `preprocess.py` and `report.py`
   - If not found, inform the user:
     ```
     Deep Insights scripts not found. Install them:
       git clone https://github.com/zaronian/claude-deep-insights.git
       cd claude-deep-insights
       ./install.sh
     ```

3. **Output directory** exists: `~/.claude/usage-data/deep-insights/`
   - Create it if it doesn't exist: `mkdir -p ~/.claude/usage-data/deep-insights/`

---

## Step 1: Run Preprocessing

Run the preprocessing script to extract structured summaries from all session JSONL files:

```bash
python3 ~/.claude/deep-insights-scripts/preprocess.py --output-dir ~/.claude/usage-data/deep-insights/
```

Report to the user:
- Number of sessions found
- Number newly processed vs. skipped (already cached)
- Total data size and compression ratio

If **zero sessions found**, tell the user: "No Claude Code sessions found. Have you used Claude Code? Sessions are stored in `~/.claude/projects/`." and stop.

---

## Step 2: Create Batch Files

Read the manifest and split sessions into batches for parallel analysis.

1. Read `~/.claude/usage-data/deep-insights/session_manifest.json`
2. Determine batch count using this auto-scaling logic:
   - total_sessions <= 20: 1 batch
   - total_sessions <= 50: 2 batches
   - total_sessions <= 100: 3 batches
   - total_sessions <= 170: 5 batches
   - total_sessions <= 300: 8 batches
   - total_sessions > 300: ceil(total_sessions / 40) batches, max 10

3. Read all session summary files from `~/.claude/usage-data/deep-insights/session_summaries/`
4. Split them evenly across batches
5. Write each batch as a JSON array to `~/.claude/usage-data/deep-insights/batch_{N}.json`

Tell the user: "Split {total} sessions into {N} batches of ~{size} sessions each. Spawning {N} Opus analysis agents..."

---

## Step 3: Spawn Analysis Agents

Launch parallel Opus sub-agents to analyze each batch. Use the Task tool with `model: "opus"` for each batch.

**IMPORTANT:** Launch ALL batch agents in a single message (parallel execution). Do NOT wait for one to finish before starting the next.

For each batch, spawn a Task agent with this prompt:

```
You are analyzing Claude Code session summaries to produce structured "facets" —
qualitative assessments of what happened in each session.

Read the batch file at: {batch_file_path}

This contains {batch_size} preprocessed session summaries. For EACH session,
produce a facet JSON object with this exact structure:

{
  "session_id": "uuid-string",
  "underlying_goal": "1-2 sentence description of what the user was fundamentally trying to accomplish",
  "goal_categories": {
    "category_name": count
  },
  "outcome": "fully_achieved | mostly_achieved | partially_achieved | not_achieved | abandoned | unclear",
  "user_satisfaction_counts": {
    "satisfied": 0,
    "dissatisfied": 0,
    "frustrated": 0,
    "neutral": 0
  },
  "claude_helpfulness": "essential | very_helpful | moderately_helpful | slightly_helpful | unhelpful",
  "session_type": "single_task | multi_task | iterative_refinement | exploration | q_and_a | research | debugging | design_planning",
  "friction_counts": {
    "friction_type": count
  },
  "friction_detail": "Specific description of what went wrong, if anything. Empty string if no friction.",
  "primary_success": "What went well — e.g. thorough_research, efficient_implementation, clear_explanation, good_debugging, good_planning. Empty string if nothing notable.",
  "brief_summary": "2-3 sentence summary of the session including what was attempted and the result."
}

Goal categories to use: bug_fix, feature_implementation, testing_implementation,
refactoring, research, data_fix_revert, deployment, documentation, configuration,
exploration, code_review, design_planning

Friction types to use: wrong_approach, buggy_code, misunderstood_request,
hallucinated_info, slow_iteration, over_engineering, missed_context,
fabricated_data, tool_failure, context_overflow

When analyzing each session:
- Look at the conversation_flow to understand what the user asked and how Claude responded
- Look at tool_usage and tool_details to understand what actions were taken
- Look at stats (message counts, token usage, subagent counts) for session complexity
- Infer satisfaction from user tone, corrections, redirections, or praise
- A session with many user corrections = friction; a session that flows smoothly = satisfied
- Sessions where Claude spawned many subagents may indicate productive parallelization
  or runaway complexity
- If the conversation is very short (1-2 exchanges) it may be a quick question or
  abandoned session
- For friction_counts and goal_categories, only include keys with non-zero values
- For user_satisfaction_counts, always include all four keys

Write ALL {batch_size} facet objects as a JSON array to: {output_path}

IMPORTANT: The output MUST be valid JSON. Write the file using the Write tool.
Do not include any text outside the JSON array in the file.
```

Set `subagent_type: "general-purpose"` and `model: "opus"` for each Task.

---

## Step 4: Validate and Combine Facets

After all agents complete:

1. Read each `facets_batch_{N}.json` file
2. Validate:
   - Each file contains valid JSON (an array of objects)
   - Each facet has required fields: session_id, outcome, claude_helpfulness, brief_summary
   - All session_ids from the manifest are accounted for
3. If a batch file is missing or invalid:
   - Log which batch failed
   - Note the missing session_ids
   - Continue with available data
4. Combine all facets into a single array
5. Write to `~/.claude/usage-data/deep-insights/all_facets.json`

Report: "{total} facets collected. {missing} sessions missing (if any)."

---

## Step 5: Generate Report

Run the report generator:

```bash
python3 ~/.claude/deep-insights-scripts/report.py --input-dir ~/.claude/usage-data/deep-insights/ --open
```

---

## Step 6: Present Summary

After the report opens, present headline metrics to the user:

```
Deep Insights Report Generated
═══════════════════════════════
Sessions analyzed:    {N}
Goals achieved:       {X}% (fully + mostly)
Claude helpful+:      {X}% (essential + very helpful)
Frictionless:         {X}% of sessions
Top friction types:   {type1} ({n1}), {type2} ({n2}), {type3} ({n3})

Report: ~/.claude/usage-data/deep-insights/report.html
```

Offer: "Want me to dig into any specific section — friction patterns, best sessions, or recommendations?"

---

## Error Handling

### Sub-agent fails to produce valid JSON
- Retry the failed batch once with the same prompt
- If still fails, log the error and skip that batch
- Note in the output: "Warning: Batch {N} failed. {X} sessions not analyzed."

### Rate limiting during analysis
- If a sub-agent reports rate limiting, inform the user:
  "Hit rate limits during analysis. Options: (1) wait 5 minutes and retry, (2) reduce batch count, (3) switch to Sonnet for analysis (faster, slightly less nuanced)."

### Preprocessing finds 0 sessions
- Print: "No Claude Code sessions found in ~/.claude/projects/. Have you used Claude Code?"
- Stop gracefully.

### Report generation fails
- Print the error from report.py
- Suggest: "Try running report.py manually to debug: `python3 ~/.claude/deep-insights-scripts/report.py --input-dir ~/.claude/usage-data/deep-insights/`"
