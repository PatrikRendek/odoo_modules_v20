# Slovenská elektronická faktúra od 1. 1. 2027: legislatíva a technické pravidlá

Podklad k modulu `l10n_sk_edi_einvoice` (Odoo 20). Anglická verzia: [legislation_en.md](legislation_en.md).

Všetky zdroje boli overené **17. 11. 2026**. Zákony sa čítali v právne záväznom PDF znení na
Slov-Lex. Dokument nie je právne ani daňové poradenstvo.

## 1. Zdroje

| Kód | Zdroj | Odkaz |
| --- | --- | --- |
| Z1 | Zákon č. 385/2025 Z. z., ktorým sa mení zákon č. 222/2004 Z. z. o DPH (vyhlásený 19. 12. 2025); záväzné PDF časových verzií 1. 1. 2026, 1. 1. 2027 a 1. 7. 2030 | https://static.slov-lex.sk/pdf/SK/ZZ/2025/385/ZZ_2025_385_20270101.pdf |
| Z2 | Zákon č. 222/2004 Z. z. o DPH, záväzné PDF znenia účinného od 1. 1. 2027 do 30. 6. 2030 | https://static.slov-lex.sk/pdf/SK/ZZ/2004/222/ZZ_2004_222_20270101.pdf |
| Z3 | Zákon č. 222/2004 Z. z. o DPH, záväzné PDF znenia účinného od 1. 7. 2030 | https://static.slov-lex.sk/pdf/SK/ZZ/2004/222/ZZ_2004_222_20300701.pdf |
| Z4 | Zákon č. 431/2002 Z. z. o účtovníctve, záväzné PDF znenia účinného od 1. 1. 2026 | https://static.slov-lex.sk/pdf/SK/ZZ/2002/431/ZZ_2002_431_20260101.pdf |
| F1 | Finančné riaditeľstvo SR, 9/DPH/2025/IM „Najčastejšie otázky a odpovede k eFaktúre“, verzia november 2026 | https://www.financnasprava.sk/_img/pfsedit/Dokumenty_PFS/Zverejnovanie_dok/Aktualne/DPH/2026/2026.11.16_009_DPH_2026_IM_FAQ_eFak.pdf |
| F2 | Finančná správa, „Transpozície štandardu Peppol BIS v podmienkach Slovenskej legislatívy“, verzia 1.13 z 29. 10. 2026 | https://www.financnasprava.sk/_img/pfsedit/Dokumenty_PFS/Podnikatelia/Dan_z_pridanej_hodnoty/efaktura/2026/2026.10.29_Peppol_Bis3_v1_13.xlsx |
| F3 | Finančná správa, stránka e-Faktúra a zoznam certifikovaných poskytovateľov doručovacej služby (17. 11. 2026) | https://www.financnasprava.sk/sk/podnikatelia/dane/dan-z-pridanej-hodnoty/e-faktura |
| P1 | OpenPeppol, Peppol BIS Billing 3.0, verzia 3.0.21 (číselníky EAS, ICD, UNCL5305, VATEX, pravidlá, schematron) | https://docs.peppol.eu/poacc/billing/3.0/ |
| P2 | OpenPeppol, validátor Peppol Testbed | https://www.testbed.peppol.org/validation |
| P3 | OpenPeppol, Slovak Republic Tax Data Document 1.0.0 (špecifikácia, schéma, pravidlá, príklady) | https://docs.peppol.eu/tdd/sk/tdd-sk/ |
| P4 | OpenPeppol, Slovakia eInvoicing and Tax Reporting Billing Test Suite, Environment Description 1.1 | https://www.testbed.peppol.org/assets/documentation/SK-Billing-eInvoicing-and-Tax-Reporting-Environment-Description-v1.1.pdf |
| F4 | Finančná správa, akreditačná schéma a návod na akreditáciu poskytovateľa doručovacej služby | https://www.financnasprava.sk/_img/pfsedit/Dokumenty_PFS/Podnikatelia/Dan_z_pridanej_hodnoty/efaktura/2026/2026.04.14_navod_akreditacie.pdf |

