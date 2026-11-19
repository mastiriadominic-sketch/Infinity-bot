import os, json, random, shutil, sqlite3, time
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, make_response
app = Flask(__name__)

# ===== REAL DB + TRIPLE BACKUP =====
# DB1 = infinity.db (Main - SQLite, survives restart)
# DB2 = infinity_backup1.db (Copy 1)
# DB3 = infinity_backup2.db (Copy 2)
# RAM = DATA in memory
# Phone = localStorage inf_backup (Copy 4)
DB_FILE = "infinity.db"
DB_B1 = "infinity_backup1.db"
DB_B2 = "infinity_backup2.db"
ALL_DB = [DB_FILE, DB_B1, DB_B2]

# SERVER STARTS - EXACT LIKE YOU SAID
DEFAULT_ECO = {"gold": 100000000, "gems": 100000, "bank_gold": 50000000, "bank_gems": 50000000, "bank_total": 100000000, "fees": 0, "lottery": 0, "backup": 100000000, "history": [100000000, 100000000]}
DATA = {"players": {}, "loans": [], "requests": [], "announcements": [], "reviews": [], "chats": {}, "game_on": True, "friend_requests": [], "economy": dict(DEFAULT_ECO)}

def db_conn(path):
    c = sqlite3.connect(path)
    c.execute("CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT)")
    return c

def db_read(path):
    try:
        if not os.path.exists(path): return None
        c = db_conn(path)
        row = c.execute("SELECT v FROM kv WHERE k='DATA'").fetchone()
        c.close()
        if row: return json.loads(row[0])
    except Exception: pass
    return None

def db_write_all():
    # Write to MAIN DB, then duplicate file to 2 backups = 3 copies of every player
    try:
        c = db_conn(DB_FILE)
        c.execute("INSERT OR REPLACE INTO kv VALUES ('DATA', ?)", (json.dumps(DATA),))
        c.commit(); c.close()
        for b in [DB_B1, DB_B2]:
            try: shutil.copyfile(DB_FILE, b)
            except Exception: pass
    except Exception: pass

def load():
    global DATA
    found = []
    for p in ALL_DB:
        d = db_read(p)
        if d: found.append(d)
    if not found:
        DATA["economy"] = dict(DEFAULT_ECO)
        db_write_all()
        return
    # Merge - keep player if in ANY DB
    found.sort(key=lambda x: len(x.get("players", {})), reverse=True)
    base = found[0]
    for k in DATA:
        if k in base: DATA[k] = base[k]
    merged = {}
    for d in found:
        for n, p in d.get("players", {}).items():
            if n not in merged: merged[n] = p
            elif (p.get("wins",0)+p.get("gold",0)) > (merged[n].get("wins",0)+merged[n].get("gold",0)):
                merged[n] = p
    DATA["players"] = merged
    # Economy: NEVER overwrite with 0 - if DB has 0, reset to your start numbers
    e = DATA.get("economy", {})
    if e.get("gold", 0) == 0 and len(merged) == 0:
        DATA["economy"] = dict(DEFAULT_ECO)
    else:
        # Keep correct start if first run, else keep saved economy
        if "bank_gold" not in e: e["bank_gold"] = 50000000
        if "bank_gems" not in e: e["bank_gems"] = 50000000
        if "gems" not in e: e["gems"] = 100000
    db_write_all()

def save(): db_write_all()
def storage_status():
    out=[]
    for p in ALL_DB:
        d=db_read(p)
        out.append({"file":p,"exists":os.path.exists(p),"players":len(d.get("players",{})) if d else 0})
    return out
load()

def norm(s): return str(s or "").strip().lower()
def getp(n):
    if not n: return None
    for k,v in DATA["players"].items():
        if norm(k)==norm(n): return v
    return None
def new_player(name,pw):
    pid="INF-"+str(random.randint(10000000,99999999)); bid="BANK INF-"+str(random.randint(10000000,99999999))
    p={"name":name,"display_name":name,"password":str(pw),"player_id":pid,"bank_id":bid,"wins":0,"losses":0,"gold":0,"gems":0,"bank_gold":0,"bank_gems":0,"cars":[],"items":[],"seen_qs":[],"galaxy_level":1,"galaxy_kills":0,"notifs":[],"friends":[],"active_loan":None,"loan_history":[],"rank":0,"last_interest":"","saved_at":int(time.time())}
    DATA["players"][name]=p; save(); return p
def check_pin(v,pin):
    if not v: return False
    if norm(v.get("name"))=="dominic": return str(pin)=="2164"
    return str(pin)==str(v.get("password"))
def notify(name,text,typ="info",extra=None):
    v=getp(name)
    if not v:
        if norm(name)=="dominic": v=new_player("dominic","2164")
        else: return
    n={"text":text,"type":typ,"time":datetime.now().strftime("%H:%M %d %b")}
    if extra: n.update(extra)
    v.setdefault("notifs",[]).append(n); save()
def find_by_id(pid):
    pid=str(pid).upper().replace("BANK ","")
    if not pid.startswith("INF-"): pid="INF-"+pid
    for v in DATA["players"].values():
        if v.get("player_id")==pid or v.get("bank_id")==pid: return v
    return None
def active_loan_of(v):
    if not v: return None
    for l in DATA["loans"]:
        if norm(l.get("from"))==norm(v["name"]) and l.get("status") in ["active","waiting_player_confirm","extended"]: return l
    return v.get("active_loan")

@app.route("/")
def home(): return make_response(HOME,200,{"Content-Type":"text/html"})
@app.route("/api/storage_status")
def api_storage():
    if norm(request.args.get("name"))!="dominic" or str(request.args.get("password"))!="2164": return jsonify({"error":"Only Dominic"}),403
    return jsonify({"db":"SQLite infinity.db + 2 backups","backups":storage_status(),"ram_players":len(DATA["players"])})
@app.route("/api/switch_status")
def sw_s(): return jsonify({"game_on":DATA.get("game_on",True)})
@app.route("/api/switch_toggle",methods=["POST"])
def sw_t():
    d=request.get_json() or {}
    if norm(d.get("admin"))!="dominic" or str(d.get("pin"))!="2164": return jsonify({"error":"Only Dominic"}),403
    DATA["game_on"]=bool(d.get("on",True)); save(); return jsonify({"ok":True,"game_on":DATA["game_on"]})
@app.route("/api/player")
def api_player():
    v=getp(request.args.get("name",""))
    if not v: return jsonify({"found":False})
    if request.args.get("password") and str(request.args.get("password"))!=str(v.get("password")): return jsonify({"found":True,"password_ok":False})
    al=active_loan_of(v)
    fr=[r for r in DATA.get("friend_requests",[]) if norm(r.get("to"))==norm(v["name"]) and r.get("status")=="pending"]
    return jsonify({"found":True,"password_ok":True,"name":v["name"],"player_id":v.get("player_id"),"bank_id":v.get("bank_id"),"wins":v.get("wins",0),"losses":v.get("losses",0),"gold":v.get("gold",0),"gems":v.get("gems",0),"bank_gold":v.get("bank_gold",0),"bank_gems":v.get("bank_gems",0),"cars":v.get("cars",[]),"items":v.get("items",[]),"seen_qs":v.get("seen_qs",[]),"galaxy_level":v.get("galaxy_level",1),"galaxy_kills":v.get("galaxy_kills",0),"notifs":v.get("notifs",[])[-30:],"friends":v.get("friends",[]),"friend_requests":fr,"active_loan":al,"loans":[x for x in DATA["loans"] if norm(x.get("from"))==norm(v["name"])],"rank":v.get("rank",0)})
@app.route("/api/restore",methods=["POST"])
def api_restore():
    d=request.get_json() or {}; name=d.get("name",""); pw=str(d.get("password","")); v=getp(name)
    if v:
        if str(v.get("password"))==pw: return jsonify({"restored":False,"found":True,"player":v})
        return jsonify({"error":"Wrong password"}),403
    v=new_player(name,pw); v["wins"]=int(d.get("wins",0) or 0); v["gold"]=int(d.get("gold",0) or 0); v["gems"]=int(d.get("gems",0) or 0); v["cars"]=d.get("cars",[]); v["items"]=d.get("items",[])
    if d.get("player_id"): v["player_id"]=d.get("player_id")
    if d.get("bank_id"): v["bank_id"]=d.get("bank_id")
    save(); return jsonify({"restored":True,"found":True,"player":v})
@app.route("/api/score",methods=["POST"])
def api_score():
    d=request.get_json() or {}; v=getp(d.get("name"))
    if not v: v=new_player(d.get("name","Player"),d.get("password","0000"))
    if int(d.get("wins",0))>v.get("wins",0): v["wins"]=int(d.get("wins",0))
    if int(d.get("gold",0))>v.get("gold",0): v["gold"]=int(d.get("gold",0))
    if int(d.get("gems",0))>v.get("gems",0): v["gems"]=int(d.get("gems",0))
    if d.get("cars") is not None and len(d.get("cars",[]))>len(v.get("cars",[])): v["cars"]=d.get("cars")
    v["saved_at"]=int(time.time()); save(); return jsonify({"ok":True})
@app.route("/api/leaderboard")
def api_leader():
    mode=request.args.get("mode","pvp"); ps=list(DATA["players"].values())
    if mode=="gold": ps.sort(key=lambda x:x.get("gold",0),reverse=True)
    elif mode=="gems": ps.sort(key=lambda x:x.get("gems",0),reverse=True)
    else: ps.sort(key=lambda x:x.get("wins",0),reverse=True)
    out=[]
    for i,p in enumerate(ps[:50]): out.append({"name":p["name"],"player_id":p.get("player_id"),"wins":p.get("wins",0),"losses":p.get("losses",0),"gold":p.get("gold",0),"gems":p.get("gems",0),"rank":i+1,"active_loan":bool(active_loan_of(p))})
    return jsonify({"players":out})
@app.route("/api/transfer",methods=["POST"])
def api_transfer():
    d=request.get_json() or {}; v=getp(d.get("sender"))
    if not v or not check_pin(v,d.get("pin","")): return jsonify({"error":"Wrong PIN"}),403
    r=find_by_id(d.get("receiver_id","")); amt=int(d.get("amount",0))
    if not r: return jsonify({"error":"Receiver not found"}),404
    if amt<=0 or v.get("gold",0)<amt: return jsonify({"error":"Not enough Gold"}),400
    v["gold"]-=amt; r["gold"]=r.get("gold",0)+amt; notify(r["name"],"💸 "+v["name"]+" sent you "+str(amt)+" Gold"); save(); return jsonify({"ok":True,"sender_gold":v["gold"]})
@app.route("/api/bank_action",methods=["POST"])
def api_bank():
    d=request.get_json() or {}; v=getp(d.get("name"))
    if not v or not check_pin(v,d.get("pin","")): return jsonify({"error":"Wrong PIN"}),403
    amt=int(d.get("amount",0)); cur=d.get("currency","Gold"); is_gold=(cur=="Gold")
    if d.get("action")=="deposit":
        if is_gold:
            if v.get("gold",0)<amt: return jsonify({"error":"Not enough"}),400
            v["gold"]-=amt; v["bank_gold"]=v.get("bank_gold",0)+amt; DATA["economy"]["bank_gold"]+=amt
        else:
            if v.get("gems",0)<amt: return jsonify({"error":"Not enough"}),400
            v["gems"]-=amt; v["bank_gems"]=v.get("bank_gems",0)+amt; DATA["economy"]["bank_gems"]+=amt
    else:
        if is_gold:
            if v.get("bank_gold",0)<amt: return jsonify({"error":"Not enough in Bank"}),400
            v["bank_gold"]-=amt; v["gold"]=v.get("gold",0)+amt; DATA["economy"]["bank_gold"]-=amt
        else:
            if v.get("bank_gems",0)<amt: return jsonify({"error":"Not enough in Bank"}),400
            v["bank_gems"]-=amt; v["gems"]=v.get("gems",0)+amt; DATA["economy"]["bank_gems"]-=amt
    save(); return jsonify({"ok":True,"gold":v["gold"],"gems":v["gems"],"bank_gold":v.get("bank_gold",0),"bank_gems":v.get("bank_gems",0)})
@app.route("/api/bank_interest",methods=["POST"])
def api_interest():
    d=request.get_json() or {}; v=getp(d.get("name"))
    if not v or not check_pin(v,d.get("pin","")): return jsonify({"error":"Wrong PIN"}),403
    month=datetime.now().strftime("%Y-%m")
    if v.get("last_interest")==month: return jsonify({"error":"Already claimed this month"}),400
    bg=int(v.get("bank_gold",0)*0.10); bm=int(v.get("bank_gems",0)*0.10)
    v["bank_gold"]=v.get("bank_gold",0)+bg; v["bank_gems"]=v.get("bank_gems",0)+bm; v["last_interest"]=month
    notify(v["name"],"🎁 Bank Interest +10%: +"+str(bg)+" Gold, +"+str(bm)+" Germs"); save()
    return jsonify({"ok":True,"bonus_gold":bg,"bonus_gems":bm,"bank_gold":v["bank_gold"],"bank_gems":v["bank_gems"]})
@app.route("/api/exchange",methods=["POST"])
def api_exchange():
    d=request.get_json() or {}; v=getp(d.get("name")); amt=int(d.get("amount",0)); direction=d.get("direction","gold_to_gem")
    if not v or not check_pin(v,d.get("pin","")): return jsonify({"error":"Wrong PIN"}),403
    if direction=="gold_to_gem":
        gems=amt//100
        if gems<1 or v.get("gold",0)<gems*100: return jsonify({"error":"Need 100 Gold = 1 Germ"}),400
        v["gold"]-=gems*100; v["gems"]=v.get("gems",0)+gems
    else:
        if v.get("gems",0)<amt: return jsonify({"error":"Not enough Gems"}),400
        v["gems"]-=amt; v["gold"]=v.get("gold",0)+amt*100
    save(); return jsonify({"ok":True,"gold":v["gold"],"gems":v["gems"]})
