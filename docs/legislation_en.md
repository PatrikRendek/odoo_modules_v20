# Slovak e-invoice from 1 January 2027: legislation and technical rules

Background for the `l10n_sk_edi_einvoice` module (Odoo 20). Slovak version: [legislation_sk.md](legislation_sk.md).

All sources were checked on **17 November 2026**. The acts were read in the legally binding PDF
texts published on Slov-Lex. This document is not legal or tax advice.

## 1. Sources

| Code | Source | Link |
| --- | --- | --- |
| Z1 | Act No. 385/2025 Coll. amending the VAT Act No. 222/2004 Coll. (promulgated on 19 December 2025); binding PDF of the versions valid from 1 January 2026, 1 January 2027 and 1 July 2030 | https://static.slov-lex.sk/pdf/SK/ZZ/2025/385/ZZ_2025_385_20270101.pdf |
| Z2 | VAT Act No. 222/2004 Coll., binding PDF of the version valid from 1 January 2027 to 30 June 2030 | https://static.slov-lex.sk/pdf/SK/ZZ/2004/222/ZZ_2004_222_20270101.pdf |
| Z3 | VAT Act No. 222/2004 Coll., binding PDF of the version valid from 1 July 2030 | https://static.slov-lex.sk/pdf/SK/ZZ/2004/222/ZZ_2004_222_20300701.pdf |
| Z4 | Accounting Act No. 431/2002 Coll., binding PDF of the version valid from 1 January 2026 | https://static.slov-lex.sk/pdf/SK/ZZ/2002/431/ZZ_2002_431_20260101.pdf |
| F1 | Financial Directorate of the Slovak Republic, 9/DPH/2025/IM "Frequently asked questions on the e-invoice", November 2026 version | https://www.financnasprava.sk/_img/pfsedit/Dokumenty_PFS/Zverejnovanie_dok/Aktualne/DPH/2026/2026.11.16_009_DPH_2026_IM_FAQ_eFak.pdf |
| F2 | Financial Administration, "Transposition of the Peppol BIS standard to the Slovak legislation", version 1.13 of 29 October 2026 | https://www.financnasprava.sk/_img/pfsedit/Dokumenty_PFS/Podnikatelia/Dan_z_pridanej_hodnoty/efaktura/2026/2026.10.29_Peppol_Bis3_v1_13.xlsx |
| F3 | Financial Administration, e-invoice page and list of certified delivery service providers (17 November 2026) | https://www.financnasprava.sk/sk/podnikatelia/dane/dan-z-pridanej-hodnoty/e-faktura |
| P1 | OpenPeppol, Peppol BIS Billing 3.0, version 3.0.21 (EAS, ICD, UNCL5305 and VATEX code lists, rules, schematron) | https://docs.peppol.eu/poacc/billing/3.0/ |
| P2 | OpenPeppol, Peppol Testbed validator | https://www.testbed.peppol.org/validation |
| P3 | OpenPeppol, Slovak Republic Tax Data Document 1.0.0 (specification, schema, rules, examples) | https://docs.peppol.eu/tdd/sk/tdd-sk/ |
| P4 | OpenPeppol, Slovakia eInvoicing and Tax Reporting Billing Test Suite, Environment Description 1.1 | https://www.testbed.peppol.org/assets/documentation/SK-Billing-eInvoicing-and-Tax-Reporting-Environment-Description-v1.1.pdf |
| F4 | Financial Administration, accreditation scheme and accreditation guide for delivery service providers | https://www.financnasprava.sk/_img/pfsedit/Dokumenty_PFS/Podnikatelia/Dan_z_pridanej_hodnoty/efaktura/2026/2026.04.14_navod_akreditacie.pdf |

## 2. Scope and deadlines

