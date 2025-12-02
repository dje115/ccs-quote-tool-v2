#!/bin/bash
# Complete database setup script
# Runs all migrations and seed scripts to set up a fresh database

set -e

echo "🚀 Starting database setup..."
echo "================================"

# Run migrations
echo ""
echo "Step 1: Running migrations..."
bash "$(dirname "$0")/run_all_migrations.sh"

# Run seed scripts
echo ""
echo "Step 2: Running seed scripts..."
bash "$(dirname "$0")/run_all_seeds.sh"

echo ""
echo "✅ Database setup completed successfully!"
echo "================================"

