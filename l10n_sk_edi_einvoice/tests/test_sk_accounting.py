from freezegun import freeze_time

from odoo.tests import tagged

from odoo.addons.l10n_sk_edi_einvoice.tests.common import TestSkEinvoiceCommon


@tagged('post_install_l10n', 'post_install', '-at_install')
class TestSkAccounting(TestSkEinvoiceCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.currency_usd = cls.env.ref('base.USD')
        cls.currency_usd.active = True
        cls.env['res.currency.rate'].create([
            {
                'name': rate_date,
                'rate': rate,
                'currency_id': cls.currency_usd.id,
                'company_id': cls.company.id,
            }
            for rate_date, rate in (
                ('2027-01-13', 1.10),
                ('2027-01-14', 1.20),
                ('2027-01-15', 1.30),
                ('2027-01-20', 1.40),
            )
        ])

    def _get_send_alerts(self, invoice):
        wizard = self.env['account.move.send.wizard'].with_context(
            active_model='account.move',
            active_ids=invoice.ids,
        ).create({})
        return wizard.alerts or {}

    # -------------------------------------------------------------------------
    # EXCHANGE RATE
    # -------------------------------------------------------------------------

    def test_rate_of_the_day_before_the_tax_point(self):
        """ Supply on 15 January, invoice on 20 January: the rate published on 14 January applies. """
        invoice = self._create_sk_invoice(currency_id=self.currency_usd.id)

        self.assertAlmostEqual(invoice.invoice_currency_rate, 1.20)
        # 2 x 100 USD + 23 % = 246 USD, converted at 1.20 USD for 1 EUR.
        self.assertAlmostEqual(invoice.amount_total_signed, 205.0)

    def test_rate_without_separate_tax_point(self):
        """ Without a separate date of supply, the last rate published before the invoice date applies. """
        invoice = self._create_sk_invoice(currency_id=self.currency_usd.id, taxable_supply_date='2027-01-20')

        self.assertAlmostEqual(invoice.invoice_currency_rate, 1.30)

    def test_credit_note_keeps_the_rate_of_the_invoice(self):
        invoice = self._create_sk_invoice(currency_id=self.currency_usd.id)
        credit_note = invoice._reverse_moves([{'invoice_date': '2027-01-25'}])

        self.assertAlmostEqual(credit_note.invoice_currency_rate, 1.20)

    # -------------------------------------------------------------------------
    # CONTACT DATA
    # -------------------------------------------------------------------------

    def test_no_alert_for_complete_contacts(self):
        alerts = self._get_send_alerts(self._create_sk_invoice())

        self.assertNotIn('l10n_sk_edi_einvoice_partner_data', alerts)

    def test_alert_for_incomplete_contacts(self):
        """ The Send wizard points out the contacts the generation of the file would refuse. """
        invoice = self._create_sk_invoice()
        self.partner_sk.street = False
        self.company.partner_id.zip = False
        alerts = self._get_send_alerts(invoice)

        alert = alerts['l10n_sk_edi_einvoice_partner_data']
        self.assertEqual(alert['level'], 'warning')
        self.assertIn(self.partner_sk.display_name, alert['message'])
        self.assertIn(self.company.partner_id.display_name, alert['message'])
        self.assertEqual(alert['action']['domain'][0][2], (self.company.partner_id + self.partner_sk).ids)

    def test_alert_for_invoice_address_without_zip(self):
        """ The address checked is the one of the contact the invoice is addressed to. """
        invoice_address = self.env['res.partner'].create({
            'name': "Fakturačná adresa",
            'type': 'invoice',
            'parent_id': self.partner_sk.id,
            'street': "Bočná 3",
            'city': "Prešov",
            'country_id': self.env.ref('base.sk').id,
        })
        alerts = self._get_send_alerts(self._create_sk_invoice(partner=invoice_address))

        alert = alerts['l10n_sk_edi_einvoice_partner_data']
        self.assertIn(invoice_address.display_name, alert['message'])
        self.assertEqual(alert['action']['res_id'], invoice_address.id)

    def test_alert_for_customer_without_tin(self):
        partner = self.env['res.partner'].create({
            'name': "Bez DIC s.r.o.",
            'is_company': True,
            'street': "Dlhá 5",
            'city': "Košice",
            'zip': "04001",
            'country_id': self.env.ref('base.sk').id,
            'additional_identifiers': {'SK_EN': '36000001'},
        })
        alerts = self._get_send_alerts(self._create_sk_invoice(partner=partner))

        self.assertIn(partner.display_name, alerts['l10n_sk_edi_einvoice_partner_data']['message'])
        self.assertNotIn('account_edi_ubl_cii_configure_partner', alerts)

    def test_no_contact_alert_for_a_foreign_customer(self):
        self.partner_be.street = False
        alerts = self._get_send_alerts(self._create_sk_invoice(partner=self.partner_be))

        self.assertNotIn('l10n_sk_edi_einvoice_partner_data', alerts)

    # -------------------------------------------------------------------------
    # ISSUE DATE
    # -------------------------------------------------------------------------

    def test_no_alert_when_sent_on_the_invoice_date(self):
        invoice = self._create_sk_invoice()
        with freeze_time('2027-01-20'):
            alerts = self._get_send_alerts(invoice)

        self.assertNotIn('l10n_sk_edi_einvoice_issue_date', alerts)

    def test_alert_when_sent_on_another_day(self):
        invoice = self._create_sk_invoice()
        with freeze_time('2027-01-22'):
            alerts = self._get_send_alerts(invoice)

        self.assertEqual(alerts['l10n_sk_edi_einvoice_issue_date']['level'], 'warning')

    def test_no_alert_for_a_foreign_customer(self):
        invoice = self._create_sk_invoice(partner=self.partner_be)
        with freeze_time('2027-01-22'):
            alerts = self._get_send_alerts(invoice)

        self.assertNotIn('l10n_sk_edi_einvoice_issue_date', alerts)

    def test_no_alert_for_an_invoice_already_sent(self):
        invoice = self._create_sk_invoice()
        invoice.is_move_sent = True
        with freeze_time('2027-01-22'):
            alerts = self._get_send_alerts(invoice)

        self.assertNotIn('l10n_sk_edi_einvoice_issue_date', alerts)
