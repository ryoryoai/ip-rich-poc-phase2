"""Migrate Phase1 data from public schema to Phase2 schema.

This script reads analysis_jobs from public.analysis_jobs (Phase1 Prisma)
and imports them into phase2.analysis_jobs (Phase2 SQLAlchemy).

Usage:
    cd <repo root>
    python scripts/migrate_phase1_data.py --check     # Preview data without importing
    python scripts/migrate_phase1_data.py --migrate   # Actually import data
"""

import argparse
import sys
import os
from pathlib import Path
from datetime import datetime
from uuid import UUID

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.db.session import engine, get_db
from app.db.models import AnalysisJob


def check_phase1_data(schema: str = "production"):
    """Check if Phase1 data exists in specified schema."""
    print("=" * 60)
    print(f"Phase1 データ確認 ({schema}.analysis_jobs)")
    print("=" * 60)

    with engine.connect() as conn:
        # Check if analysis_jobs exists in the schema
        result = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = '{schema}'
                AND table_name = 'analysis_jobs'
            )
        """))
        exists = result.scalar()

        if not exists:
            print(f"[X] {schema}.analysis_jobs テーブルが存在しません")
            return None

        # Get count
        result = conn.execute(text(f"SELECT COUNT(*) FROM {schema}.analysis_jobs"))
        count = result.scalar()
        print(f"[OK] テーブル存在: {schema}.analysis_jobs")
        print(f"[OK] レコード数: {count}")

        if count == 0:
            print("[!] データがありません")
            return []

        # Get sample data
        print("\n--- サンプルデータ (最新5件) ---")
        result = conn.execute(text(f"""
            SELECT
                id::text,
                status,
                patent_number,
                company_name,
                product_name,
                created_at,
                finished_at
            FROM {schema}.analysis_jobs
            ORDER BY created_at DESC
            LIMIT 5
        """))
        rows = result.fetchall()

        for row in rows:
            print(f"  ID: {row[0][:8]}...")
            print(f"    Status: {row[1]}, Patent: {row[2]}")
            print(f"    Company: {row[3]}, Product: {row[4]}")
            print(f"    Created: {row[5]}, Finished: {row[6]}")
            print()

        # Get all data for migration
        result = conn.execute(text(f"SELECT * FROM {schema}.analysis_jobs ORDER BY created_at"))
        columns = result.keys()
        all_rows = result.fetchall()

        return [dict(zip(columns, row)) for row in all_rows]


def check_phase2_data():
    """Check existing Phase2 data."""
    print("\n" + "=" * 60)
    print("Phase2 データ確認 (phase2.analysis_jobs)")
    print("=" * 60)

    with engine.connect() as conn:
        # Check if phase2.analysis_jobs exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'phase2'
                AND table_name = 'analysis_jobs'
            )
        """))
        exists = result.scalar()

        if not exists:
            print("[X] phase2.analysis_jobs テーブルが存在しません")
            print("   supabase/migrations を適用してください")
            return False

        # Get count
        result = conn.execute(text("SELECT COUNT(*) FROM phase2.analysis_jobs"))
        count = result.scalar()
        print(f"[OK] テーブル存在: phase2.analysis_jobs")
        print(f"[OK] 既存レコード数: {count}")

        return True


