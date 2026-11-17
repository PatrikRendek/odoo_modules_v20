# Slovensko – elektronická fakturácia (`l10n_sk_edi_einvoice`)

Dokumentácia modulu pre Odoo 20. Anglická verzia: [documentation_en.md](documentation_en.md).
Právne a technické zdroje pravidiel sú v súbore
[`docs/legislation_sk.md`](../../docs/legislation_sk.md).

## 1. Na čo modul slúži

Od 1. 1. 2027 musia platitelia DPH pri tuzemských dodaniach pre podnikateľov a právnické osoby
vyhotovovať faktúry ako štruktúrované elektronické faktúry podľa normy EN 16931 a posielať ich
cez certifikovanú doručovaciu službu v sieti Peppol.

Odoo 20 vie faktúru vo formáte Peppol BIS Billing 3.0 vytvoriť aj prijať. Modul dopĺňa slovenské
požiadavky, ktoré jadro nepokrýva, a nič z jadra neduplikuje. Samotné doručovanie a oznamovanie
údajov finančnému riaditeľstvu zabezpečuje doručovacia služba.

## 2. Čo robí jadro a čo dopĺňa modul

| Oblasť | Jadro Odoo 20 | Modul |
| --- | --- | --- |
| Formát | Generuje a importuje Peppol BIS Billing 3.0, pre slovenských partnerov ho však predvolene nenavrhuje. | Navrhne ho pre slovenských odberateľov slovenskej firmy okrem spotrebiteľov. |
| Identifikátor Peppol | Pozná schému 0245 (DIČ) a DIČ odvodí z IČ DPH. | Kontroluje formát DIČ (10 číslic) a pred odoslaním overí identifikátor 0245:DIČ oboch strán. |
| IČ DPH v XML (BT-31, BT-48) | Pri slovenskom partnerovi uvedie DIČ bez predpony SK. | Uvedie IČ DPH s predponou SK; subjekt bez IČ DPH nemá identifikátor DPH žiadny. |
| IČO v XML (BT-30, BT-47) | Uvedie DIČ so schémou 0245. | Uvedie IČO so schémou 0158, ak je na kontakte vyplnené. |
| Dátum dodania (BT-7) | Neexportuje ani neimportuje. | Exportuje, ak sa líši od dátumu vyhotovenia; pri importe ho zapíše do dátumu zdaniteľného plnenia. |
| Kategória DPH | Daň 0 % v tuzemsku označí ako oslobodenú s anglickým textom. | Nastaví kategórie daní slovenskej osnovy a dopĺňa zákonné texty v slovenčine. |
| Odkaz dobropisu (BT-25) | Pri dobropise odoslanom pred spárovaním ho nevyplní. | Vyplní ho z faktúry, z ktorej dobropis vznikol, alebo z faktúry, s ktorou je spárovaný. |
| Kontrola pred odoslaním | Všeobecné pravidlá EN 16931 a Peppol. | Slovenské povinné údaje so zrozumiteľnými hláseniami. |
| Kurz cudzej meny | Hľadá kurz podľa dátumu faktúry. | Hľadá kurz podľa dátumu zdaniteľného plnenia. |
| Dátum vyhotovenia | Neporovnáva ho s dňom odoslania. | Sprievodca odoslaním na rozdiel upozorní. |
| Import dodávateľa | Vytvorí kontakt aj bez IČ DPH; chybný identifikátor zo súboru import zastaví. | Uloží na kontakt IČO a chybný identifikátor zahodí, aby import prebehol. |
| Spôsob odoslania | Peppol predvolí len pre vybrané krajiny, Slovensko medzi nimi nie je. | Predvolí Peppol pre slovenských odberateľov, ak je firma do siete zapojená. |

## 3. Inštalácia

1. Závislosti: `l10n_sk` a `account_edi_ubl_cii` (súčasť Odoo). Na odosielanie cez Peppol treba
   navyše modul `account_peppol`; modul funguje aj bez neho a vtedy XML len vytvára a kontroluje.
2. Pridajte priečinok repozitára do `addons_path` a modul nainštalujte.
3. Pri inštalácii sa na daniach slovenskej účtovej osnovy doplní kategória DPH pre elektronickú
   fakturáciu. Dane, ktoré už kategóriu majú nastavenú, modul nemení.

## 4. Nastavenie

