import logging
from urllib.parse import quote

from odoo import api, fields, models
from odoo.exceptions import UserError

from ..tools.sapi_client import SapiError

_logger = logging.getLogger(__name__)

# Statuses that mean the delivery service took the invoice over (and reports it to the tax authority).
SAPI_SENT_STATES = ('processing', 'delivered', 'undeliverable')
# Status interface of the supported delivery services (it is not part of the common SAPI-SK core): the
# path of the call, the key holding the document in the answer (None when the answer is the document),
# the key of the explanation and the mapping of the statuses of the service to those of the invoice.
SAPI_PROVIDER_STATUS = {
    'verteco': {
        'path': '/document/sent/%s',
        'document_key': 'document',
        'detail_key': 'statusDetail',
        'states': {
            'pending': 'processing',
            'submitted': 'processing',
            'delivered': 'delivered',
            'undeliverable': 'undeliverable',
            'rejected': 'rejected',
            'failed': 'error',
        },
    },
    'efakturuj': {
        'path': '/document/status/%s',
        'document_key': None,
        'detail_key': 'errorMessage',
        'states': {
            'ACCEPTED': 'processing',
            'PROCESSING': 'processing',
            # The access point of the recipient accepted the transmission.
            'SENT': 'delivered',
            'FAILED': 'error',
        },
    },
}
SAPI_PAGE_SIZE = 50
# Upper bound of the pages read in one run, so that a service repeating its page token cannot loop forever.
SAPI_MAX_PAGES = 100
# Number of invoices whose delivery status is asked for in one run of the scheduled action: each of
# them is a call to the service, and the run has to end before the time limit of the worker.
SAPI_STATUS_BATCH_SIZE = 100


