# Slovensko - doručovacia služba e-faktúr (SAPI-SK)

Modul pre Odoo 20, ktorý odosiela a prijíma slovenské e-faktúry cez certifikovanú doručovaciu
službu („digitálneho poštára“) rozhraním SAPI-SK 1.0.

- odovzdá e-faktúru Peppol BIS Billing 3.0 službe zo sprievodcu Odoslať,
- sleduje stav doručenia (Verteco, eFakturuj),
- sťahuje prijaté e-faktúry ako návrhy dodávateľských faktúr.

Závisí od modulu `l10n_sk_edi_einvoice`. Licencia: LGPL-3.

Dokumentácia: [slovensky](doc/documentation_sk.md), [anglicky](doc/documentation_en.md).