### 4.1 Vlastná firma

Na kontakte firmy musia byť vyplnené:

- názov, ulica, mesto, PSČ a krajina Slovensko,
- IČ DPH v tvare `SK` a 10 číslic,
- DIČ (10 číslic) medzi ďalšími identifikátormi; ak je vyplnené IČ DPH, DIČ sa odvodí samo,
- IČO medzi ďalšími identifikátormi,
- bankový účet označený ako dôveryhodný, ak sa má na faktúre uvádzať. Faktúra bez banky
  príjemcu (napr. uhradená v hotovosti alebo kartou) sa odošle bez platobných pokynov.

### 4.2 Odberatelia

- Slovenský odberateľ potrebuje DIČ (alebo IČ DPH, z ktorého sa DIČ odvodí), úplnú adresu a
  IČO, ak ho má pridelené.
- Formát elektronickej faktúry sa pri slovenskom odberateľovi nastaví na „EU Standard (Peppol
  Bis 3.0)“ automaticky, ak je kontakt firma alebo má IČO, DIČ či IČ DPH. Kontakt bez týchto
  údajov sa považuje za spotrebiteľa.
- Predvoľbu možno na kontakte zmeniť (karta Účtovníctvo). Urobte tak pri fyzickej osobe, ktorá
  oznámi, že je zdaniteľnou osobou.

### 4.3 Smerovací identifikátor

Slovenské subjekty sa v sieti Peppol adresujú ako `0245:DIČ`. Odoo tento identifikátor zvolí
samo, keď má kontakt DIČ.

## 5. Dane a kategórie DPH

| Daň v osnove | Použitie | Kategória | Kód dôvodu | Text dôvodu |
| --- | --- | --- | --- | --- |
| 0 % PREN (`vy_rc`) | tuzemské prenesenie daňovej povinnosti | AE | VATEX-EU-AE | Prenesenie daňovej povinnosti |
| 0 % EÚ S (`vy_eu_s`) | služby do iného členského štátu | AE | VATEX-EU-AE | Prenesenie daňovej povinnosti |
| 0 % EÚ TRI (`vy_eu_t`) | trojstranný obchod, faktúra prvého odberateľa druhému odberateľovi | AE | VATEX-EU-AE | Prenesenie daňovej povinnosti |
| 0 % EÚ T (`vy_eu_m`) | dodanie tovaru do iného členského štátu | K | VATEX-EU-IC | Dodanie je oslobodené od dane podľa § 43 zákona č. 222/2004 Z. z. |
| 0 % VÝV (`vy_mimo_eu`) | vývoz mimo EÚ | G | VATEX-EU-G | Dodanie je oslobodené od dane podľa § 47 zákona č. 222/2004 Z. z. |

- Dane 23 %, 19 % a 5 % dostanú kategóriu S automaticky.
- Tuzemské dane 0 % dostanú kategóriu E a text „Dodanie je oslobodené od dane“. Kód dôvodu
  podľa konkrétneho ustanovenia zákona možno vybrať na dani (Účtovníctvo → Konfigurácia → Dane);
  prehľad kódov je v `docs/legislation_sk.md`, kapitola 4.
- Text dôvodu vyplnený priamo na dani má prednosť pred textom, ktorý dopĺňa modul.

## 6. Vystavenie a odoslanie faktúry

1. Vystavte a potvrďte faktúru. Ak sa dátum dodania líši od dátumu vyhotovenia, vyplňte pole
   Dátum zdaniteľného plnenia. Pri faktúre k prijatej platbe doň zadajte deň prijatia platby.
2. Kliknite na **Odoslať**. Pri slovenskom odberateľovi je predvolený formát Peppol BIS 3.0 a
   medzi prílohami je popri PDF aj súbor XML. Ak je firma zapojená do siete Peppol, je predvolený
   aj spôsob odoslania Peppol.
3. Pri odoslaní sa XML vytvorí a skontroluje. Ak niečo chýba, sprievodca vypíše zoznam chýb a
   faktúra sa neodošle.

### 6.1 Obsah XML