@app.route("/api/loan_apply",methods=["POST"])
def loan_apply():
    d=request.get_json() or {}; v=getp(d.get("name")); amt=int(d.get("amount",0))
    if not v or not check_pin(v,d.get("pin","")): return jsonify({"error":"Wrong PIN"}),403
    if active_loan_of(v): return jsonify({"error":"You already have ACTIVE loan. Pay it first!"}),400
    # Loan money must exist in server economy
    cur=d.get("currency","Gold")
    if cur=="Gold" and DATA["economy"]["gold"]<amt: return jsonify({"error":"Server economy does not have enough Gold"}),400
    if cur=="Gems" and DATA["economy"]["gems"]<amt: return jsonify({"error":"Server economy does not have enough Germs"}),400
    lid="LN-"+str(random.randint(10000000,99999999))
    loan={"id":lid,"from":v["display_name"],"from_id":v.get("player_id"),"amount":amt,"currency":cur,"repay_date":d.get("repay_date",""),"original_date":d.get("repay_date",""),"status":"pending_dominic","new_date":"","dominic_new_date":"","extended":False}
    DATA["loans"].append(loan)
    notify("dominic","LOAN: "+v["display_name"]+" wants "+str(amt)+" "+cur+" repay "+loan["repay_date"],"loan_request",{"loan_id":lid,"amount":amt,"currency":cur,"repay_date":loan["repay_date"],"from":v["display_name"]})
    save(); return jsonify({"ok":True})
@app.route("/api/loan_dominic",methods=["POST"])
def loan_dom():
    d=request.get_json() or {}
    if norm(d.get("admin"))!="dominic" or str(d.get("pin"))!="2164": return jsonify({"error":"Only Dominic"}),403
    for l in list(DATA["loans"]):
        if l["id"]==d.get("loan_id"):
            dom=getp("dominic")
            if not d.get("approve"):
                # DECLINE = delete loan + delete Dominic notification
                if dom: dom["notifs"]=[n for n in dom.get("notifs",[]) if not (n.get("type")=="loan_request" and n.get("loan_id")==l["id"])]
                notify(l["from"],"Loan DECLINED by Dominic")
                DATA["loans"]=[x for x in DATA["loans"] if x["id"]!=l["id"]]; save(); return jsonify({"ok":True})
            # APPROVE = delete Dominic notification + delete from Dominic list, move to waiting
            if dom: dom["notifs"]=[n for n in dom.get("notifs",[]) if not (n.get("type")=="loan_request" and n.get("loan_id")==l["id"])]
            l["new_date"]=d.get("new_date") or l["repay_date"]; l["dominic_new_date"]=l["new_date"]; l["status"]="waiting_player_confirm"
            notify(l["from"],"Dominic APPROVED your loan! Date: "+l["new_date"]+" - Tap Yes to receive.","loan_date_change",{"loan_id":l["id"],"new_date":l["new_date"]})
            save(); return jsonify({"ok":True})
    return jsonify({"error":"Not found"}),404
@app.route("/api/loan_player_confirm",methods=["POST"])
def loan_player_confirm():
    d=request.get_json() or {}; v=getp(d.get("name"))
    if not v: return jsonify({"error":"No player"}),404
    for l in list(DATA["loans"]):
        if l["id"]==d.get("loan_id"):
            if l.get("status")=="active":
                v["notifs"]=[n for n in v.get("notifs",[]) if not (n.get("type")=="loan_date_change" and n.get("loan_id")==l["id"])]; save(); return jsonify({"error":"Already claimed!"}),400
            if d.get("approve"):
                l["status"]="active"; l["repay_date"]=l.get("dominic_new_date") or l["repay_date"]; v["active_loan"]=l
                # MONEY COMES FROM SERVER ECONOMY
                if l["currency"]=="Gold":
                    DATA["economy"]["gold"]-=l["amount"]; v["gold"]=v.get("gold",0)+l["amount"]
                else:
                    DATA["economy"]["gems"]-=l["amount"]; v["gems"]=v.get("gems",0)+l["amount"]
                v["notifs"]=[n for n in v.get("notifs",[]) if not (n.get("type")=="loan_date_change" and n.get("loan_id")==l["id"])]
                v["notifs"].append({"text":"✅ Loan APPROVED & RECEIVED: +"+str(l["amount"])+" "+l["currency"]+" - Repay by "+l["repay_date"]+" - PENDING in Profile","type":"loan_active","time":datetime.now().strftime("%H:%M %d %b")})
                notify("dominic",v["name"]+" received Loan "+str(l["amount"])+" "+l["currency"]+" from Server Economy")
            else:
                v["notifs"]=[n for n in v.get("notifs",[]) if not (n.get("type")=="loan_date_change" and n.get("loan_id")==l["id"])]
                DATA["loans"]=[x for x in DATA["loans"] if x["id"]!=l["id"]]
                notify("dominic",v["name"]+" declined Loan - Refunded")
            save(); return jsonify({"ok":True})
    return jsonify({"error":"Not found / Already claimed"}),404
@app.route("/api/loan_repay",methods=["POST"])
def loan_repay():
    d=request.get_json() or {}; v=getp(d.get("name"))
    if not v or not check_pin(v,d.get("pin","")): return jsonify({"error":"Wrong PIN"}),403
    loan=None
    for l in DATA["loans"]:
        if l["id"]==d.get("loan_id") and norm(l.get("from"))==norm(v["name"]): loan=l; break
    if not loan or loan.get("status") not in ["active","extended"]: return jsonify({"error":"No active loan"}),404
    amt=loan["amount"]; cur=loan["currency"]
    if cur=="Gold":
        if v.get("gold",0)<amt: return jsonify({"error":"Not enough Gold. Ask Extension or server will deduct Wins."}),400
        v["gold"]-=amt; DATA["economy"]["gold"]+=amt
    else:
        if v.get("gems",0)<amt: return jsonify({"error":"Not enough Germs"}),400
        v["gems"]-=amt; DATA["economy"]["gems"]+=amt
    DATA["loans"]=[x for x in DATA["loans"] if x["id"]!=loan["id"]]; v["active_loan"]=None
    v.setdefault("loan_history",[]).append({"amount":amt,"currency":cur,"status":"paid","date":datetime.now().strftime("%Y-%m-%d")})
    notify(v["name"],"✅ Loan PAID: "+str(amt)+" "+cur); save(); return jsonify({"ok":True,"gold":v["gold"],"gems":v["gems"]})
@app.route("/api/loan_due",methods=["POST"])
def loan_due():
    d=request.get_json() or {}; v=getp(d.get("name"))
    if not v: return jsonify({"error":"No player"}),404
    loan=None
    for l in DATA["loans"]:
        if l["id"]==d.get("loan_id") and norm(l.get("from"))==norm(v["name"]): loan=l; break
    if not loan: return jsonify({"error":"No loan"}),404
    if d.get("action","extend")=="extend" and not loan.get("extended"):
        try:
            old=datetime.strptime(loan["repay_date"],"%Y-%m-%d"); loan["repay_date"]=(old+timedelta(days=7)).strftime("%Y-%m-%d")
        except Exception: pass
        loan["extended"]=True; loan["status"]="extended"; v["active_loan"]=loan
        notify(v["name"],"⏳ Extension: New date "+loan["repay_date"]+" - Next time server COLLECTS."); save(); return jsonify({"ok":True,"new_date":loan["repay_date"]})
    amt=loan["amount"]; cur=loan["currency"]; wins_taken=0
    if cur=="Gold":
        have=v.get("gold",0)
        if have>=amt: v["gold"]-=amt; DATA["economy"]["gold"]+=amt
        else: v["gold"]=0; wins_taken=((amt-have)+999)//1000; v["wins"]=max(0,v.get("wins",0)-wins_taken); DATA["economy"]["gold"]+=have
    else:
        have=v.get("gems",0)
        if have>=amt: v["gems"]-=amt; DATA["economy"]["gems"]+=amt
        else: v["gems"]=0; wins_taken=((amt-have)+9)//10; v["wins"]=max(0,v.get("wins",0)-wins_taken); DATA["economy"]["gems"]+=have
    DATA["loans"]=[x for x in DATA["loans"] if x["id"]!=loan["id"]]; v["active_loan"]=None
    notify(v["name"],"⚠️ Server COLLECTED Loan: Deducted "+str(wins_taken)+" Wins (1 Win = 1000 Gold / 10 Germs). Rank dropped!"); save(); return jsonify({"ok":True,"wins_taken":wins_taken,"wins":v["wins"]})
@app.route("/api/request_money",methods=["POST"])
def api_req():
    d=request.get_json() or {}; v=getp(d.get("name"))
    if not v: return jsonify({"error":"No player"}),404
    rid="RQ-"+str(random.randint(10000000,99999999)); amt=int(d.get("amount") or 0)
    r={"id":rid,"from":v["display_name"],"amount":amt,"currency":d.get("currency","Gold"),"message":d.get("message","")}
    DATA["requests"].append(r); notify("dominic","🔒 SECRET: "+v["display_name"]+" wants "+str(amt)+" "+r["currency"],"request",{"request_id":rid,"amount":amt,"currency":r["currency"]}); save(); return jsonify({"ok":True})
@app.route("/api/request_approve",methods=["POST"])
def api_req_ap():
    d=request.get_json() or {}
    if norm(d.get("admin"))!="dominic" or str(d.get("pin"))!="2164": return jsonify({"error":"Only Dominic"}),403
    for r in DATA["requests"]:
        if r["id"]==d.get("request_id"):
            v=getp(r["from"])
            if v:
                if d.get("currency","Gold")=="Gold": v["gold"]=v.get("gold",0)+int(d.get("amount",0)); DATA["economy"]["gold"]-=int(d.get("amount",0))
                else: v["gems"]=v.get("gems",0)+int(d.get("amount",0)); DATA["economy"]["gems"]-=int(d.get("amount",0))
                notify(v["name"],"🔒 Secret Approved: +"+str(d.get("amount",0))+" "+d.get("currency","Gold"))
                # Delete Dominic notification for this request
                dom=getp("dominic")
                if dom: dom["notifs"]=[n for n in dom.get("notifs",[]) if not (n.get("type")=="request" and n.get("request_id")==r["id"])]
            DATA["requests"]=[x for x in DATA["requests"] if x["id"]!=r["id"]]; save(); return jsonify({"ok":True})
    return jsonify({"error":"Not found"}),404
@app.route("/api/buy_item",methods=["POST"])
def api_buy():
    d=request.get_json() or {}; v=getp(d.get("name"))
    if not v or not check_pin(v,d.get("pin","")): return jsonify({"error":"Wrong PIN"}),403
    item=d.get("item",""); price=int(d.get("price",0))
    if v.get("gold",0)<price: return jsonify({"error":"Not enough Gold"}),400
    if item in v.get("cars",[]) or item in v.get("items",[]): return jsonify({"error":"Already owned"}),400
    v["gold"]-=price
    if any(x in item for x in ["Toyota","BMW","Lamborghini","Ferrari","Tesla","Mercedes","Audi","Rover","Hilux","Nissan","Bugatti"]): v.setdefault("cars",[]).append(item)
    else: v.setdefault("items",[]).append(item)
    save(); return jsonify({"ok":True,"gold":v["gold"]})
@app.route("/api/consume",methods=["POST"])
def api_consume():
    d=request.get_json() or {}; v=getp(d.get("name"))
    if not v or not check_pin(v,d.get("pin","")): return jsonify({"error":"Wrong PIN"}),403
    p=d.get("product","")
    if p in v.get("items",[]): v["items"].remove(p)
    v["wins"]=v.get("wins",0)+int(d.get("bonus",20)); save(); return jsonify({"ok":True,"wins":v["wins"]})
@app.route("/api/lottery",methods=["POST"])
def api_lot():
    d=request.get_json() or {}; v=getp(d.get("name"))
    if not v or not check_pin(v,d.get("pin","")): return jsonify({"error":"Wrong PIN"}),403
    bet=int(d.get("bet",0)); cur=d.get("currency","Gold")
    if bet<=0: return jsonify({"error":"Bet > 0"}),400
    if cur=="Gold":
        if v.get("gold",0)<bet: return jsonify({"error":"Not enough Gold"}),400
        v["gold"]-=bet
    else:
        if v.get("gems",0)<bet: return jsonify({"error":"Not enough Gems"}),400
        v["gems"]-=bet
    win=random.random()<0.35
    if win:
        prize=bet*2
        if cur=="Gold": v["gold"]+=prize
        else: v["gems"]+=prize
        res={"win":True,"prize":prize,"lost":0}
    else: res={"win":False,"prize":0,"lost":bet}; DATA["economy"]["lottery"]=DATA["economy"].get("lottery",0)+bet
    save(); return jsonify({"ok":True,"gold":v["gold"],"gems":v["gems"],"result":res})
@app.route("/api/announce",methods=["POST"])
def api_ann():
    d=request.get_json() or {}
    if norm(d.get("admin"))!="dominic" or str(d.get("pin"))!="2164": return jsonify({"error":"Only Dominic"}),403
    DATA["announcements"].append({"text":d.get("text",""),"time":datetime.now().strftime("%H:%M")})
    for v in DATA["players"].values(): v.setdefault("notifs",[]).append({"text":"📢 "+d.get("text",""),"type":"announce","time":datetime.now().strftime("%H:%M")})
    save(); return jsonify({"ok":True})
@app.route("/api/announcements")
def api_anns(): return jsonify({"announcements":DATA["announcements"][-5:]})
@app.route("/api/economy")
def api_eco():
    if norm(request.args.get("name"))!="dominic" or str(request.args.get("password"))!="2164": return jsonify({"error":"Only Dominic"}),403
    e=DATA["economy"]; e["history"]=(e.get("history",[])+[e.get("gold",100000000)])[-20:]
    # DO NOT overwrite gems/bank with sums - keep real server numbers
    save()
    pending=[x for x in DATA["loans"] if x.get("status")=="pending_dominic"]
    return jsonify({"economy":e,"requests":DATA["requests"],"loans":pending,"is_negative":e.get("gold",100000000)<0,"backups":storage_status()})
