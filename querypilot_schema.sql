-- QueryPilot Phase 1: e-commerce/retail schema (PostgreSQL)
-- 28 tables, created in dependency order so it runs top to bottom.
-- Run:  psql -d querypilot -f querypilot_schema.sql

BEGIN;

-- ============================================================
-- EMPLOYEES / OPS
-- ============================================================

CREATE TABLE departments (
    department_id   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name            TEXT NOT NULL UNIQUE
);

CREATE TABLE employees (
    employee_id     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    department_id   BIGINT NOT NULL REFERENCES departments(department_id),
    manager_id      BIGINT REFERENCES employees(employee_id),
    first_name      TEXT NOT NULL,
    last_name       TEXT NOT NULL,
    email           TEXT NOT NULL UNIQUE,
    job_title       TEXT NOT NULL,
    hired_at        DATE NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE stores (
    store_id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name            TEXT NOT NULL,
    city            TEXT NOT NULL,
    country         TEXT NOT NULL,
    manager_id      BIGINT REFERENCES employees(employee_id),
    opened_at       DATE NOT NULL
);

CREATE TABLE employee_store_assignments (
    employee_id     BIGINT NOT NULL REFERENCES employees(employee_id),
    store_id        BIGINT NOT NULL REFERENCES stores(store_id),
    started_at      DATE NOT NULL,
    ended_at        DATE,
    PRIMARY KEY (employee_id, store_id, started_at),
    CHECK (ended_at IS NULL OR ended_at >= started_at)
);

-- ============================================================
-- CATALOG / INVENTORY
-- ============================================================

CREATE TABLE categories (
    category_id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    parent_category_id  BIGINT REFERENCES categories(category_id),
    name                TEXT NOT NULL
);

CREATE TABLE suppliers (
    supplier_id     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name            TEXT NOT NULL,
    country         TEXT NOT NULL,
    contact_email   TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE products (
    product_id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category_id     BIGINT NOT NULL REFERENCES categories(category_id),
    supplier_id     BIGINT NOT NULL REFERENCES suppliers(supplier_id),
    name            TEXT NOT NULL,
    description     TEXT,
    brand           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_discontinued BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE product_variants (
    variant_id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id      BIGINT NOT NULL REFERENCES products(product_id),
    sku             TEXT NOT NULL UNIQUE,
    size            TEXT,
    color           TEXT,
    current_price   NUMERIC(12,2) NOT NULL CHECK (current_price >= 0),
    unit_cost       NUMERIC(12,2) NOT NULL CHECK (unit_cost >= 0)
);

CREATE TABLE warehouses (
    warehouse_id    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name            TEXT NOT NULL,
    city            TEXT NOT NULL,
    country         TEXT NOT NULL
);

CREATE TABLE inventory_stock (
    warehouse_id    BIGINT NOT NULL REFERENCES warehouses(warehouse_id),
    variant_id      BIGINT NOT NULL REFERENCES product_variants(variant_id),
    quantity_on_hand INTEGER NOT NULL CHECK (quantity_on_hand >= 0),
    reorder_level   INTEGER NOT NULL DEFAULT 0,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (warehouse_id, variant_id)
);

CREATE TABLE price_history (
    price_history_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    variant_id      BIGINT NOT NULL REFERENCES product_variants(variant_id),
    price           NUMERIC(12,2) NOT NULL CHECK (price >= 0),
    effective_from  DATE NOT NULL,
    effective_to    DATE,
    CHECK (effective_to IS NULL OR effective_to >= effective_from)
);

-- ============================================================
-- CUSTOMERS
-- ============================================================

CREATE TABLE customers (
    customer_id     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    first_name      TEXT NOT NULL,
    last_name       TEXT NOT NULL,
    email           TEXT NOT NULL UNIQUE,
    phone           TEXT,
    signed_up_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    acquisition_channel TEXT,            -- e.g. 'organic', 'paid_search', 'referral'
    is_active       BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE customer_addresses (
    address_id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id     BIGINT NOT NULL REFERENCES customers(customer_id),
    line1           TEXT NOT NULL,
    line2           TEXT,
    city            TEXT NOT NULL,
    state           TEXT,
    postal_code     TEXT,
    country         TEXT NOT NULL,
    is_default      BOOLEAN NOT NULL DEFAULT FALSE
);

-- ============================================================
-- SALES
-- ============================================================

CREATE TABLE shipping_carriers (
    carrier_id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name            TEXT NOT NULL UNIQUE
);

CREATE TABLE orders (
    order_id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id     BIGINT NOT NULL REFERENCES customers(customer_id),
    store_id        BIGINT REFERENCES stores(store_id),            -- NULL = online order
    shipping_address_id BIGINT REFERENCES customer_addresses(address_id),
    status          TEXT NOT NULL CHECK (status IN
                      ('pending','paid','shipped','delivered','cancelled','returned')),
    ordered_at      TIMESTAMPTZ NOT NULL,
    shipping_fee    NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (shipping_fee >= 0)
);

CREATE TABLE order_items (
    order_item_id   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id        BIGINT NOT NULL REFERENCES orders(order_id),
    variant_id      BIGINT NOT NULL REFERENCES product_variants(variant_id),
    quantity        INTEGER NOT NULL CHECK (quantity > 0),
    unit_price      NUMERIC(12,2) NOT NULL CHECK (unit_price >= 0),  -- price paid at purchase time
    discount_amount NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (discount_amount >= 0)
);

-- ============================================================
-- PAYMENTS / FULFILLMENT
-- ============================================================

CREATE TABLE payments (
    payment_id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id        BIGINT NOT NULL REFERENCES orders(order_id),
    method          TEXT NOT NULL CHECK (method IN ('card','upi','paypal','bank_transfer','cod')),
    amount          NUMERIC(12,2) NOT NULL CHECK (amount >= 0),
    status          TEXT NOT NULL CHECK (status IN ('pending','succeeded','failed')),
    paid_at         TIMESTAMPTZ
);

CREATE TABLE refunds (
    refund_id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    payment_id      BIGINT NOT NULL REFERENCES payments(payment_id),
    order_item_id   BIGINT REFERENCES order_items(order_item_id),  -- NULL = whole-order refund
    amount          NUMERIC(12,2) NOT NULL CHECK (amount > 0),
    reason          TEXT,
    refunded_at     TIMESTAMPTZ NOT NULL
);

CREATE TABLE shipments (
    shipment_id     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id        BIGINT NOT NULL REFERENCES orders(order_id),
    carrier_id      BIGINT NOT NULL REFERENCES shipping_carriers(carrier_id),
    warehouse_id    BIGINT NOT NULL REFERENCES warehouses(warehouse_id),
    tracking_number TEXT,
    shipped_at      TIMESTAMPTZ,
    delivered_at    TIMESTAMPTZ
);

CREATE TABLE shipment_items (
    shipment_id     BIGINT NOT NULL REFERENCES shipments(shipment_id),
    order_item_id   BIGINT NOT NULL REFERENCES order_items(order_item_id),
    quantity        INTEGER NOT NULL CHECK (quantity > 0),
    PRIMARY KEY (shipment_id, order_item_id)
);

-- ============================================================
-- CUSTOMER ENGAGEMENT
-- ============================================================

CREATE TABLE reviews (
    review_id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id     BIGINT NOT NULL REFERENCES customers(customer_id),
    product_id      BIGINT NOT NULL REFERENCES products(product_id),
    order_item_id   BIGINT REFERENCES order_items(order_item_id),
    rating          SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    title           TEXT,
    body            TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE support_tickets (
    ticket_id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id     BIGINT NOT NULL REFERENCES customers(customer_id),
    order_id        BIGINT REFERENCES orders(order_id),
    assigned_employee_id BIGINT REFERENCES employees(employee_id),
    subject         TEXT NOT NULL,
    status          TEXT NOT NULL CHECK (status IN ('open','in_progress','resolved','closed')),
    priority        TEXT NOT NULL CHECK (priority IN ('low','medium','high')),
    opened_at       TIMESTAMPTZ NOT NULL,
    resolved_at     TIMESTAMPTZ
);

CREATE TABLE support_ticket_messages (
    message_id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ticket_id       BIGINT NOT NULL REFERENCES support_tickets(ticket_id),
    sender_type     TEXT NOT NULL CHECK (sender_type IN ('customer','employee')),
    body            TEXT NOT NULL,
    sent_at         TIMESTAMPTZ NOT NULL
);

CREATE TABLE wishlists (
    customer_id     BIGINT NOT NULL REFERENCES customers(customer_id),
    product_id      BIGINT NOT NULL REFERENCES products(product_id),
    added_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (customer_id, product_id)
);

-- ============================================================
-- MARKETING
-- ============================================================

CREATE TABLE marketing_campaigns (
    campaign_id     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name            TEXT NOT NULL,
    channel         TEXT NOT NULL,            -- e.g. 'email', 'social', 'search'
    budget          NUMERIC(12,2) NOT NULL CHECK (budget >= 0),
    start_date      DATE NOT NULL,
    end_date        DATE,
    CHECK (end_date IS NULL OR end_date >= start_date)
);

CREATE TABLE campaign_customers (
    campaign_id     BIGINT NOT NULL REFERENCES marketing_campaigns(campaign_id),
    customer_id     BIGINT NOT NULL REFERENCES customers(customer_id),
    sent_at         TIMESTAMPTZ NOT NULL,
    opened          BOOLEAN NOT NULL DEFAULT FALSE,
    clicked         BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (campaign_id, customer_id)
);

CREATE TABLE promotions (
    promotion_id    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    campaign_id     BIGINT REFERENCES marketing_campaigns(campaign_id),
    code            TEXT NOT NULL UNIQUE,
    discount_type   TEXT NOT NULL CHECK (discount_type IN ('percent','fixed')),
    discount_value  NUMERIC(12,2) NOT NULL CHECK (discount_value > 0),
    valid_from      DATE NOT NULL,
    valid_to        DATE,
    CHECK (valid_to IS NULL OR valid_to >= valid_from)
);

CREATE TABLE promotion_redemptions (
    redemption_id   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    promotion_id    BIGINT NOT NULL REFERENCES promotions(promotion_id),
    order_id        BIGINT NOT NULL REFERENCES orders(order_id),
    customer_id     BIGINT NOT NULL REFERENCES customers(customer_id),
    redeemed_at     TIMESTAMPTZ NOT NULL
);

-- ============================================================
-- INDEXES on foreign keys used in the most common joins
-- (Postgres does not index FK columns automatically.)
-- ============================================================

CREATE INDEX idx_orders_customer      ON orders(customer_id);
CREATE INDEX idx_orders_ordered_at    ON orders(ordered_at);
CREATE INDEX idx_order_items_order    ON order_items(order_id);
CREATE INDEX idx_order_items_variant  ON order_items(variant_id);
CREATE INDEX idx_variants_product     ON product_variants(product_id);
CREATE INDEX idx_products_category    ON products(category_id);
CREATE INDEX idx_reviews_product      ON reviews(product_id);
CREATE INDEX idx_payments_order       ON payments(order_id);
CREATE INDEX idx_shipments_order      ON shipments(order_id);
CREATE INDEX idx_tickets_customer     ON support_tickets(customer_id);

COMMIT;
