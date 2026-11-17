import re

from odoo import api, fields, models

from .account_edi_xml_ubl_bis3 import SK_TIN_RE, SK_TIN_SCHEME, SK_VAT_RE


class AccountMoveSend(models.AbstractModel):
    _inherit = 'account.move.send'

    @api.model
    def _get_default_sending_methods(self, move):
        # EXTENDS account
        default_sending_methods = super()._get_default_sending_methods(move)

        # The Slovak e-invoice has to go through a delivery service: when the Peppol connection of
        # Odoo is installed and usable for the invoice, it is preselected for Slovak customers too.
        if (
            'peppol' not in default_sending_methods
            and 'peppol_move_state' in move._fields
            and move.country_code == 'SK'
            and move.commercial_partner_id.country_code == 'SK'
            and self._is_applicable_to_move('peppol', move)
        ):
            default_sending_methods.append('peppol')
        return default_sending_methods

    def _l10n_sk_edi_get_incomplete_partners(self, partner):
        """ Give the contacts to complete before the Slovak e-invoice of a party can be generated.

        The address is the one of the contact the document is addressed to, the identifiers are those
        of its commercial entity: the same data the generation of the file checks.

        :param partner: The contact of the supplier or of the customer of the document.
        """
        commercial_partner = partner.commercial_partner_id
        incomplete_partners = self.env['res.partner']
        if commercial_partner.country_code != 'SK':
            return incomplete_partners
        if not (partner.street and partner.city and partner.zip):
            incomplete_partners |= partner
        vat_number = re.sub(r'\s', '', commercial_partner.vat or '').upper()
        if (
            commercial_partner.routing_scheme != SK_TIN_SCHEME
            or not SK_TIN_RE.fullmatch(commercial_partner.routing_endpoint or '')
            or vat_number and not SK_VAT_RE.fullmatch(vat_number)
        ):
            incomplete_partners |= commercial_partner
        return incomplete_partners

    def _get_alerts(self, moves, moves_data):
        # EXTENDS account
        alerts = super()._get_alerts(moves, moves_data)

        # The generation of the file refuses a Slovak party without its mandatory data: the contacts
        # to complete are pointed out before the user clicks on Send.
        sk_moves = moves.filtered(lambda move: (
            move.country_code == 'SK'
            and move.is_sale_document()
            and moves_data[move].get('invoice_edi_format') == 'ubl_bis3'
        ))
        incomplete_partners = self.env['res.partner']
        for partner in sk_moves.company_id.partner_id | sk_moves.partner_id:
            incomplete_partners |= self._l10n_sk_edi_get_incomplete_partners(partner)
        if incomplete_partners:
            if sk_moves == moves and all(move.commercial_partner_id.country_code == 'SK' for move in moves):
                # The generic hints about a missing Peppol address are covered by this more precise
                # one, unless they concern a contact this one does not look at.
                alerts.pop('account_edi_ubl_cii_configure_company', None)
                alerts.pop('account_edi_ubl_cii_configure_partner', None)
            alerts['l10n_sk_edi_einvoice_partner_data'] = {
                'level': 'warning',
                'message': self.env._(
                    "Complete these contacts before sending the Slovak e-invoice (%(partners)s): each needs its"
                    " street, city and ZIP, its tax identification number (DIC, 10 digits) and, when it has"
                    " one, a VAT number made of SK and 10 digits.",
                    partners=incomplete_partners.mapped('display_name'),
                ),
                'action_text': self.env._("View Partner(s)"),
                'action': incomplete_partners._get_records_action(name=self.env._("Check Partner(s)")),
            }

        # A Slovak e-invoice is issued when it is handed over to the delivery service: the issue date it
        # states has to be the day it is actually sent. The date of a posted invoice cannot be changed
        # here, so the user is warned before sending instead.
        today = fields.Date.context_today(self)
        misdated_moves = moves.filtered(lambda move: (
            move.country_code == 'SK'
            and move.commercial_partner_id.country_code == 'SK'
            and move.is_sale_document()
            and not move.is_move_sent
            and moves_data[move].get('invoice_edi_format') == 'ubl_bis3'
            and move.invoice_date
            and move.invoice_date != today
        ))
        if misdated_moves:
            is_batch = len(moves) > 1
            alerts['l10n_sk_edi_einvoice_issue_date'] = {
                'level': 'warning',
                'message': self.env._(
                    "The invoice date is not today. A Slovak e-invoice must state the day it is sent as its"
                    " issue date: send it on the invoice date, or reset the invoice to draft and change its"
                    " date first."
                ),
                'action_text': self.env._("View Invoice(s)") if is_batch else None,
                'action': misdated_moves._get_records_action(name=self.env._("Check Invoice(s)")) if is_batch else None,
            }
        return alerts