@app.route("/api/emergency",methods=["POST"])
def api_em():
    d=request.get_json() or {}
    if norm(d.get("name"))!="dominic" or str(d.get("pin"))!="2164": return jsonify({"error":"Only Dominic"}),403
    if DATA["economy"].get("gold",100000000)>=0: return jsonify({"error":"Not negative - Locked"}),400
    v=getp("dominic") or new_player("dominic","2164"); DATA["economy"].update({"gold":100000000,"gems":100000,"bank_gold":50000000,"bank_gems":50000000}); v["gold"]=v.get("gold",0)+500000000000; save(); return jsonify({"ok":True})
@app.route("/api/server_info")
def api_srv():
    if norm(request.args.get("name"))!="dominic" or str(request.args.get("password"))!="2164": return jsonify({"error":"Only Dominic"}),403
    return jsonify({"players":len(DATA["players"]),"earning_on":True,"reviews":DATA["reviews"][-20:],"backups":storage_status()})
@app.route("/api/review",methods=["POST"])
def api_rev():
    d=request.get_json() or {}; DATA["reviews"].append({"name":d.get("name"),"type":d.get("type"),"text":d.get("text")}); save(); return jsonify({"ok":True})
@app.route("/api/friends")
def api_friends():
    v=getp(request.args.get("name",""))
    if not v: return jsonify({"friends":[],"requests":[]})
    out=[]
    for fn in v.get("friends",[]):
        fv=getp(fn)
        if fv: out.append({"name":fv["name"],"player_id":fv.get("player_id")})
    reqs=[r for r in DATA.get("friend_requests",[]) if norm(r.get("to"))==norm(v["name"]) and r.get("status")=="pending"]
    return jsonify({"friends":out,"requests":reqs})
@app.route("/api/friend_request",methods=["POST"])
def api_fr():
    d=request.get_json() or {}; v=getp(d.get("name")); t=find_by_id(d.get("target_id",""))
    if not v or not t: return jsonify({"error":"Not found"}),404
    if norm(t["name"])==norm(v["name"]): return jsonify({"error":"Cannot add yourself"}),400
    if t["name"] in v.get("friends",[]): return jsonify({"error":"Already friends"}),400
    for r in DATA.get("friend_requests",[]):
        if norm(r.get("from"))==norm(v["name"]) and norm(r.get("to"))==norm(t["name"]) and r.get("status")=="pending": return jsonify({"error":"Request already sent"}),400
    DATA.setdefault("friend_requests",[]).append({"id":"FR-"+str(random.randint(10000000,99999999)),"from":v["display_name"],"to":t["display_name"],"status":"pending"})
    notify(t["name"],"👥 Friend Request from "+v["display_name"]+" - Accept in Profile!","friend_request"); save(); return jsonify({"ok":True})
@app.route("/api/friend_respond",methods=["POST"])
def api_fresp():
    d=request.get_json() or {}; v=getp(d.get("name"))
    if not v: return jsonify({"error":"No player"}),404
    for r in DATA.get("friend_requests",[]):
        if r["id"]==d.get("request_id") and norm(r.get("to"))==norm(v["name"]):
            if d.get("accept"):
                r["status"]="accepted"; f=getp(r["from"])
                if f and f["name"] not in v.get("friends",[]): v.setdefault("friends",[]).append(f["name"])
                if f and v["name"] not in f.get("friends",[]): f.setdefault("friends",[]).append(v["name"])
                notify(r["from"],"✅ "+v["display_name"]+" ACCEPTED your Friend Request!")
            else: r["status"]="declined"; notify(r["from"],"❌ "+v["display_name"]+" declined Friend Request")
            save(); return jsonify({"ok":True})
    return jsonify({"error":"Not found"}),404
@app.route("/api/chat_send",methods=["POST"])
def api_chat_send():
    d=request.get_json() or {}; key="|".join(sorted([norm(d.get("sender","")),norm(d.get("to",""))])); DATA["chats"].setdefault(key,[]).append({"from":d.get("sender",""),"text":d.get("text","")}); save(); return jsonify({"ok":True})
@app.route("/api/chat_get")
def api_chat_get():
    key="|".join(sorted([norm(request.args.get("a","")),norm(request.args.get("b",""))])); return jsonify({"messages":DATA["chats"].get(key,[])})