class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_sk_sapi_document_id = fields.Char(
        string="Delivery Service Document",
        help="Identifier of the document at the delivery service.",
        copy=False,
        readonly=True,
        index='btree_not_null',
    )
    l10n_sk_sapi_idempotency_key = fields.Char(string="Delivery Service Request Key", copy=False, readonly=True)
    l10n_sk_sapi_state = fields.Selection(
        selection=[
            ('processing', "Handed over"),
            ('delivered', "Delivered"),
            ('undeliverable', "Recipient not on the network"),
            ('rejected', "Rejected by the recipient"),
            ('error', "Error"),
        ],
        string="Delivery Service Status",
        copy=False,
        readonly=True,
        tracking=True,
    )
    l10n_sk_sapi_state_detail = fields.Char(string="Delivery Service Message", copy=False, readonly=True)
    l10n_sk_sapi_check_date = fields.Datetime(string="Delivery Service Status Check", copy=False, readonly=True)
    l10n_sk_sapi_is_sent = fields.Boolean(
        string="Handed over to the Delivery Service",
        compute='_compute_l10n_sk_sapi_is_sent',
    )

    @api.depends('l10n_sk_sapi_state', 'move_type')
    def _compute_l10n_sk_sapi_is_sent(self):
        for move in self:
            move.l10n_sk_sapi_is_sent = move.is_sale_document() and move.l10n_sk_sapi_state in SAPI_SENT_STATES

    @api.depends('l10n_sk_sapi_is_sent')
    def _compute_show_reset_to_draft_button(self):
        # EXTENDS account
        super()._compute_show_reset_to_draft_button()
        self.filtered('l10n_sk_sapi_is_sent').show_reset_to_draft_button = False

    @api.ondelete(at_uninstall=False)
    def _unlink_except_l10n_sk_sapi_sent(self):
        if self.filtered('l10n_sk_sapi_is_sent'):
            raise UserError(self.env._(
                "You cannot delete an invoice that was handed over to the delivery service."
                " To cancel it, issue a credit note."
            ))

    def _check_draftable(self):
        # EXTENDS account
        # The delivery service reports the invoice it took over to the tax authority: neither a reset
        # to draft nor a cancellation undoes that, only a credit note does.
        if self.filtered('l10n_sk_sapi_is_sent'):
            raise UserError(self.env._(
                "You cannot reset to draft an invoice that was handed over to the delivery service."
                " To change it, issue a credit note."
            ))
        return super()._check_draftable()

    # -------------------------------------------------------------------------
    # DELIVERY STATUS
    # -------------------------------------------------------------------------

    def _l10n_sk_sapi_update_states(self):
        """ Ask the delivery service for the delivery status of the invoices handed over to it. """
        for company, moves in self.grouped('company_id').items():
            provider_status = SAPI_PROVIDER_STATUS.get(company.l10n_sk_sapi_provider)
            if not provider_status or not company.l10n_sk_sapi_is_configured:
                continue
            try:
                client = company._l10n_sk_sapi_get_client()
            except UserError as error:
                _logger.warning("SAPI-SK: the delivery statuses of company %s were not updated: %s", company.id, error)
                continue
            for move in moves:
                move.l10n_sk_sapi_check_date = fields.Datetime.now()
                try:
                    document = client.request('GET', provider_status['path'] % quote(move.l10n_sk_sapi_document_id, safe=''))
                except SapiError as error:
                    if error.is_connection_failure:
                        _logger.warning("SAPI-SK: the delivery statuses of company %s were not updated: %s", company.id, error)
                        break
                    if error.status_code != 404:
                        # The service refuses this document only: the others are still asked for.
                        _logger.warning("SAPI-SK: no delivery status for the document %s: %s", move.l10n_sk_sapi_document_id, error)
                    # With 404 the service does not know the document (yet): the status is kept.
                    continue
                if provider_status['document_key']:
                    document = document.get(provider_status['document_key'])
                if not isinstance(document, dict):
                    continue
                state = provider_status['states'].get(document.get('status'))
                if state:
                    detail = document.get(provider_status['detail_key'])
                    move.l10n_sk_sapi_state = state
                    move.l10n_sk_sapi_state_detail = detail if isinstance(detail, str) and detail else False

    @api.model
    def _cron_l10n_sk_sapi_update_states(self, batch_size=SAPI_STATUS_BATCH_SIZE):
        run_start = fields.Datetime.now()
        domain = [
            ('l10n_sk_sapi_state', '=', 'processing'),
            ('l10n_sk_sapi_document_id', '!=', False),
            ('company_id.l10n_sk_sapi_provider', 'in', list(SAPI_PROVIDER_STATUS)),
        ]
        # The invoices that were not asked for the longest go first, so that none is starved.
        self.search(domain, order='l10n_sk_sapi_check_date, id', limit=batch_size)._l10n_sk_sapi_update_states()
        is_remaining = self.search_count([*domain, ('l10n_sk_sapi_check_date', '<', run_start)], limit=1)
        cron = self.env.ref('l10n_sk_edi_sapi.ir_cron_l10n_sk_sapi_update_states', raise_if_not_found=False)
        if is_remaining and cron:
            cron._trigger()

    # -------------------------------------------------------------------------
    # RECEIVED DOCUMENTS
    # -------------------------------------------------------------------------

    @api.model
    def _l10n_sk_sapi_get_received_document_ids(self, client):
        """ List the identifiers of the received documents that were not acknowledged yet. """
        document_ids = []
        page_token = None
        for _page in range(SAPI_MAX_PAGES):
            params = {'status': 'RECEIVED', 'limit': SAPI_PAGE_SIZE}
            if page_token:
                params['pageToken'] = page_token
            content = client.request('GET', '/document/receive', params=params)
            documents = content.get('documents')
            document_ids += [
                document['documentId']
                for document in (documents if isinstance(documents, list) else [])
                if isinstance(document, dict)
                and isinstance(document.get('documentId'), str)
                and document['documentId']
                and document['documentId'] not in document_ids
            ]
            if not content.get('nextPageToken') or content['nextPageToken'] == page_token:
                break
            page_token = content['nextPageToken']
        return document_ids

    @api.model
    def _l10n_sk_sapi_import_document(self, company, document_id, payload, invoice_number=None):
        """ Create the vendor bill of a received e-invoice.

        :param payload: The XML of the document, as a string.
        :return: The new vendor bill.
        """
        attachment = self.env['ir.attachment'].create({
            'name': f"{invoice_number or document_id}.xml".replace('/', '_'),
            'raw': payload.encode(),
            'mimetype': 'application/xml',
            'company_id': company.id,
        })
        move = self.with_company(company).create({
            'journal_id': company._l10n_sk_sapi_get_purchase_journal().id,
            'move_type': 'in_invoice',
            'l10n_sk_sapi_document_id': document_id,
        })
        if 'is_in_extractable_state' in move._fields:
            # The content comes from the structured file, not from a digitization of the PDF.
            move.is_in_extractable_state = False
        try:
            # No savepoint here: the import commits and rolls back by itself to isolate a broken file.
            move._extend_with_attachments(self._to_files_data(attachment), new=True)
        except Exception:  # noqa: BLE001
            # The content is third-party data and the service offers the document again until it is
            # acknowledged: whatever the import trips on, one document must not block the others.
            _logger.exception("SAPI-SK: the import of the received document %s failed", document_id)
        if not attachment.res_id:
            # The import did not recognize the file: it is kept on the bill to be processed by hand.
            attachment.write({'res_model': 'account.move', 'res_id': move.id})
            move._message_log(body=self.env._("The received e-invoice could not be read. The file is attached to the bill."))
        return move

    @api.model
    def _l10n_sk_sapi_get_new_documents(self, company):
        """ Download the e-invoices the delivery service received for the company, as vendor bills. """
        client = company._l10n_sk_sapi_get_client()
        if not company._l10n_sk_sapi_get_purchase_journal():
            raise UserError(self.env._("The company has no purchase journal for the received e-invoices."))
        new_moves = self.env['account.move']
        # The page tokens of some services are offsets in the list of the documents that are not
        # acknowledged: the whole list is read before the first acknowledgement shrinks it.
        document_ids = self._l10n_sk_sapi_get_received_document_ids(client)
        known_document_ids = set(self.search([
            ('l10n_sk_sapi_document_id', 'in', document_ids),
            ('company_id', '=', company.id),
            ('move_type', 'in', self.get_purchase_types(include_receipts=True)),
        ]).mapped('l10n_sk_sapi_document_id'))
        for document_id in document_ids:
            document_path = f"/document/receive/{quote(document_id, safe='')}"
            try:
                if document_id not in known_document_ids:
                    content = client.request('GET', document_path)
                    if not isinstance(content.get('payload'), str) or not content['payload']:
                        _logger.warning("SAPI-SK: the received document %s has no content, it is skipped", document_id)
                        continue
                    metadata = content.get('metadata')
                    invoice_number = metadata.get('invoiceNumber') if isinstance(metadata, dict) else None
                    new_moves += self._l10n_sk_sapi_import_document(
                        company,
                        document_id,
                        content['payload'],
                        invoice_number=invoice_number if isinstance(invoice_number, str) else None,
                    )
                client.request('POST', f'{document_path}/acknowledge')
            except SapiError as error:
                if error.is_connection_failure:
                    raise
                # The service refuses this document only: the others are still downloaded.
                _logger.warning("SAPI-SK: the received document %s was not processed: %s", document_id, error)
            if self.env['account.move.send']._can_commit():
                # The acknowledgement cannot be rolled back: the bill must not be lost with a later failure.
                self.env.cr.commit()
        return new_moves

    @api.model
    def _cron_l10n_sk_sapi_get_new_documents(self):
        for company in self.env['res.company'].search([('l10n_sk_sapi_url', '!=', False)]):
            if not company.l10n_sk_sapi_is_configured:
                continue
            try:
                self._l10n_sk_sapi_get_new_documents(company)
            except (SapiError, UserError) as error:
                _logger.warning("SAPI-SK: the received documents of company %s were not downloaded: %s", company.id, error)
