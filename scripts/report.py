#!/usr/bin/env python3
"""
Claude Deep Insights — Stage 3: Report Generation

Reads facets and session manifest, computes aggregates, and generates
a self-contained HTML report.

Usage:
    python3 report.py [--input-dir DIR] [--output FILE] [--open] [--no-comparison]

No external dependencies — stdlib only.
"""

import argparse
import json
import os
import platform
import subprocess
import sys
from collections import Counter
from datetime import datetime

# Add parent directory to path so we can import templates
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from templates.report_template import render, _escape

DEFAULT_INPUT_DIR = './deep-insights-output/'
NATIVE_FACETS_DIR = os.path.expanduser('~/.claude/usage-data/facets/')

# Color mappings
OUTCOME_COLORS = {
    'fully_achieved': '#3fb950',
    'mostly_achieved': '#58a6ff',
    'partially_achieved': '#d29922',
    'not_achieved': '#f85149',
    'abandoned': '#8b949e',
    'unclear': '#8b949e',
}

HELPFULNESS_COLORS = {
    'essential': '#3fb950',
    'very_helpful': '#58a6ff',
    'moderately_helpful': '#d29922',
    'slightly_helpful': '#db6d28',
    'unhelpful': '#f85149',
}

SATISFACTION_COLORS = {
    'satisfied': '#3fb950',
    'neutral': '#58a6ff',
    'frustrated': '#db6d28',
    'dissatisfied': '#f85149',
}

FRICTION_COLORS = {
    'tool_failure': '#f85149',
    'missed_context': '#f85149',
    'slow_iteration': '#db6d28',
    'context_overflow': '#db6d28',
    'wrong_approach': '#d29922',
    'buggy_code': '#d29922',
    'misunderstood_request': '#8b949e',
    'hallucinated_info': '#8b949e',
    'fabricated_data': '#8b949e',
    'over_engineering': '#8b949e',
}

OUTCOME_LABELS = {
    'fully_achieved': 'Fully Achieved',
    'mostly_achieved': 'Mostly Achieved',
    'partially_achieved': 'Partially Achieved',
    'not_achieved': 'Not Achieved',
    'abandoned': 'Abandoned',
    'unclear': 'Unclear',
}

HELPFULNESS_LABELS = {
    'essential': 'Essential',
    'very_helpful': 'Very Helpful',
    'moderately_helpful': 'Moderately Helpful',
    'slightly_helpful': 'Slightly Helpful',
    'unhelpful': 'Unhelpful',
}

SATISFACTION_LABELS = {
    'satisfied': 'Satisfied',
    'neutral': 'Neutral',
    'frustrated': 'Frustrated',
    'dissatisfied': 'Dissatisfied',
}

FRICTION_LABELS = {
    'tool_failure': 'Tool Failure',
    'missed_context': 'Missed Context',
    'slow_iteration': 'Slow Iteration',
    'context_overflow': 'Context Overflow',
    'wrong_approach': 'Wrong Approach',
    'buggy_code': 'Buggy Code',
    'misunderstood_request': 'Misunderstood Request',
    'hallucinated_info': 'Hallucinated Info',
    'fabricated_data': 'Fabricated Data',
    'over_engineering': 'Over-Engineering',
}

GOAL_LABELS = {
    'bug_fix': 'Bug Fix',
    'feature_implementation': 'Feature Implementation',
    'testing_implementation': 'Testing',
    'refactoring': 'Refactoring',
    'research': 'Research',
    'data_fix_revert': 'Data Fix / Revert',
    'deployment': 'Deployment',
    'documentation': 'Documentation',
    'configuration': 'Configuration',
    'exploration': 'Exploration',
    'code_review': 'Code Review',
    'design_planning': 'Design & Planning',
}

SESSION_TYPE_LABELS = {
    'single_task': 'Single Task',
    'multi_task': 'Multi-Task',
    'iterative_refinement': 'Iterative Refinement',
    'exploration': 'Exploration',
    'q_and_a': 'Q&A',
    'research': 'Research',
    'debugging': 'Debugging',
    'design_planning': 'Design Planning',
}

SUCCESS_LABELS = {
    'thorough_research': 'Thorough Research',
    'efficient_implementation': 'Efficient Implementation',
    'clear_explanation': 'Clear Explanation',
    'good_debugging': 'Good Debugging',
    'good_planning': 'Good Planning',
}


