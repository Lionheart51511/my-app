
import sqlite3, json
from datetime import datetime

DB_PATH = "borsa.db"

def init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS transactions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tx_date TEXT, stock TEXT, side TEXT,
        price REAL, qty REAL, gross REAL,
        commission REAL, net REAL, raw_json TEXT,
        created_at TEXT)""")
    con.commit(); con.close()

def insert_transactions(txs):
    con = sqlite3.connect(DB_PATH)
    for t in txs:
        gross = round(t["price"] * t["qty"], 4)
        comm  = t.get("commission", 0) or 0
        net   = round(gross - comm, 4) if t["side"] == "بيع" else round(-(gross + comm), 4)
        con.execute("""INSERT INTO transactions
            (tx_date,stock,side,price,qty,gross,commission,net,raw_json,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (t.get("date",""), t["stock"], t["side"], t["price"], t["qty"],
             gross, comm, net, json.dumps(t, ensure_ascii=False),
             datetime.now().isoformat()))
    con.commit(); con.close()

def fetch_all():
    con = sqlite3.connect(DB_PATH)
    rows = con.execute("""SELECT tx_date,stock,side,price,qty,gross,commission,net
                          FROM transactions ORDER BY tx_date, id""").fetchall()
    con.close()
    cols = ["date","stock","side","price","qty","gross","commission","net"]
    return [dict(zip(cols, r)) for r in rows]
