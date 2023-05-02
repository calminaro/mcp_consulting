import sqlite3
import json

datiDB_path = "mcp.db"

datiDB = sqlite3.connect(datiDB_path)
cur = datiDB.cursor()

#crea_db
cur.execute("CREATE TABLE IF NOT EXISTS commesse (id INTEGER PRIMARY KEY AUTOINCREMENT, numero TEXT, nome TEXT, cliente INTEGER, specifiche json, durata json, note TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS lavorazioni (id INTEGER PRIMARY KEY AUTOINCREMENT, collaboratore INTEGER, commessa INTEGER, tipo INTEGER, durata json)")
cur.execute("CREATE TABLE IF NOT EXISTS clienti (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS tipo_lavorazioni (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT)")

#valori default
tipo_lavorazioni = ["Supporti", "Piping", "Stress Analysis"]
for i in tipo_lavorazioni:
    cur.execute("INSERT INTO tipo_lavorazioni (nome) VALUES (?)", [i])

#valori esempio
cur.execute("INSERT INTO clienti (nome) VALUES (?)", ["MCP Consulting"])
cur.execute("INSERT INTO clienti (nome) VALUES (?)", ["Paperoni SPA"])

specifiche = {
    "budget_ore": 200,
    "budget_euro": 5000,
    "project_manager": 1
    }
durata = {
    "inizio": "2023-05-02",
    "fine": False
    }
cur.execute("INSERT INTO commesse (numero, nome, cliente, specifiche, durata, note) VALUES (?,?,?,?,?,?)", ["0001", "Tubiline", 2, json.dumps(specifiche), json.dumps(durata), "Campo libero per scrivere cose tipo bho il cliente è uno stronzo ma ci ha aumentato il budget quindi bene."])

specifiche = {
    "budget_ore": 0,
    "budget_euro": 0,
    "project_manager": 2
    }
durata = {
    "inizio": "2023-05-02",
    "fine": False
    }
cur.execute("INSERT INTO commesse (numero, nome, cliente, specifiche, durata, note) VALUES (?,?,?,?,?,?)", ["000A", "Offerte", 1, json.dumps(specifiche), json.dumps(durata), ""])

durata = {
    "data": "2023-04-27",
    "ore": "2.5",
    "trasferta": False
    }
cur.execute("INSERT INTO lavorazioni (collaboratore, commessa, tipo, durata) VALUES (?,?,?,?)", [2, 1, 1, json.dumps(durata)])
durata = {
    "data": "2023-05-02",
    "ore": "3.5",
    "trasferta": True
    }
cur.execute("INSERT INTO lavorazioni (collaboratore, commessa, tipo, durata) VALUES (?,?,?,?)", [1, 1, 1, json.dumps(durata)])
durata = {
    "data": "2023-05-02",
    "ore": "3.5",
    "trasferta": False
    }
cur.execute("INSERT INTO lavorazioni (collaboratore, commessa, tipo, durata) VALUES (?,?,?,?)", [1, 2, 1, json.dumps(durata)])

datiDB.commit()
datiDB.close()