## 2. Rozsah a termíny

| Pravidlo | Zdroj |
| --- | --- |
| Od 1. 1. 2027 platiteľ (§ 4, § 4b, § 4c) vyhotovuje elektronickú faktúru pri dodaní tovaru alebo služby s miestom dodania v tuzemsku a pri prijatí platby vopred, ak je príjemcom zdaniteľná osoba so sídlom, miestom podnikania, prevádzkarňou alebo bydliskom v tuzemsku, alebo nezdaniteľná právnická osoba so sídlom v tuzemsku. Súhlas príjemcu sa nevyžaduje. | Z2, § 85o ods. 2 a 3 |
| Povinnosť neplatí pre dodania oslobodené od dane podľa § 28 až § 43 a § 47 a pre zjednodušené faktúry (doklad do 100 EUR, doklad z eKasy do 400 EUR). | Z2, § 85o ods. 2, § 74 ods. 3 |
| Spotrebiteľov (B2C) sa povinnosť netýka. | F1; vyplýva z § 85o ods. 3 |
| Každý, kto je povinný elektronickú faktúru vyhotoviť, musí vedieť ju odoslať aj prijať cez doručovaciu službu; príjemca takéhoto plnenia ju musí vedieť prijať. | Z2, § 71 ods. 5 |
| Zdaniteľnou osobou je každá osoba, ktorá nezávisle vykonáva ekonomickú činnosť, vrátane využívania majetku na dosahovanie príjmu. | Z2, § 3 ods. 1 a 2 |
| Ak odberateľ dodatočne oznámi, že mu mala byť vyhotovená elektronická faktúra, lehota je dodržaná, ak ju dodávateľ vyhotoví do 15 dní od oznámenia. Finančná správa odporúča pôvodnú faktúru stornovať a vyhotoviť novú elektronickú faktúru s poznámkou o dodatočnom oznámení. | Z2, § 85o ods. 8; F1 |
| Ak odberateľ nemá doručovaciu službu, dodávateľ si povinnosť splnil odoslaním faktúry doručovacou službou. | F1; Z2, § 71 ods. 5 |
| Elektronická faktúra sa vyhotovuje do 15 dní od dodania, od prijatia platby, alebo od konca mesiaca, v ktorom nastala skutočnosť rozhodná pre opravu základu dane. | Z2, § 85o ods. 6 |
| Elektronická faktúra je vyhotovená až odovzdaním doručovacej službe; dátum vyhotovenia na faktúre má byť deň, keď sa odoslala. | F1; Z2, § 85o ods. 4 a 6 |
| Súhrnnú elektronickú faktúru možno vyhotoviť najviac za jeden kalendárny mesiac, do 15 dní od jeho skončenia. | Z2, § 85o ods. 7 |
| Dodávateľ oznamuje údaje z faktúry finančnému riaditeľstvu v čase jej vyhotovenia; odovzdaním faktúry doručovacej službe je povinnosť splnená. Lehota piatich dní sa týka faktúr vyhotovených odberateľom a príjemcu faktúry. | Z2, § 85o ods. 9 až 11 |
| Za neoznámenie, oneskorené alebo nesprávne oznámenie údajov hrozí pokuta do 10 000 EUR, pri opakovaní do 100 000 EUR; neuloží sa pri oprave zjavného omylu ani pri preukázanej poruche poskytovateľa. | Z2, § 85o ods. 12 až 14 |
| Elektronická faktúra sa uchováva desať rokov. | Z2, § 85o ods. 15 |
| Zákon neobsahuje splnomocnenie na vydanie vykonávacieho predpisu k formátu faktúry; formát určuje európska norma. | Z2, § 85o ods. 4 |

## 3. Formát a doručovanie

