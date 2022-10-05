import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # l10n_bo_dfe_service_provider = fields.Selection(related='company_id.l10n_bo_dfe_service_provider', readonly=False,
    #                                                 help='Please select your company service provider for DFE service.')
    # # l10n_cl_activity_description = fields.Char(
    # #     string='Glosa Giro', related='company_id.l10n_cl_activity_description', readonly=False)
    # l10n_bo_company_activity_ids = fields.Many2many('l10n_bo.company.activities', string='Activities Names',
    #                                                 related='company_id.l10n_bo_company_activity_ids', readonly=False,
    #                                                 help='Please select the SIN registered economic activities codes for the company')

    l10n_bo_sync_time = fields.Datetime(
        string='Sync Time', related='company_id.l10n_bo_sync_time',
        help='Set the synchronization time for the SIN values', readonly=False)
    # SIN Codes
    l10n_bo_system_code = fields.Char(
        string='System Code', related='company_id.l10n_bo_system_code',
        help='Code given by SIN in order to emit invoices', readonly=False)
    l10n_bo_token = fields.Text(
        string='Token Api', related='company_id.l10n_bo_token', help='Token Api delegated', readonly=False)

    l10n_bo_invoicing_modality = fields.Many2one(
        'modalities.siat', related='company_id.l10n_bo_invoicing_modality', string='Modality Selection', readonly=False)
    l10n_bo_sector_type = fields.Many2one(
        'sector.types', related='company_id.l10n_bo_sector_type', string='Sector Type Selection', readonly=False)
    l10n_bo_ambience = fields.Many2one('ambience.siat', related='company_id.l10n_bo_ambience', string='Ambience',
                                       readonly=False)
    l10n_bo_invoice_package_number = fields.Integer(
        string='Package Number', related='company_id.l10n_bo_invoice_package_number',
        help='Set the number of invoices per package', readonly=False)
    module_l10n_bo_reports = fields.Boolean(string='Accounting Reports', related='company_id.module_l10n_bo_reports',
                                            readonly=False)
    l10n_bo_invoicing_type = fields.Boolean('Invoicing Type', related='company_id.l10n_bo_invoicing_type',
                                            readonly=False)
