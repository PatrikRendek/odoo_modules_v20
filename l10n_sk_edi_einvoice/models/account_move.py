from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _l10n_sk_edi_get_currency_rate_date(self):
        """ Give the date of the exchange rate a Slovak company converts the document with.

        Section 26(1) of the VAT Act and Section 24(2) of the Accounting Act: the amounts are converted
        with the reference rate set and published by the ECB (or the NBS) on the day preceding the day
        the tax liability arises. A correction of the tax base keeps the rate of the corrected document.

        The rate lookup of 'res.currency' already takes the last rate published before the given date,
        so the date to give is the tax point itself, not the day before it.

        :return: The date to look the rate up at, or None when the Slovak rule does not apply.
        """
        self.ensure_one()
        if self.country_code != 'SK':
            return None
        original_invoice = self.reversed_entry_id
        if (
            self.move_type in ('out_refund', 'in_refund')
            and original_invoice
            and original_invoice.is_invoice(include_receipts=True)
        ):
            return original_invoice._get_invoice_currency_rate_date()
        return self.taxable_supply_date or self.invoice_date or None

    def _get_invoice_currency_rate_date(self):
        # EXTENDS account
        self.ensure_one()
        return self._l10n_sk_edi_get_currency_rate_date() or super()._get_invoice_currency_rate_date()

    def _get_default_currency_rate_date(self):
        # EXTENDS account
        self.ensure_one()
        return self._l10n_sk_edi_get_currency_rate_date() or super()._get_default_currency_rate_date()
