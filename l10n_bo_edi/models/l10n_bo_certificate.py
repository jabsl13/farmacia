# -*- coding: utf-8 -*-
import base64
import logging
import ssl
from base64 import b64decode, b64encode
from OpenSSL import crypto
from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class Certificate(models.Model):
    _name = 'l10n_bo.certificate'
    _description = 'Digital Signature'
    _rec_name = 'signature_filename'
    _order = 'id desc'

    content = fields.Binary(string="Certificate", help="File P12")
    content_name = fields.Char(string='P12 Name')
    password = fields.Char(help="Passphrase for P12")

    signature_crt_filename = fields.Char('Signature File Name')
    signature_crt_file = fields.Binary(string='Certificate Crt', help='Certificate crt')

    signature_key_filename = fields.Char('Signature File Name')
    signature_filename = fields.Char('Signature File Name')
    signature_key_file = fields.Binary(string='Certificate Key', help='Certificate key')
    cert_expiration = fields.Datetime(string='Expiration date', help='The date on which the certificate expires',
                                      store=True)
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company.id, required=True, readonly=True)
    user_id = fields.Many2one('res.users', 'Certificate Owner',
                              help='If this certificate has an owner, he will be the only user authorized to use it, '
                                   'otherwise, the certificate will be shared with other users of the current company')
    last_token = fields.Char('Last Token')
    token_time = fields.Datetime('Token Time')

    def create_pem(self):
        self.ensure_one()
        decrypted_content = crypto.load_pkcs12(b64decode(self.content), self.password.encode())
        certificate = decrypted_content.get_certificate()
        private_key = decrypted_content.get_privatekey()
        pem_certificate = crypto.dump_certificate(crypto.FILETYPE_PEM, certificate)
        pem_private_key = crypto.dump_privatekey(crypto.FILETYPE_PEM, private_key)

        # Cleanup pem_content.
        # for to_clean in ('\n', ssl.PEM_HEADER, ssl.PEM_FOOTER):
        #    pem_certificate = pem_certificate.replace(to_clean.encode('UTF-8'), b'')
        self.signature_crt_file = base64.b64encode(pem_certificate)
        self.signature_crt_filename = 'file_crt.pem'
        self.signature_key_file = base64.b64encode(pem_private_key)
        self.signature_key_filename = 'file_key.pem'
