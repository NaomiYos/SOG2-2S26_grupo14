-- ============================================================
-- SOG2 - Practica 1 - Grupo 14
-- Esquema relacional para PostgreSQL (Supabase)
-- ============================================================
-- Modelo: 1 fila del CSV = 1 cliente + 1 registro de compra.
-- Se normaliza en 3 catalogos + 2 tablas de datos para que el
-- modelo sea genuinamente relacional (evita la penalizacion
-- del -20% por "no utilizar una base de datos relacional").
-- ============================================================

DROP TABLE IF EXISTS registro_compra CASCADE;
DROP TABLE IF EXISTS cliente        CASCADE;
DROP TABLE IF EXISTS metodo_pago    CASCADE;
DROP TABLE IF EXISTS navegador      CASCADE;
DROP TABLE IF EXISTS genero         CASCADE;

-- ------------------------------------------------------------
-- CATALOGOS
-- ------------------------------------------------------------
-- Existen para que las consultas devuelvan etiquetas legibles
-- en vez de codigos. Importa para el agente de IA: responder
-- "Tarjeta de Credito" es mejor que responder "MetodoPago 1".

CREATE TABLE genero (
    id          SMALLINT PRIMARY KEY,
    descripcion VARCHAR(20) NOT NULL UNIQUE
);

INSERT INTO genero (id, descripcion) VALUES
    (0, 'Masculino'),
    (1, 'Femenino');

CREATE TABLE metodo_pago (
    id             SMALLINT PRIMARY KEY,
    descripcion    VARCHAR(40) NOT NULL UNIQUE,

);

-- El valor 0 agrupa efectivo Y contra entrega en una sola
-- categoria (aclaracion del catedratico). Tarjeta de credito
-- y debito NO se consideran contra entrega.
INSERT INTO metodo_pago (id, descripcion) VALUES
    (0, 'Efectivo / Contra entrega'),
    (1, 'Tarjeta de Credito'),
    (2, 'Tarjeta de Debito');

CREATE TABLE navegador (
    id          SMALLINT PRIMARY KEY,
    descripcion VARCHAR(30) NOT NULL UNIQUE,
    es_online   BOOLEAN NOT NULL
);

INSERT INTO navegador (id, descripcion, es_online) VALUES
    (0, 'Tienda Fisica', FALSE),
    (1, 'Navegador 1',   TRUE),
    (2, 'Navegador 2',   TRUE),
    (3, 'Navegador 3',   TRUE),
    (4, 'Navegador 4',   TRUE);

-- ------------------------------------------------------------
-- CLIENTE
-- ------------------------------------------------------------
-- Atributos propios del cliente y sus acumulados historicos.
-- venta_total y n_compras son agregados del cliente, NO del
-- registro de compra: por eso viven aqui y no alla.

CREATE TABLE cliente (
    id_cliente   INTEGER PRIMARY KEY,
    edad         SMALLINT      NOT NULL,
    genero_id    SMALLINT      NOT NULL REFERENCES genero (id),
    venta_total  NUMERIC(12,2) NOT NULL,
    n_compras    INTEGER       NOT NULL,

    CONSTRAINT chk_edad        CHECK (edad BETWEEN 0 AND 120),
    CONSTRAINT chk_venta_total CHECK (venta_total >= 0),
    CONSTRAINT chk_n_compras   CHECK (n_compras >= 0)
);

-- ------------------------------------------------------------
-- REGISTRO_COMPRA
-- ------------------------------------------------------------
-- La transaccion puntual asociada al cliente: la unica parte
-- del dataset que tiene fecha. Se modela como tabla aparte
-- porque describe un evento, no al cliente.
--
-- id_cliente es UNIQUE porque en este dataset hay exactamente
-- un registro por cliente. Si en el futuro llega el detalle
-- transaccional completo, basta con quitar ese UNIQUE y la
-- relacion pasa a 1:N sin rehacer nada.

CREATE TABLE registro_compra (
    id_compra      SERIAL PRIMARY KEY,
    id_cliente     INTEGER       NOT NULL UNIQUE
                                 REFERENCES cliente (id_cliente)
                                 ON DELETE CASCADE,
    fecha_compra   DATE          NOT NULL,
    monto_compra   NUMERIC(12,3) NOT NULL,
    metodo_pago_id SMALLINT      NOT NULL REFERENCES metodo_pago (id),
    tiempo         INTEGER       NOT NULL,
    navegador_id   SMALLINT      NOT NULL REFERENCES navegador (id),
    boletin        BOOLEAN       NOT NULL,
    vale           BOOLEAN       NOT NULL,

    CONSTRAINT chk_monto  CHECK (monto_compra >= 0),
    CONSTRAINT chk_tiempo CHECK (tiempo >= 0)
);

-- ------------------------------------------------------------
-- INDICES
-- ------------------------------------------------------------
-- El agente de IA consulta por mes, metodo de pago y navegador
-- de forma repetida. Sin indices cada pregunta hace un scan
-- completo de 6500 filas contra la nube: se siente lento en la
-- demo de calificacion.

CREATE INDEX idx_compra_fecha    ON registro_compra (fecha_compra);
CREATE INDEX idx_compra_metodo   ON registro_compra (metodo_pago_id);
CREATE INDEX idx_compra_naveg    ON registro_compra (navegador_id);
CREATE INDEX idx_compra_promos   ON registro_compra (boletin, vale);
CREATE INDEX idx_cliente_genero  ON cliente (genero_id);
CREATE INDEX idx_cliente_edad    ON cliente (edad);

-- ------------------------------------------------------------
-- VISTA DESNORMALIZADA
-- ------------------------------------------------------------
-- Comodidad para el analisis: el Rol 2 y el Rol 3 consultan
-- esta vista en vez de escribir el mismo JOIN de 5 tablas una
-- y otra vez. La base sigue siendo relacional; la vista es
-- solo una capa de lectura.

CREATE OR REPLACE VIEW v_ventas AS
SELECT
    c.id_cliente,
    c.edad,
    g.descripcion                AS genero,
    c.genero_id,
    c.venta_total,
    c.n_compras,
    r.fecha_compra,
    EXTRACT(MONTH FROM r.fecha_compra)::INT AS mes,
    TO_CHAR(r.fecha_compra, 'TMMonth')      AS nombre_mes,
    r.monto_compra,
    mp.descripcion               AS metodo_pago,
    r.metodo_pago_id,
    mp.es_contraentrega,
    r.tiempo,
    n.descripcion                AS navegador,
    r.navegador_id,
    n.es_online,
    r.boletin,
    r.vale
FROM cliente c
JOIN genero          g  ON g.id  = c.genero_id
JOIN registro_compra r  ON r.id_cliente = c.id_cliente
JOIN metodo_pago     mp ON mp.id = r.metodo_pago_id
JOIN navegador       n  ON n.id  = r.navegador_id;
