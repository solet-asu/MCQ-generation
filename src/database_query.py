import sqlite3
from typing import List
import csv
import os


# Define the database file
DATABASE_FILE = '../database/mcq_metadata.db'


def get_extraction_values(table_name: str) -> List[str]:
    """Retrieve all values from the extraction column in the mcq_metadata table."""
    extraction_values = []
    
    # Connect to the SQLite database
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        
        # Execute a query to select the extraction column
        cursor.execute(f'SELECT extraction FROM {table_name}')
        
        # Fetch all results from the query
        rows = cursor.fetchall()
        
        # Extract the values from the rows and add them to the list
        extraction_values = [row[0] for row in rows]
    
    return extraction_values



def export_table_to_csv(table_name: str, file_name: str) -> None:
    """Export all rows from a specified table to a CSV file in the output directory."""
    
    OUTPUT_DIR = '../output'

    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    OUTPUT_CSV = os.path.join(OUTPUT_DIR, file_name)
    
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        
        # Fetch all rows from the table
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        # Fetch column names
        column_names = [description[0] for description in cursor.description]
        
        # Write to CSV
        with open(OUTPUT_CSV, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(column_names)  # write header
            writer.writerows(rows)         # write data
        
        print(f"Exported {len(rows)} rows to {OUTPUT_CSV}")
