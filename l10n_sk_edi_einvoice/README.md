# Slovakia - E-invoicing (Peppol BIS Billing 3.0)

Slovak version: [README_sk.md](README_sk.md)

Slovak specifics on top of the Peppol BIS Billing 3.0 e-invoice of Odoo 20, for the mandatory
domestic e-invoicing that starts on 1 January 2027 (Act No. 385/2025 Coll. amending the VAT Act
No. 222/2004 Coll.).

- Version: 1.0.0
- License: LGPL-3
- Depends on: `l10n_sk`, `account_edi_ubl_cii`

The delivery of the invoices and the reporting of the data to the tax authority are done by the
certified delivery service (Peppol access point), not by this module.

## Features

- Peppol BIS Billing 3.0 is the default e-invoice format for the Slovak business customers of a
  Slovak company. Consumers keep receiving the invoice as before.
- The tax identification number (DIC) is validated: it is the Peppol identifier of every Slovak
  entity (scheme 0245).
- Slovak content of the XML: VAT number (IC DPH) with the SK prefix as VAT identifier, company
  number (ICO, scheme 0158) as legal registration identifier, date of the taxable supply as tax
  point date, reference to the original invoice on credit notes.
- VAT categories of the Slovak chart of accounts: reverse charge (AE, including services to
  other member states and triangular trade), intra-community supply (K), export (G), with the
  wording required by the VAT Act.
- Checks before sending, with messages that tell the user what to fix: address, DIC, VAT number,
  reverse charge, credit note reference.
- Exchange rate of foreign currency invoices of Slovak companies taken at the date of the
  taxable supply, which gives the rate published the day before the tax point.
- Warning in the Send wizard when a Slovak e-invoice is sent on another day than its invoice
  date.
- Peppol preselected as the sending method for Slovak customers when the `account_peppol`
  module is installed and the company is connected to the network.
- Import of received e-invoices: date of the taxable supply, company number of the supplier, and
  no failure on a malformed supplier identifier.
- Slovak and Czech translations.

## Documentation

- [`doc/documentation_en.md`](doc/documentation_en.md): documentation of the module.
- [`../docs/legislation_en.md`](../docs/legislation_en.md): legal and technical sources of the
  rules.

The module is not legal or tax advice.

## Tests

```
odoo-bin -d <db> -i l10n_sk_edi_einvoice --test-enable --test-tags /l10n_sk_edi_einvoice --stop-after-init
```

The generated invoices and the sample files were validated with the Peppol Testbed validator
(BIS Billing 3.0.21).

## Changelog

### 1.0.0

- Initial version for Odoo 20.
