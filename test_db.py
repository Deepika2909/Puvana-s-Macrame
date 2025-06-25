import psycopg2

def get_connection():
    return psycopg2.connect(
        "postgresql://postgres.kfdqdghuwhvjuafdpgis:Deepika%4029092003@aws-0-ap-south-1.pooler.supabase.com:6543/postgres"
    )
conn = get_connection()
cur = conn.cursor()
cur.execute("SELECT NOW();")
print(cur.fetchone())
conn.close()
