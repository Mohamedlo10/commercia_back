-- =====================================================
-- COMMERCIA - Script SQL Complet pour Supabase
-- Version: 2.0
-- Description: Système de gestion commerciale avec POS, Stock, Réservations
-- =====================================================

-- Activer l'extension UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- 1. TABLES DE BASE
-- =====================================================

-- MAGASINS
CREATE TABLE stores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    address TEXT,
    phone VARCHAR(20),
    email VARCHAR(255),
    siret VARCHAR(50),
    logo_url TEXT,
    currency VARCHAR(3) DEFAULT 'XOF',
    timezone VARCHAR(50) DEFAULT 'Africa/Abidjan',
    vat_rate DECIMAL(5,2) DEFAULT 0.00,
    tax_config JSONB DEFAULT '{}',
    settings JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- UTILISATEURS
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL, -- admin, manager, cashier, seller
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- EMPLOYÉS (extension de users avec infos RH)
CREATE TABLE employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    store_id UUID REFERENCES stores(id),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    national_id VARCHAR(50),
    phone VARCHAR(20),
    email VARCHAR(255),
    address TEXT,
    position VARCHAR(100) NOT NULL,
    hire_date DATE NOT NULL,
    base_salary DECIMAL(15,2),
    status VARCHAR(50) DEFAULT 'active', -- active, on_leave, terminated
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- PERMISSIONS
CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role VARCHAR(50) NOT NULL,
    resource VARCHAR(100) NOT NULL, -- products, orders, cash_register, etc.
    actions JSONB NOT NULL, -- {"read": true, "create": true, "update": false, "delete": false}
    created_at TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- 2. CLIENTS
-- =====================================================

CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id),
    code VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    company_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    client_type VARCHAR(50) DEFAULT 'individual', -- individual, company
    loyalty_points INT DEFAULT 0,
    credit_limit DECIMAL(15,2) DEFAULT 0,
    current_debt DECIMAL(15,2) DEFAULT 0,
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- 3. CATÉGORIES ET PRODUITS
-- =====================================================

-- CATÉGORIES
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    parent_id UUID REFERENCES categories(id),
    level INT DEFAULT 0,
    path VARCHAR(500), -- pour la hiérarchie (ex: "1/5/12")
    image_url TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- PRODUITS
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id),
    sku VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category_id UUID REFERENCES categories(id),
    product_type VARCHAR(50) NOT NULL, -- retail, clothing, electronics, hardware, service

    -- Prix
    purchase_price DECIMAL(15,2),
    selling_price DECIMAL(15,2) NOT NULL,
    wholesale_price DECIMAL(15,2),

    -- Gestion des unités multiples
    has_multiple_units BOOLEAN DEFAULT false,
    primary_unit VARCHAR(50) DEFAULT 'pièce', -- carton, boîte, etc.
    secondary_unit VARCHAR(50), -- pièce, unité
    units_per_primary INT DEFAULT 1, -- nombre d'unités secondaires dans une unité primaire

    -- Stock
    track_stock BOOLEAN DEFAULT true,
    stock_quantity_primary DECIMAL(15,3) DEFAULT 0,
    stock_quantity_secondary DECIMAL(15,3) DEFAULT 0,
    stock_alert_threshold DECIMAL(15,3) DEFAULT 10,

    -- Variantes
    has_variants BOOLEAN DEFAULT false,
    variant_attributes JSONB, -- {"size": ["S", "M", "L"], "color": ["red", "blue"]}

    -- Attributs spécifiques par type
    attributes JSONB DEFAULT '{}',

    -- Images
    images JSONB DEFAULT '[]', -- ["url1", "url2"]

    -- Taxes
    tax_rate DECIMAL(5,2) DEFAULT 0,

    -- E-commerce
    is_published_online BOOLEAN DEFAULT false,
    online_description TEXT,

    -- Métadonnées
    barcode VARCHAR(100),
    brand VARCHAR(100),
    supplier_reference VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- VARIANTES DE PRODUITS
