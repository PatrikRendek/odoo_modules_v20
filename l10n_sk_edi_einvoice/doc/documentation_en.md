# Slovakia - E-invoicing (`l10n_sk_edi_einvoice`)

Documentation of the module for Odoo 20. Slovak version: [documentation_sk.md](documentation_sk.md).
The legal and technical sources of the rules are in
[`docs/legislation_en.md`](../../docs/legislation_en.md).

## 1. Purpose

From 1 January 2027 VAT payers have to issue their invoices for domestic supplies to businesses
and legal persons as structured e-invoices complying with EN 16931, and send them through a
certified delivery service of the Peppol network.

Odoo 20 builds and receives invoices in the Peppol BIS Billing 3.0 format. The module adds the
Slovak requirements the core does not cover and duplicates nothing of the core. The delivery
itself and the reporting of the data to the Financial Directorate are done by the delivery
service.

## 2. What the core does and what the module adds

| Area | Odoo 20 core | Module |
| --- | --- | --- |
| Format | Builds and imports Peppol BIS Billing 3.0, but does not suggest it for Slovak partners. | Suggests it for the Slovak customers of a Slovak company, consumers excepted. |
| Peppol identifier | Knows scheme 0245 (DIC) and deduces the DIC from the VAT number. | Validates the DIC (10 digits) and checks the 0245:DIC identifier of both parties before sending. |
| VAT number in the XML (BT-31, BT-48) | Writes the DIC without the SK prefix for a Slovak partner. | Writes the VAT number with the SK prefix; an entity without a VAT number gets no VAT identifier. |
| Company number in the XML (BT-30, BT-47) | Writes the DIC with scheme 0245. | Writes the company number (ICO) with scheme 0158 when the contact has one. |
| Date of supply (BT-7) | Neither exported nor imported. | Exported when it differs from the issue date; imported into the taxable supply date. |
| VAT category | Marks a domestic 0 % tax as exempt with an English text. | Sets the categories of the taxes of the Slovak chart and adds the legal wording in Slovak. |
| Credit note reference (BT-25) | Not filled for a credit note that is sent before being matched. | Filled from the invoice the credit note was created from, or from the invoice it is reconciled with. |
| Checks before sending | Generic EN 16931 and Peppol rules. | Slovak mandatory data, with messages telling the user what to fix. |
| Exchange rate | Looked up at the invoice date. | Looked up at the date of the taxable supply. |
| Issue date | Not compared with the sending day. | The Send wizard warns about a difference. |
| Import of a supplier | Creates the contact even without a VAT number; a malformed identifier of the file stops the import. | Stores the company number on the contact and drops a malformed identifier so that the import goes through. |
| Sending method | Peppol is only preselected for a set of countries, Slovakia is not one of them. | Peppol is preselected for Slovak customers when the company is connected to the network. |

## 3. Installation

1. Dependencies: `l10n_sk` and `account_edi_ubl_cii` (part of Odoo). Sending through Peppol
   also needs the `account_peppol` module; the module works without it and then only builds and
   checks the XML.
2. Add the repository folder to the `addons_path` and install the module.
3. On installation the taxes of the Slovak chart of accounts get their e-invoicing VAT category.
   Taxes that already have a category are left untouched.

## 4. Configuration

### 4.1 Own company

The contact of the company needs:

- name, street, city, postal code and the country Slovakia,
- the VAT number as `SK` followed by 10 digits,
- the tax identification number (DIC, 10 digits) among the additional identifiers; it is deduced
  from the VAT number when there is one,
- the company number (ICO) among the additional identifiers,
- a trusted bank account if it has to appear on the invoice. An invoice without a recipient
  bank (paid in cash or by card, for instance) is sent without payment instructions.

### 4.2 Customers

- A Slovak customer needs a DIC (or a VAT number the DIC is deduced from), a full address and
  the company number when one was assigned.
- The e-invoice format of a Slovak customer is set to "EU Standard (Peppol Bis 3.0)"
  automatically when the contact is a company or has a company number, a DIC or a VAT number.
  A contact without any of them is treated as a consumer.
- The default can be changed on the contact (Accounting tab). Do so for an individual who
  notifies that they are a taxable person.

### 4.3 Routing identifier

