from odoo import models, fields, api
from odoo.exceptions import UserError

class StudentEmailWizard(models.TransientModel):
    _name = 'student.email.wizard'
    _description = 'Send Student or Department Report by Email'

    # Step 1.1: Add Selection Field
    report_type = fields.Selection([
        ('single', 'Single Student'),
        ('department', 'Department Wise')
    ], string='Report Type', default='single', required=True)

    # Step 1.2: Add Related Fields
    student_id = fields.Many2one('student', string='Student')
    department_id = fields.Many2one('department', string='Department')

    email_to = fields.Char(string='Recipient Email', required=True)
    phone = fields.Char(string='Phone')

    # Step 1.3: Add onchange to clear irrelevant field
    @api.onchange('report_type')
    def _onchange_report_type(self):
        """When report type changes, clear the other field to avoid confusion."""
        if self.report_type == 'single':
            self.department_id = False
        elif self.report_type == 'department':
            self.student_id = False

    # Step 1.4: Add button logic for sending email
    def action_send_email(self):
        """Validate data and send email."""
        for wizard in self:
            if not wizard.email_to:
                raise UserError("Recipient email is required!")

            # Validate based on report type
            if wizard.report_type == 'single' and not wizard.student_id:
                raise UserError("Please select a student for the single report.")
            if wizard.report_type == 'department' and not wizard.department_id:
                raise UserError("Please select a department for the department report.")

            # Simulated success message
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success!',
                    'message': f'Report sent successfully to {wizard.email_to}.',
                    'type': 'success',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
