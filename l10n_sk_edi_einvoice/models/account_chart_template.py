from odoo import models

from odoo.addons.account.models.chart_template import template

# Legal wording required on the invoice, kept in Slovak whatever the user language is:
# - Section 74(1)(k) of the VAT Act: "prenesenie danovej povinnosti" (reverse charge)
# - Section 74(1)(h) of the VAT Act: reference to the exempting provision
SK_REVERSE_CHARGE_REASON = "Prenesenie daňovej povinnosti"
SK_EXEMPT_REASON = "Dodanie je oslobodené od dane"

# VAT category (BT-118/BT-151) and exemption reason (BT-120/BT-121) of the Slovak sales taxes
# whose category cannot be deduced from the rate alone.
SK_EDI_TAX_VALUES = {
    # Domestic reverse charge, Section 69(12) of the VAT Act.
    'vy_rc': {
        'ubl_cii_tax_category_code': 'AE',
        'ubl_cii_tax_exemption_reason_code': 'VATEX-EU-AE',
        'ubl_cii_tax_exemption_reason': SK_REVERSE_CHARGE_REASON,
    },
    # Services supplied to a taxable person of another member state: the customer is liable for the
    # tax, so the invoice states the reverse charge wording (Section 74(1)(k) of the VAT Act).
    'vy_eu_s': {
        'ubl_cii_tax_category_code': 'AE',
        'ubl_cii_tax_exemption_reason_code': 'VATEX-EU-AE',
        'ubl_cii_tax_exemption_reason': SK_REVERSE_CHARGE_REASON,
    },
    # Exempt intra-community supply of goods, Section 43 of the VAT Act.
    'vy_eu_m': {
        'ubl_cii_tax_category_code': 'K',
        'ubl_cii_tax_exemption_reason_code': 'VATEX-EU-IC',
        'ubl_cii_tax_exemption_reason': "Dodanie je oslobodené od dane podľa § 43 zákona č. 222/2004 Z. z.",
    },
    # Triangular trade, Section 45(3) of the VAT Act: the first customer invoices the second one
    # without tax and with the reverse charge wording.
    'vy_eu_t': {
        'ubl_cii_tax_category_code': 'AE',
        'ubl_cii_tax_exemption_reason_code': 'VATEX-EU-AE',
        'ubl_cii_tax_exemption_reason': SK_REVERSE_CHARGE_REASON,
    },
    # Exempt export of goods, Section 47 of the VAT Act.
    'vy_mimo_eu': {
        'ubl_cii_tax_category_code': 'G',
        'ubl_cii_tax_exemption_reason_code': 'VATEX-EU-G',
        'ubl_cii_tax_exemption_reason': "Dodanie je oslobodené od dane podľa § 47 zákona č. 222/2004 Z. z.",
    },
}


class AccountChartTemplate(models.AbstractModel):
    _inherit = 'account.chart.template'

    @template('sk', 'account.tax')
    def _get_sk_edi_einvoice_account_tax(self):
        # The data is loaded on new charts and, when the module is installed or updated, on the
        # existing ones: a tax that already carries a VAT category was configured on purpose and is
        # left untouched.
        tax_values = {}
        for xmlid, values in SK_EDI_TAX_VALUES.items():
            tax = self.ref(xmlid, raise_if_not_found=False)
            if not tax or not tax.ubl_cii_tax_category_code:
                tax_values[xmlid] = dict(values)
        return tax_values