def aggregate_dict_field(facets, field):
    """Aggregate a dict field across all facets."""
    result = Counter()
    for facet in facets:
        val = facet.get(field, {})
        if isinstance(val, dict):
            for k, v in val.items():
                if isinstance(v, (int, float)):
                    result[k] += v
    return result


def load_facets(input_dir):
    """Load all_facets.json."""
    path = os.path.join(input_dir, 'all_facets.json')
    if not os.path.exists(path):
        print(f"Error: {path} not found.")
        print("Run the analysis stage first to generate facets.")
        sys.exit(1)
    with open(path) as f:
        return json.load(f)


def load_manifest(input_dir):
    """Load session_manifest.json."""
    path = os.path.join(input_dir, 'session_manifest.json')
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def compute_date_range(facets, manifest):
    """Compute the date range string from manifest or facets."""
    dates = []
    if manifest:
        for s in manifest.get('sessions', []):
            if s.get('start_time'):
                dates.append(s['start_time'])
            if s.get('end_time'):
                dates.append(s['end_time'])

    if not dates:
        return "Date range unknown"

    try:
        sorted_dates = sorted(dates)
        start = datetime.fromisoformat(sorted_dates[0].replace('Z', '+00:00'))
        end = datetime.fromisoformat(sorted_dates[-1].replace('Z', '+00:00'))
        return f"{start.strftime('%b %d')} \u2013 {end.strftime('%b %d, %Y')}"
    except (ValueError, TypeError):
        return "Date range unknown"


def format_date_from_facet(facet, manifest):
    """Get a human-readable date for a facet from the manifest."""
    if not manifest:
        return "Unknown date"
    for s in manifest.get('sessions', []):
        if s['session_id'] == facet.get('session_id'):
            ts = s.get('start_time')
            if ts:
                try:
                    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    return dt.strftime('%b %d')
                except (ValueError, TypeError):
                    pass
    return "Unknown date"


def generate_friction_insight(friction_types, total_friction, friction_count, total_sessions, top_friction_sessions):
    """Auto-generate the friction key insight text."""
    parts = []

    if not friction_types:
        return '<p>No friction detected across any sessions. This is excellent.</p>'

    # Top friction concentration
    if top_friction_sessions:
        top5_total = sum(s['friction_total'] for s in top_friction_sessions[:5])
        if total_friction > 0:
            parts.append(
                f'<p><strong>Friction concentrates in a few sessions.</strong> '
                f'The top {min(5, len(top_friction_sessions))} highest-friction sessions account for '
                f'{top5_total} of {total_friction} events ({top5_total*100//total_friction}%).</p>'
            )

    # Top friction type analysis
    sorted_friction = sorted(friction_types, key=lambda x: x[1], reverse=True)
    if sorted_friction:
        top = sorted_friction[0]
        parts.append(
            f'<p><strong>{top[0]} is the top friction type ({top[1]} events).</strong></p>'
        )

    # Context-related friction
    context_friction = sum(
        v for label, v, _ in friction_types
        if 'context' in label.lower()
    )
    if context_friction > 0:
        parts.append(
            f'<p><strong>Context-related friction ({context_friction} events)</strong> '
            f'is addressable with session management practices like /compact and session handoffs.</p>'
        )

    frictionless = total_sessions - friction_count
    parts.append(
        f'<p>{frictionless} of {total_sessions} sessions ({frictionless*100//total_sessions}%) '
        f'had zero friction.</p>'
    )

    return '\n'.join(parts)


def generate_excels_text(primary_successes, goal_categories, total_sessions):
    """Auto-generate 'Where Claude Excels' text."""
    parts = []
    if primary_successes:
        top3 = primary_successes[:3]
        for label, count in top3:
            pct = count * 100 // total_sessions if total_sessions else 0
            parts.append(f'<p><strong>{_escape(label)}</strong> — {count} sessions ({pct}%)</p>')
    if not parts:
        parts.append('<p>Not enough data to identify patterns.</p>')
    return '\n'.join(parts)


def generate_struggles_text(friction_types, total_friction):
    """Auto-generate 'Where Claude Struggles' text."""
    parts = []
    if not friction_types:
        return '<p>No significant friction patterns detected.</p>'

    for label, count, _ in friction_types[:3]:
        pct = count * 100 // total_friction if total_friction else 0
        parts.append(f'<p><strong>{_escape(label)}</strong> — {count} events ({pct}% of friction)</p>')
    return '\n'.join(parts)


