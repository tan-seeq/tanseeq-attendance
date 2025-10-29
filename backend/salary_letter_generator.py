"""
Salary Letter PDF Generator
Generates professional salary letters in English matching the provided template
"""

def generate_salary_letter_html(employee_data: dict, cycle_data: dict) -> str:
    """
    Generate HTML for salary letter matching the TANSEEQ template
    
    Args:
        employee_data: Dictionary containing employee salary details
        cycle_data: Dictionary containing payroll cycle information
    
    Returns:
        HTML string ready for PDF conversion
    """
    
    # Extract data
    emp_name = employee_data.get('name', 'N/A')
    emp_id = employee_data.get('employee_code') or employee_data.get('employee_id', 'N/A')
    
    # Salary components
    base_salary = float(employee_data.get('base_salary', 0))
    allowances = float(employee_data.get('allowances', 0) or employee_data.get('total_allowances', 0))
    gross_salary = float(employee_data.get('gross_salary', base_salary + allowances))
    
    # Deductions
    admin_deduction = float(employee_data.get('manual_deductions', 0))
    attendance_deduction = float(employee_data.get('attendance_deductions', 0))
    advance_deduction = float(employee_data.get('advance_deductions', 0))
    total_deductions = admin_deduction + attendance_deduction + advance_deduction
    
    # Net salary
    net_payable = gross_salary - total_deductions
    
    # Cycle info
    cycle_id = cycle_data.get('id', 'N/A')
    period = cycle_data.get('period', cycle_data.get('month', 'N/A'))
    
    # Current date
    from datetime import datetime
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Salary Statement - {emp_name}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Arial', 'Helvetica', sans-serif;
            color: #1a1a1a;
            line-height: 1.3;
            padding: 20px 15px;
        }}
        
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border: 2px solid #e5e7eb;
            border-radius: 6px;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 15px;
            border-bottom: 2px solid #003366;
            padding-bottom: 10px;
        }}
        
        .company-name {{
            font-size: 22px;
            font-weight: bold;
            color: #003366;
            margin-bottom: 3px;
            letter-spacing: 0.5px;
        }}
        
        .document-title {{
            font-size: 16px;
            color: #555;
            font-weight: 600;
        }}
        
        .employee-info {{
            background: #f8f9fa;
            padding: 8px;
            border-radius: 4px;
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
        }}
        
        .employee-info .info-item {{
            margin: 3px 8px;
            font-size: 12px;
        }}
        
        .employee-info .label {{
            font-weight: 600;
            color: #555;
        }}
        
        .employee-info .value {{
            color: #1a1a1a;
        }}
        
        .section {{
            margin-bottom: 12px;
        }}
        
        .section-header {{
            background: #003366;
            color: white;
            padding: 6px 10px;
            font-size: 13px;
            font-weight: bold;
            border-radius: 3px;
            margin-bottom: 8px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 8px;
        }}
        
        table th,
        table td {{
            padding: 6px 8px;
            text-align: left;
            border: 1px solid #e5e7eb;
        }}
        
        table th {{
            background: #f3f4f6;
            font-weight: 600;
            color: #374151;
            font-size: 11px;
        }}
        
        table td {{
            font-size: 11px;
        }}
        
        .amount {{
            font-weight: 600;
            color: #059669;
        }}
        
        .deduction {{
            color: #dc2626;
        }}
        
        .summary {{
            background: #f0f9ff;
            border: 2px solid #0284c7;
            border-radius: 4px;
            padding: 10px;
            margin-top: 10px;
        }}
        
        .summary-row {{
            display: flex;
            justify-content: space-between;
            padding: 4px 0;
            font-size: 12px;
        }}
        
        .summary-row.total {{
            border-top: 2px solid #0284c7;
            margin-top: 6px;
            padding-top: 8px;
            font-weight: bold;
            font-size: 14px;
            color: #059669;
        }}
        
        .formula {{
            color: #6b7280;
            font-size: 10px;
            font-style: italic;
        }}
        
        .signatures {{
            margin-top: 20px;
            display: flex;
            justify-content: space-between;
        }}
        
        .signature-block {{
            width: 45%;
            border-top: 1px solid #d1d5db;
            padding-top: 6px;
        }}
        
        .signature-label {{
            font-weight: 600;
            color: #374151;
            margin-bottom: 10px;
            font-size: 11px;
        }}
        
        .signature-line {{
            border-bottom: 1px solid #9ca3af;
            margin-bottom: 3px;
            height: 20px;
        }}
        
        .footer {{
            margin-top: 15px;
            padding-top: 10px;
            border-top: 1px solid #e5e7eb;
            text-align: center;
            color: #6b7280;
            font-size: 9px;
        }}
        
        .cycle-id {{
            font-weight: 600;
            color: #374151;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div class="company-name">TANSEEQ TAX CONSULTANCY</div>
            <div class="document-title">Salary Statement</div>
        </div>
        
        <!-- Employee Information -->
        <div class="employee-info">
            <div class="info-item">
                <span class="label">Date:</span>
                <span class="value">{current_date}</span>
            </div>
            <div class="info-item">
                <span class="label">Employee Name:</span>
                <span class="value">{emp_name}</span>
            </div>
            <div class="info-item">
                <span class="label">Employee ID:</span>
                <span class="value">{emp_id}</span>
            </div>
            <div class="info-item">
                <span class="label">Period:</span>
                <span class="value">{period}</span>
            </div>
        </div>
        
        <!-- Section 1: Deductions Breakdown -->
        <div class="section">
            <div class="section-header">1) DEDUCTIONS BREAKDOWN</div>
            <table>
                <thead>
                    <tr>
                        <th>Type</th>
                        <th>Description</th>
                        <th>Amount (AED)</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    # Add deduction rows
    if admin_deduction > 0:
        html += f"""
                    <tr>
                        <td>Administrative</td>
                        <td>Manual Administrative Deduction</td>
                        <td class="deduction">{admin_deduction:,.2f}</td>
                    </tr>
        """
    
    if attendance_deduction > 0:
        html += f"""
                    <tr>
                        <td>Attendance</td>
                        <td>Late Arrivals, Early Departures & Absences</td>
                        <td class="deduction">{attendance_deduction:,.2f}</td>
                    </tr>
        """
    
    if advance_deduction > 0:
        html += f"""
                    <tr>
                        <td>Advance</td>
                        <td>Salary Advance Deduction</td>
                        <td class="deduction">{advance_deduction:,.2f}</td>
                    </tr>
        """
    
    if total_deductions == 0:
        html += """
                    <tr>
                        <td colspan="3" style="text-align: center; color: #059669; font-weight: 600;">
                            No Deductions for this Period
                        </td>
                    </tr>
        """
    
    html += f"""
                </tbody>
            </table>
        </div>
        
        <!-- Section 2: Net Salary Summary -->
        <div class="section">
            <div class="section-header">2) NET SALARY SUMMARY</div>
            <div class="summary">
                <div class="summary-row">
                    <span>Gross Salary:</span>
                    <span class="amount">AED {gross_salary:,.2f}</span>
                </div>
                <div class="summary-row">
                    <span>Total Deductions:</span>
                    <span class="deduction">- AED {total_deductions:,.2f}</span>
                </div>
                <div class="summary-row total">
                    <span>NET PAYABLE:</span>
                    <span>AED {net_payable:,.2f}</span>
                </div>
            </div>
        </div>
        
        <!-- Signatures -->
        <div class="signatures">
            <div class="signature-block">
                <div class="signature-label">HR Signature:</div>
                <div class="signature-line"></div>
                <div style="margin-top: 10px;">
                    <strong>Name:</strong> __________________
                </div>
                <div style="margin-top: 5px;">
                    <strong>Date:</strong> ____/____/________
                </div>
            </div>
            
            <div class="signature-block">
                <div class="signature-label">Employee Signature:</div>
                <div class="signature-line"></div>
                <div style="margin-top: 10px;">
                    <strong>Name:</strong> __________________
                </div>
                <div style="margin-top: 5px;">
                    <strong>Date:</strong> ____/____/________
                </div>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <p>This salary statement has been auto-generated from the Payroll Ledger system</p>
            <p>in accordance with company policies.</p>
            <p class="cycle-id">Payroll Cycle ID: {cycle_id}</p>
        </div>
    </div>
</body>
</html>
    """
    
    return html
