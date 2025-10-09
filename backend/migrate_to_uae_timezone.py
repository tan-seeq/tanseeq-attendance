#!/usr/bin/env python3
"""
UAE Timezone Migration Script
==============================
Automatically replace datetime.now() and datetime.utcnow() with UAE timezone equivalents.

Safety: Creates backup before modifications.
"""

import re
import os
from pathlib import Path
from datetime import datetime

# Files to process (critical files first)
PRIORITY_FILES = [
    "server.py",
    "payroll_integration_engine.py",
    "english_salary_letter_pdf.py",
    "advances_model.py",
    "attendance_engine.py",
]

BACKUP_DIR = Path("/app/backend_backup")


def create_backup(file_path: Path):
    """Create backup of file before modification"""
    BACKUP_DIR.mkdir(exist_ok=True)
    backup_path = BACKUP_DIR / f"{file_path.name}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
    content = file_path.read_text()
    backup_path.write_text(content)
    print(f"  ✓ Backup created: {backup_path}")
    return content


def count_replacements(content: str) -> dict:
    """Count different datetime patterns"""
    counts = {
        "datetime.utcnow()": len(re.findall(r'datetime\.utcnow\(\)', content)),
        "datetime.now()": len(re.findall(r'datetime\.now\(\)', content)),
        "datetime.now(timezone.utc)": len(re.findall(r'datetime\.now\(timezone\.utc\)', content)),
        "datetime.now(UAE_TZ)": len(re.findall(r'datetime\.now\(UAE_TZ\)', content)),
    }
    return counts


def migrate_file(file_path: Path, dry_run=False) -> dict:
    """
    Migrate a single file to UAE timezone
    
    Replacements:
    1. datetime.utcnow() → get_uae_now()
    2. datetime.now() → get_uae_now() (except datetime.now(timezone.utc) and datetime.now(UAE_TZ))
    3. datetime.now(timezone.utc) → get_uae_now()
    """
    print(f"\n📄 Processing: {file_path.name}")
    
    # Read content
    content = file_path.read_text()
    
    # Count before
    before_counts = count_replacements(content)
    print(f"  Before: {sum(before_counts.values())} datetime calls")
    for pattern, count in before_counts.items():
        if count > 0:
            print(f"    - {pattern}: {count}")
    
    # Create backup
    if not dry_run:
        create_backup(file_path)
    
    # Perform replacements
    modified = content
    
    # 1. Replace datetime.now(timezone.utc) → get_uae_now()
    modified = re.sub(
        r'datetime\.now\(timezone\.utc\)',
        'get_uae_now()  # UAE timezone',
        modified
    )
    
    # 2. Replace datetime.utcnow() → get_uae_now()
    modified = re.sub(
        r'datetime\.utcnow\(\)',
        'get_uae_now()  # UAE timezone',
        modified
    )
    
    # 3. Replace datetime.now() → get_uae_now() (but NOT datetime.now(UAE_TZ))
    # We need to be careful here - only replace bare datetime.now()
    modified = re.sub(
        r'datetime\.now\(\)(?!\s*#\s*UAE)',  # Negative lookahead for UAE comment
        'get_uae_now()  # UAE timezone',
        modified
    )
    
    # 4. Keep datetime.now(UAE_TZ) as is (already correct)
    
    # Count after
    after_counts = count_replacements(modified)
    replacements = sum(before_counts.values()) - sum(after_counts.values())
    
    print(f"  After: {sum(after_counts.values())} datetime calls")
    print(f"  ✅ Replacements made: {replacements}")
    
    # Write modified content
    if not dry_run and replacements > 0:
        file_path.write_text(modified)
        print(f"  ✅ File updated successfully")
    elif dry_run:
        print(f"  ℹ️  DRY RUN - No changes written")
    
    return {
        "file": file_path.name,
        "before": sum(before_counts.values()),
        "after": sum(after_counts.values()),
        "replacements": replacements,
        "success": True
    }


def main(dry_run=True):
    """Main migration function"""
    print("=" * 70)
    print("🇦🇪 UAE TIMEZONE MIGRATION SCRIPT")
    print("=" * 70)
    print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'LIVE (will modify files)'}")
    print()
    
    backend_dir = Path("/app/backend")
    results = []
    
    # Process priority files first
    for filename in PRIORITY_FILES:
        file_path = backend_dir / filename
        if file_path.exists():
            try:
                result = migrate_file(file_path, dry_run=dry_run)
                results.append(result)
            except Exception as e:
                print(f"  ❌ Error processing {filename}: {e}")
                results.append({
                    "file": filename,
                    "success": False,
                    "error": str(e)
                })
        else:
            print(f"  ⚠️  File not found: {filename}")
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 MIGRATION SUMMARY")
    print("=" * 70)
    
    total_before = sum(r.get("before", 0) for r in results if r.get("success"))
    total_after = sum(r.get("after", 0) for r in results if r.get("success"))
    total_replacements = sum(r.get("replacements", 0) for r in results if r.get("success"))
    
    print(f"Files processed: {len([r for r in results if r.get('success')])}")
    print(f"Total datetime calls before: {total_before}")
    print(f"Total datetime calls after: {total_after}")
    print(f"Total replacements: {total_replacements}")
    
    if dry_run:
        print("\n⚠️  This was a DRY RUN - no files were modified")
        print("Run with dry_run=False to apply changes")
    else:
        print(f"\n✅ Migration complete! Backups saved to: {BACKUP_DIR}")
    
    return results


if __name__ == "__main__":
    import sys
    
    # Default to dry run
    dry_run = True
    
    if len(sys.argv) > 1 and sys.argv[1] == "--apply":
        dry_run = False
        print("⚠️  LIVE MODE - Files will be modified!")
        response = input("Continue? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted.")
            sys.exit(0)
    
    results = main(dry_run=dry_run)
    
    # Exit code
    if all(r.get("success") for r in results):
        sys.exit(0)
    else:
        sys.exit(1)