def generate_usage_narrative(goal_categories, session_types, total_sessions):
    """Auto-generate 'Your Usage Pattern' narrative."""
    if not goal_categories:
        return '<p>Not enough data to characterize usage patterns.</p>'

    top_goal = goal_categories[0] if goal_categories else ('unknown', 0)
    top_type = session_types[0] if session_types else ('unknown', 0)

    narrative = f'<p>Across {total_sessions} sessions, your primary use of Claude is '
    narrative += f'<strong>{_escape(top_goal[0].lower())}</strong> ({top_goal[1]} goal instances). '

    if len(goal_categories) >= 2:
        narrative += f'This is followed by <strong>{_escape(goal_categories[1][0].lower())}</strong> ({goal_categories[1][1]}) '
    if len(goal_categories) >= 3:
        narrative += f'and <strong>{_escape(goal_categories[2][0].lower())}</strong> ({goal_categories[2][1]}). '

    narrative += f'Your most common session type is <strong>{_escape(top_type[0].lower())}</strong> ({top_type[1]} sessions).'
    narrative += '</p>'

    return narrative


def generate_recommendations(friction_counter, total_sessions, goal_counter, session_types):
    """Auto-generate recommendations based on data patterns (PRD Section 7.12)."""
    recs = []

    if friction_counter.get('context_overflow', 0) >= 3:
        recs.append({
            'title': 'Manage Session Length',
            'description': f'You had {friction_counter["context_overflow"]} context overflow events. '
                           f'Use /compact proactively when sessions exceed 20 messages. '
                           f'Write session state to a file before context compression so nothing is lost.'
        })

    if friction_counter.get('tool_failure', 0) >= 5:
        recs.append({
            'title': 'Add Subagent Limits',
            'description': f'Tool failures ({friction_counter["tool_failure"]} events) often come from '
                           f'rate limits when spawning too many parallel subagents. '
                           f'Limit to 5 concurrent subagents and wait for each batch to complete.'
        })

    if friction_counter.get('fabricated_data', 0) >= 1:
        recs.append({
            'title': 'Add Data Verification Guardrails',
            'description': f'Fabricated data was detected in {friction_counter["fabricated_data"]} session(s). '
                           f'Add a CLAUDE.md rule requiring source citations for factual claims, '
                           f'and consider a post-tool hook that validates research output quality.'
        })

    if friction_counter.get('wrong_approach', 0) >= 5:
        recs.append({
            'title': 'Provide More Upfront Constraints',
            'description': f'Claude took the wrong approach {friction_counter["wrong_approach"]} times. '
                           f'When starting complex tasks, provide explicit constraints and preferred approaches '
                           f'upfront rather than letting Claude choose freely.'
        })

    if goal_counter.get('research', 0) > total_sessions * 0.3:
        recs.append({
            'title': 'Build a Research Skill',
            'description': f'Research dominates your usage ({goal_counter["research"]} goal instances). '
                           f'Create a custom /research skill that encodes your research workflow, '
                           f'including output format, quality checks, and rate-limit-aware batching.'
        })

    if friction_counter.get('missed_context', 0) >= 3:
        recs.append({
            'title': 'Start Sessions with Context Loading',
            'description': f'Missed context ({friction_counter["missed_context"]} events) wastes time '
                           f're-explaining prior work. Start each session by having Claude read '
                           f'the relevant CLAUDE.md and recent work logs before diving in.'
        })

    # Always recommend running deep-insights monthly
    recs.append({
        'title': 'Run Deep Insights Monthly',
        'description': 'Track how your usage patterns, friction rates, and session quality change '
                       'over time. Monthly reports help you see whether CLAUDE.md improvements '
                       'are actually reducing friction.'
    })

    return recs[:5]  # Cap at 5 recommendations


