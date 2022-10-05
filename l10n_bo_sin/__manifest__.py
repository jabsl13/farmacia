# -*- coding: utf-8 -*-

{
    "name": "Bolivia - Accounting",
    "version": "14.0.0.3",
    "description": """
Bolivian accounting chart and tax localization.

Plan contable boliviano e impuestos de acuerdo a disposiciones vigentes

    """,
    "author": "Alpha Systems - Indasoge",
    'category': 'Accounting/Localizations/Account Charts',
    "depends": ["account", "account_tax_python"],
    "data": [
        "data/l10n_bo_chart_data.xml",
        "data/account.account.template.csv",
        "data/l10n_bo_chart_post_data.xml",
        'data/account_data.xml',
        'data/account_tax_report_data.xml',
        # "data/account_tax_data.xml",
        'data/account_tax_template_data.xml',
        "data/account_chart_template_data.xml",
    ],
    'demo': [
        # 'demo/demo_company.xml',
    ],
    'license': 'LGPL-3',
}