| Prvok XML | Obsah |
| --- | --- |
| `cbc:TaxPointDate` (BT-7) | dátum zdaniteľného plnenia, ak sa líši od dátumu vyhotovenia |
| `cac:PartyTaxScheme/cbc:CompanyID` (BT-31, BT-48) | IČ DPH s predponou SK; chýba, ak subjekt IČ DPH nemá |
| `cac:PartyLegalEntity/cbc:CompanyID` (BT-30, BT-47) | IČO so `schemeID="0158"`; bez IČO ostáva DIČ so `schemeID="0245"` |
| `cac:TaxCategory` (BT-118, BT-120, BT-121) | AE + VATEX-EU-AE + „Prenesenie daňovej povinnosti“; E + „Dodanie je oslobodené od dane“ |
| `cac:BillingReference` (BT-25) | číslo a dátum pôvodnej faktúry pri dobropise |

Identifikátory (IČ DPH, IČO) sa upravujú pri každej slovenskej strane dokladu. Ostatné pravidlá
sa uplatnia na doklady, ktorých dodávateľ sídli na Slovensku.

### 6.2 Kontroly pred odoslaním

| Hlásenie | Kedy sa zobrazí |
| --- | --- |
| Adresa partnera je neúplná | dodávateľovi alebo slovenskému odberateľovi chýba ulica, mesto alebo PSČ |
| Partner musí byť identifikovaný DIČ | dodávateľ alebo slovenský odberateľ nemá identifikátor 0245 s 10 číslicami |
| IČ DPH nie je platné | IČ DPH slovenského subjektu nemá tvar SK a 10 číslic |
| Dodávateľ nemá IČ DPH | faktúra obsahuje inú kategóriu DPH než O a dodávateľ nemá IČ DPH |
| Prenesenie daňovej povinnosti, odberateľ nemá IČ DPH | kategória AE a slovenský odberateľ bez IČ DPH |
| Dobropis sa neodkazuje na faktúru | dobropis bez väzby na pôvodnú faktúru |

K týmto kontrolám sa pridávajú všeobecné kontroly jadra.

Neúplné kontakty sa hlásia aj pred odoslaním: ak vlastnej firme alebo slovenskému odberateľovi
chýba adresa, DIČ alebo má IČ DPH v nesprávnom tvare, sprievodca Odoslať zobrazí upozornenie
s tlačidlom, ktoré otvorí kontakty na doplnenie.

### 6.3 Kurz pri faktúrach v cudzej mene

Vo firme so slovenskou fiškálnou krajinou sa suma faktúry prepočíta kurzom podľa **dátumu
zdaniteľného plnenia**. Odoo 20 k danému dátumu hľadá posledný kurz vyhlásený pred ním, takže
výsledkom je kurz z dňa predchádzajúceho dňu vzniku daňovej povinnosti, ako vyžaduje § 26 ods. 1
zákona o DPH a § 24 ods. 2 zákona o účtovníctve.

- Platí pre odberateľské aj dodávateľské faktúry.
- Dobropis vytvorený z faktúry preberá dátum kurzu pôvodnej faktúry.
- Kurzy treba mať v Odoo nahraté s dátumom, keď ich ECB alebo NBS vyhlásila.
- Zaúčtované doklady sa inštaláciou modulu neprepočítajú.

### 6.4 Dátum vyhotovenia a deň odoslania

Elektronická faktúra je vyhotovená až odovzdaním doručovacej službe a jej dátum vyhotovenia má
byť deň odoslania. Ak sa slovenskému odberateľovi prvýkrát odosiela faktúra, ktorej dátum nie je
dnešný, sprievodca odoslaním zobrazí upozornenie. Odoslanie neblokuje a dátum zaúčtovanej
faktúry nemení; faktúru možno vrátiť do návrhu a dátum upraviť.

### 6.5 Odoslanie cez Peppol

Sieť Peppol sprístupňuje modul `account_peppol` (Účtovníctvo → Konfigurácia → Nastavenia →
Elektronická fakturácia). Odoo je prístupovým bodom siete Peppol a je v zozname certifikovaných
poskytovateľov doručovacej služby Finančnej správy.

- Registračný sprievodca navrhne slovenskej firme identifikátor `0245:DIČ`. Registráciu
  dokončuje používateľ: zadáva kontaktný e-mail a telefón a firmu overuje poskytovateľ.
- Odberateľa Odoo vyhľadá v sieti podľa `0245:DIČ` a overí, že prijíma Peppol BIS Billing 3.0.
  Vyhľadanie slovenských účastníkov bolo overené v produkčnej sieti; sú registrovaní v
  slovenskom SMP.
