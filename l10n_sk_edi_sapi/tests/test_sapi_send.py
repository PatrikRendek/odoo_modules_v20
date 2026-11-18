from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.l10n_sk_edi_sapi.tests.common import FakeSapiResponse, TestSkSapiCommon


@tagged('post_install_l10n', 'post_install', '-at_install')
class TestSkSapiSend(TestSkSapiCommon):

    def _accepted(self, **values):
        return FakeSapiResponse(status_code=202, content={
            'providerDocumentId': 'doc-0001',
            'status': 'ACCEPTED',
            **values,
        })

    def test_send_hands_the_invoice_over(self):
        """ The e-invoice is posted to the service with the Peppol identifiers of both parties. """
        invoice = self._create_sk_invoice()
        with self._mock_sapi({('POST', '/document/send'): self._accepted(warnings=["Check the date."])}) as calls:
            self._send_through_sapi(invoice)

        token_call = self._get_calls(calls, 'POST', '/auth/token')[0]
        self.assertEqual(token_call['json'], {
            'grant_type': 'client_credentials',
            'client_id': 'test-client',
            'client_secret': 'test-secret',
        })
        send_call = self._get_calls(calls, 'POST', '/document/send')[0]
        self.assertEqual(send_call['headers']['Authorization'], 'Bearer test-token')
        self.assertEqual(send_call['headers']['X-Peppol-Participant-Id'], '0245:2020317068')
        self.assertTrue(send_call['headers']['Idempotency-Key'])
        body = send_call['json']
        self.assertEqual(body['payloadFormat'], 'XML')
        self.assertRegex(body['metadata']['creationDateTime'], r'^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$')
        self.assertEqual(body['metadata']['senderParticipantId'], '0245:2020317068')
        self.assertEqual(body['metadata']['receiverParticipantId'], '0245:2022749619')
        self.assertEqual(
            body['metadata']['documentTypeId'],
            'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2::Invoice'
            '##urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0::2.1',
        )
        self.assertIn(f'<cbc:ID>{invoice.name}</cbc:ID>', body['payload'])

        self.assertRecordValues(invoice, [{
            'l10n_sk_sapi_state': 'processing',
            'l10n_sk_sapi_document_id': 'doc-0001',
            'l10n_sk_sapi_idempotency_key': False,
            'l10n_sk_sapi_is_sent': True,
        }])
        self.assertTrue(invoice.ubl_cii_xml_id)
        self.assertIn("Check the date.", invoice.message_ids[0].body)

    def test_credit_note_document_type(self):
        invoice = self._create_sk_invoice()
        credit_note = invoice._reverse_moves([{'invoice_date': '2027-01-25'}])
        credit_note.action_post()
        with self._mock_sapi({('POST', '/document/send'): self._accepted()}) as calls:
            self._send_through_sapi(credit_note)

        self.assertTrue(
            self._get_calls(calls, 'POST', '/document/send')[0]['json']['metadata']['documentTypeId'].startswith(
                'urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2::CreditNote##'
            )
        )

    def test_recipient_not_on_the_network(self):
        invoice = self._create_sk_invoice()
        with self._mock_sapi({('POST', '/document/send'): self._accepted(undeliverable=True)}):
            self._send_through_sapi(invoice)

        self.assertEqual(invoice.l10n_sk_sapi_state, 'undeliverable')

    def test_document_rejected_by_the_service(self):
        """ A document the service refuses stays unsent and can be sent again after its correction. """
        invoice = self._create_sk_invoice()
        rejected = FakeSapiResponse(status_code=202, content={
            'providerDocumentId': 'doc-0002',
            'status': 'REJECTED',
            'detail': "validation_failed: BR-CO-15",
        })
        with self._mock_sapi({('POST', '/document/send'): rejected}):
            self._send_through_sapi(invoice)

        self.assertRecordValues(invoice, [{
            'l10n_sk_sapi_state': 'error',
            'l10n_sk_sapi_state_detail': "validation_failed: BR-CO-15",
            'l10n_sk_sapi_document_id': False,
            'l10n_sk_sapi_is_sent': False,
        }])
        self.assertTrue(self.env['account.move.send']._is_applicable_to_move('sk_sapi', invoice))

        with self._mock_sapi({('POST', '/document/send'): self._accepted()}):
            self._send_through_sapi(invoice)
        self.assertEqual(invoice.l10n_sk_sapi_state, 'processing')

    def test_service_error_is_shown(self):
        invoice = self._create_sk_invoice()
        refused = FakeSapiResponse(status_code=401, content={
            'error': {'code': 'SAPI-AUTH-003', 'message': "Participant not authorized."},
        })
        with self._mock_sapi({('POST', '/document/send'): refused}):
            self._send_through_sapi(invoice)

        self.assertRecordValues(invoice, [{
            'l10n_sk_sapi_state': 'error',
            'l10n_sk_sapi_state_detail': "SAPI-AUTH-003: Participant not authorized.",
        }])

    def test_lost_answer_keeps_the_idempotency_key(self):
        """ An attempt repeated after a network failure reuses the key, so the invoice is not sent twice. """
        invoice = self._create_sk_invoice()
        with self._mock_sapi({('POST', '/document/send'): self._connection_error()}) as failed_calls:
            self._send_through_sapi(invoice)
        self.assertEqual(invoice.l10n_sk_sapi_state, 'error')
        first_key = self._get_calls(failed_calls, 'POST', '/document/send')[0]['headers']['Idempotency-Key']
        self.assertEqual(invoice.l10n_sk_sapi_idempotency_key, first_key)

        with self._mock_sapi({('POST', '/document/send'): self._accepted()}) as calls:
            self._send_through_sapi(invoice)
        self.assertEqual(self._get_calls(calls, 'POST', '/document/send')[0]['headers']['Idempotency-Key'], first_key)
        self.assertEqual(invoice.l10n_sk_sapi_state, 'processing')

    def test_sent_invoice_cannot_be_changed(self):
        invoice = self._create_sk_invoice()
        with self._mock_sapi({('POST', '/document/send'): self._accepted()}) as calls:
            self._send_through_sapi(invoice)
            self.assertFalse(self.env['account.move.send']._is_applicable_to_move('sk_sapi', invoice))
            self._send_through_sapi(invoice)

        self.assertEqual(len(self._get_calls(calls, 'POST', '/document/send')), 1)
        self.assertFalse(invoice.show_reset_to_draft_button)
        with self.assertRaises(UserError):
            invoice.button_draft()

    def test_default_sending_method(self):
        """ The delivery service is preselected for the Slovak customers of a connected company only. """
        AccountMoveSend = self.env['account.move.send']
        invoice = self._create_sk_invoice()
        self.assertIn('sk_sapi', AccountMoveSend._get_default_sending_methods(invoice))
        self.assertEqual(AccountMoveSend._get_default_invoice_edi_format(invoice, sending_methods=['sk_sapi']), 'ubl_bis3')

        foreign_invoice = self._create_sk_invoice(partner=self.partner_a)
        self.assertNotIn('sk_sapi', AccountMoveSend._get_default_sending_methods(foreign_invoice))

        self.company.l10n_sk_sapi_client_secret = False
        self.assertFalse(AccountMoveSend._is_applicable_to_company('sk_sapi', self.company))
        self.assertNotIn('sk_sapi', AccountMoveSend._get_default_sending_methods(invoice))

    def test_delivery_status_update(self):
        invoices = self._create_sk_invoice() + self._create_sk_invoice() + self._create_sk_invoice()
        for index, invoice in enumerate(invoices):
            invoice.write({'l10n_sk_sapi_state': 'processing', 'l10n_sk_sapi_document_id': f'doc-{index}'})
        answers = {
            ('GET', '/document/sent/doc-0'): FakeSapiResponse(content={'document': {'status': 'delivered'}}),
            ('GET', '/document/sent/doc-1'): FakeSapiResponse(content={
                'document': {'status': 'rejected', 'statusDetail': "Unknown buyer"},
            }),
            # 'doc-2' is not known by the service yet: it answers 404.
        }
        with self._mock_sapi(answers):
            self.env['account.move']._cron_l10n_sk_sapi_update_states()

        self.assertRecordValues(invoices, [
            {'l10n_sk_sapi_state': 'delivered', 'l10n_sk_sapi_state_detail': False},
            {'l10n_sk_sapi_state': 'rejected', 'l10n_sk_sapi_state_detail': "Unknown buyer"},
            {'l10n_sk_sapi_state': 'processing', 'l10n_sk_sapi_state_detail': False},
        ])
        # A rejected invoice was not delivered: it can be corrected.
        self.assertFalse(invoices[1].l10n_sk_sapi_is_sent)

    def test_delivery_status_update_efakturuj(self):
        """ eFakturuj answers on its own status endpoint, with the document at the top level. """
        self.company.l10n_sk_sapi_provider = 'efakturuj'
        invoices = self._create_sk_invoice() + self._create_sk_invoice() + self._create_sk_invoice()
        for index, invoice in enumerate(invoices):
            invoice.write({'l10n_sk_sapi_state': 'processing', 'l10n_sk_sapi_document_id': f'efk_sapi_doc_{index}'})
        answers = {
            ('GET', '/document/status/efk_sapi_doc_0'): FakeSapiResponse(content={'status': 'SENT', 'errorMessage': None}),
            ('GET', '/document/status/efk_sapi_doc_1'): FakeSapiResponse(content={
                'status': 'FAILED',
                'errorMessage': "EBMS:0004",
            }),
            ('GET', '/document/status/efk_sapi_doc_2'): FakeSapiResponse(content={'status': 'PROCESSING'}),
        }
        with self._mock_sapi(answers):
            self.env['account.move']._cron_l10n_sk_sapi_update_states()

        self.assertRecordValues(invoices, [
            {'l10n_sk_sapi_state': 'delivered', 'l10n_sk_sapi_state_detail': False},
            {'l10n_sk_sapi_state': 'error', 'l10n_sk_sapi_state_detail': "EBMS:0004"},
            {'l10n_sk_sapi_state': 'processing', 'l10n_sk_sapi_state_detail': False},
        ])

    def test_delivery_status_is_not_followed_for_other_services(self):
        self.company.l10n_sk_sapi_provider = 'other'
        invoice = self._create_sk_invoice()
        invoice.write({'l10n_sk_sapi_state': 'processing', 'l10n_sk_sapi_document_id': 'doc-0'})
        with self._mock_sapi() as calls:
            self.env['account.move']._cron_l10n_sk_sapi_update_states()

        self.assertFalse(calls)
        self.assertEqual(invoice.l10n_sk_sapi_state, 'processing')

    def test_connection_check(self):
        settings = self.env['res.config.settings'].create({})
        with self._mock_sapi():
            self.assertEqual(settings.action_l10n_sk_sapi_test_connection()['params']['type'], 'success')

        refused = FakeSapiResponse(status_code=401, content={
            'error': {'code': 'SAPI-AUTH-001', 'message': "Invalid client credentials."},
        })
        with self._mock_sapi({('POST', '/auth/token'): refused}), self.assertRaisesRegex(UserError, "SAPI-AUTH-001"):
            settings.action_l10n_sk_sapi_test_connection()

    # -------------------------------------------------------------------------
    # ROBUSTNESS
    # -------------------------------------------------------------------------

    def test_batch_continues_after_a_rejected_invoice(self):
        """ An invoice the service refuses does not undo nor stop the hand-over of the others. """
        invoices = self._create_sk_invoice() + self._create_sk_invoice() + self._create_sk_invoice()
        refused_number = invoices[1].name

        def answer(json=None, **kwargs):
            if f'<cbc:ID>{refused_number}</cbc:ID>' in json['payload']:
                return FakeSapiResponse(status_code=202, content={'status': 'REJECTED', 'detail': "BR-CO-15"})
            return self._accepted(providerDocumentId=f"doc-{json['metadata']['documentId']}")

        with self._mock_sapi({('POST', '/document/send'): answer}) as calls:
            self._send_through_sapi(invoices)

        self.assertEqual(len(self._get_calls(calls, 'POST', '/document/send')), 3)
        self.assertEqual(invoices.mapped('l10n_sk_sapi_state'), ['processing', 'error', 'processing'])
        self.assertEqual(invoices[1].l10n_sk_sapi_state_detail, "BR-CO-15")
        self.assertEqual(len(set(invoices.mapped('l10n_sk_sapi_document_id'))), 3)

    def test_unreachable_service_is_called_once_per_batch(self):
        """ The invoices of a batch are not tried one by one against a service that does not answer. """
        invoices = self._create_sk_invoice() + self._create_sk_invoice() + self._create_sk_invoice()
        with self._mock_sapi({('POST', '/document/send'): self._connection_error()}) as calls:
            self._send_through_sapi(invoices)

        self.assertEqual(len(self._get_calls(calls, 'POST', '/document/send')), 1)
        self.assertEqual(invoices.mapped('l10n_sk_sapi_state'), ['error'] * 3)

    def test_gateway_error_keeps_the_idempotency_key(self):
        """ After an answer that does not tell the outcome, the next attempt repeats the same request. """
        invoice = self._create_sk_invoice()
        with self._mock_sapi({('POST', '/document/send'): FakeSapiResponse(status_code=504)}) as failed_calls:
            self._send_through_sapi(invoice)
        first_key = self._get_calls(failed_calls, 'POST', '/document/send')[0]['headers']['Idempotency-Key']
        self.assertRecordValues(invoice, [{'l10n_sk_sapi_state': 'error', 'l10n_sk_sapi_idempotency_key': first_key}])

        # A 200 answer that is neither an acceptance nor a rejection does not tell the outcome either.
        with self._mock_sapi({('POST', '/document/send'): FakeSapiResponse(content={})}) as unclear_calls:
            self._send_through_sapi(invoice)
        self.assertEqual(self._get_calls(unclear_calls, 'POST', '/document/send')[0]['headers']['Idempotency-Key'], first_key)
        self.assertEqual(invoice.l10n_sk_sapi_idempotency_key, first_key)

        refused = FakeSapiResponse(status_code=400, content={'error': {'code': 'SAPI-VAL-001', 'message': "Bad request."}})
        with self._mock_sapi({('POST', '/document/send'): refused}):
            self._send_through_sapi(invoice)
        self.assertFalse(invoice.l10n_sk_sapi_idempotency_key)

    def test_one_network_per_invoice(self):
        """ An invoice ticked for both networks only goes through the delivery service. """
        AccountMoveSend = self.env['account.move.send']
        invoice = self._create_sk_invoice()
        self.assertFalse(AccountMoveSend._is_applicable_to_move('peppol', invoice, sending_methods=['peppol', 'sk_sapi']))

        self.partner_sk.invoice_sending_method = 'sk_sapi'
        default_sending_methods = AccountMoveSend._get_default_sending_methods(invoice)
        self.assertIn('sk_sapi', default_sending_methods)
        self.assertNotIn('peppol', default_sending_methods)

    def test_vendor_bill_is_not_handed_over(self):
        bill = self._create_sk_invoice(move_type='in_invoice')
        self.assertFalse(self.env['account.move.send']._is_applicable_to_move('sk_sapi', bill))

    def test_address_of_the_service_must_be_secure(self):
        with self.assertRaises(ValidationError):
            self.company.l10n_sk_sapi_url = 'http://sapi.example.test/sapi'

    @mute_logger('odoo.addons.l10n_sk_edi_sapi.models.account_move')
    def test_delivery_status_of_one_document_refused(self):
        """ A document the service refuses to report on does not stop the others. """
        invoices = self._create_sk_invoice() + self._create_sk_invoice()
        for index, invoice in enumerate(invoices):
            invoice.write({'l10n_sk_sapi_state': 'processing', 'l10n_sk_sapi_document_id': f'doc-{index}'})
        answers = {
            ('GET', '/document/sent/doc-0'): FakeSapiResponse(status_code=500),
            ('GET', '/document/sent/doc-1'): FakeSapiResponse(content={'document': {'status': 'delivered'}}),
        }
        with self._mock_sapi(answers):
            self.env['account.move']._cron_l10n_sk_sapi_update_states()

        self.assertEqual(invoices.mapped('l10n_sk_sapi_state'), ['processing', 'delivered'])
        self.assertTrue(all(invoices.mapped('l10n_sk_sapi_check_date')))

    def test_handed_over_file_is_kept_in_the_history(self):
        invoice = self._create_sk_invoice()
        with self._mock_sapi({('POST', '/document/send'): self._accepted()}):
            self._send_through_sapi(invoice)

        attachment = invoice.message_ids[0].attachment_ids
        self.assertEqual(len(attachment), 1)
        self.assertIn(f'<cbc:ID>{invoice.name}</cbc:ID>'.encode(), bytes(attachment.raw))

