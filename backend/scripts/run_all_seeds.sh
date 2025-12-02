#!/bin/bash
# Run all database seed scripts
# This script runs all Python seed scripts to populate initial data

set -e

SCRIPTS_DIR="backend/scripts"
PYTHON="${PYTHON:-python3}"

echo "🌱 Running database seed scripts..."

# Run seed scripts in order
echo "📦 Seeding AI Providers..."
$PYTHON "$SCRIPTS_DIR/seed_ai_providers.py" || echo "⚠️  Warning: seed_ai_providers.py failed"

echo "📦 Seeding AI Prompts..."
$PYTHON "$SCRIPTS_DIR/seed_ai_prompts.py" || echo "⚠️  Warning: seed_ai_prompts.py failed"

echo "📦 Seeding Quote Type Prompts..."
$PYTHON "$SCRIPTS_DIR/seed_quote_type_prompts.py" || echo "⚠️  Warning: seed_quote_type_prompts.py failed"

echo "✅ All seed scripts completed"