def migrate_data(phase1_data: list[dict], dry_run: bool = True):
    """Migrate Phase1 data to Phase2 schema."""
    print("\n" + "=" * 60)
    print("データマイグレーション" + (" (DRY RUN)" if dry_run else ""))
    print("=" * 60)

    if not phase1_data:
        print("マイグレーション対象データがありません")
        return

    # Check for existing records in Phase2
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id FROM phase2.analysis_jobs"))
        existing_ids = {str(row[0]) for row in result.fetchall()}

    migrated_count = 0
    skipped_count = 0
    errors = []

    for row in phase1_data:
        row_id = str(row['id'])

        # Skip if already exists
        if row_id in existing_ids:
            skipped_count += 1
            print(f"  SKIP (既存): {row_id[:8]}... - {row.get('patent_number', 'N/A')}")
            continue

        # Map Phase1 fields to Phase2
        phase2_data = {
            'id': row['id'],
            'status': row.get('status', 'pending'),
            'progress': row.get('progress', 0),
            'error_message': row.get('error_message'),

            # Field name mappings
            'patent_id': row.get('patent_number', ''),
            'claim_text': row.get('claim_text'),
            'company_name': row.get('company_name'),
            'product_name': row.get('product_name'),

            # Phase2 specific defaults
            'pipeline': 'phase1',  # Mark as migrated from Phase1
            'current_stage': None,

            # Deep Research fields
            'openai_response_id': row.get('openai_response_id'),
            'input_prompt': row.get('input_prompt'),
            'research_results': row.get('research_results'),

            # Analysis results
            'requirements': row.get('requirements'),
            'compliance_results': row.get('compliance_results'),
            'summary': row.get('summary'),

            # Batch processing
            'priority': row.get('priority', 5),
            'scheduled_for': row.get('scheduled_for'),
            'retry_count': row.get('retry_count', 0),
            'max_retries': row.get('max_retries', 3),
            'batch_id': row.get('batch_id'),
            'search_type': row.get('search_type', 'infringement_check'),

            # Additional results
            'infringement_score': row.get('infringement_score'),
            'revenue_estimate': row.get('revenue_estimate'),

            # Timestamps
            'created_at': row.get('created_at'),
            'updated_at': row.get('updated_at'),
            'queued_at': row.get('queued_at'),
            'started_at': row.get('started_at'),
            'completed_at': row.get('finished_at'),  # Field name change

            # Metadata
            'user_id': row.get('user_id'),
            'ip_address': row.get('ip_address'),
        }

        if dry_run:
            print(f"  MIGRATE: {row_id[:8]}... - {phase2_data['patent_id']}")
            migrated_count += 1
        else:
            try:
                with get_db() as db:
                    job = AnalysisJob(**phase2_data)
                    db.add(job)
                    db.commit()
                    print(f"  [OK] MIGRATED: {row_id[:8]}... - {phase2_data['patent_id']}")
                    migrated_count += 1
            except Exception as e:
                errors.append((row_id, str(e)))
                print(f"  [X] ERROR: {row_id[:8]}... - {e}")

    print("\n--- 結果サマリー ---")
    print(f"  マイグレーション: {migrated_count} 件")
    print(f"  スキップ (既存): {skipped_count} 件")
    if errors:
        print(f"  エラー: {len(errors)} 件")
        for error_id, error_msg in errors:
            print(f"    - {error_id[:8]}...: {error_msg}")


def main():
    parser = argparse.ArgumentParser(
        description='Phase1からPhase2へのデータマイグレーション'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='データの確認のみ（マイグレーションなし）'
    )
    parser.add_argument(
        '--migrate',
        action='store_true',
        help='実際にマイグレーションを実行'
    )
    parser.add_argument(
        '--source-schema',
        default='production',
        help='Phase1データのスキーマ名 (default: production)'
    )
    args = parser.parse_args()

    if not args.check and not args.migrate:
        parser.print_help()
        print("\n[!] --check または --migrate オプションを指定してください")
        sys.exit(1)

    # Check Phase1 data
    phase1_data = check_phase1_data(schema=args.source_schema)
    if phase1_data is None:
        sys.exit(1)

    # Check Phase2 table exists
    if not check_phase2_data():
        sys.exit(1)

    if args.check:
        # Preview only
        migrate_data(phase1_data, dry_run=True)
        print("\n[OK] 確認完了。実際にマイグレーションする場合は --migrate オプションを使用してください")

    elif args.migrate:
        # Confirm before migration
        print(f"\n[!] {len(phase1_data)} 件のデータをマイグレーションします。続行しますか？ [y/N] ", end='')
        response = input().strip().lower()
        if response != 'y':
            print("キャンセルしました")
            sys.exit(0)

        migrate_data(phase1_data, dry_run=False)
        print("\n[OK] マイグレーション完了")


if __name__ == '__main__':
    main()