| Rule | Source |
| --- | --- |
| From 1 January 2027 a VAT payer (Sections 4, 4b, 4c) issues an e-invoice for a supply of goods or services with the place of supply in Slovakia, and for a payment received before it, when the recipient is a taxable person with a seat, place of business, fixed establishment or residence in Slovakia, or a non-taxable legal person with a seat in Slovakia. The consent of the recipient is not required. | Z2, Section 85o(2) and (3) |
| The obligation does not cover supplies exempt under Sections 28 to 43 and 47, nor simplified invoices (document up to EUR 100, cash register receipt up to EUR 400). | Z2, Sections 85o(2) and 74(3) |
| Consumers (B2C) are not concerned. | F1; follows from Section 85o(3) |
| Whoever has to issue an e-invoice must be able to send and receive it through a delivery service; the recipient of such a supply must be able to receive it. | Z2, Section 71(5) |
| A taxable person is any person who independently carries out an economic activity, including the use of property to obtain income. | Z2, Section 3(1) and (2) |
| When the customer notifies later that an e-invoice should have been issued, the deadline is met if the supplier issues it within 15 days of the notification. The Financial Administration recommends cancelling the original invoice and issuing a new e-invoice with a note about the notification. | Z2, Section 85o(8); F1 |
| When the customer has no delivery service, the supplier has met the obligation by sending the invoice through the delivery service. | F1; Z2, Section 71(5) |
| The e-invoice is issued within 15 days of the supply, of the receipt of the payment, or of the end of the month in which the event leading to a correction of the tax base occurred. | Z2, Section 85o(6) |
| The e-invoice is only issued once it is handed over to the delivery service; the issue date it states should be the day it was sent. | F1; Z2, Section 85o(4) and (6) |
| A summary e-invoice covers at most one calendar month and is issued within 15 days of its end. | Z2, Section 85o(7) |
| The supplier reports the invoice data to the Financial Directorate when issuing the invoice; handing the invoice over to the delivery service fulfils the obligation. The five-day deadline concerns self-billed invoices and the recipient of the invoice. | Z2, Section 85o(9) to (11) |
| Failing to report, reporting late or reporting wrong data is fined up to EUR 10,000, repeatedly up to EUR 100,000; no fine applies when an obvious mistake is corrected or the provider had a proven outage. | Z2, Section 85o(12) to (14) |
| The e-invoice is kept for ten years. | Z2, Section 85o(15) |
| The act contains no delegation for an implementing decree on the invoice format; the format is set by the European standard. | Z2, Section 85o(4) |

## 3. Format and delivery

| Rule | Source |
| --- | --- |
| An e-invoice is a document with the content of Section 74(1) that is issued, sent and received in a structured format allowing automated processing, in a data structure complying with the European standard on electronic invoicing (EN 16931) and the list of its syntaxes. | Z2, Section 85o(4) |
| In practice it is an XML file in the UBL 2.1 or CII D16B syntax; in the Peppol network the Peppol BIS Billing 3.0 profile. A PDF is only a readable rendering. | F1 |
| The delivery service is provided by a certified provider entered in the register of the Financial Directorate; it checks the formal requirements, identifies the sender and the addressee, keeps the content intact, proves the time of sending and delivery and reports the data. | Z2, Section 76a |
| Slovak entities are identified in the Peppol network by scheme **0245 and the tax identification number (DIC)** of 10 digits, not by scheme 9950 (VAT number). The delivery service provider registers them in the Slovak SMP. | F1; F2 (BT-34, BT-49); P1 (EAS code list) |
| An entity without a DIC has to obtain one, otherwise it cannot be identified in the network. | F1 |
| Peppol BIS Billing 3.0 has no Slovak national rules; the stricter Slovak requirements are the responsibility of the sender. | P1; F1 |
| A contracting authority must be able to receive e-invoices through a delivery service; an invoice resulting from public procurement also states the number of the procurement notice (field BT-12). | Z1, Article VII (Section 2 of Act No. 215/2019 Coll.); F2 |

## 4. Invoice content

BT and BG are the business terms of EN 16931.

