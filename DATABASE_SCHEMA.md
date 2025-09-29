# DealNews Scraper - Database Schema

## Overview
The DealNews scraper uses a **normalized database structure** with separate tables for different types of data to ensure data integrity and efficient querying.

## Database Tables

### 1. `deals` - Main Deals Table
**Primary table containing all deal information**

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT AUTO_INCREMENT PRIMARY KEY | Unique deal ID |
| `dealid` | VARCHAR(100) | DealNews deal ID |
| `recid` | VARCHAR(100) | DealNews record ID |
| `url` | VARCHAR(500) UNIQUE | Deal URL (unique) |
| `title` | TEXT | Deal title |
| `price` | VARCHAR(100) | Deal price |
| `promo` | VARCHAR(255) | Promo code/discount |
| `category` | VARCHAR(100) | Main category |
| `store` | VARCHAR(100) | Store name (Amazon, Walmart, etc.) |
| `deal` | VARCHAR(255) | Deal description |
| `dealplus` | VARCHAR(255) | Additional deal info |
| `deallink` | VARCHAR(500) | Deal link |
| `dealtext` | VARCHAR(255) | Deal button text |
| `dealhover` | VARCHAR(255) | Deal hover text |
| `published` | VARCHAR(100) | Published date |
| `popularity` | VARCHAR(50) | Popularity rating |
| `staffpick` | VARCHAR(50) | Staff pick flag |
| `detail` | TEXT | Full deal description |
| `raw_html` | TEXT | Raw HTML content |
| `created_at` | TIMESTAMP | Record creation time |
| `updated_at` | TIMESTAMP | Record update time |

**Indexes:**
- `idx_dealid` on `dealid`
- `idx_category` on `category`
- `idx_store` on `store`
- `idx_created_at` on `created_at`
- `idx_price` on `price(20)`

### 2. `deal_images` - Deal Images Table
**Separate table for deal images (one-to-many relationship)**

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT AUTO_INCREMENT PRIMARY KEY | Unique image ID |
| `dealid` | VARCHAR(100) | Reference to deal |
| `imageurl` | VARCHAR(500) | Image URL |
| `created_at` | TIMESTAMP | Record creation time |

**Indexes:**
- `idx_dealid` on `dealid`

### 3. `deal_categories` - Deal Categories Table
**Separate table for deal categories (many-to-many relationship)**

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT AUTO_INCREMENT PRIMARY KEY | Unique category ID |
| `dealid` | VARCHAR(100) | Reference to deal |
| `category_name` | VARCHAR(100) | Category name |
| `category_url` | VARCHAR(500) | Category URL |
| `category_title` | VARCHAR(255) | Category title |
| `created_at` | TIMESTAMP | Record creation time |

**Indexes:**
- `idx_dealid` on `dealid`

### 4. `related_deals` - Related Deals Table
**Separate table for related deals (one-to-many relationship)**

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT AUTO_INCREMENT PRIMARY KEY | Unique related deal ID |
| `dealid` | VARCHAR(100) | Reference to main deal |
| `relatedurl` | VARCHAR(500) | Related deal URL |
| `created_at` | TIMESTAMP | Record creation time |

**Indexes:**
- `idx_dealid` on `dealid`

## Data Relationships

```
deals (1) -----> (many) deal_images
deals (1) -----> (many) deal_categories  
deals (1) -----> (many) related_deals
```

## Key Features

### ✅ **Normalized Structure**
- **No data duplication** - Each piece of data stored once
- **Referential integrity** - Related data linked by dealid
- **Efficient storage** - Optimized for large datasets

### ✅ **Related Deals Implementation**
- **3+ related deals per main deal** as requested
- **Multiple extraction strategies** to ensure coverage
- **Deduplication** to avoid duplicate related deals
- **Proper indexing** for fast queries

### ✅ **Performance Optimizations**
- **Indexes on key fields** for fast searching
- **Unique constraints** to prevent duplicates
- **Proper data types** for efficient storage
- **Timestamp tracking** for data management

## Sample Queries

### Get all deals with their images and categories:
```sql
SELECT d.*, di.imageurl, dc.category_name
FROM deals d
LEFT JOIN deal_images di ON d.dealid = di.dealid
LEFT JOIN deal_categories dc ON d.dealid = dc.dealid
WHERE d.store = 'Amazon'
ORDER BY d.created_at DESC;
```

### Get deals with their related deals:
```sql
SELECT d.title, d.url, rd.relatedurl
FROM deals d
LEFT JOIN related_deals rd ON d.dealid = rd.dealid
WHERE d.category = 'Electronics'
ORDER BY d.created_at DESC;
```

### Count related deals per main deal:
```sql
SELECT d.title, COUNT(rd.id) as related_count
FROM deals d
LEFT JOIN related_deals rd ON d.dealid = rd.dealid
GROUP BY d.id, d.title
HAVING related_count >= 3
ORDER BY related_count DESC;
```

## Data Volume Expectations

With the improved scraper:
- **3,000+ main deals** per run
- **3+ related deals** per main deal = **9,000+ related deals**
- **Multiple images** per deal = **1,000+ images**
- **Multiple categories** per deal = **6,000+ category entries**

**Total expected records per run: 20,000+ records across all tables**