Slovak entities are addressed in the Peppol network as `0245:DIC`. Odoo picks this identifier
by itself when the contact has a DIC.

## 5. Taxes and VAT categories

| Tax of the chart | Use | Category | Reason code | Reason text |
| --- | --- | --- | --- | --- |
| 0% RC (`vy_rc`) | domestic reverse charge | AE | VATEX-EU-AE | Prenesenie daňovej povinnosti |
| 0% EU S (`vy_eu_s`) | services to another member state | AE | VATEX-EU-AE | Prenesenie daňovej povinnosti |
| 0% EU T (`vy_eu_t`) | triangular trade, invoice of the first customer to the second customer | AE | VATEX-EU-AE | Prenesenie daňovej povinnosti |
| 0% EU M (`vy_eu_m`) | supply of goods to another member state | K | VATEX-EU-IC | Dodanie je oslobodené od dane podľa § 43 zákona č. 222/2004 Z. z. |
| 0% EXP (`vy_mimo_eu`) | export outside the EU | G | VATEX-EU-G | Dodanie je oslobodené od dane podľa § 47 zákona č. 222/2004 Z. z. |

- The 23 %, 19 % and 5 % taxes get category S automatically.
- The domestic 0 % taxes get category E and the text "Dodanie je oslobodené od dane". The reason
  code of the specific provision can be selected on the tax (Accounting → Configuration → Taxes);
  the codes are listed in `docs/legislation_en.md`, chapter 4.
- A reason text set on the tax itself wins over the text added by the module.

## 6. Issuing and sending an invoice

1. Create and confirm the invoice. When the date of supply differs from the issue date, fill in
   the Taxable Supply Date. For an invoice for a received payment, enter the day the payment was
   received.
2. Click **Send**. For a Slovak customer the Peppol BIS 3.0 format is preselected and the XML
   file is listed among the attachments next to the PDF. When the company is connected to the
   Peppol network, the Peppol sending method is preselected as well.
3. On sending, the XML is built and checked. When something is missing, the wizard lists the
   errors and the invoice is not sent.

### 6.1 Content of the XML

| XML element | Content |
| --- | --- |
| `cbc:TaxPointDate` (BT-7) | taxable supply date, when it differs from the issue date |
| `cac:PartyTaxScheme/cbc:CompanyID` (BT-31, BT-48) | VAT number with the SK prefix; absent when the entity has no VAT number |
| `cac:PartyLegalEntity/cbc:CompanyID` (BT-30, BT-47) | company number with `schemeID="0158"`; without it the DIC with `schemeID="0245"` stays |
| `cac:TaxCategory` (BT-118, BT-120, BT-121) | AE + VATEX-EU-AE + "Prenesenie daňovej povinnosti"; E + "Dodanie je oslobodené od dane" |
| `cac:BillingReference` (BT-25) | number and date of the original invoice on a credit note |

The identifiers (VAT number, company number) are adjusted for every Slovak party of a document.
The other rules apply to the documents whose supplier is established in Slovakia.

### 6.2 Checks before sending

| Message | Shown when |
| --- | --- |
| The address of the partner is incomplete | the supplier or the Slovak customer lacks the street, the city or the postal code |
| The partner must be identified by its DIC | the supplier or the Slovak customer has no 0245 identifier of 10 digits |
| The VAT number is not valid | the VAT number of a Slovak entity is not SK followed by 10 digits |
| The supplier has no VAT number | the invoice has another VAT category than O and the supplier has no VAT number |
| Reverse charge, the customer has no VAT number | category AE and a Slovak customer without a VAT number |
| The credit note does not refer to the invoice | credit note without a link to the original invoice |

The generic checks of the core apply on top of these.

Incomplete contacts are reported before sending as well: when the own company or a Slovak
customer lacks the address, the DIC or has a malformed VAT number, the Send wizard shows a
warning with a button that opens the contacts to complete.

### 6.3 Exchange rate of foreign currency invoices

In a company whose fiscal country is Slovakia, the invoice amount is converted with the rate
looked up at the **date of the taxable supply**. Odoo 20 takes the last rate published before
the given date, which gives the rate of the day preceding the day the tax liability arises, as
required by Section 26(1) of the VAT Act and Section 24(2) of the Accounting Act.

