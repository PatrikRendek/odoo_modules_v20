from odoo import fields
from odoo.tests import tagged

from odoo.addons.l10n_sk_edi_einvoice.tests.common import TestSkEinvoiceCommon


@tagged('post_install_l10n', 'post_install', '-at_install')
class TestSkEinvoiceImport(TestSkEinvoiceCommon):

    def test_import_domestic_invoice(self):
        bill = self._import_sk_test_file('sk_invoice_domestic.xml')

        self.assertRecordValues(bill, [{
            'move_type': 'in_invoice',
            'ref': 'FV20270042',
            'invoice_date': fields.Date.from_string('2027-01-20'),
            'invoice_date_due': fields.Date.from_string('2027-02-03'),
            'taxable_supply_date': fields.Date.from_string('2027-01-15'),
            'amount_untaxed': 200.0,
            'amount_tax': 46.0,
            'amount_total': 246.0,
        }])
        supplier = bill.partner_id
        self.assertRecordValues(supplier, [{
            'name': "Vzorový dodávateľ s.r.o.",
            'vat': 'SK2021869234',
            'routing_scheme': '0245',
            'routing_endpoint': '2021869234',
            'country_code': 'SK',
        }])
        self.assertEqual(supplier._get_additional_identifier('SK_TIN'), '2021869234')
        self.assertEqual(supplier._get_additional_identifier('SK_EN'), '36570460')
        self.assertRecordValues(bill.invoice_line_ids, [{
            'name': "Montážne práce",
            'quantity': 2.0,
            'price_unit': 100.0,
        }])
        self.assertEqual(bill.invoice_line_ids.tax_ids.amount, 23.0)

    def test_import_matches_existing_partner_by_tin(self):
        """ A supplier that is not registered for VAT is found back through its DIC. """
        self.partner_sk_non_vat.additional_identifiers = {'SK_EN': '36570460', 'SK_TIN': '2021869234'}
        bill = self._import_sk_test_file('sk_invoice_non_vat_supplier.xml')

        self.assertEqual(bill.partner_id, self.partner_sk_non_vat)
        self.assertRecordValues(bill, [{
            'amount_untaxed': 200.0,
            'amount_total': 200.0,
        }])

    def test_import_non_vat_supplier(self):
        """ The identifiers of a supplier without VAT number are not taken as a VAT number. """
        bill = self._import_sk_test_file('sk_invoice_non_vat_supplier.xml')

        supplier = bill.partner_id
        self.assertFalse(supplier.vat)
        self.assertEqual(supplier._get_additional_identifier('SK_TIN'), '2021869234')
        self.assertEqual(supplier._get_additional_identifier('SK_EN'), '36570460')
        # No tax point date in the file: the date of the taxable supply follows the issue date.
        self.assertEqual(bill.taxable_supply_date, fields.Date.from_string('2027-01-20'))

    def test_import_reverse_charge_invoice(self):
        bill = self._import_sk_test_file('sk_invoice_reverse_charge.xml')

        self.assertRecordValues(bill, [{
            'ref': 'FV20270042',
            'taxable_supply_date': fields.Date.from_string('2027-01-15'),
            'amount_untaxed': 200.0,
        }])
        self.assertEqual(bill.partner_id.vat, 'SK2021869234')

    def test_import_malformed_tax_point_date(self):
        """ A malformed tax point date is ignored instead of blocking the import. """
        bill = self._import_sk_test_file('sk_invoice_domestic.xml', replacements={
            '<cbc:TaxPointDate>2027-01-15</cbc:TaxPointDate>': '<cbc:TaxPointDate>15.1.2027</cbc:TaxPointDate>',
        })

        self.assertRecordValues(bill, [{
            'invoice_date': fields.Date.from_string('2027-01-20'),
            'taxable_supply_date': fields.Date.from_string('2027-01-20'),
            'amount_total': 246.0,
        }])

    def test_import_malformed_tin_is_dropped(self):
        """ A malformed DIC of the file does not block the import, the supplier is created without it. """
        bill = self._import_sk_test_file('sk_invoice_non_vat_supplier.xml', replacements={
            '<cbc:EndpointID schemeID="0245">2021869234</cbc:EndpointID>': '<cbc:EndpointID schemeID="0245">12345</cbc:EndpointID>',
        })

        self.assertEqual(bill.amount_untaxed, 200.0)
        supplier = bill.partner_id
        self.assertEqual(supplier.name, "Vzorový dodávateľ s.r.o.")
        self.assertFalse(supplier.routing_endpoint)
        self.assertFalse(supplier._get_additional_identifier('SK_TIN'))
        self.assertEqual(supplier._get_additional_identifier('SK_EN'), '36570460')

    def test_import_blank_tax_point_date(self):
        """ A tax point date made of blanks only is ignored: the issue date is kept. """
        bill = self._import_sk_test_file('sk_invoice_domestic.xml', replacements={
            '<cbc:TaxPointDate>2027-01-15</cbc:TaxPointDate>': '<cbc:TaxPointDate> </cbc:TaxPointDate>',
        })

        self.assertTrue(bill.taxable_supply_date)
        self.assertEqual(bill.taxable_supply_date, bill.invoice_date)

