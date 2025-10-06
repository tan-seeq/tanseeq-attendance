#!/usr/bin/env python3
"""
Debug test to verify the root cause of working hours calculation issue
"""

def calculate_working_hours_and_deductions_debug(check_in, check_out, break_time_minutes=0, is_admin_edited=False):
    """Debug version of the calculation function"""
    from datetime import datetime
    
    print(f"DEBUG: check_in = '{check_in}' (type: {type(check_in)})")
    print(f"DEBUG: check_out = '{check_out}' (type: {type(check_out)})")
    
    try:
        # Parse times - this is where the error occurs
        if isinstance(check_in, str):
            print(f"DEBUG: Splitting check_in by 'T': {check_in.split('T')}")
            if 'T' in check_in:
                check_in_time = datetime.strptime(check_in.split('T')[0] + ' ' + check_in.split('T')[1][:5], "%Y-%m-%d %H:%M")
            else:
                # Handle space-separated format
                check_in_time = datetime.strptime(check_in[:16], "%Y-%m-%d %H:%M")
            print(f"DEBUG: Parsed check_in_time = {check_in_time}")
        else:
            check_in_time = check_in

        if isinstance(check_out, str):
            print(f"DEBUG: Splitting check_out by 'T': {check_out.split('T')}")
            if 'T' in check_out:
                check_out_time = datetime.strptime(check_out.split('T')[0] + ' ' + check_out.split('T')[1][:5], "%Y-%m-%d %H:%M")
            else:
                # Handle space-separated format
                check_out_time = datetime.strptime(check_out[:16], "%Y-%m-%d %H:%M")
            print(f"DEBUG: Parsed check_out_time = {check_out_time}")
        else:
            check_out_time = check_out

        # Calculate total worked time
        total_worked_time = (check_out_time - check_in_time).total_seconds() / 3600.0
        break_time_hours = break_time_minutes / 60.0
        net_worked_hours = max(0, total_worked_time - break_time_hours)
        
        print(f"DEBUG: total_worked_time = {total_worked_time}")
        print(f"DEBUG: break_time_hours = {break_time_hours}")
        print(f"DEBUG: net_worked_hours = {net_worked_hours}")
        
        return {
            "total_hours": round(net_worked_hours, 2),
            "status": "complete"
        }

    except Exception as e:
        print(f"DEBUG: Error occurred: {e}")
        return {
            "total_hours": 0.0,
            "status": "error"
        }

# Test with the problematic format
print("=== Testing with problematic format (space-separated) ===")
result1 = calculate_working_hours_and_deductions_debug("2025-08-28 11:08:41", "2025-08-28 18:00", 60)
print(f"Result: {result1}")

print("\n=== Testing with ISO format (T-separated) ===")
result2 = calculate_working_hours_and_deductions_debug("2025-08-28T11:08:41", "2025-08-28T18:00", 60)
print(f"Result: {result2}")

print("\n=== Testing with mixed format ===")
result3 = calculate_working_hours_and_deductions_debug("2025-08-28 11:08:41", "2025-08-28 18:00:00", 60)
print(f"Result: {result3}")