| Pravidlo | Zdroj |
| --- | --- |
| Elektronická faktúra je doklad s náležitosťami podľa § 74 ods. 1 vyhotovený, zaslaný a prijatý v štruktúrovanom formáte umožňujúcom automatizované spracovanie, v dátovej štruktúre podľa európskej normy pre elektronickú fakturáciu (EN 16931) a zoznamu jej syntaxí. | Z2, § 85o ods. 4 |
| V praxi ide o XML v syntaxi UBL 2.1 alebo CII D16B; v sieti Peppol o profil Peppol BIS Billing 3.0. PDF je len čitateľné zobrazenie. | F1 |
| Doručovacou službou je služba certifikovaného poskytovateľa zapísaného v evidencii finančného riaditeľstva; zabezpečuje kontrolu formálnych náležitostí, identifikáciu odosielateľa a adresáta, neporušenosť obsahu, preukázanie času odoslania a doručenia a oznamovanie údajov. | Z2, § 76a |
| Slovenské subjekty sa v sieti Peppol identifikujú schémou **0245 a DIČ** (10 číslic), nie schémou 9950 (IČ DPH). Registruje ich poskytovateľ doručovacej služby v slovenskom SMP. | F1; F2 (BT-34, BT-49); P1 (číselník EAS) |
| Subjekt bez DIČ si ho musí vybaviť, inak ho v sieti nemožno identifikovať. | F1 |
| Peppol BIS Billing 3.0 neobsahuje slovenské národné pravidlá; prísnejšie slovenské požiadavky sú zodpovednosťou odosielateľa. | P1; F1 |
| Verejný obstarávateľ musí vedieť prijímať elektronické faktúry cez doručovaciu službu; faktúra z verejného obstarávania uvádza aj číslo oznámenia o vyhlásení verejného obstarávania (pole BT-12). | Z1, čl. VII (§ 2 zákona č. 215/2019 Z. z.); F2 |

## 4. Obsah faktúry

Označenia BT a BG sú obchodné termíny normy EN 16931.

