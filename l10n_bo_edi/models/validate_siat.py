from odoo import fields, models, _
import time
from datetime import timedelta, datetime
import base64
from odoo.exceptions import ValidationError, UserError
import tarfile
import io


class ValidateSiat(models.Model):
    _name = 'validate.siat'
    _description = 'Validate system siat'
    name = fields.Char(string='Validate Name', required=True)
    dosage_one = fields.Many2one('invoice.dosage', string='Dosage One', required=True)
    dosage_two = fields.Many2one('invoice.dosage', string='Dosage Two', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

    def step1(self):
        self.dosage_one.get_cuis_dosage()
        self.dosage_two.get_cuis_dosage()

    def step2(self):
        sync = self.env['sin.sync']
        for i in range(50):
            # Pdv 1
            ambience = self.company_id.l10n_bo_ambience.id_ambience
            selling_point = self.dosage_one.selling_point_id.id_selling_point
            branch_office = self.dosage_one.selling_point_id.branch_office_id.id_branch_office
            system_code = self.company_id.l10n_bo_system_code
            cuis = self.dosage_one.cuis
            nit = self.company_id.vat

            ws_method_sync = sync._sync_general(ambience,
                                                selling_point,
                                                system_code,
                                                branch_office,
                                                cuis,
                                                nit,
                                                self.company_id)
            sync.sync_activities(ws_method_sync)
            sync.sync_fecha_hora(ws_method_sync)
            sync.sync_document_sec_type(ws_method_sync)
            sync.sync_invoice_caption(ws_method_sync)
            sync.sync_messages_service(ws_method_sync)
            sync.sync_sin_items(ws_method_sync)
            sync.sync_invoice_events(ws_method_sync)
            sync.sync_null_reasons(ws_method_sync)
            sync.sync_native_country(ws_method_sync)
            sync.sync_id_type(ws_method_sync)
            sync.sync_actividades_doc_sector(ws_method_sync)
            sync.sync_type_emission(ws_method_sync)
            sync.sync_type_rooms(ws_method_sync)
            sync.sync_payment_method(ws_method_sync)
            sync.sync_currency_siat(ws_method_sync)
            sync.sync_sale_point_type(ws_method_sync)
            sync.sync_invoice_type_siat(ws_method_sync)
            sync.sync_measure_unit(ws_method_sync)

            # Pdv 2
            ambience = self.company_id.l10n_bo_ambience.id_ambience
            selling_point = self.dosage_two.selling_point_id.id_selling_point
            branch_office = self.dosage_two.selling_point_id.branch_office_id.id_branch_office
            system_code = self.company_id.l10n_bo_system_code
            cuis = self.dosage_two.cuis
            nit = self.company_id.vat

            ws_method_sync = sync._sync_general(ambience,
                                                selling_point,
                                                system_code,
                                                branch_office,
                                                cuis,
                                                nit,
                                                self.company_id)
            sync.sync_activities(ws_method_sync)
            sync.sync_fecha_hora(ws_method_sync)
            sync.sync_document_sec_type(ws_method_sync)
            sync.sync_invoice_caption(ws_method_sync)
            sync.sync_messages_service(ws_method_sync)
            sync.sync_sin_items(ws_method_sync)
            sync.sync_invoice_events(ws_method_sync)
            sync.sync_null_reasons(ws_method_sync)
            sync.sync_native_country(ws_method_sync)
            sync.sync_id_type(ws_method_sync)
            sync.sync_actividades_doc_sector(ws_method_sync)
            sync.sync_type_emission(ws_method_sync)
            sync.sync_type_rooms(ws_method_sync)
            sync.sync_payment_method(ws_method_sync)
            sync.sync_currency_siat(ws_method_sync)
            sync.sync_sale_point_type(ws_method_sync)
            sync.sync_invoice_type_siat(ws_method_sync)
            sync.sync_measure_unit(ws_method_sync)
            print(str(i))
            time.sleep(0.3)

    def step3(self):
        for i in range(100):
            self.dosage_one.get_cufd_dosage()
            self.dosage_two.get_cufd_dosage()
            time.sleep(0.3)

    def step4(self):
        invoice = self.env['account.move']
        sync = self.env['sin.sync']
        util = self.env['l10n_bo.edi.util']

    def step5(self):
        invoice = self.env['account.move']
        sync = self.env['sin.sync']
        events = self.env['invoice.event'].search([], order='code,id')
        for event in events:
            date_zone = invoice.getTime()
            date_zone_init = date_zone + timedelta(minutes=event.id, seconds=40)
            date_zone_end = date_zone + timedelta(minutes=event.id + 1, seconds=40)
            for i in range(5):
                val_incident = {
                    'invoice_event_id': event.id,
                    'description': event.name,
                    'begin_date': date_zone_init.strftime("%Y-%m-%d %H:%M:%S"),
                    'end_date': date_zone_end.strftime("%Y-%m-%d %H:%M:%S"),
                    'selling_point_id': self.dosage_one.selling_point_id.id,
                    'cuis': self.dosage_one.cuis,
                    'sector_siat_id': self.dosage_one.sector_siat_id.id,
                    'company_id': self.company_id.id,
                }
                incident = self.env['invoice.incident'].create(val_incident)
                selling = self.dosage_one.selling_point_id.id_selling_point
                branch = self.dosage_one.selling_point_id.branch_office_id.id_branch_office
                sync.send_invoice_event(self.company_id,
                                        selling,
                                        branch,
                                        incident.cuis,
                                        incident.cufd_log_id.cufd,
                                        incident.invoice_event_id.code,
                                        incident.invoice_event_id.description,
                                        incident.begin_date,
                                        incident.end_date,
                                        incident.cufd_log_id.cufd)

    def step6(self):
        invoice = self.env['account.move']
        sync = self.env['sin.sync']
        util = self.env['l10n_bo.edi.util']
        events = self.env['invoice.event'].search([], order='code,id')
        for event in events:
            date_zone = invoice.getTime()
            date_zone_init = date_zone + timedelta(minutes=event.id, seconds=40)
            date_zone_end = date_zone + timedelta(minutes=event.id + 1, seconds=40)

            # pdv0
            val_incident = {
                'invoice_event_id': event.id,
                'description': event.name,
                'begin_date': date_zone_init.strftime("%Y-%m-%d %H:%M:%S"),
                'end_date': date_zone_end.strftime("%Y-%m-%d %H:%M:%S"),
                'selling_point_id': self.dosage_one.selling_point_id.id,
                'cuis': self.dosage_one.cuis,
                'sector_siat_id': self.dosage_one.sector_siat_id.id,
                'company_id': self.company_id.id,
            }
            incident = self.env['invoice.incident'].create(val_incident)
            selling = self.dosage_one.selling_point_id.id_selling_point
            branch = self.dosage_one.selling_point_id.branch_office_id.id_branch_office
            result = sync.send_invoice_event(self.company_id,
                                             selling,
                                             branch,
                                             incident.cuis,
                                             incident.cufd_log_id.cufd,
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

            buf = io.BytesIO()
            with tarfile.open(fileobj=buf, mode='w:gz') as tar:
                for i in range(10):
                    invoice = self.create_test_invoice_dos(self.dosage_one)
                    invoice.incident_id = incident.id
                    invoice.with_context(offline=True).post()
                    info = tarfile.TarInfo(invoice.l10n_bo_xml_filename)
                    info.mtime = time.time()
                    file_xml_od = base64.b64decode(invoice.l10n_bo_xml)
                    file_xml = io.BytesIO(file_xml_od)
                    info.size = len(file_xml_od)
                    tar.addfile(info, file_xml)
            tar_invoice = buf.getvalue()
            with open('../fichero.tar.gz', 'wb') as f:
                f.write(buf.getvalue())
            hashed_xml = invoice._GetHashSha256(tar_invoice)
            sector = incident.sector_siat_id.code
            date = invoice.getTime().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
            cafc = ''
            invoices_len = 10
            result = sync.send_invoice_paquete(self.company_id,
                                               selling,
                                               branch,
                                               sector,
                                               incident.cuis,
                                               incident.cufd_log_id.cufd,
                                               tar_invoice,
                                               hashed_xml,
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

            # pdv1
            val_incident = {
                'invoice_event_id': event.id,
                'description': event.name,
                'begin_date': date_zone_init.strftime("%Y-%m-%d %H:%M:%S"),
                'end_date': date_zone_end.strftime("%Y-%m-%d %H:%M:%S"),
                'selling_point_id': self.dosage_two.selling_point_id.id,
                'cuis': self.dosage_two.cuis,
                'sector_siat_id': self.dosage_two.sector_siat_id.id,
                'company_id': self.company_id.id,
            }
            incident = self.env['invoice.incident'].create(val_incident)
            selling = self.dosage_two.selling_point_id.id_selling_point
            branch = self.dosage_two.selling_point_id.branch_office_id.id_branch_office
            result = sync.send_invoice_event(self.company_id,
                                             selling,
                                             branch,
                                             incident.cuis,
                                             incident.cufd_log_id.cufd,
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

            buf = io.BytesIO()
            with tarfile.open(fileobj=buf, mode='w:gz') as tar:
                for i in range(10):
                    invoice = self.create_test_invoice_dos(self.dosage_two)
                    invoice.incident_id = incident.id
                    invoice.with_context(offline=True).post()
                    info = tarfile.TarInfo(invoice.l10n_bo_xml_filename)
                    info.mtime = time.time()
                    file_xml_od = base64.b64decode(invoice.l10n_bo_xml)
                    file_xml = io.BytesIO(file_xml_od)
                    info.size = len(file_xml_od)
                    tar.addfile(info, file_xml)
            tar_invoice = buf.getvalue()
            with open('../fichero.tar.gz', 'wb') as f:
                f.write(buf.getvalue())
            hashed_xml = invoice._GetHashSha256(tar_invoice)
            sector = incident.sector_siat_id.code
            date = invoice.getTime().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
            cafc = ''
            invoices_len = 10
            result = sync.send_invoice_paquete(self.company_id,
                                               selling,
                                               branch,
                                               sector,
                                               incident.cuis,
                                               incident.cufd_log_id.cufd,
                                               tar_invoice,
                                               hashed_xml,
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

    def step7(self):
        # Anulacion
        invoice = self.env['account.move']
        sync = self.env['sin.sync']
        util = self.env['l10n_bo.edi.util']
        null_reason_invoice = self.env['null.reason'].search([('code', '=', '1')])
        null_reason_dc = self.env['null.reason'].search([('code', '=', '2')])
        for i in range(2):
            invoice1, invoice2 = self.create_test_invoice()
            invoice1.post()
            # refund1 = self.create_refund(invoice1)
            invoice1.button_draft()
            invoice1.l10n_bo_null_reason = null_reason_invoice[0].id
            invoice1.button_cancel()
            time.sleep(0.1)
            invoice2.post()
            # refund1 = self.create_refund(invoice1)
            invoice2.button_draft()
            invoice2.l10n_bo_null_reason = null_reason_invoice[0].id
            invoice2.button_cancel()
            # refund1.button_draft()
            time.sleep(0.1)
            # refund1.l10n_bo_null_reason = null_reason_dc[0].id
            # refund1.button_draft()
            # refund1.button_cancel()
            time.sleep(0.1)

    def step8(self):
        invoice = self.env['account.move']
        sync = self.env['sin.sync']
        util = self.env['l10n_bo.edi.util']
        for i in range(2):
            invoice1, invoice2 = self.create_test_invoice()
            invoice1.post()
            time.sleep(0.1)
            self.create_refund(invoice1)
            time.sleep(0.1)
            invoice2.post()
            time.sleep(0.1)
            self.create_refund(invoice2)
            time.sleep(0.1)

    def step9(self):
        invoice = self.env['account.move']
        sync = self.env['sin.sync']
        util = self.env['l10n_bo.edi.util']

    def create_test_invoice(self):
        journal = self.env['account.journal'].search([('type', '=', 'sale')])
        partner = self.env['res.partner'].search([('customer_rank', '>=', 1), ('vat', '!=', '')])
        product = self.env['product.product'].search([('product_tmpl_id.sin_item', '!=', False)])
        invoice_create1 = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.context_today(self),
            'date': fields.Date.context_today(self),
            'partner_id': partner[0].id,
            'journal_id': journal[0].id,
            'dosage_id': self.dosage_one.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': product[0].id,
                'price_unit': 1000.0,
                'tax_ids': [(6, 0, product[0].taxes_id.ids)]
            })],
        })
        invoice_create1.onchange_partner_id_sin()

        invoice_create2 = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.context_today(self),
            'date': fields.Date.context_today(self),
            'partner_id': partner[0].id,
            'journal_id': journal[0].id,
            'dosage_id': self.dosage_one.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': product[0].id,
                'price_unit': 1000.0,
                'tax_ids': [(6, 0, product[0].taxes_id.ids)]
            })],
        })
        invoice_create2.onchange_partner_id_sin()
        # invoice_create.onchange_dosage_user_id()

        return invoice_create1, invoice_create2

    def create_test_invoice_dos(self, dosage):
        journal = self.env['account.journal'].search([('type', '=', 'sale')])
        partner = self.env['res.partner'].search([('customer_rank', '>', 1), ('vat', '!=', False)])
        product = self.env['product.product'].search([('product_tmpl_id.sin_item', '!=', False)])
        invoice_create = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.context_today(self),
            'date': fields.Date.context_today(self),
            'partner_id': partner[0].id,
            'journal_id': journal[0].id,
            'dosage_id': self.dosage_one.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': product[0].id,
                'price_unit': 1000.0,
                'tax_ids': [(6, 0, product[0].taxes_id.ids)]
            })],
        })
        invoice_create.onchange_partner_id_sin()
        return invoice_create

    def create_refund(self, invoice):
        invoice.note_credit_debit = True
        move_reversal = self.env['account.move.reversal'].with_context(active_model="account.move",
                                                                       active_ids=[invoice.id]).create({
            'date': fields.Date.context_today(self),
            'reason': 'Test Nota Debito/Credito',
            'refund_method': 'cancel',
            'nota_credito_debito': True,
            'journal_id': invoice.journal_id.id,
        })
        reversal = move_reversal.reverse_moves()
        reverse_move = self.env['account.move'].browse(reversal['res_id'])
        return reverse_move
