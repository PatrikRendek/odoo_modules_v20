from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.l10n_sk_edi_einvoice.tests.common import TestSkEinvoiceCommon


@tagged('post_install_l10n', 'post_install', '-at_install')
class TestSkPeppol(TestSkEinvoiceCommon):
    """ Sending through the Peppol connection of Odoo, in its demo mode (no external call).

    The module does not depend on 'account_peppol': the tests are skipped when it is not installed.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not cls.has_peppol:
            return
        cls.company.write({'email': 'info@mojafirma.example', 'phone': '+421 2 5555 5555'})
        cls.env['peppol.registration'].create({
            'contact_email': 'info@mojafirma.example',
            'phone_number': '+421255555555',
        }).button_register_peppol_participant()
        for partner in cls.partner_sk + cls.partner_sk_non_vat:
            partner.button_account_peppol_check_partner_endpoint()

    def setUp(self):
        super().setUp()
        if not self.has_peppol:
            self.skipTest("account_peppol is not installed")

    def _create_send_wizard(self, invoice):
        return self.env['account.move.send.wizard'].with_context(
            active_model='account.move',
            active_ids=invoice.ids,
        ).create({})

    def test_company_registers_with_its_tin(self):
        """ A Slovak company joins the Peppol network under the 0245:DIC identifier. """
        self.assertEqual(self.company.routing_identifier, '0245:2020317068')
        self.assertTrue(self.company.peppol_can_send)

    def test_peppol_is_preselected_for_slovak_customer(self):
        wizard = self._create_send_wizard(self._create_sk_invoice())

        self.assertIn('peppol', wizard.sending_methods)
        self.assertEqual(wizard.invoice_edi_format, 'ubl_bis3')

    def test_peppol_is_not_preselected_for_consumer(self):
        consumer = self.env['res.partner'].create({
            **self._create_partner_default_values(),
            'name': "Jozef Spotrebiteľ",
            'street': "Dolná 2",
            'city': "Prešov",
            'zip': "08001",
            'country_id': self.env.ref('base.sk').id,
        })
        wizard = self._create_send_wizard(self._create_sk_invoice(partner=consumer))

        self.assertNotIn('peppol', wizard.sending_methods or [])

    def test_send_through_peppol(self):
        invoice = self._create_sk_invoice()
        wizard = self._create_send_wizard(invoice)
        wizard.sending_methods = ['peppol']
        wizard.action_send_and_print()

        self.assertTrue(invoice.ubl_cii_xml_id)
        self.assertEqual(invoice.peppol_move_state, 'processing')
        self.env['account_edi_proxy_client.user']._cron_peppol_get_message_status()
        self.assertEqual(invoice.peppol_move_state, 'done')

    def test_slovak_checks_block_peppol_sending(self):
        self.partner_sk.write({'street': False, 'zip': False})
        invoice = self._create_sk_invoice()
        wizard = self._create_send_wizard(invoice)
        wizard.sending_methods = ['peppol']

        with self.assertRaisesRegex(UserError, "address of Odberateľ a.s. is incomplete"):
            wizard.action_send_and_print()
        self.assertFalse(invoice.ubl_cii_xml_id)
