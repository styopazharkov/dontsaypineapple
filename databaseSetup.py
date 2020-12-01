import sqlite3

#SQLite database setup:
con = sqlite3.connect("database.db")
print("Database opened successfully")
con.execute("create table Players ( \
    id INTEGER PRIMARY KEY AUTOINCREMENT, \
    key TEXT NOT NULL, \
    name TEXT NOT NULL)") 
print("Players table created successfully")  
con.close()  