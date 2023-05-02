from flask import Flask, request, render_template, url_for, redirect, flash, Markup, abort
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
#from flask_mail import Mail, Message
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

def gestisce():
    gestione = False
    if current_user.collaboratore["ruolo"] == "manager":
        gestione = True
    return gestione

def get_nome(tipo, tmp_id):
    mcpDB = sqlite3.connect(mcpDB_path)
    cur = mcpDB.cursor()
    if tipo == "cliente":
        cur.execute("select nome from clienti where id = ?", [tmp_id])
        cliente = cur.fetchall()
        nome = cliente[0][0]
    elif tipo == "tipo_lavorazione":
        cur.execute("select nome from tipo_lavorazioni where id = ?", [tmp_id])
        tipo_lavorazione = cur.fetchall()
        nome = tipo_lavorazione[0][0]
    elif tipo == "collaboratore":
        user = User.query.filter_by(id=tmp_id).first()
        nome = user.anagrafica["nome"] + " " + user.anagrafica["cognome"]
    mcpDB.commit()
    mcpDB.close()
    return nome

def dati_mcp(tipo):
    mcpDB = sqlite3.connect(mcpDB_path)
    cur = mcpDB.cursor()

    if tipo == "commesse":
        cur.execute("select * from commesse")
        commesse = cur.fetchall()
        dati = []
        for commessa in commesse:
            tmp_specifiche = {
                    "budget_ore": json.loads(commessa[4])["budget_ore"],
                    "budget_euro": json.loads(commessa[4])["budget_euro"],
                    "project_manager": get_nome("collaboratore", json.loads(commessa[4])["project_manager"])
                    }
            tmp_commessa = {
                "id": commessa[0],
                "numero": commessa[1],
                "nome": commessa[2],
                "cliente": get_nome("cliente", commessa[3]),
                "specifiche": tmp_specifiche,
                "durata": json.loads(commessa[5]),
                "note": commessa[6]
                }
            print(tmp_commessa)
            dati.append(tmp_commessa)

    elif tipo == "commesse_complete":
        cur.execute("select * from commesse")
        commesse = cur.fetchall()
        dati = []
        for commessa in commesse:
            tmp_specifiche = {
                    "budget_ore": json.loads(commessa[4])["budget_ore"],
                    "budget_euro": json.loads(commessa[4])["budget_euro"],
                    "project_manager": get_nome("collaboratore", json.loads(commessa[4])["project_manager"])
                    }
            cur.execute("select * from lavorazioni where commessa = ?", [commessa[0]])
            lavorazioni = cur.fetchall()
            tmp_lavorazioni = []
            for lavorazione in lavorazioni:
                tmp_lavorazione = {
                    "id": lavorazione[0],
                    "collaboratore": get_nome("collaboratore", lavorazione[1]),
                    "tipo": get_nome("tipo_lavorazione", lavorazione[3]),
                    "durata": json.loads(lavorazione[4])
                    }
                tmp_lavorazioni.append(tmp_lavorazione)
            tmp_commessa = {
                "id": commessa[0],
                "numero": commessa[1],
                "nome": commessa[2],
                "cliente": get_nome("cliente", commessa[3]),
                "specifiche": tmp_specifiche,
                "durata": json.loads(commessa[5]),
                "note": commessa[6],
                "lavorazioni": tmp_lavorazioni
                }
            print(tmp_commessa)
            dati.append(tmp_commessa)
    mcpDB.commit()
    mcpDB.close()
    return dati

@app.route("/")
def homepage():
    return render_template("index.html")

@app.route("/dashboard")
@login_required
def dashboard():
    dati_mcp("commesse_complete")
    return render_template("dashboard.html", gestione=gestisce())

@app.route("/storico")
@login_required
def storico():
    return render_template("storico.html", gestione=gestisce())

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
                    "costo": request.form["costo"]
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
    utenti = User.query.all()
    return render_template("collaboratori.html", gestione=gestisce(), utenti=utenti)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
