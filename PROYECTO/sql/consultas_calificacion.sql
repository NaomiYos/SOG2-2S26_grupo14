-- =============================================================================
-- QuetzalMart · Consultas SQL para la calificación (PostgreSQL, base quetzalmart)
-- Ejecutar completo:  ver PROYECTO/sql/README.md
-- Los nombres traducibles de Odoo se guardan como JSON: se lee el español y, si
-- no existe, el inglés (coalesce(name->>'es_419', name->>'en_US')).
-- =============================================================================


-- -----------------------------------------------------------------------------
-- 0. RESUMEN: cada requisito del enunciado contra su mínimo
-- -----------------------------------------------------------------------------
SELECT requisito, minimo, cargado, CASE WHEN cargado >= minimo THEN 'CUMPLE' ELSE 'FALTA' END AS estado
FROM (
    SELECT 1 AS orden, 'Ventas confirmadas' AS requisito, 150 AS minimo,
           (SELECT count(*) FROM sale_order WHERE state = 'sale') AS cargado
    UNION ALL SELECT 2, 'Cotizaciones a clientes y proveedores', 20,
           (SELECT count(*) FROM sale_order WHERE state IN ('draft', 'sent'))
         + (SELECT count(*) FROM purchase_order WHERE state IN ('draft', 'sent'))
    UNION ALL SELECT 3, 'Empleados', 35,
           (SELECT count(*) FROM hr_employee WHERE active AND name <> 'Administrator')
    UNION ALL SELECT 4, 'Cargos', 6, (SELECT count(*) FROM hr_job)
    UNION ALL SELECT 5, 'Departamentos', 5, (SELECT count(*) FROM hr_department WHERE active)
    UNION ALL SELECT 6, 'Compras confirmadas', 100,
           (SELECT count(*) FROM purchase_order WHERE state = 'purchase')
    UNION ALL SELECT 7, 'Facturas de compras (proveedor)', 100,
           (SELECT count(*) FROM account_move WHERE move_type = 'in_invoice' AND state = 'posted')
    UNION ALL SELECT 8, 'Materiales de operación', 60,
           (SELECT count(*) FROM product_template WHERE default_code LIKE 'MAT-%')
    UNION ALL SELECT 9, 'Facturas de venta (cliente)', 50,
           (SELECT count(*) FROM account_move WHERE move_type = 'out_invoice' AND state = 'posted')
    UNION ALL SELECT 10, 'Documentos en el gestor documental', 15, (SELECT count(*) FROM dms_file)
) r
ORDER BY orden;


-- -----------------------------------------------------------------------------
-- 1. VENTAS
-- -----------------------------------------------------------------------------

-- 1.1 Ventas confirmadas con cliente, sucursal, total y estado de factura
SELECT so.name                         AS venta,
       so.date_order::date             AS fecha,
       p.name                          AS cliente,
       w.code                          AS sucursal,
       so.amount_untaxed               AS subtotal,
       so.amount_tax                   AS iva,
       so.amount_total                 AS total,
       so.delivery_status              AS entrega,
       so.invoice_status               AS facturacion
FROM sale_order so
JOIN res_partner p      ON p.id = so.partner_id
JOIN stock_warehouse w  ON w.id = so.warehouse_id
WHERE so.state = 'sale'
ORDER BY so.date_order;

-- 1.2 Variedad: clientes y productos distintos en las ventas
SELECT count(DISTINCT so.id)         AS ventas,
       count(DISTINCT so.partner_id) AS clientes_distintos,
       count(DISTINCT sol.product_id) AS productos_distintos,
       sum(sol.product_uom_qty)       AS unidades_vendidas
FROM sale_order so
JOIN sale_order_line sol ON sol.order_id = so.id
WHERE so.state = 'sale';

-- 1.3 Ventas por sucursal
SELECT w.code AS sucursal, count(*) AS ventas, sum(so.amount_total) AS total_q
FROM sale_order so
JOIN stock_warehouse w ON w.id = so.warehouse_id
WHERE so.state = 'sale'
GROUP BY w.code
ORDER BY total_q DESC;

-- 1.4 Productos más vendidos (top 10)
SELECT pt.default_code AS codigo,
       coalesce(pt.name->>'es_419', pt.name->>'en_US') AS producto,
       sum(sol.product_uom_qty) AS unidades,
       sum(sol.price_total)     AS total_q
