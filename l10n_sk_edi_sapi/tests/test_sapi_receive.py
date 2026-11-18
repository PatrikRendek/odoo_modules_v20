from unittest.mock import patch

from odoo.tests import tagged
from odoo.tools import file_open, mute_logger

from odoo.addons.l10n_sk_edi_sapi.tests.common import FakeSapiResponse, TestSkSapiCommon

MOVE_LOGGER = 'odoo.addons.l10n_sk_edi_sapi.models.account_move'


@tagged('post_install_l10n', 'post_install', '-at_install')
class TestSkSapiReceive(TestSkSapiCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with file_open('l10n_sk_edi_einvoice/tests/test_files/sk_invoice_domestic.xml', 'r') as file:
            cls.received_xml = file.read()

    def _received_answers(self):
        def list_documents(params=None, **kwargs):
            if params.get('pageToken') == 'page-2':
                return FakeSapiResponse(content={'documents': [{'documentId': 'in-0002'}]})
            return FakeSapiResponse(content={'documents': [{'documentId': 'in-0001'}], 'nextPageToken': 'page-2'})

        return {
            ('GET', '/document/receive'): list_documents,
            ('GET', '/document/receive/in-0001'): FakeSapiResponse(content={
                'metadata': {'documentId': 'in-0001', 'invoiceNumber': 'FV/2027/0001'},
                'payload': self.received_xml,
                'payloadFormat': 'XML',
            }),
            # A document without content must not stop the others.
            ('GET', '/document/receive/in-0002'): FakeSapiResponse(content={'metadata': {'documentId': 'in-0002'}}),
            ('POST', '/document/receive/in-0001/acknowledge'): FakeSapiResponse(content={'status': 'ACKNOWLEDGED'}),
        }

    @mute_logger(MOVE_LOGGER)
    def test_received_invoice_becomes_a_vendor_bill(self):
        with self._mock_sapi(self._received_answers()) as calls:
            self.env['account.move']._cron_l10n_sk_sapi_get_new_documents()

        list_calls = self._get_calls(calls, 'GET', '/document/receive')
        self.assertEqual([call['params'].get('pageToken') for call in list_calls], [None, 'page-2'])
        self.assertEqual(list_calls[0]['params']['status'], 'RECEIVED')
        self.assertEqual(list_calls[0]['headers']['X-Peppol-Participant-Id'], '0245:2020317068')

        bill = self.env['account.move'].search([('l10n_sk_sapi_document_id', '=', 'in-0001')])
        self.assertEqual(len(bill), 1)
        self.assertRecordValues(bill, [{
            'move_type': 'in_invoice',
            'state': 'draft',
            'company_id': self.company.id,
            'l10n_sk_sapi_is_sent': False,
        }])
        self.assertTrue(bill.partner_id)
        self.assertTrue(bill.invoice_line_ids)
        self.assertEqual(bill.ubl_cii_xml_id.name, 'FV_2027_0001.xml')
        self.assertEqual(len(self._get_calls(calls, 'POST', '/document/receive/in-0001/acknowledge')), 1)
        self.assertFalse(self._get_calls(calls, 'POST', '/document/receive/in-0002/acknowledge'))
        self.assertFalse(self.env['account.move'].search([('l10n_sk_sapi_document_id', '=', 'in-0002')]))

    @mute_logger(MOVE_LOGGER)
    def test_known_document_is_only_acknowledged(self):
        """ A document whose acknowledgement was lost is not imported a second time. """
        with self._mock_sapi(self._received_answers()):
            self.env['account.move']._cron_l10n_sk_sapi_get_new_documents()
        with self._mock_sapi(self._received_answers()) as calls:
            self.env['account.move']._cron_l10n_sk_sapi_get_new_documents()

        self.assertEqual(self.env['account.move'].search_count([('l10n_sk_sapi_document_id', '=', 'in-0001')]), 1)
        self.assertFalse(self._get_calls(calls, 'GET', '/document/receive/in-0001'))
        self.assertEqual(len(self._get_calls(calls, 'POST', '/document/receive/in-0001/acknowledge')), 1)

    def test_unreadable_document_is_kept_on_the_bill(self):
        """ A file the import does not recognize is not lost: it is attached to an empty bill. """
        answers = {
            ('GET', '/document/receive'): FakeSapiResponse(content={'documents': [{'documentId': 'in-0003'}]}),
            ('GET', '/document/receive/in-0003'): FakeSapiResponse(content={'payload': '<Unknown/>'}),
            ('POST', '/document/receive/in-0003/acknowledge'): FakeSapiResponse(content={'status': 'ACKNOWLEDGED'}),
        }
        with self._mock_sapi(answers) as calls:
            self.env['account.move']._cron_l10n_sk_sapi_get_new_documents()

        bill = self.env['account.move'].search([('l10n_sk_sapi_document_id', '=', 'in-0003')])
        self.assertEqual(len(bill), 1)
        attachments = self.env['ir.attachment'].search([('res_model', '=', 'account.move'), ('res_id', '=', bill.id)])
        self.assertEqual(attachments.mapped('name'), ['in-0003.xml'])
        self.assertEqual(len(self._get_calls(calls, 'POST', '/document/receive/in-0003/acknowledge')), 1)

    @mute_logger(MOVE_LOGGER)
    def test_failing_import_does_not_block_the_other_documents(self):
        """ A document the import crashes on is kept as an empty bill and acknowledged like the others. """
        answers = self._received_answers()
        answers['GET', '/document/receive'] = FakeSapiResponse(content={
            'documents': [{'documentId': 'in-0004'}, {'documentId': 'in-0001'}],
        })
        answers['GET', '/document/receive/in-0004'] = FakeSapiResponse(content={'payload': self.received_xml})
        answers['POST', '/document/receive/in-0004/acknowledge'] = FakeSapiResponse(content={'status': 'ACKNOWLEDGED'})
        AccountMove = self.env.registry['account.move']
        original_extend = AccountMove._extend_with_attachments

        def failing_extend(move, *args, **kwargs):
            if move.l10n_sk_sapi_document_id == 'in-0004':
                raise ValueError("Broken document")
            return original_extend(move, *args, **kwargs)

        with self._mock_sapi(answers) as calls, patch.object(AccountMove, '_extend_with_attachments', failing_extend):
            self.env['account.move']._cron_l10n_sk_sapi_get_new_documents()

        broken_bill = self.env['account.move'].search([('l10n_sk_sapi_document_id', '=', 'in-0004')])
        self.assertEqual(len(broken_bill), 1)
        self.assertFalse(broken_bill.invoice_line_ids)
        attachments = self.env['ir.attachment'].search([('res_model', '=', 'account.move'), ('res_id', '=', broken_bill.id)])
        self.assertEqual(attachments.mapped('name'), ['in-0004.xml'])
        self.assertTrue(self.env['account.move'].search([('l10n_sk_sapi_document_id', '=', 'in-0001')]).invoice_line_ids)
        self.assertEqual(len(self._get_calls(calls, 'POST', '/document/receive/in-0004/acknowledge')), 1)
        self.assertEqual(len(self._get_calls(calls, 'POST', '/document/receive/in-0001/acknowledge')), 1)

    @mute_logger(MOVE_LOGGER)
    def test_document_refused_by_the_service_does_not_block_the_others(self):
        answers = self._received_answers()
        answers['GET', '/document/receive'] = FakeSapiResponse(content={
            'documents': [{'documentId': 'in-0005'}, {'documentId': 'in-0001'}, {'documentId': 17}, "garbage"],
        })
        answers['GET', '/document/receive/in-0005'] = FakeSapiResponse(status_code=500)
        with self._mock_sapi(answers) as calls:
            self.env['account.move']._cron_l10n_sk_sapi_get_new_documents()

        self.assertTrue(self.env['account.move'].search([('l10n_sk_sapi_document_id', '=', 'in-0001')]))
        self.assertFalse(self.env['account.move'].search([('l10n_sk_sapi_document_id', '=', 'in-0005')]))
        self.assertFalse(self._get_calls(calls, 'POST', '/document/receive/in-0005/acknowledge'))

    @mute_logger(MOVE_LOGGER)
    def test_bill_goes_to_the_configured_journal(self):
        journal = self.company_data['default_journal_purchase'].copy({'name': "Received e-invoices"})
        self.company.l10n_sk_sapi_purchase_journal_id = journal
        with self._mock_sapi(self._received_answers()):
            self.env['account.move']._cron_l10n_sk_sapi_get_new_documents()

        self.assertEqual(self.env['account.move'].search([('l10n_sk_sapi_document_id', '=', 'in-0001')]).journal_id, journal)

    @mute_logger(MOVE_LOGGER)
    def test_unreachable_service_does_not_fail_the_cron(self):
        with self._mock_sapi({('POST', '/auth/token'): self._connection_error()}):
            self.env['account.move']._cron_l10n_sk_sapi_get_new_documents()

        self.assertFalse(self.env['account.move'].search([('l10n_sk_sapi_document_id', '!=', False)]))