- Faktúru odošlite zo sprievodcu odoslaním so zaškrtnutým spôsobom Peppol. Stav doručenia je na
  faktúre v poli Stav Peppol.
- Kontroly modulu platia aj pri odoslaní cez Peppol: faktúra s chybou sa do siete neodošle.
- Oznámenie údajov finančnému riaditeľstvu robí doručovacia služba pri prevzatí faktúry.
- Na vyskúšanie bez skutočného odosielania slúži demo režim modulu `account_peppol`. Produkčný
  server Odoo pri registrácii vyžaduje overenie firmy.

### 6.6 Dobropis

Dobropis vytvorte tlačidlom Dobropis na pôvodnej faktúre. XML dobropisu nesie číslo a dátum
pôvodnej faktúry. Dátum zdaniteľného plnenia na dobropise ponechajte rovný dátumu dobropisu:
zákon vyžaduje len číslo pôvodnej faktúry a údaje, ktoré sa menia.

## 7. Príjem elektronickej faktúry

XML sa importuje bežnými cestami Odoo: nahratím do zoznamu dodávateľských faktúr, e-mailom na
alias denníka alebo cez Peppol. Modul pri tom:

- zapíše `cbc:TaxPointDate` do poľa Dátum zdaniteľného plnenia; ak v súbore chýba alebo je
  chybný, použije sa dátum vyhotovenia,
- uloží na novovytvoreného dodávateľa IČO zo `schemeID="0158"`,
- chybný identifikátor dodávateľa zo súboru (napr. DIČ, ktoré nemá 10 číslic) zahodí, takže
  import prebehne a dodávateľ sa vytvorí bez neho.

Existujúceho dodávateľa nájde jadro podľa IČ DPH alebo DIČ; nového vytvorí aj bez IČ DPH.

Importovaný doklad je návrh; pred zaúčtovaním skontrolujte dane a účty.

## 8. Rozsah modulu

Modul nepokrýva: doručovanie a oznamovanie údajov, ťarchopisy, typ dokladu 384, údaje o zápise v registri
(BT-33), číslo verejného obstarávania (BT-12), osobitnú podporu zálohových faktúr, faktúr
vyhotovených odberateľom, skupiny DPH a daňového zástupcu, sledovanie lehôt a pravidlá účinné od
1. 7. 2030. Kontrola DIČ overuje počet číslic.

## 9. Technický opis

| Súbor | Obsah |
| --- | --- |
| `models/res_partner.py` | kontrola DIČ, predvolený formát faktúry, Slovensko medzi krajinami formátu BIS 3 |
| `models/account_edi_xml_ubl_bis3.py` | rozšírenie `account.edi.xml.ubl_bis3`: uzly XML, kontroly pred odoslaním, import |
| `models/account_move.py` | dátum kurzu podľa dátumu zdaniteľného plnenia |
| `models/account_move_send.py` | predvoľba spôsobu odoslania Peppol, upozornenia na údaje kontaktov a na dátum faktúry v sprievodcovi odoslaním |
| `models/account_chart_template.py` | kategórie DPH daní slovenskej osnovy, doplnené do nových osnov a pri inštalácii aj do existujúcich |
| `i18n/` | preklady `sk.po` a `cs.po` |
| `tests/` | testy exportu, importu, kontaktov, účtovania a odoslania cez Peppol v demo režime; vzorové XML v `tests/test_files/` |

Modul nepridáva nový formát, polia, modely, prístupové práva ani zobrazenia.

### Testy

```
odoo-bin -d <db> -i l10n_sk_edi_einvoice --test-enable --test-tags /l10n_sk_edi_einvoice --stop-after-init
```

| Vzorový súbor | Scenár |
| --- | --- |
| `sk_invoice_domestic.xml` | tuzemská faktúra 23 %, dátum dodania odlišný od dátumu vyhotovenia |
| `sk_invoice_reverse_charge.xml` | tuzemské prenesenie daňovej povinnosti |
| `sk_invoice_non_vat_supplier.xml` | dodávateľ, ktorý nie je platiteľom DPH |

Vzorové súbory aj faktúry vygenerované modulom prešli validátorom Peppol Testbed (BIS Billing
3.0.21). Identifikačné čísla vo vzorkách a testoch sú vymyslené.
