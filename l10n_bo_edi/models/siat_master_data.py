from odoo import api, fields, models


class ActivivityDocSector(models.Model):
    _name = 'activity.doc.sector'
    _description = 'Relation Model between Sectors and Activities'

    name = fields.Char('Nombre Actividad')
    activity_code = fields.Char('Activity Code')
    sector_doc_code = fields.Char('Sector Doc Code')
    sector_doc_type = fields.Char('Sector Doc type')


class AmbienceSiat(models.Model):
    _name = 'ambience.siat'
    _description = 'ambience'
    name = fields.Char('Ambience')
    id_ambience = fields.Integer(string='Ambiance Code')
    description = fields.Text(string='Description')
    current_ambience = fields.One2many(
        'res.config.settings', 'l10n_bo_ambience', string='Current Ambience')
    active = fields.Boolean(
        'Active', help='Allows you to hide the ambiance without removing it.', default=True)


class BoediDateTime(models.Model):
    _name = 'boedi.date.time'
    _description = 'Date and time data sync with SIN'

    name = fields.Char(string='Date sync SIN')
    date_time = fields.Text(string='Date and Time')
    active = fields.Boolean(
        'Active', help='Allows you to hide the date_time without removing it.', default=True)


class BranchOffice(models.Model):
    _name = 'branch.office'
    _description = 'Sucursales'

    name = fields.Char(string='Branch office')
    id_branch_office = fields.Integer(
        string='Branch Office Code', required=True)
    description = fields.Text(string='Description', required=True)
    address = fields.Text(string='Address', required=False)
    selling_point_ids = fields.One2many(
        'selling.point', 'branch_office_id', string='Selling Points')
    user_ids = fields.One2many(
        'res.users', 'l10n_bo_branch_office_id', string='Users')
    active = fields.Boolean(
        'Active', help='Allows you to hide the branch office without removing it.', default=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)


class SellingPoint(models.Model):
    _name = 'selling.point'
    _description = 'selling_point'

    name = fields.Char('Selling point')
    id_selling_point = fields.Integer(
        string='Selling Point Code', required=True)
    description = fields.Text(string='Description')
    branch_office_id = fields.Many2one('branch.office', string='Branch Office', ondelete='cascade', required=True)
    user_ids = fields.One2many(
        'res.users', 'l10n_bo_selling_point_id', string='Users in Charge')
    cufd_ids = fields.One2many(
        'cufd.log', 'selling_point_id', string='Cufd Related Codes')
    invoice_dosage_ids = fields.One2many(
        'invoice.dosage', 'cufd_log_id', string='Invoice Dosages')
    active = fields.Boolean(
        'Active', help='Allows you to hide the selling point without removing it.', default=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)


class CancelledInvoices(models.Model):
    _name = 'cancelled.invoices'
    _description = 'SIN cancelled invoices'

    name = fields.Char('Name cencel')
    payment_reference = fields.Char('payment_reference')
    # reason_id = fields.Many2one(
    #     'cancellation_reasons', string='Cancellation Reason')
    date = fields.Datetime('date')
    reversed = fields.Boolean('reversed')
    active = fields.Boolean(
        'Active', help='Allows you to hide the cancelled invoice without removing it.', default=True)


class CancellationReasons(models.Model):
    _name = 'cancellation.reasons'
    _description = 'cancellation_reasons'

    name = fields.Many2one('Razón Cancel')
    code = fields.Integer('Code')
    description = fields.Text('description')
    active = fields.Boolean(
        'Active', help='Allows you to hide the cancellation reasons without removing it.', default=True)


class DocumentSecType(models.Model):
    _name = 'document.sec.type'
    _description = 'BO EDI Native Country'

    name = fields.Char('Document type')
    code = fields.Char('Code Sector Invoice')
    description = fields.Char('description')
    code_type = fields.Char('Code Type Document')


class DocumentStatus(models.Model):
    _name = 'document.status'
    _description = 'SIN document status'

    name = fields.Char('Document state')
    code = fields.Integer('Code')
    description = fields.Text('description')
    active = fields.Boolean(
        'Active', help='Allows you to hide the document status without removing it.', default=True)


class IdType(models.Model):
    _name = 'id.type'
    _description = 'Client ID type'

    name = fields.Char('Client ID type')
    id_type_code = fields.Integer(string='ID Type Code')
    description = fields.Text(string='Description')
    res_partner_ids = fields.One2many(
        'res.partner', 'l10n_bo_id_type', string='Related Clients')
    active = fields.Boolean(
        'Active', help='Allows you to hide the id type without removing it.', default=True)


class InvoiceCaption(models.Model):
    _name = 'invoice.caption'
    _description = 'BO EDI invoice captions'

    name = fields.Char('Caption')
    activity_code = fields.Char('Activity Code')
    description = fields.Char('Caption')


class InvoiceEvents(models.Model):
    _name = 'invoice.event'
    _description = 'BO EDI Invoice Events'

    name = fields.Char('Invoice Events')
    code = fields.Char('Code')
    description = fields.Char('Message')


class MeasureUnit(models.Model):
    _name = 'measure.unit'
    _description = 'Measure items provided by SIN'

    name = fields.Char('Measure unit sin')
    measure_unit_code = fields.Integer(string='Measure Unit Code')
    description = fields.Text(string='Description')
    active = fields.Boolean(
        'Active', help='Allows you to hide the Measure Unit without removing it.', default=True)


