import os, json, random, shutil, sqlite3, time
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, make_response
app = Flask(__name__)
DB_FILE="infinity.db"; DB_B1="infinity_backup1.db"; DB_B2="infinity_backup2.db"; ALL_DB=[DB_FILE,DB_B1,DB_B2]
DEFAULT_ECO={"gold":100000000,"gems":100000,"bank_gold":50000000,"bank_gems":50000000,"bank_total":100000000,"fees":0,"lottery":0,"backup":100000000,"history":[100000000,100000000]}
DATA={"players":{},"loans":[],"requests":[],"announcements":[],"reviews":[],"chats":{},"game_on":True,"friend_requests":[],"economy":dict(DEFAULT_ECO)}
def db_conn(p):
    c=sqlite3.connect(p); c.execute("CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT)"); return c
def db_read(p):
    try:
        if not os.path.exists(p): return None
        c=db_conn(p); r=c.execute("SELECT v FROM kv WHERE k='DATA'").fetchone(); c.close()
        if r: return json.loads(r[0])
    except Exception: pass
    return None
def db_write_all():
    try:
        c=db_conn(DB_FILE); c.execute("INSERT OR REPLACE INTO kv VALUES ('DATA',?)",(json.dumps(DATA),)); c.commit(); c.close()
        for b in [DB_B1,DB_B2]:
            try: shutil.copyfile(DB_FILE,b)
            except Exception: pass
    except Exception: pass
def load():
    global DATA
    found=[]
    for p in ALL_DB:
        d=db_read(p)
        if d: found.append(d)
    if not found:
        DATA["economy"]=dict(DEFAULT_ECO); db_write_all(); return
    found.sort(key=lambda x: len(x.get("players",{})),reverse=True); base=found[0]
    for k in DATA:
        if k in base: DATA[k]=base[k]
    merged={}
    for d in found:
        for n,p in d.get("players",{}).items():
            if n not in merged: merged[n]=p
            elif (p.get("wins",0)+p.get("gold",0))>(merged[n].get("wins",0)+merged[n].get("gold",0)): merged[n]=p
    DATA["players"]=merged
    e=DATA.get("economy",{})
    if e.get("gold",0)==0 and len(merged)==0: DATA["economy"]=dict(DEFAULT_ECO)
    else:
        if "bank_gold" not in e: e["bank_gold"]=50000000
        if "bank_gems" not in e: e["bank_gems"]=50000000
        if "gems" not in e: e["gems"]=100000
    db_write_all()
def save(): db_write_all()
def storage_status():
    o=[]
    for p in ALL_DB:
        d=db_read(p); o.append({"file":p,"exists":os.path.exists(p),"players":len(d.get("players",{})) if d else 0})
    return o
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
    al=active_loan_of(v); fr=[r for r in DATA.get("friend_requests",[]) if norm(r.get("to"))==norm(v["name"]) and r.get("status")=="pending"]
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
    if d.get("seen_qs") is not None and len(d.get("seen_qs",[]))>len(v.get("seen_qs",[])): v["seen_qs"]=d.get("seen_qs")
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
                if dom: dom["notifs"]=[n for n in dom.get("notifs",[]) if not (n.get("type")=="loan_request" and n.get("loan_id")==l["id"])]
                notify(l["from"],"Loan DECLINED by Dominic"); DATA["loans"]=[x for x in DATA["loans"] if x["id"]!=l["id"]]; save(); return jsonify({"ok":True})
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
                if l["currency"]=="Gold": DATA["economy"]["gold"]-=l["amount"]; v["gold"]=v.get("gold",0)+l["amount"]
                else: DATA["economy"]["gems"]-=l["amount"]; v["gems"]=v.get("gems",0)+l["amount"]
                v["notifs"]=[n for n in v.get("notifs",[]) if not (n.get("type")=="loan_date_change" and n.get("loan_id")==l["id"])]
                v["notifs"].append({"text":"✅ Loan APPROVED & RECEIVED: +"+str(l["amount"])+" "+l["currency"]+" - Repay by "+l["repay_date"],"type":"loan_active","time":datetime.now().strftime("%H:%M %d %b")})
                notify("dominic",v["name"]+" received Loan "+str(l["amount"])+" "+l["currency"]+" from Server Economy")
            else:
                v["notifs"]=[n for n in v.get("notifs",[]) if not (n.get("type")=="loan_date_change" and n.get("loan_id")==l["id"])]
                DATA["loans"]=[x for x in DATA["loans"] if x["id"]!=l["id"]]; notify("dominic",v["name"]+" declined Loan - Refunded")
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
        if v.get("gold",0)<amt: return jsonify({"error":"Not enough Gold."}),400
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
        notify(v["name"],"⏳ Extension: New date "+loan["repay_date"]); save(); return jsonify({"ok":True,"new_date":loan["repay_date"]})
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
    notify(v["name"],"⚠️ Server COLLECTED Loan: Deducted "+str(wins_taken)+" Wins"); save(); return jsonify({"ok":True,"wins_taken":wins_taken,"wins":v["wins"]})
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
    e=DATA["economy"]; e["history"]=(e.get("history",[])+[e.get("gold",100000000)])[-20:]; save()
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
@app.route("/api/storage_status")
def api_storage():
    if norm(request.args.get("name"))!="dominic" or str(request.args.get("password"))!="2164": return jsonify({"error":"Only Dominic"}),403
    return jsonify({"db":"SQLite infinity.db + 2 backups","backups":storage_status(),"ram_players":len(DATA["players"])})