HOME = r"""<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>INFINITY BOT v33 - DB</title><link href="https://fonts.googleapis.com/css2?family=Great+Vibes&family=Poppins:wght@400;700;900&display=swap" rel="stylesheet"><style>*{box-sizing:border-box}body{margin:0;font-family:Poppins,Arial;color:#fff;background:radial-gradient(circle at 50% 20%,#3a0a5e,#12002b 70%);min-height:100vh}.cursive{font-family:'Great Vibes',cursive}.topbar{display:flex;justify-content:space-between;padding:8px 14px}.profile{width:40px;height:40px;border-radius:50%;background:linear-gradient(135deg,#ff006e,#ffd700);display:flex;align-items:center;justify-content:center;border:2px solid #fff;cursor:pointer}.center{min-height:82vh;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:20px}.crownBig{font-size:90px}.enterBtn{padding:16px 70px;font-family:'Great Vibes',cursive;font-size:48px;border:none;border-radius:60px;background:linear-gradient(90deg,#ff006e,#ffd700,#00e5ff);cursor:pointer}.card{background:rgba(255,255,255,.08);border:2px solid rgba(255,255,255,.35);border-radius:26px;padding:20px;margin:14px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.box{background:linear-gradient(160deg,rgba(255,255,255,.18),rgba(0,0,0,.4));border:2px solid #fff;border-radius:24px;padding:22px 10px;text-align:center;cursor:pointer}.box span{font-size:38px;display:block}button{cursor:pointer}.btn{width:100%;padding:14px;border:none;border-radius:25px;font-weight:900;background:#ffd700;margin:6px 0}.btn:disabled{opacity:.4}.btn2{width:100%;padding:13px;border-radius:25px;border:2px solid #00e5ff;background:transparent;color:#00e5ff;font-weight:900;margin:6px 0}.opt{width:100%;padding:13px;margin:7px 0;border-radius:16px;border:2px solid #fff;background:rgba(0,0,0,.5);color:#fff;font-weight:700;cursor:pointer;text-align:left}input,select,textarea{width:100%;padding:14px;border-radius:14px;border:2px solid #ffd700;margin:8px 0;font-size:16px;background:#fff;color:#000}.hidden{display:none!important}.leadRow{display:flex;justify-content:space-between;align-items:center;padding:10px 12px;background:rgba(0,0,0,.45);border-radius:14px;margin:6px 0;cursor:pointer}.toast{position:fixed;top:70px;left:50%;transform:translateX(-50%);background:#fff;color:#000;padding:12px 18px;border-radius:20px;font-weight:700;z-index:999;max-width:90%;text-align:center}.gameOverlay{position:fixed;inset:0;background:rgba(0,0,0,.75);display:flex;align-items:center;justify-content:center;padding:16px;z-index:500}.gamePopup{background:linear-gradient(160deg,#2b005e,#12002b);border:3px solid #ffd700;border-radius:28px;padding:22px 18px;max-width:420px;width:100%;text-align:center}.choiceRow{display:flex;gap:12px;margin-top:16px}.choiceBox{flex:1;padding:18px 8px;border-radius:20px;cursor:pointer;font-weight:900;border:3px solid #fff}.choiceNo{background:#ff2222;color:#fff}.choiceYes{background:#00cc44;color:#000}.bottomNav{position:fixed;bottom:0;left:0;right:0;background:rgba(0,0,0,.85);border-top:2px solid #ffd700;display:flex;justify-content:space-around;padding:10px 0 14px;z-index:200}.bottomNav div{font-size:28px;cursor:pointer;text-align:center}.bottomNav small{display:block;font-size:10px;color:#ffd700}.walletCard{background:linear-gradient(135deg,#ffd700,#ff006e);color:#000;border-radius:24px;padding:18px;text-align:center}.bigBankBox{padding:22px 10px;border-radius:24px;border:2px solid #fff;text-align:center;cursor:pointer;background:linear-gradient(160deg,rgba(255,255,255,.18),rgba(0,0,0,.4))}.loanGreen{border:4px solid #00ff88!important;background:linear-gradient(160deg,#00cc44,#00ff88)!important;color:#000!important}.idPrefix{display:flex;align-items:center;background:#fff;border-radius:14px;border:2px solid #ffd700;padding:0 10px;margin:8px 0}.idPrefix b{color:#000}.idPrefix input{border:none;flex:1;margin:0}.timerBar{height:14px;background:#333;border-radius:99px;overflow:hidden}.timerFill{height:100%;background:linear-gradient(90deg,#00ff88,#ffd700,#ff2222)}.fallArea{position:relative;height:420px;background:linear-gradient(#000428,#004e92);border:2px solid #00e5ff;border-radius:18px;overflow:hidden}.fallItem{position:absolute;font-size:34px;cursor:pointer}.tabBox{flex:1;padding:12px 4px;border-radius:16px;background:rgba(255,255,255,.15);border:2px solid #ffd700;text-align:center;cursor:pointer;font-weight:900;font-size:13px}.tabBox.active{background:#ffd700;color:#000}.pinInput{font-size:28px;text-align:center;letter-spacing:12px}.shopGrid{display:grid;grid-template-columns:1fr 1fr;gap:10px}.shopBox{background:rgba(255,255,255,.12);border:2px solid rgba(255,255,255,.5);border-radius:18px;padding:12px;text-align:center}.catTab{padding:8px 4px;border-radius:12px;background:rgba(255,255,255,.12);border:1px solid #ffd700;text-align:center;cursor:pointer;font-size:11px;font-weight:900}.catTab.active{background:#ffd700;color:#000}#menuDrop{position:fixed!important;top:108px!important;right:8px!important;width:200px!important;background:#1a1a2e;border:2px solid #ffd700;border-radius:14px;padding:6px;z-index:900}#menuDrop div{padding:8px!important;font-size:12px!important}</style></head><body>
<div id="frozenOverlay" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.92);z-index:2000;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:20px"><div style="font-size:80px">❄️</div><h1>GAME PAUSED</h1><p style="color:#ffd700;font-weight:900">SWITCHED OFF BY DOMINIC</p><div id="frozenDominicBox" style="display:none;margin-top:20px;background:#1a1a2e;border:2px solid #ffd700;border-radius:20px;padding:16px;width:100%;max-width:320px"><p>👑 Dominic Only</p><input id="frozenPin" type="password" inputmode="numeric" maxlength="4" placeholder="2164"><button class="btn" type="button" onclick="dominicUnfreeze()">🔓 TURN GAME ON</button></div></div>
<div id="loanDatePopup" class="gameOverlay hidden" style="display:none;z-index:1200"><div class="gamePopup"><div style="font-size:50px">📅</div><h2>Dominic Changed Date</h2><p id="loanDatePopupText"></p><p style="font-size:12px">This popup is from INFINITY BOT GAME - not your browser.</p><label>New Repay Date (Dominic's choice):</label><input id="loanDateInput" type="date" readonly style="background:#ffe"><div class="choiceRow"><div class="choiceBox choiceNo" onclick="loanDateRespond(false)">❌ No - Refund</div><div class="choiceBox choiceYes" onclick="loanDateRespond(true)">✅ Yes - Receive Loan</div></div></div></div>
<div id="loanDueOverlay" class="gameOverlay hidden" style="display:none;z-index:1100"><div class="gamePopup"><div style="font-size:50px">⏰</div><h2>LOAN DUE!</h2><p id="loanDueText"></p><p style="font-size:12px">1 Win = 1000 Gold / 10 Germs. Wins CANNOT be sold - only server deducts.</p><div class="choiceRow"><div class="choiceBox choiceNo" onclick="loanDueAction('extend')">⏳ Extension +7 Days</div><div class="choiceBox choiceYes" onclick="loanDueAction('collect')">💰 Pay / Collect Now</div></div></div></div>
<div id="announceBar" class="hidden" style="position:fixed;top:0;left:0;right:0;background:#ffd700;color:#000;padding:10px;text-align:center;font-weight:900;z-index:1000">📢</div>
<div class="topbar"><div><span id="catTime" style="font-size:12px;background:rgba(0,0,0,.55);border:1px solid #ffd700;padding:5px 9px;border-radius:20px">00:00:00 CAT</span><br><span id="catDate" style="font-size:10px;background:rgba(0,0,0,.45);padding:3px 8px;border-radius:20px">Central Africa</span><br><div style="font-weight:900">INFINITY BOT</div><div style="font-size:10px;color:#00ff88">🗄️ DB: infinity.db + 2 Backups - 256GB Style</div></div><div id="topRight" style="display:none;flex-direction:column;align-items:flex-end;gap:2px"><div style="display:flex;gap:6px"><div id="soundBtn" style="width:30px;height:30px;border-radius:50%;background:rgba(0,0,0,.55);border:1px solid #ffd700;display:flex;align-items:center;justify-content:center;cursor:pointer">🔊</div><div onclick="openShop()" style="width:30px;height:30px;border-radius:50%;background:rgba(0,0,0,.55);border:1px solid #ffd700;display:flex;align-items:center;justify-content:center;cursor:pointer">🛍️</div><div class="profile" id="profileBtn">👤</div></div><div id="menuBtn" style="width:30px;height:30px;border-radius:50%;background:rgba(0,0,0,.55);border:1px solid #ffd700;display:flex;align-items:center;justify-content:center;cursor:pointer">⋮</div></div></div>
<div id="menuDrop" class="hidden"></div><div id="toast" class="toast hidden"></div>
<div id="pinOverlay" class="gameOverlay hidden" style="display:none;z-index:900"><div class="gamePopup"><h2>Enter PIN</h2><p id="pinDesc"></p><input id="pinInput" class="pinInput" placeholder="...." maxlength="4" inputmode="numeric" type="password"><div class="choiceRow"><div class="choiceBox choiceNo" onclick="closePin()">❌ Cancel</div><div class="choiceBox choiceYes" onclick="confirmPin()">✅ Confirm</div></div></div></div>
<div id="announceOverlay" class="gameOverlay hidden" style="display:none;z-index:960"><div class="gamePopup"><h2>📢 Announcement</h2><textarea id="annText" style="height:100px"></textarea><button class="btn" type="button" onclick="sendAnnounce()">📢 Announce</button><button class="btn2" type="button" onclick="closeAnnounce()">Cancel</button></div></div>
<div id="secretOverlay" class="gameOverlay hidden" style="display:none;z-index:920"><div class="gamePopup"><h2>🔒 Secret</h2><input id="reqMsg" type="password" placeholder="Secret message"><input id="reqAmt" type="password" inputmode="numeric" placeholder="Amount"><select id="reqCur"><option>Gold</option><option>Gems</option></select><div class="choiceRow"><div class="choiceBox choiceNo" onclick="closeSecret()">❌ Cancel</div><div class="choiceBox choiceYes" onclick="sendMoneyRequest()">📩 Send</div></div></div></div>
<div id="loanOverlay" class="gameOverlay hidden" style="display:none;z-index:920"><div class="gamePopup"><h2>🏦 Apply for Loan</h2><input id="loanAmt" type="number" placeholder="Amount"><select id="loanCur"><option>Gold</option><option>Gems</option></select><label>When to repay?</label><input id="loanDate" type="date"><div class="choiceRow"><div class="choiceBox choiceNo" onclick="closeLoan()">❌ Cancel</div><div class="choiceBox choiceYes" onclick="submitLoan()">📩 Apply</div></div></div></div>
<div id="page-welcome" class="gameOverlay hidden" style="display:none;z-index:950"><div class="gamePopup"><h2>Do you already have an account?</h2><div class="choiceRow"><div class="choiceBox choiceNo" onclick="welcomeChoice('no')">❌ No</div><div class="choiceBox choiceYes" onclick="welcomeChoice('yes')">✅ Yes</div></div></div></div>
<div id="page-home" class="center"><div style="font-size:26px">✨ 💖 ⭐ 🌟 💫</div><div class="crownBig">👑</div><h1 class="cursive" style="font-size:68px;margin:5px">Infinity Bot</h1><p style="letter-spacing:3px;font-weight:900">DOMINIC MASTIRIA</p><p style="font-size:11px;color:#00ff88">🗄️ DB Storage - Never Lose Account</p><button class="enterBtn" id="enterBtn" type="button">Enter</button></div>
<div id="page-register" class="hidden" style="max-width:520px;margin:0 auto;padding:20px 14px"><div class="card" style="text-align:center"><h1 class="cursive" style="font-size:48px">Register</h1><div id="registerForm"><input id="regName" placeholder="Your Name" maxlength="20"><input id="regPass" placeholder="...." maxlength="4" inputmode="numeric" type="password"><button class="btn" type="button" onclick="doRegister()">📝 REGISTER</button><p>Already? <b style="color:#ffd700;cursor:pointer" onclick="showLogin()">Login</b></p></div><div id="loginForm" class="hidden"><input id="loginName" placeholder="Your Name"><input id="loginPass" placeholder="...." maxlength="4" inputmode="numeric" type="password"><button class="btn" type="button" onclick="doLogin()">🔓 LOGIN</button><p>New? <b style="color:#ffd700;cursor:pointer" onclick="showRegister()">Register</b></p><p style="font-size:11px;color:#aaa">Saved in DB + 2 backups + phone. Login on any phone.</p></div></div></div>
<div id="page-dash" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div style="text-align:center"><h2 class="cursive" style="font-size:44px" id="welcomeText">Welcome 👑</h2><span style="padding:5px 10px;border-radius:20px;background:rgba(0,0,0,.5);border:1px solid #ffd700;font-size:12px">⭐ Rank: <b id="myRank">#-</b></span> <span style="padding:5px 10px;border-radius:20px;background:rgba(0,0,0,.5);border:1px solid #ffd700;font-size:12px">🚗 Cars: <b id="myCarsCount">0</b> = +<span id="myExtraTime">0</span>s</span><div id="dashLoanBox" style="margin-top:10px"></div></div><div class="grid"><div class="box" onclick="openRiddles()"><span>🧩</span><b>RIDDLES</b></div><div class="box" onclick="openBible()"><span>📖</span><b>BIBLE FIGHT</b></div><div class="box" onclick="openSciFi()"><span>🚀</span><b>SCI-FI</b></div><div class="box" onclick="openMessages()"><span>💚</span><b>WHATSAPP</b></div></div><div class="card"><h3 style="text-align:center;margin:0">🏆 TOP 5 🏆</h3><div id="leaderList">Loading...</div><button class="btn2" type="button" onclick="openFullLeader()">👀 Full Leaderboard</button></div></div>
<div id="page-leader" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h3 style="text-align:center">🏆 LEADERBOARD</h3><div style="display:flex;gap:8px"><div class="tabBox" id="tabGold" onclick="setLeaderMode('gold')">🪙 Gold</div><div class="tabBox" id="tabGems" onclick="setLeaderMode('gems')">💎 Germ</div><div class="tabBox active" id="tabPvp" onclick="setLeaderMode('pvp')">⚔️ PvP</div></div><div id="fullLeaderList" style="margin-top:10px">Loading...</div></div></div>
<div id="page-game" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 id="gameTitle" style="text-align:center">Game</h2><div id="gameBody"></div></div></div>
<div id="page-coming" class="hidden" style="max-width:520px;margin:0 auto;padding:40px 20px 110px;text-align:center"><div style="font-size:80px">🚀</div><h1 class="cursive" style="font-size:54px">Coming Soon</h1><h2>SCI-FI - 25 Dec 2026</h2><p id="countDown" style="font-size:28px;color:#ffd700;font-weight:900"></p></div>
<div id="page-bank" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">💰 BANK</h2><div class="walletCard"><div>🏦 BANK PROFILE</div><div id="bankIDShow">Bank INF-</div><div>🪙 Bank Gold: <b id="bankGold">0</b> | 💎 <b id="bankGems">0</b></div><div>Wallet — 🪙 <span id="walletGold">0</span> | 💎 <span id="walletGems">0</span></div><button class="btn" type="button" style="background:#00cc44" onclick="claimInterest()">🎁 Claim 10% Interest (Monthly)</button></div><div style="display:flex;gap:12px;margin-top:14px"><div style="flex:1"><div class="bigBankBox" onclick="openSendPage()">💸<br><b>Send</b></div><div class="bigBankBox" style="margin-top:10px" onclick="openExchangePage()">🔄<br><b>Exchange</b></div><div class="bigBankBox" style="margin-top:10px" onclick="openWithdrawPage()">🏧<br><b>Withdraw</b></div></div><div style="flex:1"><div class="bigBankBox" onclick="openDepositPage()">💰<br><b>Deposit</b></div><div class="bigBankBox loanGreen" style="margin-top:10px" onclick="openLoan()">🏦<br><b>LOAN</b></div><div class="bigBankBox" style="margin-top:10px" onclick="openMyProfile()">👤<br><b>My Profile</b></div><div id="myLoansBox" style="margin-top:10px;font-size:12px"></div></div></div></div></div>
<div id="page-send" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">💸 SEND GOLD</h2><div class="walletCard">🪙 <b id="sendPageGold">0</b> | 💎 <b id="sendPageGems">0</b><br>Your ID: <b id="sendPageMyID">INF-</b></div><div class="idPrefix"><b>INF-</b><input id="sendDigits" placeholder="12345678" inputmode="numeric" maxlength="8"></div><input id="sendAmt" type="number" placeholder="Amount"><button class="btn" type="button" onclick="doSend()">➤ SEND NOW</button></div></div>
<div id="page-withdraw" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">🏧 WITHDRAW</h2><input id="withdrawAmt" type="number" placeholder="Amount"><select id="withdrawCur"><option>Gold</option><option>Gems</option></select><button class="btn" type="button" onclick="doWithdraw()">🏧 WITHDRAW</button></div></div>
<div id="page-deposit" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">💰 DEPOSIT</h2><input id="depositAmt" type="number" placeholder="Amount"><select id="depositCur"><option>Gold</option><option>Gems</option></select><button class="btn" type="button" onclick="doDeposit()">💰 DEPOSIT</button></div></div>
<div id="page-exchange" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">🔄 EXCHANGE</h2><div class="bigBankBox" onclick="openExchange('gold_to_gem')"><b>Gold >>>> Germ</b><br><small>100 Gold = 1 Germ</small></div><div class="bigBankBox" style="margin-top:10px" onclick="openExchange('gem_to_gold')"><b>Germ >>>> Gold</b></div><div id="exchangeForm"></div></div></div>
<div id="page-profile" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card" style="text-align:center"><div style="font-size:70px">👤</div><h2 id="profName">Player</h2><p id="profIDShow">ID:INF-</p><p id="profBankID">Bank INF-</p><p>⭐ Rank: <b id="profRank">#-</b></p><p>🏆 Wins: <b id="profWins">0</b> | ❌ <b id="profLoss">0</b></p><p>🪙 Gold: <b id="profGold">0</b> | 💎 Germ: <b id="profGems">0</b></p><p>🚗 Cars: <b id="profCars">None</b></p><p>🌌 Galaxy: <b id="profGalaxy">1</b> | Kills: <b id="profGalaxyKills">0</b></p><div id="profLoanBox" style="background:#00ff88;color:#000;padding:12px;border-radius:14px;display:none"></div><button class="btn2" type="button" onclick="openSecret()">🔒 Secret</button><p style="font-size:11px;color:#00ff88">🗄️ Saved in DB + 2 Backups</p></div><div class="card"><h3>👥 FRIENDS</h3><div id="profFriends">No friends yet</div><h3>📩 FRIEND REQUESTS</h3><div id="profFriendReqs">No requests</div></div><div class="card"><h3>🎒 INVENTORY</h3><div id="profInventory">No items</div><div id="consumeBox"></div></div></div>
<div id="page-other" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card" style="text-align:center"><h2 id="otherName">Player</h2><p>⭐ <b id="otherRank">#-</b></p><p><b id="otherWins">0</b> Win | <b id="otherLoss">0</b> Lose</p><div id="otherActions"></div></div></div>
<div id="page-notifs" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">✉️ NOTIFICATIONS</h2><div id="notifList">No notifications</div></div></div>
<div id="page-menu" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">🎮 MENU</h2><div id="menuGamesList"></div></div></div>
<div id="page-economy" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><div style="display:flex;justify-content:space-between"><h2>💰 SERVER ECONOMY</h2><button id="emergencyBtn" class="btn" type="button" style="width:auto;background:#666" disabled onclick="doEmergency()">🚨 Emergency (Locked)</button></div><p id="ecoStatus" style="font-size:12px;color:#ffd700"></p><div class="grid"><div class="walletCard">Server Gold<br><b id="ecoGold">0</b></div><div class="walletCard">Server Germ<br><b id="ecoGems">0</b></div><div class="bigBankBox">🏦 Bank Gold<br><b id="ecoBankGold">0</b></div><div class="bigBankBox">🏦 Bank Germ<br><b id="ecoBankGems">0</b></div><div class="bigBankBox">🎰 Lottery<br><b id="ecoLottery">0</b></div><div class="bigBankBox">🛟 Backup<br><b id="ecoBackup">0</b></div></div><h3>🗄️ DB BACKUPS</h3><div id="ecoBackups" style="font-size:12px"></div><h3>💰 SECRET REQUESTS</h3><div id="ecoRequests">No requests</div><h3>🏦 LOANS - PENDING ONLY</h3><div id="ecoLoans">No loans</div></div></div>
<div id="page-lottery" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">🎰 LOTTERY</h2><input id="lotBet" type="number" placeholder="1000"><select id="lotCur"><option>Gold</option><option>Gems</option></select><button class="btn" type="button" onclick="playLottery()">🎰 SPIN</button><div id="lotResult" style="text-align:center"></div></div></div>
<div id="page-update" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">🔄 UPDATE - DOMINIC ONLY</h2><button class="btn" type="button" onclick="doServerUpdate()">🚀 APPLY UPDATE</button><button class="btn" type="button" style="background:#ff2222;color:#fff" onclick="toggleGameSwitch()">🔌 SWITCH ON / OFF</button></div></div>
<div id="page-server-info" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">🖥️ SERVER INFO</h2><p>PLAYERS: <span id="serverPlayers">0</span></p><div id="serverBackups"></div><h3>📜 Reviews</h3><div id="serverReviewsList"></div></div></div>
<div id="page-review" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 id="reviewTitle">⭐ Review</h2><textarea id="reviewText" style="height:140px"></textarea><button class="btn" type="button" onclick="submitReview()">📩 SEND</button></div></div>
<div id="page-challenge" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">🎮 CHALLENGE</h2><div class="grid"><div class="box" onclick="hostPickMode('Bible Fight')"><span>📖</span><b>Bible</b></div><div class="box" onclick="hostPickMode('Riddles')"><span>🧩</span><b>Riddles</b></div><div class="box" onclick="hostPickMode('Galaxy Shooter')"><span>🌌</span><b>Galaxy</b></div><div class="box" onclick="hostPickMode('Decoding')"><span>💻</span><b>Decoding</b></div></div><button class="btn2" type="button" onclick="goDash()">❌ Decline</button></div></div>
<div id="page-messages" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h1 style="text-align:center">💚 WhatsApp</h1><div style="display:flex;gap:8px"><div class="idPrefix" style="flex:1"><b>INF-</b><input id="addFriendDigits" placeholder="Add friend ID" inputmode="numeric" maxlength="8"></div><button class="btn" type="button" style="width:auto" onclick="sendFriendRequest()">➕ Send Request</button></div><p style="font-size:11px">Sending = Friend Request. Other person must Accept in Profile.</p><div id="chatFriendList"></div></div></div>
<div id="page-chat" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">💬 <span id="chatWith">Friend</span></h2><div id="chatBox" style="background:#1a1a2e;border-radius:20px;padding:12px;min-height:260px;max-height:360px;overflow-y:auto"></div><div style="display:flex;gap:8px;margin-top:10px"><input id="msgInput" placeholder="Message..." style="flex:1"><button class="btn" type="button" style="width:70px" onclick="sendMsg()">➤</button></div></div></div>
<div id="page-scifi" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">🚀 SCI-FI - READY 25 DEC</h2><div id="scifiList"></div></div></div>
<div id="backFab" style="position:fixed;left:16px;bottom:88px;width:58px;height:58px;border-radius:50%;background:#1a1a2e;display:none;align-items:center;justify-content:center;font-size:28px;color:#ffd700;border:3px solid #ffd700;cursor:pointer;z-index:150">←</div>
<div id="msgFab" style="position:fixed;right:16px;bottom:88px;width:62px;height:62px;border-radius:50%;background:linear-gradient(135deg,#ff006e,#ffd700,#00e5ff);display:none;align-items:center;justify-content:center;font-size:30px;border:3px solid #fff;cursor:pointer;z-index:150">💬</div>
<div id="bottomNav" class="bottomNav hidden"><div onclick="goDash()">🏡<small>Home</small></div><div onclick="openFullLeader()">🏆<small>Leader</small></div><div onclick="openBank()">💰<small>Bank</small></div><div onclick="openNotifs()">✉️<small>Notify</small></div></div>
<audio id="pinSound" preload="auto" src="https://cdn.pixabay.com/audio/2025/07/09/audio_121db7b43f.mp3"></audio><audio id="dashAudio" loop preload="auto" style="display:none"></audio>
<script>
var CUTE_SOUND="https://cdn.pixabay.com/audio/2025/06/12/audio_0ea789b238.mp3";var soundOn=true,dashAudio=null;
function updateCatTime(){try{var now=new Date();var ft=new Intl.DateTimeFormat("en-GB",{timeZone:"Africa/Lusaka",hour:"2-digit",minute:"2-digit",second:"2-digit",hour12:false});var fd=new Intl.DateTimeFormat("en-GB",{timeZone:"Africa/Lusaka",weekday:"short",day:"2-digit",month:"short",year:"numeric"});document.getElementById("catTime").textContent=ft.format(now)+" CAT";document.getElementById("catDate").textContent=fd.format(now)+" - Central Africa"}catch(e){}}
updateCatTime();setInterval(updateCatTime,1000);
function playPin(){try{var a=document.getElementById("pinSound");if(a){a.currentTime=0;var p=a.play();if(p&&p.catch)p.catch(function(){})}}catch(e){}}
function startDashLoop(){try{if(!dashAudio)dashAudio=document.getElementById("dashAudio");if(!dashAudio)return;if(!dashAudio.src)dashAudio.src=CUTE_SOUND;dashAudio.loop=true;dashAudio.volume=0.6;if(soundOn){var p=dashAudio.play();if(p&&p.catch)p.catch(function(){})}}catch(e){}}
function stopDashLoop(){try{if(dashAudio)dashAudio.pause()}catch(e){}}
function toggleSound(){soundOn=!soundOn;document.getElementById("soundBtn").innerText=soundOn?"🔊":"🔇";if(soundOn){startDashLoop();playPin()}else stopDashLoop();toast(soundOn?"🔊 ON":"🔇 OFF")}
var user=null;try{user=JSON.parse(localStorage.getItem("inf_user")||localStorage.getItem("inf_backup")||"null")}catch(e){}
var wins=0,losses=0,myGold=0,myGems=0,myPlayerID="",myBankID="",myCars=[];try{var _b=JSON.parse(localStorage.getItem("inf_backup")||"{}");wins=parseInt(localStorage.getItem("inf_wins")||_b.wins||"0")||0;myGold=parseInt(localStorage.getItem("inf_gold")||_b.gold||"0")||0;myGems=parseInt(localStorage.getItem("inf_gems")||_b.gems||"0")||0;myPlayerID=localStorage.getItem("inf_player_id")||_b.player_id||"";myBankID=localStorage.getItem("inf_bank_id")||_b.bank_id||"";myCars=JSON.parse(localStorage.getItem("inf_cars")||JSON.stringify(_b.cars||[]))}catch(e){}
var loggedIn=false,currentPage="page-home",seenQs=[];try{seenQs=JSON.parse(localStorage.getItem("inf_seen")||"[]")}catch(e){}
var pinCb=null,leaderMode="pvp",chatWithName="",quizT=null,quizLeft=0,quizRound=[],quizIdx=0,quizScore=0,quizMode="",galaxyKills=0,galaxyLevel=1,fallInt=null,matchScore=0,reviewType="review",gameOn=true,shopCat="All",currentLoan=null,pendingLoanForDate=null,pendingDominicDate="";
function carExtraTime(){var t=0;myCars.forEach(function(c){if(/Lamborghini|Ferrari|Bugatti/.test(c))t+=15;else if(/Tesla|Mercedes|BMW/.test(c))t+=10;else if(/Audi|Range Rover/.test(c))t+=7;else t+=2});return Math.min(t,30)}
function isDom(){return user&&user.name&&user.name.toLowerCase()==="dominic"&&user.password==="2164"}
function toast(m){var t=document.getElementById("toast");if(!t)return;t.innerText=m;t.classList.remove("hidden");setTimeout(function(){t.classList.add("hidden")},4500)}
function showPage(id){currentPage=id;["page-home","page-register","page-dash","page-leader","page-game","page-coming","page-bank","page-send","page-withdraw","page-deposit","page-exchange","page-profile","page-other","page-notifs","page-menu","page-update","page-server-info","page-review","page-challenge","page-messages","page-chat","page-economy","page-lottery","page-scifi"].forEach(function(p){var e=document.getElementById(p);if(e){e.classList.add("hidden");e.style.display="none"}});var tg=document.getElementById(id);if(tg){tg.classList.remove("hidden");tg.style.display="block"}window.scrollTo(0,0);updateVisibility()}
function updateVisibility(){var r=document.getElementById("topRight"),nv=document.getElementById("bottomNav"),b=document.getElementById("backFab"),mf=document.getElementById("msgFab");var isEnter=(currentPage==="page-home"||currentPage==="page-register");if(isEnter){if(r)r.style.display="none";if(nv)nv.classList.add("hidden");if(b)b.style.display="none";if(mf)mf.style.display="none";stopDashLoop()}else if(loggedIn&&currentPage==="page-dash"){if(r){r.classList.remove("hidden");r.style.display="flex"}if(nv)nv.classList.remove("hidden");if(b)b.style.display="none";if(mf)mf.style.display="flex";startDashLoop()}else if(loggedIn){if(r)r.style.display="none";if(nv)nv.classList.add("hidden");if(b)b.style.display="flex";if(mf)mf.style.display="flex";stopDashLoop()}else{if(r)r.style.display="none";if(nv)nv.classList.add("hidden");if(b)b.style.display="none";if(mf)mf.style.display="none";stopDashLoop()}checkSwitch();checkLoanDue()}
function checkSwitch(){fetch("/api/switch_status").then(function(r){return r.json()}).then(function(d){gameOn=d.game_on!==false;var o=document.getElementById("frozenOverlay");if(!o)return;if(!gameOn){o.style.display="flex";document.getElementById("frozenDominicBox").style.display=isDom()?"block":"none"}else o.style.display="none"}).catch(function(){})}
function dominicUnfreeze(){var pin=document.getElementById("frozenPin").value.trim();if(pin!=="2164"){toast("Wrong PIN");return}fetch("/api/switch_toggle",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({admin:"dominic",pin:"2164",on:true})}).then(function(){gameOn=true;document.getElementById("frozenOverlay").style.display="none";toast("✅ GAME ON")})}
function toggleGameSwitch(){if(!isDom()){toast("🔒 Dominic only");return}var wantOff=gameOn;if(!confirm(wantOff?"Turn OFF? All FREEZE.":"Turn ON?"))return;openPin("PIN 2164 SWITCH "+(wantOff?"OFF":"ON"),function(pin){fetch("/api/switch_toggle",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({admin:"dominic",pin:pin,on:!wantOff})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}gameOn=d.game_on;toast(gameOn?"✅ ON":"❄️ OFF");checkSwitch()})})}
function goDash(){if(!loggedIn){showPage("page-register");return}showPage("page-dash");loadLeader()}
function goBack(){if(currentPage==="page-register")showPage("page-home");else if(currentPage==="page-chat")showPage("page-messages");else goDash()}
function enterClicked(){showPage("page-register");showRegister();setTimeout(function(){var o=document.getElementById("page-welcome");if(o){o.classList.remove("hidden");o.style.display="flex"}},100)}
function welcomeChoice(c){var o=document.getElementById("page-welcome");o.classList.add("hidden");o.style.display="none";if(c==="yes")showLogin();else showRegister()}
function showRegister(){document.getElementById("registerForm").classList.remove("hidden");document.getElementById("loginForm").classList.add("hidden")}
function showLogin(){document.getElementById("registerForm").classList.add("hidden");document.getElementById("loginForm").classList.remove("hidden")}
function saveLocal(){try{var backup={name:user?user.name:"",password:user?user.password:"",wins:wins,losses:losses,gold:myGold,gems:myGems,player_id:myPlayerID,bank_id:myBankID,cars:myCars,seen:seenQs};localStorage.setItem("inf_user",JSON.stringify(user));localStorage.setItem("inf_backup",JSON.stringify(backup));sessionStorage.setItem("inf_user",JSON.stringify(user));localStorage.setItem("inf_wins",wins);localStorage.setItem("inf_gold",myGold);localStorage.setItem("inf_gems",myGems);localStorage.setItem("inf_player_id",myPlayerID);localStorage.setItem("inf_bank_id",myBankID);localStorage.setItem("inf_seen",JSON.stringify(seenQs));localStorage.setItem("inf_cars",JSON.stringify(myCars))}catch(e){}}
function doLogout(){loggedIn=false;stopDashLoop();showPage("page-home");toast("👋 Logged out - Data SAFE in DB. Login to restore.")}
function special(n,pw){var x=(n||"").toLowerCase().trim();if(x==="britney"||x==="kayula")return"Welcome MY Fiance 💖";if(x==="blessing")return"Welcome Avatar ✨";if(x==="lubuto")return"Welcome Desk Bender 🛠️";if(x==="dominic"&&pw==="2164")return"Welcome Infinity Emperor ♾";return"Welcome, "+n+" 👑"}
function doRegister(){var n=document.getElementById("regName").value.trim();var pw=document.getElementById("regPass").value.trim();if(!n||!pw||pw.length!==4||isNaN(pw)){toast("Name + 4-digit PIN");return}if(pw==="1234"||pw==="0000"){toast("Too easy");return}fetch("/api/player?name="+encodeURIComponent(n)).then(function(r){return r.json()}).then(function(d){if(d&&d.found){showLogin();document.getElementById("loginName").value=n;toast("Already exists! Just Login");return}user={name:n,password:pw};wins=0;losses=0;myGold=0;myGems=0;seenQs=[];myCars=[];saveLocal();syncScore();enterDash(special(n,pw))})}
function doLogin(){var n=document.getElementById("loginName").value.trim();var pw=document.getElementById("loginPass").value.trim();if(!n||!pw){toast("Name + Password");return}fetch("/api/player?name="+encodeURIComponent(n)+"&password="+encodeURIComponent(pw)).then(function(r){return r.json()}).then(function(d){if(d&&d.found&&d.password_ok!==false){user={name:n,password:pw};wins=d.wins||0;losses=d.losses||0;myGold=d.gold||0;myGems=d.gems||0;myPlayerID=d.player_id||"";myBankID=d.bank_id||"";seenQs=d.seen_qs||[];myCars=d.cars||[];galaxyLevel=d.galaxy_level||1;galaxyKills=d.galaxy_kills||0;saveLocal();enterDash(special(n,pw)+" - Restored from DB ✅")}else if(d&&d.found===false){var b={};try{b=JSON.parse(localStorage.getItem("inf_backup")||"{}")}catch(e){}if(b.name&&b.name.toLowerCase()===n.toLowerCase()){toast("⚠️ DB missing - Restoring from phone backup...");fetch("/api/restore",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:n,password:pw,wins:b.wins||wins,gold:b.gold||myGold,gems:b.gems||myGems,cars:b.cars||myCars,player_id:b.player_id||myPlayerID,bank_id:b.bank_id||myBankID})}).then(function(r){return r.json()}).then(function(rd){if(rd.found){user={name:n,password:pw};wins=rd.player.wins||0;myGold=rd.player.gold||0;myGems=rd.player.gems||0;myPlayerID=rd.player.player_id||"";saveLocal();enterDash(special(n,pw)+" - RESTORED ✅")}else toast("Not found - Register")})}else toast("Wrong / Not found")}else toast("Wrong / Not found")})}
function enterDash(m){loggedIn=true;toast(m);playPin();startDashLoop();showPage("page-dash");document.getElementById("welcomeText").innerText=m;loadLeader();loadMe();checkAnn()}
function syncScore(){if(!user)return;fetch("/api/score",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,password:user.password,wins:wins,losses:losses,gold:myGold,gems:myGems,seen_qs:seenQs,cars:myCars,galaxy_level:galaxyLevel,galaxy_kills:galaxyKills})}).catch(function(){})}
function loadMe(){if(!user)return;fetch("/api/player?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){if(!d||!d.found)return;myGold=d.gold;myGems=d.gems;myCars=d.cars||myCars;wins=d.wins;saveLocal();var e=function(id,v){var x=document.getElementById(id);if(x)x.innerText=v};e("bankGold",d.bank_gold||0);e("bankGems",d.bank_gems||0);e("bankIDShow",d.bank_id||myBankID);e("walletGold",d.gold);e("walletGems",d.gems);e("myCarsCount",myCars.length);e("myExtraTime",carExtraTime());var lb=document.getElementById("dashLoanBox");if(d.active_loan){lb.innerHTML="<div style='background:#00ff88;color:#000;padding:10px;border-radius:14px;font-size:12px;font-weight:900'>🏦 ACTIVE LOAN: "+d.active_loan.amount+" "+d.active_loan.currency+" - Repay by "+d.active_loan.repay_date+"<br><button class='btn' type='button' style='background:#000;color:#fff;padding:8px' onclick=\"payLoanNow('"+d.active_loan.id+"')\">💰 Pay Loan Now</button></div>"}else lb.innerHTML="";checkLoanDueWith(d.active_loan)})}
function loadLeader(){fetch("/api/leaderboard?mode=pvp").then(function(r){return r.json()}).then(function(d){var h="";(d.players||[]).slice(0,5).forEach(function(p,i){h+="<div class='leadRow' onclick=\"viewOther('"+p.name+"')\"><span>"+(i+1)+". "+p.name+(p.active_loan?" 🏦":"")+"</span><span>🏆 "+p.wins+"W</span></div>"});document.getElementById("leaderList").innerHTML=h||"No players"})}
function setLeaderMode(m){leaderMode=m;["gold","gems","pvp"].forEach(function(x){var el=document.getElementById("tab"+x.charAt(0).toUpperCase()+x.slice(1));if(el)el.classList.remove("active")});var a=document.getElementById("tab"+m.charAt(0).toUpperCase()+m.slice(1));if(a)a.classList.add("active");openFullLeader()}
function openFullLeader(){showPage("page-leader");fetch("/api/leaderboard?mode="+leaderMode).then(function(r){return r.json()}).then(function(d){var h="";(d.players||[]).forEach(function(p,i){h+="<div class='leadRow' onclick=\"viewOther('"+p.name+"')\"><span>"+(i+1)+". "+p.name+"<br><small>"+p.player_id+(p.active_loan?" | 🏦 Has Loan":"")+"</small></span><span>"+(leaderMode==="gold"?"🪙 "+p.gold:leaderMode==="gems"?"💎 "+p.gems:"🏆 "+p.wins+"W")+"</span></div>"});document.getElementById("fullLeaderList").innerHTML=h||"No players"})}
function viewOther(name){fetch("/api/player?name="+encodeURIComponent(name)).then(function(r){return r.json()}).then(function(d){showPage("page-other");document.getElementById("otherName").innerText=d.name;document.getElementById("otherRank").innerText=d.rank;document.getElementById("otherWins").innerText=d.wins;document.getElementById("otherLoss").innerText=d.losses;document.getElementById("otherActions").innerHTML="<button class='btn' type='button' onclick=\"openBankSendTo('"+d.player_id+"')\">💸 Send Gold</button><button class='btn2' type='button' onclick=\"sendFriendTo('"+d.player_id+"')\">👥 Send Friend Request</button>"})}
function openMyProfile(){showPage("page-profile");fetch("/api/player?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){document.getElementById("profName").innerText=special(d.name,user.password);document.getElementById("profIDShow").innerText="ID:"+d.player_id;document.getElementById("profBankID").innerText=d.bank_id;document.getElementById("profRank").innerText="#-";document.getElementById("profWins").innerText=d.wins;document.getElementById("profLoss").innerText=d.losses;document.getElementById("profGold").innerText=d.gold;document.getElementById("profGems").innerText=d.gems;document.getElementById("profCars").innerText=(d.cars||[]).join(", ")||"None";document.getElementById("profGalaxy").innerText=d.galaxy_level||1;document.getElementById("profGalaxyKills").innerText=d.galaxy_kills||0;var lb=document.getElementById("profLoanBox");if(d.active_loan){lb.style.display="block";lb.innerHTML="🏦 ACTIVE LOAN - PENDING<br>"+d.active_loan.amount+" "+d.active_loan.currency+"<br>Repay by: "+d.active_loan.repay_date+"<br>Status: "+d.active_loan.status.toUpperCase()+"<br><button class='btn' type='button' onclick=\"payLoanNow('"+d.active_loan.id+"')\">💰 Pay Now</button>"}else lb.style.display="none";var fh="";(d.friends||[]).forEach(function(f){fh+="<div style='padding:10px;background:rgba(0,0,0,.4);border-radius:12px;margin:6px 0;display:flex;justify-content:space-between'><span>👥 "+f+"</span><button class='btn' type='button' style='width:auto;padding:6px 10px' onclick=\"openChatWith('"+f+"')\">💬 Chat</button></div>"});document.getElementById("profFriends").innerHTML=fh||"No friends yet";var rh="";(d.friend_requests||[]).forEach(function(rq){rh+="<div style='padding:10px;background:rgba(255,215,0,.2);border-radius:12px;margin:6px 0'>👥 "+rq.from+" wants to be friend<br><button class='btn' type='button' onclick=\"respondFriend('"+rq.id+"',true)\">✅ Accept</button><button class='btn2' type='button' onclick=\"respondFriend('"+rq.id+"',false)\">❌ Decline</button></div>"});document.getElementById("profFriendReqs").innerHTML=rh||"No pending requests";var inv=d.items||[];var h="";inv.forEach(function(it){h+="<div style='padding:10px;background:rgba(0,0,0,.4);border-radius:12px;margin:6px 0'>🎒 "+it+"</div>"});document.getElementById("profInventory").innerHTML=h||"No items";var cb=document.getElementById("consumeBox");var drink=inv.find(function(x){return /Cola|Juice|Drink/.test(x)});var food=inv.find(function(x){return /Burger|Pizza|Donut/.test(x)});var h2="";if(drink)h2+="<button class='btn' type='button' onclick=\"consumeP('"+drink+"')\">🥤 Drink "+drink+"</button>";if(food)h2+="<button class='btn2' type='button' onclick=\"consumeP('"+food+"')\">🍔 Eat "+food+"</button>";cb.innerHTML=h2})}
function respondFriend(id,ok){fetch("/api/friend_respond",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,request_id:id,accept:ok})}).then(function(){toast(ok?"✅ Friend Accepted":"❌ Declined");openMyProfile()})}
function sendFriendTo(pid){fetch("/api/friend_request",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,target_id:pid})}).then(function(r){return r.json()}).then(function(d){toast(d.error||"✅ Friend Request Sent")})}
function sendFriendRequest(){var dg=document.getElementById("addFriendDigits").value.replace(/[^0-9]/g,"");if(dg.length!==8){toast("8 digits");return}sendFriendTo("INF-"+dg)}
function consumeP(p){openPin("PIN consume "+p,function(pin){var b=[20,50,100][Math.floor(Math.random()*3)];fetch("/api/consume",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,product:p,bonus:b})}).then(function(r){return r.json()}).then(function(d){wins=d.wins;saveLocal();syncScore();toast("😋 +"+b+" Wins");openMyProfile()})})}
function openSecret(){var o=document.getElementById("secretOverlay");o.classList.remove("hidden");o.style.display="flex"}
function closeSecret(){var o=document.getElementById("secretOverlay");o.classList.add("hidden");o.style.display="none"}
function sendMoneyRequest(){var m=document.getElementById("reqMsg").value;var a=document.getElementById("reqAmt").value;var c=document.getElementById("reqCur").value;closeSecret();fetch("/api/request_money",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,amount:a||"",currency:c,message:m})}).then(function(){toast("🔒 Secret sent")})}
function openBank(){showPage("page-bank");loadMe()}
function claimInterest(){openPin("PIN Claim 10% Interest",function(pin){fetch("/api/bank_interest",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}toast("🎁 +10%: +"+d.bonus_gold+" Gold, +"+d.bonus_gems+" Germs");loadMe()})})}
function openLoan(){fetch("/api/player?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){if(d.active_loan){toast("❌ Already have ACTIVE loan - Pay first!");openMyProfile();return}var o=document.getElementById("loanOverlay");o.classList.remove("hidden");o.style.display="flex"})}
function closeLoan(){var o=document.getElementById("loanOverlay");o.classList.add("hidden");o.style.display="none"}
function submitLoan(){var a=document.getElementById("loanAmt").value;var c=document.getElementById("loanCur").value;var dt=document.getElementById("loanDate").value;if(!a||!dt){toast("Amount + date");return}closeLoan();openPin("PIN Loan "+a,function(pin){fetch("/api/loan_apply",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,amount:a,currency:c,repay_date:dt})}).then(function(r){return r.json()}).then(function(d){toast(d.error||"🏦 Loan sent to Dominic")})})}
function payLoanNow(id){openPin("PIN Pay Loan",function(pin){fetch("/api/loan_repay",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,loan_id:id})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);checkLoanDue();return}toast("✅ Loan PAID");loadMe();openMyProfile()})})}
function checkLoanDue(){fetch("/api/player?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){checkLoanDueWith(d.active_loan)})}
function checkLoanDueWith(loan){if(!loan)return;var today=new Date();today.setHours(0,0,0,0);var due=new Date(loan.repay_date);due.setHours(0,0,0,0);if(today>=due){currentLoan=loan;document.getElementById("loanDueText").innerText="Your loan of "+loan.amount+" "+loan.currency+" is DUE ("+loan.repay_date+"). Pay now or Extension. If no money, server deducts Wins: 1 Win = 1000 Gold / 10 Germs.";var o=document.getElementById("loanDueOverlay");o.classList.remove("hidden");o.style.display="flex"}}
function loanDueAction(act){var o=document.getElementById("loanDueOverlay");o.classList.add("hidden");o.style.display="none";if(!currentLoan)return;if(act==="collect"){payLoanNow(currentLoan.id);setTimeout(function(){fetch("/api/loan_due",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,loan_id:currentLoan.id,action:"collect"})}).then(function(r){return r.json()}).then(function(d){toast(d.error||("⚠️ Collected - Wins taken: "+d.wins_taken));loadMe()})},600)}else{fetch("/api/loan_due",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,loan_id:currentLoan.id,action:"extend"})}).then(function(r){return r.json()}).then(function(d){toast(d.error||("⏳ Extended to "+d.new_date));loadMe()})}}
function openBankSendTo(id){openSendPage();document.getElementById("sendDigits").value=id.replace("INF-","")}
function openSendPage(){showPage("page-send");fetch("/api/player?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){document.getElementById("sendPageGold").innerText=d.gold;document.getElementById("sendPageGems").innerText=d.gems;document.getElementById("sendPageMyID").innerText=d.player_id})}
function openWithdrawPage(){showPage("page-withdraw")}
function openDepositPage(){showPage("page-deposit")}
function openExchangePage(){showPage("page-exchange");document.getElementById("exchangeForm").innerHTML=""}
function openExchange(dir){document.getElementById("exchangeForm").innerHTML="<input id='exAmt' type='number' placeholder='Amount'><button class='btn' type='button' onclick=\"doExchange('"+dir+"')\">Confirm</button>"}
function doSend(){var dg=document.getElementById("sendDigits").value.replace(/[^0-9]/g,"");var amt=parseInt(document.getElementById("sendAmt").value||"0");if(dg.length<8||!amt){toast("ID + Amount");return}openPin("PIN send "+amt,function(pin){fetch("/api/transfer",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({sender:user.name,pin:pin,receiver_id:"INF-"+dg,amount:amt})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.sender_gold;saveLocal();toast("✅ Sent")})})}
function doWithdraw(){var amt=parseInt(document.getElementById("withdrawAmt").value||"0");var cur=document.getElementById("withdrawCur").value;openPin("PIN withdraw "+amt,function(pin){fetch("/api/bank_action",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,amount:amt,action:"withdraw",currency:cur})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.gold;myGems=d.gems;saveLocal();toast("✅ Withdrawn")})})}
function doDeposit(){var amt=parseInt(document.getElementById("depositAmt").value||"0");var cur=document.getElementById("depositCur").value;openPin("PIN deposit "+amt,function(pin){fetch("/api/bank_action",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,amount:amt,action:"deposit",currency:cur})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.gold;myGems=d.gems;saveLocal();toast("✅ Deposited")})})}
function doExchange(dir){var amt=parseInt(document.getElementById("exAmt").value||"0");openPin("PIN Exchange",function(pin){fetch("/api/exchange",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,amount:amt,direction:dir})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.gold;myGems=d.gems;saveLocal();toast("✅ Exchange done")})})}
function openNotifs(){showPage("page-notifs");fetch("/api/player?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){var h="";(d.notifs||[]).slice().reverse().forEach(function(n){var extra="";if(n.type==="loan_request"){extra="<br><button class='btn' type='button' onclick=\"domLoanFromNotif('"+n.loan_id+"',true)\">✅ Approve Loan</button><button class='btn2' type='button' onclick=\"domLoanFromNotif('"+n.loan_id+"',false)\">❌ Decline</button>"}if(n.type==="loan_date_change"){extra="<br><button class='btn' type='button' onclick=\"showLoanDatePopup('"+n.loan_id+"','"+n.new_date+"')\">📅 Open Date Popup - Approve / Refund</button>"}if(n.type==="request"){extra="<br><button class='btn' type='button' onclick=\"approveReq('"+n.request_id+"',"+n.amount+",'"+n.currency+"')\">✅ Approve Secret</button>"}if(n.type==="friend_request"){extra="<br><button class='btn' type='button' onclick=\"openMyProfile()\">👥 Go to Profile to Accept</button>"}h+="<div style='padding:12px;background:rgba(0,0,0,.4);border-radius:14px;margin:8px 0'>"+n.text+"<br><small>"+(n.time||"")+"</small>"+extra+"</div>"});document.getElementById("notifList").innerHTML=h||"No notifications"})}
// IN-GAME DATE POPUP - NOT browser prompt
function showLoanDatePopup(loanId,newDate){pendingLoanForDate=loanId;pendingDominicDate=newDate;document.getElementById("loanDatePopupText").innerText="Dominic changed your repay date to "+newDate+". Do you accept this new date? If YES, money comes from Server Economy immediately. If NO, loan is refunded.";document.getElementById("loanDateInput").value=newDate;var o=document.getElementById("loanDatePopup");o.classList.remove("hidden");o.style.display="flex"}
function loanDateRespond(ok){var o=document.getElementById("loanDatePopup");o.classList.add("hidden");o.style.display="none";if(!pendingLoanForDate)return;var id=pendingLoanForDate;pendingLoanForDate=null;playerLoanConfirm(id,ok)}
function openEconomy(){if(!isDom()){toast("🔒 Dominic only");return}showPage("page-economy");fetch("/api/economy?name=Dominic&password=2164").then(function(r){return r.json()}).then(function(d){var e=d.economy||{};var sg=e.gold||0;document.getElementById("ecoGold").innerText=sg.toLocaleString();document.getElementById("ecoGems").innerText=(e.gems||0).toLocaleString();document.getElementById("ecoBankGold").innerText=(e.bank_gold||0).toLocaleString();document.getElementById("ecoBankGems").innerText=(e.bank_gems||0).toLocaleString();document.getElementById("ecoLottery").innerText=e.lottery||0;document.getElementById("ecoBackup").innerText=e.backup||0;var eb=document.getElementById("emergencyBtn");var es=document.getElementById("ecoStatus");if(sg<0){eb.disabled=false;eb.style.background="#ff2222";eb.innerText="🚨 Emergency - CLICKABLE";es.innerText="⚠️ NEGATIVE - Emergency UNLOCKED"}else{eb.disabled=true;eb.style.background="#666";eb.innerText="🚨 Emergency (Locked - Not Negative)";es.innerText="✅ Server Healthy: "+sg.toLocaleString()+" Gold - Emergency locked until negative"}var bh="";(d.backups||[]).forEach(function(b){bh+="<div>🗄️ "+b.file+" - "+(b.exists?"✅ "+b.players+" players":"❌ Missing")+"</div>"});document.getElementById("ecoBackups").innerHTML=bh;var h="";(d.requests||[]).forEach(function(rq){h+="<div style='padding:12px;background:rgba(0,0,0,.4);border-radius:14px;margin:8px 0'>"+rq.from+" wants "+rq.amount+" "+rq.currency+" <button class='btn' type='button' onclick=\"approveReq('"+rq.id+"',"+rq.amount+",'"+rq.currency+"')\">✅ Approve</button></div>"});document.getElementById("ecoRequests").innerHTML=h||"No Requests";var h2="";(d.loans||[]).forEach(function(l){h2+="<div style='padding:12px;background:rgba(0,0,0,.4);border-radius:14px;margin:8px 0'>"+l.from+" Loan "+l.amount+" "+l.currency+" Repay "+l.repay_date+" <button class='btn' type='button' onclick=\"domLoan('"+l.id+"',true)\">✅ Approve</button><button class='btn2' type='button' onclick=\"domLoan('"+l.id+"',false)\">❌ Decline</button></div>"});document.getElementById("ecoLoans").innerHTML=h2||"No Loans"})}
function approveReq(id,amt,cur){openPin("PIN approve "+amt,function(pin){fetch("/api/request_approve",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({admin:"dominic",pin:pin,request_id:id,amount:amt,currency:cur})}).then(function(){toast("✅ Approved");openEconomy()})})}
// Dominic approve - IN-GAME popup for date, NOT prompt()
var domLoanPendingId=null;
function domLoan(id,ap){domLoanPendingId=id;if(!ap){openPin("PIN decline loan",function(pin){fetch("/api/loan_dominic",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({admin:"dominic",pin:pin,loan_id:id,approve:false})}).then(function(){toast("Declined - Disappeared from BOTH");openEconomy();openNotifs()})});return}showDomDatePopup(id)}
function domLoanFromNotif(id,ap){domLoan(id,ap)}
function showDomDatePopup(id){var o=document.getElementById("loanDatePopup");document.getElementById("loanDatePopupText").innerText="Dominic: Choose new repay date for this loan (leave as original if you want). This is IN-GAME popup.";document.getElementById("loanDateInput").value="";document.getElementById("loanDateInput").readOnly=false;pendingLoanForDate="DOMINIC:"+id;o.classList.remove("hidden");o.style.display="flex"}
function loanDateRespondDom(){}
function playerLoanConfirm(id,ap){fetch("/api/loan_player_confirm",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,loan_id:id,approve:ap})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}toast(ap?"✅ Loan Credited from Server Economy":"↩️ Refunded");loadMe();openNotifs()})}
function doEmergency(){openPin("PIN Emergency",function(pin){fetch("/api/emergency",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:"dominic",pin:pin})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}toast("🚨 Restored to 100M");openEconomy()})})}
function openLottery(){showPage("page-lottery")}
function playLottery(){var bet=parseInt(document.getElementById("lotBet").value||"0");var cur=document.getElementById("lotCur").value;openPin("PIN Lottery "+bet,function(pin){fetch("/api/lottery",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,bet:bet,currency:cur})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.gold;myGems=d.gems;saveLocal();document.getElementById("lotResult").innerHTML=d.result.win?"<h2 style='color:#00ff88'>🎉 WON "+d.result.prize+"</h2>":"<h2 style='color:#ff5555'>😢 Lost "+d.result.lost+"</h2>"})})}
function openAnnounce(){if(!isDom()){toast("🔒 Dominic only");return}var o=document.getElementById("announceOverlay");o.classList.remove("hidden");o.style.display="flex"}
function closeAnnounce(){var o=document.getElementById("announceOverlay");o.classList.add("hidden");o.style.display="none"}
function sendAnnounce(){var t=document.getElementById("annText").value.trim();if(!t){toast("Type announcement");return}closeAnnounce();openPin("PIN 2164 Announce",function(pin){fetch("/api/announce",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({admin:"dominic",pin:pin,text:t})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}toast("📢 Announced")})})}
function checkAnn(){fetch("/api/announcements").then(function(r){return r.json()}).then(function(d){var a=(d.announcements||[]).slice(-1)[0];if(a){var bar=document.getElementById("announceBar");bar.innerText="📢 "+a.text;bar.classList.remove("hidden");setTimeout(function(){bar.classList.add("hidden")},3000)}})}
function doServerUpdate(){toast("🚀 Update Applied - No Data Lost - DB Safe");playPin()}
function openServerInfo(){if(!isDom()){toast("🔒 Dominic only");return}showPage("page-server-info");fetch("/api/server_info?name=Dominic&password=2164").then(function(r){return r.json()}).then(function(d){document.getElementById("serverPlayers").innerText=d.players||0;var h="";(d.backups||[]).forEach(function(b){h+="<div>🗄️ "+b.file+" - "+(b.exists?"✅ "+b.players+" players":"❌ Missing")+"</div>"});document.getElementById("serverBackups").innerHTML=h;var h2="";(d.reviews||[]).forEach(function(rv){h2+="<div style='padding:10px;background:rgba(0,0,0,.4);border-radius:12px;margin:6px 0'>"+rv.name+": "+rv.text+"</div>"});document.getElementById("serverReviewsList").innerHTML=h2||"No reviews"})}
function openMenuPage(){showPage("page-menu");var g=[["🧩 Riddles","openRiddles()"],["📖 Bible Fight","openBible()"],["🚀 Sci-Fi","openSciFi()"],["💚 WhatsApp","openMessages()"],["💰 Bank","openBank()"],["🛍️ Shop","openShop()"],["🎰 Lottery","openLottery()"],["🏆 Leaderboard","openFullLeader()"],["🎮 Challenge","openChallengeDash()"],["📢 Announcement","openAnnounce()"]];var h="";g.forEach(function(x){h+="<button class='btn2' type='button' onclick=\""+x[1]+"\">"+x[0]+"</button>"});document.getElementById("menuGamesList").innerHTML=h}
function openChallengeDash(){showPage("page-challenge")}
function hostPickMode(m){toast("Host picked "+m);openRiddles()}
function openRiddles(){pickRiddleCat()}
function openBible(){pickBible()}
var QB=["vanity of vanities book?|Ecclesiastes - Solomon|Genesis - Moses|Psalms - David|OLD","Woman judge under palm tree?|Deborah - Palm tree|Esther - Palace|Ruth - Field|OLD","Methuselah lived how long?|969 years|930 years|950 years|OLD","3 men in fiery furnace?|Shadrach, Meshach, Abednego|Daniel, Shadrach, Meshach|Peter, James, John|OLD","High priest tore robes?|Caiaphas|Annas|Pilate|NEW","24 elders represent?|12 tribes + 12 apostles|24 prophets|24 angels|NEW","Father of Caleb?|Jephunneh|Jesse|Jacob|OLD","Moses father-in-law?|Jethro / Reuel|Aaron|Joshua|OLD","First Gentile church?|Antioch|Rome|Corinth|NEW","Ebenezer means?|Stone of Help - Samuel|Stone of God - Moses|Holy Stone - David|OLD"];
var QR=["Always hungry, finger red?|Fire|Water|Wind|FUNNY","Man photo - father's son?|His son|His brother|His father|SMART","Plane crashes border, bury survivors?|Nowhere - alive|USA|Canada|FUNNY","Rooster lays egg on roof?|Roosters don't lay eggs|Left side|Right side|FUNNY","Overtake 2nd place?|2nd place|1st place|3rd place|SMART","Cowboy Friday 3 days leaves Friday?|Horse named Friday|Time travel|Magic|FUNNY","Once in minute, twice moment?|Letter M|Letter O|Letter N|SMART","Hold in right not left?|Your left hand|Your right foot|Pen|SMART","Cities no houses, forests no trees?|A map|A book|A photo|SMART","Fragile saying name breaks?|Silence|Glass|Egg|SMART","Beginning eternity, end time?|Letter E|Letter A|Letter T|SMART","Grows when give away?|Love|Money|Gold|LOVE","Bat+ball $1.10 bat $1 more?|5 cents|10 cents|50 cents|SMART","Half of 2+2?|3|2|4|SMART","Months have 28 days?|All 12|February only|1|SMART"];
function parseQ(s){var p=s.split("|");var opts=[p[1],p[2],p[3]];for(var i=opts.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1));var t=opts[i];opts[i]=opts[j];opts[j]=t}return{q:p[0],correct:p[1],opts:opts,cat:p[4]}}
function pickRiddleCat(){showPage("page-game");document.getElementById("gameTitle").innerText="🧩 PICK RIDDLE TYPE";document.getElementById("gameBody").innerHTML="<button class='btn2' type='button' onclick=\"startQuiz('RIDDLE','LIVE')\">🎤 Live</button><button class='btn2' type='button' onclick=\"startQuiz('RIDDLE','SMART')\">🧠 Smart</button><button class='btn2' type='button' onclick=\"startQuiz('RIDDLE','FUNNY')\">😂 Funny</button><button class='btn2' type='button' onclick=\"startQuiz('RIDDLE','LOVE')\">💖 Love</button><button class='btn2' type='button' onclick='goDash()'>⬅ Back</button>"}
function pickBible(){showPage("page-game");document.getElementById("gameTitle").innerText="📖 PICK TESTAMENT";document.getElementById("gameBody").innerHTML="<button class='btn2' type='button' onclick=\"startQuiz('BIBLE','OLD')\">📜 Old</button><button class='btn2' type='button' onclick=\"startQuiz('BIBLE','NEW')\">✝️ New</button><button class='btn2' type='button' onclick='goDash()'>⬅ Back</button>"}
function startQuiz(mode,cat){quizMode=mode;var pool=(mode==="BIBLE"?QB:QR);var filtered=pool.filter(function(s){if(cat==="LIVE")return true;return s.split("|")[4]===cat});var avail=filtered.filter(function(s){return seenQs.indexOf(s)<0});if(avail.length<10){seenQs=[];avail=filtered}avail.sort(function(){return Math.random()-0.5});quizRound=avail.slice(0,10).map(parseQ);quizIdx=0;quizScore=0;showQuizQ()}
function showQuizQ(){if(quizIdx>=10){finishQuiz();return}var q=quizRound[quizIdx];showPage("page-game");document.getElementById("gameTitle").innerText=(quizMode==="BIBLE"?"📖 BIBLE":"🧩 RIDDLES")+" - Q "+(quizIdx+1)+"/10";var total=25+carExtraTime();quizLeft=total;document.getElementById("gameBody").innerHTML="<div style='font-size:28px;font-weight:900' id='timerTxt'>⏱️ "+quizLeft+"s</div><div class='timerBar'><div class='timerFill' id='timerFill' style='width:100%'></div></div><p>🏆 "+wins+" | 🪙 "+myGold+" | Score: "+quizScore+"/10</p><p style='font-size:18px;font-weight:700'>"+q.q+"</p><div id='hintBox'></div>"+q.opts.map(function(o,i){return "<button class='opt' type='button' onclick=\"answerQuiz("+i+")\">"+o+"</button>"}).join("")+"<button class='btn2' type='button' onclick='goDash()'>⬅ Quit</button>";if(quizT)clearInterval(quizT);quizT=setInterval(function(){quizLeft--;var t=document.getElementById("timerTxt");if(t)t.innerText="⏱️ "+quizLeft+"s";var f=document.getElementById("timerFill");if(f)f.style.width=(quizLeft/total*100)+"%";if(quizLeft===5&&myCars.length>0){var hb=document.getElementById("hintBox");if(hb)hb.innerHTML="<p style='color:#ffd700'>💡 HINT: Starts with '"+q.correct.charAt(0)+"'</p>"}if(quizLeft<=0){clearInterval(quizT);losses++;saveLocal();syncScore();toast("⏰ Time up! "+q.correct);quizIdx++;setTimeout(showQuizQ,900)}},1000)}
function answerQuiz(i){if(quizT)clearInterval(quizT);var q=quizRound[quizIdx];var ok=(q.opts[i]===q.correct);if(ok){quizScore++;wins++;myGold+=50;toast("✅ Correct +1 Win +50 Gold")}else{losses++;toast("❌ Wrong! "+q.correct)}seenQs.push(q.q+"|"+q.correct);saveLocal();syncScore();quizIdx++;setTimeout(showQuizQ,900)}
function finishQuiz(){showPage("page-game");document.getElementById("gameTitle").innerText="🏁 DONE";document.getElementById("gameBody").innerHTML="<h2>Score: "+quizScore+"/10</h2><p>Wins: "+wins+" | Gold: "+myGold+"</p><button class='btn' type='button' onclick=\"pickRiddleCat()\">🧩 Again</button><button class='btn2' type='button' onclick='goDash()'>⬅ Dashboard</button>"}
function openSciFi(){var now=new Date();var openDate=new Date(2026,11,25);if(now<openDate){showPage("page-coming");var diff=openDate-now;var days=Math.floor(diff/(1000*60*60*24));document.getElementById("countDown").innerText="⏳ "+days+" days left - Unlocks 25 Dec 2026";return}showPage("page-scifi");var games=[["🌌 Galaxy Shooter","openGalaxy()"],["🦖 Dino Jump","openDino()"],["🍬 Royal Match","openMatch()"]];var h="";games.forEach(function(g){h+="<button class='btn2' type='button' onclick=\""+g[1]+"\">"+g[0]+"</button>"});document.getElementById("scifiList").innerHTML=h}
function openGalaxy(){showPage("page-game");document.getElementById("gameTitle").innerText="🌌 GALAXY SHOOTER";document.getElementById("gameBody").innerHTML="<p>Level "+galaxyLevel+" Kills: "+galaxyKills+"</p><button class='btn' type='button' onclick='startGalaxy()'>🚀 START</button><button class='btn2' type='button' onclick='openSciFi()'>⬅ Sci-Fi</button>"}
function startGalaxy(){showPage("page-game");document.getElementById("gameTitle").innerText="🌌 GALAXY - Level "+galaxyLevel;document.getElementById("gameBody").innerHTML="<p>Kills: <b id='gKillTxt'>"+galaxyKills+"</b></p><div class='fallArea' id='fallArea'></div><button class='btn2' type='button' onclick='stopGalaxy();openSciFi()'>⬅ Stop</button>";var area=document.getElementById("fallArea");if(fallInt)clearInterval(fallInt);fallInt=setInterval(function(){var el=document.createElement("div");el.className="fallItem";el.innerText=["👾","🛸","☄️","👽"][Math.floor(Math.random()*4)];el.style.left=Math.random()*85+"%";el.style.top="0px";area.appendChild(el);var top=0;var iv=setInterval(function(){top+=8+galaxyLevel*3;el.style.top=top+"px";if(top>380){clearInterval(iv);if(el.parentNode)el.parentNode.removeChild(el)}},50);el.onclick=function(){galaxyKills++;var t=document.getElementById("gKillTxt");if(t)t.innerText=galaxyKills;if(el.parentNode)el.parentNode.removeChild(el);clearInterval(iv);var need=(galaxyLevel===1?100:galaxyLevel*500);if(galaxyKills>=need){stopGalaxy();galaxyLevel++;galaxyKills=0;wins+=50;myGold+=50;saveLocal();syncScore();toast("🌌 LEVEL UP!");openGalaxy()}}},1200)}
function stopGalaxy(){if(fallInt)clearInterval(fallInt)}
function openDino(){showPage("page-game");document.getElementById("gameTitle").innerText="🦖 DINO JUMP";document.getElementById("gameBody").innerHTML="<p>Jumps: <b id='dinoTxt'>0</b></p><div style='height:120px;background:#fff;border-radius:18px;position:relative'><div id='dinoEl' style='position:absolute;bottom:20px;left:40px;font-size:52px'>🦖</div></div><button class='btn' type='button' onclick='jumpDino()'>🦖 JUMP</button><button class='btn2' type='button' onclick='openSciFi()'>⬅ Sci-Fi</button>"}
function jumpDino(){var d=document.getElementById("dinoEl");if(!d)return;d.style.bottom="90px";setTimeout(function(){d.style.bottom="20px"},350);var t=document.getElementById("dinoTxt");t.innerText=parseInt(t.innerText)+1}
function openMatch(){showPage("page-game");document.getElementById("gameTitle").innerText="🍬 ROYAL MATCH";var emojis=["🍬","🍭","🍓","🍇","💎","⭐"];var board="";for(var i=0;i<9;i++){board+="<div style='display:inline-block;font-size:36px;padding:8px;cursor:pointer;background:rgba(255,255,255,.2);border-radius:12px;margin:4px' onclick=\"matchTap(this)\">"+emojis[Math.floor(Math.random()*emojis.length)]+"</div>"}document.getElementById("gameBody").innerHTML=board+"<button class='btn2' type='button' onclick='openSciFi()'>⬅ Sci-Fi</button>"}
function matchTap(el){matchScore++;el.style.opacity="0.3";if(matchScore%3===0){myGold+=30;wins+=1;saveLocal();syncScore();toast("🍬 Match +30 Gold +1 Win")}}
function openShop(){showPage("page-game");document.getElementById("gameTitle").innerText="🛍️ SHOP - CATALOG";var cats=["All","Cars","Food","Tech","Pets"];var h="<div style='display:flex;gap:6px;margin-bottom:10px'>"+cats.map(function(c){return "<div class='catTab "+(shopCat===c?"active":"")+"' onclick=\"setShopCat('"+c+"')\">"+c+"</div>"}).join("")+"</div><div class='shopGrid' id='shopGrid'></div><button class='btn2' type='button' onclick='goDash()'>⬅ Back</button>";document.getElementById("gameBody").innerHTML=h;renderShop()}
function setShopCat```javascript
function setShopCat(c){shopCat=c;openShop()}
function renderShop(){var items=[["Toyota Corolla 🚗",5000,"Cars"],["BMW M4 🚗",15000,"Cars"],["Lamborghini 🏎️",50000,"Cars"],["Ferrari 🏎️",60000,"Cars"],["Tesla 🚗",30000,"Cars"],["Mercedes 🚗",25000,"Cars"],["Audi 🚗",20000,"Cars"],["Range Rover 🚙",28000,"Cars"],["Hilux 🛻",18000,"Cars"],["Nissan GTR 🚗",22000,"Cars"],["Bugatti 🏎️",100000,"Cars"],["Burger 🍔",500,"Food"],["Pizza 🍕",800,"Food"],["Donut 🍩",300,"Food"],["Cola 🥤",200,"Food"],["Juice 🧃",250,"Food"],["Phone 📱",8000,"Tech"],["Laptop 💻",20000,"Tech"],["Headphones 🎧",5000,"Tech"],["Dog 🐶",10000,"Pets"],["Cat 🐱",8000,"Pets"]];var grid=document.getElementById("shopGrid");if(!grid)return;var html="";items.forEach(function(it){if(shopCat!=="All"&&it[2]!==shopCat)return;var owned=myCars.indexOf(it[0])>=0;html+="<div class='shopBox'><div style='font-size:32px'>"+it[0].split(" ").pop()+"</div><b>"+it[0]+"</b><div>🪙 "+it[1]+" Gold</div><div style='font-size:11px;color:#ffd700'>"+it[2]+" Catalog</div>"+(owned?"<div style='color:#00ff88;font-weight:900'>✅ OWNED</div>":"<button class='btn' type='button' onclick=\"buyShopItem('"+it[0]+"',"+it[1]+")\">Buy</button>")+"</div>"});grid.innerHTML=html||"No items"}
function buyShopItem(name,price){openPin("PIN Buy "+name+" "+price,function(pin){fetch("/api/buy_item",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,item:name,price:price})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.gold;saveLocal();syncScore();toast("✅ Bought "+name);openShop();loadMe()})})}
function openMessages(){showPage("page-messages");fetch("/api/friends?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){var h="";(d.friends||[]).forEach(function(f){h+="<div class='leadRow' onclick=\"openChatWith('"+f.name+"')\"><span>👥 "+f.name+"</span><span>💬 Chat</span></div>"});if(d.requests&&d.requests.length){h+="<h3>📩 Friend Requests</h3>";d.requests.forEach(function(rq){h+="<div style='padding:10px;background:rgba(255,215,0,.2);border-radius:12px;margin:6px 0'>👥 "+rq.from+"<br><button class='btn' type='button' onclick=\"respondFriend('"+rq.id+"',true)\">✅ Accept</button><button class='btn2' type='button' onclick=\"respondFriend('"+rq.id+"',false)\">❌ Decline</button></div>"})}document.getElementById("chatFriendList").innerHTML=h||"No friends yet - Send request by ID"})}
function openChatWith(name){chatWithName=name;showPage("page-chat");document.getElementById("chatWith").innerText=name;loadChat()}
function loadChat(){if(!chatWithName)return;fetch("/api/chat_get?a="+encodeURIComponent(user.name)+"&b="+encodeURIComponent(chatWithName)).then(function(r){return r.json()}).then(function(d){var h="";(d.messages||[]).forEach(function(m){h+="<div style='padding:8px;margin:6px 0;border-radius:12px;background:"+(m.from===user.name?"#00cc44;color:#000":"rgba(255,255,255,.2)")+"'><b>"+m.from+":</b> "+m.text+"</div>"});var box=document.getElementById("chatBox");if(box){box.innerHTML=h||"No messages yet";box.scrollTop=box.scrollHeight}})}
function sendMsg(){var t=document.getElementById("msgInput").value.trim();if(!t||!chatWithName)return;document.getElementById("msgInput").value="";fetch("/api/chat_send",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({sender:user.name,to:chatWithName,text:t})}).then(function(){loadChat()})}
function openPin(desc,cb){pinCb=cb;document.getElementById("pinDesc").innerText=desc;document.getElementById("pinInput").value="";var o=document.getElementById("pinOverlay");o.classList.remove("hidden");o.style.display="flex";playPin()}
function closePin(){var o=document.getElementById("pinOverlay");o.classList.add("hidden");o.style.display="none";pinCb=null}
function confirmPin(){var pin=document.getElementById("pinInput").value.trim();if(pin.length!==4){toast("4 digits");return}var cb=pinCb;closePin();if(cb)cb(pin)}
// Fix for Dominic date popup - handle both player and Dominic flows in one place
var _origLoanDateRespond = loanDateRespond;
function loanDateRespond(ok){
  var o=document.getElementById("loanDatePopup"); o.classList.add("hidden"); o.style.display="none";
  if(pendingLoanForDate && String(pendingLoanForDate).indexOf("DOMINIC:")===0){
    var loanId=String(pendingLoanForDate).replace("DOMINIC:","");
    pendingLoanForDate=null;
    if(!ok){ toast("Cancelled"); return; }
    var newDate=document.getElementById("loanDateInput").value || "";
    openPin("PIN approve loan",function(pin){fetch("/api/loan_dominic",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({admin:"dominic",pin:pin,loan_id:loanId,approve:true,new_date:newDate})}).then(function(){toast("Sent to player");openEconomy();openNotifs()})});
    return;
  }
  if(!pendingLoanForDate) return;
  var id=pendingLoanForDate; pendingLoanForDate=null;
  playerLoanConfirm(id,ok);
}
function setupMenu(){var mb=document.getElementById("menuBtn");if(mb){mb.onclick=function(e){e.stopPropagation();var drop=document.getElementById("menuDrop");if(drop.classList.contains("hidden")){var items="";if(isDom()){items+="<div onclick=\"openEconomy()\">💰 Economy (Dominic)</div><div onclick=\"openAnnounce()\">📢 Announcement</div><div onclick=\"openServerInfo()\">🖥️ Server Info</div><div onclick=\"showPage('page-update')\">🔄 Update</div><div onclick=\"toggleGameSwitch()\" style='color:#ff5555'>🔌 SWITCH ON/OFF</div>"}items+="<div onclick=\"openMenuPage()\">🎮 Menu</div><div onclick=\"openShop()\">🛍️ Shop</div><div onclick=\"openLottery()\">🎰 Lottery</div><div onclick=\"toggleSound()\">🔊 Sound ON/OFF</div><div onclick=\"openMyProfile()\">👤 My Profile</div><div onclick=\"doLogout()\" style='color:#ff5555'>👋 Logout</div>";drop.innerHTML=items;drop.classList.remove("hidden")}else drop.classList.add("hidden")}};var pb=document.getElementById("profileBtn");if(pb)pb.onclick=function(){openMyProfile()};var sb=document.getElementById("soundBtn");if(sb)sb.onclick=function(){toggleSound()};var eb=document.getElementById("enterBtn");if(eb)eb.onclick=function(){enterClicked()};var bf=document.getElementById("backFab");if(bf)bf.onclick=function(){goBack()};var mf=document.getElementById("msgFab");if(mf)mf.onclick=function(){openMessages()};document.addEventListener("click",function(e){var drop=document.getElementById("menuDrop");var btn=document.getElementById("menuBtn");if(drop&&btn&&!drop.contains(e.target)&&e.target!==btn){drop.classList.add("hidden")}})}
setupMenu();
if(user){fetch("/api/player?name="+encodeURIComponent(user.name)+"&password="+encodeURIComponent(user.password)).then(function(r){return r.json()}).then(function(d){if(d&&d.found&&d.password_ok!==false){wins=d.wins||0;myGold=d.gold||0;myGems=d.gems||0;myPlayerID=d.player_id||"";myBankID=d.bank_id||"";saveLocal()}}).catch(function(){})}
</script></body></html>"""
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
