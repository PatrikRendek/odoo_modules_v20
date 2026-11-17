from lxml import etree

from odoo import Command
from odoo.tools import file_open

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.addons.account_edi_ubl_cii.tests.common import TestUblCiiCommon

UBL_NAMESPACES = {
    'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
    'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
}


class TestSkEinvoiceCommon(TestUblCiiCommon):

    @classmethod
    @AccountTestInvoicingCommon.setup_country('sk')
    def setUpClass(cls):
        super().setUpClass()
        # With the Peppol connection of Odoo installed, creating a partner looks its identifier up on
        # the network: the demo mode keeps the tests offline and deterministic.
        cls.has_peppol = 'peppol_move_state' in cls.env['account.move']._fields
        if cls.has_peppol:
            cls.env['ir.config_parameter'].sudo().set_str('account_peppol.edi.mode', 'demo')
        cls.company = cls.company_data['company']
        cls.company.partner_id.write({
            'street': "Hlavná 1",
            'city': "Bratislava",
            'zip': "81101",
            'vat': 'SK2020317068',
            'additional_identifiers': {'SK_EN': '35697270', 'SK_TIN': '2020317068'},
        })
        cls.company_bank = cls.env['res.partner.bank'].create({
            'account_number': 'SK3112000000198742637541',
            'partner_id': cls.company.partner_id.id,
            'allow_out_payment': True,
        })
        cls.partner_sk = cls.env['res.partner'].create({
            **cls._create_partner_default_values(),
            'name': "Odberateľ a.s.",
            'is_company': True,
            'street': "Dlhá 5",
            'city': "Košice",
            'zip': "04001",
            'country_id': cls.env.ref('base.sk').id,
            'vat': 'SK2022749619',
            'additional_identifiers': {'SK_EN': '31322832', 'SK_TIN': '2022749619'},
        })
        # A taxable person that is not registered for VAT: it has a DIC but no IC DPH.
        cls.partner_sk_non_vat = cls.env['res.partner'].create({
            **cls._create_partner_default_values(),
            'name': "Živnostník Ján Vzorový",
            'is_company': True,
            'street': "Krátka 7",
            'city': "Nitra",
            'zip': "94901",
            'country_id': cls.env.ref('base.sk').id,
            'additional_identifiers': {'SK_EN': '41234567', 'SK_TIN': '1020304050'},
        })
        ChartTemplate = cls.env['account.chart.template'].with_company(cls.company)
        cls.tax_23 = ChartTemplate.ref('vy_tuz_23')
        cls.tax_0 = ChartTemplate.ref('vy_tuz_0')
        cls.tax_reverse_charge = ChartTemplate.ref('vy_rc')

    @classmethod
    def _create_sk_invoice(cls, move_type='out_invoice', partner=None, taxes=None, **invoice_values):
        """ Create and post a customer document of the Slovak company with one line of 2 x 100 EUR. """
        invoice = cls.env['account.move'].create({
            'move_type': move_type,
            'partner_id': (partner or cls.partner_sk).id,
            'invoice_date': '2027-01-20',
            'taxable_supply_date': '2027-01-15',
            'partner_bank_id': cls.company_bank.id,
            'invoice_line_ids': [Command.create({
                'name': "Montážne práce",
                'quantity': 2,
                'price_unit': 100.0,
                'tax_ids': [Command.set((taxes if taxes is not None else cls.tax_23).ids)],
            })],
            **invoice_values,
        })
        invoice.action_post()
        return invoice

    @classmethod
    def _export_sk_invoice(cls, invoice):
        """ Generate the Peppol BIS Billing 3.0 file of the invoice.

        :return: A tuple (parsed XML tree, set of error messages).
        """
        xml_content, errors = cls.env['account.edi.xml.ubl_bis3']._export_invoice(invoice)
        return etree.fromstring(xml_content), errors

    def _find_values(self, tree, xpath):
        """ Give the texts (or attribute values) matched by the xpath. """
        return [
            node if isinstance(node, str) else node.text
            for node in tree.xpath(xpath, namespaces=UBL_NAMESPACES)
        ]

    @classmethod
    def _import_sk_test_file(cls, filename, replacements=None):
        """ Import a sample e-invoice of 'tests/test_files' as a new vendor bill.

        :param replacements: An optional dictionary {text to find: replacement} applied on the file.
        """
        with file_open(f'l10n_sk_edi_einvoice/tests/test_files/{filename}', 'rb') as file:
            content = file.read()
        for old_text, new_text in (replacements or {}).items():
            content = content.replace(old_text.encode(), new_text.encode())
        attachment = cls.env['ir.attachment'].create({
            'mimetype': 'application/xml',
            'name': filename,
            'raw': content,
        })
        return cls._import_invoice_as_attachment_on(attachment=attachment)