CREATE TABLE product_variants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    sku VARCHAR(100) UNIQUE NOT NULL,
    variant_name VARCHAR(255) NOT NULL, -- "Rouge - M"
    attributes JSONB NOT NULL, -- {"color": "red", "size": "M"}

    -- Prix spécifique (optionnel)
    selling_price DECIMAL(15,2),
    purchase_price DECIMAL(15,2),

    -- Stock spécifique
    stock_quantity DECIMAL(15,3) DEFAULT 0,
    stock_alert_threshold DECIMAL(15,3) DEFAULT 5,

    -- Métadonnées
    barcode VARCHAR(100),
    image_url TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- 4. MOUVEMENTS DE STOCK
-- =====================================================

CREATE TABLE stock_movements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id),
    product_id UUID REFERENCES products(id),
    variant_id UUID REFERENCES product_variants(id),

    movement_type VARCHAR(50) NOT NULL, -- in, out, adjustment, return, transfer
    quantity DECIMAL(15,3) NOT NULL,
    unit VARCHAR(50) NOT NULL, -- primary, secondary

    -- Référence
    reference_type VARCHAR(50), -- order, refund, manual, import
    reference_id UUID,

    -- Métadonnées
    reason TEXT,
    performed_by UUID REFERENCES users(id),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- 5. COMMANDES ET VENTES
-- =====================================================

-- COMMANDES
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id),
    order_number VARCHAR(50) UNIQUE NOT NULL,

    -- Client
    client_id UUID REFERENCES clients(id),
    client_name VARCHAR(255),
    client_phone VARCHAR(20),

    -- Type de commande
    order_type VARCHAR(50) NOT NULL, -- pos, online, reservation, location
    order_source VARCHAR(50) DEFAULT 'pos', -- pos, ecommerce

    -- Montants
    subtotal DECIMAL(15,2) NOT NULL,
    discount_amount DECIMAL(15,2) DEFAULT 0,
    promo_code_discount DECIMAL(15,2) DEFAULT 0,
    loyalty_points_used INT DEFAULT 0,
    loyalty_discount DECIMAL(15,2) DEFAULT 0,
    tax_amount DECIMAL(15,2) DEFAULT 0,
    total_amount DECIMAL(15,2) NOT NULL,

    -- Paiement
    montant_paye DECIMAL(15,2) DEFAULT 0,
    montant_restant DECIMAL(15,2) DEFAULT 0,
    statut_paiement VARCHAR(50) DEFAULT 'Non Payer', -- Payer, Non Payer, Partiellement, Rembourser, Partiellement Rembourser

    -- Statut
    status VARCHAR(50) DEFAULT 'pending', -- pending, confirmed, completed, cancelled

    -- Métadonnées
    notes TEXT,
    created_by UUID REFERENCES users(id),
    cash_register_session_id UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ARTICLES DE COMMANDE
CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID REFERENCES orders(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id),
    variant_id UUID REFERENCES product_variants(id),

    product_name VARCHAR(255) NOT NULL,
    variant_name VARCHAR(255),
    sku VARCHAR(100),

    -- Quantité et unité
    quantity DECIMAL(15,3) NOT NULL,
    unit VARCHAR(50) NOT NULL, -- primary, secondary

    -- Prix
    unit_price DECIMAL(15,2) NOT NULL,
    discount_amount DECIMAL(15,2) DEFAULT 0,
    tax_rate DECIMAL(5,2) DEFAULT 0,
    tax_amount DECIMAL(15,2) DEFAULT 0,
    total_price DECIMAL(15,2) NOT NULL,

    created_at TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- 6. TRANSACTIONS ET PAIEMENTS
-- =====================================================

-- MÉTHODES DE PAIEMENT
CREATE TABLE payment_methods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id),
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL, -- cash, card, mobile_money, check, bank_transfer, credit
    is_active BOOLEAN DEFAULT true,
    requires_reference BOOLEAN DEFAULT false,
    config JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- TRANSACTIONS
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id),
    order_id UUID REFERENCES orders(id),
    client_id UUID REFERENCES clients(id),

    transaction_type VARCHAR(50) NOT NULL, -- sale, refund, expense, deposit, caution, deduction, final_payment
    payment_method_id UUID REFERENCES payment_methods(id),

    amount DECIMAL(15,2) NOT NULL,
    reference VARCHAR(255),

    status VARCHAR(50) DEFAULT 'pending', -- pending, completed, failed, cancelled

    -- Métadonnées
    notes TEXT,
    processed_by UUID REFERENCES users(id),
    cash_register_session_id UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- 7. CAISSE