- It applies to customer invoices and vendor bills.
- A credit note created from an invoice keeps the rate date of that invoice.
- The rates have to be stored in Odoo under the date the ECB or the NBS published them.
- Posted documents are not recomputed when the module is installed.

### 6.4 Issue date and sending day

An e-invoice is issued once it is handed over to the delivery service, and its issue date should
be the sending day. When an invoice whose date is not today is sent to a Slovak customer for the
first time, the Send wizard shows a warning. It does not block the sending and does not change
the date of the posted invoice; the invoice can be reset to draft and its date changed.

### 6.5 Sending through Peppol

The Peppol network is provided by the `account_peppol` module (Accounting → Configuration →
Settings → Electronic Invoicing). Odoo is a Peppol access point and is on the list of certified
delivery service providers of the Financial Administration.

- The registration wizard suggests the `0245:DIC` identifier to a Slovak company. The
  registration is completed by the user, who enters a contact e-mail and a phone number; the
  provider verifies the company.
- Odoo looks the customer up in the network by `0245:DIC` and checks that it receives Peppol BIS
  Billing 3.0. The lookup of Slovak participants was verified on the production network; they
  are registered in the Slovak SMP.
- Send the invoice from the Send wizard with the Peppol method ticked. The delivery status is
  shown in the Peppol status field of the invoice.
- The checks of the module also apply to Peppol: an invoice with an error is not sent to the
  network.
- The delivery service reports the data to the Financial Directorate when it takes over the
  invoice.
- The demo mode of `account_peppol` allows trying the flow without sending anything. The
  production server of Odoo requires a verification of the company on registration.

### 6.6 Credit note

Create the credit note with the Credit Note button of the original invoice. The XML of the
credit note carries the number and the date of the original invoice. Keep the taxable supply
date of the credit note equal to its own date: the act only requires the number of the original
invoice and the data that change.

## 7. Receiving an e-invoice

The XML is imported through the usual ways of Odoo: upload in the list of vendor bills, e-mail
to the journal alias, or Peppol. The module then:

- writes `cbc:TaxPointDate` into the Taxable Supply Date; when it is missing or malformed, the
  issue date is used,
- stores the company number of `schemeID="0158"` on a newly created supplier,
- drops a malformed supplier identifier of the file (a DIC that is not made of 10 digits, for
  instance), so that the import goes through and the supplier is created without it.

The core finds an existing supplier by its VAT number or DIC, and creates a new one even
without a VAT number.

The imported document is a draft; check the taxes and the accounts before posting.

## 8. Scope

The module does not cover: delivery and reporting of the data, debit notes, document type 384, company
register data (BT-33), public procurement reference (BT-12), specific support of advance payment
invoices, self-billed invoices, VAT groups and tax representatives, tracking of the deadlines,
and the rules valid from 1 July 2030. The DIC check verifies the number of digits.

## 9. Technical description

| File | Content |
| --- | --- |
| `models/res_partner.py` | DIC validation, default invoice format, Slovakia among the countries of the BIS 3 format |
| `models/account_edi_xml_ubl_bis3.py` | extension of `account.edi.xml.ubl_bis3`: XML nodes, checks before sending, import |
| `models/account_move.py` | exchange rate date taken from the taxable supply date |
| `models/account_move_send.py` | Peppol preselected as the sending method, contact data and invoice date warnings in the Send wizard |
| `models/account_chart_template.py` | VAT categories of the taxes of the Slovak chart, applied to new charts and, at installation, to the existing ones |
| `i18n/` | `sk.po` and `cs.po` translations |
| `tests/` | export, import, contact, accounting and demo mode Peppol tests; sample XML files in `tests/test_files/` |

The module adds no new format, field, model, access right or view.

### Tests

```
odoo-bin -d <db> -i l10n_sk_edi_einvoice --test-enable --test-tags /l10n_sk_edi_einvoice --stop-after-init
```

| Sample file | Scenario |
| --- | --- |
| `sk_invoice_domestic.xml` | domestic invoice at 23 %, date of supply different from the issue date |
| `sk_invoice_reverse_charge.xml` | domestic reverse charge |
| `sk_invoice_non_vat_supplier.xml` | supplier that is not registered for VAT |

The sample files and the invoices generated by the module passed the Peppol Testbed validator
(BIS Billing 3.0.21). The identification numbers of the samples and of the tests are made up.
