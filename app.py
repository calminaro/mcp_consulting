from flask import Flask, request, render_template, url_for, redirect, flash, Markup, abort
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
#from flask_mail import Mail, Message
from string import ascii_lowercase
import itertools
import json
import datetime
import random
import string
import sqlite3

with open("credenziali.json", "r") as f:
    cr = json.load(f)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] =  "sqlite:///utenti.db"
app.config['SECRET_KEY'] = cr["secret_key"]

db = SQLAlchemy(app)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(128), nullable=False)
    anagrafica = db.Column(db.JSON, nullable=False)
    collaboratore = db.Column(db.JSON, nullable=False)
    verifica = db.Column(db.JSON, nullable=False)

#with app.app_context():
#    db.create_all()

'''
app.config['MAIL_SERVER']= cr["mail"]["server"]
app.config['MAIL_PORT'] = cr["mail"]["port"]
app.config['MAIL_USERNAME'] = cr["mail"]["mail"]
app.config['MAIL_PASSWORD'] = cr["mail"]["pw"]
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)
'''

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

utentiDB_path = "utenti.db"
mcpDB_path = "mcp.db"

#Genera e trova i numeri commessa
def iter_all_strings():
    for size in itertools.count(1):
        for s in itertools.product(ascii_lowercase, repeat=size):
            yield "".join(s)

def genera_int():
    mcpDB = sqlite3.connect(mcpDB_path)
    cur = mcpDB.cursor()
    cur.execute("select * from commesse")
    commesse = cur.fetchall()
    mcpDB.commit()
    mcpDB.close()
    n = 1
    for i in commesse:
        if i[2] == "interna":
            n = trova(i[1]) + 1
    i = 1
    for s in itertools.islice(iter_all_strings(), n):
        if i == n:
            return s.upper()
        i += 1
def trova(n):
    i = 1
    for s in iter_all_strings():
        if s == n.lower():
            return i
        i += 1

def genera_ext():
    mcpDB = sqlite3.connect(mcpDB_path)
    cur = mcpDB.cursor()
    cur.execute("select * from commesse")
    commesse = cur.fetchall()
    mcpDB.commit()
    mcpDB.close()
    n = 1
    for i in commesse:
        if i[2] == "esterna":
            n = int(i[1]) + 1
    return n
# ---------------------------

def gestisce():
    gestione = False
    if current_user.collaboratore["ruolo"] == "manager":
        gestione = True
    return gestione

def get_clienti():
    mcpDB = sqlite3.connect(mcpDB_path)
    cur = mcpDB.cursor()
    cur.execute("select * from clienti")
    clienti = cur.fetchall()
    mcpDB.commit()
    mcpDB.close()
    return clienti

def get_nome(tipo, tmp_id):
    mcpDB = sqlite3.connect(mcpDB_path)
    cur = mcpDB.cursor()
    if tipo == "cliente":
        cur.execute("select nome from clienti where id = ?", [tmp_id])
        cliente = cur.fetchall()
        nome = cliente[0][0]
    elif tipo == "tipo_lavorazione":
        nome = "Altro"
        if int(tmp_id) != 0:
            cur.execute("select nome from tipo_lavorazioni where id = ?", [tmp_id])
            tipo_lavorazione = cur.fetchall()
            nome = tipo_lavorazione[0][0]
    elif tipo == "collaboratore":
        user = User.query.filter_by(id=tmp_id).first()
        nome = user.anagrafica["nome"] + " " + user.anagrafica["cognome"]
    mcpDB.commit()
    mcpDB.close()
    return nome

def get_numero_commessa(numero):
    l_base = 4
    new_numero = ""
    lunghezza = len(numero)
    for i in range(l_base-lunghezza):
        new_numero = "0"+new_numero
    new_numero = new_numero+numero
    return new_numero

def get_tipo_commessa(lista):
    new_lista = []
    for i in lista:
        tmp_tipo = {"id": i,"nome": get_nome("tipo_lavorazione", i)}
        new_lista.append(tmp_tipo)
    return new_lista