-- =====================================================

-- SESSIONS DE CAISSE
CREATE TABLE cash_register_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id),
    session_number VARCHAR(50) UNIQUE NOT NULL,

    opened_by UUID REFERENCES users(id),
    closed_by UUID REFERENCES users(id),

    opening_amount DECIMAL(15,2) NOT NULL,
    closing_amount DECIMAL(15,2),
    expected_amount DECIMAL(15,2),
    difference DECIMAL(15,2),

    status VARCHAR(50) DEFAULT 'open', -- open, closed

    opened_at TIMESTAMP DEFAULT NOW(),
    closed_at TIMESTAMP,

    notes TEXT,
    closing_notes TEXT
);

-- DÉTAILS DE CAISSE PAR MÉTHODE
CREATE TABLE cash_register_details (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES cash_register_sessions(id) ON DELETE CASCADE,
    payment_method_id UUID REFERENCES payment_methods(id),

    opening_amount DECIMAL(15,2) DEFAULT 0,
    total_in DECIMAL(15,2) DEFAULT 0, -- entrées (ventes, dépôts)
    total_out DECIMAL(15,2) DEFAULT 0, -- sorties (remboursements, retraits)
    expected_closing DECIMAL(15,2) DEFAULT 0,
    actual_closing DECIMAL(15,2),
    difference DECIMAL(15,2),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- 8. CODES PROMO
-- =====================================================

CREATE TABLE promo_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id),
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,

    discount_type VARCHAR(20) NOT NULL, -- percentage, fixed_amount
    discount_value DECIMAL(15,2) NOT NULL,

    min_order_amount DECIMAL(15,2),

    start_date DATE NOT NULL,
    end_date DATE NOT NULL,

    max_uses INT,
    max_uses_per_client INT,
    current_uses INT DEFAULT 0,

    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- HISTORIQUE D'UTILISATION DES CODES PROMO
CREATE TABLE promo_code_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    promo_code_id UUID REFERENCES promo_codes(id),
    order_id UUID REFERENCES orders(id),
    client_id UUID REFERENCES clients(id),
    discount_applied DECIMAL(15,2) NOT NULL,
    used_at TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- 9. RÉSERVATIONS ET LOCATIONS
-- =====================================================

CREATE TABLE reservations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id),
    reservation_number VARCHAR(50) UNIQUE NOT NULL,

    -- Client
    client_id UUID REFERENCES clients(id),
    client_name VARCHAR(255) NOT NULL,
    client_phone VARCHAR(20) NOT NULL,

    -- Type
    reservation_type VARCHAR(50) NOT NULL, -- service, location

    -- Dates
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP,
    duration_hours DECIMAL(10,2),

    -- Montants
    total_amount DECIMAL(15,2) NOT NULL,
    caution_amount DECIMAL(15,2) DEFAULT 0,
    amount_paid DECIMAL(15,2) DEFAULT 0,
    amount_remaining DECIMAL(15,2) DEFAULT 0,

    -- Statut
    status VARCHAR(50) DEFAULT 'pending', -- pending, confirmed, in_progress, completed, cancelled
    payment_status VARCHAR(50) DEFAULT 'Non Payer',

    -- Métadonnées
    notes TEXT,
    order_id UUID REFERENCES orders(id),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ARTICLES DE RÉSERVATION
CREATE TABLE reservation_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reservation_id UUID REFERENCES reservations(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id),
    variant_id UUID REFERENCES product_variants(id),

    product_name VARCHAR(255) NOT NULL,
    quantity DECIMAL(15,3) NOT NULL,
    unit_price DECIMAL(15,2) NOT NULL,
    total_price DECIMAL(15,2) NOT NULL,

    created_at TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- 10. HISTORIQUES
-- =====================================================

