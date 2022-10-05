# -*- coding: utf-8 -*-
{
    'name': """Bolivia - Facturacion en linea""",
    "version": "15.0.0.1",
    'author': "MCM",
    'website': "http://odooboliviaerp.com",
    'category': 'Accounting/Localizations',
    'depends': ['base',
                'sale_management',
                'purchase',
                'account'
                ],
    'external_dependencies': {
        'python': [
            'signxml', 'M2Crypto', 'qrcode'
        ],
    },
    'data': [
        'data/siat_data.xml',
        'views/dte_cuf_view.xml',
        'views/siat_master_data_view.xml',
        'views/company_activities_view.xml',
        'views/account_move_form_inherit.xml',
        'views/base_view_users_form_inherit.xml',
        'views/cufd_view.xml',
        'views/res_partner_form_inherit.xml',
        'views/product_template_form_inherit.xml',
        'views/l10n_bo_edi_actions.xml',
        'views/l10n_bo_certificate_view.xml',
        'views/res_config_settings_view.xml',
        'views/edi_signature.xml',
        'views/report_invoice.xml',
        'security/ir.model.access.csv',
        'reports/graphic_representation.xml',
        'reports/graphic_representation_templates.xml',
        'views/invoice_dosage.xml',
        'views/bo_edi_params_view.xml',
        'views/sin_sync_view.xml',
        'views/validate_siat_view.xml',
        'wizard/account_move_reversal_view.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
