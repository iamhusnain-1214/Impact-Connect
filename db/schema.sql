-- ImpactConnect Pakistan - Database Schema
-- Run this once to set up the database: mysql -u root -p < schema.sql

CREATE DATABASE IF NOT EXISTS impactconnect;
USE impactconnect;

-- ==========================
-- USERS
-- ==========================
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('donor', 'ngo_admin', 'admin') NOT NULL DEFAULT 'donor',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================
-- NGOs
-- ==========================
CREATE TABLE IF NOT EXISTS ngos (
    ngo_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    mission TEXT,
    city VARCHAR(100),
    province VARCHAR(100),
    contact VARCHAR(100),
    website VARCHAR(255),
    social_links VARCHAR(255),
    verified BOOLEAN DEFAULT FALSE,
    created_by INT,                     -- FK to users (ngo_admin who registered it)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE SET NULL
);

-- ==========================
-- CATEGORIES
-- ==========================
CREATE TABLE IF NOT EXISTS categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

-- Many-to-many: NGOs <-> Categories
CREATE TABLE IF NOT EXISTS ngo_categories (
    ngo_id INT NOT NULL,
    category_id INT NOT NULL,
    PRIMARY KEY (ngo_id, category_id),
    FOREIGN KEY (ngo_id) REFERENCES ngos(ngo_id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE CASCADE
);

-- ==========================
-- REVIEWS
-- ==========================
CREATE TABLE IF NOT EXISTS reviews (
    review_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    ngo_id INT NOT NULL,
    rating TINYINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (ngo_id) REFERENCES ngos(ngo_id) ON DELETE CASCADE
);

-- ==========================
-- VOLUNTEER OPPORTUNITIES
-- ==========================
CREATE TABLE IF NOT EXISTS volunteer_opportunities (
    opportunity_id INT AUTO_INCREMENT PRIMARY KEY,
    ngo_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    event_date DATE,
    location VARCHAR(150),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ngo_id) REFERENCES ngos(ngo_id) ON DELETE CASCADE
);

-- ==========================
-- CAMPAIGNS
-- ==========================
CREATE TABLE IF NOT EXISTS campaigns (
    campaign_id INT AUTO_INCREMENT PRIMARY KEY,
    ngo_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    active BOOLEAN DEFAULT TRUE,
    start_date DATE,
    end_date DATE,
    FOREIGN KEY (ngo_id) REFERENCES ngos(ngo_id) ON DELETE CASCADE
);

-- ==========================
-- VERIFICATION REQUESTS (admin approval queue)
-- ==========================
CREATE TABLE IF NOT EXISTS verification_requests (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    ngo_id INT NOT NULL,
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP NULL,
    FOREIGN KEY (ngo_id) REFERENCES ngos(ngo_id) ON DELETE CASCADE
);

-- ==========================
-- FAVORITES (users saving NGOs)
-- ==========================
CREATE TABLE IF NOT EXISTS favorites (
    user_id INT NOT NULL,
    ngo_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, ngo_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (ngo_id) REFERENCES ngos(ngo_id) ON DELETE CASCADE
);

-- ==========================
-- SEED DATA: Categories
-- ==========================
INSERT INTO categories (name) VALUES
('Education'), ('Healthcare'), ('Flood Relief'), ('Ramadan'), ('Food'),
('Water'), ('Climate'), ('Women'), ('Children'), ('Orphans'),
('Disability'), ('Animal Welfare'), ('Disaster Relief'), ('Blood Donation'),
('Mental Health'), ('Legal Aid'), ('Senior Citizens')
ON DUPLICATE KEY UPDATE name = name;

-- ==========================
-- SEED DATA: Sample NGOs (for testing before real data entry)
-- ==========================
INSERT INTO ngos (name, description, mission, city, province, contact, website, verified) VALUES
('Roshni Trust', 'Provides free primary education to underprivileged children in rural Sindh.', 'Educate every child regardless of income.', 'Hyderabad', 'Sindh', '0300-1234567', 'https://example.com/roshni', TRUE),
('Sailaab Relief', 'Emergency flood relief, food and shelter distribution across Punjab and Sindh.', 'Rapid response to disaster-hit families.', 'Multan', 'Punjab', '0300-7654321', 'https://example.com/sailaab', TRUE),
('Garam Kapray Foundation', 'Collects and distributes winter clothing to low-income families.', 'No child should be cold in winter.', 'Lahore', 'Punjab', '0321-1112223', 'https://example.com/garamkapray', FALSE);

-- Link sample NGOs to categories
INSERT INTO ngo_categories (ngo_id, category_id)
SELECT n.ngo_id, c.category_id FROM ngos n, categories c
WHERE (n.name = 'Roshni Trust' AND c.name = 'Education')
   OR (n.name = 'Sailaab Relief' AND c.name IN ('Flood Relief', 'Disaster Relief', 'Food'))
   OR (n.name = 'Garam Kapray Foundation' AND c.name = 'Children');
