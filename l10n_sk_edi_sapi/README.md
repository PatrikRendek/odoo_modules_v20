# Slovakia - E-invoicing delivery service (SAPI-SK)

Odoo 20 module that sends and receives Slovak e-invoices through a certified delivery service
("digital postman") over the SAPI-SK 1.0 interface.

- hands the Peppol BIS Billing 3.0 e-invoice over to the service from the Send wizard,
- follows the delivery status (Verteco, eFakturuj),
- downloads the received e-invoices as draft vendor bills.

Depends on `l10n_sk_edi_einvoice`. License: LGPL-3.

Documentation: [English](doc/documentation_en.md), [Slovak](doc/documentation_sk.md).
Slovak README: [README_sk.md](README_sk.md).
