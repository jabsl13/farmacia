from odoo import fields, models, api


class BoEdiParams(models.Model):
    _name = 'bo.edi.params'
    _description = 'BO EDI TEST Params'

    param_code = fields.Integer(string='Param Code')
    name = fields.Text(string='Name')
    value = fields.Text(string='Value')
    active = fields.Boolean(
        'Active', help='Allows you to hide the param without removing it.', default=True)
