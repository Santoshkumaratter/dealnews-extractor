-- DealNews Scraper MySQL Schema
-- Database: dealnews

CREATE DATABASE IF NOT EXISTS dealnews CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE dealnews;

-- Main deals table with all required fields
CREATE TABLE IF NOT EXISTS deals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dealid VARCHAR(100),
    recid VARCHAR(100),
    url VARCHAR(500) UNIQUE NOT NULL,
    title TEXT NOT NULL,
    price VARCHAR(100),
    promo VARCHAR(255),
    category VARCHAR(100) DEFAULT 'general',
    store VARCHAR(100),
    deal VARCHAR(255),
    dealplus VARCHAR(255),
    deallink VARCHAR(500),
    dealtext VARCHAR(255),
    dealhover VARCHAR(255),
    published VARCHAR(100),
    popularity VARCHAR(50),
    staffpick VARCHAR(50),
    detail TEXT,
    raw_html TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_dealid (dealid),
    INDEX idx_category (category),
    INDEX idx_store (store),
    INDEX idx_created_at (created_at),
    INDEX idx_price (price(20))
);

-- Images table for multiple images per deal
CREATE TABLE IF NOT EXISTS deal_images (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dealid VARCHAR(100),
    imageurl VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_dealid (dealid)
);

-- Categories table for multiple categories per deal
CREATE TABLE IF NOT EXISTS deal_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dealid VARCHAR(100),
    category_name VARCHAR(100),
    category_url VARCHAR(500),
    category_title VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_dealid (dealid)
);

-- Related deals table
CREATE TABLE IF NOT EXISTS related_deals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dealid VARCHAR(100),
    relatedurl VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_dealid (dealid)
);

-- Grant permissions to user
GRANT ALL PRIVILEGES ON dealnews.* TO 'dealnews_user'@'%';
GRANT ALL PRIVILEGES ON dealnews.* TO 'dealnews_user'@'localhost';
FLUSH PRIVILEGES;