| Rule | Source |
| --- | --- |
| The invoice number (BT-1) is based on one or more series and identifies the invoice uniquely; the issue date (BT-2) is mandatory. | Z2, Section 74(1)(c) and (e) |
| The date of the supply or of the received payment is stated when it can be determined and differs from the issue date; in the e-invoice it goes to BT-7. BT-8 is not used. For a payment received in advance the tax liability arises on the day the payment is received. | Z2, Sections 74(1)(d) and 19(4); F2 |
| The name and address of the supplier and of the customer are mandatory; street (BT-35, BT-50), city (BT-37, BT-52) and postal code (BT-38, BT-53) are required. | Z2, Section 74(1)(a) and (b); F2 |
| The VAT identifier (BT-31, BT-48) is the VAT number with the country prefix, when one was assigned. | Z2, Section 74(1)(a) and (b); P1 (BR-CO-09) |
| The legal registration identifier (BT-30, BT-47) is the company number (ICO), when one was assigned, with a scheme of the ISO 6523 list; scheme 0158 for the Slovak ICO. | F2; P1 (ICD code list) |
| The electronic address of the supplier (BT-34) and of the customer (BT-49) is mandatory, with scheme 0245. | F2 |
| The VAT category follows the legal regime of the supply: S (standard and reduced rates), E (exempt, Sections 28 to 42), K (Section 43), G (Section 47), AE (reverse charge), O (outside the scope of VAT), Z (genuine zero rate). | F1, part III |
| When the recipient is liable for the tax, the invoice states the wording "prenesenie daňovej povinnosti" (reverse charge): category AE, code VATEX-EU-AE. | Z2, Section 74(1)(k); F1; P1 (BR-AE-10) |
| The domestic reverse charge only applies when both the supplier and the recipient are VAT payers with an assigned VAT number. | Z2, Section 69(12) |
| For a service with the place of supply in another member state where the recipient is liable for the tax, the invoice states "prenesenie daňovej povinnosti"; the rate and the tax amount may be omitted. | Z2, Sections 72(1)(b), 74(1)(k) and 74(2) |
| In triangular trade the first customer issues an invoice to the second customer without tax and with the wording "prenesenie daňovej povinnosti". | Z2, Section 45(3) |
| For an exemption the invoice refers to the provision of the act or of Directive 2006/112/EC, or states the wording "dodanie je oslobodené od dane" (the supply is exempt). A reason code or a text is enough; the Financial Administration recommends the code, with the text as a complement. | Z2, Section 74(1)(h); P1 (BR-E-10); F1 |
| Category O cannot be mixed with other categories on one invoice and is used without the VAT numbers of the supplier and of the customer. It is also the category of a non-VAT payer who invoices electronically on a voluntary basis. | P1 (BR-O-02, BR-O-11); F1 |
| The tax amount is stated in euros, also on a foreign currency invoice (BT-6, BT-111). The conversion uses the ECB or NBS reference rate of the day preceding the day the tax liability arises; a correction of the tax base uses the rate of the original invoice. The same rule applies in accounting. | Z2, Sections 74(1)(i) and 26(1); Z4, Section 24(2) |
| A document amending an e-invoice is an e-invoice as well. It must contain the number of the original invoice (BT-25) and the data that change; when the original invoice went through the delivery service, the amending document must too. | Z2, Sections 85o(5), 71(2) and 74(3)(c) |
| A correction of the tax base is declared in the tax period in which the correcting document was issued. | Z2, Section 25(3) |
| Payment instructions (BG-16) are optional; the account number of the supplier (BT-84) is only required for a credit transfer. | F2; P1 (BR-61) |
| A pro-forma invoice used as a payment request is not an invoice and is not sent through the delivery service; the invoice for a received payment must be an e-invoice. | F1; Z2, Section 85o(2) |

### Exemption reason codes (VATEX) according to the Financial Administration

| Provision of the VAT Act | Supply | Category | VATEX code |
| --- | --- | --- | --- |
| Section 22 | amounts in a suspense account | E | VATEX-EU-79-C |
| Section 28 | postal services | E | VATEX-EU-132-1A |
| Section 29 | health care | E | VATEX-EU-132-1B, 1C, 1D, 1E or 1P depending on the case |
| Section 30 | social assistance services | E | VATEX-EU-132-1G or 1H |
| Section 31 | education services | E | VATEX-EU-132-1I or 1J |
| Section 32 | services supplied to members | E | VATEX-EU-132-1L or 1F |
| Section 33 | services related to sport | E | VATEX-EU-132-1M |
| Section 34 | cultural services | E | VATEX-EU-132-1N |
| Section 35 | fund-raising | E | VATEX-EU-132-1O |
| Section 36 | public television and radio services | E | VATEX-EU-132-1Q |
| Sections 37 to 41 | insurance and financial services, immovable property, postal stamps, lotteries | E | VATEX-EU-135-1 |
| Section 42 | goods for which the tax was not deducted | E | no code |
| Section 43 | supply of goods to another member state | K | VATEX-EU-IC |
| Section 47 | export of goods | G | VATEX-EU-G |
| Section 69 | reverse charge | AE | VATEX-EU-AE |
| – | supply outside the scope of VAT | O | VATEX-EU-O |

Source: F1, part III. Supplies exempt under Sections 28 to 43 and 47 are not covered by the
mandatory e-invoicing; the table applies when they are invoiced electronically on a voluntary
basis.

## 5. From 1 July 2030

The rules change on 1 July 2030; the module does not cover them and has to be adapted before
that date.

| Rule | Source |
| --- | --- |
| The e-invoice becomes the default form of an invoice, cross-border supplies included; the exceptions are the simplified invoice and the "invoice in another form". | Z3, Sections 71(1), (4) and (6), 72(9) to (11) |
| The deadline for issuing an invoice is shortened to ten days. | Z3, Section 73 |
| New mandatory content: the wording "trojstranný obchod" (triangular trade), the number of the original invoice on an amending document and the account numbers of the supplier. | Z3, Section 74(1)(k), (p) and (q) |
| The control statement and the recapitulative statement are abolished and replaced by the reporting of the data of every invoice for cross-border (Section 80) and domestic (Section 80a) supplies. | Z3, Sections 80, 80a and 85o(17) |
| An invoice for a supply made until 30 June 2030 is corrected under the rules valid until that day. | Z3, Section 85o(24) |

