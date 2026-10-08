-- =============================================================================
-- Corrección única: ventas, facturas de cliente y cobros registrados en USD en lugar de GTQ
-- (base quetzalmart del servidor, 2026-10-08).
--
-- Causa: al instalar contabilidad en una base nueva, Odoo cargó primero el plan genérico
-- (generic_coa), que dejó la compañía y la lista de precios "Predeterminado" en USD.
-- La compañía se corrigió a GTQ antes de la carga, pero la lista de precios no, y con ella
-- se crearon las 150 ventas, las 12 cotizaciones, las 150 facturas y los 113 cobros.
--
-- Por qué es seguro: no existe ninguna tasa de cambio USD, así que todo se registró a tasa 1
-- (amount_currency = balance en todas las líneas). Cambiar la moneda no altera ningún monto
-- ni el cuadre contable. No se tocan res_country ni payment_method_res_currency_rel, que son
-- datos maestros correctos.
--
-- Ejecutar con respaldo previo, desde PROYECTO/infra:
--   docker compose exec -T db pg_dump -U odoo -Fc quetzalmart > ~/respaldo_antes_moneda.dump
--   docker compose exec -T db psql -U odoo -d quetzalmart -v ON_ERROR_STOP=1 < ../evidencias/carga_masiva/correccion_moneda_gtq.sql
--   docker compose restart odoo
-- =============================================================================
BEGIN;

CREATE TEMP TABLE m AS
SELECT (SELECT id FROM res_currency WHERE name = 'USD') AS usd,
       (SELECT id FROM res_currency WHERE name = 'GTQ') AS gtq;

-- Seguridad: abortar si hay tasas USD o líneas con montos distintos (no sería solo un cambio de etiqueta)
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM res_currency_rate WHERE currency_id = (SELECT usd FROM m)) THEN
    RAISE EXCEPTION 'Hay tasas de cambio USD: la corrección no es solo de etiqueta';
  END IF;
  IF EXISTS (SELECT 1 FROM account_move_line WHERE currency_id = (SELECT usd FROM m) AND amount_currency <> balance) THEN
    RAISE EXCEPTION 'Hay líneas en USD con amount_currency distinto de balance';
  END IF;
END $$;

UPDATE product_pricelist         SET currency_id        = (SELECT gtq FROM m) WHERE currency_id        = (SELECT usd FROM m);
UPDATE sale_order                SET currency_id        = (SELECT gtq FROM m) WHERE currency_id        = (SELECT usd FROM m);
UPDATE sale_order_line           SET currency_id        = (SELECT gtq FROM m) WHERE currency_id        = (SELECT usd FROM m);
UPDATE account_move              SET currency_id        = (SELECT gtq FROM m) WHERE currency_id        = (SELECT usd FROM m);
UPDATE account_move_line         SET currency_id        = (SELECT gtq FROM m) WHERE currency_id        = (SELECT usd FROM m);
UPDATE account_payment           SET currency_id        = (SELECT gtq FROM m) WHERE currency_id        = (SELECT usd FROM m);
UPDATE account_partial_reconcile SET debit_currency_id  = (SELECT gtq FROM m) WHERE debit_currency_id  = (SELECT usd FROM m);
UPDATE account_partial_reconcile SET credit_currency_id = (SELECT gtq FROM m) WHERE credit_currency_id = (SELECT usd FROM m);

-- Resultado esperado: 0 registros en USD en documentos de venta, facturación y cobro
SELECT 'sale_order' AS tabla, count(*) AS en_usd FROM sale_order WHERE currency_id = (SELECT usd FROM m)
UNION ALL SELECT 'account_move',      count(*) FROM account_move      WHERE currency_id = (SELECT usd FROM m)
UNION ALL SELECT 'account_move_line', count(*) FROM account_move_line WHERE currency_id = (SELECT usd FROM m)
UNION ALL SELECT 'account_payment',   count(*) FROM account_payment   WHERE currency_id = (SELECT usd FROM m)
UNION ALL SELECT 'product_pricelist', count(*) FROM product_pricelist WHERE currency_id = (SELECT usd FROM m);

COMMIT;
