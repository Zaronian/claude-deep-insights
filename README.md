# Claude Deep Insights

**Your Claude Code `/insights` report is lying to you.**

The native `/insights` command samples at most 50 sessions, analyzes them with a lightweight model, then *extrapolates* aggregate statistics across your full history. One bad session in the sample can make your entire report look catastrophic. The session counts, satisfaction rates, and friction numbers are often wildly inaccurate.

**Claude Deep Insights** preprocesses *all* your sessions locally (zero token cost), analyzes them with Opus-quality faceting, and produces a comprehensive HTML report based on real data from every session.

## Before & After

| Metric | Native /insights | Deep Insights |
|---|---|---|
| Sessions analyzed | 1 (sampled from 50 max) | 170 (every session) |
| Dissatisfaction rate | ~75% | ~10% |
| Wrong approach events | 330 (extrapolated) | 14 (actual) |
| Goals fully achieved | 0% | 50% |
| Claude helpful+ rate | "moderately helpful" | 75.9% |
| Fabricated data incidents | "Major theme" | 3 out of 170 |

*Same user, same month, same sessions. Different methodology.*

## How It Works

```
Stage 1: PREPROCESS          Stage 2: ANALYZE           Stage 3: REPORT
(Pure Python, local)         (Opus sub-agents)          (Pure Python, local)

~/.claude/projects/          session_summaries/          all_facets.json
  *.jsonl files         →      *.json files        →      │
  (raw sessions)              (compact summaries)         ▼
                                                        report.html
Cost: $0                     Cost: ~$0.50-2.00          Cost: $0
Time: ~30 seconds            Time: ~3-5 minutes         Time: ~5 seconds
```

1. **Preprocessing** reads all session JSONL files and extracts structured summaries — compressing ~163MB of raw data to ~1MB (99.4% reduction). Pure Python, zero tokens.
2. **Analysis** sends compressed summaries to Opus sub-agents in parallel batches. Each produces structured "facets" — qualitative assessments of goals, satisfaction, friction, and helpfulness.
3. **Report generation** aggregates all facets and renders a self-contained HTML file. Pure Python, zero tokens.

Total cost: roughly equivalent to one medium coding conversation.

## Installation

```bash
git clone https://github.com/zaronian/claude-deep-insights.git
cd claude-deep-insights
./install.sh
```

Requirements:
- Python 3.8+ (no pip packages needed — stdlib only)
- Claude Code (any plan)

## Usage

In Claude Code:

```
/deep-insights
```

That's it. The skill orchestrates all three stages automatically: preprocessing, parallel Opus analysis, and report generation. The HTML report opens in your browser when complete.

### Manual Usage

You can also run the scripts directly:

```bash
# Stage 1: Preprocess sessions
python3 ~/.claude/deep-insights-scripts/preprocess.py \
  --output-dir ~/.claude/usage-data/deep-insights/

# Stage 3: Generate report (after analysis is complete)
python3 ~/.claude/deep-insights-scripts/report.py \
  --input-dir ~/.claude/usage-data/deep-insights/ --open
```

## What You Get

The report includes:

- **At a Glance** — Total sessions, goals achieved %, helpfulness %, friction rate
- **Session Outcomes** — Distribution of fully/mostly/partially achieved, not achieved, abandoned
- **User Satisfaction** — Satisfaction signal distribution + Claude helpfulness ratings
- **What You Use Claude For** — Goal categories, session types, what goes right
- **Friction Analysis** — Friction type breakdown with key insights
- **Highest-Friction Sessions** — Top sessions by friction count with details
- **Best Sessions** — Sessions rated "essential" with goal badges
- **Anomaly Detection** — Subagent explosions, not-achieved outcomes, abandoned sessions
- **Patterns & Insights** — Where Claude excels, where it struggles, your usage narrative
- **Recommendations** — Actionable suggestions based on your friction patterns
- **Methodology** — Full transparency on data sources and analysis approach

## Configuration

### Preprocessing

```bash
python3 preprocess.py --help

Options:
  --output-dir DIR     Output directory (default: ./deep-insights-output/)
  --session-dir DIR    Session JSONL directory (default: ~/.claude/projects/)
  --force              Re-process all sessions (ignore cache)
```

### Report Generation

```bash
python3 report.py --help

Options:
  --input-dir DIR      Directory with facets + manifest (default: ./deep-insights-output/)
  --output FILE        Output HTML path (default: {input-dir}/report.html)
  --open               Auto-open report in browser
  --no-comparison      Skip native /insights comparison
```

### Analysis Model

The skill defaults to Opus for analysis (best quality). The architecture supports other models — Sonnet produces adequate results at lower cost for very large session counts.

## Cost Estimate

| Sessions | Preprocessing | Analysis (Opus) | Report | Total |
|---|---|---|---|---|
| 50 | $0 | ~$0.30 | $0 | ~$0.30 |
| 170 | $0 | ~$1.00 | $0 | ~$1.00 |
| 300 | $0 | ~$1.80 | $0 | ~$1.80 |
| 500 | $0 | ~$3.00 | $0 | ~$3.00 |

*Costs approximate. Actual usage depends on session complexity and content length.*

## Privacy

All processing happens locally on your machine. Session data never leaves your computer except when sent to Claude for analysis — which happens through your existing Claude Code session using your own API key/plan. The tool introduces no new privacy vectors.

## Uninstalling

```bash
cd claude-deep-insights
./uninstall.sh          # Remove scripts and skill
./uninstall.sh --purge  # Also remove cached data and reports
```

## Contributing

Found a bug or have a feature idea? [Open an issue](https://github.com/zaronian/claude-deep-insights/issues).

Pull requests welcome. Please:
- Keep changes focused and minimal
- Test with real session data if possible
- No external Python dependencies (stdlib only is a hard requirement)

## License

MIT — see [LICENSE](LICENSE).

---

*Built by [Snowline Consulting](https://github.com/zaronian). Analyzes your Claude Code sessions so you can work smarter.*