def generate_methodology(total_sessions, manifest):
    """Generate methodology section HTML."""
    parts = []
    parts.append(
        f'<p><strong>Data source:</strong> {total_sessions} parent session JSONL files '
        f'from <code>~/.claude/projects/</code>. Subagent sessions excluded from primary analysis.</p>'
    )
    parts.append(
        '<p><strong>Preprocessing:</strong> A Python script extracted structured summaries '
        'from each session, compressing raw data into compact summaries at zero token cost.</p>'
    )
    parts.append(
        '<p><strong>Analysis:</strong> Opus sub-agents analyzed batches of sessions, '
        'producing structured facets with qualitative assessments of goals, satisfaction, '
        'friction, and helpfulness.</p>'
    )
    parts.append(
        '<p><strong>Limitations:</strong> Facets are qualitative assessments from session '
        'summaries, not full transcripts. Satisfaction is inferred from user tone, not explicit '
        'ratings. Short automated sessions may skew aggregates. Recommendations are suggestions, '
        'not prescriptions.</p>'
    )
    return '\n'.join(parts)


def build_report_data(facets, manifest, include_comparison=True):
    """Compute all aggregates and build the data dict for the template."""
    total = len(facets)
    if total == 0:
        print("Error: No facets to generate report from.")
        sys.exit(1)

    # --- Basic aggregations ---
    outcomes = Counter(f.get('outcome', 'unclear') for f in facets)
    satisfaction = aggregate_dict_field(facets, 'user_satisfaction_counts')
    helpfulness = Counter(f.get('claude_helpfulness', 'unknown') for f in facets)
    session_types = Counter(f.get('session_type', 'unknown') for f in facets)
    goal_categories = aggregate_dict_field(facets, 'goal_categories')
    friction_counter = aggregate_dict_field(facets, 'friction_counts')
    primary_successes = Counter()
    for f in facets:
        ps = f.get('primary_success')
        if ps and ps not in ('', 'None', None):
            primary_successes[ps] += 1

    # --- Derived metrics ---
    goals_achieved = outcomes.get('fully_achieved', 0) + outcomes.get('mostly_achieved', 0)
    goals_achieved_pct = (goals_achieved / total * 100) if total else 0

    helpful_count = helpfulness.get('essential', 0) + helpfulness.get('very_helpful', 0)
    helpful_pct = (helpful_count / total * 100) if total else 0

    sessions_with_friction = sum(
        1 for f in facets
        if any(v > 0 for v in (f.get('friction_counts') or {}).values())
    )
    friction_pct = (sessions_with_friction / total * 100) if total else 0
    total_friction = sum(friction_counter.values())

    # --- Sorted lists for charts ---
    outcome_order = ['fully_achieved', 'mostly_achieved', 'partially_achieved',
                     'not_achieved', 'abandoned', 'unclear']
    outcomes_list = [
        (OUTCOME_LABELS.get(k, k), outcomes.get(k, 0),
         outcomes.get(k, 0) * 100 / total if total else 0,
         OUTCOME_COLORS.get(k, '#8b949e'))
        for k in outcome_order if outcomes.get(k, 0) > 0
    ]

    satisfaction_order = ['satisfied', 'neutral', 'frustrated', 'dissatisfied']
    satisfaction_list = [
        (SATISFACTION_LABELS.get(k, k), satisfaction.get(k, 0),
         SATISFACTION_COLORS.get(k, '#8b949e'))
        for k in satisfaction_order if satisfaction.get(k, 0) > 0
    ]

    helpfulness_order = ['essential', 'very_helpful', 'moderately_helpful',
                         'slightly_helpful', 'unhelpful']
    helpfulness_list = [
        (HELPFULNESS_LABELS.get(k, k), helpfulness.get(k, 0),
         HELPFULNESS_COLORS.get(k, '#8b949e'))
        for k in helpfulness_order if helpfulness.get(k, 0) > 0
    ]

    goal_list = [
        (GOAL_LABELS.get(k, k), v)
        for k, v in goal_categories.most_common()
        if v > 0
    ]

    type_list = [
        (SESSION_TYPE_LABELS.get(k, k), v)
        for k, v in session_types.most_common()
        if v > 0
    ]

    success_list = [
        (SUCCESS_LABELS.get(k, k), v)
        for k, v in primary_successes.most_common()
        if v > 0
    ]

    friction_list = [
        (FRICTION_LABELS.get(k, k), v, FRICTION_COLORS.get(k, '#8b949e'))
        for k, v in friction_counter.most_common()
        if v > 0
    ]

    # --- Top friction sessions ---
    friction_sessions = []
    for f in facets:
        fc = f.get('friction_counts', {})
        ftotal = sum(v for v in fc.values() if isinstance(v, (int, float)))
        if ftotal > 0:
            friction_sessions.append({
                'session_id': f.get('session_id', ''),
                'date': format_date_from_facet(f, manifest),
                'summary': f.get('brief_summary', ''),
                'friction_total': ftotal,
                'frictions': sorted(
                    [(FRICTION_LABELS.get(k, k), v) for k, v in fc.items() if v > 0],
                    key=lambda x: x[1], reverse=True
                )
            })
    friction_sessions.sort(key=lambda x: x['friction_total'], reverse=True)
    top_friction = friction_sessions[:10]

    # --- Best sessions ---
    best_sessions = []
    for f in facets:
        if f.get('claude_helpfulness') == 'essential':
            goals = list((f.get('goal_categories') or {}).keys())
            best_sessions.append({
                'session_id': f.get('session_id', ''),
                'date': format_date_from_facet(f, manifest),
                'summary': f.get('brief_summary', ''),
                'helpfulness': 'Essential',
                'goals': [GOAL_LABELS.get(g, g) for g in goals[:3]],
            })
    best_sessions = best_sessions[:10]

    # --- Anomalies ---
    anomalies = []

    subagent_explosions = [
        f for f in facets
        if any(
            s.get('subagent_count', 0) >= 10
            for s in (manifest.get('sessions', []) if manifest else [])
            if s['session_id'] == f.get('session_id')
        )
    ]
    if subagent_explosions:
        anomalies.append({
            'title': f'{len(subagent_explosions)} session(s) with 10+ subagents',
            'description': 'Sessions that spawned 10 or more subagents. '
                           'This may indicate productive parallelization or runaway complexity. '
                           'IDs: ' + ', '.join(f.get('session_id', '')[:8] for f in subagent_explosions[:5])
        })

    not_achieved = [f for f in facets if f.get('outcome') == 'not_achieved']
    if not_achieved:
        anomalies.append({
            'title': f'{len(not_achieved)} session(s) with "not achieved" outcome',
            'description': 'Sessions where the primary goal was not accomplished. '
                           'Common causes: tool failures, rate limits, or abandoned tasks. '
                           'IDs: ' + ', '.join(f.get('session_id', '')[:8] for f in not_achieved[:5])
        })

    abandoned = [f for f in facets if f.get('outcome') == 'abandoned']
    if abandoned:
        anomalies.append({
            'title': f'{len(abandoned)} abandoned session(s)',
            'description': 'Sessions that were started but abandoned before completion. '
                           'IDs: ' + ', '.join(f.get('session_id', '')[:8] for f in abandoned[:5])
        })

    # --- Comparison ---
    comparison = None
    if include_comparison and os.path.isdir(NATIVE_FACETS_DIR):
        native_facets = []
        for fname in os.listdir(NATIVE_FACETS_DIR):
            if fname.endswith('.json'):
                try:
                    with open(os.path.join(NATIVE_FACETS_DIR, fname)) as nf:
                        native_facets.append(json.load(nf))
                except (json.JSONDecodeError, IOError):
                    pass

        if native_facets:
            native_help = Counter(f.get('claude_helpfulness', '') for f in native_facets)
            native_outcomes = Counter(f.get('outcome', '') for f in native_facets)
            native_sat = aggregate_dict_field(native_facets, 'user_satisfaction_counts')
            native_total = len(native_facets)
            native_dissatisfied = native_sat.get('dissatisfied', 0) + native_sat.get('frustrated', 0)
            native_total_sat = sum(native_sat.values())
            native_dissat_pct = (native_dissatisfied * 100 // native_total_sat) if native_total_sat else 0

            deep_dissatisfied = satisfaction.get('dissatisfied', 0) + satisfaction.get('frustrated', 0)
            deep_total_sat = sum(satisfaction.values())
            deep_dissat_pct = (deep_dissatisfied * 100 // deep_total_sat) if deep_total_sat else 0

            comparison = {
                'rows': [
                    {
                        'metric': 'Sessions analyzed',
                        'native': str(native_total),
                        'deep': str(total),
                    },
                    {
                        'metric': 'Dissatisfaction rate',
                        'native': f'{native_dissat_pct}%',
                        'deep': f'{deep_dissat_pct}%',
                    },
                    {
                        'metric': 'Goals fully achieved',
                        'native': f'{native_outcomes.get("fully_achieved", 0) * 100 // native_total if native_total else 0}%',
                        'deep': f'{outcomes.get("fully_achieved", 0) * 100 // total}%',
                    },
                    {
                        'metric': 'Claude helpful+',
                        'native': f'{(native_help.get("essential", 0) + native_help.get("very_helpful", 0)) * 100 // native_total if native_total else 0}%',
                        'deep': f'{helpful_pct:.0f}%',
                    },
                ]
            }

    # --- Build final data dict ---
    data = {
        'total_sessions': total,
        'date_range': compute_date_range(facets, manifest),
        'generated_date': datetime.now().strftime('%b %d, %Y'),
        'goals_achieved_pct': goals_achieved_pct,
        'helpful_pct': helpful_pct,
        'friction_count': sessions_with_friction,
        'friction_pct': friction_pct,
        'total_friction_events': total_friction,
        'outcomes': outcomes_list,
        'satisfaction': satisfaction_list,
        'helpfulness': helpfulness_list,
        'goal_categories': goal_list,
        'session_types': type_list,
        'primary_successes': success_list,
        'friction_types': friction_list,
        'friction_insight': generate_friction_insight(
            friction_list, total_friction, sessions_with_friction, total, top_friction
        ),
        'top_friction_sessions': top_friction,
        'best_sessions': best_sessions,
        'anomalies': anomalies,
        'excels_text': generate_excels_text(success_list, goal_list, total),
        'struggles_text': generate_struggles_text(friction_list, total_friction),
        'usage_narrative': generate_usage_narrative(goal_list, type_list, total),
        'recommendations': generate_recommendations(
            dict(friction_counter), total, dict(goal_categories), dict(session_types)
        ),
        'comparison': comparison,
        'methodology_text': generate_methodology(total, manifest),
    }

    return data


def main():
    parser = argparse.ArgumentParser(
        description='Claude Deep Insights — Generate HTML report',
        epilog='Part of claude-deep-insights: https://github.com/zaronian/claude-deep-insights'
    )
    parser.add_argument(
        '--input-dir',
        default=DEFAULT_INPUT_DIR,
        help=f'Directory containing facets and manifest (default: {DEFAULT_INPUT_DIR})'
    )
    parser.add_argument(
        '--output',
        default=None,
        help='Output HTML file path (default: {input-dir}/report.html)'
    )
    parser.add_argument(
        '--open',
        action='store_true',
        help='Auto-open the report in the default browser'
    )
    parser.add_argument(
        '--no-comparison',
        action='store_true',
        help='Skip native /insights comparison even if data exists'
    )
    args = parser.parse_args()

    input_dir = os.path.expanduser(args.input_dir)
    output_file = args.output or os.path.join(input_dir, 'report.html')

    # Load data
    print("Claude Deep Insights — Report Generation")
    print(f"  Input directory: {input_dir}")

    facets = load_facets(input_dir)
    manifest = load_manifest(input_dir)

    print(f"  Facets loaded:   {len(facets)}")
    if manifest:
        print(f"  Manifest:        {manifest.get('total_sessions', '?')} sessions")

    if not facets:
        print("Error: No facets found. Cannot generate report.")
        sys.exit(1)

    if len(facets) < 5:
        print(f"Note: Limited data — analysis based on {len(facets)} sessions.")

    # Build report data
    data = build_report_data(facets, manifest, include_comparison=not args.no_comparison)

    # Render HTML
    html = render(data)

    # Write output
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    with open(output_file, 'w') as f:
        f.write(html)

    file_size = os.path.getsize(output_file)
    print(f"\n  Report generated: {output_file} ({file_size / 1024:.0f} KB)")
    print(f"  Sessions:        {data['total_sessions']}")
    print(f"  Date range:      {data['date_range']}")
    print(f"  Goals achieved:  {data['goals_achieved_pct']:.0f}%")
    print(f"  Helpful+:        {data['helpful_pct']:.0f}%")
    print(f"  Friction rate:   {data['friction_pct']:.0f}%")

    # Auto-open
    if args.open:
        system = platform.system()
        if system == 'Darwin':
            subprocess.run(['open', output_file])
        elif system == 'Linux':
            subprocess.run(['xdg-open', output_file])
        else:
            print(f"  Open {output_file} in your browser to view the report.")


if __name__ == '__main__':
    main()