def get_costo(tmp_id, durata):
    costo = 0.0
    tmp_durata = float(durata["ore"])
    if durata["trasferta"]:
        costo += 100
        tmp_durata = 8.0
    user = User.query.filter_by(id=tmp_id).first()
    user_costo = float(user.collaboratore["costo"])
    costo = costo + (tmp_durata*user_costo)
    return costo

def insert_edit_lavorazione(dati):
    mcpDB = sqlite3.connect(mcpDB_path)
    cur = mcpDB.cursor()
    if dati["form"] == "inserisci_lavorazione":
        cur.execute("INSERT INTO lavorazioni (collaboratore, commessa, tipo, durata) VALUES (?,?,?,?)", [int(current_user.id), int(dati["id_commessa"]), int(dati["tipo"]), json.dumps(dati["durata"])])
    elif dati["form"] == "modifica_lavorazione":
        cur.execute("UPDATE lavorazioni SET tipo = ?, durata = ? WHERE id = ?", [int(dati["tipo"]), json.dumps(dati["durata"]), int(dati["id_lavorazione"])])
    elif dati["form"] == "elimina_lavorazione":
        cur.execute("DELETE from lavorazioni where id = ?", [int(dati["id_lavorazione"])])
    mcpDB.commit()
    mcpDB.close()

def insert_edit_commessa(dati):
    mcpDB = sqlite3.connect(mcpDB_path)
    cur = mcpDB.cursor()
    if dati["form"] == "inserisci_commessa":
        specifiche = {
            "budget_ore": int(dati["ore"]),
            "budget_euro": int(dati["euro"]),
            "project_manager": int(dati["project_manager"]),
            "tipologia": dati["tipologia"]
            }
        durata = {
            "inizio": dati["data"],
            "fine": False
            }
        numero = ""
        tipo = ""
        if dati["cliente"] == "1":
            numero = str(genera_int())
            tipo = "interna"
        else:
            numero = str(genera_ext())
            tipo = "esterna"
        cur.execute("INSERT INTO commesse (numero, tipo, nome, cliente, specifiche, durata, note) VALUES (?,?,?,?,?,?,?)", [numero, tipo, dati["nome"], int(dati["cliente"]), json.dumps(specifiche), json.dumps(durata), dati["note"]])
    elif dati["form"] == "modifica_commessa":
        print("dovrei modificare: ", dati)
        specifiche = {
            "budget_ore": int(dati["ore"]),
            "budget_euro": int(dati["euro"]),
            "project_manager": int(dati["project_manager"]),
            "tipologia": dati["tipologia"]
            }
        durata = {
            "inizio": dati["data"],
            "fine": False
            }
        tipo = ""
        if dati["cliente"] == "1":
            tipo = "interna"
        else:
            tipo = "esterna"
        cur.execute("UPDATE commesse SET tipo = ?, nome = ?, cliente = ?, specifiche = ?, durata = ?, note = ? WHERE id = ?", [tipo, dati["nome"], int(dati["cliente"]), json.dumps(specifiche), json.dumps(durata), dati["note"], dati["id_commessa"]])
    elif dati["form"] == "elimina_commessa":
        print("dovrei eliminare: ", dati)
    mcpDB.commit()
    mcpDB.close()

