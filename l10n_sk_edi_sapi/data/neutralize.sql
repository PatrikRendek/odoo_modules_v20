-- A neutralized copy of the database must not reach the delivery service of the production.
UPDATE res_company
   SET l10n_sk_sapi_url = NULL,
       l10n_sk_sapi_client_id = NULL,
       l10n_sk_sapi_client_secret = NULL;