class MessagesService(models.Model):
    _name = 'messages.service'
    _description = 'BO EDI Messages Service'

    name = fields.Char('Message Service')
    code = fields.Char('Code')
    description = fields.Char('Message')


class ModalitiesSiat(models.Model):
    _name = 'modalities.siat'
    _description = 'modalities'

    name = fields.Char('Modalities')
    id_modality = fields.Integer(string='Modality Code')
    description = fields.Text(string='Description')
    current_invoicing_modality = fields.One2many(
        'res.config.settings', 'l10n_bo_invoicing_modality', string='Current Invoicing Modality')
    active = fields.Boolean(
        'Active', help='Allows you to hide the modality without removing it.', default=True)


class NativeCountry(models.Model):
    _name = 'native.country'
    _description = 'BO EDI Native Country'

    name = fields.Char('Native country')
    code = fields.Char('Code')
    description = fields.Char('description')


class NullReason(models.Model):
    _name = 'null.reason'
    _description = 'BO EDI Null Reason'

    name = fields.Char('Null reason')
    code = fields.Char('Code')
    description = fields.Char('Message')


class PaymentMethod(models.Model):
    _name = 'payment.method'
    _description = 'SIN Payment Method'

    name = fields.Char('Payment method')
    code = fields.Integer('Code')
    description = fields.Text('description')
    active = fields.Boolean(
        'Active', help='Allows you to hide the document status without removing it.', default=True)


class SectorType(models.Model):
    _name = 'sector.types'
    _description = 'Sector Type'

    name = fields.Char('Sector Type')
    id_sector_type = fields.Integer(string='ID Sector Type')
    description = fields.Text(string='Description')
    current_sector_type = fields.One2many(
        'res.config.settings', 'l10n_bo_sector_type', string='Current Sector Type')
    active = fields.Boolean(
        'Active', help='Allows you to hide the sector type without removing it.', default=True)


class SinItems(models.Model):
    _name = 'sin.items'
    _description = 'Items provided by SIN'

    name = fields.Char('Items SIN')
    sin_code = fields.Integer(string='ProductService Code')
    description = fields.Text(string='Description')
    activity_code = fields.Many2one(
        'l10n_bo.company.activities', string='Activity Code')
    active = fields.Boolean(
        'Active', help='Allows you to hide the Sin Items without removing it.', default=True)


class InvoiceTypeSiat(models.Model):
    _name = 'invoice.type.siat'
    _description = 'SIAT Invoice Type SIAT'

    name = fields.Char('Payment method')
    code = fields.Integer('Code')
    active = fields.Boolean(
        'Active', help='Allows you to hide the document status without removing it.', default=True)


class SalePointType(models.Model):
    _name = 'sale.point.type'
    _description = 'SIAT Invoice Type SIAT'

    name = fields.Char('Sale Point Type')
    code = fields.Integer('Code')
    active = fields.Boolean(
        'Active', help='Allows you to hide the document status without removing it.', default=True)

class TypeRooms(models.Model):
    _name = 'type.rooms'
    _description = 'Type Rooms SIAT'

    name = fields.Char('Type Room')
    code = fields.Integer('Code')
    active = fields.Boolean(
        'Active', help='Allows you to hide the document status without removing it.', default=True)

class TypeEmission(models.Model):
    _name = 'type.emission'
    _description = 'Type Emision SIAT'

    name = fields.Char('Type Emission')
    code = fields.Integer('Code')
    active = fields.Boolean(
        'Active', help='Allows you to hide the document status without removing it.', default=True)

class CurrencySiat(models.Model):
    _name = 'currency.siat'
    _description = 'Currency SIAT'

    name = fields.Char('Currency')
    code = fields.Integer('Code')
    active = fields.Boolean(
        'Active', help='Allows you to hide the document status without removing it.', default=True)

class InvoiceIncident(models.Model):
    _name = 'invoice.incident'
    _description = 'BO EDI Invoice Incident'

    name = fields.Char(string='Incident', default='Nuevo', copy=False)
    invoice_event_id = fields.Many2one(comodel_name='invoice.event', string='Invoice Event')
    description = fields.Char('Description')
    begin_date = fields.Datetime(string='Begin Date')
    end_date = fields.Datetime(string='End Date')
    selling_point_id = fields.Many2one(comodel_name='selling.point', string='Selling Point')
    sin_code = fields.Char(string='SIN code', readonly=True)
    cufd_log_id = fields.Many2one(comodel_name='cufd.log', string='CUFD related')
    cuis = fields.Char(string='Log CUIS')
    sector_siat_id = fields.Many2one('document.sec.type', string='Document Type')
    company_id = fields.Many2one('res.company', string='Company')
    siat_code = fields.Char(string='Return SIAT Code')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('process', 'Process'),
        ('error', 'Error'),
        ('done', 'Done')
    ], default='draft', string='Estate', required=True)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            seq_date = None
            vals['name'] = self.env['ir.sequence'].next_by_code('invoice.incident', sequence_date=seq_date) or '/'
        res = super(InvoiceIncident, self).create(vals)
        return res