-- HISTORIQUE DETTE CLIENT
CREATE TABLE client_debt_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    order_id UUID REFERENCES orders(id),
    transaction_id UUID REFERENCES transactions(id),

    movement_type VARCHAR(50) NOT NULL, -- debt_increase, payment
    amount DECIMAL(15,2) NOT NULL,
    balance_before DECIMAL(15,2) NOT NULL,
    balance_after DECIMAL(15,2) NOT NULL,

    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- HISTORIQUE POINTS FIDÉLITÉ
CREATE TABLE loyalty_points_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    order_id UUID REFERENCES orders(id),

    movement_type VARCHAR(50) NOT NULL, -- earned, redeemed, expired, adjusted
    points INT NOT NULL,
    balance_before INT NOT NULL,
    balance_after INT NOT NULL,

    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- 11. LOGS ET AUDIT
-- =====================================================

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id),
    user_id UUID REFERENCES users(id),

    action VARCHAR(100) NOT NULL, -- create, update, delete
    entity_type VARCHAR(100) NOT NULL, -- product, order, client, etc.
    entity_id UUID,

    old_values JSONB,
    new_values JSONB,

    ip_address VARCHAR(45),
    user_agent TEXT,

    created_at TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- 12. INDEXES POUR PERFORMANCE
-- =====================================================

-- Stores
CREATE INDEX idx_stores_is_active ON stores(is_active);

