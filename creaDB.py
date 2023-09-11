import sqlite3

datiDB_path = "mcp.db"

datiDB = sqlite3.connect(datiDB_path)
cur = datiDB.cursor()

#Tabella Commesse esterne e relativa commessa ore "lavorazioni"
cur.execute("CREATE TABLE IF NOT EXISTS commesse (id INTEGER PRIMARY KEY AUTOINCREMENT, numero TEXT, nome TEXT, cliente INTEGER, specifiche json, durata json, note TEXT, offerta INTEGER, file json)")
cur.execute("CREATE TABLE IF NOT EXISTS lavorazioni (id INTEGER PRIMARY KEY AUTOINCREMENT, collaboratore INTEGER, commessa INTEGER, tipo INTEGER, durata json)")

#Tabella Offerte e Addestramento con relative ore
cur.execute("CREATE TABLE IF NOT EXISTS offerte (id INTEGER PRIMARY KEY AUTOINCREMENT, numero TEXT, ordine_rif TEXT, cliente INTEGER, versioni json, note TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS interne (id INTEGER PRIMARY KEY AUTOINCREMENT, numero TEXT, nome TEXT, durata json, note TEXT)")

cur.execute("CREATE TABLE IF NOT EXISTS ore_interne (id INTEGER PRIMARY KEY AUTOINCREMENT, collaboratore INTEGER, id_interna INTEGER, durata json)")

#Qualità
cur.execute("CREATE TABLE IF NOT EXISTS fornitori (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, valutazioni json)")

cur.execute("CREATE TABLE IF NOT EXISTS clienti (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT)")

cur.execute("CREATE TABLE IF NOT EXISTS tipo_lavorazioni (id INTEGER PRIMARY KEY AUTOINCREMENT, tag TEXT, nome TEXT)")

#File storage
cur.execute("CREATE TABLE IF NOT EXISTS file (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, dati BLOB)")

datiDB.commit()
datiDB.close()
