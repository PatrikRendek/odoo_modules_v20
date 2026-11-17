from odoo.tests import tagged

from odoo.addons.l10n_sk_edi_einvoice.tests.common import TestSkEinvoiceCommon

SUPPLIER = './cac:AccountingSupplierParty/cac:Party'
CUSTOMER = './cac:AccountingCustomerParty/cac:Party'
TAX_CATEGORY = './cac:TaxTotal/cac:TaxSubtotal/cac:TaxCategory'


@tagged('post_install_l10n', 'post_install', '-at_install')
class TestSkEinvoiceExport(TestSkEinvoiceCommon):

    def test_domestic_invoice(self):
        tree, errors = self._export_sk_invoice(self._create_sk_invoice())

        self.assertFalse(errors)
        self.assertEqual(self._find_values(tree, './cbc:InvoiceTypeCode'), ['380'])
        self.assertEqual(self._find_values(tree, './cbc:IssueDate'), ['2027-01-20'])
        # Section 74(1)(d): the date of the supply differs from the issue date.
        self.assertEqual(self._find_values(tree, './cbc:TaxPointDate'), ['2027-01-15'])
        for party_xpath, tin, vat_number, company_number in (
            (SUPPLIER, '2020317068', 'SK2020317068', '35697270'),
            (CUSTOMER, '2022749619', 'SK2022749619', '31322832'),
        ):
            with self.subTest(party=party_xpath):
                self.assertEqual(self._find_values(tree, f'{party_xpath}/cbc:EndpointID'), [tin])
                self.assertEqual(self._find_values(tree, f'{party_xpath}/cbc:EndpointID/@schemeID'), ['0245'])
                self.assertEqual(
                    self._find_values(tree, f'{party_xpath}/cac:PartyTaxScheme/cbc:CompanyID'),
                    [vat_number],
                )
                self.assertEqual(
                    self._find_values(tree, f'{party_xpath}/cac:PartyLegalEntity/cbc:CompanyID'),
                    [company_number],
                )
                self.assertEqual(
                    self._find_values(tree, f'{party_xpath}/cac:PartyLegalEntity/cbc:CompanyID/@schemeID'),
                    ['0158'],
                )
        self.assertEqual(
            self._find_values(tree, './cac:PaymentMeans/cac:PayeeFinancialAccount/cbc:ID'),
            ['SK3112000000198742637541'],
        )
        self.assertEqual(self._find_values(tree, f'{TAX_CATEGORY}/cbc:ID'), ['S'])
        self.assertEqual(self._find_values(tree, './cac:TaxTotal/cbc:TaxAmount'), ['46.00'])
        self.assertEqual(self._find_values(tree, './cac:LegalMonetaryTotal/cbc:PayableAmount'), ['246.00'])

    def test_no_tax_point_date_when_same_as_issue_date(self):
        invoice = self._create_sk_invoice(taxable_supply_date='2027-01-20')
        tree, errors = self._export_sk_invoice(invoice)

        self.assertFalse(errors)
        self.assertFalse(self._find_values(tree, './cbc:TaxPointDate'))

    def test_customer_not_registered_for_vat(self):
        """ The DIC is never exported as a VAT identifier. """
        tree, errors = self._export_sk_invoice(self._create_sk_invoice(partner=self.partner_sk_non_vat))

        self.assertFalse(errors)
        self.assertEqual(self._find_values(tree, f'{CUSTOMER}/cbc:EndpointID'), ['1020304050'])
        self.assertFalse(self._find_values(tree, f'{CUSTOMER}/cac:PartyTaxScheme'))
        self.assertEqual(self._find_values(tree, f'{CUSTOMER}/cac:PartyLegalEntity/cbc:CompanyID'), ['41234567'])

    def test_customer_without_company_number(self):
        """ Without ICO, the legal registration identifier falls back on the DIC. """
        self.partner_sk.additional_identifiers = {'SK_TIN': '2022749619'}
        tree, errors = self._export_sk_invoice(self._create_sk_invoice())

        self.assertFalse(errors)
        self.assertEqual(self._find_values(tree, f'{CUSTOMER}/cac:PartyLegalEntity/cbc:CompanyID'), ['2022749619'])
        self.assertEqual(
            self._find_values(tree, f'{CUSTOMER}/cac:PartyLegalEntity/cbc:CompanyID/@schemeID'),
            ['0245'],
        )

    def test_domestic_reverse_charge(self):
        invoice = self._create_sk_invoice(taxes=self.tax_reverse_charge)
        tree, errors = self._export_sk_invoice(invoice)

        self.assertFalse(errors)
        self.assertEqual(self._find_values(tree, f'{TAX_CATEGORY}/cbc:ID'), ['AE'])
        self.assertEqual(self._find_values(tree, f'{TAX_CATEGORY}/cbc:TaxExemptionReasonCode'), ['VATEX-EU-AE'])
        self.assertEqual(
            self._find_values(tree, f'{TAX_CATEGORY}/cbc:TaxExemptionReason'),
            ["Prenesenie daňovej povinnosti"],
        )
        self.assertEqual(
            self._find_values(tree, './cac:InvoiceLine/cac:Item/cac:ClassifiedTaxCategory/cbc:ID'),
            ['AE'],
        )
        self.assertEqual(self._find_values(tree, './cac:TaxTotal/cbc:TaxAmount'), ['0.00'])

    def test_reverse_charge_wording_without_reason_on_tax(self):
        """ The legal wording does not depend on the configuration of the tax. """
        self.tax_reverse_charge.write({
            'ubl_cii_tax_exemption_reason_code': False,
            'ubl_cii_tax_exemption_reason': False,
        })
        tree, errors = self._export_sk_invoice(self._create_sk_invoice(taxes=self.tax_reverse_charge))

        self.assertFalse(errors)
        self.assertEqual(self._find_values(tree, f'{TAX_CATEGORY}/cbc:TaxExemptionReasonCode'), ['VATEX-EU-AE'])
        self.assertEqual(
            self._find_values(tree, f'{TAX_CATEGORY}/cbc:TaxExemptionReason'),
            ["Prenesenie daňovej povinnosti"],
        )

    def test_reverse_charge_requires_customer_vat_number(self):
        invoice = self._create_sk_invoice(partner=self.partner_sk_non_vat, taxes=self.tax_reverse_charge)
        _tree, errors = self._export_sk_invoice(invoice)

        self.assertTrue(any("reverse charge" in error for error in errors), errors)

    def test_exempt_supply_wording(self):
        tree, errors = self._export_sk_invoice(self._create_sk_invoice(taxes=self.tax_0))

        self.assertFalse(errors)
        self.assertEqual(self._find_values(tree, f'{TAX_CATEGORY}/cbc:ID'), ['E'])
        self.assertEqual(
            self._find_values(tree, f'{TAX_CATEGORY}/cbc:TaxExemptionReason'),
            ["Dodanie je oslobodené od dane"],
        )

    def test_credit_note_refers_to_invoice(self):
        invoice = self._create_sk_invoice()
        credit_note = invoice._reverse_moves([{'invoice_date': '2027-01-25'}])
        credit_note.action_post()
        tree, errors = self._export_sk_invoice(credit_note)

        self.assertFalse(errors)
        self.assertEqual(self._find_values(tree, './cbc:CreditNoteTypeCode'), ['381'])
        self.assertEqual(
            self._find_values(tree, './cac:BillingReference/cac:InvoiceDocumentReference/cbc:ID'),
            [invoice.name],
        )

    def test_credit_note_without_invoice(self):
        _tree, errors = self._export_sk_invoice(self._create_sk_invoice(move_type='out_refund'))

        self.assertTrue(any("does not refer to the invoice" in error for error in errors), errors)

    def test_missing_address(self):
        self.partner_sk.write({'street': False, 'zip': False})
        _tree, errors = self._export_sk_invoice(self._create_sk_invoice())

        self.assertTrue(any("address of Odberateľ a.s. is incomplete" in error for error in errors), errors)

    def test_missing_tin(self):
        partner_without_tin = self.env['res.partner'].create({
            **self._create_partner_default_values(),
            'name': "Bez DIČ s.r.o.",
            'is_company': True,
            'street': "Nová 3",
            'city': "Žilina",
            'zip': "01001",
            'country_id': self.env.ref('base.sk').id,
            'additional_identifiers': {'SK_EN': '31322832'},
        })
        _tree, errors = self._export_sk_invoice(self._create_sk_invoice(partner=partner_without_tin))

        self.assertTrue(any("0245:DIC" in error for error in errors), errors)

    def test_invoice_without_bank_account(self):
        """ The payment instructions are optional: an invoice paid in cash or by card has no account. """
        tree, errors = self._export_sk_invoice(self._create_sk_invoice(partner_bank_id=False))

        self.assertFalse(errors)
        self.assertFalse(self._find_values(tree, './cac:PaymentMeans/cac:PayeeFinancialAccount'))

    def test_supplier_without_vat_number(self):
        self.company.partner_id.vat = False
        _tree, errors = self._export_sk_invoice(self._create_sk_invoice())

        self.assertTrue(any("has no VAT number" in error for error in errors), errors)

    def test_foreign_customer_is_not_checked(self):
        """ The Slovak identification rules only apply to Slovak parties. """
        tree, errors = self._export_sk_invoice(self._create_sk_invoice(partner=self.partner_be))

        self.assertFalse(any("DIC" in error for error in errors), errors)
        self.assertEqual(
            self._find_values(tree, f'{CUSTOMER}/cac:PartyTaxScheme/cbc:CompanyID'),
            ['BE0477472701'],
        )

    def test_credit_note_created_on_its_own_refers_to_the_reconciled_invoice(self):
        """ A credit note that was not created from the invoice refers to the invoice it is reconciled with. """
        invoice = self._create_sk_invoice()
        credit_note = self._create_sk_invoice(move_type='out_refund', invoice_date='2027-01-25', taxable_supply_date='2027-01-25')
        _tree, errors = self._export_sk_invoice(credit_note)
        self.assertTrue(any("does not refer to the invoice" in error for error in errors))

        (invoice + credit_note).line_ids.filtered(lambda line: line.account_id.account_type == 'asset_receivable').reconcile()
        tree, errors = self._export_sk_invoice(credit_note)
        self.assertFalse(errors)
        self.assertEqual(
            self._find_values(tree, './cac:BillingReference/cac:InvoiceDocumentReference/cbc:ID'),
            [invoice.name],
        )

    def test_reason_text_of_the_tax_without_a_code(self):
        """ A reason text set on a tax that has no reason code is still stated on the invoice. """
        self.tax_reverse_charge.write({
            'ubl_cii_tax_exemption_reason_code': False,
            'ubl_cii_tax_exemption_reason': "Prenesenie daňovej povinnosti podľa § 69 ods. 12 písm. f)",
        })
        tree, errors = self._export_sk_invoice(self._create_sk_invoice(taxes=self.tax_reverse_charge))

        self.assertFalse(errors)
        self.assertEqual(
            self._find_values(tree, './cac:TaxTotal/cac:TaxSubtotal/cac:TaxCategory/cbc:TaxExemptionReason'),
            ["Prenesenie daňovej povinnosti podľa § 69 ods. 12 písm. f)"],
        )
        self.assertEqual(
            self._find_values(tree, './cac:TaxTotal/cac:TaxSubtotal/cac:TaxCategory/cbc:TaxExemptionReasonCode'),
            ['VATEX-EU-AE'],
        )

