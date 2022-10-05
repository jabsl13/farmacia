from odoo import fields, models, _
import zeep
from odoo.exceptions import ValidationError
import requests.exceptions
import socket


class SinSync(models.Model):
    _name = 'sin.sync'
    _description = 'Recurrent SIN Api calls'

    name = fields.Char(string='Sincronización SIAT', required=True)
    dosage_id = fields.Many2one('invoice.dosage', string='Dosage', required=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)

    def _get_token(self, company_id):
        return "TokenApi " + company_id.l10n_bo_token

    # SERVICIO DE OBTENCIÓN DE CÓDIGOS
    def check_communication(self, company_id):
        token = self._get_token(company_id)
        settings = zeep.Settings(
            extra_http_headers={'apikey': str(token)})
        try:
            client = zeep.Client(
                wsdl='https://pilotosiatservicios.impuestos.gob.bo/v2/FacturacionCodigos?wsdl',
                settings=settings)
            result = client.service.verificarComunicacion()
            return True, result
        except requests.exceptions.HTTPError as errh:
            return False, str(errh)
        except requests.exceptions.ConnectionError as errc:
            return False, str(errc)
        except requests.exceptions.Timeout as errt:
            return False, str(errt)
        except requests.exceptions.RequestException as err:
            return False, str(err)

    def get_cuis(self, ambiente, modalidad, codSistema, codSucursal, puntoVenta, nit, company_id):
        if not ambiente:
            raise ValidationError(_('Error:\n'
                                    'Defina ambiente en la configuracion de contabilidad \n'))
        if not nit:
            raise ValidationError(_('Error:\n'
                                    'Defina NIT en la compañia actual\n'))
        token = self._get_token(company_id)
        settings = zeep.Settings(extra_http_headers={'apikey': str(token)})
        client = zeep.Client(
            wsdl='https://pilotosiatservicios.impuestos.gob.bo/v2/FacturacionCodigos?wsdl',
            settings=settings)
        params = {'SolicitudCuis': {
            'codigoAmbiente': ambiente,
            'codigoSistema': codSistema,
            'nit': nit,
            'codigoModalidad': modalidad,
            'codigoSucursal': codSucursal,
            'codigoPuntoVenta': puntoVenta,
        }}
        # Generar mensaje en caso de error
        result = client.service.cuis(**params)
        if result.codigo is None:
            mensajeList = result.mensajesList[0]
            raise ValidationError(_('Error SIAT:\n'
                                    'Codigo %s.- %s\n') % (str(mensajeList.codigo), mensajeList.descripcion))
        return result.codigo

    def get_cufd(self, ambiente, modalidad, codSistema, codSucursal, puntoVenta, nit, company_id, cuis):
        token = self._get_token(company_id)
        settings = zeep.Settings(extra_http_headers={'apikey': str(token)})
        client = zeep.Client(
            wsdl='https://pilotosiatservicios.impuestos.gob.bo/v2/FacturacionCodigos?wsdl',
            settings=settings)
        params = {'SolicitudCufd': {
            'codigoAmbiente': ambiente,
            'codigoSistema': codSistema,
            'nit': nit,
            'codigoModalidad': modalidad,
            'cuis': cuis,
            'codigoSucursal': codSucursal,
            'codigoPuntoVenta': puntoVenta
        }}
        result = client.service.cufd(**params)
        if result.codigo is None:
            mensajeList = result.mensajesList[0]
            raise ValidationError(_('Error SIAT:\n'
                                    'Codigo %s.- %s\n') % (str(mensajeList.codigo), mensajeList.descripcion))
        return result

    def _sync_general(self, ambiente, puntoVenta, codSistema, codSucursal, cuis, nit, company_id):
        if not ambiente:
            raise ValidationError(_('Error:\n'
                                    'Defina ambiente en la configuracion de contabilidad \n'))
        if not cuis:
            raise ValidationError(_('Error:\n'
                                    'Defina CUIS en la Dosificación actual\n'))

        if not nit:
            raise ValidationError(_('Error:\n'
                                    'Defina NIT en la compañia actual\n'))

        token = self._get_token(company_id)
        settings = zeep.Settings(extra_http_headers={'apikey': str(token)})
        client = zeep.Client(wsdl='https://pilotosiatservicios.impuestos.gob.bo/v2/FacturacionSincronizacion?wsdl',
                             settings=settings)
        params = {'SolicitudSincronizacion': {
            'codigoAmbiente': ambiente,
            'codigoSistema': codSistema,
            'nit': nit,
            'codigoPuntoVenta': puntoVenta,
            'codigoSucursal': codSucursal,
            'cuis': cuis,
        }}
        return {'client': client, 'params': params, 'ambience': ambiente}

    def sync_activities(self, ws_method):
        client = ws_method['client']
        params = ws_method['params']
        result = client.service.sincronizarActividades(**params)
        activities = self.env['l10n_bo.company.activities']
        for activity in result.listaActividades:
            activity_type = activities.search([('code', '=', activity.codigoCaeb)])
            if not activity_type:
                new_record = {
                    'code': activity.codigoCaeb,
                    'name': activity.descripcion,
                    'type': activity.tipoActividad
                }
                activities.create(new_record)

    def sync_fecha_hora(self, ws_method):
        client = ws_method['client']
        params = ws_method['params']
        result = client.service.sincronizarFechaHora(**params)
        date_time = self.env['boedi.date.time']
        new_record = {
            'name': result.fechaHora,
            'date_time': result.fechaHora
        }
        date_time.create(new_record)

    def sync_actividades_doc_sector(self, ws_method):
        client = ws_method['client']
        params = ws_method['params']
        result = client.service.sincronizarListaActividadesDocumentoSector(
            **params)
        activities_doc_sec = self.env['activity.doc.sector']
        for act_doc_sec in result.listaActividadesDocumentoSector:
            dact_doc_sec_type = activities_doc_sec.search([('activity_code', '=', act_doc_sec.codigoActividad)])
            if not dact_doc_sec_type:
                new_record = {
                    'name': act_doc_sec.codigoActividad,
                    'activity_code': act_doc_sec.codigoActividad,
                    'sector_doc_code': act_doc_sec.codigoDocumentoSector,
                    'sector_doc_type': act_doc_sec.tipoDocumentoSector
                }
                activities_doc_sec.create(new_record)

    def sync_invoice_caption(self, ws_method):
        client = ws_method['client']
        params = ws_method['params']
        result = client.service.sincronizarListaLeyendasFactura(
            **params)
        inv_caption = self.env['invoice.caption']
        for inv_cap in result.listaLeyendas:
            inv_cap_type = inv_caption.search([('activity_code', '=', inv_cap.codigoActividad)])
            if not inv_cap_type:
                new_record = {
                    'name': inv_cap.descripcionLeyenda,
                    'activity_code': inv_cap.codigoActividad,
                    'description': inv_cap.descripcionLeyenda
                }
                inv_caption.create(new_record)

    def sync_messages_service(self, ws_method):
        client = ws_method['client']
        params = ws_method['params']
        result = client.service.sincronizarListaMensajesServicios(
            **params)
        message_serv = self.env['messages.service']
        for mes_serv in result.listaCodigos:
            message_serv_type = message_serv.search([('code', '=', mes_serv.codigoClasificador)])
            if not message_serv_type:
                new_record = {
                    'name': mes_serv.descripcion,
                    'code': mes_serv.codigoClasificador,
                    'description': mes_serv.descripcion
                }
                message_serv.create(new_record)

    def sync_sin_items(self, ws_method):
        client = ws_method['client']
        params = ws_method['params']
        result = client.service.sincronizarListaProductosServicios(**params)
        sin_items = self.env['sin.items']
        for sin_item in result.listaCodigos:
            sin_item_type = sin_items.search([('sin_code', '=', sin_item.codigoProducto)])
            if not sin_item_type:
                activity_id = self.env['l10n_bo.company.activities'].search([('code', '=', sin_item.codigoActividad)])
                new_record = {
                    'name': sin_item.descripcionProducto,
                    'sin_code': sin_item.codigoProducto,
                    'description': sin_item.descripcionProducto,
                    'activity_code': activity_id[0].id
                }
                sin_items.create(new_record)

    def sync_invoice_events(self, ws_method):
        client = ws_method['client']
        params = ws_method['params']
        result = client.service.sincronizarParametricaEventosSignificativos(
            **params)
        invoice_event = self.env['invoice.event']
        for inv_ev in result.listaCodigos:
            inv_ev_type = invoice_event.search([('code', '=', inv_ev.codigoClasificador)])
            if not inv_ev_type:
                new_record = {
                    'name': inv_ev.descripcion,
                    'code': inv_ev.codigoClasificador,
                    'description': inv_ev.descripcion
                }
                invoice_event.create(new_record)

    def sync_null_reasons(self, ws_method):
        client = ws_method['client']
        params = ws_method['params']
        result = client.service.sincronizarParametricaMotivoAnulacion(**params)
        null_reason = self.env['null.reason']
        for null_re in result.listaCodigos:
            null_re_type = null_reason.search([('code', '=', null_re.codigoClasificador)])
            if not null_re_type:
                new_record = {
                    'name': null_re.descripcion,
                    'code': null_re.codigoClasificador,
                    'description': null_re.descripcion
                }
                null_reason.create(new_record)

    def sync_native_country(self, ws_method):
        client = ws_method['client']
        params = ws_method['params']
        result = client.service.sincronizarParametricaPaisOrigen(
            **params)
        native_country = self.env['native.country']
        for nat_co in result.listaCodigos:
            nat_co_type = native_country.search([('code', '=', nat_co.codigoClasificador)])
            if not nat_co_type:
                new_record = {
                    'name': nat_co.descripcion,
                    'code': nat_co.codigoClasificador,
                    'description': nat_co.descripcion
                }
                native_country.create(new_record)

    def sync_id_type(self, ws_method):
        client = ws_method['client']
        params = ws_method['params']
        result = client.service.sincronizarParametricaTipoDocumentoIdentidad(**params)
        id_type = self.env['id.type']
        for id_t in result.listaCodigos:
            id_t_type = id_type.search([('id_type_code', '=', id_t.codigoClasificador)])
            if not id_t_type:
                new_record = {
                    'name': id_t.descripcion,
                    'id_type_code': id_t.codigoClasificador,
                    'description': id_t.descripcion
                }
                id_type.create(new_record)

    def sync_document_sec_type(self, ws_method):
        client = ws_method['client']
        params = ws_method['params']
        result = client.service.sincronizarParametricaTipoDocumentoSector(**params)
        document_sec_type = self.env['document.sec.type']
        for doc_sec_type in result.listaCodigos:
            document_type = document_sec_type.search([('code', '=', doc_sec_type.codigoClasificador)])
            if not document_type:
                new_record = {
                    'name': doc_sec_type.descripcion,
                    'code': doc_sec_type.codigoClasificador,
                    'description': doc_sec_type.descripcion
                }
                document_sec_type.create(new_record)

    def sync_invoice_type_siat(self, ws_method):
        client = ws_method['client']
        params = ws_method['params']
        result = client.service.sincronizarParametricaTiposFactura(**params)
        inv_type = self.env['invoice.type.siat']
        for inv_list in result.listaCodigos:
            document_type = inv_type.search([('code', '=', inv_list.codigoClasificador)])
            if not document_type:
                new_record = {
                    'name': inv_list.descripcion,
                    'code': inv_list.codigoClasificador
                }
                inv_type.create(new_record)

    def sync_sale_point_type(self, ws_method):
        client = ws_method['client']
        params = ws_method['params']
        result = client.service.sincronizarParametricaTipoPuntoVenta(**params)
        inv_type = self.env['sale.point.type']
        for inv_list in result.listaCodigos:
            document_type = inv_type.search([('code', '=', inv_list.codigoClasificador)])
            if not document_type:
                new_record = {
                    'name': inv_list.descripcion,
                    'code': inv_list.codigoClasificador
                }
                inv_type.create(new_record)

    def sync_type_rooms(self, ws_method):
        client = ws_method['client']
        params = ws_method['params']
        result = client.service.sincronizarParametricaTipoHabitacion(**params)
        inv_type = self.env['type.rooms']
        for inv_list in result.listaCodigos:
            document_type = inv_type.search([('code', '=', inv_list.codigoClasificador)])
            if not document_type:
                new_record = {
                    'name': inv_list.descripcion,
                    'code': inv_list.codigoClasificador
                }
                inv_type.create(new_record)

    def sync_type_emission(self, ws_method):
        client = ws_method['client']
        params = ws_method['params']
        result = client.service.sincronizarParametricaTipoEmision(**params)
        inv_type = self.env['type.emission']
        for inv_list in result.listaCodigos:
            document_type = inv_type.search([('code', '=', inv_list.codigoClasificador)])
            if not document_type:
                new_record = {
                    'name': inv_list.descripcion,
                    'code': inv_list.codigoClasificador
                }
                inv_type.create(new_record)

    def sync_currency_siat(self, ws_method):
        client = ws_method['client']
        params = ws_method['params']
        result = client.service.sincronizarParametricaTipoMoneda(**params)
        inv_type = self.env['currency.siat']
        for inv_list in result.listaCodigos:
            document_type = inv_type.search([('code', '=', inv_list.codigoClasificador)])
            if not document_type:
                new_record = {
                    'name': inv_list.descripcion,
                    'code': inv_list.codigoClasificador
                }
                inv_type.create(new_record)

    def sync_payment_method(self, ws_method):
        client = ws_method['client']
        params = ws_method['params']
        result = client.service.sincronizarParametricaTipoMetodoPago(**params)
        payment_method = self.env['payment.method']
        for payment_met in result.listaCodigos:
            payment_method_type = payment_method.search([('code', '=', payment_met.codigoClasificador)])
            if not payment_method_type:
                new_record = {
                    'name': payment_met.descripcion,
                    'code': payment_met.codigoClasificador,
                    'description': payment_met.descripcion
                }
                payment_method.create(new_record)

    def sync_measure_unit(self, ws_method):
        client = ws_method['client']
        params = ws_method['params']
        result = client.service.sincronizarParametricaUnidadMedida(**params)
        measure_unit = self.env['measure.unit']
        for measure in result.listaCodigos:
            measure_type = measure_unit.search([('measure_unit_code', '=', measure.codigoClasificador)])
            if not measure_type:
                new_record = {
                    'name': measure.descripcion,
                    'measure_unit_code': measure.codigoClasificador,
                    'description': measure.descripcion
                }
                measure_unit.create(new_record)

    # Métodos de Facturacion Electrónica
    def send_invoice(self, company, selling, branch, sector, cuis, cufd, xml_file, xml_hash, date):
        ambience = company.l10n_bo_ambience.id_ambience
        code_emission = 1  # Describe si la emisión se realizó en línea
        code_modality = company.l10n_bo_invoicing_modality.id_modality
        system_code = str(company.l10n_bo_system_code)
        cuis = str(cuis)
        nit = str(company.vat)
        token = self._get_token(company)
        settings = zeep.Settings(
            extra_http_headers={'apikey': str(token)})
        client = zeep.Client(
            wsdl='https://pilotosiatservicios.impuestos.gob.bo/v2/ServicioFacturacionCompraVenta?wsdl',
            settings=settings)

        params = {'SolicitudServicioRecepcionFactura': {
            'codigoAmbiente': ambience,
            'codigoPuntoVenta': selling,
            'codigoSistema': system_code,
            'codigoSucursal': branch,
            'nit': nit,
            'codigoDocumentoSector': sector.code_type or '1',
            'codigoEmision': code_emission,
            'codigoModalidad': code_modality,
            'cufd': cufd,
            'cuis': cuis,
            'tipoFacturaDocumento': sector.code,
            'archivo': xml_file,
            'fechaEnvio': date,
            'hashArchivo': xml_hash
        }
        }
        result = client.service.recepcionFactura(**params)
        return result

    def send_invoice_dc(self, company, selling, branch, sector, cuis, cufd, xml_file, xml_hash, date):
        ambience = company.l10n_bo_ambience.id_ambience
        code_emission = 1  # Describe si la emisión se realizó en línea
        code_modality = company.l10n_bo_invoicing_modality.id_modality
        system_code = str(company.l10n_bo_system_code)
        cuis = str(cuis)
        nit = str(company.vat)
        token = self._get_token(company)
        settings = zeep.Settings(
            extra_http_headers={'apikey': str(token)})
        client = zeep.Client(
            wsdl='https://pilotosiatservicios.impuestos.gob.bo/v2/ServicioFacturacionDocumentoAjuste?wsdl',
            settings=settings)

        params = {'SolicitudServicioRecepcionDocumentoAjuste': {
            'codigoAmbiente': ambience,
            'codigoPuntoVenta': selling,
            'codigoSistema': system_code,
            'codigoSucursal': branch,
            'nit': nit,
            'codigoDocumentoSector': sector.code or '1',
            'codigoEmision': code_emission,
            'codigoModalidad': code_modality,
            'cufd': cufd,
            'cuis': cuis,
            'tipoFacturaDocumento': 3,
            'archivo': xml_file,
            'fechaEnvio': date,
            'hashArchivo': xml_hash
        }
        }
        result = client.service.recepcionDocumentoAjuste(**params)
        return result

    def cancel_invoice(self, company, selling, branch, sector, cuis, cuf, cufd, reason_code):
        ambience = company.l10n_bo_ambience.id_ambience
        code_modality = company.l10n_bo_invoicing_modality.id_modality
        nit = str(company.vat)
        system_code = str(company.l10n_bo_system_code)
        code_emission = 1  # Describe si la emisión se realizó en línea
        token = self._get_token(company)
        settings = zeep.Settings(
            extra_http_headers={'apikey': str(token)})
        client = zeep.Client(
            wsdl='https://pilotosiatservicios.impuestos.gob.bo/v2/ServicioFacturacionCompraVenta?wsdl',
            settings=settings)
        params = {'SolicitudServicioAnulacionFactura': {
            'codigoAmbiente': ambience,
            'codigoDocumentoSector': sector.code_type or '1',
            'codigoEmision': code_emission,
            'codigoModalidad': code_modality,
            'codigoPuntoVenta': selling,
            'codigoSistema': system_code,
            'codigoSucursal': branch,
            'cufd': cufd,
            'cuis': cuis,
            'nit': nit,
            'tipoFacturaDocumento': sector.code,
            'codigoMotivo': str(reason_code.code),
            'cuf': cuf
        }
        }
        result = client.service.anulacionFactura(**params)
        return result

        # Métodos de Facturacion Electrónica

    def send_invoice_paquete(self, company, selling, branch, sector, cuis, cufd, xml_file, xml_hash, date, cafc,
                             invoices_len, event):
        ambience = company.l10n_bo_ambience.id_ambience
        code_emission = 2  # Describe si la emisión se realizó offline
        code_modality = company.l10n_bo_invoicing_modality.id_modality
        system_code = str(company.l10n_bo_system_code)
        nit = company.vat
        token = self._get_token(company)
        settings = zeep.Settings(
            extra_http_headers={'apikey': str(token)})
        client = zeep.Client(
            wsdl='https://pilotosiatservicios.impuestos.gob.bo/v2/ServicioFacturacionCompraVenta?wsdl',
            settings=settings)

        params = {'SolicitudServicioRecepcionPaquete': {
            'codigoAmbiente': ambience,
            'codigoPuntoVenta': selling,
            'codigoSistema': system_code,
            'codigoSucursal': branch,
            'nit': nit,
            'codigoDocumentoSector': sector or '1',
            'codigoEmision': code_emission,
            'codigoModalidad': code_modality,
            'cufd': cufd,
            'cuis': cuis,
            'tipoFacturaDocumento': sector,
            'archivo': xml_file,
            'fechaEnvio': date,
            'hashArchivo': xml_hash,
            'cafc': cafc,
            'cantidadFacturas': invoices_len,
            'codigoEvento': event,
        }
        }
        result = client.service.recepcionPaqueteFactura(**params)
        return result

    def confirm_invoice_paquete(self, company, selling, branch, sector, cuis, cufd, code_receipt):
        ambience = company.l10n_bo_ambience.id_ambience
        code_emission = 2  # Describe si la emisión se realizó offline
        code_modality = company.l10n_bo_invoicing_modality.id_modality
        system_code = company.l10n_bo_system_code
        nit = company.vat
        token = self._get_token(company)
        settings = zeep.Settings(
            extra_http_headers={'apikey': str(token)})
        client = zeep.Client(
            wsdl='https://pilotosiatservicios.impuestos.gob.bo/v2/ServicioFacturacionCompraVenta?wsdl',
            settings=settings)

        params = {'SolicitudServicioValidacionRecepcionPaquete': {
            'codigoAmbiente': ambience,
            'codigoPuntoVenta': selling,
            'codigoSistema': system_code,
            'codigoSucursal': branch,
            'nit': nit,
            'codigoDocumentoSector': sector or '1',
            'codigoEmision': code_emission,
            'codigoModalidad': code_modality,
            'cufd': cufd,
            'cuis': cuis,
            'tipoFacturaDocumento': sector,
            'codigoRecepcion': code_receipt
        }
        }
        result = client.service.validacionRecepcionPaqueteFactura(**params)
        return result

    def send_invoice_event(self, company, puntoventa, codSucursal, cuis, cufd, codigoMotivoEvento,
                           descripcion, fechaInicioEvento, fechaFinEvento, cufdEvento):
        ambiente = company.l10n_bo_ambience.id_ambience
        codSistema = company.l10n_bo_system_code
        nit = company.vat
        token = self._get_token(company)
        settings = zeep.Settings(
            extra_http_headers={'apikey': str(token)})
        client = zeep.Client(
            wsdl='https://pilotosiatservicios.impuestos.gob.bo/v2/FacturacionOperaciones?wsdl',
            settings=settings)
        params = {'SolicitudEventoSignificativo': {
            'codigoAmbiente': ambiente,
            'codigoSistema': codSistema,
            'nit': nit,
            'cuis': cuis,
            'cufd': cufd,
            'codigoSucursal': codSucursal,
            'codigoPuntoVenta': puntoventa,
            'codigoMotivoEvento': codigoMotivoEvento,
            'descripcion': descripcion,
            'fechaHoraInicioEvento': fechaInicioEvento,
            'fechaHoraFinEvento': fechaFinEvento,
            'cufdEvento': cufdEvento
        }
        }

        result = client.service.registroEventoSignificativo(**params)
        return result

    def conexion(self):
        resp = False
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        try:
            s.connect(("www.google.com", 80))
        except (socket.gaierror, socket.timeout):
            print("Sin conexión a internet")
        else:
            print("Con conexión a internet")
            resp = True
        s.close()
        return resp

    # Método de consumo Certificación Catalogos
    def cert_sync_catal(self):
        ambience = self.company_id.l10n_bo_ambience.id_ambience
        selling_point = self.dosage_id.selling_point_id.id_selling_point
        branch_office = self.dosage_id.selling_point_id.branch_office_id.id_branch_office

        system_code = str(self.company_id.l10n_bo_system_code)
        cuis = self.dosage_id.cuis
        nit = str(self.company_id.vat)

        ws_method_sync = self._sync_general(ambience,
                                            selling_point,
                                            system_code,
                                            branch_office,
                                            cuis,
                                            nit,
                                            self.company_id)
        # Sincronizar Datos SIAT
        # 1 Actividades
        self.sync_activities(ws_method_sync)
        # 2 Fecha y Hora
        self.sync_fecha_hora(ws_method_sync)
        # 3 Actividades Documento Sector
        self.sync_document_sec_type(ws_method_sync)
        # 4 Leyenda Factura
        self.sync_invoice_caption(ws_method_sync)
        # 5 Mensaje Servicios
        self.sync_messages_service(ws_method_sync)
        # 6 ProductServicios
        self.sync_sin_items(ws_method_sync)
        # 7 EventoSignificativo
        self.sync_invoice_events(ws_method_sync)
        # 8 MotivoAnulacion
        self.sync_null_reasons(ws_method_sync)
        # 9 PaisOrigen
        self.sync_native_country(ws_method_sync)
        # 10 TipoDocumentoIdentidad
        self.sync_id_type(ws_method_sync)
        # 11 TipoDocumentoSector
        self.sync_actividades_doc_sector(ws_method_sync)
        # 12 TipoEmision
        self.sync_type_emission(ws_method_sync)
        # 13 TipoHabitacion
        self.sync_type_rooms(ws_method_sync)
        # 14 TipoMetodoPago
        self.sync_payment_method(ws_method_sync)
        # 15 TipoMoneda
        self.sync_currency_siat(ws_method_sync)
        # 16 TipoPuntoVenta
        self.sync_sale_point_type(ws_method_sync)
        # 17 TipoFactura
        self.sync_invoice_type_siat(ws_method_sync)
        # 18 UnidadMedida
        self.sync_measure_unit(ws_method_sync)
