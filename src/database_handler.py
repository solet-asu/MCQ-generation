import sqlite3
from typing import List
import csv
import os
import sqlite3
from typing import Dict
from datetime import datetime 


# Define the database file
DATABASE_FILE = '../database/mcq_metadata.db'

def table_exists(table_name: str, database_file: str) -> bool:
    """Check if a table exists in the database."""
    with sqlite3.connect(database_file) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT name FROM sqlite_master WHERE type='table' AND name=?
        ''', (table_name,))
        return cursor.fetchone() is not None

def create_table(table_name: str = "mcq_metadata", database_file: str ="../database/mcq_metadata.db"):
    """Create the table if it doesn't exist."""
    if not table_exists(table_name):
        with sqlite3.connect(database_file) as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                CREATE TABLE {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_type TEXT,
                    system_prompt TEXT,
                    user_prompt TEXT,
                    model TEXT,
                    completion TEXT,
                    mcq TEXT,
                    mcq_answer TEXT,
                    execution_time TEXT,
                    input_tokens INTEGER,
                    output_tokens INTEGER,
                    timestamp TEXT
                )
            ''')
            conn.commit()

def insert_metadata(metadata: Dict[str, str], table_name: str = "mcq_metadata", database_file: str = "../database/mcq_metadata.db"):
    """Insert table into the database."""
    timestamp = datetime.now().isoformat()
    with sqlite3.connect(database_file) as conn:
        cursor = conn.cursor()
        cursor.execute(f'''
            INSERT INTO {table_name} (
                question_type, system_prompt, user_prompt, model, 
                completion, mcq, mcq_answer, execution_time, input_tokens, output_tokens, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metadata['question_type'],
            metadata['system_prompt'],
            metadata['user_prompt'],
            metadata['model'],
            metadata['completion'],
            metadata['mcq'],
            metadata['mcq_answer'],
            metadata['execution_time'],
            metadata['input_tokens'],
            metadata['output_tokens'],
            timestamp
        ))
        conn.commit()


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
