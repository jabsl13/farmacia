from odoo import _, fields, models
from odoo.exceptions import UserError


class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_bo_dfe_service_provider = fields.Selection([
        ('SINTEST', 'SIN - Test'),
        ('SIN', 'SIN - Production')], 'DFE Service Provider',
        help='Please select your company service provider for DFE service.')
    l10n_bo_company_activity_ids = fields.Many2many('l10n_bo.company.activities', string='Activities Names',
                                                    help='Please select the SIN registered economic activities codes for the company',
                                                    readonly=False)
    l10n_bo_sync_time = fields.Datetime(string='Sync Time', help='Set the synchronization time for the SIN values')
    l10n_bo_system_code = fields.Char(
        string='System Code', help='Code given by SIN in order to emit invoices')
    l10n_bo_token = fields.Text(
        string='Token Api Delegated', help='Token Api delegated')
    l10n_bo_invoicing_modality = fields.Many2one(
        'modalities.siat', string='Modality Selection')
    l10n_bo_sector_type = fields.Many2one(
        'sector.types', string='Sector Type Selection')
    l10n_bo_ambience = fields.Many2one('ambience.siat', string='Ambience')
    l10n_bo_invoice_package_number = fields.Integer(
        string='Package Number', help='Set the number of invoices per package')
    module_l10n_bo_reports = fields.Boolean(string='Accounting Reports')
    l10n_bo_invoicing_type = fields.Boolean('Invoicing Type')
    l10n_bo_certificate_ids = fields.One2many(
        'l10n_bo.certificate', 'company_id', string='Certificates (BO)')

    def _get_digital_signature(self, user_id=None):
        if user_id is not None:
            user_certificates = self.sudo().l10n_bo_certificate_ids.filtered(lambda x: x.user_id.id == user_id and x.company_id.id == self.id)
            if user_certificates:
                return user_certificates[0]
        shared_certificates = self.sudo().l10n_bo_certificate_ids.filtered(
            lambda x: not x.user_id and x.company_id.id == self.id)
        if not shared_certificates:
            raise UserError(_('There is not a valid certificate for the company: %s') % self.name)

        return shared_certificates[0]
