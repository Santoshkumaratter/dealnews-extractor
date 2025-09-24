#!/bin/bash

# DealNews Scraper Export Script

echo "Exporting deals data..."

# Create exports directory if it doesn't exist
mkdir -p exports

# Export to CSV
mysql -h localhost -P 3307 -u root -proot dealnews -e "
SELECT id, url, title, price, promo, category, created_at 
FROM deals 
ORDER BY created_at DESC 
INTO OUTFILE '/var/lib/mysql-files/deals_export.csv'
FIELDS TERMINATED BY ',' 
ENCLOSED BY '\"' 
LINES TERMINATED BY '\n';
"

# Export to JSON (using Python script)
python3 -c "
import mysql.connector
import json
from datetime import datetime

conn = mysql.connector.connect(
    host='localhost',
    port=3307,
    user='root',
    password='root',
    database='dealnews'
)

cursor = conn.cursor(dictionary=True)
cursor.execute('SELECT * FROM deals ORDER BY created_at DESC')

deals = cursor.fetchall()

# Convert datetime objects to strings for JSON serialization
for deal in deals:
    if deal['created_at']:
        deal['created_at'] = deal['created_at'].isoformat()
    if deal['updated_at']:
        deal['updated_at'] = deal['updated_at'].isoformat()

with open('exports/deals_export.json', 'w') as f:
    json.dump(deals, f, indent=2, default=str)

cursor.close()
conn.close()

print(f'Exported {len(deals)} deals to exports/deals_export.json')
"

echo "Export completed. Files available in exports/ directory."
