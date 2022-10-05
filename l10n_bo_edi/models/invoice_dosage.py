from odoo import fields, models
from datetime import datetime


class InvoiceDosage(models.Model):
    _name = 'invoice.dosage'
    _description = 'BO SIN invoice dosage'

    name = fields.Char('Invoice dosage', required=True)
    code = fields.Text('Code')
    auth_number = fields.Text('Authorization Number')
    end_date = fields.Date('Dosage Deadline', required=True)
    selling_point_id = fields.Many2one('selling.point', string='Selling Point', required=True)
    invoice_number = fields.Integer('Invoice Number', default=1, required=True)
    invoice_number_dc = fields.Integer('Invoice Number Debit/Credit', default=1, required=True)
    key = fields.Text('Dosage Key')
    invoice_caption_id = fields.Many2one('invoice.caption', 'Invoice Caption')
    cuis = fields.Char('Unique CUIS System')
    cufd_log_id = fields.Many2one('cufd.log', string='CUFD current')
    cafc_log_id = fields.Many2one('cafc.log', string='CAFC current')
    sector_siat_id = fields.Many2one('document.sec.type', string='Document Type')
    user_ids = fields.Many2many('res.users', string="Users Dosage", required=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    active = fields.Boolean(
        'Active', default=True)

    def get_cuis_dosage(self):
        ambiente = self.company_id.l10n_bo_ambience.id_ambience
        modalidad = self.company_id.l10n_bo_invoicing_modality.id_modality
        codSistema = self.company_id.l10n_bo_system_code
        codSucursal = self.selling_point_id.branch_office_id.id_branch_office
        puntoVenta = self.selling_point_id.id_selling_point
        nit = self.company_id.vat
        self.cuis = self.env['sin.sync'].get_cuis(ambiente, modalidad, codSistema, codSucursal, puntoVenta, nit,
                                                  self.company_id)

    def get_cufd_dosage(self):
        ambiente = self.company_id.l10n_bo_ambience.id_ambience
        modalidad = self.company_id.l10n_bo_invoicing_modality.id_modality
        codSistema = self.company_id.l10n_bo_system_code
        codSucursal = self.selling_point_id.branch_office_id.id_branch_office
        puntoVenta = self.selling_point_id.id_selling_point
        nit = self.company_id.vat
        cuis = self.cuis
        result_cufd = self.env['sin.sync'].get_cufd(ambiente, modalidad, codSistema, codSucursal, puntoVenta, nit,
                                                    self.company_id, cuis)
        val_cufd = {
            'name': result_cufd.codigo,
            'cufd': result_cufd.codigo,
            'control_code': result_cufd.codigoControl,
            'end_date': datetime.strptime(str(result_cufd.fechaVigencia)[:19], "%Y-%m-%d %H:%M:%S"),
            'selling_point_id': self.selling_point_id.id,
            'street': result_cufd.direccion,
        }
        cufd_ver = self.env['cufd.log'].create(val_cufd)
        self.cufd_log_id = cufd_ver.id