FROM sale_order_line sol
JOIN sale_order so        ON so.id = sol.order_id AND so.state = 'sale'
JOIN product_product pp  ON pp.id = sol.product_id
JOIN product_template pt ON pt.id = pp.product_tmpl_id
GROUP BY pt.default_code, producto
ORDER BY unidades DESC
LIMIT 10;


-- -----------------------------------------------------------------------------
-- 2. COTIZACIONES (a clientes y a proveedores)
-- -----------------------------------------------------------------------------
SELECT 'Cliente'   AS dirigida_a, so.name AS documento, so.date_order::date AS fecha,
       p.name AS contacto, so.state AS estado, so.amount_total AS total
FROM sale_order so
JOIN res_partner p ON p.id = so.partner_id
WHERE so.state IN ('draft', 'sent')
UNION ALL
SELECT 'Proveedor', po.name, po.date_order::date, p.name, po.state, po.amount_total
FROM purchase_order po
JOIN res_partner p ON p.id = po.partner_id
WHERE po.state IN ('draft', 'sent')
ORDER BY dirigida_a, fecha;


-- -----------------------------------------------------------------------------
-- 3. EMPLEADOS, CARGOS Y DEPARTAMENTOS
-- -----------------------------------------------------------------------------

-- 3.1 Empleados con cargo, departamento, sucursal y jefe directo
SELECT e.name AS empleado,
       coalesce(j.name->>'es_419', j.name->>'en_US') AS cargo,
       coalesce(d.name->>'es_419', d.name->>'en_US') AS departamento,
       wl.name   AS sucursal,
       jefe.name AS jefe_directo,
       e.work_email AS correo
FROM hr_employee e
LEFT JOIN hr_job j            ON j.id = e.job_id
LEFT JOIN hr_department d     ON d.id = e.department_id
LEFT JOIN hr_work_location wl ON wl.id = e.work_location_id
LEFT JOIN hr_employee jefe    ON jefe.id = e.parent_id
WHERE e.active AND e.name <> 'Administrator'
ORDER BY departamento, cargo, e.name;

-- 3.2 Cargos y cuántos empleados tiene cada uno
SELECT coalesce(j.name->>'es_419', j.name->>'en_US') AS cargo,
       coalesce(d.name->>'es_419', d.name->>'en_US') AS departamento,
       count(e.id) AS empleados
FROM hr_job j
LEFT JOIN hr_department d ON d.id = j.department_id
LEFT JOIN hr_employee e   ON e.job_id = j.id AND e.active
GROUP BY cargo, departamento
ORDER BY departamento, cargo;

-- 3.3 Departamentos con su jefe y número de empleados
SELECT coalesce(d.name->>'es_419', d.name->>'en_US') AS departamento,
       m.name AS jefe,
       count(e.id) AS empleados
FROM hr_department d
LEFT JOIN hr_employee m ON m.id = d.manager_id
LEFT JOIN hr_employee e ON e.department_id = d.id AND e.active AND e.name <> 'Administrator'
WHERE d.active
GROUP BY departamento, m.name
ORDER BY departamento;


-- -----------------------------------------------------------------------------
-- 4. COMPRAS Y FACTURAS DE PROVEEDOR
-- -----------------------------------------------------------------------------

-- 4.1 Compras con su recepción y su factura
SELECT po.name               AS compra,
       po.date_order::date   AS fecha,
       p.name                AS proveedor,
       spt.warehouse_code    AS sucursal,
       po.amount_total       AS total,
       po.receipt_status     AS recepcion,
       f.name                AS factura,
       f.ref                 AS factura_proveedor,
       f.payment_state       AS pago
FROM purchase_order po
JOIN res_partner p ON p.id = po.partner_id
JOIN LATERAL (SELECT w.code AS warehouse_code
              FROM stock_picking_type t JOIN stock_warehouse w ON w.id = t.warehouse_id
              WHERE t.id = po.picking_type_id) spt ON true
LEFT JOIN account_move f ON f.invoice_origin = po.name AND f.move_type = 'in_invoice'
WHERE po.state = 'purchase'
ORDER BY po.date_order;

-- 4.2 Facturas de proveedor: publicadas, pagadas y pendientes
SELECT count(*)                                                        AS facturas,
       count(*) FILTER (WHERE payment_state IN ('paid', 'in_payment'))  AS pagadas,
       count(*) FILTER (WHERE payment_state = 'not_paid')               AS pendientes,
       sum(amount_total)                                                AS total_q,
       sum(amount_residual)                                             AS por_pagar_q
