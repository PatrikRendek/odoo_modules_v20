from contextlib import contextmanager
from unittest.mock import patch

import requests

from odoo.addons.l10n_sk_edi_einvoice.tests.common import TestSkEinvoiceCommon

SAPI_URL = 'https://sapi.example.test/sapi'


class FakeSapiResponse:

    def __init__(self, status_code=200, content=None):
        self.status_code = status_code
        self.ok = status_code < 400
        self.reason = "Fake reason"
        self._content = content

    def json(self):
        if self._content is None:
            raise ValueError("No JSON body")
        return self._content


class TestSkSapiCommon(TestSkEinvoiceCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company.write({
            'l10n_sk_sapi_provider': 'verteco',
            'l10n_sk_sapi_url': SAPI_URL,
            'l10n_sk_sapi_client_id': 'test-client',
            'l10n_sk_sapi_client_secret': 'test-secret',
        })

    @contextmanager
    def _mock_sapi(self, answers=None):
        """ Replace the delivery service by canned answers.

        :param answers: A dictionary {(HTTP method, path): answer}, where the answer is a FakeSapiResponse,
                        an exception to raise or a function of the request arguments giving one of them.
                        The token endpoint answers by itself unless it is given.
        :return: The list of the calls that were made, as dictionaries.
        """
        answers = {
            ('POST', '/auth/token'): FakeSapiResponse(content={'access_token': 'test-token', 'expires_in': 900}),
            **(answers or {}),
        }
        calls = []

        def fake_request(method, url, **kwargs):
            path = url.removeprefix(SAPI_URL)
            calls.append({'method': method, 'path': path, **kwargs})
            if (method, path) not in answers:
                return FakeSapiResponse(status_code=404, content={
                    'error': {'code': 'SAPI-RES-001', 'message': "Document not found."},
                })
            answer = answers[method, path]
            if callable(answer):
                answer = answer(**kwargs)
            if isinstance(answer, Exception):
                raise answer
            return answer

        with patch('odoo.addons.l10n_sk_edi_sapi.tools.sapi_client.requests.request', side_effect=fake_request):
            yield calls

    def _get_calls(self, calls, method, path):
        return [call for call in calls if call['method'] == method and call['path'] == path]

    def _send_through_sapi(self, invoices, **kwargs):
        return self.env['account.move.send']._generate_and_send_invoices(
            invoices,
            sending_methods=['sk_sapi'],
            allow_raising=False,
            **kwargs,
        )

    @staticmethod
    def _connection_error():
        return requests.exceptions.ConnectionError("Connection refused")
