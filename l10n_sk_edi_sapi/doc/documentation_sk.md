# Slovensko - doručovacia služba e-faktúr (`l10n_sk_edi_sapi`)

Dokumentácia modulu pre Odoo 20. Anglická verzia: [documentation_en.md](documentation_en.md).

## 1. Účel

Od 1. januára 2027 sa slovenská e-faktúra odosiela cez certifikovanú doručovaciu službu
(„digitálneho poštára“), ktorá ju doručí sieťou Peppol a nahlási jej údaje Finančnému
riaditeľstvu.

Takouto službou je aj samotné Odoo (modul `account_peppol`). Tento modul je určený firmám,
ktoré majú zmluvu s inou slovenskou doručovacou službou: e-faktúru jej odovzdá cez rozhranie
**SAPI-SK 1.0**, sleduje doručenie a sťahuje prijaté e-faktúry.

Súbor XML a jeho slovenské kontroly pochádzajú z modulu `l10n_sk_edi_einvoice`; tento modul
súbor iba prepravuje.

## 2. Čo modul robí

| Oblasť | Správanie |
| --- | --- |
| Odoslanie | Nový spôsob odoslania „cez slovenskú doručovaciu službu“ v sprievodcovi Odoslať. Súbor Peppol BIS Billing 3.0 sa odovzdá službe. |
| Stav | Na faktúre je stav u služby: Odovzdaná, Doručená, Príjemca nie je v sieti, Odmietnutá príjemcom, Chyba. |
| Príjem | Plánovaná akcia stiahne prijaté e-faktúry, vytvorí z nich návrhy dodávateľských faktúr a potvrdí ich prevzatie. |
| Ochrana | Faktúru odovzdanú službe nemožno vrátiť do návrhu, zrušiť ani zmazať, neodošle sa dvakrát a ide len jednou sieťou. |

## 3. Pred začatím

1. Uzatvorte zmluvu s certifikovanou doručovacou službou, ktorá ponúka rozhranie SAPI-SK.
2. Službu si vyberte na portáli Finančnej správy. Firma má práve jednu službu na príjem
   a môže mať viac služieb na odosielanie.
3. V portáli služby si vytvorte prístupové údaje pre API (client ID a client secret).

## 4. Inštalácia a nastavenie

1. Nainštalujte modul. Závisí od modulu `l10n_sk_edi_einvoice`.
2. Otvorte Účtovníctvo → Konfigurácia → Nastavenia → **Slovenská doručovacia služba** (sekcia
   sa zobrazuje firme s fiškálnou krajinou Slovensko) a vyplňte:

| Pole | Obsah |
| --- | --- |
| Doručovacia služba | Verteco, eFakturuj alebo Iná služba SAPI-SK |
| URL | adresa rozhrania začínajúca `https://` a zakončená `/sapi` |
| Client ID, Client Secret | prístupové údaje vytvorené v portáli služby |
| Denník prijatých faktúr | nákupný denník stiahnutých faktúr; prázdne = prvý nákupný denník |

3. Uložte nastavenia a kliknite na **Otestovať spojenie**. Modul si od služby vyžiada prístupový token a oznámi
   výsledok.

Firma musí mať medzi doplnkovými identifikátormi svojho kontaktu DIČ: službe sa posiela ako
`0245:DIČ` pri každom volaní. Prístupové údaje vidia len správcovia.

## 5. Odoslanie faktúry

1. Potvrďte faktúru a kliknite na **Odoslať**.
2. Slovenskému odberateľovi sa predvyberie spôsob „cez slovenskú doručovaciu službu“, ak sa na
   faktúru nepoužije pripojenie Odoo na Peppol. Spôsob možno zaškrtnúť pri každom odberateľovi,
   ktorý má identifikátor Peppol.
3. Pri odoslaní sa XML vytvorí, skontroluje a odovzdá službe.

| Odpoveď služby | Výsledok na faktúre |
| --- | --- |
| Prijatá | stav Odovzdaná, uloží sa identifikátor dokladu, upozornenia služby sa zapíšu do histórie |
| Prijatá, príjemca nie je v sieti | stav Príjemca nie je v sieti |
| Odmietnutá (validácia, oprávnenie) | stav Chyba so správou služby; faktúru možno opraviť a odoslať znova |
| Bez odpovede alebo s nejasnou odpoveďou (výpadok siete, chyba brány) | stav Chyba; ďalší pokus zopakuje tú istú požiadavku, faktúra sa teda neodošle dvakrát |

Preferovaný spôsob odberateľa sa nastavuje na kontakte (záložka Účtovníctvo, Odosielanie faktúr).

- Faktúra ide len jednou sieťou. Ak je zaškrtnutá doručovacia služba aj pripojenie Odoo na
  Peppol, faktúra pôjde cez doručovaciu službu a sprievodca Odoslať na to upozorní.