-- Users
CREATE INDEX idx_users_store_id ON users(store_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- Employees
CREATE INDEX idx_employees_user_id ON employees(user_id);
CREATE INDEX idx_employees_store_id ON employees(store_id);
CREATE INDEX idx_employees_status ON employees(status);

-- Clients
CREATE INDEX idx_clients_store_id ON clients(store_id);
CREATE INDEX idx_clients_code ON clients(code);
CREATE INDEX idx_clients_phone ON clients(phone);
CREATE INDEX idx_clients_email ON clients(email);

-- Categories
CREATE INDEX idx_categories_store_id ON categories(store_id);
CREATE INDEX idx_categories_parent_id ON categories(parent_id);
CREATE INDEX idx_categories_path ON categories(path);

-- Products
CREATE INDEX idx_products_store_id ON products(store_id);
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_category_id ON products(category_id);
CREATE INDEX idx_products_product_type ON products(product_type);
CREATE INDEX idx_products_is_active ON products(is_active);
CREATE INDEX idx_products_barcode ON products(barcode);

-- Product Variants
CREATE INDEX idx_variants_product_id ON product_variants(product_id);
CREATE INDEX idx_variants_sku ON product_variants(sku);
CREATE INDEX idx_variants_barcode ON product_variants(barcode);

-- Stock Movements
CREATE INDEX idx_stock_movements_store_id ON stock_movements(store_id);
CREATE INDEX idx_stock_movements_product_id ON stock_movements(product_id);
CREATE INDEX idx_stock_movements_variant_id ON stock_movements(variant_id);
CREATE INDEX idx_stock_movements_created_at ON stock_movements(created_at);

-- Orders
CREATE INDEX idx_orders_store_id ON orders(store_id);
CREATE INDEX idx_orders_order_number ON orders(order_number);
CREATE INDEX idx_orders_client_id ON orders(client_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_statut_paiement ON orders(statut_paiement);
CREATE INDEX idx_orders_created_at ON orders(created_at);
CREATE INDEX idx_orders_created_by ON orders(created_by);

-- Order Items
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
CREATE INDEX idx_order_items_variant_id ON order_items(variant_id);

-- Transactions
CREATE INDEX idx_transactions_store_id ON transactions(store_id);
CREATE INDEX idx_transactions_order_id ON transactions(order_id);
CREATE INDEX idx_transactions_client_id ON transactions(client_id);
CREATE INDEX idx_transactions_transaction_type ON transactions(transaction_type);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_created_at ON transactions(created_at);

-- Cash Register Sessions
CREATE INDEX idx_cash_sessions_store_id ON cash_register_sessions(store_id);
CREATE INDEX idx_cash_sessions_status ON cash_register_sessions(status);
CREATE INDEX idx_cash_sessions_opened_at ON cash_register_sessions(opened_at);

-- Promo Codes
CREATE INDEX idx_promo_codes_store_id ON promo_codes(store_id);
CREATE INDEX idx_promo_codes_code ON promo_codes(code);
CREATE INDEX idx_promo_codes_is_active ON promo_codes(is_active);

-- Reservations
CREATE INDEX idx_reservations_store_id ON reservations(store_id);
CREATE INDEX idx_reservations_client_id ON reservations(client_id);
CREATE INDEX idx_reservations_status ON reservations(status);
CREATE INDEX idx_reservations_start_date ON reservations(start_date);

-- Audit Logs
CREATE INDEX idx_audit_logs_store_id ON audit_logs(store_id);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_entity_type ON audit_logs(entity_type);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

-- =====================================================
-- 13. TRIGGERS
-- =====================================================

-- TRIGGER 1: Auto-génération du code client
CREATE OR REPLACE FUNCTION generate_client_code()
RETURNS TRIGGER AS $$
DECLARE
    v_count INT;
    v_code VARCHAR(50);
BEGIN
    IF NEW.code IS NULL OR NEW.code = '' THEN
        SELECT COUNT(*) + 1 INTO v_count FROM clients WHERE store_id = NEW.store_id;
        v_code := 'CLI-' || LPAD(v_count::TEXT, 6, '0');

        -- Vérifier l'unicité
        WHILE EXISTS (SELECT 1 FROM clients WHERE code = v_code) LOOP
            v_count := v_count + 1;
            v_code := 'CLI-' || LPAD(v_count::TEXT, 6, '0');
        END LOOP;

        NEW.code := v_code;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_generate_client_code
BEFORE INSERT ON clients
FOR EACH ROW
EXECUTE FUNCTION generate_client_code();

-- TRIGGER 2: Auto-génération du numéro de commande
CREATE OR REPLACE FUNCTION generate_order_number()
RETURNS TRIGGER AS $$
DECLARE
    v_count INT;
    v_date VARCHAR(8);
    v_number VARCHAR(50);
BEGIN
    IF NEW.order_number IS NULL OR NEW.order_number = '' THEN
        v_date := TO_CHAR(NOW(), 'YYYYMMDD');
        SELECT COUNT(*) + 1 INTO v_count
        FROM orders
        WHERE store_id = NEW.store_id
        AND order_number LIKE 'CMD-' || v_date || '%';

        v_number := 'CMD-' || v_date || '-' || LPAD(v_count::TEXT, 4, '0');

        -- Vérifier l'unicité
        WHILE EXISTS (SELECT 1 FROM orders WHERE order_number = v_number) LOOP
            v_count := v_count + 1;
            v_number := 'CMD-' || v_date || '-' || LPAD(v_count::TEXT, 4, '0');
        END LOOP;

        NEW.order_number := v_number;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_generate_order_number
BEFORE INSERT ON orders
FOR EACH ROW
EXECUTE FUNCTION generate_order_number();

-- TRIGGER 3: Mise à jour automatique du statut de paiement avec gestion des remboursements
CREATE OR REPLACE FUNCTION update_order_payment_status()
RETURNS TRIGGER AS $$
DECLARE
    v_total_paid DECIMAL(15,2);
    v_total_refunded DECIMAL(15,2);
    v_net_paid DECIMAL(15,2);
    v_order_total DECIMAL(15,2);
BEGIN
    -- Récupérer le total de la commande
    SELECT total_amount INTO v_order_total
    FROM orders WHERE id = NEW.order_id;

    -- Calculer le total payé (transactions de type 'sale')
    SELECT COALESCE(SUM(amount), 0) INTO v_total_paid
    FROM transactions
    WHERE order_id = NEW.order_id
    AND transaction_type IN ('sale', 'deposit', 'final_payment')
    AND status = 'completed';

    -- Calculer le total remboursé (transactions de type 'refund')
    SELECT COALESCE(SUM(ABS(amount)), 0) INTO v_total_refunded
    FROM transactions
    WHERE order_id = NEW.order_id
    AND transaction_type = 'refund'
    AND status = 'completed';

    -- Calculer le montant net payé
    v_net_paid := v_total_paid - v_total_refunded;

    -- Mettre à jour la commande
    UPDATE orders
    SET
        montant_paye = v_net_paid,
        montant_restant = v_order_total - v_net_paid,
        statut_paiement = CASE
            WHEN v_total_refunded >= v_order_total THEN 'Rembourser'
            WHEN v_total_refunded > 0 AND v_net_paid > 0 THEN 'Partiellement Rembourser'
            WHEN v_net_paid >= v_order_total THEN 'Payer'
            WHEN v_net_paid > 0 THEN 'Partiellement'
            ELSE 'Non Payer'
        END,
        updated_at = NOW()
    WHERE id = NEW.order_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_order_payment_status
AFTER INSERT OR UPDATE ON transactions
FOR EACH ROW
WHEN (NEW.status = 'completed')
EXECUTE FUNCTION update_order_payment_status();

-- TRIGGER 4: Déduction automatique du stock lors d'une commande
CREATE OR REPLACE FUNCTION deduct_stock_on_order()
RETURNS TRIGGER AS $$
DECLARE
    v_item RECORD;
    v_product RECORD;
BEGIN
    -- Vérifier que la commande est confirmée ou complétée
    IF NEW.status IN ('confirmed', 'completed')
       AND (OLD.status IS NULL OR OLD.status NOT IN ('confirmed', 'completed')) THEN

        FOR v_item IN
            SELECT * FROM order_items WHERE order_id = NEW.id
        LOOP
            -- Récupérer les infos du produit
            SELECT * INTO v_product FROM products WHERE id = v_item.product_id;

            IF v_product.track_stock THEN
                IF v_item.variant_id IS NOT NULL THEN
                    -- Produit avec variante
                    UPDATE product_variants
                    SET stock_quantity = stock_quantity - v_item.quantity
                    WHERE id = v_item.variant_id;

                ELSE
                    -- Produit sans variante
                    IF v_item.unit = 'primary' THEN
                        UPDATE products
                        SET stock_quantity_primary = stock_quantity_primary - v_item.quantity
                        WHERE id = v_item.product_id;

                        -- Si multi-unités, synchroniser
                        IF v_product.has_multiple_units THEN
                            UPDATE products
                            SET stock_quantity_secondary = stock_quantity_primary * units_per_primary
                            WHERE id = v_item.product_id;
                        END IF;
                    ELSE
                        UPDATE products
                        SET stock_quantity_secondary = stock_quantity_secondary - v_item.quantity
                        WHERE id = v_item.product_id;

                        -- Si multi-unités, synchroniser
                        IF v_product.has_multiple_units THEN
                            UPDATE products
                            SET stock_quantity_primary = stock_quantity_secondary / units_per_primary
                            WHERE id = v_item.product_id;
                        END IF;
                    END IF;
                END IF;

                -- Enregistrer le mouvement de stock
                INSERT INTO stock_movements (
                    store_id, product_id, variant_id, movement_type,
                    quantity, unit, reference_type, reference_id, performed_by
                ) VALUES (
                    NEW.store_id, v_item.product_id, v_item.variant_id, 'out',
                    v_item.quantity, v_item.unit, 'order', NEW.id, NEW.created_by
                );
            END IF;
        END LOOP;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_deduct_stock_on_order
AFTER INSERT OR UPDATE ON orders
FOR EACH ROW
EXECUTE FUNCTION deduct_stock_on_order();

-- TRIGGER 5: Réintégration du stock lors d'un remboursement
CREATE OR REPLACE FUNCTION restock_after_refund()
RETURNS TRIGGER AS $$
DECLARE
    v_order RECORD;
    v_item RECORD;
    v_product RECORD;
    v_loyalty_earned INT;
BEGIN
    IF NEW.transaction_type = 'refund' AND NEW.status = 'completed' THEN
        -- Récupérer la commande
        SELECT * INTO v_order FROM orders WHERE id = NEW.order_id;

        -- Réintégrer le stock pour chaque article
        FOR v_item IN
            SELECT * FROM order_items WHERE order_id = NEW.order_id
        LOOP
            SELECT * INTO v_product FROM products WHERE id = v_item.product_id;

            IF v_product.track_stock THEN
                IF v_item.variant_id IS NOT NULL THEN
                    -- Produit avec variante
                    UPDATE product_variants
                    SET stock_quantity = stock_quantity + v_item.quantity
                    WHERE id = v_item.variant_id;

                ELSE
                    -- Produit sans variante
                    IF v_item.unit = 'primary' THEN
                        UPDATE products
                        SET stock_quantity_primary = stock_quantity_primary + v_item.quantity
                        WHERE id = v_item.product_id;

                        IF v_product.has_multiple_units THEN
                            UPDATE products
                            SET stock_quantity_secondary = stock_quantity_primary * units_per_primary
                            WHERE id = v_item.product_id;
                        END IF;
                    ELSE
                        UPDATE products
                        SET stock_quantity_secondary = stock_quantity_secondary + v_item.quantity
                        WHERE id = v_item.product_id;

                        IF v_product.has_multiple_units THEN
                            UPDATE products
                            SET stock_quantity_primary = stock_quantity_secondary / units_per_primary
                            WHERE id = v_item.product_id;
                        END IF;
                    END IF;
                END IF;

                -- Enregistrer le mouvement de stock
                INSERT INTO stock_movements (
                    store_id, product_id, variant_id, movement_type,
                    quantity, unit, reference_type, reference_id, performed_by
                ) VALUES (
                    NEW.store_id, v_item.product_id, v_item.variant_id, 'in',
                    v_item.quantity, v_item.unit, 'refund', NEW.id, NEW.processed_by
                );
            END IF;
        END LOOP;

        -- Déduire les points de fidélité si la commande était payée
        IF v_order.client_id IS NOT NULL AND v_order.statut_paiement IN ('Payer', 'Partiellement') THEN
            -- Calculer les points qui avaient été attribués (1 point par 1000 XOF)
            v_loyalty_earned := FLOOR(v_order.total_amount / 1000);

            UPDATE clients
            SET loyalty_points = GREATEST(0, loyalty_points - v_loyalty_earned)
            WHERE id = v_order.client_id;

            -- Enregistrer l'historique
            INSERT INTO loyalty_points_history (
                client_id, order_id, movement_type, points,
                balance_before, balance_after, notes
            )
            SELECT
                v_order.client_id,
                v_order.id,
                'deducted',
                -v_loyalty_earned,
                loyalty_points + v_loyalty_earned,
                loyalty_points,
                'Déduction suite au remboursement de la commande ' || v_order.order_number
            FROM clients WHERE id = v_order.client_id;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_restock_after_refund
AFTER INSERT OR UPDATE ON transactions
FOR EACH ROW
EXECUTE FUNCTION restock_after_refund();

-- TRIGGER 6: Attribution automatique des points de fidélité
CREATE OR REPLACE FUNCTION award_loyalty_points()
RETURNS TRIGGER AS $$
DECLARE
    v_points_earned INT;
    v_current_points INT;
BEGIN
    -- Attribuer des points uniquement si la commande est complètement payée
    IF NEW.statut_paiement = 'Payer'
       AND (OLD.statut_paiement IS NULL OR OLD.statut_paiement != 'Payer')
       AND NEW.client_id IS NOT NULL THEN

        -- Calculer les points (1 point par 1000 XOF dépensé)
        v_points_earned := FLOOR((NEW.total_amount - NEW.loyalty_discount) / 1000);

        IF v_points_earned > 0 THEN
            -- Mettre à jour les points du client
            UPDATE clients
            SET loyalty_points = loyalty_points + v_points_earned
            WHERE id = NEW.client_id
            RETURNING loyalty_points INTO v_current_points;

            -- Enregistrer l'historique
            INSERT INTO loyalty_points_history (
                client_id, order_id, movement_type, points,
                balance_before, balance_after, notes
            ) VALUES (
                NEW.client_id,
                NEW.id,
                'earned',
                v_points_earned,
                v_current_points - v_points_earned,
                v_current_points,
                'Points gagnés pour la commande ' || NEW.order_number
            );
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_award_loyalty_points
AFTER UPDATE ON orders
FOR EACH ROW
EXECUTE FUNCTION award_loyalty_points();

-- TRIGGER 7: Gestion de la dette client
CREATE OR REPLACE FUNCTION manage_client_debt()
RETURNS TRIGGER AS $$
DECLARE
    v_order RECORD;
    v_old_debt DECIMAL(15,2);
BEGIN
    IF NEW.transaction_type IN ('sale', 'deposit', 'final_payment')
       AND NEW.status = 'completed'
       AND NEW.order_id IS NOT NULL THEN

        SELECT * INTO v_order FROM orders WHERE id = NEW.order_id;

        IF v_order.client_id IS NOT NULL THEN
            -- Récupérer la dette actuelle
            SELECT current_debt INTO v_old_debt FROM clients WHERE id = v_order.client_id;

            -- Vérifier si c'était une vente à crédit qui est maintenant payée
            IF v_order.statut_paiement = 'Payer' THEN
                -- Réduire la dette
                UPDATE clients
                SET current_debt = GREATEST(0, current_debt - NEW.amount)
                WHERE id = v_order.client_id;

                -- Enregistrer l'historique
                INSERT INTO client_debt_history (
                    client_id, order_id, transaction_id, movement_type,
                    amount, balance_before, balance_after, notes
                )
                SELECT
                    v_order.client_id,
                    v_order.id,
                    NEW.id,
                    'payment',
                    NEW.amount,
                    v_old_debt,
                    current_debt,
                    'Paiement pour la commande ' || v_order.order_number
                FROM clients WHERE id = v_order.client_id;
            END IF;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_manage_client_debt
AFTER INSERT OR UPDATE ON transactions
FOR EACH ROW
EXECUTE FUNCTION manage_client_debt();

-- TRIGGER 8: Mise à jour des timestamps
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Appliquer le trigger sur les tables pertinentes
CREATE TRIGGER trigger_update_timestamp_stores
BEFORE UPDATE ON stores FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trigger_update_timestamp_users
BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trigger_update_timestamp_employees
BEFORE UPDATE ON employees FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trigger_update_timestamp_clients
BEFORE UPDATE ON clients FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trigger_update_timestamp_categories
BEFORE UPDATE ON categories FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trigger_update_timestamp_products
BEFORE UPDATE ON products FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trigger_update_timestamp_product_variants
BEFORE UPDATE ON product_variants FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trigger_update_timestamp_orders
BEFORE UPDATE ON orders FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trigger_update_timestamp_transactions
BEFORE UPDATE ON transactions FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trigger_update_timestamp_reservations
BEFORE UPDATE ON reservations FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trigger_update_timestamp_promo_codes
BEFORE UPDATE ON promo_codes FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- =====================================================
-- 14. ROW LEVEL SECURITY (RLS)
-- =====================================================

-- Activer RLS sur toutes les tables principales
ALTER TABLE stores ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE employees ENABLE ROW LEVEL SECURITY;
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_variants ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE order_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE cash_register_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE reservations ENABLE ROW LEVEL SECURITY;
ALTER TABLE promo_codes ENABLE ROW LEVEL SECURITY;
ALTER TABLE stock_movements ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Politiques RLS: Les utilisateurs ne peuvent accéder qu'aux données de leur magasin
-- Note: Ces politiques seront créées côté Supabase avec l'authentification JWT

-- =====================================================
-- 15. DONNÉES INITIALES (OPTIONNEL)
-- =====================================================

-- Méthodes de paiement par défaut
-- INSERT INTO payment_methods (store_id, name, type) VALUES
-- ((SELECT id FROM stores LIMIT 1), 'Espèces', 'cash'),
-- ((SELECT id FROM stores LIMIT 1), 'Carte bancaire', 'card'),
-- ((SELECT id FROM stores LIMIT 1), 'Mobile Money', 'mobile_money'),
-- ((SELECT id FROM stores LIMIT 1), 'Chèque', 'check'),
-- ((SELECT id FROM stores LIMIT 1), 'Virement', 'bank_transfer'),
-- ((SELECT id FROM stores LIMIT 1), 'Crédit', 'credit');

-- =====================================================
-- FIN DU SCRIPT
-- =====================================================

-- Version: 2.0
-- Date: 2026-01-12
-- Status: Prêt pour l'exécution sur Supabase
