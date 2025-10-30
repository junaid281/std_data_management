from odoo import models, fields, api
from odoo.exceptions import UserError


class StudentReportWizard(models.TransientModel):
    _name = 'student.report.wizard'
    _description = 'Student Report Wizard'

    report_type = fields.Selection([
        ('single', 'Single Student'),
        ('department', 'Department Wise'),
    ], string='Report Type', required=True, default='single')

    student_id = fields.Many2one('student', string='Student')
    department_id = fields.Many2one('department', string='Department')

    # -------------------------------------------------------
    # Main Action Method
    # -------------------------------------------------------
    def action_generate_report(self):
        """Generate report based on selected type."""
        self.ensure_one()

        report_model = self.env['report.student_reports']

        # -------------------------
        # SINGLE STUDENT REPORT
        # -------------------------
        if self.report_type == 'single':
            if not self.student_id:
                raise UserError("Please select a student.")
            try:
                return report_model.generate_single_student_report(self.student_id)
            except Exception as e:
                raise UserError(f"Error generating single student report:\n{str(e)}")

        # -------------------------
        # DEPARTMENT REPORT
        # -------------------------
        elif self.report_type == 'department':
            if not self.department_id:
                raise UserError("Please select a department.")
            try:
                return report_model.print_department_report(self.department_id.id)
            except Exception as e:
                raise UserError(f"Error generating department report:\n{str(e)}")

        # -------------------------
        # SAFETY CATCH
        # -------------------------
        else:
            raise UserError("Invalid report type selected.")