- Faktúry v dávke sa odovzdávajú a ukladajú po jednej: odmietnutá faktúra nezastaví ostatné.
  Ak je služba nedostupná, zvyšok dávky sa neskúša.
- Odovzdaný súbor je priložený k záznamu o odovzdaní v histórii faktúry.

## 6. Stav doručenia

Plánovaná akcia („SAPI-SK: update delivery statuses“) sa služby pýta na stav faktúr v stave
Odovzdaná, 100 faktúr na jeden beh, od tých, na ktoré sa pýtala najdávnejšie. Spustí sa päť
minút po odovzdaní a potom každé štyri hodiny.

| Stav vo Verteco | Stav v eFakturuj | Stav faktúry |
| --- | --- | --- |
| pending, submitted | ACCEPTED, PROCESSING | Odovzdaná |
| delivered | SENT | Doručená |
| undeliverable | | Príjemca nie je v sieti |
| rejected | | Odmietnutá príjemcom |
| failed | FAILED | Chyba |

Rozhranie stavov nie je súčasťou spoločného jadra SAPI-SK, každá služba má vlastné. Pri voľbe
„Iná služba SAPI-SK“ ostáva faktúra v stave Odovzdaná; doručenie je potom viditeľné v portáli
služby.

Odmietnutú faktúru alebo faktúru v stave Chyba možno vrátiť do návrhu a odoslať znova. Faktúru,
ktorá bola odovzdaná, doručená alebo označená ako nedoručiteľná, možno opraviť len dobropisom.

## 7. Príjem e-faktúr

Plánovaná akcia „SAPI-SK: retrieve received e-invoices“ beží každú hodinu:

1. vypíše doklady firmy, ktorých prevzatie ešte nebolo potvrdené,
2. každý stiahne a štandardným importom Odoo z neho vytvorí návrh dodávateľskej faktúry
   (dodávateľ, riadky, dane, dátum dodania),
3. potvrdí prevzatie dokladu u služby, aby ho neponúkala znova.

Doklad, ktorý služba odmietne vydať, sa preskočí a ostatné sa stiahnu. Doklad, ktorý už bol
naimportovaný, sa iba potvrdí. Pôvodné XML je uložené na faktúre. Doklad,
ktorý import nedokáže načítať, ostane ako prázdny návrh faktúry s priloženým súborom.

## 8. Volania rozhrania

| Volanie | Použitie |
| --- | --- |
| `POST /auth/token` | prístupový token (OAuth2 client credentials, telo JSON) |
| `POST /document/send` | odovzdanie e-faktúry s hlavičkou `Idempotency-Key` |
| `GET /document/receive?status=RECEIVED` | zoznam prijatých dokladov, stránkovanie cez `pageToken` |
| `GET /document/receive/{id}` | obsah prijatého dokladu |
| `POST /document/receive/{id}/acknowledge` | potvrdenie prevzatia |
| `GET /document/sent/{id}` | stav doručenia (Verteco) |
| `GET /document/status/{id}` | stav doručenia (eFakturuj) |

Každé volanie dokladov nesie hlavičky `Authorization: Bearer` a `X-Peppol-Participant-Id`.

## 9. Rozsah

Modul neregistruje firmu u služby ani na Finančnej správe, nehlási údaje Finančnému
riaditeľstvu (robí to služba), nespracúva webhooky, pred odoslaním neoveruje príjemcu v sieti
a nesťahuje doručenku. Stav doručenia sa sleduje len pre Verteco a eFakturuj.

## 10. Technický popis

| Súbor | Obsah |
| --- | --- |
| `tools/sapi_client.py` | HTTP klient rozhrania: token, volania, chybové správy |
| `models/res_company.py` | nastavenie spojenia firmy |
| `models/res_config_settings.py` | nastavenia a test spojenia |
| `models/res_partner.py` | spôsob odoslania „cez slovenskú doručovaciu službu“ |
| `models/account_move_send.py` | odovzdanie faktúry v procese odosielania |
| `models/account_move.py` | polia stavu, aktualizácia stavu, sťahovanie prijatých dokladov |
| `data/ir_cron_data.xml` | dve plánované akcie |
| `data/neutralize.sql` | odstráni spojenie z neutralizovanej kópie databázy |
| `tests/` | testy so simulovanou službou |

### Testy

```
odoo-bin -d <db> -i l10n_sk_edi_sapi --test-enable --test-tags /l10n_sk_edi_sapi --stop-after-init
```

Testy nahrádzajú službu pripravenými odpoveďami a nevolajú nič mimo Odoo.

Modul bol spustený aj proti testovacím prostrediam Verteco a eFakturuj, ktoré sú pripojené na
testovaciu sieť Peppol. Faktúra a dobropis odoslané z Odoo prešli zo stavu Odovzdaná do stavu
Doručená a doklady prijaté odberateľom sa stiahli ako návrh dodávateľskej faktúry a návrh
dodávateľského dobropisu s dodávateľom, riadkami a daňami a ich prevzatie sa potvrdilo.
