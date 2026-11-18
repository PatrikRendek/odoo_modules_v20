{
    'name': "Slovakia - E-invoicing delivery service (SAPI-SK)",
    'version': '1.0.0',
    'category': 'Accounting/Localizations/EDI',
    'summary': "Send and receive Slovak e-invoices through a certified delivery service (SAPI-SK)",
    'description': """
Connects Odoo to a Slovak certified delivery service ("digital postman") through the
SAPI-SK 1.0 interface: hands the Peppol BIS Billing 3.0 e-invoice over to the service,
follows its delivery status and downloads the received e-invoices as vendor bills.

The module is documented in doc/documentation_en.md (English) and
doc/documentation_sk.md (Slovak).
    """,
    'author': "Patrik Rendek",
    'countries': ['sk'],
    'depends': [
        'account_edi_ubl_cii',
        'l10n_sk_edi_einvoice',
    ],
    'data': [
        'data/ir_cron_data.xml',
        'views/account_move_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'license': 'LGPL-3',
}
