#!/bin/bash
# Claude Deep Insights — Installer
# Copies scripts and skill to the appropriate Claude Code directories.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$HOME/.claude/skills/deep-insights"
SCRIPTS_DIR="$HOME/.claude/deep-insights-scripts"
OUTPUT_DIR="$HOME/.claude/usage-data/deep-insights"

echo "Claude Deep Insights — Installing"
echo "=================================="

# Check for Claude Code
if [ ! -d "$HOME/.claude" ]; then
    echo ""
    echo "Error: ~/.claude directory not found."
    echo "Please install Claude Code first: https://docs.anthropic.com/en/docs/claude-code"
    exit 1
fi

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo ""
    echo "Error: python3 not found."
    echo "Please install Python 3.8+: https://python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo ""
    echo "Error: Python 3.8+ required (found $PYTHON_VERSION)."
    echo "Please upgrade Python: https://python.org"
    exit 1
fi

echo "  Python:  $PYTHON_VERSION ✓"

# Copy skill
echo "  Skill:   $SKILL_DIR/"
mkdir -p "$SKILL_DIR"
cp "$SCRIPT_DIR/skill/SKILL.md" "$SKILL_DIR/"

# Copy scripts
echo "  Scripts: $SCRIPTS_DIR/"
mkdir -p "$SCRIPTS_DIR/templates"
cp "$SCRIPT_DIR/scripts/preprocess.py" "$SCRIPTS_DIR/"
cp "$SCRIPT_DIR/scripts/report.py" "$SCRIPTS_DIR/"
cp "$SCRIPT_DIR/scripts/templates/__init__.py" "$SCRIPTS_DIR/templates/"
cp "$SCRIPT_DIR/scripts/templates/report_template.py" "$SCRIPTS_DIR/templates/"

# Create output directory
mkdir -p "$OUTPUT_DIR"
echo "  Output:  $OUTPUT_DIR/"

echo ""
echo "Installation complete! ✓"
echo ""
echo "Usage:"
echo "  In Claude Code, type: /deep-insights"
echo ""
echo "Or run scripts directly:"
echo "  python3 $SCRIPTS_DIR/preprocess.py --output-dir $OUTPUT_DIR"
echo "  python3 $SCRIPTS_DIR/report.py --input-dir $OUTPUT_DIR --open"
