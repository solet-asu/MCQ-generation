import sqlite3
from typing import List

# Define the database file
DATABASE_FILE = 'database/mcq_metadata.db'

def get_extraction_values() -> List[str]:
    """Retrieve all values from the extraction column in the mcq_metadata table."""
    extraction_values = []
    
    # Connect to the SQLite database
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        
        # Execute a query to select the extraction column
        cursor.execute('SELECT extraction FROM mcq_metadata')
        
        # Fetch all results from the query
        rows = cursor.fetchall()
        
        # Extract the values from the rows and add them to the list
        extraction_values = [row[0] for row in rows]
    
    return extraction_values

# Example usage of the function
extraction_list = get_extraction_values()