HOME = r"""<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>INFINITY BOT v35 MERGED</title><link href="https://fonts.googleapis.com/css2?family=Great+Vibes&family=Poppins:wght@400;700;900&display=swap" rel="stylesheet"><style>*{box-sizing:border-box}body{margin:0;font-family:Poppins,Arial;color:#fff;background:radial-gradient(circle at 50% 20%,#3a0a5e,#12002b 70%);min-height:100vh}.cursive{font-family:'Great Vibes',cursive}.topbar{display:flex;justify-content:space-between;padding:8px 14px}.profile{width:40px;height:40px;border-radius:50%;background:linear-gradient(135deg,#ff006e,#ffd700);display:flex;align-items:center;justify-content:center;border:2px solid #fff;cursor:pointer}.center{min-height:82vh;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:20px}.crownBig{font-size:90px}.enterBtn{margin-top:18px;padding:16px 70px;font-family:'Great Vibes',cursive;font-size:48px;border:none;border-radius:60px;background:linear-gradient(90deg,#ff006e,#ffd700,#00e5ff);cursor:pointer;position:relative;z-index:5}.db-note{margin:10px 0 4px;font-size:11px;color:#00ff88}.card{background:rgba(255,255,255,.08);border:2px solid rgba(255,255,255,.35);border-radius:26px;padding:20px;margin:14px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.box{background:linear-gradient(160deg,rgba(255,255,255,.18),rgba(0,0,0,.4));border:2px solid #fff;border-radius:24px;padding:22px 10px;text-align:center;cursor:pointer}.box span{font-size:38px;display:block}button{cursor:pointer}.btn{width:100%;padding:14px;border:none;border-radius:25px;font-weight:900;background:#ffd700;margin:6px 0}.btn2{width:100%;padding:13px;border-radius:25px;border:2px solid #00e5ff;background:transparent;color:#00e5ff;font-weight:900;margin:6px 0}.opt{width:100%;padding:13px;margin:7px 0;border-radius:16px;border:2px solid #fff;background:rgba(0,0,0,.5);color:#fff;font-weight:700;cursor:pointer;text-align:left}input,select,textarea{width:100%;padding:14px;border-radius:14px;border:2px solid #ffd700;margin:8px 0;font-size:16px;background:#fff;color:#000}.hidden{display:none!important}.leadRow{display:flex;justify-content:space-between;align-items:center;padding:10px 12px;background:rgba(0,0,0,.45);border-radius:14px;margin:6px 0;cursor:pointer}.toast{position:fixed;top:70px;left:50%;transform:translateX(-50%);background:#fff;color:#000;padding:12px 18px;border-radius:20px;font-weight:700;z-index:999;max-width:90%;text-align:center}.gameOverlay{position:fixed;inset:0;background:rgba(0,0,0,.75);display:flex;align-items:center;justify-content:center;padding:16px;z-index:500}.gamePopup{background:linear-gradient(160deg,#2b005e,#12002b);border:3px solid #ffd700;border-radius:28px;padding:22px 18px;max-width:420px;width:100%;text-align:center}.choiceRow{display:flex;gap:12px;margin-top:16px}.choiceBox{flex:1;padding:18px 8px;border-radius:20px;cursor:pointer;font-weight:900;border:3px solid #fff}.choiceNo{background:#ff2222;color:#fff}.choiceYes{background:#00cc44;color:#000}.bottomNav{position:fixed;bottom:0;left:0;right:0;background:rgba(0,0,0,.85);border-top:2px solid #ffd700;display:flex;justify-content:space-around;padding:10px 0 14px;z-index:200}.bottomNav div{font-size:28px;cursor:pointer;text-align:center}.bottomNav small{display:block;font-size:10px;color:#ffd700}.walletCard{background:linear-gradient(135deg,#ffd700,#ff006e);color:#000;border-radius:24px;padding:18px;text-align:center}.bigBankBox{padding:22px 10px;border-radius:24px;border:2px solid #fff;text-align:center;cursor:pointer;background:linear-gradient(160deg,rgba(255,255,255,.18),rgba(0,0,0,.4))}.loanGreen{border:4px solid #00ff88!important;background:linear-gradient(160deg,#00cc44,#00ff88)!important;color:#000!important}.idPrefix{display:flex;align-items:center;background:#fff;border-radius:14px;border:2px solid #ffd700;padding:0 10px;margin:8px 0}.idPrefix b{color:#000}.idPrefix input{border:none;flex:1;margin:0}.timerBar{height:14px;background:#333;border-radius:99px;overflow:hidden}.timerFill{height:100%;background:linear-gradient(90deg,#00ff88,#ffd700,#ff2222)}.fallArea{position:relative;height:420px;background:linear-gradient(#000428,#004e92);border:2px solid #00e5ff;border-radius:18px;overflow:hidden}.fallItem{position:absolute;font-size:34px;cursor:pointer}.tabBox{flex:1;padding:12px 4px;border-radius:16px;background:rgba(255,255,255,.15);border:2px solid #ffd700;text-align:center;cursor:pointer;font-weight:900;font-size:13px}.tabBox.active{background:#ffd700;color:#000}.pinInput{font-size:28px;text-align:center;letter-spacing:12px}.shopGrid{display:grid;grid-template-columns:1fr 1fr;gap:10px}.shopBox{background:rgba(255,255,255,.12);border:2px solid rgba(255,255,255,.5);border-radius:18px;padding:12px;text-align:center}.catTab{padding:8px 4px;border-radius:12px;background:rgba(255,255,255,.12);border:1px solid #ffd700;text-align:center;cursor:pointer;font-size:11px;font-weight:900}.catTab.active{background:#ffd700;color:#000}#menuDrop{position:fixed!important;top:108px!important;right:8px!important;width:200px!important;background:#1a1a2e;border:2px solid #ffd700;border-radius:14px;padding:6px;z-index:900}#menuDrop div{padding:8px!important;font-size:12px!important}</style></head><body>
<div id="frozenOverlay" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.92);z-index:2000;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:20px"><div style="font-size:80px">❄️</div><h1>GAME PAUSED</h1><p style="color:#ffd700;font-weight:900">SWITCHED OFF BY DOMINIC</p><div id="frozenDominicBox" style="display:none;margin-top:20px;background:#1a1a2e;border:2px solid #ffd700;border-radius:20px;padding:16px;width:100%;max-width:320px"><p>👑 Dominic Only</p><input id="frozenPin" type="password" inputmode="numeric" maxlength="4" placeholder="2164"><button class="btn" type="button" onclick="dominicUnfreeze()">🔓 TURN GAME ON</button></div></div>
<div id="loanDatePopup" class="gameOverlay hidden" style="display:none;z-index:1200"><div class="gamePopup"><div style="font-size:50px">📅</div><h2>Dominic Changed Date</h2><p id="loanDatePopupText"></p><p style="font-size:12px">This popup is from INFINITY BOT GAME - not your browser.</p><label>New Repay Date:</label><input id="loanDateInput" type="date"><div class="choiceRow"><div class="choiceBox choiceNo" onclick="loanDateRespond(false)">❌ No - Refund</div><div class="choiceBox choiceYes" onclick="loanDateRespond(true)">✅ Yes - Receive Loan</div></div></div></div>
<div id="loanDueOverlay" class="gameOverlay hidden" style="display:none;z-index:1100"><div class="gamePopup"><div style="font-size:50px">⏰</div><h2>LOAN DUE!</h2><p id="loanDueText"></p><div class="choiceRow"><div class="choiceBox choiceNo" onclick="loanDueAction('extend')">⏳ Extension +7 Days</div><div class="choiceBox choiceYes" onclick="loanDueAction('collect')">💰 Pay / Collect Now</div></div></div></div>
<div id="announceBar" class="hidden" style="position:fixed;top:0;left:0;right:0;background:#ffd700;color:#000;padding:10px;text-align:center;font-weight:900;z-index:1000">📢</div>
<div class="topbar"><div><span id="catTime" style="font-size:12px;background:rgba(0,0,0,.55);border:1px solid #ffd700;padding:5px 9px;border-radius:20px">Loading time...</span><br><span id="catDate" style="font-size:10px;background:rgba(0,0,0,.45);padding:3px 8px;border-radius:20px">Central Africa</span><br><div style="font-weight:900">INFINITY BOT</div></div><div id="topRight" style="display:none;flex-direction:column;align-items:flex-end;gap:2px"><div style="display:flex;gap:6px"><div id="soundBtn" onclick="toggleSound()" style="width:30px;height:30px;border-radius:50%;background:rgba(0,0,0,.55);border:1px solid #ffd700;display:flex;align-items:center;justify-content:center;cursor:pointer">🔊</div><div onclick="openShop()" style="width:30px;height:30px;border-radius:50%;background:rgba(0,0,0,.55);border:1px solid #ffd700;display:flex;align-items:center;justify-content:center;cursor:pointer">🛍️</div><div class="profile" id="profileBtn" onclick="openMyProfile()">👤</div></div><div id="menuBtn" style="width:30px;height:30px;border-radius:50%;background:rgba(0,0,0,.55);border:1px solid #ffd700;display:flex;align-items:center;justify-content:center;cursor:pointer">⋮</div></div></div>
<div id="menuDrop" class="hidden"></div><div id="toast" class="toast hidden"></div>
<div id="pinOverlay" class="gameOverlay hidden" style="display:none;z-index:900"><div class="gamePopup"><h2>Enter PIN</h2><p id="pinDesc"></p><input id="pinInput" class="pinInput" placeholder="...." maxlength="4" inputmode="numeric" type="password"><div class="choiceRow"><div class="choiceBox choiceNo" onclick="closePin()">❌ Cancel</div><div class="choiceBox choiceYes" onclick="confirmPin()">✅ Confirm</div></div></div></div>
<div id="announceOverlay" class="gameOverlay hidden" style="display:none;z-index:960"><div class="gamePopup"><h2>📢 Announcement</h2><textarea id="annText" style="height:100px"></textarea><button class="btn" type="button" onclick="sendAnnounce()">📢 Announce</button><button class="btn2" type="button" onclick="closeAnnounce()">Cancel</button></div></div>
<div id="secretOverlay" class="gameOverlay hidden" style="display:none;z-index:920"><div class="gamePopup"><h2>🔒 Secret</h2><input id="reqMsg" type="password" placeholder="Secret message"><input id="reqAmt" type="password" inputmode="numeric" placeholder="Amount"><select id="reqCur"><option>Gold</option><option>Gems</option></select><div class="choiceRow"><div class="choiceBox choiceNo" onclick="closeSecret()">❌ Cancel</div><div class="choiceBox choiceYes" onclick="sendMoneyRequest()">📩 Send</div></div></div></div>
<div id="loanOverlay" class="gameOverlay hidden" style="display:none;z-index:920"><div class="gamePopup"><h2>🏦 Apply for Loan</h2><input id="loanAmt" type="number" placeholder="Amount"><select id="loanCur"><option>Gold</option><option>Gems</option></select><label>When to repay?</label><input id="loanDate" type="date"><div class="choiceRow"><div class="choiceBox choiceNo" onclick="closeLoan()">❌ Cancel</div><div class="choiceBox choiceYes" onclick="submitLoan()">📩 Apply</div></div></div></div>
<div id="page-welcome" class="gameOverlay hidden" style="display:none;z-index:950"><div class="gamePopup"><h2>Do you already have an account?</h2><div class="choiceRow"><div class="choiceBox choiceNo" onclick="welcomeChoice('no')">❌ No</div><div class="choiceBox choiceYes" onclick="welcomeChoice('yes')">✅ Yes</div></div></div></div>
<div id="page-home" class="center"><div style="font-size:26px">✨ 💖 ⭐ 🌟 💫</div><div class="crownBig">👑</div><h1 class="cursive" style="font-size:68px;margin:5px">Infinity Bot</h1><p style="letter-spacing:3px;font-weight:900">DOMINIC MASTIRIA</p><p class="db-note">DB Storage - Never Lose Account</p><button class="enterBtn" id="enterBtn" type="button" onclick="enterClicked()">Enter</button></div>
<div id="page-register" class="hidden" style="max-width:520px;margin:0 auto;padding:20px 14px"><div class="card" style="text-align:center"><h1 class="cursive" style="font-size:48px">Register</h1><div id="registerForm"><input id="regName" placeholder="Your Name" maxlength="20"><input id="regPass" placeholder="...." maxlength="4" inputmode="numeric" type="password"><button class="btn" type="button" onclick="doRegister()">📝 REGISTER</button><p>Already? <b style="color:#ffd700;cursor:pointer" onclick="showLogin()">Login</b></p></div><div id="loginForm" class="hidden"><input id="loginName" placeholder="Your Name"><input id="loginPass" placeholder="...." maxlength="4" inputmode="numeric" type="password"><button class="btn" type="button" onclick="doLogin()">🔓 LOGIN</button><p>New? <b style="color:#ffd700;cursor:pointer" onclick="showRegister()">Register</b></p></div></div></div>
<div id="page-dash" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div style="text-align:center"><h2 class="cursive" style="font-size:44px" id="welcomeText">Welcome 👑</h2><span style="padding:5px 10px;border-radius:20px;background:rgba(0,0,0,.5);border:1px solid #ffd700;font-size:12px">⭐ Rank: <b id="myRank">#-</b></span> <span style="padding:5px 10px;border-radius:20px;background:rgba(0,0,0,.5);border:1px solid #ffd700;font-size:12px">🚗 Cars: <b id="myCarsCount">0</b> = +<span id="myExtraTime">0</span>s</span><div id="dashLoanBox" style="margin-top:10px"></div></div><div class="grid"><div class="box" onclick="openRiddles()"><span>🧩</span><b>RIDDLES</b></div><div class="box" onclick="openBible()"><span>📖</span><b>BIBLE FIGHT</b></div><div class="box" onclick="openSciFi()"><span>🚀</span><b>SCI-FI</b></div><div class="box" onclick="openMessages()"><span>💚</span><b>WHATSAPP</b></div></div><div class="card"><h3 style="text-align:center;margin:0">🏆 TOP 5 🏆</h3><div id="leaderList">Loading...</div><button class="btn2" type="button" onclick="openFullLeader()">👀 Full Leaderboard</button></div></div>
<div id="page-leader" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h3 style="text-align:center">🏆 LEADERBOARD</h3><div style="display:flex;gap:8px"><div class="tabBox" id="tabGold" onclick="setLeaderMode('gold')">🪙 Gold</div><div class="tabBox" id="tabGems" onclick="setLeaderMode('gems')">💎 Germ</div><div class="tabBox active" id="tabPvp" onclick="setLeaderMode('pvp')">⚔️ PvP</div></div><div id="fullLeaderList" style="margin-top:10px">Loading...</div></div></div>
<div id="page-game" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 id="gameTitle" style="text-align:center">Game</h2><div id="gameBody"></div></div></div>
<div id="page-coming" class="hidden" style="max-width:520px;margin:0 auto;padding:40px 20px 110px;text-align:center"><div style="font-size:80px">🚀</div><h1 class="cursive" style="font-size:54px">Coming Soon</h1><h2>SCI-FI - 25 Dec 2026</h2><p id="countDown" style="font-size:28px;color:#ffd700;font-weight:900"></p></div>
<div id="page-bank" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">💰 BANK</h2><div class="walletCard"><div>🏦 BANK PROFILE</div><div id="bankIDShow">Bank INF-</div><div>🪙 Bank Gold: <b id="bankGold">0</b> | 💎 <b id="bankGems">0</b></div><div>Wallet — 🪙 <span id="walletGold">0</span> | 💎 <span id="walletGems">0</span></div><button class="btn" type="button" style="background:#00cc44" onclick="claimInterest()">🎁 Claim 10% Interest (Monthly)</button></div><div style="display:flex;gap:12px;margin-top:14px"><div style="flex:1"><div class="bigBankBox" onclick="openSendPage()">💸<br><b>Send</b></div><div class="bigBankBox" style="margin-top:10px" onclick="openExchangePage()">🔄<br><b>Exchange</b></div><div class="bigBankBox" style="margin-top:10px" onclick="openWithdrawPage()">🏧<br><b>Withdraw</b></div></div><div style="flex:1"><div class="bigBankBox" onclick="openDepositPage()">💰<br><b>Deposit</b></div><div class="bigBankBox loanGreen" style="margin-top:10px" onclick="openLoan()">🏦<br><b>LOAN</b></div><div class="bigBankBox" style="margin-top:10px" onclick="openMyProfile()">👤<br><b>My Profile</b></div></div></div></div></div>
<div id="page-send" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">💸 SEND GOLD</h2><div class="walletCard">🪙 <b id="sendPageGold">0</b> | 💎 <b id="sendPageGems">0</b><br>Your ID: <b id="sendPageMyID">INF-</b></div><div class="idPrefix"><b>INF-</b><input id="sendDigits" placeholder="12345678" inputmode="numeric" maxlength="8"></div><input id="sendAmt" type="number" placeholder="Amount"><button class="btn" type="button" onclick="doSend()">➤ SEND NOW</button></div></div>
<div id="page-withdraw" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">🏧 WITHDRAW</h2><input id="withdrawAmt" type="number" placeholder="Amount"><select id="withdrawCur"><option>Gold</option><option>Gems</option></select><button class="btn" type="button" onclick="doWithdraw()">🏧 WITHDRAW</button></div></div>
<div id="page-deposit" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">💰 DEPOSIT</h2><input id="depositAmt" type="number" placeholder="Amount"><select id="depositCur"><option>Gold</option><option>Gems</option></select><button class="btn" type="button" onclick="doDeposit()">💰 DEPOSIT</button></div></div>
<div id="page-exchange" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">🔄 EXCHANGE</h2><div class="bigBankBox" onclick="openExchange('gold_to_gem')"><b>Gold >>>> Germ</b><br><small>100 Gold = 1 Germ</small></div><div class="bigBankBox" style="margin-top:10px" onclick="openExchange('gem_to_gold')"><b>Germ >>>> Gold</b></div><div id="exchangeForm"></div></div></div>
<div id="page-profile" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card" style="text-align:center"><div style="font-size:70px">👤</div><h2 id="profName">Player</h2><p id="profIDShow">ID:INF-</p><p id="profBankID">Bank INF-</p><p>⭐ Rank: <b id="profRank">#-</b></p><p>🏆 Wins: <b id="profWins">0</b> | ❌ <b id="profLoss">0</b></p><p>🪙 Gold: <b id="profGold">0</b> | 💎 Germ: <b id="profGems">0</b></p><p>🚗 Cars: <b id="profCars">None</b></p><p>🌌 Galaxy: <b id="profGalaxy">1</b> | Kills: <b id="profGalaxyKills">0</b></p><div id="profLoanBox" style="background:#00ff88;color:#000;padding:12px;border-radius:14px;display:none"></div><button class="btn2" type="button" onclick="openSecret()">🔒 Secret</button></div><div class="card"><h3>👥 FRIENDS</h3><div id="profFriends">No friends yet</div><h3>📩 FRIEND REQUESTS</h3><div id="profFriendReqs">No requests</div></div><div class="card"><h3>🎒 INVENTORY</h3><div id="profInventory">No items</div><div id="consumeBox"></div></div></div>
<div id="page-other" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card" style="text-align:center"><h2 id="otherName">Player</h2><p>⭐ <b id="otherRank">#-</b></p><p><b id="otherWins">0</b> Win | <b id="otherLoss">0</b> Lose</p><div id="otherActions"></div></div></div>
<div id="page-notifs" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">✉️ NOTIFICATIONS</h2><div id="notifList">No notifications</div></div></div>
<div id="page-menu" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">🎮 MENU</h2><div id="menuGamesList"></div></div></div>
<div id="page-economy" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><div style="display:flex;justify-content:space-between"><h2>💰 SERVER ECONOMY</h2><button id="emergencyBtn" class="btn" type="button" style="width:auto;background:#666" disabled onclick="doEmergency()">🚨 Emergency (Locked)</button></div><p id="ecoStatus" style="font-size:12px;color:#ffd700"></p><div class="grid"><div class="walletCard">Server Gold<br><b id="ecoGold">0</b></div><div class="walletCard">Server Germ<br><b id="ecoGems">0</b></div><div class="bigBankBox">🏦 Bank Gold<br><b id="ecoBankGold">0</b></div><div class="bigBankBox">🏦 Bank Germ<br><b id="ecoBankGems">0</b></div><div class="bigBankBox">🎰 Lottery<br><b id="ecoLottery">0</b></div><div class="bigBankBox">🛟 Backup<br><b id="ecoBackup">0</b></div></div><h3>🗄️ DB BACKUPS</h3><div id="ecoBackups" style="font-size:12px"></div><h3>💰 SECRET REQUESTS</h3><div id="ecoRequests">No requests</div><h3>🏦 LOANS - PENDING ONLY</h3><div id="ecoLoans">No loans</div></div></div>
<div id="page-lottery" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">🎰 LOTTERY</h2><input id="lotBet" type="number" placeholder="1000"><select id="lotCur"><option>Gold</option><option>Gems</option></select><button class="btn" type="button" onclick="playLottery()">🎰 SPIN</button><div id="lotResult" style="text-align:center"></div></div></div>
<div id="page-update" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">🔄 UPDATE - DOMINIC ONLY</h2><button class="btn" type="button" onclick="doServerUpdate()">🚀 APPLY UPDATE</button><button class="btn" type="button" style="background:#ff2222;color:#fff" onclick="toggleGameSwitch()">🔌 SWITCH ON / OFF</button></div></div>
<div id="page-server-info" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">🖥️ SERVER INFO</h2><p>PLAYERS: <span id="serverPlayers">0</span></p><div id="serverBackups"></div><h3>📜 Reviews</h3><div id="serverReviewsList"></div></div></div>
<div id="page-review" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 id="reviewTitle">⭐ Review</h2><textarea id="reviewText" style="height:140px"></textarea><button class="btn" type="button" onclick="submitReview()">📩 SEND</button></div></div>
<div id="page-challenge" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">🎮 CHALLENGE</h2><div class="grid"><div class="box" onclick="hostPickMode('Bible Fight')"><span>📖</span><b>Bible</b></div><div class="box" onclick="hostPickMode('Riddles')"><span>🧩</span><b>Riddles</b></div><div class="box" onclick="hostPickMode('Galaxy Shooter')"><span>🌌</span><b>Galaxy</b></div><div class="box" onclick="hostPickMode('Decoding')"><span>💻</span><b>Decoding</b></div></div><button class="btn2" type="button" onclick="goDash()">❌ Decline</button></div></div>
<div id="page-messages" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h1 style="text-align:center">💚 WhatsApp</h1><div style="display:flex;gap:8px"><div class="idPrefix" style="flex:1"><b>INF-</b><input id="addFriendDigits" placeholder="Add friend ID" inputmode="numeric" maxlength="8"></div><button class="btn" type="button" style="width:auto" onclick="sendFriendRequest()">➕ Send Request</button></div><div id="chatFriendList"></div></div></div>
<div id="page-chat" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">💬 <span id="chatWith">Friend</span></h2><div id="chatBox" style="background:#1a1a2e;border-radius:20px;padding:12px;min-height:260px;max-height:360px;overflow-y:auto"></div><div style="display:flex;gap:8px;margin-top:10px"><input id="msgInput" placeholder="Message..." style="flex:1"><button class="btn" type="button" style="width:70px" onclick="sendMsg()">➤</button></div></div></div>
<div id="page-scifi" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">🚀 SCI-FI - READY 25 DEC</h2><div id="scifiList"></div></div></div>
<div id="page-shop" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">🛍️ SHOP</h2><div style="display:flex;gap:6px"><div class="catTab" onclick="setShopCat('All')">All</div><div class="catTab" onclick="setShopCat('Cars')">Cars</div><div class="catTab" onclick="setShopCat('Food')">Food</div><div class="catTab" onclick="setShopCat('Tech')">Tech</div><div class="catTab" onclick="setShopCat('Pets')">Pets</div></div><div id="shopGrid" class="shopGrid" style="margin-top:12px"></div></div></div>
<div id="backFab" onclick="goBack()" style="position:fixed;left:16px;bottom:88px;width:58px;height:58px;border-radius:50%;background:#1a1a2e;display:none;align-items:center;justify-content:center;font-size:28px;color:#ffd700;border:3px solid #ffd700;cursor:pointer;z-index:150">←</div>
<div id="msgFab" onclick="openMessages()" style="position:fixed;right:16px;bottom:88px;width:62px;height:62px;border-radius:50%;background:linear-gradient(135deg,#ff006e,#ffd700,#00e5ff);display:none;align-items:center;justify-content:center;font-size:30px;border:3px solid #fff;cursor:pointer;z-index:150">💬</div>
<div id="bottomNav" class="bottomNav hidden"><div onclick="goDash()">🏡<small>Home</small></div><div onclick="openFullLeader()">🏆<small>Leader</small></div><div onclick="openBank()">💰<small>Bank</small></div><div onclick="openNotifs()">✉️<small>Notify</small></div></div>
<audio id="pinSound" preload="auto" src="https://cdn.pixabay.com/audio/2025/07/09/audio_121db7b43f.mp3"></audio><audio id="dashAudio" loop preload="auto" style="display:none"></audio>
<script>
var CUTE_SOUND="https://cdn.pixabay.com/audio/2025/06/12/audio_0ea789b238.mp3";var soundOn=true,dashAudio=null;
function updateCatTime(){try{var now=new Date();var ft=new Intl.DateTimeFormat("en-GB",{timeZone:"Africa/Lusaka",hour:"2-digit",minute:"2-digit",second:"2-digit",hour12:false});var fd=new Intl.DateTimeFormat("en-GB",{timeZone:"Africa/Lusaka",weekday:"short",day:"2-digit",month:"short",year:"numeric"});var t=document.getElementById("catTime");if(t)t.textContent=ft.format(now)+" CAT";var d=document.getElementById("catDate");if(d)d.textContent=fd.format(now)+" - Central Africa"}catch(e){var t2=document.getElementById("catTime");if(t2){var n=new Date();var h=n.getUTCHours()+2;if(h>=24)h-=24;t2.textContent=(h<10?"0":"")+h+":"+(n.getUTCMinutes()<10?"0":"")+n.getUTCMinutes()+":"+(n.getUTCSeconds()<10?"0":"")+n.getUTCSeconds()+" CAT"}}}
updateCatTime();setInterval(updateCatTime,1000);
function playPin(){try{var a=document.getElementById("pinSound");if(a){a.currentTime=0;var p=a.play();if(p&&p.catch)p.catch(function(){})}}catch(e){}}
function startDashLoop(){try{if(!dashAudio)dashAudio=document.getElementById("dashAudio");if(!dashAudio)return;if(!dashAudio.src)dashAudio.src=CUTE_SOUND;dashAudio.loop=true;dashAudio.volume=0.6;if(soundOn){var p=dashAudio.play();if(p&&p.catch)p.catch(function(){})}}catch(e){}}
function stopDashLoop(){try{if(dashAudio)dashAudio.pause()}catch(e){}}
function toggleSound(){soundOn=!soundOn;var b=document.getElementById("soundBtn");if(b)b.innerText=soundOn?"🔊":"🔇";if(soundOn){startDashLoop();playPin()}else stopDashLoop();toast(soundOn?"🔊 ON":"🔇 OFF")}
var user=null;try{user=JSON.parse(localStorage.getItem("inf_user")||localStorage.getItem("inf_backup")||"null")}catch(e){}
var wins=0,losses=0,myGold=0,myGems=0,myPlayerID="",myBankID="",myCars=[];try{var b2=JSON.parse(localStorage.getItem("inf_backup")||"{}");wins=parseInt(localStorage.getItem("inf_wins")||b2.wins||"0")||0;myGold=parseInt(localStorage.getItem("inf_gold")||b2.gold||"0")||0;myGems=parseInt(localStorage.getItem("inf_gems")||b2.gems||"0")||0;myPlayerID=localStorage.getItem("inf_player_id")||b2.player_id||"";myBankID=localStorage.getItem("inf_bank_id")||b2.bank_id||"";myCars=JSON.parse(localStorage.getItem("inf_cars")||JSON.stringify(b2.cars||[]))}catch(e){}
var loggedIn=false,currentPage="page-home",seenQs=[];try{seenQs=JSON.parse(localStorage.getItem("inf_seen")||"[]")}catch(e){}
var pinCb=null,leaderMode="pvp",chatWithName="",quizT=null,quizLeft=0,quizRound=[],quizIdx=0,quizScore=0,quizMode="",galaxyKills=0,galaxyLevel=1,fallInt=null,matchScore=0,gameOn=true,shopCat="All",currentLoan=null,pendingLoanForDate=null,reviewType="review";
function carExtraTime(){var t=0;myCars.forEach(function(c){if(/Lamborghini|Ferrari|Bugatti/.test(c))t+=15;else if(/Tesla|Mercedes|BMW/.test(c))t+=10;else if(/Audi|Range Rover/.test(c))t+=7;else t+=2});return Math.min(t,30)}
function isDom(){return user&&user.name&&user.name.toLowerCase()==="dominic"&&user.password==="2164"}
function toast(m){var t=document.getElementById("toast");if(!t)return;t.innerText=m;t.classList.remove("hidden");setTimeout(function(){t.classList.add("hidden")},4500)}
function showPage(id){currentPage=id;["page-home","page-register","page-dash","page-leader","page-game","page-coming","page-bank","page-send","page-withdraw","page-deposit","page-exchange","page-profile","page-other","page-notifs","page-menu","page-update","page-server-info","page-review","page-challenge","page-messages","page-chat","page-economy","page-lottery","page-scifi","page-shop"].forEach(function(p){var e=document.getElementById(p);if(e){e.classList.add("hidden");e.style.display="none"}});var tg=document.getElementById(id);if(tg){tg.classList.remove("hidden");tg.style.display="block"}window.scrollTo(0,0);updateVisibility()}
function updateVisibility(){var r=document.getElementById("topRight"),nv=document.getElementById("bottomNav"),b=document.getElementById("backFab"),mf=document.getElementById("msgFab");var isEnter=(currentPage==="page-home"||currentPage==="page-register");if(isEnter){if(r)r.style.display="none";if(nv)nv.classList.add("hidden");if(b)b.style.display="none";if(mf)mf.style.display="none";stopDashLoop()}else if(loggedIn&&currentPage==="page-dash"){if(r){r.classList.remove("hidden");r.style.display="flex"}if(nv)nv.classList.remove("hidden");if(b)b.style.display="none";if(mf)mf.style.display="flex";startDashLoop()}else if(loggedIn){if(r)r.style.display="none";if(nv)nv.classList.add("hidden");if(b)b.style.display="flex";if(mf)mf.style.display="flex";stopDashLoop()}else{if(r)r.style.display="none";if(nv)nv.classList.add("hidden");if(b)b.style.display="none";if(mf)mf.style.display="none";stopDashLoop()}checkSwitch();checkLoanDue()}
function checkSwitch(){fetch("/api/switch_status").then(function(r){return r.json()}).then(function(d){gameOn=d.game_on!==false;var o=document.getElementById("frozenOverlay");if(!o)return;if(!gameOn){o.style.display="flex";document.getElementById("frozenDominicBox").style.display=isDom()?"block":"none"}else o.style.display="none"}).catch(function(){})}
function dominicUnfreeze(){var pin=document.getElementById("frozenPin").value.trim();if(pin!=="2164"){toast("Wrong PIN");return}fetch("/api/switch_toggle",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({admin:"dominic",pin:"2164",on:true})}).then(function(){gameOn=true;document.getElementById("frozenOverlay").style.display="none";toast("✅ GAME ON")})}
function toggleGameSwitch(){if(!isDom()){toast("🔒 Dominic only");return}var wantOff=gameOn;if(!confirm(wantOff?"Turn OFF?":"Turn ON?"))return;openPin("PIN 2164 SWITCH "+(wantOff?"OFF":"ON"),function(pin){fetch("/api/switch_toggle",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({admin:"dominic",pin:pin,on:!wantOff})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}gameOn=d.game_on;toast(gameOn?"✅ ON":"❄️ OFF");checkSwitch()})})}
function goDash(){if(!loggedIn){showPage("page-register");return}showPage("page-dash");loadLeader()}
function goBack(){if(currentPage==="page-register")showPage("page-home");else if(currentPage==="page-chat")showPage("page-messages");else goDash()}
function enterClicked(){showPage("page-register");showRegister();setTimeout(function(){var o=document.getElementById("page-welcome");if(o){o.classList.remove("hidden");o.style.display="flex"}},100)}
function welcomeChoice(c){var o=document.getElementById("page-welcome");o.classList.add("hidden");o.style.display="none";if(c==="yes")showLogin();else showRegister()}
function showRegister(){document.getElementById("registerForm").classList.remove("hidden");document.getElementById("loginForm").classList.add("hidden")}
function showLogin(){document.getElementById("registerForm").classList.add("hidden");document.getElementById("loginForm").classList.remove("hidden")}
function saveLocal(){try{var backup={name:user?user.name:"",password:user?user.password:"",wins:wins,losses:losses,gold:myGold,gems:myGems,player_id:myPlayerID,bank_id:myBankID,cars:myCars,seen:seenQs};localStorage.setItem("inf_user",JSON.stringify(user));localStorage.setItem("inf_backup",JSON.stringify(backup));sessionStorage.setItem("inf_user",JSON.stringify(user));localStorage.setItem("inf_wins",wins);localStorage.setItem("inf_gold",myGold);localStorage.setItem("inf_gems",myGems);localStorage.setItem("inf_player_id",myPlayerID);localStorage.setItem("inf_bank_id",myBankID);localStorage.setItem("inf_seen",JSON.stringify(seenQs));localStorage.setItem("inf_cars",JSON.stringify(myCars))}catch(e){}}
function doLogout(){loggedIn=false;stopDashLoop();showPage("page-home");toast("👋 Logged out - Data SAFE in DB.")}
function special(n,pw){var x=(n||"").toLowerCase().trim();if(x==="britney"||x==="kayula")return"Welcome MY Fiance 💖";if(x==="blessing")return"Welcome Avatar ✨";if(x==="lubuto")return"Welcome Desk Bender 🛠️";if(x==="dominic"&&pw==="2164")return"Welcome Infinity Emperor ♾";return"Welcome, "+n+" 👑"}
function doRegister(){var n=document.getElementById("regName").value.trim();var pw=document.getElementById("regPass").value.trim();if(!n||!pw||pw.length!==4||isNaN(pw)){toast("Name + 4-digit PIN");return}if(pw==="1234"||pw==="0000"){toast("Too easy");return}fetch("/api/player?name="+encodeURIComponent(n)).then(function(r){return r.json()}).then(function(d){if(d&&d.found){showLogin();document.getElementById("loginName").value=n;toast("Already exists! Just Login");return}user={name:n,password:pw};wins=0;losses=0;myGold=0;myGems=0;seenQs=[];myCars=[];saveLocal();syncScore();enterDash(special(n,pw))})}
function doLogin(){var n=document.getElementById("loginName").value.trim();var pw=document.getElementById("loginPass").value.trim();if(!n||!pw){toast("Name + Password");return}fetch("/api/player?name="+encodeURIComponent(n)+"&password="+encodeURIComponent(pw)).then(function(r){return r.json()}).then(function(d){if(d&&d.found&&d.password_ok!==false){user={name:n,password:pw};wins=d.wins||0;losses=d.losses||0;myGold=d.gold||0;myGems=d.gems||0;myPlayerID=d.player_id||"";myBankID=d.bank_id||"";seenQs=d.seen_qs||[];myCars=d.cars||[];saveLocal();enterDash(special(n,pw)+" - Restored from DB ✅")}else if(d&&d.found===false){var b={};try{b=JSON.parse(localStorage.getItem("inf_backup")||"{}")}catch(e){}if(b.name&&b.name.toLowerCase()===n.toLowerCase()){toast("⚠️ Restoring from phone backup...");fetch("/api/restore",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:n,password:pw,wins:b.wins||wins,gold:b.gold||myGold,gems:b.gems||myGems,cars:b.cars||myCars,player_id:b.player_id||myPlayerID,bank_id:b.bank_id||myBankID})}).then(function(r){return r.json()}).then(function(rd){if(rd.found){user={name:n,password:pw};wins=rd.player.wins||0;myGold=rd.player.gold||0;myGems=rd.player.gems||0;myPlayerID=rd.player.player_id||"";saveLocal();enterDash(special(n,pw)+" - RESTORED ✅")}else toast("Not found - Register")})}else toast("Wrong / Not found")}else toast("Wrong / Not found")})}
function enterDash(m){loggedIn=true;toast(m);playPin();startDashLoop();showPage("page-dash");document.getElementById("welcomeText").innerText=m;loadLeader();loadMe();checkAnn()}
function syncScore(){if(!user)return;fetch("/api/score",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,password:user.password,wins:wins,losses:losses,gold:myGold,gems:myGems,seen_qs:seenQs,cars:myCars})}).catch(function(){})}
function loadMe(){if(!user)return;fetch("/api/player?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){if(!d||!d.found)return;myGold=d.gold;myGems=d.gems;myCars=d.cars||myCars;wins=d.wins;saveLocal();var e=function(id,v){var x=document.getElementById(id);if(x)x.innerText=v};e("bankGold",d.bank_gold||0);e("bankGems",d.bank_gems||0);e("bankIDShow",d.bank_id||myBankID);e("walletGold",d.gold);e("walletGems",d.gems);e("myCarsCount",myCars.length);e("myExtraTime",carExtraTime());var lb=document.getElementById("dashLoanBox");if(d.active_loan){lb.innerHTML="<div style='background:#00ff88;color:#000;padding:10px;border-radius:14px;font-size:12px;font-weight:900'>🏦 ACTIVE LOAN: "+d.active_loan.amount+" "+d.active_loan.currency+" - Repay by "+d.active_loan.repay_date+"<br><button class='btn' type='button' style='background:#000;color:#fff;padding:8px' onclick=\"payLoanNow('"+d.active_loan.id+"')\">💰 Pay Loan Now</button></div>"}else lb.innerHTML="";checkLoanDueWith(d.active_loan)})}
function loadLeader(){fetch("/api/leaderboard?mode=pvp").then(function(r){return r.json()}).then(function(d){var h="";(d.players||[]).slice(0,5).forEach(function(p,i){h+="<div class='leadRow' onclick=\"viewOther('"+p.name+"')\"><span>"+(i+1)+". "+p.name+(p.active_loan?" 🏦":"")+"</span><span>🏆 "+p.wins+"W</span></div>"});document.getElementById("leaderList").innerHTML=h||"No players"})}
function setLeaderMode(m){leaderMode=m;["gold","gems","pvp"].forEach(function(x){var el=document.getElementById("tab"+x.charAt(0).toUpperCase()+x.slice(1));if(el)el.classList.remove("active")});var a=document.getElementById("tab"+m.charAt(0).toUpperCase()+m.slice(1));if(a)a.classList.add("active");openFullLeader()}
function openFullLeader(){showPage("page-leader");fetch("/api/leaderboard?mode="+leaderMode).then(function(r){return r.json()}).then(function(d){var h="";(d.players||[]).forEach(function(p,i){h+="<div class='leadRow' onclick=\"viewOther('"+p.name+"')\"><span>"+(i+1)+". "+p.name+"<br><small>"+p.player_id+(p.active_loan?" | 🏦 Has Loan":"")+"</small></span><span>"+(leaderMode==="gold"?"🪙 "+p.gold:leaderMode==="gems"?"💎 "+p.gems:"🏆 "+p.wins+"W")+"</span></div>"});document.getElementById("fullLeaderList").innerHTML=h||"No players"})}
function viewOther(name){fetch("/api/player?name="+encodeURIComponent(name)).then(function(r){return r.json()}).then(function(d){showPage("page-other");document.getElementById("otherName").innerText=d.name;document.getElementById("otherRank").innerText=d.rank;document.getElementById("otherWins").innerText=d.wins;document.getElementById("otherLoss").innerText=d.losses;document.getElementById("otherActions").innerHTML="<button class='btn' type='button' onclick=\"openBankSendTo('"+d.player_id+"')\">💸 Send Gold</button><button class='btn2' type='button' onclick=\"sendFriendTo('"+d.player_id+"')\">👥 Send Friend Request</button>"})}
function openMyProfile(){showPage("page-profile");fetch("/api/player?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){document.getElementById("profName").innerText=special(d.name,user.password);document.getElementById("profIDShow").innerText="ID:"+d.player_id;document.getElementById("profBankID").innerText=d.bank_id;document.getElementById("profRank").innerText="#-";document.getElementById("profWins").innerText=d.wins;document.getElementById("profLoss").innerText=d.losses;document.getElementById("profGold").innerText=d.gold;document.getElementById("profGems").innerText=d.gems;document.getElementById("profCars").innerText=(d.cars||[]).join(", ")||"None";document.getElementById("profGalaxy").innerText=d.galaxy_level||1;document.getElementById("profGalaxyKills").innerText=d.galaxy_kills||0;var lb=document.getElementById("profLoanBox");if(d.active_loan){lb.style.display="block";lb.innerHTML="🏦 ACTIVE LOAN - PENDING<br>"+d.active_loan.amount+" "+d.active_loan.currency+"<br>Repay by: "+d.active_loan.repay_date+"<br><button class='btn' type='button' onclick=\"payLoanNow('"+d.active_loan.id+"')\">💰 Pay Now</button>"}else lb.style.display="none";var fh="";(d.friends||[]).forEach(function(f){fh+="<div style='padding:10px;background:rgba(0,0,0,.4);border-radius:12px;margin:6px 0;display:flex;justify-content:space-between'><span>👥 "+f+"</span><button class='btn' type='button' style='width:auto;padding:6px 10px' onclick=\"openChatWith('"+f+"')\">💬 Chat</button></div>"});document.getElementById("profFriends").innerHTML=fh||"No friends yet";var rh="";(d.friend_requests||[]).forEach(function(rq){rh+="<div style='padding:10px;background:rgba(255,215,0,.2);border-radius:12px;margin:6px 0'>👥 "+rq.from+"<br><button class='btn' type='button' onclick=\"respondFriend('"+rq.id+"',true)\">✅ Accept</button><button class='btn2' type='button' onclick=\"respondFriend('"+rq.id+"',false)\">❌ Decline</button></div>"});document.getElementById("profFriendReqs").innerHTML=rh||"No pending requests";var inv=d.items||[];var h="";inv.forEach(function(it){h+="<div style='padding:10px;background:rgba(0,0,0,.4);border-radius:12px;margin:6px 0'>🎒 "+it+"</div>"});document.getElementById("profInventory").innerHTML=h||"No items";var cb=document.getElementById("consumeBox");var drink=inv.find(function(x){return /Cola|Juice|Drink/.test(x)});var food=inv.find(function(x){return /Burger|Pizza|Donut/.test(x)});var h2="";if(drink)h2+="<button class='btn' type='button' onclick=\"consumeP('"+drink+"')\">🥤 Drink "+drink+"</button>";if(food)h2+="<button class='btn2' type='button' onclick=\"consumeP('"+food+"')\">🍔 Eat "+food+"</button>";cb.innerHTML=h2})}
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
function checkLoanDue(){if(!user)return;fetch("/api/player?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){checkLoanDueWith(d.active_loan)})}
function checkLoanDueWith(loan){if(!loan)return;var today=new Date();today.setHours(0,0,0,0);var due=new Date(loan.repay_date);due.setHours(0,0,0,0);if(today>=due){currentLoan=loan;document.getElementById("loanDueText").innerText="Your loan of "+loan.amount+" "+loan.currency+" is DUE ("+loan.repay_date+").";var o=document.getElementById("loanDueOverlay");o.classList.remove("hidden");o.style.display="flex"}}
function loanDueAction(act){var o=document.getElementById("loanDueOverlay");o.classList.add("hidden");o.style.display="none";if(!currentLoan)return;if(act==="collect"){payLoanNow(currentLoan.id);setTimeout(function(){fetch("/api/loan_due",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,loan_id:currentLoan.id,action:"collect"})}).then(function(r){return r.json()}).then(function(d){toast(d.error||("⚠️ Collected - Wins taken: "+d.wins_taken));loadMe()})},600)}else{fetch("/api/loan_due",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,loan_id:currentLoan.id,action:"extend"})}).then(function(r){return r.json()}).then(function(d){toast(d.error||("⏳ Extended to "+d.new_date));loadMe()})}}
function loanDateRespond(yes){var o=document.getElementById("loanDatePopup");o.classList.add("hidden");o.style.display="none";if(!pendingLoanForDate)return;fetch("/api/loan_player_confirm",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,loan_id:pendingLoanForDate,approve:yes})}).then(function(r){return r.json()}).then(function(d){toast(d.error||(yes?"✅ Loan Received":"❌ Loan Refunded"));pendingLoanForDate=null;loadMe();openMyProfile()})}
function openBankSendTo(id){openSendPage();document.getElementById("sendDigits").value=id.replace("INF-","")}
function openSendPage(){showPage("page-send");fetch("/api/player?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){document.getElementById("sendPageGold").innerText=d.gold;document.getElementById("sendPageGems").innerText=d.gems;document.getElementById("sendPageMyID").innerText=d.player_id})}
function openWithdrawPage(){showPage("page-withdraw")}
function openDepositPage(){showPage("page-deposit")}
function openExchangePage(){showPage("page-exchange");document.getElementById("exchangeForm").innerHTML=""}
function openExchange(dir){document.getElementById("exchangeForm").innerHTML="<input id='exAmt' type='number' placeholder='Amount'><button class='btn' type='button' onclick=\"doExchange('"+dir+"')\">Confirm</button>"}
function doSend(){var dg=document.getElementById("sendDigits").value.replace(/[^0-9]/g,"");var amt=parseInt(document.getElementById("sendAmt").value||"0");if(dg.length<8||!amt){toast("ID + Amount");return}openPin("PIN send "+amt,function(pin){fetch("/api/transfer",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({sender:user.name,pin:pin,receiver_id:"INF-"+dg,amount:amt})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.sender_gold;saveLocal();toast("✅ Sent")})})}
function doWithdraw(){var amt=parseInt(document.getElementById("withdrawAmt").value||"0");var cur=document.getElementById("withdrawCur").value;openPin("PIN withdraw "+amt,function(pin){fetch("/api/bank_action",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,amount:amt,action:"withdraw",currency:cur})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.gold;myGems=d.gems;saveLocal();toast("✅ Withdrawn")})})}
function doDeposit(){var amt=parseInt(document.getElementById("depositAmt").value||"0");var cur=document.getElementById("depositCur").value;openPin("PIN deposit "+amt,function(pin){fetch("/api/bank_action",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,amount:amt,action:"deposit",currency:cur})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.gold;myGems=d.gems;saveLocal();toast("✅ Deposited")})})}
function doExchange(dir){var amt=parseInt(document.getElementById("exAmt").value||"0");openPin("PIN Exchange",function(pin){fetch("/api/exchange",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,amount:amt,direction:dir})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.gold;myGems=d.gems;saveLocal();toast("✅ Exchanged")})})}
function openNotifs(){showPage("page-notifs");fetch("/api/player?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){var h="";(d.notifs||[]).slice().reverse().forEach(function(n){if(n.type==="loan_request"&&isDom()){h+="<div style='padding:12px;background:rgba(255,215,0,.2);border-radius:12px;margin:6px 0'><b>🏦 LOAN:</b> "+n.text+"<br><input type='date' id='domDate_"+n.loan_id+"' value='"+(n.repay_date||"")+"'><br><button class='btn' type='button' onclick=\"dominicLoan('"+n.loan_id+"',true)\">✅ Approve</button><button class='btn2' type='button' onclick=\"dominicLoan('"+n.loan_id+"',false)\">❌ Decline</button></div>"}else if(n.type==="request"&&isDom()){h+="<div style='padding:12px;background:rgba(255,0,255,.15);border-radius:12px;margin:6px 0'><b>🔒 SECRET:</b> "+n.text+"<br><input type='number' id='domAmt_"+n.request_id+"' value='"+(n.amount||"")+"' placeholder='Amount'><br><button class='btn' type='button' onclick=\"dominicReq('"+n.request_id+"','"+n.currency+"')\">✅ Approve</button></div>"}else if(n.type==="loan_date_change"){h+="<div style='padding:12px;background:#00ff88;color:#000;border-radius:12px;margin:6px 0'><b>📅 Dominic changed date to "+n.new_date+"</b><br><button class='btn' type='button' style='background:#000;color:#fff' onclick=\"showLoanDatePopup('"+n.loan_id+"','"+n.new_date+"')\">📅 View / Accept</button></div>"}else{h+="<div style='padding:10px;background:rgba(0,0,0,.4);border-radius:12px;margin:6px 0'>"+n.text+"<br><small>"+(n.time||"")+"</small></div>"}});document.getElementById("notifList").innerHTML=h||"No notifications"})}
function showLoanDatePopup(id,dt){pendingLoanForDate=id;document.getElementById("loanDatePopupText").innerText="Dominic set repay date to "+dt+". Tap Yes to receive loan, No to refund.";document.getElementById("loanDateInput").value=dt;var o=document.getElementById("loanDatePopup");o.classList.remove("hidden");o.style.display="flex"}
function dominicLoan(id,ok){var dt="";var el=document.getElementById("domDate_"+id);if(el)dt=el.value;openPin("PIN Dominic Loan",function(pin){fetch("/api/loan_dominic",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({admin:"dominic",pin:pin,loan_id:id,approve:ok,new_date:dt})}).then(function(r){return r.json()}).then(function(d){toast(d.error||(ok?"✅ Loan Approved":"❌ Declined"));openNotifs();loadMe()})})}
function dominicReq(id,cur){var amt=document.getElementById("domAmt_"+id).value;openPin("PIN Secret",function(pin){fetch("/api/request_approve",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({admin:"dominic",pin:pin,request_id:id,amount:amt,currency:cur})}).then(function(r){return r.json()}).then(function(d){toast(d.error||"✅ Secret Approved");openNotifs()})})}
function openEconomy(){if(!isDom()){toast("Dominic only");return}showPage("page-economy");fetch("/api/economy?name=dominic&password=2164").then(function(r){return r.json()}).then(function(d){var e=d.economy;document.getElementById("ecoGold").innerText=e.gold;document.getElementById("ecoGems").innerText=e.gems;document.getElementById("ecoBankGold").innerText=e.bank_gold;document.getElementById("ecoBankGems").innerText=e.bank_gems;document.getElementById("ecoLottery").innerText=e.lottery||0;document.getElementById("ecoBackup").innerText=e.backup||0;document.getElementById("ecoStatus").innerText=e.gold<0?"⚠️ NEGATIVE - Emergency unlocked":"✅ Economy Healthy";document.getElementById("emergencyBtn").disabled=e.gold>=0;document.getElementById("emergencyBtn").style.background=e.gold<0?"#ff2222":"#666";var h="";(d.backups||[]).forEach(function(b){h+="<div>"+b.file+" - Players: "+b.players+" - Exists: "+b.exists+"</div>"});document.getElementById("ecoBackups").innerHTML=h;var rh="";(d.requests||[]).forEach(function(rq){rh+="<div style='padding:10px;background:rgba(0,0,0,.4);border-radius:12px;margin:6px 0'>🔒 "+rq.from+" wants "+rq.amount+" "+rq.currency+"<br><button class='btn' type='button' onclick=\"dominicReq('"+rq.id+"','"+rq.currency+"')\">Approve (use amount in Notifs)</button></div>"});document.getElementById("ecoRequests").innerHTML=rh||"No requests";var lh="";(d.loans||[]).forEach(function(l){lh+="<div style='padding:10px;background:rgba(0,0,0,.4);border-radius:12px;margin:6px 0'>🏦 "+l.from+" - "+l.amount+" "+l.currency+" repay "+l.repay_date+"<br><input type='date' id='ecoDate_"+l.id+"' value='"+l.repay_date+"'><button class='btn' type='button' onclick=\"dominicLoanEco('"+l.id+"',true)\">Approve</button></div>"});document.getElementById("ecoLoans").innerHTML=lh||"No loans"})}
function dominicLoanEco(id,ok){var dt=document.getElementById("ecoDate_"+id).value;openPin("PIN Dominic",function(pin){fetch("/api/loan_dominic",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({admin:"dominic",pin:pin,loan_id:id,approve:ok,new_date:dt})}).then(function(){toast("Done");openEconomy()})})}
function doEmergency(){openPin("PIN Emergency",function(pin){fetch("/api/emergency",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:"dominic",pin:pin})}).then(function(r){return r.json()}).then(function(d){toast(d.error||"🚨 Economy Restored");openEconomy()})})}
function openAnnounce(){if(!isDom()){toast("Dominic only");return}var o=document.getElementById("announceOverlay");o.classList.remove("hidden");o.style.display="flex"}
function closeAnnounce(){var o=document.getElementById("announceOverlay");o.classList.add("hidden");o.style.display="none"}
function sendAnnounce(){var t=document.getElementById("annText").value;closeAnnounce();fetch("/api/announce",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({admin:"dominic",pin:"2164",text:t})}).then(function(){toast("📢 Announced")})}
function checkAnn(){fetch("/api/announcements").then(function(r){return r.json()}).then(function(d){if(d.announcements&&d.announcements.length){var a=d.announcements[d.announcements.length-1];var bar=document.getElementById("announceBar");bar.innerText="📢 "+a.text;bar.classList.remove("hidden");setTimeout(function(){bar.classList.add("hidden")},8000)}})}
function openServerInfo(){if(!isDom()){toast("Dominic only");return}showPage("page-server-info");fetch("/api/server_info?name=dominic&password=2164").then(function(r){return r.json()}).then(function(d){document.getElementById("serverPlayers").innerText=d.players;var h="";(d.backups||[]).forEach(function(b){h+="<div>"+b.file+" - "+b.players+" players</div>"});document.getElementById("serverBackups").innerHTML=h;var rh="";(d.reviews||[]).forEach(function(rv){rh+="<div style='padding:8px;background:rgba(0,0,0,.4);border-radius:10px;margin:5px 0'><b>"+rv.name+"</b>: "+rv.text+"</div>"});document.getElementById("serverReviewsList").innerHTML=rh||"No reviews"})}
function doServerUpdate(){toast("🚀 Update applied - Redeploy on Render to finish");toggleGameSwitch()}
function openMenuPage(){showPage("page-menu");document.getElementById("menuGamesList").innerHTML="<button class='btn' type='button' onclick='openRiddles()'>🧩 Riddles</button><button class='btn' type='button' onclick='openBible()'>📖 Bible Fight</button><button class='btn' type='button' onclick='openSciFi()'>🚀 SCI-FI</button><button class='btn' type='button' onclick='openShop()'>🛍️ Shop</button><button class='btn' type='button' onclick='openLottery()'>🎰 Lottery</button><button class='btn' type='button' onclick='openMessages()'>💚 WhatsApp</button><button class='btn' type='button' onclick='openBank()'>💰 Bank</button><button class='btn' type='button' onclick='openMyProfile()'>👤 Profile</button><button class='btn' type='button' onclick=\"openReview('review')\">⭐ Review</button>"}
function openReview(t){reviewType=t;showPage("page-review");document.getElementById("reviewTitle").innerText=t==="bug"?"🐛 Report Bug":"⭐ Review"}
function submitReview(){var t=document.getElementById("reviewText").value;fetch("/api/review",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,type:reviewType,text:t})}).then(function(){toast("✅ Sent");goDash()})}
function openLottery(){showPage("page-lottery")}
function playLottery(){var bet=parseInt(document.getElementById("lotBet").value||"0");var cur=document.getElementById("lotCur").value;openPin("PIN Lottery",function(pin){fetch("/api/lottery",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,bet:bet,currency:cur})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.gold;myGems=d.gems;saveLocal();document.getElementById("lotResult").innerHTML=d.result.win?"🎉 WON +"+d.result.prize:"😢 Lost "+d.result.lost})})}
function openSciFi(){var now=new Date();var unlock=new Date(2026,11,25);if(now<unlock){showPage("page-coming");var diff=unlock-now;var days=Math.floor(diff/86400000);document.getElementById("countDown").innerText=days+" days left";return}showPage("page-scifi");document.getElementById("scifiList").innerHTML="<button class='btn' type='button' onclick=\"startGalaxy()\">🌌 Galaxy Shooter</button><button class='btn' type='button' onclick=\"startDino()\">🦖 Dino Jump</button><button class='btn' type='button' onclick=\"startMatch()\">🍬 Royal Match</button>"}
function startGalaxy(){showPage("page-game");document.getElementById("gameTitle").innerText="🌌 Galaxy Shooter";document.getElementById("gameBody").innerHTML="<p>Kills: <b id='gKills'>0</b></p><button class='btn' type='button' onclick='galaxyKills++;document.getElementById(\"gKills\").innerText=galaxyKills;if(galaxyKills%5==0){wins+=5;myGold+=500;saveLocal();syncScore();toast(\"+5 Wins +500 Gold\")}'>🔫 SHOOT</button><button class='btn2' type='button' onclick='goDash()'>Back</button>"}
function startDino(){showPage("page-game");document.getElementById("gameTitle").innerText="🦖 Dino Jump";var j=0;document.getElementById("gameBody").innerHTML="<p>Jumps: <b id='dJumps'>0</b></p><button class='btn' type='button' id='dinoBtn'>🦖 JUMP</button><button class='btn2' type='button' onclick='goDash()'>Back</button>";document.getElementById("dinoBtn").onclick=function(){j++;document.getElementById("dJumps").innerText=j;if(j%10==0){wins+=2;saveLocal();syncScore();toast("+2 Wins")}}}
function startMatch(){showPage("page-game");document.getElementById("gameTitle").innerText="🍬 Royal Match";document.getElementById("gameBody").innerHTML="<p>Score: <b id='mScore'>0</b></p><div class='grid'><div class='box' onclick='matchHit()'>🍬</div><div class='box' onclick='matchHit()'>🍭</div><div class='box' onclick='matchHit()'>🍫</div><div class='box' onclick='matchHit()'>🍩</div></div><button class='btn2' type='button' onclick='goDash()'>Back</button>"}
function matchHit(){matchScore++;document.getElementById("mScore").innerText=matchScore;if(matchScore%5==0){wins+=1;myGold+=100;saveLocal();syncScore();toast("+1 Win +100 Gold")}}
function hostPickMode(m){toast("Challenge mode: "+m+" - Coming in PvP");goDash()}
function openRiddles(){startQuiz("Riddles")}
function openBible(){startQuiz("Bible Fight")}
function startQuiz(mode){quizMode=mode;quizScore=0;quizIdx=0;var qs=mode==="Riddles"?[["What has keys but can't open locks?","Piano"],["What runs but never walks?","Water"],["I speak without a mouth?","Echo"]]:[["Who built the ark?","Noah"],["Who defeated Goliath?","David"],["First book of Bible?","Genesis"]];quizRound=qs;showPage("page-game");document.getElementById("gameTitle").innerText=mode;showQuizQ()}
function showQuizQ(){if(quizIdx>=quizRound.length){wins+=quizScore;myGold+=quizScore*100;saveLocal();syncScore();document.getElementById("gameBody").innerHTML="<h3>Done! Score "+quizScore+"/"+quizRound.length+"</h3><p>+ "+(quizScore*100)+" Gold</p><button class='btn' type='button' onclick='goDash()'>Back Home</button>";return}var q=quizRound[quizIdx];document.getElementById("gameBody").innerHTML="<p>Q"+(quizIdx+1)+"/"+quizRound.length+": <b>"+q[0]+"</b></p><input id='quizAns' placeholder='Your answer'><button class='btn' type='button' onclick='answerQuiz()'>Answer</button><div class='timerBar'><div class='timerFill' style='width:100%'></div></div>"}
function answerQuiz(){var a=document.getElementById("quizAns").value.trim().toLowerCase();var correct=quizRound[quizIdx][1].toLowerCase();if(a===correct||a.indexOf(correct)>=0||correct.indexOf(a)>=0&&a.length>2){quizScore++;toast("✅ Correct +1")}else toast("❌ Answer: "+quizRound[quizIdx][1]);quizIdx++;showQuizQ()}
function setShopCat(c){shopCat=c;openShop()}
function openShop(){showPage("page-shop");renderShop()}
function renderShop(){var items=[["Toyota Corolla",5000,"Cars"],["BMW M4",15000,"Cars"],["Lamborghini",50000,"Cars"],["Ferrari",60000,"Cars"],["Tesla",30000,"Cars"],["Mercedes",25000,"Cars"],["Audi",20000,"Cars"],["Range Rover",28000,"Cars"],["Hilux",18000,"Cars"],["Nissan GTR",22000,"Cars"],["Bugatti",100000,"Cars"],["Burger",500,"Food"],["Pizza",800,"Food"],["Donut",300,"Food"],["Cola",200,"Food"],["Juice",250,"Food"],["Phone",8000,"Tech"],["Laptop",20000,"Tech"],["Headphones",5000,"Tech"],["Dog",10000,"Pets"],["Cat",8000,"Pets"]];var grid=document.getElementById("shopGrid");if(!grid)return;var html="";items.forEach(function(it){if(shopCat!=="All"&&it[2]!==shopCat)return;var owned=myCars.indexOf(it[0])>=0;html+="<div class='shopBox'><b>"+it[0]+"</b><div>Gold "+it[1]+"</div><div style='font-size:11px;color:#ffd700'>"+it[2]+"</div>"+(owned?"<div style='color:#00ff88;font-weight:900'>OWNED</div>":"<button class='btn' type='button' onclick=\"buyShopItem('"+it[0]+"',"+it[1]+")\">Buy</button>")+"</div>"});grid.innerHTML=html||"No items"}
function buyShopItem(name,price){openPin("PIN Buy "+name+" "+price,function(pin){fetch("/api/buy_item",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,item:name,price:price})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.gold;saveLocal();syncScore();toast("Bought "+name);openShop();loadMe()})})}
function openMessages(){showPage("page-messages");fetch("/api/friends?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){var h="";(d.friends||[]).forEach(function(f){h+="<div class='leadRow' onclick=\"openChatWith('"+f.name+"')\"><span>"+f.name+"</span><span>Chat</span></div>"});if(d.requests&&d.requests.length){h+="<h3>Friend Requests</h3>";d.requests.forEach(function(rq){h+="<div style='padding:10px;background:rgba(255,215,0,.2);border-radius:12px;margin:6px 0'>"+rq.from+"<br><button class='btn' type='button' onclick=\"respondFriend('"+rq.id+"',true)\">Accept</button><button class='btn2' type='button' onclick=\"respondFriend('"+rq.id+"',false)\">Decline</button></div>"})}document.getElementById("chatFriendList").innerHTML=h||"No friends yet - Send request by ID"})}
function openChatWith(name){chatWithName=name;showPage("page-chat");document.getElementById("chatWith").innerText=name;loadChat()}
function loadChat(){if(!chatWithName)return;fetch("/api/chat_get?a="+encodeURIComponent(user.name)+"&b="+encodeURIComponent(chatWithName)).then(function(r){return r.json()}).then(function(d){var h="";(d.messages||[]).forEach(function(m){h+="<div style='padding:8px;margin:6px 0;border-radius:12px;background:"+(m.from===user.name?"#00cc44":"rgba(255,255,255,.2)")+"'><b>"+m.from+":</b> "+m.text+"</div>"});var box=document.getElementById("chatBox");if(box){box.innerHTML=h||"No messages yet";box.scrollTop=box.scrollHeight}})}
function sendMsg(){var t=document.getElementById("msgInput").value.trim();if(!t||!chatWithName)return;document.getElementById("msgInput").value="";fetch("/api/chat_send",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({sender:user.name,to:chatWithName,text:t})}).then(function(){loadChat()})}
function openPin(desc,cb){pinCb=cb;document.getElementById("pinDesc").innerText=desc;document.getElementById("pinInput").value="";var o=document.getElementById("pinOverlay");o.classList.remove("hidden");o.style.display="flex";playPin()}
function closePin(){var o=document.getElementById("pinOverlay");o.classList.add("hidden");o.style.display="none";pinCb=null}
function confirmPin(){var pin=document.getElementById("pinInput").value.trim();if(pin.length!==4){toast("4 digits");return}var cb=pinCb;closePin();if(cb)cb(pin)}
function setupMenu(){var mb=document.getElementById("menuBtn");if(mb){mb.onclick=function(e){e.stopPropagation();var drop=document.getElementById("menuDrop");if(drop.classList.contains("hidden")){var items="";if(isDom()){items+="<div onclick=\"openEconomy()\">Economy (Dominic)</div><div onclick=\"openAnnounce()\">Announcement</div><div onclick=\"openServerInfo()\">Server Info</div><div onclick=\"showPage('page-update')\">Update</div><div onclick=\"toggleGameSwitch()\" style='color:#ff5555'>SWITCH ON/OFF</div>"}items+="<div onclick=\"openMenuPage()\">Menu</div><div onclick=\"openShop()\">Shop</div><div onclick=\"openLottery()\">Lottery</div><div onclick=\"toggleSound()\">Sound ON/OFF</div><div onclick=\"openMyProfile()\">My Profile</div><div onclick=\"doLogout()\" style='color:#ff5555'>Logout</div>";drop.innerHTML=items;drop.classList.remove("hidden")}else drop.classList.add("hidden")}};var pb=document.getElementById("profileBtn");if(pb)pb.onclick=function(){openMyProfile()};document.addEventListener("click",function(e){var drop=document.getElementById("menuDrop");var btn=document.getElementById("menuBtn");if(drop&&btn&&!drop.contains(e.target)&&e.target!==btn){drop.classList.add("hidden") }})}
setupMenu();
try{document.getElementById("enterBtn").onclick=function(){enterClicked()}}catch(e){}
if(user){fetch("/api/player?name="+encodeURIComponent(user.name)+"&password="+encodeURIComponent(user.password)).then(function(r){return r.json()}).then(function(d){if(d&&d.found&&d.password_ok!==false){wins=d.wins||0;myGold=d.gold||0;myGems=d.gems||0;myPlayerID=d.player_id||"";myBankID=d.bank_id||"";saveLocal()}}).catch(function(){})}
</script></body></html>"""
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