| Pravidlo | Zdroj |
| --- | --- |
| Poradové číslo faktúry (BT-1) vychádza z jednej alebo viacerých sérií a faktúru jednoznačne identifikuje; dátum vyhotovenia (BT-2) je povinný. | Z2, § 74 ods. 1 písm. c) a e) |
| Dátum dodania alebo dátum prijatia platby sa uvádza, ak ho možno určiť a ak sa líši od dátumu vyhotovenia; v elektronickej faktúre v poli BT-7. Pole BT-8 sa nepoužíva. Pri platbe vopred vzniká daňová povinnosť dňom prijatia platby. | Z2, § 74 ods. 1 písm. d), § 19 ods. 4; F2 |
| Meno a adresa dodávateľa aj odberateľa sú povinné; vyžaduje sa ulica (BT-35, BT-50), mesto (BT-37, BT-52) a PSČ (BT-38, BT-53). | Z2, § 74 ods. 1 písm. a) a b); F2 |
| Identifikátor na účely DPH (BT-31, BT-48) je IČ DPH s predponou krajiny, ak bolo pridelené. | Z2, § 74 ods. 1 písm. a) a b); P1 (BR-CO-09) |
| Identifikátor zákonnej registrácie (BT-30, BT-47) je IČO, ak bolo pridelené, so schémou zo zoznamu ISO 6523; pre slovenské IČO je to schéma 0158. | F2; P1 (číselník ICD) |
| Elektronická adresa dodávateľa (BT-34) aj odberateľa (BT-49) je povinná, so schémou 0245. | F2 |
| Kategória DPH sa určuje podľa právneho režimu dodania: S (základná aj znížená sadzba), E (oslobodené, § 28 až § 42), K (§ 43), G (§ 47), AE (prenesenie daňovej povinnosti), O (mimo predmetu dane), Z (skutočná nulová sadzba). | F1, časť III |
| Ak daň platí príjemca, faktúra uvádza slovnú informáciu „prenesenie daňovej povinnosti“: kategória AE, kód VATEX-EU-AE. | Z2, § 74 ods. 1 písm. k); F1; P1 (BR-AE-10) |
| Tuzemské prenesenie daňovej povinnosti sa uplatní, len ak je dodávateľ aj príjemca platiteľom s prideleným identifikačným číslom pre daň. | Z2, § 69 ods. 12 |
| Pri službe s miestom dodania v inom členskom štáte, keď daň platí príjemca, sa uvádza „prenesenie daňovej povinnosti“; sadzba a suma dane sa uvádzať nemusia. | Z2, § 72 ods. 1 písm. b), § 74 ods. 1 písm. k) a ods. 2 |
| Pri trojstrannom obchode prvý odberateľ vyhotoví pre druhého odberateľa faktúru bez dane s informáciou „prenesenie daňovej povinnosti“. | Z2, § 45 ods. 3 |
| Pri oslobodení od dane sa uvádza odkaz na ustanovenie zákona alebo smernice 2006/112/ES, alebo slovná informácia „dodanie je oslobodené od dane“. Stačí kód dôvodu alebo text; Finančná správa odporúča kód a text ako doplnok. | Z2, § 74 ods. 1 písm. h); P1 (BR-E-10); F1 |
| Kategóriu O nemožno na jednej faktúre kombinovať s inými kategóriami a neuvádza sa pri nej IČ DPH dodávateľa ani odberateľa. Používa ju aj neplatiteľ DPH, ktorý fakturuje elektronicky dobrovoľne. | P1 (BR-O-02, BR-O-11); F1 |
| Výška dane sa uvádza v eurách aj pri faktúre v cudzej mene (BT-6, BT-111). Prepočet sa robí referenčným kurzom ECB alebo NBS z dňa predchádzajúceho dňu vzniku daňovej povinnosti; pri oprave základu dane kurzom pôvodnej faktúry. To isté pravidlo platí v účtovníctve. | Z2, § 74 ods. 1 písm. i), § 26 ods. 1; Z4, § 24 ods. 2 |
| Doklad, ktorý mení elektronickú faktúru, je tiež elektronickou faktúrou. Musí obsahovať poradové číslo pôvodnej faktúry (BT-25) a údaje, ktoré sa menia; ak bola pôvodná faktúra zaslaná doručovacou službou, musí ňou ísť aj opravný doklad. | Z2, § 85o ods. 5, § 71 ods. 2, § 74 ods. 3 písm. c) |
| Oprava základu dane sa priznáva v zdaňovacom období, v ktorom sa opravný doklad vyhotovil. | Z2, § 25 ods. 3 |
| Pokyny pre platbu (BG-16) nie sú povinné; číslo účtu dodávateľa (BT-84) sa vyžaduje len pri platbe prevodom. | F2; P1 (BR-61) |
| Zálohová (proforma) faktúra ako výzva na úhradu nie je faktúrou a cez doručovaciu službu sa neposiela; faktúra k prijatej platbe elektronickou faktúrou byť musí. | F1; Z2, § 85o ods. 2 |

### Kódy dôvodu oslobodenia (VATEX) podľa Finančnej správy

| Ustanovenie zákona o DPH | Plnenie | Kategória | Kód VATEX |
| --- | --- | --- | --- |
| § 22 | prechodné položky | E | VATEX-EU-79-C |
| § 28 | poštové služby | E | VATEX-EU-132-1A |
| § 29 | zdravotná starostlivosť | E | VATEX-EU-132-1B, 1C, 1D, 1E alebo 1P podľa prípadu |
| § 30 | služby sociálnej pomoci | E | VATEX-EU-132-1G alebo 1H |
| § 31 | výchovné a vzdelávacie služby | E | VATEX-EU-132-1I alebo 1J |
| § 32 | služby dodávané členom | E | VATEX-EU-132-1L alebo 1F |
| § 33 | služby súvisiace so športom | E | VATEX-EU-132-1M |
| § 34 | kultúrne služby | E | VATEX-EU-132-1N |
| § 35 | zhromažďovanie finančných prostriedkov | E | VATEX-EU-132-1O |
| § 36 | služby verejnoprávnej televízie a rozhlasu | E | VATEX-EU-132-1Q |
| § 37 až § 41 | poisťovacie a finančné služby, nehnuteľnosti, poštové ceniny, lotérie | E | VATEX-EU-135-1 |
| § 42 | tovar, pri ktorom nebola odpočítaná daň | E | bez kódu |
| § 43 | dodanie tovaru do iného členského štátu | K | VATEX-EU-IC |
| § 47 | vývoz tovaru | G | VATEX-EU-G |
| § 69 | prenesenie daňovej povinnosti | AE | VATEX-EU-AE |
| – | plnenie mimo predmetu dane | O | VATEX-EU-O |

