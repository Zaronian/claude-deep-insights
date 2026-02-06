"""
Claude Deep Insights — HTML Report Template

Self-contained HTML with inline CSS, dark theme, CSS-only charts.
No external dependencies, no JavaScript required for data visualization.
Responsive design (grid collapses below 768px).

Design specs from PRD Section 7:
- Background: #0d1117
- Card background: #161b22
- Border: #30363d
- Text: #e6edf3
- Muted text: #8b949e
- Accent blue: #58a6ff
- Green: #3fb950 / Yellow: #d29922 / Orange: #db6d28 / Red: #f85149 / Purple: #bc8cff
"""


def _css():
    return """
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
        background: #0d1117; color: #e6edf3; line-height: 1.6;
        padding: 48px 24px;
    }
    .container { max-width: 1200px; margin: 0 auto; }
    h1 { font-size: 32px; font-weight: 700; color: #e6edf3; margin-bottom: 4px; }
    h2 { font-size: 22px; font-weight: 600; color: #e6edf3; margin-top: 48px; margin-bottom: 16px;
         padding-bottom: 8px; border-bottom: 1px solid #30363d; }
    h3 { font-size: 16px; font-weight: 600; color: #e6edf3; margin-bottom: 12px; }
    a { color: #58a6ff; text-decoration: none; }
    a:hover { text-decoration: underline; }
    .subtitle { color: #8b949e; font-size: 14px; margin-bottom: 4px; }
    .methodology-note { color: #8b949e; font-size: 12px; margin-bottom: 32px; }

    /* At a Glance stat cards */
    .stats-row {
        display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;
        margin-bottom: 40px;
    }
    .stat-card {
        background: #161b22; border: 1px solid #30363d; border-radius: 8px;
        padding: 20px; text-align: center;
    }
    .stat-value { font-size: 28px; font-weight: 700; }
    .stat-label { font-size: 12px; color: #8b949e; text-transform: uppercase; margin-top: 4px; }
    .stat-green .stat-value { color: #3fb950; }
    .stat-blue .stat-value { color: #58a6ff; }
    .stat-yellow .stat-value { color: #d29922; }
    .stat-purple .stat-value { color: #bc8cff; }

    /* Cards */
    .card {
        background: #161b22; border: 1px solid #30363d; border-radius: 8px;
        padding: 20px; margin-bottom: 16px;
    }
    .card p { font-size: 14px; color: #8b949e; line-height: 1.6; margin-bottom: 8px; }

    /* Two-column grid */
    .grid-2 {
        display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px;
    }

    /* Bar charts */
    .chart-title {
        font-size: 12px; font-weight: 600; color: #8b949e;
        text-transform: uppercase; margin-bottom: 12px;
    }
    .bar-row { display: flex; align-items: center; margin-bottom: 8px; }
    .bar-label {
        width: 150px; font-size: 12px; color: #8b949e; flex-shrink: 0;
        overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    }
    .bar-track {
        flex: 1; height: 8px; background: #21262d; border-radius: 4px; margin: 0 10px;
    }
    .bar-fill { height: 100%; border-radius: 4px; min-width: 2px; }
    .bar-value {
        width: 70px; font-size: 12px; font-weight: 500; color: #8b949e; text-align: right;
    }

    /* Comparison callout */
    .comparison-callout {
        background: #161b22; border: 1px solid #d29922; border-radius: 8px;
        padding: 20px; margin-bottom: 24px;
    }
    .comparison-callout h3 { color: #d29922; margin-bottom: 12px; }
    .comparison-table { width: 100%; border-collapse: collapse; font-size: 13px; }
    .comparison-table th {
        text-align: left; padding: 8px; border-bottom: 2px solid #30363d;
        color: #8b949e; font-size: 11px; text-transform: uppercase;
    }
    .comparison-table td { padding: 8px; border-bottom: 1px solid #21262d; }
    .comparison-table .old { color: #f85149; }
    .comparison-table .new { color: #3fb950; font-weight: 600; }

    /* Session cards (friction, best) */
    .session-card {
        background: #161b22; border: 1px solid #30363d; border-radius: 8px;
        padding: 16px; margin-bottom: 12px;
    }
    .session-card-title {
        font-size: 14px; font-weight: 600; color: #e6edf3; margin-bottom: 6px;
    }
    .session-card-desc { font-size: 13px; color: #8b949e; line-height: 1.5; }
    .session-card-tags { margin-top: 10px; }

    /* Friction cards */
    .friction-session { border-color: #f8514950; }
    .friction-session .session-card-title { color: #f85149; }

    /* Best session cards */
    .best-session { border-color: #3fb95050; }
    .best-session .session-card-title { color: #3fb950; }

    /* Tags */
    .tag {
        display: inline-block; padding: 2px 8px; border-radius: 4px;
        font-size: 11px; font-weight: 500; margin-right: 4px; margin-bottom: 4px;
    }
    .tag-red { background: #f8514920; color: #f85149; }
    .tag-yellow { background: #d2992220; color: #d29922; }
    .tag-green { background: #3fb95020; color: #3fb950; }
    .tag-blue { background: #58a6ff20; color: #58a6ff; }
    .tag-purple { background: #bc8cff20; color: #bc8cff; }
    .tag-gray { background: #8b949e20; color: #8b949e; }

    /* Insight boxes */
    .insight-box {
        background: #161b22; border: 1px solid #30363d; border-radius: 8px;
        padding: 16px; font-size: 14px; color: #8b949e; line-height: 1.6;
    }
    .insight-box p { margin-bottom: 10px; }
    .insight-box strong { color: #e6edf3; }

    /* Recommendation cards */
    .rec-card {
        background: #161b22; border: 1px solid #58a6ff50; border-radius: 8px;
        padding: 16px; margin-bottom: 12px;
    }
    .rec-title { font-size: 15px; font-weight: 600; color: #58a6ff; margin-bottom: 6px; }
    .rec-desc { font-size: 13px; color: #8b949e; line-height: 1.5; }

    /* Anomaly section */
    .anomaly-card {
        background: #161b22; border: 1px solid #d2992250; border-radius: 8px;
        padding: 16px; margin-bottom: 12px;
    }
    .anomaly-title { font-size: 14px; font-weight: 600; color: #d29922; margin-bottom: 6px; }
    .anomaly-desc { font-size: 13px; color: #8b949e; line-height: 1.5; }

    /* Patterns section */
    .pattern-box {
        background: #161b22; border: 1px solid #30363d; border-radius: 8px;
        padding: 16px;
    }
    .pattern-box h3 { color: #3fb950; margin-bottom: 8px; }
    .pattern-box.struggle h3 { color: #f85149; }
    .pattern-narrative {
        background: #161b22; border: 1px solid #30363d; border-radius: 8px;
        padding: 16px; margin-top: 16px; font-size: 14px; color: #8b949e; line-height: 1.7;
    }

    /* Methodology */
    .methodology {
        background: #161b22; border: 1px solid #30363d; border-radius: 8px;
        padding: 20px; font-size: 13px; color: #8b949e; line-height: 1.6;
    }
    .methodology p { margin-bottom: 8px; }
    .methodology strong { color: #e6edf3; }

    /* Footer */
    .footer {
        margin-top: 40px; text-align: center; font-size: 12px; color: #484f58;
        padding-top: 24px; border-top: 1px solid #21262d;
    }
    .footer a { color: #484f58; }

    /* Responsive */
    @media (max-width: 768px) {
        .grid-2 { grid-template-columns: 1fr; }
        .stats-row { grid-template-columns: repeat(2, 1fr); }
        .bar-label { width: 100px; }
    }
    """


