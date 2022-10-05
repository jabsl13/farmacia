from io import BytesIO
import io
import logging
import base64
import qrcode
import tarfile
import io
import time
from datetime import datetime
from odoo import fields, models, api, _
from pytz import timezone
from hashlib import sha256
from odoo.exceptions import ValidationError, UserError
from lxml import etree
import gzip
from .num_literal import to_word

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'
    _description = 'Account move inherit'

    @api.depends('line_ids.balance', 'currency_id', 'company_id', 'invoice_date', 'line_ids')
    def _compute_amount_sin(self):
        amount_des = 0
        amount_exe = 0
        amount_ice = 0
        amount_open = 0
        for move in self:
            for line_inv in move.invoice_line_ids:
                if line_inv.price_unit > 0:
                    amount_open += line_inv.quantity * line_inv.price_unit
                else:
                    amount_des += line_inv.quantity * line_inv.price_unit
                if not line_inv.tax_ids:
                    amount_exe += line_inv.price_subtotal

            move.amount_iva = move.amount_tax
            move.amount_des = amount_des * -1
            move.amount_exe = amount_exe
            move.amount_ice_iehd = amount_ice
            move.amount_open = amount_open
            move.amount_imp = amount_open - amount_exe - amount_ice + amount_des

    l10n_bo_cuf = fields.Char(
        string='CUF Code', help='(Código Unico de Facturación) Code referred to Point of Attention', readonly=True,
        copy=False)
    l10n_bo_cufd = fields.Char(
        string='CUFD Code',
        help='(Código Unico de Facturación Diaria) Code provided by SIN, generated daily, identifies the invoice along with a number',
        readonly=True, copy=False)
    efact_control_code = fields.Char(
        string='CUFD Control Code', help='Control Code, given along CUFD', readonly=True, copy=False)
    l10n_bo_invoice_number = fields.Char(
        string='Invoice Number', help='Along with CUFD Code, helps in identifying the invoice', readonly=True,
        copy=False)
    l10n_bo_selling_point = fields.Many2one(
        'selling.point', string='Selling Point', readonly=True, copy=False)
    l10n_bo_branch_office = fields.Many2one(
        'branch.office', string='Branch Office', readonly=True, copy=False)
    l10n_bo_emission_type = fields.Selection([
        ('1', 'Online'),
        ('2', 'Offline'),
        ('3', 'Massiva')
    ], default='1', string='Emision Type', required=True,
        readonly=True,
        states={'draft': [('readonly', False)]})
    l10n_bo_type_doc = fields.Selection([
        ('1', 'Factura con Derecho a Crédito Fiscal'),
        ('2', 'Factura sin Derecho a Crédito Fiscal'),
        ('3', 'Documento de Ajuste')
    ], default='1', string='Document Type', required=True,
        readonly=True,
        states={'draft': [('readonly', False)]}
    )
    dosage_id = fields.Many2one('invoice.dosage', string='Selected Dosage', readonly=True,
                                states={'draft': [('readonly', False)]})
    l10n_bo_document_status = fields.Many2one(
        'document.status', string='Document Status', copy=False, readonly=True,
        states={'draft': [('readonly', False)]})
    l10n_bo_payment_method = fields.Many2one(
        'payment.method', string='Payment method', copy=False, readonly=True,
        states={'draft': [('readonly', False)]})
    l10n_bo_card = fields.Char(string='Card number', copy=False, readonly=True,
                               states={'draft': [('readonly', False)]})
    l10n_bo_xml = fields.Binary(string='XML File', copy=False, readonly=True,
                                states={'draft': [('readonly', False)]})
    l10n_bo_xml_filename = fields.Char(compute='_compute_filename', store=True, copy=False)
    l10n_bo_gzip = fields.Binary(string='GZIP File', copy=False, readonly=True,
                                 states={'draft': [('readonly', False)]})
    l10n_bo_gzip_filename = fields.Char(compute='_compute_filename_gzip', store=True, copy=False)
    l10n_bo_time_sync = fields.Char(string='Date sync SIAT', copy=False, readonly=True,
                                    states={'draft': [('readonly', False)]})
    l10n_bo_time_sync_cuf = fields.Char(string='Date sync SIAT to CUF', copy=False, readonly=True,
                                        states={'draft': [('readonly', False)]})
    l10n_bo_time = fields.Char(string='Date time print', copy=False, readonly=True,
                               states={'draft': [('readonly', False)]})
    l10n_bo_url = fields.Char(string='URL Invoice SIAT', copy=False, readonly=True,
                              states={'draft': [('readonly', False)]})
    l10n_bo_code_receipt = fields.Char(string='Receipt Code SIAT Invoice', copy=False, readonly=True,
                                       states={'draft': [('readonly', False)]})
    l10n_bo_null_reason = fields.Many2one(
        'null.reason', string='Null Reason', copy=False)
    cafc_log_id = fields.Many2one('cafc.log', string='CAFC current', readonly=True,
                                  states={'draft': [('readonly', False)]})
    incident_id = fields.Many2one('invoice.incident', string='Event ID', readonly=True,
                                  states={'draft': [('readonly', False)]})
    qr_code = fields.Binary("QR Code", attachment=True, store=True, readonly=True,
                            states={'draft': [('readonly', False)]})
    l10n_bo_cancellation_reason = fields.Many2one(
        'cancellation.reasons', string='Cancellation Reason', copy=False, readonly=True,
        states={'draft': [('readonly', False)]})
    cafc = fields.Text(string='cafc', default='123', readonly=True,
                       states={'draft': [('readonly', False)]})
    e_billing = fields.Boolean('e_billing',
                               related='company_id.l10n_bo_invoicing_type',
                               store=True)
    inv_type = fields.Boolean(string='Invoice')

    dui = fields.Text('DUI', copy=False)
    auth_number = fields.Text('Authorization Number', copy=False)
    control_code = fields.Text('Control Code', copy=False)
    l10n_bo_id_type = fields.Many2one('id.type', string='ID Type', readonly=True, copy=True,
                                      states={'draft': [('readonly', False)]})
    nit_ci = fields.Char(string='NIT/CI', size=12, default='0',
                         readonly=True, copy=True,
                         states={'draft': [('readonly', False)]})
    razon_social = fields.Char(string='Razón Social', size=100, default='S/N',
                               readonly=True, copy=True,
                               states={'draft': [('readonly', False)]})
    amount_text = fields.Char(string="Monto Literal")

    state_sin = fields.Selection([
        ('A', 'ANULADA'),
        ('V', u'VÁLIDA'),
        ('E', 'EXTRAVIADA'),
        ('N', 'NO UTILIZADA'),
        ('C', 'EMITIDA EN CONTINGENCIA'),
        ('L', u'LIBRE CONSIGNACIÓN'),
        ('NA', u'NO APLICA'),
    ], "Estado SIN", help="Estado SIN", copy=False)
    note_credit_debit = fields.Boolean(string='Nota de Credito Debito',
                                       default=False, copy=False,
                                       readonly=True)
    qr_image = fields.Binary(string='Código QR', help='Imágen QR de la Factura',
                             readonly=True, copy=False,
                             states={'draft': [('readonly', False)]})
    tipo_com = fields.Selection([
        ('1',
         u'Compras para mercado interno con destino y actividades gravadas'),
        ('2',
         u'Compras para mercado interno con destino a actividades no gravadas'),
        ('3', u'Compras sujetas a proporcionalidad'),
        ('4', u'Compras para exportaciones'),
        (
            '5', u'Compras tanto para el mercado interno como para exportaciones'),
    ], "Tipo de Compra", help="Tipo de Compra", readonly=True,
        states={'draft': [('readonly', False)]})

    # TOTALES
    amount_imp = fields.Monetary(string='Importe Base para Impuesto',
                                 currency_field='',
                                 compute='_compute_amount_sin',
                                 store=True, readonly=True,
                                 help='Importe base para crédito o débito fiscal')

    amount_iva = fields.Monetary(string='Importe IVA',
                                 store=True, readonly=True,
                                 compute='_compute_amount_sin',
                                 currency_field='company_currency_id',
                                 track_visibility='always')

    amount_exe = fields.Monetary(string='Importe Exento',
                                 currency_field='company_currency_id',
                                 store=True,
                                 compute='_compute_amount_sin', readonly=True)

    amount_des = fields.Monetary('Descuento',
                                 currency_field='company_currency_id',
                                 compute='_compute_amount_sin',
                                 store=True,
                                 readonly=True)

    amount_ice_iehd = fields.Monetary(string='Importe ICE/IEHD',
                                      currency_field='company_currency_id',
                                      store=True,
                                      compute='_compute_amount_sin',
                                      readonly=True)

    amount_open = fields.Monetary(string='Total Factura',
                                  currency_field='company_currency_id',
                                  compute='_compute_amount_sin',
                                  store=True, readonly=True,
                                  )

    amount_giftcard = fields.Text(string='Total Gift Card', currency_field='company_currency_id', readonly=True,
                                  states={'draft': [('readonly', False)]})

    @api.constrains('dosage_id', 'l10n_bo_invoice_number')
    def _check_factura_sin_numero(self):
        for inv in self:
            if inv.move_type in ('out_invoice', 'out_refund'):
                if inv.l10n_bo_invoice_number and inv.dosage_id:
                    val = inv.search_count(
                        [('dosage_id', '=', inv.dosage_id.id),
                         ('company_id', '=', inv.company_id.id),
                         ('l10n_bo_invoice_number', '=', inv.l10n_bo_invoice_number),
                         ('move_type', '=', 'out_invoice'),
                         ('state', '=', 'posted')])
                    if val > 1:
                        raise ValidationError(_(
                            "Ya tiene registrado el Nro de Factura y Nro de Dosificación en el sistema"))

                    val = inv.search_count(
                        [('dosage_id', '=', inv.dosage_id.id),
                         ('company_id', '=', inv.company_id.id),
                         ('l10n_bo_invoice_number', '=', inv.l10n_bo_invoice_number),
                         ('move_type', '=', 'out_refund'),
                         ('state', '=', 'posted')])
                    if val > 1:
                        raise ValidationError(_(
                            "Ya tiene registrado el Nro de Nota debit/credito y Nro de Dosificación en el sistema"))

    @api.onchange('partner_id')
    def onchange_partner_id_sin(self):
        for invoice in self:
            if invoice.partner_id:
                if invoice.partner_id.name:
                    invoice.razon_social = invoice.partner_id.name
                else:
                    invoice.razon_social = 'S/N'
                if invoice.partner_id.vat:
                    invoice.nit_ci = invoice.partner_id.vat
                    invoice.l10n_bo_id_type = invoice.partner_id.l10n_bo_id_type.id
                else:
                    invoice.nit_ci = '0'

    @api.onchange('invoice_user_id')
    def onchange_dosage_user_id(self):
        for invoice in self:
            if invoice.invoice_user_id and invoice.invoice_user_id.l10n_bo_selling_point_id:
                dosage_ids = self.env['invoice.dosage'].search(
                    [('user_ids', 'in', [invoice.invoice_user_id.id]), ('active', '=', True)])
                invoice.dosage_id = dosage_ids[0].id

    @api.depends('l10n_bo_xml')
    def _compute_filename(self):
        for invoice in self:
            if invoice.l10n_bo_invoice_number:
                filename = ''
                if invoice.move_type == 'out_invoice':
                    filename = 'factura-' + invoice.partner_id.vat + '-' + invoice.l10n_bo_invoice_number + ".xml"
                elif invoice.move_type == 'out_refund':
                    filename = 'nota_dc-' + invoice.partner_id.vat + '-' + invoice.l10n_bo_invoice_number + ".xml"
                invoice.l10n_bo_xml_filename = filename

    @api.depends('l10n_bo_gzip')
    def _compute_filename_gzip(self):
        for invoice in self:
            if invoice.l10n_bo_invoice_number:
                filename = ''
                if invoice.move_type == 'out_invoice':
                    filename = 'factura-' + invoice.partner_id.vat + '-' + invoice.l10n_bo_invoice_number + ".gz"
                elif invoice.move_type == 'out_refund':
                    filename = 'nota_dc-' + invoice.partner_id.vat + '-' + invoice.l10n_bo_invoice_number + ".gz"
                invoice.l10n_bo_gzip_filename = filename

    def _addZeros(self, field, value):
        if field == 'nit':
            if len(value) == 9:
                return '0000' + value
            elif len(value) == 10:
                return '000' + value
            else:
                return value

        elif field == 'branch_office':
            if len(value) == 1:
                return '000' + value
            elif len(value) == 2:
                return '00' + value
            elif len(value) == 3:
                return '0' + value

        elif field == 'document_type':
            if len(value) == 1:
                return '0' + value
            elif len(value) == 2:
                return value

        elif field == 'invoice_number':
            if len(value) == 1:
                return '000000000' + value
            elif len(value) == 2:
                return '00000000' + value
            elif len(value) == 3:
                return '0000000' + value
            elif len(value) == 4:
                return '0000000' + value

        elif field == 'selling_point':
            if len(value) == 1:
                return '000' + value
            elif len(value) == 2:
                return '00' + value
            elif len(value) == 3:
                return '0' + value

    def _Mod11(self, dado, numDig, limMult, x10):
        if not x10:
            numDig = 1
        n = 1
        while n <= numDig:
            soma = 0
            mult = 2
            i = len(dado) - 1
            while i >= 0:
                soma += (mult * int(dado[i:i + 1]))
                mult += 1
                if mult > limMult:
                    mult = 2
                i -= 1
            if x10:
                dig = ((soma * 10) % 11) % 10
            else:
                dig = soma % 11
            if dig == 10:
                dado += "1"
            if dig == 11:
                dado += "0"
            if dig < 10:
                dado += str(dig)
            n += 1
        return dado[len(dado) - numDig:len(dado)]

    def _Base16(self, cadena):
        hex_val = (hex(int(cadena))[2:]).upper()
        return hex_val

    def getTime(self):
        now = datetime.now(timezone('America/La_Paz'))
        return now

    def getCuf(self, nit, branch_office, modality, emission_type, invoice_type, document_type, invoice_number,
               selling_point, control_code):

        str_nit = str(self._addZeros('nit', nit))
        branch_office_str = self._addZeros('branch_office', str(branch_office))
        document_type_str = self._addZeros('document_type', str(document_type))
        invoice_number_str = self._addZeros('invoice_number', str(invoice_number))
        selling_point_str = self._addZeros('selling_point', str(selling_point))
        now = self.getTime()
        l10n_bo_time = now.strftime("%d/%m/%Y %I:%M")
        tim = now.strftime("%H:%M")[:2]
        if int(tim) >= 12:
            l10n_bo_time = l10n_bo_time + ' PM'
        else:
            l10n_bo_time = l10n_bo_time + ' AM'
        l10n_bo_time_sync = now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
        l10n_bo_time_sync_cuf = now.strftime("%Y%m%d%H%M%S%f")[:-3]

        zero_str = str(str_nit +
                       str(l10n_bo_time_sync_cuf) +
                       str(branch_office_str) +
                       str(modality) +
                       str(emission_type) +
                       str(invoice_type) +
                       str(document_type_str) +
                       str(invoice_number_str) +
                       str(selling_point_str))
        mod11_str = str(self._Mod11(zero_str, 1, 9, False))
        base16_str = str(self._Base16(zero_str + mod11_str))
        cuf = base16_str + str(control_code)
        return cuf, l10n_bo_time_sync, l10n_bo_time_sync_cuf, l10n_bo_time

    def send_invoice_siat(self):
        for invoice in self:
            if not invoice.dosage_id.sector_siat_id:
                raise ValidationError(_('Error Factura:\n'
                                        'Defina sector en la dosificacion'))

            if not invoice.l10n_bo_payment_method:
                raise ValidationError(_('Error Factura:\n'
                                        'Defina método de pago para la factura'))

            card_n = False
            if invoice.l10n_bo_payment_method.code == 2:
                if not invoice.l10n_bo_card:
                    raise ValidationError(_('Error Factura:\n'
                                            'Defina número de tarjeta'))
                else:
                    if len(invoice.l10n_bo_card) == 16:
                        card_n = invoice.l10n_bo_card[0:4] + '00000000' + invoice.l10n_bo_card[-4:]

            invoice_header = {
                'nit': invoice.company_id.vat,
                'company_name': invoice.env.company.name,
                'city_name': invoice.env.company.city,
                'phone': invoice.env.company.phone,
                'invoice_number': invoice.l10n_bo_invoice_number,
                'cufd': invoice.dosage_id.cufd_log_id.cufd,
                'branch_office_id': invoice.l10n_bo_branch_office.id_branch_office,
                'company_address': invoice.env.company.street,
                'selling_point_id': invoice.l10n_bo_selling_point.id_selling_point,
                'current_time': invoice.l10n_bo_time_sync,
                'client_name': invoice.razon_social or invoice.partner_id.name,
                'client_id_type': invoice.l10n_bo_id_type.id_type_code or invoice.partner_id.l10n_bo_id_type.id_type_code,
                'modality': invoice.company_id.l10n_bo_invoicing_modality.id_modality,
                'emission_type': invoice.l10n_bo_emission_type,
                'type_doc': invoice.l10n_bo_type_doc,
                'client_id': invoice.partner_id.id,
                'vat': invoice.nit_ci or invoice.partner_id.vat,
                'payment_method': invoice.l10n_bo_payment_method.code,
                'card_number': card_n and int(card_n) or int(invoice.l10n_bo_card) or 0,
                'document_type': invoice.dosage_id.sector_siat_id.code,
                'control_code': invoice.dosage_id.cufd_log_id.control_code,
                'total_untaxed': invoice.amount_total,
                'total': invoice.amount_total,
                'user': invoice.env.user.login,
                'leyenda': invoice.dosage_id.invoice_caption_id.name,
                'sector': invoice.dosage_id.sector_siat_id.code,
                'currency_type': '1'
            }
            additional_data = invoice._getAdditionalData(0)
            invoice._setXML(invoice_header, invoice._getInvoiceItemsData(),
                            additional_data)

    def send_invoice_siat_dc(self):
        for invoice in self:
            invoice_header = {
                'nit': invoice.company_id.vat,
                'company_name': invoice.env.company.name,
                'city_name': invoice.env.company.city,
                'phone': invoice.env.company.phone,
                'invoice_number': invoice.l10n_bo_invoice_number,
                'cufd': invoice.dosage_id.cufd_log_id.cufd,
                'branch_office_id': invoice.l10n_bo_branch_office.id_branch_office,
                'company_address': invoice.env.company.street,
                'selling_point_id': invoice.l10n_bo_selling_point.id_selling_point,
                'current_time': invoice.l10n_bo_time_sync,
                'client_name': invoice.razon_social or invoice.partner_id.name,
                'client_id_type': invoice.l10n_bo_id_type.id_type_code or invoice.partner_id.l10n_bo_id_type.id_type_code,
                'modality': invoice.company_id.l10n_bo_invoicing_modality.id_modality,
                'emission_type': invoice.l10n_bo_emission_type,
                'type_doc': invoice.l10n_bo_type_doc,
                'client_id': invoice.partner_id.id,
                'vat': invoice.nit_ci or invoice.partner_id.vat,
                'payment_method': '1',
                'document_type': '24',
                'control_code': invoice.dosage_id.cufd_log_id.control_code,
                'total_untaxed': invoice.amount_total,
                'total': invoice.amount_total,
                'total_tax': invoice.amount_tax,
                'user': invoice.env.user.login,
                'leyenda': invoice.dosage_id.invoice_caption_id.name,
                'sector': '24',
                'currency_type': '1'
            }
            additional_data = invoice._getAdditionalData_dc(0)
            invoice._setXML_dc(invoice_header, invoice._getInvoiceItemsData(),
                               additional_data)

    def _getInvoiceItemsData(self):
        items = self.invoice_line_ids
        return items

    def _getAdditionalData(self, invoice_type):
        header_start = ()
        xml_end = ""
        if invoice_type == 0:
            header_start = ("<facturaElectronicaCompraVenta"
                            ' xmlns:ds="http://www.w3.org/2000/09/xmldsig#"'
                            ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
                            ' xsi:noNamespaceSchemaLocation="facturaElectronicaCompraVenta.xsd">')
            xml_end = "</facturaElectronicaCompraVenta>"
        additional_data = {'start': header_start,
                           'end': xml_end}
        return additional_data

    def _getAdditionalData_dc(self, invoice_type):
        header_start = ()
        xml_end = ""
        if invoice_type == 0:
            header_start = ("<notaFiscalElectronicaCreditoDebito"
                            ' xmlns:ds="http://www.w3.org/2000/09/xmldsig#"'
                            ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
                            ' xsi:noNamespaceSchemaLocation="notaElectronicaCreditoDebito.xsd">')
            xml_end = "</notaFiscalElectronicaCreditoDebito>"
        additional_data = {'start': header_start,
                           'end': xml_end}
        return additional_data

    def _getSignature(self):
        sign = "<Signature xmlns=\"http://www.w3.org/2000/09/xmldsig#\" Id=\"placeholder\"></Signature>\n"
        return sign

    def _setXML(self, invh, invoiceitems, additionaldata):
        bo_util = self.env['l10n_bo.edi.util']
        bo_sync = self.env['sin.sync']
        digital_signature = self.company_id._get_digital_signature(user_id=self.env.user.id)
        pem_certificate = base64.decodebytes(digital_signature.signature_crt_file)
        pem_private_key = base64.decodebytes(digital_signature.signature_key_file)
        xml = ''
        cuf, date_format, date_format_cuf, date_time = self.getCuf(invh['nit'],
                                                                   invh['branch_office_id'],
                                                                   invh['modality'],
                                                                   invh['emission_type'],
                                                                   invh['type_doc'],
                                                                   invh['document_type'],
                                                                   invh['invoice_number'],
                                                                   invh['selling_point_id'],
                                                                   invh['control_code'])
        xmlHeader = ("<cabecera>"
                     F"<nitEmisor>{invh['nit']}</nitEmisor>"
                     F"<razonSocialEmisor>{invh['company_name']}</razonSocialEmisor>"
                     F"<municipio>{invh['city_name']}</municipio>"
                     F"<telefono>{invh['phone']}</telefono>"
                     F"<numeroFactura>{invh['invoice_number']}</numeroFactura>"
                     F"<cuf>{cuf}</cuf>"
                     F"<cufd>{invh['cufd']}</cufd>"
                     F"<codigoSucursal>{invh['branch_office_id']}</codigoSucursal>"
                     F"<direccion>{invh['company_address']}</direccion>"
                     F"<codigoPuntoVenta>{invh['selling_point_id']}</codigoPuntoVenta>"
                     F"<fechaEmision>{date_format}</fechaEmision>"
                     F"<nombreRazonSocial>{invh['client_name']}</nombreRazonSocial>"
                     F"<codigoTipoDocumentoIdentidad>{invh['client_id_type']}</codigoTipoDocumentoIdentidad>"
                     F"<numeroDocumento>{invh['vat']}</numeroDocumento>"
                     '<complemento/>'
                     F"<codigoCliente>{invh['client_id']}</codigoCliente>"
                     F"<codigoMetodoPago>{invh['payment_method']}</codigoMetodoPago>"
                     F"<numeroTarjeta>{invh['card_number']}</numeroTarjeta>"
                     F"<montoTotal>{invh['total_untaxed']}</montoTotal>"
                     F"<montoTotalSujetoIva>{invh['total']}</montoTotalSujetoIva>"
                     F"<codigoMoneda>1</codigoMoneda>"
                     F"<tipoCambio>1</tipoCambio>"
                     F"<montoTotalMoneda>{invh['total']}</montoTotalMoneda>"
                     "<montoGiftCard>0</montoGiftCard>"
                     "<descuentoAdicional>0</descuentoAdicional>"
                     "<codigoExcepcion>0</codigoExcepcion>"
                     "<cafc xsi:nil='true'/>"
                     F"<leyenda>{invh['leyenda']}</leyenda>"
                     F"<usuario>{invh['user']}</usuario>"
                     F"<codigoDocumentoSector>{invh['sector']}</codigoDocumentoSector>"
                     "</cabecera>"
                     )
        xml = xml + additionaldata['start'] + xmlHeader
        for item in invoiceitems:
            xmlItem = ("<detalle>"
                       F"<actividadEconomica>{item.product_id.sin_item.activity_code.code}</actividadEconomica>"
                       F"<codigoProductoSin>{item.product_id.sin_item.sin_code}</codigoProductoSin>"
                       F"<codigoProducto>{item.product_id.default_code}</codigoProducto>"
                       F"<descripcion>{item.name}</descripcion>"
                       F"<cantidad>{round(item.quantity, 2)}</cantidad>"
                       F"<unidadMedida>{item.product_id.measure_unit.measure_unit_code}</unidadMedida>"
                       F"<precioUnitario>{round(item.price_unit, 2)}</precioUnitario>"
                       F"<montoDescuento>{round(item.discount, 2)}</montoDescuento>"
                       F"<subTotal>{round(item.price_total, 2)}</subTotal>"
                       '<numeroSerie/>'
                       '<numeroImei/>'
                       "</detalle>")
            xml = xml + xmlItem

        xml = xml + self._getSignature() + additionaldata['end']
        # root = etree.fromstring(xml, parser=etree.XMLParser(remove_blank_text=True))
        root = etree.fromstring(bytes(xml, 'utf-8'), parser=etree.XMLParser(encoding='utf-8'))
        root_sign_bin = bo_util._sign_xml(root, pem_certificate, pem_private_key)
        # xml_formatted_str = etree.tostring(root_sign, pretty_print=True, encoding='UTF-8', xml_declaration=True)
        # self.l10n_bo_xml = base64.encodebytes(xml_formatted_str)

        if self.company_id.l10n_bo_invoicing_modality.id_modality == 1:
            xsd_name_file = 'facturaElectronicaCompraVenta.xsd'
        elif self.company_id.l10n_bo_invoicing_modality.id_modality == 2:
            xsd_name_file = 'facturaComputarizadaCompraVenta.xsd'
        self.l10n_bo_xml = base64.b64encode(root_sign_bin)
        bo_util._compute_validation_xml(xsd_name_file, self.l10n_bo_xml)
        file_xml = root_sign_bin
        buf = io.BytesIO()
        filename = 'factura-' + invh['vat'] + '-' + invh['invoice_number'] + ".xml"
        with gzip.GzipFile(filename=filename, fileobj=buf, mode='wb', compresslevel=9,
                           mtime=None) as f:
            f.write(file_xml)
        compress_gzip = buf.getvalue()
        hashed_xml = self._GetHashSha256(compress_gzip)
        offline = self.env.context.get('offline', False)
        if offline:
            self.cafc_log_id = self.dosage_id.cafc_log_id.id
            self.l10n_bo_gzip = base64.encodebytes(compress_gzip)
            self.l10n_bo_cuf = cuf
            self.l10n_bo_time = date_time
            self.l10n_bo_time_sync = date_format
            self.l10n_bo_time_sync_cuf = date_format_cuf
            self.l10n_bo_emission_type = '2'
        else:
            if self.check_communication():
                result = bo_sync.send_invoice(self.company_id,
                                              self.l10n_bo_selling_point.id_selling_point,
                                              self.l10n_bo_branch_office.id_branch_office,
                                              self.dosage_id.sector_siat_id,
                                              self.dosage_id.cuis,
                                              self.l10n_bo_cufd,
                                              compress_gzip,
                                              hashed_xml,
                                              date_format)

                if result.codigoDescripcion == 'RECHAZADA' or result.codigoDescripcion is None:
                    mensaje_list = result.mensajesList[0]
                    raise ValidationError(_('Error SIAT:\n'
                                            'Codigo %s.- %s\n') % (str(mensaje_list.codigo), mensaje_list.descripcion))
                else:
                    self.l10n_bo_code_receipt = result.codigoRecepcion
                    self.state_sin = 'V'
                    self.l10n_bo_gzip = base64.encodebytes(compress_gzip)
                    self.l10n_bo_cuf = cuf
                    self.l10n_bo_time = date_time
                    self.l10n_bo_time_sync = date_format
                    self.l10n_bo_time_sync_cuf = date_format_cuf
                    if self.company_id.l10n_bo_ambience.id_ambience == 1:
                        url = "https://siat.impuestos.gob.bo/consulta/QR?nit=%s&cuf=%s&numero=%s" % (
                            invh['nit'], cuf, invh['invoice_number'])
                        self.generate_qr_code(url)
                    else:
                        url = "https://pilotosiat.impuestos.gob.bo/consulta/QR?nit=%s&cuf=%s&numero=%s" % (
                            invh['nit'], cuf, invh['invoice_number'])
                        self.generate_qr_code(url)
                    self.l10n_bo_url = url
            else:
                self.cafc_log_id = self.dosage_id.cafc_log_id.id
                self.l10n_bo_gzip = base64.encodebytes(compress_gzip)
                self.l10n_bo_cuf = cuf
                self.l10n_bo_time = date_time
                self.l10n_bo_time_sync = date_format
                self.l10n_bo_time_sync_cuf = date_format_cuf
                self.l10n_bo_emission_type = '2'

    def _setXML_dc(self, invh, invoiceitems, additionaldata):
        bo_util = self.env['l10n_bo.edi.util']
        bo_sync = self.env['sin.sync']

        invoice_origin = self.reversed_entry_id
        digital_signature = self.company_id._get_digital_signature(user_id=self.env.user.id)
        pem_certificate = base64.decodebytes(digital_signature.signature_crt_file)
        pem_private_key = base64.decodebytes(digital_signature.signature_key_file)
        xml = ''
        cuf, date_format, date_format_cuf, date_time = self.getCuf(invh['nit'],
                                                                   invh['branch_office_id'],
                                                                   invh['modality'],
                                                                   invh['emission_type'],
                                                                   invh['type_doc'],
                                                                   invh['document_type'],
                                                                   invh['invoice_number'],
                                                                   invh['selling_point_id'],
                                                                   invh['control_code'])
        xmlHeader = ("<cabecera>"
                     F"<nitEmisor>{invh['nit']}</nitEmisor>"
                     F"<razonSocialEmisor>{invh['company_name']}</razonSocialEmisor>"
                     F"<municipio>{invh['city_name']}</municipio>"
                     F"<telefono>{invh['phone']}</telefono>"
                     F"<numeroNotaCreditoDebito>{invh['invoice_number']}</numeroNotaCreditoDebito>"
                     F"<cuf>{cuf}</cuf>"
                     F"<cufd>{invh['cufd']}</cufd>"
                     F"<codigoSucursal>{invh['branch_office_id']}</codigoSucursal>"
                     F"<direccion>{invh['company_address']}</direccion>"
                     F"<codigoPuntoVenta>{invh['selling_point_id']}</codigoPuntoVenta>"
                     F"<fechaEmision>{date_format}</fechaEmision>"
                     F"<nombreRazonSocial>{invh['client_name']}</nombreRazonSocial>"
                     F"<codigoTipoDocumentoIdentidad>{invh['client_id_type']}</codigoTipoDocumentoIdentidad>"
                     F"<numeroDocumento>{invh['vat']}</numeroDocumento>"
                     '<complemento/>'
                     F"<codigoCliente>{invh['client_id']}</codigoCliente>"
                     F"<numeroFactura>{invoice_origin.l10n_bo_invoice_number}</numeroFactura>"
                     F"<numeroAutorizacionCuf>{invoice_origin.l10n_bo_cuf}</numeroAutorizacionCuf>"
                     F"<fechaEmisionFactura>{invoice_origin.l10n_bo_time_sync}</fechaEmisionFactura>"
                     F"<montoTotalOriginal>{invoice_origin.amount_total}</montoTotalOriginal>"
                     F"<montoTotalDevuelto>{invh['total']}</montoTotalDevuelto>"
                     F"<montoDescuentoCreditoDebito>0</montoDescuentoCreditoDebito>"
                     F"<montoEfectivoCreditoDebito>{invh['total_tax']}</montoEfectivoCreditoDebito>"
                     F"<codigoExcepcion>0</codigoExcepcion>"
                     F"<leyenda>{invh['leyenda']}</leyenda>"
                     F"<usuario>{invh['user']}</usuario>"
                     F"<codigoDocumentoSector>{invh['sector']}</codigoDocumentoSector>"
                     "</cabecera>"
                     )
        xml = xml + additionaldata['start'] + xmlHeader

        for item in invoice_origin.invoice_line_ids:
            xmlItem = ("<detalle>"
                       F"<actividadEconomica>{item.product_id.sin_item.activity_code.code}</actividadEconomica>"
                       F"<codigoProductoSin>{item.product_id.sin_item.sin_code}</codigoProductoSin>"
                       F"<codigoProducto>{item.product_id.default_code}</codigoProducto>"
                       F"<descripcion>{item.name}</descripcion>"
                       F"<cantidad>{round(item.quantity, 2)}</cantidad>"
                       F"<unidadMedida>{item.product_id.measure_unit.measure_unit_code}</unidadMedida>"
                       F"<precioUnitario>{round(item.price_unit, 2)}</precioUnitario>"
                       F"<montoDescuento>{round(item.discount, 2)}</montoDescuento>"
                       F"<subTotal>{round(item.price_total, 2)}</subTotal>"
                       "<codigoDetalleTransaccion>1</codigoDetalleTransaccion>"
                       "</detalle>")
            xml = xml + xmlItem

        for item in invoiceitems:
            xmlItem = ("<detalle>"
                       F"<actividadEconomica>{item.product_id.sin_item.activity_code.code}</actividadEconomica>"
                       F"<codigoProductoSin>{item.product_id.sin_item.sin_code}</codigoProductoSin>"
                       F"<codigoProducto>{item.product_id.default_code}</codigoProducto>"
                       F"<descripcion>{item.name}</descripcion>"
                       F"<cantidad>{round(item.quantity, 2)}</cantidad>"
                       F"<unidadMedida>{item.product_id.measure_unit.measure_unit_code}</unidadMedida>"
                       F"<precioUnitario>{round(item.price_unit, 2)}</precioUnitario>"
                       F"<montoDescuento>{round(item.discount, 2)}</montoDescuento>"
                       F"<subTotal>{round(item.price_total, 2)}</subTotal>"
                       "<codigoDetalleTransaccion>2</codigoDetalleTransaccion>"
                       "</detalle>")
            xml = xml + xmlItem

        xml = xml + self._getSignature() + additionaldata['end']
        # root = etree.fromstring(xml, parser=etree.XMLParser(remove_blank_text=True))
        root = etree.fromstring(bytes(xml, 'utf-8'), parser=etree.XMLParser(encoding='utf-8'))
        root_sign_bin = bo_util._sign_xml(root, pem_certificate, pem_private_key)
        # xml_formatted_str = etree.tostring(root_sign, pretty_print=True, encoding='UTF-8', xml_declaration=True)
        # self.l10n_bo_xml = base64.encodebytes(xml_formatted_str)

        if self.company_id.l10n_bo_invoicing_modality.id_modality == 1:
            xsd_name_file = 'notaElectronicaCreditoDebito.xsd'
        elif self.company_id.l10n_bo_invoicing_modality.id_modality == 2:
            xsd_name_file = 'notaComputarizadaCreditoDebito.xsd'
        self.l10n_bo_xml = base64.b64encode(root_sign_bin)
        bo_util._compute_validation_xml(xsd_name_file, self.l10n_bo_xml)
        file_xml = root_sign_bin
        buf = io.BytesIO()
        filename = 'nota_dc-' + invh['vat'] + '-' + invh['invoice_number'] + ".xml"
        with gzip.GzipFile(filename=filename, fileobj=buf, mode='wb', compresslevel=9,
                           mtime=None) as f:
            f.write(file_xml)
        compress_gzip = buf.getvalue()
        hashed_xml = self._GetHashSha256(compress_gzip)
        sector = self.env['document.sec.type'].search([('code', '=', '24')])[0]
        if self.check_communication():
            result = bo_sync.send_invoice_dc(self.company_id,
                                             self.l10n_bo_selling_point.id_selling_point,
                                             self.l10n_bo_branch_office.id_branch_office,
                                             sector,
                                             self.dosage_id.cuis,
                                             self.l10n_bo_cufd,
                                             compress_gzip,
                                             hashed_xml,
                                             date_format)
            if result.codigoDescripcion == 'RECHAZADA' or result.codigoDescripcion is None:
                mensaje_list = result.mensajesList[0]
                raise ValidationError(_('Error SIAT:\n'
                                        'Codigo %s.- %s\n') % (str(mensaje_list.codigo), mensaje_list.descripcion))
            else:
                self.l10n_bo_code_receipt = result.codigoRecepcion
                self.state_sin = 'V'
                self.l10n_bo_gzip = base64.encodebytes(compress_gzip)
                self.l10n_bo_cuf = cuf
                self.l10n_bo_time = date_time
                self.l10n_bo_time_sync = date_format
                self.l10n_bo_time_sync_cuf = date_format_cuf
                if self.company_id.l10n_bo_ambience.id_ambience == 1:
                    url = "https://siat.impuestos.gob.bo/consulta/QR?nit=%s&cuf=%s&numero=%s" % (
                        invh['nit'], cuf, invh['invoice_number'])
                    self.generate_qr_code(url)
                else:
                    url = "https://pilotosiat.impuestos.gob.bo/consulta/QR?nit=%s&cuf=%s&numero=%s" % (
                        invh['nit'], cuf, invh['invoice_number'])
                    self.generate_qr_code(url)
                self.l10n_bo_url = url
        else:
            self.cafc_log_id = self.dosage_id.cafc_log_id.id
            self.l10n_bo_gzip = base64.encodebytes(compress_gzip)
            self.l10n_bo_cuf = cuf
            self.l10n_bo_time = date_time
            self.l10n_bo_time_sync = date_format
            self.l10n_bo_time_sync_cuf = date_format_cuf
            self.l10n_bo_emission_type = '2'

    def button_cancel(self):
        res = super(AccountMove, self).button_cancel()
        self.anull_siat_invoice()
        return res

    def check_communication(self):
        for invoice in self:
            ok, result = self.env['sin.sync'].check_communication(self.company_id)
            if ok:
                mensajeList = result.mensajesList[0]
                if mensajeList.codigo == 926:
                    if invoice.send_invoice_paquete():
                        time.sleep(0.8)
                        invoice.confirm_invoice_paquete()
                    return True
                else:
                    inv_event = self.env['invoice.event'].search([('code', '=', '2')])
                    incident = self.env['invoice.incident'].search(
                        [('sin_code', '=', False),
                         ('state', '=', 'draft'),
                         ('invoice_event_id', '=', inv_event[0].id),
                         ('cufd_log_id', '=', invoice.dosage_id.cufd_log_id.id)])
                    if incident:
                        invoice.incident_id = incident[0].id
                    else:
                        new_incident = {
                            'invoice_event_id': inv_event[0].id,
                            'description': "INACCESIBILIDAD AL SERVICIO WEB DE LA ADMINISTRACIÓN TRIBUTARIA",
                            'begin_date': self.getTime().strftime("%Y-%m-%d %H:%M:%S"),
                            'end_date': self.getTime().strftime("%Y-%m-%d %H:%M:%S"),
                            'selling_point_id': invoice.l10n_bo_selling_point.id,
                            'cufd_log_id': invoice.dosage_id.cufd_log_id.id,
                            'cuis': invoice.dosage_id.cuis,
                            'sector_siat_id': invoice.dosage_id.sector_siat_id.id,
                            'company_id': invoice.company_id.id,
                            'state': 'draft'
                        }
                        incident = self.env['invoice.incident'].create(new_incident)
                        invoice.incident_id = incident[0].id
                    msg = _('Error Impuestos Nacionales: %(message)s',
                            message=mensajeList.codigo + " " + mensajeList.descripcion)
                    invoice.message_post(body=msg)
                    return False
            else:
                inv_event = self.env['invoice.event'].search([('code', '=', '1')])
                incident = self.env['invoice.incident'].search(
                    [('sin_code', '=', False),
                     ('state', '=', 'draft'),
                     ('invoice_event_id', '=', inv_event[0].id),
                     ('cufd_log_id', '=', invoice.dosage_id.cufd_log_id.id)])
                if incident:
                    invoice.incident_id = incident[0].id
                else:
                    new_incident = {
                        'invoice_event_id': inv_event[0].id,
                        'description': "CORTE DEL SERVICIO DE INTERNET",
                        'begin_date': self.getTime().strftime("%Y-%m-%d %H:%M:%S"),
                        'end_date': self.getTime().strftime("%Y-%m-%d %H:%M:%S"),
                        'selling_point_id': invoice.l10n_bo_selling_point.id,
                        'cufd_log_id': invoice.dosage_id.cufd_log_id.id,
                        'cuis': invoice.dosage_id.cuis,
                        'sector_siat_id': invoice.dosage_id.sector_siat_id.id,
                        'company_id': invoice.company_id.id,
                        'state': 'draft'
                    }
                    incident = self.env['invoice.incident'].create(new_incident)
                    invoice.incident_id = incident[0].id
                msg = _('Error de conexión: %(message)s', message=result)
                invoice.message_post(body=msg)
                return False

    def anull_siat_invoice(self):
        for invoice in self:
            if not invoice.l10n_bo_null_reason:
                raise ValidationError(_('Error Factura:\n'
                                        'Defina motivo de anulación'))
            bo_sync = self.env['sin.sync']
            result = bo_sync.cancel_invoice(invoice.company_id,
                                            invoice.l10n_bo_selling_point.id_selling_point,
                                            invoice.l10n_bo_branch_office.id_branch_office,
                                            invoice.dosage_id.sector_siat_id,
                                            invoice.dosage_id.cuis,
                                            invoice.l10n_bo_cuf,
                                            invoice.l10n_bo_cufd,
                                            invoice.l10n_bo_null_reason)

            if result.codigoDescripcion == 'ANULACION CONFIRMADA':
                invoice.state_sin = 'A'
            else:
                mensajeList = result.mensajesList[0]
                raise ValidationError(_('Error SIAT:\n'
                                        'Codigo %s.- %s\n') % (str(mensajeList.codigo), mensajeList.descripcion))

    ########### Digital Signature Algorithms ################

    def _GetHashSha256(self, input):
        hash = sha256(input).hexdigest()
        return hash

    def print_report(self):
        self.generate_qr_code()
        return self.env.ref('l10n_bo_edi.graphic_representation').report_action(self)

    def generate_qr_code(self, url):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image()
        temp = BytesIO()
        img.save(temp, format="PNG")
        qr_image = base64.b64encode(temp.getvalue())
        self.qr_image = qr_image

    ########### STANDARD BILLING ################
    def generate_control_code(self):
        for invoice in self:
            if invoice.dosage_id:
                if invoice.reversed_entry_id:
                    if invoice.reversed_entry_id.note_credit_debit:
                        invoice.write({
                            'l10n_bo_branch_office': invoice.reversed_entry_id.dosage_id.selling_point_id.branch_office_id.id,
                            'l10n_bo_selling_point': invoice.reversed_entry_id.dosage_id.selling_point_id.id,
                            'l10n_bo_cufd': invoice.reversed_entry_id.dosage_id.cufd_log_id.cufd,
                            'dosage_id': invoice.reversed_entry_id.dosage_id.id,
                            'note_credit_debit': invoice.reversed_entry_id.note_credit_debit,
                            'l10n_bo_type_doc': '3',
                        })
                        inv_num = str(invoice.reversed_entry_id.dosage_id['invoice_number_dc'])
                        invoice.l10n_bo_invoice_number = inv_num
                        invoice.reversed_entry_id.dosage_id['invoice_number_dc'] += 1
                elif invoice.move_type == 'out_invoice':
                    invoice.write({
                        'l10n_bo_branch_office': invoice.dosage_id.selling_point_id.branch_office_id.id,
                        'l10n_bo_selling_point': invoice.dosage_id.selling_point_id.id,
                        'l10n_bo_cufd': invoice.dosage_id.cufd_log_id.cufd,
                    })
                    inv_num = str(self.dosage_id['invoice_number'])
                    invoice.l10n_bo_invoice_number = inv_num
                    invoice.dosage_id['invoice_number'] += 1
                else:
                    invoice.write({
                        'l10n_bo_branch_office': invoice.dosage_id.selling_point_id.branch_office_id.id,
                        'l10n_bo_selling_point': invoice.dosage_id.selling_point_id.id,
                    })

    def _post(self, soft=True):
        res = super()._post(soft)
        for invoice in self:
            invoice.generate_control_code()
            moneda = ''
            if invoice.currency_id.name == 'BOB':
                moneda = ' BOLIVIANOS'
            if invoice.currency_id.name == 'USD':
                moneda = ' DOLARES AMERICANOS'
            texto = to_word(invoice.amount_total) + moneda
            txt = str(texto).upper()
            invoice.amount_text = txt
            if self._context.get('move_reverse_cancel'):
                if invoice.reversed_entry_id.note_credit_debit:
                    if invoice.move_type == 'out_refund':
                        invoice.send_invoice_siat_dc()
            elif invoice.move_type == 'out_invoice':
                invoice.send_invoice_siat()
            # En caso de que no sea nota de credito anular factura original
            elif invoice.move_type == 'out_refund' and not invoice.note_credit_debit and invoice.reversed_entry_id:
                invoice.reversed_entry_id.anull_siat_invoice()
        return res

    def send_invoice_paquete(self):
        incidents = self.env['invoice.incident'].search([('sin_code', '=', False), ('state', '=', 'draft')])
        bo_sync = self.env['sin.sync']
        if incidents:
            for incident in incidents:
                incident.write({'end_date': self.getTime().strftime("%Y-%m-%d %H:%M:%S")})
                invoice = self.search([('l10n_bo_emission_type', '=', '2'),
                                       ('state', '=', 'posted'),
                                       ('incident_id', '=', incident.id)])

                # https://github.com/zAbuQasem/Misc/blob/75657857caa54be4f5c46e1d14007b9bad3f5711/zipslip.py
                buf = io.BytesIO()
                with tarfile.open(fileobj=buf, mode='w:gz') as tar:
                    for inv in invoice:
                        info = tarfile.TarInfo(inv.l10n_bo_xml_filename)
                        info.mtime = time.time()
                        file_xml_od = base64.b64decode(inv.l10n_bo_xml)
                        file_xml = io.BytesIO(file_xml_od)
                        info.size = len(file_xml_od)
                        tar.addfile(info, file_xml)
                tar_invoice = buf.getvalue()
                with open('../fichero.tar.gz', 'wb') as f:
                    f.write(buf.getvalue())

                hashed_xml = self._GetHashSha256(tar_invoice)
                company = incident.company_id
                selling = incident.selling_point_id.id_selling_point
                branch = incident.selling_point_id.branch_office_id.id_branch_office
                sector = incident.sector_siat_id.code
                cuis = incident.cuis
                cufd = incident.cufd_log_id.cufd
                xml_file = tar_invoice
                xml_hash = hashed_xml
                date = self.getTime().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
                result = bo_sync.send_invoice_event(company,
                                                    selling,
                                                    branch,
                                                    cuis,
                                                    cufd,
                                                    incident.invoice_event_id.code,
                                                    incident.invoice_event_id.description,
                                                    incident.begin_date,
                                                    incident.end_date,
                                                    incident.cufd_log_id.cufd)
                if result.transaccion:
                    event_code = result.codigoRecepcionEventoSignificativo
                else:
                    mensaje_list = result.mensajesList[0]
                    raise ValidationError(_('Error SIAT:\n'
                                            'Codigo %s.- %s\n') % (str(mensaje_list.codigo), mensaje_list.descripcion))

                incident.write({'sin_code': event_code})

                cafc = ''
                invoices_len = len(invoice)
                result = bo_sync.send_invoice_paquete(self.company_id,
                                                      selling,
                                                      branch,
                                                      sector,
                                                      cuis,
                                                      cufd,
                                                      xml_file,
                                                      xml_hash,
                                                      date,
                                                      cafc,
                                                      invoices_len,
                                                      event_code)
                if result.transaccion:
                    incident.siat_code = result.codigoRecepcion
                    if result.codigoEstado == 901:
                        incident.state = 'process'
                    else:
                        incident.state = 'done'
                else:
                    mensaje_list = result.mensajesList[0]
                    raise ValidationError(_('Error SIAT:\n'
                                            'Codigo %s.- %s\n') % (str(mensaje_list.codigo), mensaje_list.descripcion))
            return True
        else:
            return False

    def confirm_invoice_paquete(self):
        incidents = self.env['invoice.incident'].search([('state', '=', 'process'), ('siat_code', '!=', False)])
        bo_sync = self.env['sin.sync']
        for incident in incidents:
            company = incident.company_id
            selling = incident.selling_point_id.id_selling_point
            branch = incident.selling_point_id.branch_office_id.id_branch_office
            sector = incident.sector_siat_id.code
            cuis = incident.cuis
            cufd = incident.cufd_log_id.cufd
            result = bo_sync.confirm_invoice_paquete(company,
                                                     selling,
                                                     branch,
                                                     sector,
                                                     cuis,
                                                     cufd,
                                                     incident.siat_code)
            if result.transaccion:
                if result.codigoEstado == 901:
                    incident.state = 'process'
                elif result.codigoEstado == 904:
                    incident.state = 'error'
                else:
                    incident.siat_code = result.codigoRecepcion
                    incident.state = 'done'
                    invoices = self.search([('incident_id', '=', incident.id)])
                    for invoice in invoices:
                        invoice.l10n_bo_emission_type = '1'
                        if incident.company_id.l10n_bo_ambience.id_ambience == 1:
                            url = "https://siat.impuestos.gob.bo/consulta/QR?nit=%s&cuf=%s&numero=%s" % (
                                invoice.company_id.vat, invoice.l10n_bo_cuf, invoice.l10n_bo_invoice_number)
                        else:
                            url = "https://pilotosiat.impuestos.gob.bo/consulta/QR?nit=%s&cuf=%s&numero=%s" % (
                                invoice.company_id.vat, invoice.l10n_bo_cuf, invoice.l10n_bo_invoice_number)
                        invoice.l10n_bo_url = url
                        invoice.generate_qr_code(url)
                        invoice.l10n_bo_code_receipt = incident.siat_code

            else:
                mensaje_list = result.mensajesList[0]
                raise ValidationError(_('Error SIAT:\n'
                                        'Codigo %s.- %s\n') % (str(mensaje_list.codigo), mensaje_list.descripcion))