Zdroj: F1, časť III. Oslobodené dodania podľa § 28 až § 43 a § 47 pod povinnú elektronickú
fakturáciu nespadajú; tabuľka slúži pre prípad, že sa elektronicky fakturujú dobrovoľne.

## 5. Od 1. 7. 2030

Od 1. 7. 2030 sa pravidlá menia; modul ich nepokrýva a pred týmto dátumom ho treba upraviť.

| Pravidlo | Zdroj |
| --- | --- |
| Elektronická faktúra sa stáva predvolenou formou faktúry vrátane cezhraničných dodaní; výnimkou je zjednodušená faktúra a „faktúra v inej podobe“. | Z3, § 71 ods. 1, 4 a 6, § 72 ods. 9 až 11 |
| Lehota na vyhotovenie faktúry sa skracuje na desať dní. | Z3, § 73 |
| Pribúdajú náležitosti: slovná informácia „trojstranný obchod“, poradové číslo pôvodnej faktúry pri opravnom doklade a čísla účtov dodávateľa. | Z3, § 74 ods. 1 písm. k), p) a q) |
| Ruší sa kontrolný výkaz aj súhrnný výkaz; nahrádza ich oznamovanie údajov z každej faktúry pri cezhraničných (§ 80) a tuzemských (§ 80a) dodaniach. | Z3, § 80, § 80a, § 85o ods. 17 |
| Na opravu faktúry za dodanie do 30. 6. 2030 sa použijú pravidlá platné do tohto dňa. | Z3, § 85o ods. 24 |

## 6. Ako pravidlá pokrýva modul

| Oblasť | Riešenie |
| --- | --- |
| Formát | Jadro Odoo generuje a importuje Peppol BIS Billing 3.0. Modul ho nastaví ako predvolený pre slovenských odberateľov slovenskej firmy okrem spotrebiteľov. |
| Identifikátor Peppol | Schému 0245 a odvodenie DIČ z IČ DPH má jadro. Modul kontroluje formát DIČ a pred odoslaním overí identifikátor 0245:DIČ oboch strán. |
| IČ DPH a IČO | Do BT-31 a BT-48 ide IČ DPH s predponou SK, do BT-30 a BT-47 IČO so schémou 0158. |
| Dátum dodania | Export do BT-7 a import z BT-7. |
| Kategórie DPH | Dane slovenskej osnovy pre prenesenie daňovej povinnosti, služby do EÚ a trojstranný obchod majú kategóriu AE, tovar do EÚ K, vývoz G; zákonné texty sa dopĺňajú v slovenčine. |
| Opravný doklad | Dobropis nesie odkaz na pôvodnú faktúru; bez odkazu sa neodošle. |
| Kontrola pred odoslaním | Adresa, DIČ, IČ DPH, prenesenie daňovej povinnosti bez IČ DPH odberateľa, odkaz dobropisu. |
| Kurz | Kurz sa hľadá k dátumu zdaniteľného plnenia; jadro Odoo 20 berie posledný kurz vyhlásený pred týmto dátumom. Dobropis preberá kurz pôvodnej faktúry. |
| Dátum vyhotovenia | Sprievodca odoslaním upozorní, ak sa faktúra odosiela v iný deň, než je jej dátum. |
| Spôsob odoslania | Pri slovenskom odberateľovi je predvolený Peppol, ak je firma do siete zapojená cez modul `account_peppol`. |
| Import | Dátum dodania a IČO; chybný identifikátor dodávateľa import nezastaví. |

