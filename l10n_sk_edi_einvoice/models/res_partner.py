import re

from odoo import api, models

SK_TIN_SEPARATORS_RE = re.compile(r'[\s./-]')
SK_TIN_RE = re.compile(r'\d{10}')


def sk_tin_validate(value):
    """ Normalize and validate a Slovak tax identification number (DIC).

    The DIC is the Peppol participant identifier of every Slovak entity (scheme 0245) and is made of
    exactly ten digits. The VAT number (IC DPH) is the same number prefixed with 'SK' and is not
    accepted here on purpose: both identifiers are exchanged in different fields of the e-invoice.

    :param value:   The identifier as typed by the user.
    :return:        The identifier without separators.
    :raise ValueError: if the identifier is not made of ten digits.
    """
    compact_value = SK_TIN_SEPARATORS_RE.sub('', value or '')
    if not SK_TIN_RE.fullmatch(compact_value):
        raise ValueError("The Slovak tax identification number (DIC) is made of 10 digits.")
    return compact_value


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _get_all_additional_identifiers_metadata(self):
        # EXTENDS 'base': validate the DIC, the routing identifier of the Slovak e-invoice.
        metadata = super()._get_all_additional_identifiers_metadata()
        if 'SK_TIN' in metadata:
            metadata['SK_TIN'] = {
                **metadata['SK_TIN'],
                'placeholder': '2020317068',
                'validation_function': sk_tin_validate,
            }
        return metadata

    @api.depends('vat', 'additional_identifiers', 'is_company')
    def _compute_invoice_edi_format(self):
        # EXTENDS 'account': the suggested format of a Slovak contact follows its identifiers.
        super()._compute_invoice_edi_format()

    def _get_suggested_invoice_edi_format(self):
        # EXTENDS 'account': a Slovak company invoices the Slovak taxable persons with an e-invoice.
        # An individual without any business identifier is a consumer, who keeps receiving the invoice
        # as before.
        self.ensure_one()
        commercial_partner = self.commercial_partner_id
        if (
            commercial_partner.country_code == 'SK'
            and self.env.company.account_fiscal_country_id.code == 'SK'
            and (
                commercial_partner.is_company
                or {'SK_EN', 'SK_TIN', 'SK_VAT'} & commercial_partner._get_all_identifiers(enrich=True).keys()
            )
        ):
            return 'ubl_bis3'
        return super()._get_suggested_invoice_edi_format()

    @api.model
    def _get_ubl_cii_formats_info(self):
        # EXTENDS 'account_edi_ubl_cii': Peppol BIS Billing 3.0 is the format of the Slovak e-invoice.
        formats_info = super()._get_ubl_cii_formats_info()
        bis3_info = formats_info.get('ubl_bis3')
        if (
            bis3_info
            and 'SK' not in bis3_info['countries']
            and self.env.company.account_fiscal_country_id.code == 'SK'
        ):
            bis3_info['countries'] = [*bis3_info['countries'], 'SK']
        return formats_info
