import sqlite3

conn = sqlite3.connect("products.db")
cursor = conn.cursor()

# Delete the product with id = 7
cursor.execute('''
    UPDATE products
    SET category = 'Walls'
    WHERE id = 25;
''')

conn.commit()
conn.close()

print("🗑️ Product with id 7 deleted successfully.")
