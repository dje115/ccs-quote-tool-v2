#!/bin/bash
# Run all database migrations
# This script applies all SQL migration files in the migrations directory

set -e

MIGRATIONS_DIR="backend/migrations"
DB_NAME="${POSTGRES_DB:-ccs_quote_tool}"
DB_USER="${POSTGRES_USER:-postgres}"
DB_PASSWORD="${POSTGRES_PASSWORD:-postgres_password_2025}"
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"

echo "🔄 Running database migrations..."
echo "Database: $DB_NAME"
echo "Host: $DB_HOST:$DB_PORT"

# Export password for psql
export PGPASSWORD=$DB_PASSWORD

# Get list of all migration files, sorted
MIGRATION_FILES=$(find "$MIGRATIONS_DIR" -name "*.sql" | sort)

for migration_file in $MIGRATION_FILES; do
    echo "📄 Applying: $(basename $migration_file)"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$migration_file" || {
        echo "⚠️  Warning: Migration $(basename $migration_file) failed or already applied"
    }
done

echo "✅ All migrations completed"

