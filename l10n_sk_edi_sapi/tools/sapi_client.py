import time

import requests

SAPI_TIMEOUT = 30
# The access token is renewed this many seconds before the delivery service lets it expire.
SAPI_TOKEN_MARGIN = 60
SAPI_TOKEN_LIFETIME = 900
# Answers after which the outcome of the request is not known: the request may be repeated as it is.
SAPI_TRANSIENT_STATUS_CODES = (408, 429)


class SapiError(Exception):
    """ Failure of a call to the delivery service.

    :param message:     Text of the service, or an English fallback when the service gave none.
    :param code:        Error code of the service, when it gave one.
    :param status_code: HTTP status of the answer, None when no usable answer came back.
    :param kind:        Reason of a failure that has no text of the service: 'timeout', 'unreachable',
                        'redirect' or 'invalid_answer'. The caller turns it into a translated message.
    """

    def __init__(self, message, code=None, status_code=None, kind=None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.kind = kind

    @property
    def is_transient(self):
        """ Whether the service may have processed the request although it reported no result. """
        return (
            self.status_code is None
            or self.status_code >= 500
            or self.status_code in SAPI_TRANSIENT_STATUS_CODES
        )

    @property
    def is_connection_failure(self):
        """ Whether the next call to the same service is bound to fail the same way. """
        return self.kind in ('timeout', 'unreachable', 'redirect') or self.status_code == 401


class SapiClient:
    """ Minimal client of the SAPI-SK 1.0 interface of a Slovak delivery service.

    :param url: Base URL of the interface, ending with '/sapi'.
    :param participant_id: Peppol identifier of the company the calls are made for ('0245:<DIC>').
    """

    def __init__(self, url, client_id, client_secret, participant_id):
        self.url = url.rstrip('/')
        self.client_id = client_id
        self.client_secret = client_secret
        self.participant_id = participant_id
        self._access_token = None
        self._access_token_deadline = 0

    def _call(self, method, path, headers=None, **kwargs):
        try:
            # A redirect would hand the credentials or the document over to another address.
            response = requests.request(
                method,
                self.url + path,
                headers=headers,
                timeout=SAPI_TIMEOUT,
                allow_redirects=False,
                **kwargs,
            )
        except requests.exceptions.Timeout as error:
            raise SapiError("The delivery service did not answer in time.", kind='timeout') from error
        except requests.exceptions.RequestException as error:
            # The text of the library exposes internals and is of no use to the user.
            raise SapiError("The delivery service cannot be reached.", kind='unreachable') from error
        if 300 <= response.status_code < 400:
            raise SapiError("The delivery service redirects to another address.", kind='redirect')
        try:
            content = response.json()
        except ValueError:
            content = None
        if not response.ok:
            message, code = self._get_error_message_and_code(response, content if isinstance(content, dict) else {})
            raise SapiError(message, code=code, status_code=response.status_code)
        if not isinstance(content, dict):
            raise SapiError("The delivery service sent an answer that cannot be read.", kind='invalid_answer')
        return content

    def _get_error_message_and_code(self, response, content):
        # The interface answers {'error': {'code', 'message'}}, the token endpoint may answer the
        # OAuth2 form {'error': 'invalid_client', 'error_description'}, some answers are flat and a
        # gateway may answer in the problem details form {'title', 'detail'}.
        error = content.get('error')
        if isinstance(error, dict):
            code = error.get('code')
            message = error.get('message')
        else:
            code = content.get('code') or error
            message = (
                content.get('message')
                or content.get('error_description')
                or content.get('detail')
                or content.get('title')
            )
        code = code if isinstance(code, str) else None
        message = message if isinstance(message, str) and message else response.reason or str(response.status_code)
        return (f"{code}: {message}" if code and code != message else message), code

    def _get_access_token(self):
        if not self._access_token or time.monotonic() >= self._access_token_deadline:
            content = self._call('POST', '/auth/token', json={
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
            })
            access_token = content.get('access_token')
            if not access_token or not isinstance(access_token, str):
                raise SapiError("The delivery service did not return an access token.", kind='invalid_answer')
            lifetime = content.get('expires_in')
            if not isinstance(lifetime, (int, float)) or lifetime <= 0:
                lifetime = SAPI_TOKEN_LIFETIME
            self._access_token = access_token
            self._access_token_deadline = time.monotonic() + lifetime - SAPI_TOKEN_MARGIN
        return self._access_token

    def authenticate(self):
        """ Check the credentials by asking for an access token. """
        self._get_access_token()

    def request(self, method, path, headers=None, **kwargs):
        """ Call a document endpoint on behalf of the participant.

        :return: The decoded JSON answer, a dictionary.
        :raise SapiError: When the service cannot be reached, refuses the call or answers something else
                          than a JSON object.
        """
        return self._call(method, path, headers={
            'Authorization': f"Bearer {self._get_access_token()}",
            'X-Peppol-Participant-Id': self.participant_id,
            **(headers or {}),
        }, **kwargs)