FROM account_move
WHERE move_type = 'in_invoice' AND state = 'posted';


-- -----------------------------------------------------------------------------
-- 5. MATERIALES DE OPERACIÓN Y EXISTENCIAS POR SUCURSAL
-- -----------------------------------------------------------------------------

-- 5.1 Materiales con categoría, costo y proveedor
SELECT pt.default_code AS codigo,
       coalesce(pt.name->>'es_419', pt.name->>'en_US') AS material,
       c.name                                           AS categoria,
       (pp.standard_price->>'1')::numeric               AS costo,   -- costo por compañía (id 1)
       prov.name                                        AS proveedor
FROM product_template pt
JOIN product_product pp ON pp.product_tmpl_id = pt.id
JOIN product_category c ON c.id = pt.categ_id
LEFT JOIN LATERAL (SELECT rp.name FROM product_supplierinfo si JOIN res_partner rp ON rp.id = si.partner_id
                   WHERE si.product_tmpl_id = pt.id LIMIT 1) prov ON true
WHERE pt.default_code LIKE 'MAT-%'
ORDER BY pt.default_code;

-- 5.2 Existencias de materiales en cada sucursal
SELECT w.code AS sucursal, count(DISTINCT q.product_id) AS materiales_distintos, sum(q.quantity) AS unidades
FROM stock_quant q
JOIN stock_location l    ON l.id = q.location_id AND l.usage = 'internal'
JOIN stock_warehouse w   ON w.id = l.warehouse_id
JOIN product_product pp  ON pp.id = q.product_id
JOIN product_template pt ON pt.id = pp.product_tmpl_id
WHERE pt.default_code LIKE 'MAT-%' AND q.quantity > 0
GROUP BY w.code
ORDER BY w.code;


-- -----------------------------------------------------------------------------
-- 6. FACTURAS DE VENTA (los PDF están en PROYECTO/facturas_pdf/<número>.pdf)
-- -----------------------------------------------------------------------------
SELECT f.name                         AS factura,
       replace(f.name, '/', '_') || '.pdf' AS archivo_pdf,
       f.invoice_date                 AS fecha,
       f.invoice_date_due             AS vencimiento,
       p.name                         AS cliente,
       f.invoice_origin               AS venta,
       f.amount_total                 AS total,
       f.payment_state                AS cobro
FROM account_move f
JOIN res_partner p ON p.id = f.partner_id
WHERE f.move_type = 'out_invoice' AND f.state = 'posted'
ORDER BY f.name;


-- -----------------------------------------------------------------------------
-- 7. GESTOR DOCUMENTAL
-- -----------------------------------------------------------------------------

-- 7.1 Documentos por carpeta con sus etiquetas
SELECT d.name AS carpeta,
       f.name AS documento,
       string_agg(coalesce(t.name->>'es_419', t.name->>'en_US'), ', ' ORDER BY t.name->>'en_US') AS etiquetas
FROM dms_file f
JOIN dms_directory d ON d.id = f.directory_id
LEFT JOIN dms_file_tag_rel r ON r.fid = f.id
LEFT JOIN dms_tag t ON t.id = r.tid
GROUP BY d.name, f.name
ORDER BY d.name, f.name;

-- 7.2 Etiquetas por categoría y cuántos documentos tiene cada una
SELECT coalesce(c.name->>'es_419', c.name->>'en_US') AS categoria,
       coalesce(t.name->>'es_419', t.name->>'en_US') AS etiqueta,
       count(r.fid) AS documentos
FROM dms_tag t
JOIN dms_category c ON c.id = t.category_id
LEFT JOIN dms_file_tag_rel r ON r.tid = t.id
GROUP BY categoria, etiqueta
ORDER BY categoria, etiqueta;

-- 7.3 Documentos también adjuntos a su registro del ERP
SELECT a.res_model AS registro, count(*) AS adjuntos
FROM ir_attachment a
WHERE a.name LIKE 'Factura\_%' OR a.name LIKE 'Contrato\_%'
GROUP BY a.res_model;


-- =============================================================================
-- 8. BLOQUE 2: TIENDA EN LÍNEA Y RPA
-- Agregar aquí las consultas de los pedidos web y de lo cargado por el RPA
-- (base quetzalmart_rpa y clientes/productos creados en Odoo).
-- =============================================================================