Mimo rozsahu modulu: doručovanie a oznamovanie údajov (zabezpečuje doručovacia služba), typ
dokladu 384, údaje o zápise v registri (BT-33), číslo verejného obstarávania (BT-12), osobitná
podpora zálohových faktúr, faktúr vyhotovených odberateľom, skupiny DPH a daňového zástupcu,
sledovanie lehôt a pravidlá účinné od 1. 7. 2030.

## 7. Overenie

| Čo | Výsledok |
| --- | --- |
| Automatické testy modulu na čistej databáze Odoo 20 (zdrojové kódy zo 17. 11. 2026), s modulom `account_peppol` aj bez neho | 51 testov, bez chyby; bez modulu `account_peppol` sa 5 testov odoslania cez Peppol preskočí |
| Validátor Peppol Testbed (P2), špecifikácie BIS Billing Invoice a Credit Note 3.0.21, 17. 11. 2026 | 13 vzoriek prešlo kontrolou XSD, jurisdikčných pravidiel, EN 16931 aj Peppol |
| Používateľské rozhranie | Vystavenie a potvrdenie faktúry, sprievodca odoslaním s PDF a XML, upozornenie na dátum, chybové hlásenia a import prijatej faktúry |
| Vyhľadanie slovenských účastníkov v produkčnej sieti Peppol cez prístupový bod Odoo | Účastníci so schémou 0245 sa našli v slovenskom SMP (`sml.peppol-smp.sk`) a prijímajú Peppol BIS Billing 3.0; identifikátor so schémou 9950 sa nenašiel. Adresár Peppol evidoval 53 175 slovenských účastníkov. |
| Odoslanie a príjem cez `account_peppol` v demo režime | Registrácia firmy pod `0245:DIČ`, odoslanie faktúry so stavom „doručené“, zablokovanie faktúry s chybou a príjem dokladu prebehli |
| Certifikácia prístupového bodu Odoo | Odoo SA je v zozname certifikovaných poskytovateľov doručovacej služby (PA SK ID EFSK000048, stav k 17. 11. 2026). Podmienkou zápisu je záznam o úspešnom testovaní v prostredí Peppol Testbed pre Slovensko (F4), ktoré zahŕňa odoslanie a príjem faktúry a dobropisu spolu s hlásením údajov daňovej správe (P4). |
| Hlásenie údajov (Tax Data Document) | Z 13 vzoriek boli podľa špecifikácie P3 zostavené hlásenia tak, ako ich tvorí doručovacia služba. 12 prešlo validátorom P2 (schéma, slovenské pravidlá TDD, EN 16931, Peppol). Hlásenie k dodaniu tovaru do iného členského štátu neprešlo pravidlom BR-IC-12, lebo špecifikácia TDD 1.0.0 neumožňuje uviesť krajinu dodania; toto dodanie pod povinnosť od 1. 1. 2027 nespadá. |
| Registrácia cez Odoo | Predbežná kontrola oboch serverov Odoo identifikátor `0245:DIČ` prijala; produkčný server vyžaduje overenie firmy. |
| Verejné záznamy slovenského SMP | Vo vzorke 931 slovenských účastníkov neprijímal faktúry cez prístupový bod Odoo ani jeden; najčastejšie prístupové body boli Flowis, Softip, Verteco a ion-AP. |
| Dokumentácia Odoo | Slovensko je medzi krajinami, pre ktoré Odoo umožňuje registráciu do siete Peppol; osobitnú stránku pre Slovensko dokumentácia nemá |

Validované vzorky: tuzemská faktúra, prenesenie daňovej povinnosti, oslobodené dodanie,
odberateľ bez IČ DPH, cudzia mena, faktúra bez bankového účtu, služby do EÚ, tovar do EÚ,
trojstranný obchod, dobropis a tri vzorové súbory z testov modulu.
