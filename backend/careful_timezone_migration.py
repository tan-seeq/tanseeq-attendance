#!/usr/bin/env python3
"""
Careful UAE Timezone Migration
================================
More conservative approach - only replace safe patterns
"""

import re
from pathlib import Path


def safe_migrate_server_py():
    """Carefully migrate server.py"""
    file_path = Path("/app/backend/server.py")
    content = file_path.read_text()
    
    # Pattern 1: Replace datetime.utcnow() in simple assignments
    # now = datetime.utcnow() → now = get_uae_now()
    content = re.sub(
        r'(\s+)now\s*=\s*datetime\.utcnow\(\)',
        r'\1now = get_uae_now()  # UAE timezone',
        content
    )
    
    # Pattern 2: Replace datetime.utcnow() in expressions
    # expire = datetime.utcnow() + ... → expire = get_uae_now() + ...
    content = re.sub(
        r'(\s+)expire\s*=\s*datetime\.utcnow\(\)',
        r'\1expire = get_uae_now()  # UAE timezone',
        content
    )
    
    # Pattern 3: Replace datetime.now(timezone.utc) → get_uae_now()
    content = re.sub(
        r'datetime\.now\(timezone\.utc\)',
        'get_uae_now()  # UAE timezone',
        content
    )
    
    # Pattern 4: Replace "created_at": datetime.utcnow() → to_iso_string_uae()
    content = re.sub(
        r'"created_at":\s*datetime\.utcnow\(\)',
        '"created_at": to_iso_string_uae()  # UAE timezone',
        content
    )
    
    # Pattern 5: Replace "updated_at": datetime.utcnow() → to_iso_string_uae()
    content = re.sub(
        r'"updated_at":\s*datetime\.utcnow\(\)',
        '"updated_at": to_iso_string_uae()  # UAE timezone',
        content
    )
    
    # Pattern 6: Replace "approved_at": datetime.utcnow() → to_iso_string_uae()
    content = re.sub(
        r'"approved_at":\s*datetime\.utcnow\(\)',
        '"approved_at": to_iso_string_uae()  # UAE timezone',
        content
    )
    
    # Pattern 7: Replace attendance_data["created_at"] = datetime.utcnow()
    content = re.sub(
        r'attendance_data\["created_at"\]\s*=\s*datetime\.utcnow\(\)',
        'attendance_data["created_at"] = to_iso_string_uae()  # UAE timezone',
        content
    )
    
    # Write back
    file_path.write_text(content)
    print(f"✅ Migrated server.py (safe patterns only)")


def safe_migrate_other_files():
    """Migrate other critical files"""
    files = [
        "payroll_integration_engine.py",
        "advances_model.py",
        "attendance_engine.py"
    ]
    
    for filename in files:
        file_path = Path(f"/app/backend/{filename}")
        if not file_path.exists():
            continue
        
        content = file_path.read_text()
        
        # Replace datetime.now() → get_uae_now() (except datetime.now(UAE_TZ))
        content = re.sub(
            r'datetime\.now\(\)(?!\s)',  # Not followed by space before method call
            'get_uae_now()  # UAE timezone',
            content
        )
        
        # Replace datetime.now(timezone.utc) → get_uae_now()
        content = re.sub(
            r'datetime\.now\(timezone\.utc\)',
            'get_uae_now()  # UAE timezone',
            content
        )
        
        # Replace datetime.utcnow() → get_uae_now()
        content = re.sub(
            r'datetime\.utcnow\(\)',
            'get_uae_now()  # UAE timezone',
            content
        )
        
        file_path.write_text(content)
        print(f"✅ Migrated {filename}")


if __name__ == "__main__":
    print("Starting careful timezone migration...")
    safe_migrate_server_py()
    safe_migrate_other_files()
    print("\n✅ Migration complete!")
