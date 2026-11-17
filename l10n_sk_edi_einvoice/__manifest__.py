{
    'name': "Slovakia - E-invoicing (Peppol BIS Billing 3.0)",
    'version': '1.0.1',
    'category': 'Accounting/Localizations/EDI',
    'summary': "Slovak rules for the mandatory e-invoice (EN 16931 / Peppol BIS Billing 3.0)",
    'description': """
Slovak specifics on top of the Peppol BIS Billing 3.0 e-invoice of Odoo, for the
mandatory domestic e-invoicing that starts on 1 January 2027 (Act No. 385/2025
amending the VAT Act No. 222/2004).

The module is documented in doc/documentation_en.md (English) and
doc/documentation_sk.md (Slovak). The legal sources of the rules are listed in
docs/legislation_en.md and docs/legislation_sk.md of the repository.
    """,
    'author': "Patrik Rendek",
    'countries': ['sk'],
    'depends': [
        'account_edi_ubl_cii',
        'l10n_sk',
    ],
    'license': 'LGPL-3',
}
