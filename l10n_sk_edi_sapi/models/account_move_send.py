import logging
import uuid
from datetime import timedelta

from lxml import etree

from odoo import api, fields, models
from odoo.exceptions import UserError

from ..tools.sapi_client import SapiError

_logger = logging.getLogger(__name__)

SAPI_PROCESS_ID = 'urn:fdc:peppol.eu:2017:poacc:billing:01:1.0'
SAPI_CUSTOMIZATION_ID = 'urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0'
SAPI_ROOT_NAMES = ('Invoice', 'CreditNote')


class AccountMoveSend(models.AbstractModel):
    _inherit = 'account.move.send'

    @api.model
    def _get_default_sending_methods(self, move):
        # EXTENDS account
        default_sending_methods = super()._get_default_sending_methods(move)

        if 'sk_sapi' in default_sending_methods:
            # The customer prefers the delivery service: an invoice goes through one network only.
            if 'peppol' in default_sending_methods:
                default_sending_methods.remove('peppol')
        elif (
            # A company connected to a Slovak delivery service sends the e-invoices of its Slovak
            # customers through it, unless another network was already picked for the invoice.
            'peppol' not in default_sending_methods
            and move.commercial_partner_id.country_code == 'SK'
            and self._is_applicable_to_move('sk_sapi', move)
        ):
            default_sending_methods.append('sk_sapi')
        return default_sending_methods

    def _get_default_invoice_edi_format(self, move, **kwargs):
        # EXTENDS account
        if 'sk_sapi' in kwargs.get('sending_methods', []):
            return 'ubl_bis3'
        return super()._get_default_invoice_edi_format(move, **kwargs)

    def _get_alerts(self, moves, moves_data):
        # EXTENDS account
        alerts = super()._get_alerts(moves, moves_data)
        if any(
            {'peppol', 'sk_sapi'}.issubset(moves_data[move]['sending_methods'])
            and self._is_applicable_to_move('sk_sapi', move, **moves_data[move])
            for move in moves
        ):
            alerts['l10n_sk_edi_sapi_one_network'] = {
                'level': 'warning',
                'message': self.env._(
                    "An invoice is delivered through one network only: with both selected, it goes through"
                    " the Slovak delivery service and not through Peppol."
                ),
            }
        return alerts

    def _is_applicable_to_company(self, method, company):
        # EXTENDS account
        if method == 'sk_sapi':
            return company.country_code == 'SK' and company.l10n_sk_sapi_is_configured
        return super()._is_applicable_to_company(method, company)

    def _is_applicable_to_move(self, method, move, **move_data):
        # EXTENDS account
        if method == 'sk_sapi':
            # The service only takes the Peppol BIS Billing 3.0 file of a customer document: an
            # invoice sent in another format has nothing to hand over.
            invoice_edi_format = move_data.get('invoice_edi_format') or 'ubl_bis3'
            return bool(
                self._is_applicable_to_company(method, move.company_id)
                and move.is_sale_document()
                and move.commercial_partner_id.routing_identifier
                and not move.l10n_sk_sapi_is_sent
                and (move.ubl_cii_xml_id or invoice_edi_format == 'ubl_bis3' and move._need_ubl_cii_xml('ubl_bis3'))
            )
        if (
            method == 'peppol'
            and 'sk_sapi' in (move_data.get('sending_methods') or [])
            and self._is_applicable_to_move('sk_sapi', move, **move_data)
        ):
            # Both networks deliver the invoice and report it to the tax authority: sending it
            # through both would do it twice.
            return False
        return super()._is_applicable_to_move(method, move, **move_data)

    def _hook_if_errors(self, moves_data, allow_raising=True):
        # EXTENDS account
        # An invoice whose file could not be generated never reaches the delivery service.
        for move, move_data in moves_data.items():
            if (
                'sk_sapi' in move_data['sending_methods']
                and move_data.get('blocking_error')
                and not move.l10n_sk_sapi_is_sent
                and move.l10n_sk_sapi_state != 'error'
            ):
                move.l10n_sk_sapi_state = 'error'
                move.l10n_sk_sapi_state_detail = False
        return super()._hook_if_errors(moves_data, allow_raising=allow_raising)

    def _call_web_service_after_invoice_pdf_render(self, invoices_data):
        # EXTENDS account
        super()._call_web_service_after_invoice_pdf_render(invoices_data)

        invoices_data_sapi = {
            invoice: invoice_data
            for invoice, invoice_data in invoices_data.items()
            if 'sk_sapi' in invoice_data['sending_methods'] and self._is_applicable_to_move('sk_sapi', invoice, **invoice_data)
        }
        if not invoices_data_sapi:
            return

        clients = {}
        # Companies whose service cannot be reached: the remaining invoices are not tried one by one.
        unreachable_companies = {}
        is_status_expected = False
        for invoice, invoice_data in invoices_data_sapi.items():
            company = invoice.company_id
            try:
                if company in unreachable_companies:
                    raise unreachable_companies[company]
                if not self.env['res.company']._with_locked_records(invoice, allow_raising=False):
                    raise UserError(self.env._("The invoice is being sent by another process already."))
                if company not in clients:
                    clients[company] = company._l10n_sk_sapi_get_client()
                self._l10n_sk_sapi_send_invoice(clients[company], invoice, invoice_data)
                is_status_expected |= invoice.l10n_sk_sapi_state == 'processing'
            except SapiError as error:
                if error.is_connection_failure:
                    unreachable_companies[company] = error
                # A request whose outcome is not known is repeated as it is by the scheduled sending.
                self._l10n_sk_sapi_set_error(
                    invoice, invoice_data, company._l10n_sk_sapi_get_error_message(error), is_retryable=error.is_transient,
                )
            except UserError as error:
                self._l10n_sk_sapi_set_error(invoice, invoice_data, error.args[0])
            except Exception:  # noqa: BLE001
                # The invoices before this one were handed over and cannot be taken back: a failure
                # of this one must not roll them back.
                _logger.exception("SAPI-SK: unexpected failure while handing over the invoice %s", invoice.id)
                self._l10n_sk_sapi_set_error(invoice, invoice_data, self.env._("An unexpected error occurred, see the server log."))
            if self._can_commit():
                # The hand-over cannot be rolled back: its result is kept even when a later invoice
                # or a later step fails.
                self.env.cr.commit()

        cron = self.env.ref('l10n_sk_edi_sapi.ir_cron_l10n_sk_sapi_update_states', raise_if_not_found=False)
        if is_status_expected and cron:
            # The delivery takes a moment: asking right away would only repeat "handed over".
            cron._trigger(at=fields.Datetime.now() + timedelta(minutes=5))

    def _l10n_sk_sapi_set_error(self, invoice, invoice_data, message, is_retryable=False):
        invoice.l10n_sk_sapi_state = 'error'
        invoice.l10n_sk_sapi_state_detail = message
        invoice_data['error'] = {
            'error_title': self.env._("The invoice was not handed over to the delivery service."),
            'errors': [message],
            'retry': is_retryable,
        }

    def _l10n_sk_sapi_get_invoice_xml(self, invoice, invoice_data):
        """ Give the Peppol BIS Billing 3.0 file of the invoice.

        :return: A tuple (file name, content as bytes, name of the root element).
        :raise UserError: When the invoice has no such file.
        """
        if invoice.invoice_pdf_report_id and self._needs_ubl_postprocessing(invoice_data):
            self._postprocess_invoice_ubl_xml(invoice, invoice_data)
        if invoice_data.get('ubl_cii_xml_attachment_values'):
            filename = invoice_data['ubl_cii_xml_attachment_values']['name']
            xml_content = bytes(invoice_data['ubl_cii_xml_attachment_values']['raw'])
        elif invoice.ubl_cii_xml_id:
            filename = invoice.ubl_cii_xml_id.name
            xml_content = bytes(invoice.ubl_cii_xml_id.raw)
        else:
            raise UserError(self.env._("The e-invoice file (Peppol BIS Billing 3.0) of the invoice is missing."))
        # A file stored by an earlier sending may be of another format.
        try:
            root = etree.fromstring(xml_content)
        except etree.XMLSyntaxError:
            root = None
        root_name = etree.QName(root).localname if root is not None else None
        customization_id = root.findtext('{*}CustomizationID') if root is not None else None
        if root_name not in SAPI_ROOT_NAMES or customization_id != SAPI_CUSTOMIZATION_ID:
            raise UserError(self.env._(
                "The e-invoice file of the invoice is not in the Peppol BIS Billing 3.0 format the delivery"
                " service takes. Reset the invoice to draft, confirm it and send it again."
            ))
        return filename, xml_content, root_name

    def _l10n_sk_sapi_send_invoice(self, client, invoice, invoice_data):
        """ Hand the e-invoice over to the delivery service and store the answer on the invoice.

        :raise SapiError: When the service cannot be reached or refuses the document.
        """
        filename, xml_content, root_name = self._l10n_sk_sapi_get_invoice_xml(invoice, invoice_data)
        # The key stays the same until the service gives a definitive answer, so that an attempt
        # repeated after a lost answer does not send the invoice twice.
        if not invoice.l10n_sk_sapi_idempotency_key:
            invoice.l10n_sk_sapi_idempotency_key = str(uuid.uuid4())
        idempotency_key = invoice.l10n_sk_sapi_idempotency_key
        try:
            content = client.request('POST', '/document/send', headers={'Idempotency-Key': idempotency_key}, json={
                'metadata': {
                    'documentId': idempotency_key,
                    'documentTypeId': (
                        f"urn:oasis:names:specification:ubl:schema:xsd:{root_name}-2::{root_name}"
                        f"##{SAPI_CUSTOMIZATION_ID}::2.1"
                    ),
                    'processId': SAPI_PROCESS_ID,
                    'senderParticipantId': client.participant_id,
                    'receiverParticipantId': invoice.commercial_partner_id.routing_identifier,
                    'creationDateTime': fields.Datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                },
                'payload': xml_content.decode(),
                'payloadFormat': 'XML',
            })
        except SapiError as error:
            if not error.is_transient:
                # The service refused the request: the next attempt is a new one.
                invoice.l10n_sk_sapi_idempotency_key = False
            raise
        status = content.get('status')
        document_id = content.get('providerDocumentId')
        if status == 'REJECTED':
            invoice.l10n_sk_sapi_idempotency_key = False
            detail = content.get('detail')
            raise SapiError(
                detail if isinstance(detail, str) and detail else self.env._("The delivery service rejected the document."),
                status_code=422,
            )
        if status != 'ACCEPTED' or not isinstance(document_id, str) or not document_id:
            # Neither accepted nor rejected: the outcome is not known and the key is kept.
            raise SapiError("The delivery service sent an answer that cannot be read.", kind='invalid_answer')

        invoice.write({
            'l10n_sk_sapi_idempotency_key': False,
            'l10n_sk_sapi_document_id': document_id,
            'l10n_sk_sapi_state': 'undeliverable' if content.get('undeliverable') else 'processing',
            'l10n_sk_sapi_state_detail': False,
            'l10n_sk_sapi_check_date': fields.Datetime.now(),
        })
        message = self.env._("The e-invoice was handed over to the delivery service (document %s).", document_id)
        warnings = content.get('warnings')
        warnings = [warning for warning in (warnings if isinstance(warnings, list) else []) if isinstance(warning, str)]
        if warnings:
            message = self.env._("%(message)s Warnings of the service: %(warnings)s", message=message, warnings=" ".join(warnings))
        # The file is kept with the record of the hand-over: the attachment of the invoice is only
        # linked later and would be lost with a failure of a later step.
        handed_over_file = self.env['ir.attachment'].create({
            'name': filename,
            'raw': xml_content,
            'mimetype': 'application/xml',
            'res_model': 'account.move',
            'res_id': invoice.id,
        })
        invoice._message_log(body=message, attachment_ids=handed_over_file.ids)