## 6. How the module covers the rules

| Area | Solution |
| --- | --- |
| Format | The core of Odoo builds and imports Peppol BIS Billing 3.0. The module makes it the default for the Slovak customers of a Slovak company, consumers excepted. |
| Peppol identifier | Scheme 0245 and the deduction of the DIC from the VAT number are in the core. The module validates the DIC and checks the 0245:DIC identifier of both parties before sending. |
| VAT number and company number | BT-31 and BT-48 carry the VAT number with the SK prefix, BT-30 and BT-47 the ICO with scheme 0158. |
| Date of supply | Exported to BT-7 and imported from BT-7. |
| VAT categories | The taxes of the Slovak chart for the reverse charge, services to the EU and triangular trade get category AE, goods to the EU K, export G; the legal wording is added in Slovak. |
| Amending document | A credit note refers to the original invoice; without the reference it is not sent. |
| Checks before sending | Address, DIC, VAT number, reverse charge without the VAT number of the customer, credit note reference. |
| Exchange rate | The rate is looked up at the date of the taxable supply; the core of Odoo 20 takes the last rate published before that date. A credit note keeps the rate of the original invoice. |
| Issue date | The Send wizard warns when the invoice is sent on another day than its date. |
| Sending method | Peppol is preselected for a Slovak customer when the company is connected to the network through the `account_peppol` module. |
| Import | Date of supply and company number; a malformed supplier identifier does not stop the import. |

Outside the scope of the module: delivery and reporting of the data (done by the delivery
service), document type 384, company register data (BT-33), public procurement reference
(BT-12), specific support of advance payment invoices, self-billed invoices, VAT groups and tax
representatives, tracking of the deadlines, and the rules valid from 1 July 2030.

## 7. Verification

| What | Result |
| --- | --- |
| Automated tests of the module on a clean Odoo 20 database (sources of 17 November 2026), with and without the `account_peppol` module | 51 tests, no failure; without the `account_peppol` module the 5 Peppol sending tests are skipped |
| Peppol Testbed validator (P2), specifications BIS Billing Invoice and Credit Note 3.0.21, 17 November 2026 | 13 samples passed the XSD, jurisdiction, EN 16931 and Peppol checks |
| User interface | Creating and confirming an invoice, Send wizard with the PDF and the XML, date warning, error messages and import of a received invoice |
| Lookup of Slovak participants on the production Peppol network through the access point of Odoo | Participants with scheme 0245 were found in the Slovak SMP (`sml.peppol-smp.sk`) and receive Peppol BIS Billing 3.0; an identifier with scheme 9950 was not found. The Peppol Directory listed 53,175 Slovak participants. |
| Sending and receiving through `account_peppol` in demo mode | Registration of the company under `0245:DIC`, sending of an invoice up to the delivered status, blocking of an invoice with an error and reception of a document all went through |
| Certification of the Odoo access point | Odoo SA is on the list of certified delivery service providers (PA SK ID EFSK000048, as of 17 November 2026). The entry requires a record of successful testing in the Peppol Testbed for Slovakia (F4), which covers sending and receiving an invoice and a credit note together with the reporting of the data to the tax authority (P4). |
| Data reporting (Tax Data Document) | Reports were built from the 13 samples following specification P3, the way the delivery service builds them. 12 passed validator P2 (schema, Slovak TDD rules, EN 16931, Peppol). The report of a supply of goods to another member state failed rule BR-IC-12, because the TDD 1.0.0 specification has no place for the deliver-to country; that supply is not covered by the obligation from 1 January 2027. |
| Registration through Odoo | The preliminary check of both Odoo servers accepted the `0245:DIC` identifier; the production server requires a verification of the company. |
| Public records of the Slovak SMP | In a sample of 931 Slovak participants none received invoices through the Odoo access point; the most frequent access points were Flowis, Softip, Verteco and ion-AP. |
| Odoo documentation | Slovakia is among the countries for which Odoo allows registration to the Peppol network; the documentation has no page specific to Slovakia |

Validated samples: domestic invoice, reverse charge, exempt supply, customer without a VAT
number, foreign currency, invoice without a bank account, services to the EU, goods to the EU,
triangular trade, credit note, and the three sample files of the module tests.
