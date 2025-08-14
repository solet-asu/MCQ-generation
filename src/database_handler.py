import sqlite3
import csv
import os
import sqlite3
from typing import List, Dict, Any, Union
from datetime import datetime 
import logging


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from models.table_schema import TABLE_SCHEMAS

def table_exists(table_name: str, database_file: str) -> bool:
    """Check if a table exists in the database."""
    with sqlite3.connect(database_file) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT name FROM sqlite_master WHERE type='table' AND name=?
        ''', (table_name,))
        return cursor.fetchone() is not None



def create_table(table_name: Union[str, List[str]], database_file: str) -> None:
    """Create one or more tables with the given schema(s) if they don't exist."""
    
    # Ensure input is a list of strings
    table_names = [table_name] if isinstance(table_name, str) else table_name

    for name in table_names:
        try:
            # Check if the table schema exists
            if name not in TABLE_SCHEMAS:
                logging.error(f"Table schema for '{name}' not found.")
                continue

            # Check if the table already exists
            if table_exists(name, database_file):
                logging.info(f"Table '{name}' already exists.")
                continue

            # Get schema and create the table
            schema = TABLE_SCHEMAS[name]
            columns = ", ".join([f"{col} {dtype}" for col, dtype in schema.items()])

            with sqlite3.connect(database_file) as conn:
                cursor = conn.cursor()
                cursor.execute(f'''
                    CREATE TABLE {name} (
                        {columns}
                    )
                ''')
                conn.commit()
                logging.info(f"Table '{name}' created successfully.")
        except sqlite3.Error as e:
            logging.error(f"Error creating table '{name}': {e}")
        

def insert_metadata(
    metadata: Dict[str, Any],
    table_name: str,
    database_file: str,
    ) -> None:
    """Insert metadata into a table dynamically."""
    try:
        schema = TABLE_SCHEMAS[table_name]
        metadata["timestamp"] = datetime.now().isoformat()
        
        columns = [col for col in schema if col != "id"]
        placeholders = ", ".join(["?"] * len(columns))
        column_names = ", ".join(columns)
        values = [metadata[col] for col in columns]
        
        with sqlite3.connect(database_file) as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})",
                values
            )
            conn.commit()
            logging.info(f"Metadata inserted into '{table_name}'.")
    except KeyError as e:
        logging.error(f"Table '{table_name}' not found in schema: {e}")
    except sqlite3.Error as e:
        logging.error(f"Error inserting metadata into '{table_name}': {e}")


def get_extraction_values(table_name: str, database_file: str) -> List[str]:
    """Retrieve all values from the extraction column in the mcq_metadata table."""
    extraction_values = []
    
    # Connect to the SQLite database
    with sqlite3.connect(database_file) as conn:
        cursor = conn.cursor()
        
        # Execute a query to select the extraction column
        cursor.execute(f'SELECT extraction FROM {table_name}')
        
        # Fetch all results from the query
        rows = cursor.fetchall()
        
        # Extract the values from the rows and add them to the list
        extraction_values = [row[0] for row in rows]
    
    return extraction_values



def export_table_to_csv(table_name: str, file_name: str, database_file: str) -> None:
    """Export all rows from a specified table to a CSV file in the output directory."""
    
    OUTPUT_DIR = '../output'

    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    OUTPUT_CSV = os.path.join(OUTPUT_DIR, file_name)
    
    with sqlite3.connect(database_file) as conn:
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
