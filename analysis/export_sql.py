import psycopg2
import csv
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
DB_PARAMS = {
    'database': 'reapbotstudydb',
    'user': 'doadmin',
    'password': os.getenv('DB_PASSWORD'),
    'host': 'pingbot-v2-db-do-user-18635979-0.i.db.ondigitalocean.com', 
    'port': 25060,
    'sslmode': 'require'
}

# Tables to dump
TABLES = ["analysis_data", "conversations", "llm_queries", "messages"]

# Connect to the PostgreSQL database
try:
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()
    
    for table in TABLES:
        output_file = f"analysis/{table}.csv"
        with open(output_file, "w", newline="") as f:
            writer = csv.writer(f)
            
            # Fetch column names
            cursor.execute(f"SELECT * FROM {table} LIMIT 0;")
            col_names = [desc[0] for desc in cursor.description]
            writer.writerow(col_names)  # Write column headers
            
            # Fetch and write data
            cursor.execute(f"SELECT * FROM {table};")
            for row in cursor.fetchall():
                writer.writerow(row)
        
        print(f"Dumped {table} to {output_file}")

except Exception as e:
    print(f"Error: {e}")
finally:
    if cursor:
        cursor.close()
    if conn:
        conn.close()
