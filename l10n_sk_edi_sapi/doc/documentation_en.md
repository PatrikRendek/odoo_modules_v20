# Slovakia - E-invoicing delivery service (`l10n_sk_edi_sapi`)

Documentation of the module for Odoo 20. Slovak version: [documentation_sk.md](documentation_sk.md).

## 1. Purpose

From 1 January 2027 a Slovak e-invoice has to be sent through a certified delivery service
("digital postman"), which delivers it over the Peppol network and reports its data to the
Financial Directorate.

Odoo itself is such a service (module `account_peppol`). This module is for companies that
have a contract with another Slovak delivery service: it hands the e-invoice over through the
**SAPI-SK 1.0** interface, follows the delivery and downloads the received e-invoices.

The XML and its Slovak checks come from `l10n_sk_edi_einvoice`; this module only transports
the file.

## 2. What the module does

| Area | Behaviour |
| --- | --- |
| Sending | New sending method "by Slovak delivery service" in the Send wizard. The Peppol BIS Billing 3.0 file is posted to the service. |
| Status | The invoice shows the status at the service: Handed over, Delivered, Recipient not on the network, Rejected by the recipient, Error. |
| Receiving | A scheduled action downloads the received e-invoices, creates draft vendor bills from them and acknowledges them at the service. |
| Protection | An invoice handed over to the service cannot be reset to draft, cancelled or deleted, is not sent twice and goes through one network only. |

## 3. Before you start

1. Sign a contract with a certified delivery service that offers the SAPI-SK interface.
2. Select that service on the portal of the Financial Administration. A company has exactly
   one service for receiving and may have several for sending.
3. Create the API credentials (client ID and client secret) in the portal of the service.

## 4. Installation and configuration

1. Install the module. It depends on `l10n_sk_edi_einvoice`.
2. Open Accounting → Configuration → Settings → **Slovak Delivery Service** (shown for a company
   whose fiscal country is Slovakia) and fill in:

| Field | Content |
| --- | --- |
| Delivery Service | Verteco, eFakturuj, or Other SAPI-SK service |
| URL | address of the interface, starting with `https://` and ending with `/sapi` |
| Client ID, Client Secret | credentials created in the portal of the service |
| Bills Journal | purchase journal of the downloaded bills; empty = first purchase journal |

3. Save the settings and click **Test Connection**. The module asks the service for an access token and reports the
   result.

The company needs its DIC among the additional identifiers of its contact: it is sent to the
service as `0245:DIC` with every call. The credentials are readable by administrators only.

## 5. Sending an invoice

1. Confirm the invoice and click **Send**.
2. For a Slovak customer the method "by Slovak delivery service" is preselected, unless the
   Peppol connection of Odoo is used for the invoice. The method can be ticked for any customer
   that has a Peppol identifier.
3. On sending, the XML is built, checked and posted to the service.

| Answer of the service | Result on the invoice |
| --- | --- |
| Accepted | status Handed over, the identifier of the document is stored, warnings of the service are logged in the chatter |
| Accepted, recipient is not on the network | status Recipient not on the network |
| Rejected (validation, authorisation) | status Error with the message of the service; the invoice can be corrected and sent again |
| No answer or an unclear one (network failure, error of a gateway) | status Error; the next attempt repeats the same request, so the invoice is not sent twice |

The preferred method of a customer can be set on the contact (Accounting tab, Invoice sending).

- An invoice goes through one network only. When both the delivery service and the Peppol
  connection of Odoo are ticked, the invoice goes through the delivery service and the Send
  wizard says so.
- The invoices of a batch are handed over and stored one by one: a refused invoice does not
  stop the others. When the service cannot be reached, the rest of the batch is not tried.
- The file handed over is attached to the record of the hand-over in the history of the
  invoice.

## 6. Delivery status

A scheduled action ("SAPI-SK: update delivery statuses") asks the service for the status of the
invoices in the Handed over status, 100 invoices per run, starting with those asked for the
longest time ago. It runs five minutes after a hand-over and then every four hours.

| Status at Verteco | Status at eFakturuj | Status of the invoice |
| --- | --- | --- |
| pending, submitted | ACCEPTED, PROCESSING | Handed over |
| delivered | SENT | Delivered |
| undeliverable | | Recipient not on the network |
| rejected | | Rejected by the recipient |
| failed | FAILED | Error |

The status interface is not part of the common core of SAPI-SK, each service has its own. With
"Other SAPI-SK service" the invoice stays in the Handed over status; the delivery is then
visible in the portal of the service.

A rejected invoice or an invoice in error can be reset to draft and sent again. An invoice that
was handed over, delivered or reported as undeliverable can only be corrected by a credit note.

## 7. Receiving e-invoices

The scheduled action "SAPI-SK: retrieve received e-invoices" runs every hour:

1. lists the documents of the company that are not acknowledged yet,
2. downloads each of them and creates a draft vendor bill through the standard import of Odoo
   (supplier, lines, taxes, taxable supply date),
3. acknowledges the document at the service, so that it is not offered again.

A document the service refuses to hand out is skipped and the others are still downloaded.
A document that was already imported is only acknowledged. The original XML is stored on the
bill. A document the import cannot read is kept as an empty draft bill with the file attached.

## 8. Interface calls

| Call | Use |
| --- | --- |
| `POST /auth/token` | access token (OAuth2 client credentials, JSON body) |
| `POST /document/send` | hand-over of the e-invoice, with the `Idempotency-Key` header |
| `GET /document/receive?status=RECEIVED` | list of the received documents, paged with `pageToken` |
| `GET /document/receive/{id}` | content of a received document |
| `POST /document/receive/{id}/acknowledge` | acknowledgement |
| `GET /document/sent/{id}` | delivery status (Verteco) |
| `GET /document/status/{id}` | delivery status (eFakturuj) |

Every document call carries the `Authorization: Bearer` and `X-Peppol-Participant-Id` headers.

## 9. Scope

The module does not register the company at the service or at the Financial Administration,
does not report data to the Financial Directorate (the service does), does not process
webhooks, does not look the recipient up on the network before sending and does not download
the delivery receipt. The delivery status is followed for Verteco and eFakturuj only.

## 10. Technical description

| File | Content |
| --- | --- |
| `tools/sapi_client.py` | HTTP client of the interface: token, calls, error messages |
| `models/res_company.py` | connection settings of the company |
| `models/res_config_settings.py` | settings and the connection test |
| `models/res_partner.py` | sending method "by Slovak delivery service" |
| `models/account_move_send.py` | hand-over of the invoice in the Send flow |
| `models/account_move.py` | status fields, status update, download of the received documents |
| `data/ir_cron_data.xml` | the two scheduled actions |
| `data/neutralize.sql` | removes the connection from a neutralized copy of the database |
| `tests/` | tests with a simulated service |

### Tests

```
odoo-bin -d <db> -i l10n_sk_edi_sapi --test-enable --test-tags /l10n_sk_edi_sapi --stop-after-init
```

The tests replace the service by canned answers and make no external call.

The module was also run against the test environments of Verteco and eFakturuj, both connected to
the Peppol test network. An invoice and a credit note sent from Odoo went from Handed over to
Delivered, and the documents received by the customer were downloaded as a draft vendor bill and
a draft vendor credit note with their supplier, lines and taxes, then acknowledged.
