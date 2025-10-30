import base64
from io import BytesIO
import pandas as pd
from xhtml2pdf import pisa
from odoo import models, api
from odoo.exceptions import UserError


class StudentReport(models.AbstractModel):
    _name = 'report.student_reports'
    _description = 'Student Reports (PDF Generation with Pandas)'

    @api.model
    def print_department_report(self, department_id=None):
        """Generate department-wise student PDF report using pandas."""

        Department = self.env['department']
        Student = self.env['student']

        # -------------------------------------------------------
        # 1️⃣ Get department(s)
        # -------------------------------------------------------
        if not department_id:
            departments = Department.search([])
            dept_name = "ALL"
        else:
            departments = Department.browse(department_id)
            dept_name = departments.name or "ALL"

        if not departments:
            raise UserError("No departments found.")

        # -------------------------------------------------------
        # 2️⃣ Fetch all students (filtered if needed)
        # -------------------------------------------------------
        if dept_name == "ALL":
            students = Student.search([])
        else:
            students = Student.search([('department_id', '=', department_id)])

        # -------------------------------------------------------
        # 3️⃣ Define STANDARDIZED columns (CRITICAL FOR CONSISTENCY)
        # -------------------------------------------------------
        STANDARD_COLUMNS = [
            'Name', 
            'Father Name', 
            'Age', 
            'Grade', 
            'Total Marks', 
            'Obtained Marks', 
            'Percentage'
        ]

        # -------------------------------------------------------
        # 4️⃣ Build DataFrame from student records with FALLBACK values
        # -------------------------------------------------------
        data = []
        if students:
            for s in students:
                data.append({
                    'Department': s.department_id.name if s.department_id else 'No Department',
                    'Name': s.name or '',
                    'Father Name': s.father_name or '',
                    'Age': s.age or '',
                    'Grade': s.grade or '',
                    'Total Marks': s.total_marks or '',
                    'Obtained Marks': s.obtained_marks or '',
                    'Percentage': s.percentage or 0.0,
                })
            df = pd.DataFrame(data)
        else:
            # Create empty DataFrame with proper structure when no data
            df = pd.DataFrame(columns=['Department'] + STANDARD_COLUMNS)

        # -------------------------------------------------------
        # 5️⃣ Generate HTML with ROBUST table structure
        # -------------------------------------------------------
        html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    padding: 20px;
                }}
                .report-title {{
                    text-align: center;
                    font-size: 22px;
                    font-weight: bold;
                    margin-bottom: 15px;
                    color: #2a2a2a;
                }}
                .department-title {{
                    background-color: #555;
                    color: white;
                    padding: 8px;
                    font-size: 16px;
                    border-radius: 4px;
                    margin-top: 20px;
                    margin-bottom: 10px;
                }}
                .student-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                }}
                .student-table th, .student-table td {{
                    border: 1px solid #bbb;
                    padding: 8px;
                    text-align: center;
                    font-size: 12px;
                    min-width: 80px;
                }}
                .student-table th {{
                    background-color: #333;
                    color: white;
                    font-weight: bold;
                }}
                .student-table td {{
                    background-color: #f9f9f9;
                }}
                .no-data {{
                    text-align: center;
                    color: #666;
                    font-style: italic;
                    padding: 20px;
                    background-color: #f0f0f0;
                    border: 1px solid #ddd;
                }}
                .empty-row td {{
                    background-color: #fff;
                    color: #999;
                    font-style: italic;
                }}
            </style>
        </head>
        <body>
            <div class="report-title">Department Report - {dept_name}</div>
        """

        # -------------------------------------------------------
        # 6️⃣ Handle both scenarios: With data and Without data
        # -------------------------------------------------------
        if df.empty:
            # Scenario 1: No data available - Show structured empty table
            html += f"<div class='department-title'>Department: {dept_name}</div>"
            html += "<table class='student-table'>"
            
            # Create table header
            html += "<tr>"
            for col in STANDARD_COLUMNS:
                html += f"<th>{col}</th>"
            html += "</tr>"
            
            # Show empty data message in proper table structure
            html += f"""
            <tr class='empty-row'>
                <td colspan='{len(STANDARD_COLUMNS)}' class='no-data'>
                    No student records found for this department
                </td>
            </tr>
            """
            html += "</table>"
            
        else:
            # Scenario 2: Data available - Group by department
            for dept_name, group in df.groupby('Department'):
                html += f"<div class='department-title'>Department: {dept_name}</div>"
                
                # Create table with STANDARDIZED columns
                html += "<table class='student-table'><tr>"
                for col in STANDARD_COLUMNS:
                    html += f"<th>{col}</th>"
                html += "</tr>"

                # Add student data with PROPER NULL HANDLING
                if group.empty:
                    # Empty department within non-empty dataset
                    html += f"""
                    <tr class='empty-row'>
                        <td colspan='{len(STANDARD_COLUMNS)}' class='no-data'>
                            No students in this department
                        </td>
                    </tr>
                    """
                else:
                    for _, row in group.iterrows():
                        html += "<tr>"
                        for col in STANDARD_COLUMNS:
                            value = self._format_cell_value(row, col)
                            html += f"<td>{value}</td>"
                        html += "</tr>"
                html += "</table>"

        html += "</body></html>"

        # -------------------------------------------------------
        # 7️⃣ Generate PDF
        # -------------------------------------------------------
        pdf_file = BytesIO()
        try:
            pisa_status = pisa.CreatePDF(html, dest=pdf_file)
            if pisa_status.err:
                raise UserError(f"PDF generation error: {pisa_status.err}")
            pdf_data = pdf_file.getvalue()
        except Exception as e:
            raise UserError(f"PDF creation failed: {str(e)}")
        finally:
            pdf_file.close()

        # -------------------------------------------------------
        # 8️⃣ Create attachment and return download action
        # -------------------------------------------------------
        attachment = self.env['ir.attachment'].create({
            'name': f'Department_Report_{dept_name.replace(" ", "_")}.pdf',
            'type': 'binary',
            'datas': base64.b64encode(pdf_data).decode('utf-8'),
            'mimetype': 'application/pdf',
            'res_model': 'student',
            'res_id': 0,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content/{attachment.id}?download=true",
            'target': 'self',
        }

    def _format_cell_value(self, row, column_name):
        """
        Format cell values consistently to prevent misalignment
        """
        value = row[column_name]
        
        # Handle None/NaN values
        if pd.isna(value) or value is None or value == '':
            return '-'  # Consistent placeholder for empty values
        
        # Format percentage values
        if column_name == 'Percentage':
            try:
                if isinstance(value, (int, float)):
                    return f"{float(value):.2f}%"
                elif isinstance(value, str) and '%' not in value:
                    return f"{float(value):.2f}%"
                else:
                    return str(value)
            except (ValueError, TypeError):
                return str(value)
        
        # Format numeric values
        if column_name in ['Age', 'Total Marks', 'Obtained Marks']:
            try:
                if isinstance(value, (int, float)):
                    return f"{float(value):.1f}" if float(value) != int(value) else f"{int(value)}"
            except (ValueError, TypeError):
                pass
        
        return str(value)

    # SINGLE STUDENT REPORT
    # -------------------------------------------------------------
    def generate_single_student_report(self, student):
        """Generate a PDF for one student record with standardized columns."""
        
        # -------------------------------------------------------
        # 1️⃣ Define STANDARDIZED COLUMNS for consistent structure
        # -------------------------------------------------------
        
        # Personal Information Standard Columns
        PERSONAL_INFO_COLUMNS = [
            'Name', 
            'Father Name', 
            'Age', 
            'Gender', 
            'Department', 
            'Grade'
        ]
        
        # Academic Information Standard Columns  
        ACADEMIC_INFO_COLUMNS = [
            'Total Marks',
            'Obtained Marks', 
            'Percentage'
        ]
        
        # Education History Standard Columns
        EDUCATION_COLUMNS = [
            'Institute',
            'Degree', 
            'Passing Year'
        ]

        # -------------------------------------------------------
        # 2️⃣ Build Personal Information Data with STANDARD columns
        # -------------------------------------------------------
        personal_data = []
        personal_row = {}
        
        # Map all available data, but we'll display only STANDARD columns
        all_personal_data = {
            'Name': student.name or '-',
            'Father Name': student.father_name or '-',
            'Age': student.age or '-',
            'Gender': dict(student._fields['gender'].selection).get(student.gender, '-'),
            'Department': student.department_id.name if student.department_id else '-',
            'Grade': student.grade or '-',
            'Total Marks': student.total_marks or '-',
            'Obtained Marks': student.obtained_marks or '-',
            'Percentage': f"{student.percentage:.2f}%" if student.percentage else '0.00%',
            'Address': student.address or '-'
        }
        
        # Only include STANDARD columns in the display
        for col in PERSONAL_INFO_COLUMNS:
            personal_row[col] = all_personal_data.get(col, '-')
        
        personal_data.append(personal_row)
        df_personal = pd.DataFrame(personal_data)

        # -------------------------------------------------------
        # 3️⃣ Build Academic Information Data with STANDARD columns
        # -------------------------------------------------------
        academic_data = []
        academic_row = {}
        
        for col in ACADEMIC_INFO_COLUMNS:
            academic_row[col] = all_personal_data.get(col, '-')
        
        academic_data.append(academic_row)
        df_academic = pd.DataFrame(academic_data)

        # -------------------------------------------------------
        # 4️⃣ Build Education Data with STANDARD columns
        # -------------------------------------------------------
        education_data = []
        for edu in student.about_education:
            edu_row = {}
            edu_row['Institute'] = edu.institute.name if edu.institute else '-'
            edu_row['Degree'] = edu.degree.name if edu.degree else '-'
            edu_row['Passing Year'] = edu.passing_year or '-'
            education_data.append(edu_row)
        
        # Create empty DataFrame with standard columns if no education data
        if not education_data:
            df_education = pd.DataFrame(columns=EDUCATION_COLUMNS)
        else:
            df_education = pd.DataFrame(education_data)

        # -------------------------------------------------------
        # 5️⃣ Generate HTML with STANDARDIZED table structure
        # -------------------------------------------------------
        html = f"""
        <html>
        <head>
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    background-color: #f9f9f9; 
                    margin: 20px; 
                }}
                .report-header {{ 
                    text-align: center; 
                    background-color: #4a4a4a; 
                    color: white; 
                    padding: 15px; 
                    border-radius: 8px;
                    margin-bottom: 20px;
                }}
                .section-title {{ 
                    color: #333; 
                    border-bottom: 2px solid #ddd; 
                    margin-top: 30px;
                    padding-bottom: 5px;
                }}
                .data-table {{ 
                    width: 100%; 
                    border-collapse: collapse; 
                    background-color: white; 
                    margin-bottom: 20px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }}
                .data-table th, .data-table td {{ 
                    border: 1px solid #ddd; 
                    padding: 12px; 
                    text-align: left; 
                }}
                .data-table th {{ 
                    background-color: #4a4a4a; 
                    color: white;
                    font-weight: bold;
                }}
                .data-table td {{
                    background-color: #fafafa;
                }}
                .no-data {{ 
                    text-align: center; 
                    color: #666; 
                    font-style: italic; 
                    padding: 20px;
                    background-color: #f0f0f0;
                    border: 1px solid #ddd;
                }}
                .empty-row td {{
                    background-color: #fff;
                    color: #999;
                    font-style: italic;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="report-header">
                <h1>Student Report - {student.name or 'Unknown Student'}</h1>
            </div>
            
            <h2 class="section-title">Personal Information</h2>
        """
        
        # Personal Information Table
        html += "<table class='data-table'>"
        html += "<tr>"
        for col in PERSONAL_INFO_COLUMNS:
            html += f"<th>{col}</th>"
        html += "</tr>"
        
        if not df_personal.empty:
            for _, row in df_personal.iterrows():
                html += "<tr>"
                for col in PERSONAL_INFO_COLUMNS:
                    value = row[col] if pd.notna(row[col]) else '-'
                    html += f"<td>{value}</td>"
                html += "</tr>"
        else:
            html += f"<tr class='empty-row'><td colspan='{len(PERSONAL_INFO_COLUMNS)}'>No personal information available</td></tr>"
        html += "</table>"
        
        # Academic Information Table
        html += "<h2 class='section-title'>Academic Performance</h2>"
        html += "<table class='data-table'>"
        html += "<tr>"
        for col in ACADEMIC_INFO_COLUMNS:
            html += f"<th>{col}</th>"
        html += "</tr>"
        
        if not df_academic.empty:
            for _, row in df_academic.iterrows():
                html += "<tr>"
                for col in ACADEMIC_INFO_COLUMNS:
                    value = row[col] if pd.notna(row[col]) else '-'
                    html += f"<td>{value}</td>"
                html += "</tr>"
        else:
            html += f"<tr class='empty-row'><td colspan='{len(ACADEMIC_INFO_COLUMNS)}'>No academic information available</td></tr>"
        html += "</table>"
        
        # Education History Table
        html += "<h2 class='section-title'>Education History</h2>"
        html += "<table class='data-table'>"
        html += "<tr>"
        for col in EDUCATION_COLUMNS:
            html += f"<th>{col}</th>"
        html += "</tr>"
        
        if not df_education.empty:
            for _, row in df_education.iterrows():
                html += "<tr>"
                for col in EDUCATION_COLUMNS:
                    value = row[col] if pd.notna(row[col]) else '-'
                    html += f"<td>{value}</td>"
                html += "</tr>"
        else:
            html += f"<tr class='empty-row'><td colspan='{len(EDUCATION_COLUMNS)}'>No education history available</td></tr>"
        html += "</table>"
        
        html += "</body></html>"

        # -------------------------------------------------------
        # 6️⃣ Generate PDF
        # -------------------------------------------------------
        pdf_file = BytesIO()
        try:
            pisa_status = pisa.CreatePDF(html, dest=pdf_file)
            if pisa_status.err:
                raise UserError(f"PDF generation error: {pisa_status.err}")
            pdf_data = pdf_file.getvalue()
        except Exception as e:
            raise UserError(f"PDF creation failed: {str(e)}")
        finally:
            pdf_file.close()

        # -------------------------------------------------------
        # 7️⃣ Save attachment
        # -------------------------------------------------------
        attachment = student.env['ir.attachment'].create({
            'name': f'{student.name or "Student"}_Report.pdf',
            'type': 'binary',
            'datas': base64.b64encode(pdf_data),
            'res_model': 'student',
            'res_id': student.id,
            'mimetype': 'application/pdf',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content/{attachment.id}?download=true",
            'target': 'self',
        }