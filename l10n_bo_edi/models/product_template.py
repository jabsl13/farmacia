from odoo import fields, models
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # internal_code = fields.Integer(string='Internal Code') # Currently using "Internal Reference"
    sin_item = fields.Many2one('sin.items', string='SIN Item related')
    measure_unit = fields.Many2one(
        'measure.unit', string='SIN Measure Unit related')
