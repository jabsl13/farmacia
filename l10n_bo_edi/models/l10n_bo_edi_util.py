# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64
import hashlib
import logging
import re
import ssl
import urllib3
from lxml import etree
from OpenSSL import crypto
from io import StringIO, BytesIO
from odoo import _, models, api, fields
from copy import deepcopy
from base64 import b64decode, b64encode
from signxml import XMLSigner, XMLVerifier, methods
from odoo.modules.module import get_resource_path
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)

TIMEOUT = 30  # default timeout for all remote operations
pool = urllib3.PoolManager(timeout=TIMEOUT)

SERVER_URL = {
    'SIITEST': 'https://maullin.sii.cl/DTEWS/',
    'SII': 'https://palena.sii.cl/DTEWS/',
}

CLAIM_URL = {
    'SIITEST': 'https://ws2.sii.cl/WSREGISTRORECLAMODTECERT/registroreclamodteservice',
    'SII': 'https://ws1.sii.cl/WSREGISTRORECLAMODTE/registroreclamodteservice',
}

MAX_RETRIES = 20


class L10nBoEdiUtilMixin(models.AbstractModel):
    _name = 'l10n_bo.edi.util'
    _description = 'Utility Methods for Bolivian Electronic Invoicing'

    def _compute_validation_xml(self, xsd_name_file, xml_file):
        xsd_file_path = get_resource_path(
            'l10n_bo_edi',
            'data',
            xsd_name_file,
        )
        parser = etree.XMLParser()
        xsd_root = etree.parse(xsd_file_path, parser=parser)
        schema = etree.XMLSchema(xsd_root)
        xml_root_valid = etree.fromstring(base64.b64decode(xml_file))
        try:
            schema.assertValid(xml_root_valid)
        except etree.DocumentInvalid as err:
            raise ValidationError(_(str(err)))

    def _sign(self, edi_tree, company_id):
        # pem_certificate, pem_private_key, certificate = self._decode_certificate()
        digital_signature = company_id._get_digital_signature(user_id=self.env.user.id)
        pem_certificate = base64.decodebytes(digital_signature.signature_crt_file)
        pem_private_key = base64.decodebytes(digital_signature.signature_key_file)

        for to_clean in ('\n', ssl.PEM_HEADER, ssl.PEM_FOOTER):
            pem_certificate = pem_certificate.replace(to_clean.encode('UTF-8'), b'')

        namespaces = {'ds': 'http://www.w3.org/2000/09/xmldsig#'}

        edi_tree_copy = deepcopy(edi_tree)
        signature_element = edi_tree_copy.xpath('.//ds:Signature', namespaces=namespaces)[0]
        signature_element.getparent().remove(signature_element)

        edi_tree_c14n_str = etree.tostring(edi_tree_copy, method='c14n', exclusive=True, with_comments=True)
        digest_b64 = b64encode(hashlib.new('sha256', edi_tree_c14n_str).digest())
        signature_str = self.env.ref('l10n_bo_edi.bo_signature')._render({'digest_value': digest_b64.decode()})

        # Elimine todos los espacios no útiles y las nuevas líneas en la secuencia
        signature_str = signature_str.replace('\n', '').replace('  ', '')

        signature_tree = etree.fromstring(signature_str)
        signed_info_element = signature_tree.xpath('.//ds:SignedInfo', namespaces=namespaces)[0]
        signature = etree.tostring(signed_info_element, method='c14n', exclusive=True, with_comments=True)
        private_pem_key = crypto.load_privatekey(crypto.FILETYPE_PEM, pem_private_key)
        signature_b64_hash = b64encode(crypto.sign(private_pem_key, signature, 'sha256'))

        signature_tree.xpath('.//ds:SignatureValue', namespaces=namespaces)[0].text = signature_b64_hash
        signature_tree.xpath('.//ds:X509Certificate', namespaces=namespaces)[0].text = pem_certificate
        signed_edi_tree = deepcopy(edi_tree)
        signature_element = signed_edi_tree.xpath('.//ds:Signature', namespaces=namespaces)[0]
        for child_element in signature_tree:
            signature_element.append(child_element)
        return signed_edi_tree

    def _sign_xml(self, edi_tree, pem_certificate, pem_private_key):
        edi_tree_copy = deepcopy(edi_tree)
        signer = XMLSigner(c14n_algorithm='http://www.w3.org/TR/2001/REC-xml-c14n-20010315#WithComments')
        ns = {}
        ns[None] = signer.namespaces['ds']
        signer.namespaces = ns
        signed_root = signer.sign(edi_tree_copy, key=pem_private_key, cert=pem_certificate, always_add_key_value=False)
        XMLVerifier().verify(signed_root, x509_cert=pem_certificate).signed_xml
        tree = signed_root.getroottree()
        file = BytesIO()
        tree.write(file, encoding='utf-8')
        signed_file = file.getvalue()
        file.close()
        return signed_file
        # return tree
