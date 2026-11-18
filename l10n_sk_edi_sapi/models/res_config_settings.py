from odoo import fields, models
from odoo.exceptions import UserError

from ..tools.sapi_client import SapiError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    l10n_sk_sapi_provider = fields.Selection(related='company_id.l10n_sk_sapi_provider', readonly=False)
    l10n_sk_sapi_url = fields.Char(related='company_id.l10n_sk_sapi_url', readonly=False)
    l10n_sk_sapi_client_id = fields.Char(related='company_id.l10n_sk_sapi_client_id', readonly=False)
    l10n_sk_sapi_client_secret = fields.Char(related='company_id.l10n_sk_sapi_client_secret', readonly=False)
    l10n_sk_sapi_purchase_journal_id = fields.Many2one(
        related='company_id.l10n_sk_sapi_purchase_journal_id',
        readonly=False,
    )

    def action_l10n_sk_sapi_test_connection(self):
        self.ensure_one()
        try:
            self.company_id._l10n_sk_sapi_get_client().authenticate()
        except SapiError as error:
            raise UserError(self.env._(
                "The delivery service refused the connection: %s",
                self.company_id._l10n_sk_sapi_get_error_message(error),
            )) from error
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': self.env._("The connection to the delivery service works."),
            },
        }