def dati_mcp(tipo):
    mcpDB = sqlite3.connect(mcpDB_path)
    cur = mcpDB.cursor()

    if tipo == "commesse":
        cur.execute("select * from commesse")
        commesse = cur.fetchall()
        dati = []
        for commessa in commesse:
            tmp_specifiche = {
                    "budget_ore": json.loads(commessa[5])["budget_ore"],
                    "budget_euro": json.loads(commessa[5])["budget_euro"],
                    "project_manager": {"id": json.loads(commessa[5])["project_manager"],"nome": get_nome("collaboratore", json.loads(commessa[5])["project_manager"])},
                    "tipologia": get_tipo_commessa(json.loads(commessa[5])["tipologia"])
                    }
            tmp_commessa = {
                "id": commessa[0],
                "numero": get_numero_commessa(commessa[1]),
                "tipo": commessa[2],
                "nome": commessa[3],
                "cliente": {"id": commessa[4],"nome": get_nome("cliente", commessa[4])},
                "specifiche": tmp_specifiche,
                "durata": json.loads(commessa[6]),
                "note": commessa[7]
                }
            dati.append(tmp_commessa)

    elif tipo == "commesse_complete":
        cur.execute("select * from commesse")
        commesse = cur.fetchall()
        dati = []
        for commessa in commesse:
            cur.execute("select * from lavorazioni where commessa = ?", [commessa[0]])
            lavorazioni = cur.fetchall()
            tmp_lavorazioni = []
            ore_lavorate = 0.0
            euro_spesi = 0.0
            for lavorazione in lavorazioni:
                tmp_lavorazione = {
                    "id": lavorazione[0],
                    "collaboratore": {"id": lavorazione[1],"nome": get_nome("collaboratore", lavorazione[1])},
                    "tipo": {"id": lavorazione[3],"nome": get_nome("tipo_lavorazione", lavorazione[3])},
                    "durata": json.loads(lavorazione[4]),
                    "costo": get_costo(lavorazione[1], json.loads(lavorazione[4]))
                    }
                ore_lavorate += float(tmp_lavorazione["durata"]["ore"])
                euro_spesi += tmp_lavorazione["costo"]
                tmp_lavorazioni.append(tmp_lavorazione)
            tmp_specifiche = {
                    "budget_ore": float(json.loads(commessa[5])["budget_ore"]),
                    "budget_euro": float(json.loads(commessa[5])["budget_euro"]),
                    "ore_lavorate": ore_lavorate,
                    "euro_spesi": euro_spesi,
                    "project_manager": {"id": json.loads(commessa[5])["project_manager"],"nome": get_nome("collaboratore", json.loads(commessa[5])["project_manager"])},
                    "tipologia": get_tipo_commessa(json.loads(commessa[5])["tipologia"])
                    }
            tmp_commessa = {
                "id": commessa[0],
                "numero": get_numero_commessa(commessa[1]),
                "tipo": commessa[2],
                "nome": commessa[3],
                "cliente": {"id": commessa[4],"nome": get_nome("cliente", commessa[4])},
                "specifiche": tmp_specifiche,
                "durata": json.loads(commessa[6]),
                "note": commessa[7],
                "lavorazioni": tmp_lavorazioni
                }
            dati.append(tmp_commessa)
    mcpDB.commit()
    mcpDB.close()
    return dati

@app.route("/")
def homepage():
    return render_template("index.html")

@app.route("/dashboard", methods=("GET", "POST"))
@login_required
def dashboard():
    pagina = "riepilogo"
    if request.method == "POST":
        if request.form["id_form"] == "inserisci_lavorazione" or request.form["id_form"] == "modifica_lavorazione":
            try:
                request.form["trasferta"]
                tmp_trasferta = True
            except:
                tmp_trasferta = False
            try:
                anno, mese, giorno = request.form["data"].split('-')
                tmp = datetime.date(int(anno), int(mese), int(giorno))
                tmp_ore = float(request.form["ore"])
                ore, minuti = str(tmp_ore).split('.')
                tmp = datetime.time(hour=int(ore), minute=(int(60*(int(minuti)/10))))
                dati_validi = True
            except:
                dati_validi = False
            tmp_dati = {
                "form": request.form["id_form"],
                "id_commessa": request.form["id_commessa"],
                "id_lavorazione": request.form["id_lavorazione"],
                "tipo": request.form["tipo"],
                "durata": {
                    "data": request.form["data"],
                    "ore": request.form["ore"],
                    "trasferta": tmp_trasferta
                    }
                }
            if dati_validi:
                insert_edit_lavorazione(tmp_dati)
                flash("Inserito con successo!")
            else:
                flash("Dati errati.")
            pagina = tmp_dati["id_commessa"]
        elif request.form["id_form"] == "elimina_lavorazione":
            tmp_dati = {
                "form": request.form["id_form"],
                "id_commessa": request.form["id_commessa"],
                "id_lavorazione": request.form["id_lavorazione"]
                }
            insert_edit_lavorazione(tmp_dati)
            flash("Eliminato con successo!")
            pagina = tmp_dati["id_commessa"]
        elif request.form["id_form"] == "inserisci_commessa" or request.form["id_form"] == "modifica_commessa":
            tipi = []
            try:
                tipi.append(int(request.form["tipo_supporti"]))
            except:
                pass
            try:
                tipi.append(int(request.form["tipo_piping"]))
            except:
                pass
            try:
                tipi.append(int(request.form["tipo_stressAnalysis"]))
            except:
                pass
            try:
                tipi.append(int(request.form["tipo_altro"]))
            except:
                pass
            tmp_dati = {
                "form": request.form["id_form"],
                "id_commessa": request.form["id_commessa"],
                "nome": request.form["nome"],
                "cliente": request.form["cliente"],
                "project_manager": request.form["project_manager"],
                "tipologia": tipi,
                "data": request.form["data"],
                "ore": request.form["ore"],
                "euro": request.form["euro"],
                "note": request.form["note"]
                }
            insert_edit_commessa(tmp_dati)
            try:
                pagina = tmp_dati["id_commessa"]
            except:
                pass
        elif request.form["id_form"] == "elimina_commessa":
            tmp_dati = {
                "form": request.form["id_form"],
                "id_commessa": request.form["id_commessa"]
                }
            insert_edit_commessa(tmp_dati)
            flash("Eliminato con successo!")
    return render_template("dashboard.html", gestione=gestisce(), dati=dati_mcp("commesse_complete"), clienti=get_clienti(), utenti=User.query.all(), pagina=pagina)

