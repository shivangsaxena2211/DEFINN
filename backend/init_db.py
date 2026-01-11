import sqlite3 
conn = sqlite3.connect("database.db") 
cur = conn.cursor() 

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT UNIQUE,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT
)
""")

cur.execute(""" CREATE TABLE IF NOT EXISTS wallet ( user_id TEXT PRIMARY KEY, balance REAL ) """) 
cur.execute(""" CREATE TABLE IF NOT EXISTS transactions ( id INTEGER PRIMARY KEY AUTOINCREMENT, from_user TEXT, to_user TEXT, amount REAL, type TEXT, date TEXT ) """) 
cur.execute(""" CREATE TABLE IF NOT EXISTS crypto_holdings ( id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, symbol TEXT, quantity REAL, buy_price REAL, timestamp TEXT ) """) 
cur.execute(""" CREATE TABLE IF NOT EXISTS stock_holdings ( id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, symbol TEXT, quantity INTEGER, buy_price REAL, timestamp TEXT ) """) 
cur.execute( "INSERT OR IGNORE INTO wallet VALUES (?, ?)", ("USER123456789", 50000) ) 
conn.commit() 
conn.close() 
conn = sqlite3.connect("database.db") 
cur = conn.cursor() 
cur.execute(""" CREATE TABLE IF NOT EXISTS stock_holdings ( id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, symbol TEXT, quantity REAL, buy_price REAL, timestamp TEXT ) """) 
cur.execute(""" CREATE TABLE IF NOT EXISTS stock_orders ( id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, symbol TEXT, order_type TEXT, quantity INTEGER, price REAL, status TEXT, timestamp TEXT ) """) 
conn.commit() 
conn.close() 
print("Stock table ready") 