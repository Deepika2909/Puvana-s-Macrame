# init_db.py
import sqlite3

conn = sqlite3.connect('products.db')
c = conn.cursor()


c.execute('''CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    category TEXT, 
    name TEXT UNIQUE,
    price REAL,
    image TEXT,
    description TEXT UNIQUE
)''')

# Add dummy products
products = [
    ("Plant","Multi Holder", 70, "wm_(1).jpg", "A decorative macramé wall hanging featuring five terracotta pots nestled in intricately knotted holders. The neutral cotton rope contrasts beautifully with the green plants, creating a cozy, bohemian look ideal for interior decor."),
    ("Walls","Tree Life", 250, "tree_(5).jpg","A round macramé design representing the Tree of Life, made with twisted cotton cords within a circular frame. The roots flow downward in free-hanging strands, making it a symbolic and artistic piece for wall decor."),
    ("Essentials","Mini Runner", 200, "tr_(5).jpg", "A handcrafted macramé table runner styled on a wooden surface, adorned with small terracotta pots containing succulents. The symmetrical design and fringed edges add a rustic, natural charm to the tabletop arrangement.")
]

try:
    c.executemany('INSERT INTO products (category, name, price, image, description) VALUES (?, ?, ?, ?, ?)', products)
except sqlite3.IntegrityError:
    pass  # Skip if duplicates already exist

conn.commit()
conn.close()
