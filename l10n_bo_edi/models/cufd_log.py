from odoo import fields, models


class CufdLog(models.Model):
    _name = 'cufd.log'
    _description = 'cufd'

    name = fields.Char('Cufd Log')
    id_cufd = fields.Integer(string='Cufd ID')
    cufd = fields.Text(string='CUFD')
    control_code = fields.Text(string='Control Code')
    begin_date = fields.Datetime(string='Begin Date')
    end_date = fields.Datetime(string='End Date')
    invoice_number = fields.Integer(string='Invoice Number')
    street = fields.Char('Street')
    selling_point_id = fields.Many2one('selling.point', string='Selling Point')
    dosage_ids = fields.One2many('invoice.dosage', 'cufd_log_id', string='Invoice dosage')
    active = fields.Boolean(
        'Active', help='Allows you to hide the cufd without removing it.', default=True)
