from odoo import fields, models


class CafcLog(models.Model):
    _name = 'cafc.log'
    _description = 'cufd'

    name = fields.Char('Cafc Code')
    begin_date = fields.Datetime(string='Begin Date')
    end_date = fields.Datetime(string='End Date')
    dosage_ids = fields.One2many('invoice.dosage', 'cafc_log_id', string='Invoice dosage')
    active = fields.Boolean(
        'Active', help='Allows you to hide the cufd without removing it.', default=True)
