#!/bin/bash
# Claude Deep Insights — Uninstaller
# Removes installed scripts, skill, and optionally generated data.

set -e

SKILL_DIR="$HOME/.claude/skills/deep-insights"
SCRIPTS_DIR="$HOME/.claude/deep-insights-scripts"
OUTPUT_DIR="$HOME/.claude/usage-data/deep-insights"

echo "Claude Deep Insights — Uninstalling"
echo "====================================="

# Remove skill
if [ -d "$SKILL_DIR" ]; then
    rm -rf "$SKILL_DIR"
    echo "  Removed skill:   $SKILL_DIR"
else
    echo "  Skill not found: $SKILL_DIR (already removed)"
fi

# Remove scripts
if [ -d "$SCRIPTS_DIR" ]; then
    rm -rf "$SCRIPTS_DIR"
    echo "  Removed scripts: $SCRIPTS_DIR"
else
    echo "  Scripts not found: $SCRIPTS_DIR (already removed)"
fi

# Handle output data
if [ -d "$OUTPUT_DIR" ]; then
    if [ "$1" = "--purge" ]; then
        rm -rf "$OUTPUT_DIR"
        echo "  Removed data:    $OUTPUT_DIR (--purge)"
    else
        echo "  Kept data:       $OUTPUT_DIR"
        echo "    (Use --purge to also remove generated reports and cached data)"
    fi
else
    echo "  No data found:   $OUTPUT_DIR"
fi

echo ""
echo "Uninstall complete."
