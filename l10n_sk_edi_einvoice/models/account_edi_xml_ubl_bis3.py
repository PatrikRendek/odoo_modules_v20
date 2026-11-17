import re

from odoo import fields, models

from .account_chart_template import SK_EXEMPT_REASON, SK_REVERSE_CHARGE_REASON
from .res_partner import SK_TIN_RE

# ISO 6523 ICD of the Slovak company identification number (ICO), issued by the Statistical Office.
SK_COMPANY_ID_SCHEME = '0158'
# Peppol EAS of the Slovak tax identification number (DIC), the participant identifier of Slovak entities.
SK_TIN_SCHEME = '0245'
SK_VAT_RE = re.compile(r'SK\d{10}')


class AccountEdiXmlUblBis3(models.AbstractModel):
    _inherit = 'account.edi.xml.ubl_bis3'

    # -------------------------------------------------------------------------
    # HELPERS
    # -------------------------------------------------------------------------

    def _l10n_sk_edi_is_sk_partner(self, partner):
        """ Indicate if the commercial entity of the partner is established in Slovakia. """
        return partner.commercial_partner_id.country_code == 'SK'

    def _l10n_sk_edi_is_sk_supplier(self, vals):
        """ Indicate if the Slovak rules apply to the document: they follow the country of the supplier.

        A document a foreign company issues on behalf of its Slovak vendor (self-billing) follows the
        rules of that company.
        """
        invoice = vals.get('invoice')
        if invoice and invoice.company_id.account_fiscal_country_id.code != 'SK':
            return False
        return self._l10n_sk_edi_is_sk_partner(vals['supplier'])

    def _l10n_sk_edi_get_vat_number(self, partner):
        """ Give the Slovak VAT number (IC DPH) of the partner, if any.

        The VAT number is not the tax identification number (DIC): an entity that is not registered for
        VAT has a DIC only, so the DIC must never be used as a fallback here.
        """
        vat_number = partner.commercial_partner_id._get_all_identifiers(enrich=True).get('SK_VAT')
        return re.sub(r'\s', '', vat_number).upper() if vat_number else None

    # -------------------------------------------------------------------------
    # EXPORT: NODES
    # -------------------------------------------------------------------------

    def _add_invoice_header_nodes(self, document_node, vals):
        # EXTENDS account.edi.xml.ubl_bis3
        super()._add_invoice_header_nodes(document_node, vals)

        # Section 74(1)(d) of the VAT Act: the date of the supply (or of the received payment) is stated
        # when it differs from the issue date. It is carried by the tax point date (BT-7).
        invoice = vals.get('invoice')
        if (
            invoice
            and self._l10n_sk_edi_is_sk_supplier(vals)
            and invoice.taxable_supply_date
            and invoice.taxable_supply_date != invoice.invoice_date
        ):
            document_node['cbc:TaxPointDate'] = {'_text': invoice.taxable_supply_date}

    def _ubl_add_billing_reference_nodes(self, vals):
        # EXTENDS account.edi.ubl_pint_eu
        super()._ubl_add_billing_reference_nodes(vals)

        # Section 71(2) of the VAT Act: a document amending an invoice refers to it unambiguously (BT-25).
        # It is taken from the invoice the credit note was created from or, for a credit note created
        # on its own, from the invoice it is reconciled with.
        if not self._is_document(vals, 'credit_note') or not self._l10n_sk_edi_is_sk_supplier(vals):
            return
        nodes = vals['document_node']['cac:BillingReference']
        credit_note = vals['invoice']
        original_invoice = credit_note.reversed_entry_id or credit_note.line_ids.matched_debit_ids.debit_move_id.move_id.filtered(
            lambda move: move.is_invoice(include_receipts=True),
        ).sorted('invoice_date')[:1]
        if not nodes and original_invoice.name and original_invoice.name != '/':
            nodes.append({
                'cac:InvoiceDocumentReference': {
                    'cbc:ID': {'_text': original_invoice.name},
                    'cbc:IssueDate': {'_text': original_invoice.invoice_date},
                },
            })

    def _ubl_add_party_tax_scheme_nodes(self, vals):
        # EXTENDS account.edi.ubl_pint
        super()._ubl_add_party_tax_scheme_nodes(vals)

        # The VAT identifier (BT-31/BT-48) of a Slovak party is its VAT number (IC DPH) with the 'SK'
        # prefix [BR-CO-09], never its tax identification number (DIC).
        partner = vals['party_vals']['partner']
        if not self._l10n_sk_edi_is_sk_partner(partner) or not self._need_party_tax_scheme_nodes(vals):
            return
        vat_number = self._l10n_sk_edi_get_vat_number(partner)
        vals['party_node']['cac:PartyTaxScheme'] = [{
            'cbc:CompanyID': {'_text': vat_number},
            'cac:TaxScheme': {
                'cbc:ID': {'_text': 'VAT'},
            },
        }] if vat_number else []

    def _ubl_add_party_legal_entity_nodes(self, vals):
        # EXTENDS account.edi.ubl_pint
        super()._ubl_add_party_legal_entity_nodes(vals)

        # The legal registration identifier (BT-30/BT-47) of a Slovak party is its company
        # identification number (ICO), when one was assigned.
        partner = vals['party_vals']['partner']
        if not self._l10n_sk_edi_is_sk_partner(partner):
            return
        company_number = partner.commercial_partner_id._get_additional_identifier('SK_EN')
        if not company_number:
            return
        for node in vals['party_node']['cac:PartyLegalEntity']:
            node['cbc:CompanyID'] = {
                '_text': company_number,
                'schemeID': SK_COMPANY_ID_SCHEME,
            }

    def _ubl_default_tax_category_grouping_key(self, base_line, tax_data, vals, currency):
        # EXTENDS account.edi.ubl_cen_en16931
        grouping_key = super()._ubl_default_tax_category_grouping_key(base_line, tax_data, vals, currency)
        if not grouping_key or not self._l10n_sk_edi_is_sk_supplier(vals):
            return grouping_key

        tax = tax_data['tax'] if tax_data else self.env['account.tax']
        tax_category_code = grouping_key.get('tax_category_code')
        if tax.ubl_cii_tax_exemption_reason:
            # A reason explicitly set on the tax always wins, also when the tax has no reason code.
            grouping_key['tax_exemption_reason'] = tax.ubl_cii_tax_exemption_reason
            if tax_category_code == 'AE' and not grouping_key.get('tax_exemption_reason_code'):
                grouping_key['tax_exemption_reason_code'] = 'VATEX-EU-AE'
        elif tax_category_code == 'AE':
            # Section 74(1)(k) of the VAT Act: the reverse charge is not an exemption, the invoice states
            # the wording "prenesenie danovej povinnosti".
            grouping_key['tax_exemption_reason'] = SK_REVERSE_CHARGE_REASON
            if not grouping_key.get('tax_exemption_reason_code'):
                grouping_key['tax_exemption_reason_code'] = 'VATEX-EU-AE'
        elif tax_category_code == 'E' and not grouping_key.get('tax_exemption_reason_code'):
            # Section 74(1)(h) of the VAT Act: without a reference to the exempting provision, the invoice
            # states the wording "dodanie je oslobodene od dane".
            grouping_key['tax_exemption_reason'] = SK_EXEMPT_REASON
        return grouping_key

    # -------------------------------------------------------------------------
    # EXPORT: CONSTRAINTS
    # -------------------------------------------------------------------------

    def _export_invoice_constraints(self, invoice, vals):
        # EXTENDS account.edi.xml.ubl_bis3
        constraints = super()._export_invoice_constraints(invoice, vals)
        if self._l10n_sk_edi_is_sk_supplier(vals):
            constraints.update(self._l10n_sk_edi_invoice_constraints(invoice, vals))
        return constraints

    def _l10n_sk_edi_party_constraints(self, party_node, partner, role):
        """ Check the data of a Slovak party of the document.

        :param party_node:  The 'cac:Party' node of the party.
        :param partner:     The partner the node was built from.
        :param role:        'supplier' or 'customer', used to build the keys of the constraints.
        :return:            A dictionary {constraint key: error message or None}.
        """
        constraints = {}
        partner_name = partner.display_name

        # Section 74(1)(a) and (b) of the VAT Act: name and address of the seat of both parties. The
        # norm makes the address lines optional, the Slovak transposition requires them.
        address_node = party_node['cac:PostalAddress']
        street_label = self.env._("street")
        city_label = self.env._("city")
        zip_label = self.env._("ZIP")
        address_labels = {'cbc:StreetName': street_label, 'cbc:CityName': city_label, 'cbc:PostalZone': zip_label}
        missing_address_labels = [
            label
            for node_name, label in address_labels.items()
            if not (address_node.get(node_name) or {}).get('_text')
        ]
        if missing_address_labels:
            constraints[f'l10n_sk_edi_{role}_address'] = self.env._(
                "The address of %(partner)s is incomplete (%(fields)s). The Slovak VAT Act requires the full"
                " address of the supplier and of the customer on the invoice.",
                partner=partner_name,
                fields=missing_address_labels,
            )

        # Slovak entities are addressed in the Peppol network by their DIC (scheme 0245) only.
        endpoint_node = party_node['cbc:EndpointID']
        endpoint = endpoint_node.get('_text') or ''
        if endpoint_node.get('schemeID') != SK_TIN_SCHEME or not SK_TIN_RE.fullmatch(endpoint):
            constraints[f'l10n_sk_edi_{role}_endpoint'] = self.env._(
                "%(partner)s must be identified by its tax identification number (DIC, 10 digits): Slovak"
                " entities send and receive e-invoices under the Peppol identifier 0245:DIC. Fill in the"
                " DIC on the contact and select it as the routing identifier.",
                partner=partner_name,
            )

        # [BR-CO-09] The VAT number (IC DPH) is the DIC prefixed with 'SK'.
        for tax_scheme_node in party_node['cac:PartyTaxScheme']:
            vat_number = tax_scheme_node['cbc:CompanyID']['_text'] or ''
            if tax_scheme_node['cac:TaxScheme']['cbc:ID']['_text'] == 'VAT' and not SK_VAT_RE.fullmatch(vat_number):
                constraints[f'l10n_sk_edi_{role}_vat_format'] = self.env._(
                    "The VAT number (IC DPH) '%(vat)s' of %(partner)s is not valid: it is made of the"
                    " prefix SK followed by 10 digits.",
                    vat=vat_number,
                    partner=partner_name,
                )
        return constraints

    def _l10n_sk_edi_invoice_constraints(self, invoice, vals):
        """ Check the Slovak requirements that the norm and the Peppol rules do not enforce.

        :return: A dictionary {constraint key: error message or None}.
        """
        document_node = vals['document_node']
        supplier = vals['supplier']
        customer = vals['customer']
        supplier_party_node = document_node['cac:AccountingSupplierParty']['cac:Party']
        customer_party_node = document_node['cac:AccountingCustomerParty']['cac:Party']
        is_sk_customer = self._l10n_sk_edi_is_sk_partner(customer)

        constraints = self._l10n_sk_edi_party_constraints(supplier_party_node, supplier, 'supplier')
        if is_sk_customer:
            constraints.update(self._l10n_sk_edi_party_constraints(customer_party_node, customer, 'customer'))

        line_nodes = [
            line_node
            for line_key in ('cac:InvoiceLine', 'cac:CreditNoteLine')
            for line_node in document_node.get(line_key) or []
        ]
        tax_category_codes = {
            (tax_category_node.get('cbc:ID') or {}).get('_text')
            for line_node in line_nodes
            for tax_category_node in (line_node.get('cac:Item') or {}).get('cac:ClassifiedTaxCategory') or []
        }

        # Section 74(1)(a) of the VAT Act: the VAT number of the supplier. Only a supply that is outside
        # the scope of VAT (category O) is invoiced without it [BR-O-02].
        if tax_category_codes - {'O', None} and not supplier_party_node['cac:PartyTaxScheme']:
            constraints['l10n_sk_edi_supplier_vat'] = self.env._(
                "%(partner)s has no VAT number (IC DPH). A supplier that is not registered for VAT can only"
                " invoice with taxes of the category 'O - Services outside scope of tax'.",
                partner=supplier.display_name,
            )

        # Section 69(12) of the VAT Act: the domestic reverse charge applies between two VAT payers, the
        # VAT number of the customer is then part of the invoice (Section 74(1)(b)).
        if 'AE' in tax_category_codes and is_sk_customer and not customer_party_node['cac:PartyTaxScheme']:
            constraints['l10n_sk_edi_customer_vat_reverse_charge'] = self.env._(
                "The invoice uses the reverse charge but %(partner)s has no VAT number (IC DPH). The"
                " domestic reverse charge only applies when the customer is registered for VAT.",
                partner=customer.display_name,
            )

        # Section 71(2) of the VAT Act: the amending document refers to the original invoice (BT-25).
        if self._is_document(vals, 'credit_note') and not any(
            ((billing_reference_node.get('cac:InvoiceDocumentReference') or {}).get('cbc:ID') or {}).get('_text')
            for billing_reference_node in document_node['cac:BillingReference']
        ):
            constraints['l10n_sk_edi_credit_note_reference'] = self.env._(
                "The credit note does not refer to the invoice it corrects. Create it with the Credit Note"
                " button of the original invoice, or reconcile it with that invoice before sending it."
            )

        return constraints

    # -------------------------------------------------------------------------
    # IMPORT
    # -------------------------------------------------------------------------

    def _import_ubl_invoice_add_customer_values(self, collected_values):
        # EXTENDS account.edi.ubl
        super()._import_ubl_invoice_add_customer_values(collected_values)

        # Keep the company identification number (ICO) of a Slovak party: it identifies the entities
        # that are not registered for VAT and is a legal mention of the business documents.
        customer_values = collected_values['customer_values']
        if customer_values.get('country_code') != 'SK':
            return
        party_tag = 'AccountingCustomerParty' if collected_values['odoo_document_type'] == 'sale' else 'AccountingSupplierParty'
        company_number = collected_values['tree'].findtext(
            f"./{{*}}{party_tag}/{{*}}Party/{{*}}PartyLegalEntity/{{*}}CompanyID[@schemeID='{SK_COMPANY_ID_SCHEME}']"
        )
        if company_number and company_number.strip():
            customer_values.setdefault('additional_identifiers', {})['SK_EN'] = company_number.strip()

    def _import_prepare_missing_customer_create_values(self, collected_values):
        # EXTENDS account.edi.common
        partner_create_values = super()._import_prepare_missing_customer_create_values(collected_values)

        # The routing identifier comes from an external file. A malformed one (a DIC that is not made
        # of ten digits, for instance) must not prevent the import: the partner is created without it.
        scheme = partner_create_values.get('routing_scheme')
        endpoint = partner_create_values.get('routing_endpoint')
        Partner = self.env['res.partner']
        if scheme and endpoint and (
            scheme not in Partner._fields['routing_scheme'].get_values(self.env)
            or not Partner._validate_identifier_by_scheme(scheme, endpoint)['valid']
        ):
            del partner_create_values['routing_scheme']
            del partner_create_values['routing_endpoint']
        return partner_create_values

    def _import_ubl_invoice_add_delivery(self, collected_values):
        # EXTENDS account.edi.ubl
        super()._import_ubl_invoice_add_delivery(collected_values)

        # The tax point date (BT-7) of the received e-invoice is the date of the taxable supply.
        if collected_values['company'].account_fiscal_country_id.code != 'SK':
            return
        tax_point_date_str = (collected_values['tree'].findtext('./{*}TaxPointDate') or '').strip()
        if not tax_point_date_str:
            return
        try:
            tax_point_date = fields.Date.from_string(tax_point_date_str)
        except ValueError:
            # The file comes from a third party: a malformed date must not prevent the import.
            return
        if not tax_point_date:
            return
        collected_values['to_write']['taxable_supply_date'] = tax_point_date
