from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.l10n_sk_edi_einvoice.tests.common import TestSkEinvoiceCommon


@tagged('post_install_l10n', 'post_install', '-at_install')
class TestSkPartner(TestSkEinvoiceCommon):

    def test_routing_identifier_is_tin(self):
        """ Slovak entities are addressed in Peppol by their DIC, even when they have a VAT number. """
        self.assertRecordValues(self.partner_sk + self.partner_sk_non_vat, [
            {'routing_scheme': '0245', 'routing_endpoint': '2022749619'},
            {'routing_scheme': '0245', 'routing_endpoint': '1020304050'},
        ])

    def test_tin_deduced_from_vat_number(self):
        partner = self.env['res.partner'].create({
            'name': "Len IČ DPH s.r.o.",
            'country_id': self.env.ref('base.sk').id,
            'vat': 'SK2021869234',
        })
        self.assertRecordValues(partner, [{'routing_scheme': '0245', 'routing_endpoint': '2021869234'}])

    def test_tin_is_normalized(self):
        self.partner_sk_non_vat._set_additional_identifier('SK_TIN', '10 2030 4050')
        self.assertEqual(self.partner_sk_non_vat._get_additional_identifier('SK_TIN'), '1020304050')

    def test_invalid_tin_is_rejected(self):
        for invalid_tin in ('12345', 'SK2021869234', '20218692345', 'ABCDEFGHIJ'):
            with self.subTest(tin=invalid_tin), self.assertRaises(ValidationError):
                self.partner_sk_non_vat._set_additional_identifier('SK_TIN', invalid_tin)

    def test_invalid_routing_endpoint_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.partner_sk.write({'routing_scheme': '0245', 'routing_endpoint': '12345'})

    def test_suggested_format_is_bis3(self):
        self.assertEqual(self.partner_sk._get_suggested_ubl_cii_edi_format(), 'ubl_bis3')
        self.assertEqual(self.partner_sk_non_vat._get_suggested_ubl_cii_edi_format(), 'ubl_bis3')

    def test_default_invoice_format(self):
        """ Slovak taxable persons are invoiced with an e-invoice by default, consumers are not. """
        consumer = self.env['res.partner'].create({
            'name': "Jozef Spotrebiteľ",
            'country_id': self.env.ref('base.sk').id,
        })
        sole_trader = self.env['res.partner'].create({
            'name': "Peter Živnostník",
            'country_id': self.env.ref('base.sk').id,
            'additional_identifiers': {'SK_EN': '44556677'},
        })
        self.assertEqual(self.partner_sk.invoice_edi_format, 'ubl_bis3')
        self.assertEqual(self.partner_sk_non_vat.invoice_edi_format, 'ubl_bis3')
        self.assertEqual(sole_trader.invoice_edi_format, 'ubl_bis3')
        self.assertFalse(consumer.invoice_edi_format)
        self.assertFalse(self.partner_be.invoice_edi_format)

    def test_default_invoice_format_can_be_disabled(self):
        self.partner_sk.invoice_edi_format = False
        self.assertFalse(self.partner_sk.invoice_edi_format)

    def test_tax_categories_of_the_chart(self):
        """ The taxes of the Slovak chart carry the VAT category that cannot be deduced from their rate. """
        ChartTemplate = self.env['account.chart.template'].with_company(self.company)
        self.assertRecordValues(self.tax_reverse_charge, [{
            'ubl_cii_tax_category_code': 'AE',
            'ubl_cii_tax_exemption_reason_code': 'VATEX-EU-AE',
            'ubl_cii_tax_exemption_reason': "Prenesenie daňovej povinnosti",
        }])
        self.assertEqual(ChartTemplate.ref('vy_eu_m').ubl_cii_tax_category_code, 'K')
        self.assertEqual(ChartTemplate.ref('vy_eu_s').ubl_cii_tax_category_code, 'AE')
        self.assertEqual(ChartTemplate.ref('vy_eu_t').ubl_cii_tax_category_code, 'AE')
        self.assertEqual(ChartTemplate.ref('vy_mimo_eu').ubl_cii_tax_category_code, 'G')

    def test_install_keeps_configured_taxes(self):
        """ Loading the data on an existing chart fills the empty taxes only. """
        ChartTemplate = self.env['account.chart.template'].with_company(self.company)
        export_tax = ChartTemplate.ref('vy_mimo_eu')
        self.tax_reverse_charge.write({
            'ubl_cii_tax_category_code': False,
            'ubl_cii_tax_exemption_reason_code': False,
            'ubl_cii_tax_exemption_reason': False,
        })
        export_tax.write({'ubl_cii_tax_category_code': 'E', 'ubl_cii_tax_exemption_reason': "Custom reason"})

        tax_values = ChartTemplate._get_sk_edi_einvoice_account_tax()
        self.assertIn('vy_rc', tax_values)
        self.assertNotIn('vy_mimo_eu', tax_values)
        # The framework applies the data with a forced update when the module is installed.
        ChartTemplate._load_data({'account.tax': tax_values})

        self.assertEqual(self.tax_reverse_charge.ubl_cii_tax_category_code, 'AE')
        self.assertRecordValues(export_tax, [{
            'ubl_cii_tax_category_code': 'E',
            'ubl_cii_tax_exemption_reason': "Custom reason",
        }])
