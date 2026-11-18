from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..tools.sapi_client import SapiClient


class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_sk_sapi_provider = fields.Selection(
        selection=[
            ('verteco', "Verteco"),
            ('efakturuj', "eFakturuj"),
            ('other', "Other SAPI-SK service"),
        ],
        string="Delivery Service",
        default='other',
        help="The delivery status of the sent invoices is only followed for the services whose status"
             " interface is known. With another service the invoice stays in the Handed over status.",
    )
    l10n_sk_sapi_url = fields.Char(
        string="SAPI-SK URL",
        help="Base address of the SAPI-SK interface of the delivery service, ending with /sapi.",
        # The credentials are sent to this address: only who may read them may change it.
        groups='base.group_system',
    )
    l10n_sk_sapi_client_id = fields.Char(string="SAPI-SK Client ID", groups='base.group_system')
    l10n_sk_sapi_client_secret = fields.Char(string="SAPI-SK Client Secret", groups='base.group_system')
    l10n_sk_sapi_is_configured = fields.Boolean(
        string="Delivery Service Connected",
        compute='_compute_l10n_sk_sapi_is_configured',
        compute_sudo=True,
    )
    l10n_sk_sapi_purchase_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string="Journal of Received E-invoices",
        domain="[('type', '=', 'purchase')]",
        check_company=True,
        help="Journal the e-invoices downloaded from the delivery service are created in. Without it the"
             " first purchase journal of the company is used.",
    )

    @api.depends('l10n_sk_sapi_url', 'l10n_sk_sapi_client_id', 'l10n_sk_sapi_client_secret')
    def _compute_l10n_sk_sapi_is_configured(self):
        for company in self:
            company.l10n_sk_sapi_is_configured = bool(
                company.l10n_sk_sapi_url and company.l10n_sk_sapi_client_id and company.l10n_sk_sapi_client_secret
            )

    @api.constrains('l10n_sk_sapi_url')
    def _check_l10n_sk_sapi_url(self):
        for company in self.sudo():
            if company.l10n_sk_sapi_url and not company.l10n_sk_sapi_url.startswith('https://'):
                raise ValidationError(self.env._("The address of the delivery service has to start with https://."))

    def _l10n_sk_sapi_get_error_message(self, error):
        """ Give the text to show to the user for a failed call to the delivery service.

        :param error: A SapiError.
        """
        if error.kind == 'timeout':
            return self.env._("The delivery service did not answer in time.")
        if error.kind == 'unreachable':
            return self.env._("The delivery service cannot be reached. Check its address in the Accounting settings.")
        if error.kind == 'redirect':
            return self.env._("The delivery service redirects to another address. Check its address in the Accounting settings.")
        if error.kind == 'invalid_answer':
            return self.env._("The delivery service sent an answer that cannot be read.")
        return error.message

    def _l10n_sk_sapi_get_client(self):
        """ Give the client of the delivery service of the company.

        :raise UserError: When the connection or the Peppol identifier of the company is missing.
        """
        self.ensure_one()
        # The credentials are restricted to the administrators, while any user allowed to send an
        # invoice has to reach the service: they are only read here, to build the client.
        company_sudo = self.sudo()
        if not company_sudo.l10n_sk_sapi_is_configured:
            raise UserError(self.env._("Set the address and the credentials of the delivery service in the Accounting settings."))
        participant_id = company_sudo.partner_id.routing_identifier
        if not participant_id:
            raise UserError(self.env._("The company has no Peppol identifier: fill in its tax identification number (DIC)."))
        return SapiClient(
            company_sudo.l10n_sk_sapi_url,
            company_sudo.l10n_sk_sapi_client_id,
            company_sudo.l10n_sk_sapi_client_secret,
            participant_id,
        )

    def _l10n_sk_sapi_get_purchase_journal(self):
        self.ensure_one()
        return self.l10n_sk_sapi_purchase_journal_id or self.env['account.journal'].search([
            *self.env['account.journal']._check_company_domain(self),
            ('type', '=', 'purchase'),
        ], limit=1)
