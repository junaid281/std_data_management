import pandas as pd
import base64
from io import BytesIO
from xhtml2pdf import pisa
from odoo import models, fields, api
from odoo.exceptions import UserError


# -------------------------------------------------------------------
# Student Model
# -------------------------------------------------------------------
class Student(models.Model):
    _name = 'student'
    _description = 'Students Data Management System'

    # -----------------------------
    # Core Fields
    # -----------------------------
    active = fields.Boolean(string='Active', default=True)
    name = fields.Char(string='Name', required=True)
    father_name = fields.Char(string='Father Name')
    age = fields.Integer(string='Age', required=True)
    grade = fields.Char(string='Grade')
    address = fields.Text(string='Address')

    department_id = fields.Many2one(
        comodel_name='department',
        string='Department',
        required=True
    )

    about_education = fields.One2many(
        comodel_name='education',
        inverse_name='connecting_field',
        string='Education Details'
    )

    total_marks = fields.Float(string='Total Marks', required=True)
    obtained_marks = fields.Float(string='Obtained Marks', required=True)
    percentage = fields.Float(string='Percentage', compute='compute_percentage', store=True)

    gender = fields.Selection(
        [('male', 'Male'), ('female', 'Female')],
        string='Gender',
    )

    # -----------------------------
    # Computed Field
    # -----------------------------
    @api.depends('total_marks', 'obtained_marks')
    def compute_percentage(self):
        for record in self:
            if record.total_marks > 0:
                record.percentage = (record.obtained_marks / record.total_marks) * 100
            else:
                record.percentage = 0

    # -----------------------------
    # Actions
    # -----------------------------
    def action_save_record(self):
        """Show success popup when record saved"""
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Saved!',
                'message': 'Student record has been saved successfully.',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_delete_record(self):
        """Archive (deactivate) record"""
        self.ensure_one()
        self.active = False
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Archived!',
                'message': f'Student {self.name} has been archived.',
                'type': 'warning',
                'sticky': False,
            }
        }

    def action_restore_record(self):
        """Restore archived record"""
        self.ensure_one()
        self.active = True
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Restored!',
                'message': f'Student {self.name} has been restored.',
                'type': 'success',
                'sticky': False,
            }
        }

    # -----------------------------
    # Report Choice Wizard
    # -----------------------------
    def action_open_report_choice(self):
        """Open a wizard to choose between single student report or department report"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Generate Report',
            'res_model': 'student.report.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_student_id': self.id,
                'default_report_type': 'single',
                'default_department_id': self.department_id.id,
            }
        }

    # -----------------------------
    # Send Email Wizard
    # -----------------------------
    def action_open_send_email_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'student.email.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_report_type': 'single',
                'default_student_id': self.id,
                'default_email_to': getattr(self, 'email', '')  # if student has email field
        },
    }


# -------------------------------------------------------------------
# Education Model
# -------------------------------------------------------------------
class Education(models.Model):
    _name = 'education'
    _description = 'Education History'

    active = fields.Boolean(string='Active', default=True)
    connecting_field = fields.Many2one('student', string='Student', required=True)
    institute = fields.Many2one('institute', string='Institute', required=True)
    degree = fields.Many2one('degree', string='Degree', required=True)
    passing_year = fields.Integer(string='Passing Year')


# -------------------------------------------------------------------
# Department Model
# -------------------------------------------------------------------
class Department(models.Model):
    _name = 'department'
    _description = 'Department Information'

    name = fields.Char(string='Department Name', required=True)

    @api.model
    def init(self):
        """Initialize default departments"""
        department_names = ['MATH', 'BSCS', 'PHYSICS', 'BBA', 'COMMERCE', 'ALL']
        for name in department_names:
            if not self.search([('name', '=', name)], limit=1):
                self.create({'name': name})


# -------------------------------------------------------------------
# Institute Model
# -------------------------------------------------------------------
class Institute(models.Model):
    _name = 'institute'
    _description = 'Institute Information'

    name = fields.Char(string='Institute Name', required=True)

    @api.model
    def init(self):
        """Initialize default institutes"""
        institute_names = ['Superior', 'Aspire', 'Degree', 'GUCF', 'Punjab']
        for name in institute_names:
            if not self.search([('name', '=', name)], limit=1):
                self.create({'name': name})


# -------------------------------------------------------------------
# Degree Model
# -------------------------------------------------------------------
class Degree(models.Model):
    _name = 'degree'
    _description = 'Degree Information'

    name = fields.Char(string='Degree Name', required=True)

    @api.model
    def init(self):
        """Initialize default degrees"""
        degree_names = ['Matric', 'FSc', 'BSc', 'MPhil']
        for name in degree_names:
            if not self.search([('name', '=', name)], limit=1):
                self.create({'name': name})
