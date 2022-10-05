# -*- coding: utf-8 -*-

from odoo import api, models
import base64


class MailTemplate(models.Model):
    _inherit = "mail.template"

    def _get_edi_attachments_xml(self, document):
        if not document.l10n_bo_xml:
            return []
        return [(document.l10n_bo_xml_filename, document.l10n_bo_xml)]

    def generate_email(self, res_ids, fields):
        res = super().generate_email(res_ids, fields)

        multi_mode = True
        if isinstance(res_ids, int):
            res_ids = [res_ids]
            multi_mode = False

        if self.model not in ['account.move']:
            return res

        records = self.env[self.model].browse(res_ids)
        for record in records:
            record_data = (res[record.id] if multi_mode else res)
            for doc in record:
                record_data.setdefault('attachments', [])
                record_data['attachments'] += self._get_edi_attachments_xml(doc)

        return res
