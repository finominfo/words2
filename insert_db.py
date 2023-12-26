import sqlite3

# Specify the file path and database name
db_path = 'words.db'
table_name = 'translations'

# Create a connection to the database (this will create the database if it doesn't exist)
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create the translations table if it doesn't exist
cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS {table_name} (
        original TEXT PRIMARY KEY,
        translation TEXT
    )
''')

# Commit the changes to the database
conn.commit()

# Read the translations from the file, modify the target, and insert into the database
with open('translated.txt', 'r', encoding='utf-8') as file:
    for line in file:
        parts = line.strip().split(' ', 1)

        if len(parts) == 2:
            source, target = parts
            modified_target = ' '.join('+' + word for word in target.split())
            cursor.execute(f'''
                INSERT OR REPLACE INTO {table_name} (original, translation)
                VALUES (?, ?)
            ''', (source, modified_target))
        else:
            print(f'WARNING: invalid line: {line}')


# Commit the changes to the database
conn.commit()

cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
row_count = cursor.fetchone()[0]

# Print the number of rows
print(f'Number of rows in the table: {row_count}')

# Close the connection
conn.close()