@app.route("/storico")
@login_required
def storico():
    return render_template("storico.html", gestione=gestisce())

@app.route("/clienti")
@login_required
def clienti():
    return render_template("clienti.html", gestione=gestisce(), clienti=get_clienti())

@app.route("/dettaglio_storico")
@login_required
def dettaglio_storico():
    return render_template("dettaglio_storico.html", gestione=gestisce())

@app.route("/report")
@login_required
def report():
    return render_template("report.html", gestione=gestisce())

#GESTIONE ACCOUNT - GESTIONE LOGIN
@app.route("/account", methods=("GET", "POST"))
@login_required
def account():
    if request.method == "POST":
        if request.form["id_form"] == "aggiorna_passwd":
            if check_password_hash(current_user.password, request.form["old_passwd"]) and request.form["passwd"] == request.form["new_passwd"] and request.form["passwd"] != "":
                tmp_password = generate_password_hash(request.form["passwd"])
                utente = User.query.filter_by(username=current_user.username).first()
                utente.password = tmp_password
                db.session.commit()
    return render_template("account.html", gestione=gestisce())

@app.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        utente = User.query.filter_by(username=request.form["username"]).first()
        if utente:
            if check_password_hash(utente.password, request.form["passwd"]):
                login_user(utente)
                return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("homepage"))

@app.route("/collaboratori", methods=("GET", "POST"))
@login_required
def collaboratori():
    if current_user.collaboratore["ruolo"] != "manager":
        redirect(url_for("homepage"))
    if request.method == "POST":
        if request.form["id_form"] == "nuovo_utente":
            utente = User.query.filter_by(username=request.form["username"]).first()
            if utente is None:
                password = generate_password_hash(request.form["passwd"])
                tmp_cod = random.randint(111111,999999)
                anagrafica = {
                    "nome": request.form["nome"],
                    "cognome": request.form["cognome"],
                    "mail": request.form["mail"]
                    }
                verifica = {
                    "mail": tmp_cod,
                    "recupero": ""
                    }
                collaboratore = {
                    "ruolo": request.form["ruolo"],
                    "costo": request.form["costo"] if request.form["costo"] != "" else "0"
                    }

                #msg = Message("MCP Consulting - Nuovo Account", sender = cr["mail"]["mail"], recipients = [request.form["mail"]])
                #msg.html = "Buongiorno "+request.form["nome"]+" "+request.form["cognome"]+",<br>account creato correttamente.<br><br>Codice di verifica: "+str(verifica["mail"])+"<br><br>Grazie,<br>MCP Consulting"
                #mail.send(msg)

                utente = User(username=request.form["username"], password=password, anagrafica=anagrafica, collaboratore=collaboratore, verifica=verifica)
                db.session.add(utente)
                db.session.commit()
                return redirect(url_for("login"))
            else:
                flash("Esiste già un utente "+request.form["username!"])
    return render_template("collaboratori.html", gestione=gestisce(), utenti=User.query.all())

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
