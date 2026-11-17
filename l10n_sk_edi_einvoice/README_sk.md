# Slovensko – elektronická fakturácia (Peppol BIS Billing 3.0)

Anglická verzia: [README.md](README.md)

Slovenské špecifiká nad elektronickou faktúrou Peppol BIS Billing 3.0 v Odoo 20 pre povinnú
tuzemskú elektronickú fakturáciu od 1. 1. 2027 (zákon č. 385/2025 Z. z., ktorým sa mení zákon
č. 222/2004 Z. z. o DPH).

- Verzia: 1.0.0
- Licencia: LGPL-3
- Závislosti: `l10n_sk`, `account_edi_ubl_cii`

Doručovanie faktúr a oznamovanie údajov finančnej správe zabezpečuje certifikovaná doručovacia
služba (prístupový bod Peppol), nie tento modul.

## Funkcie

- Peppol BIS Billing 3.0 je predvolený formát elektronickej faktúry pre slovenských firemných
  odberateľov slovenskej firmy. Spotrebitelia dostávajú faktúru ako doteraz.
- Kontrola daňového identifikačného čísla (DIČ), ktoré je identifikátorom každého slovenského
  subjektu v sieti Peppol (schéma 0245).
- Slovenský obsah XML: IČ DPH s predponou SK ako identifikátor na účely DPH, IČO (schéma 0158)
  ako identifikátor zákonnej registrácie, dátum zdaniteľného plnenia ako dátum dodania, odkaz na
  pôvodnú faktúru pri dobropise.
- Kategórie DPH slovenskej účtovej osnovy: prenesenie daňovej povinnosti (AE, vrátane služieb do
  iného členského štátu a trojstranného obchodu), dodanie tovaru do EÚ (K), vývoz (G), s textami,
  ktoré vyžaduje zákon o DPH.
- Kontroly pred odoslaním s hláseniami, ktoré používateľovi povedia, čo má opraviť: adresa, DIČ,
  IČ DPH, prenesenie daňovej povinnosti, odkaz dobropisu.
- Kurz faktúr v cudzej mene slovenských firiem podľa dátumu zdaniteľného plnenia, čo dáva kurz
  vyhlásený deň pred vznikom daňovej povinnosti.
- Upozornenie v sprievodcovi odoslaním, ak sa slovenská elektronická faktúra odosiela v iný deň,
  než je jej dátum.
- Peppol ako predvolený spôsob odoslania pre slovenských odberateľov, ak je nainštalovaný modul
  `account_peppol` a firma je do siete zapojená.
- Import prijatých elektronických faktúr: dátum zdaniteľného plnenia, IČO dodávateľa a odolnosť
  voči chybnému identifikátoru dodávateľa.
- Slovenské a české preklady.

## Dokumentácia

- [`doc/documentation_sk.md`](doc/documentation_sk.md): dokumentácia modulu.
- [`../docs/legislation_sk.md`](../docs/legislation_sk.md): právne a technické zdroje pravidiel.

Modul nie je právne ani daňové poradenstvo.

## Testy

```
odoo-bin -d <db> -i l10n_sk_edi_einvoice --test-enable --test-tags /l10n_sk_edi_einvoice --stop-after-init
```

Vygenerované faktúry aj vzorové súbory boli overené validátorom Peppol Testbed (BIS Billing
3.0.21).

## Zoznam zmien

### 1.0.0

- Prvá verzia pre Odoo 20.