def _escape(text):
    """Escape HTML special characters."""
    if text is None:
        return ''
    return (str(text)
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;'))


def _bar_chart(items, color='#58a6ff', max_val=None):
    """Generate HTML for a CSS-only horizontal bar chart.

    items: list of (label, count) tuples
    """
    if not items:
        return '<p style="color:#8b949e;font-size:13px;">No data</p>'

    if max_val is None:
        max_val = max(v for _, v in items) if items else 1
    if max_val == 0:
        max_val = 1

    rows = []
    for label, value in items:
        pct = (value / max_val) * 100
        rows.append(
            f'<div class="bar-row">'
            f'<div class="bar-label">{_escape(label)}</div>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{pct:.1f}%;background:{color}"></div></div>'
            f'<div class="bar-value">{value}</div>'
            f'</div>'
        )
    return '\n'.join(rows)


def _bar_chart_colored(items):
    """Bar chart where each item has its own color.

    items: list of (label, count, color) tuples
    """
    if not items:
        return '<p style="color:#8b949e;font-size:13px;">No data</p>'

    max_val = max(v for _, v, _ in items) if items else 1
    if max_val == 0:
        max_val = 1

    rows = []
    for label, value, color in items:
        pct = (value / max_val) * 100
        rows.append(
            f'<div class="bar-row">'
            f'<div class="bar-label">{_escape(label)}</div>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{pct:.1f}%;background:{color}"></div></div>'
            f'<div class="bar-value">{value}</div>'
            f'</div>'
        )
    return '\n'.join(rows)


def _bar_chart_with_pct(items):
    """Bar chart showing count and percentage.

    items: list of (label, count, pct, color) tuples
    """
    if not items:
        return '<p style="color:#8b949e;font-size:13px;">No data</p>'

    max_val = max(v for _, v, _, _ in items) if items else 1
    if max_val == 0:
        max_val = 1

    rows = []
    for label, value, pct, color in items:
        bar_pct = (value / max_val) * 100
        rows.append(
            f'<div class="bar-row">'
            f'<div class="bar-label">{_escape(label)}</div>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{bar_pct:.1f}%;background:{color}"></div></div>'
            f'<div class="bar-value">{value} ({pct:.0f}%)</div>'
            f'</div>'
        )
    return '\n'.join(rows)


def _friction_tag(friction_type, count):
    """Generate a friction tag badge."""
    return f'<span class="tag tag-red">{_escape(friction_type)} &times;{count}</span>'


def _goal_tag(category):
    """Generate a goal category tag."""
    return f'<span class="tag tag-blue">{_escape(category)}</span>'


def render(data):
    """Render the full HTML report from aggregated data.

    data dict keys:
        total_sessions, date_range, generated_date,
        goals_achieved_pct, helpful_pct, friction_count, friction_pct,
        outcomes (list of tuples), satisfaction (list of tuples),
        helpfulness (list of tuples), goal_categories (list of tuples),
        session_types (list of tuples), primary_successes (list of tuples),
        friction_types (list of tuples), total_friction_events,
        top_friction_sessions (list of dicts),
        best_sessions (list of dicts),
        anomalies (list of dicts),
        excels_text, struggles_text, usage_narrative,
        recommendations (list of dicts),
        comparison (dict or None),
        methodology_text
    """
    # --- Header ---
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Claude Deep Insights</title>
  <style>{_css()}</style>
</head>
<body>
<div class="container">

<h1>Claude Deep Insights</h1>
<p class="subtitle">{data['total_sessions']} sessions analyzed &middot; {_escape(data['date_range'])} &middot; Generated {_escape(data['generated_date'])}</p>
<p class="methodology-note">All sessions analyzed with Opus-quality faceting on locally preprocessed summaries. No sampling. No extrapolation.</p>
"""

    # --- Comparison Callout (conditional) ---
    if data.get('comparison'):
        comp = data['comparison']
        html += f"""
<div class="comparison-callout">
  <h3>Deep Insights vs. Native /insights</h3>
  <table class="comparison-table">
    <tr><th>Metric</th><th>Native /insights</th><th>Deep Insights</th></tr>
"""
        for row in comp.get('rows', []):
            html += f'    <tr><td>{_escape(row["metric"])}</td><td class="old">{_escape(row["native"])}</td><td class="new">{_escape(row["deep"])}</td></tr>\n'
        html += """  </table>
</div>
"""

    # --- At a Glance ---
    html += f"""
<h2>At a Glance</h2>
<div class="stats-row">
  <div class="stat-card stat-blue">
    <div class="stat-value">{data['total_sessions']}</div>
    <div class="stat-label">Sessions Analyzed</div>
  </div>
  <div class="stat-card stat-green">
    <div class="stat-value">{data['goals_achieved_pct']:.0f}%</div>
    <div class="stat-label">Goals Achieved</div>
  </div>
  <div class="stat-card stat-purple">
    <div class="stat-value">{data['helpful_pct']:.0f}%</div>
    <div class="stat-label">Claude Helpful+</div>
  </div>
  <div class="stat-card stat-yellow">
    <div class="stat-value">{data['friction_count']}</div>
    <div class="stat-label">Sessions with Friction ({data['friction_pct']:.0f}%)</div>
  </div>
</div>
"""

    # --- Session Outcomes ---
    html += """<h2>Session Outcomes</h2>\n<div class="card">\n"""
    html += _bar_chart_with_pct(data['outcomes'])
    html += "\n</div>\n"

    # --- User Satisfaction ---
    html += """<h2>User Satisfaction</h2>\n<div class="grid-2">\n"""

    # Left: satisfaction signals
    html += '<div class="card">\n<div class="chart-title">Satisfaction Signals'
    total_sat = sum(v for _, v, _ in data['satisfaction'])
    html += f' ({total_sat} total)</div>\n'
    html += _bar_chart_colored(data['satisfaction'])
    pos = sum(v for label, v, _ in data['satisfaction'] if label in ('Satisfied', 'Neutral'))
    neg = total_sat - pos
    if total_sat > 0:
        html += f'\n<p style="font-size:12px;color:#8b949e;margin-top:10px;">Positive/neutral: <strong style="color:#e6edf3">{pos/total_sat*100:.0f}%</strong> &middot; Negative: <strong style="color:#e6edf3">{neg/total_sat*100:.0f}%</strong></p>'
    html += '\n</div>\n'

    # Right: helpfulness
    html += '<div class="card">\n<div class="chart-title">Claude Helpfulness</div>\n'
    html += _bar_chart_colored(data['helpfulness'])
    html += '\n</div>\n</div>\n'

    # --- What You Use Claude For ---
    html += """<h2>What You Use Claude For</h2>\n<div class="grid-2">\n"""

    # Left: goal categories
    html += '<div class="card">\n<div class="chart-title">Goal Categories</div>\n'
    html += _bar_chart(data['goal_categories'], color='#bc8cff')
    html += '\n</div>\n'

    # Right: session types + what went right
    html += '<div class="card">\n<div class="chart-title">What Goes Right</div>\n'
    html += _bar_chart(data['primary_successes'], color='#3fb950')
    html += '\n<div class="chart-title" style="margin-top:16px;">Session Types</div>\n'
    html += _bar_chart(data['session_types'], color='#58a6ff')
    html += '\n</div>\n</div>\n'

    # --- Friction Analysis ---
    html += f"""<h2>Friction Analysis</h2>
<p style="color:#8b949e;font-size:14px;margin-bottom:16px;">{data['total_friction_events']} friction events across {data['friction_count']} of {data['total_sessions']} sessions ({data['friction_pct']:.0f}%). {data['total_sessions'] - data['friction_count']} sessions had zero friction.</p>
<div class="grid-2">
"""
    # Left: friction types
    html += '<div class="card">\n<div class="chart-title">Friction Types</div>\n'
    html += _bar_chart_colored(data['friction_types'])
    html += '\n</div>\n'

    # Right: key insight
    html += '<div class="insight-box">\n<div class="chart-title">Key Insight</div>\n'
    html += data.get('friction_insight', '')
    html += '\n</div>\n</div>\n'

    # --- Highest-Friction Sessions ---
    if data.get('top_friction_sessions'):
        html += '<h2>Highest-Friction Sessions</h2>\n'
        for sess in data['top_friction_sessions']:
            html += f"""<div class="session-card friction-session">
  <div class="session-card-title">{_escape(sess['date'])} &middot; {_escape(sess['session_id'][:8])} &middot; {sess['friction_total']} friction events</div>
  <div class="session-card-desc">{_escape(sess['summary'])}</div>
  <div class="session-card-tags">{''.join(_friction_tag(ft, fc) for ft, fc in sess['frictions'])}</div>
</div>
"""

    # --- Best Sessions ---
    if data.get('best_sessions'):
        html += '<h2>Best Sessions</h2>\n'
        for sess in data['best_sessions']:
            html += f"""<div class="session-card best-session">
  <div class="session-card-title">{_escape(sess['date'])} &middot; {_escape(sess['session_id'][:8])} &middot; {_escape(sess['helpfulness'])}</div>
  <div class="session-card-desc">{_escape(sess['summary'])}</div>
  <div class="session-card-tags">{''.join(_goal_tag(g) for g in sess['goals'])}</div>
</div>
"""

    # --- Anomaly Detection ---
    if data.get('anomalies'):
        html += '<h2>Anomaly Detection</h2>\n'
        for anom in data['anomalies']:
            html += f"""<div class="anomaly-card">
  <div class="anomaly-title">{_escape(anom['title'])}</div>
  <div class="anomaly-desc">{_escape(anom['description'])}</div>
</div>
"""

    # --- Patterns & Insights ---
    html += '<h2>Patterns &amp; Insights</h2>\n<div class="grid-2">\n'
    html += f'<div class="pattern-box"><h3>Where Claude Excels</h3>\n{data.get("excels_text", "")}\n</div>\n'
    html += f'<div class="pattern-box struggle"><h3>Where Claude Struggles</h3>\n{data.get("struggles_text", "")}\n</div>\n'
    html += '</div>\n'
    html += f'<div class="pattern-narrative">\n<h3 style="color:#58a6ff;margin-bottom:8px;">Your Usage Pattern</h3>\n{data.get("usage_narrative", "")}\n</div>\n'

    # --- Recommendations ---
    if data.get('recommendations'):
        html += '<h2>Recommendations</h2>\n'
        for rec in data['recommendations']:
            html += f"""<div class="rec-card">
  <div class="rec-title">{_escape(rec['title'])}</div>
  <div class="rec-desc">{_escape(rec['description'])}</div>
</div>
"""

    # --- Methodology ---
    html += '<h2>Methodology</h2>\n<div class="methodology">\n'
    html += data.get('methodology_text', '')
    html += '\n</div>\n'

    # --- Footer ---
    html += f"""
<div class="footer">
  Claude Deep Insights v1.0 &middot; {data['total_sessions']} sessions &middot; Opus-quality analysis &middot; {_escape(data['generated_date'])}<br>
  <a href="https://github.com/zaronian/claude-deep-insights">github.com/zaronian/claude-deep-insights</a>
</div>

</div>
</body>
</html>"""

    return html
