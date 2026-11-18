
from flask import Flask, request, jsonify
import os, json, threading, random, datetime
app = Flask(__name__)
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN","infinity")
BASE = os.path.dirname(__file__)
LEADER_FILE = os.path.join(BASE,"leaderboard.json")
MSG_FILE = os.path.join(BASE,"messages.json")
USERS={}; MESSAGES={}; CHALLENGES={}
_lock=threading.Lock()
EARNING_ON=True
EARNING_START=datetime.datetime(2026,12,25,0,0,0)
RANKS=[("Beginner",0),("Intermediate",200),("Advanced",400),("Expert",800),("Professional",1600),("National",3200),("S Rank",6400),("SS Rank",12800),("SSS Rank",25600),("SSS Classified",51200),("Godly Rank Classified",102400)]
SERVER_ECONOMY={"gold":100000000,"gems":1000000,"bank_total":0,"fees":0,"lottery":0,"history":[100000000],"backup":10000000000}
REQUESTS=[]
def norm(n): return str(n or "").strip().lower()
def load_json_safe(p):
    try:
        if os.path.exists(p):
            with open(p,"r") as f:
                d=json.load(f)
                if isinstance(d,dict): return d
    except: pass
    return {}
def gen_id(): return "INF-"+"".join(str(random.randint(0,9)) for _ in range(8))
def gen_bank_id(): return "Bank INF-"+"".join(str(random.randint(0,9)) for _ in range(10))
def clean_id(s):
    s=str(s or "").upper().replace("BANK INF-","").replace("BANK","").replace("INF-","").replace("INF","").strip()
    return "".join(c for c in s if c.isdigit())
def rank_for(w):
    r="Beginner"
    for name,need in RANKS:
        if w>=need: r=name
    return r
def is_classified(w): return w>=3200
def ensure_player(v,k):
    v.setdefault("display_name",k); v.setdefault("history",{}); v.setdefault("friends",[]); v.setdefault("requests",[]); v.setdefault("wins",0); v.setdefault("losses",0); v.setdefault("stage",0); v.setdefault("gold",0); v.setdefault("gems",0); v.setdefault("bank_gold",0); v.setdefault("bank_gems",0); v.setdefault("notifs",[]); v.setdefault("seen_qs",[]); v.setdefault("items",[])
    if not v.get("player_id"): v["player_id"]=gen_id()
    if not v.get("bank_id"): v["bank_id"]=gen_bank_id()
    return v
def load_users():
    global USERS
    d=load_json_safe(LEADER_FILE)
    if d: USERS={norm(v.get("display_name",k) or k):ensure_player(v,k) for k,v in d.items()}
load_users()
try:
    if os.path.exists(MSG_FILE):
        with open(MSG_FILE) as f: MESSAGES=json.load(f)
except: pass
def save_users():
    try:
        with _lock:
            data=json.dumps(USERS)
            for p in [LEADER_FILE, os.path.join(BASE,"leaderboard.json.backup")]:
                with open(p,"w") as f: f.write(data)
    except Exception as e: print(e)
def is_earning_active(): return datetime.datetime.now()>=EARNING_START and EARNING_ON
def economy_add(a,src):
    SERVER_ECONOMY["gold"]+=a
    if src=="fees": SERVER_ECONOMY["fees"]+=a
    if src=="bank": SERVER_ECONOMY["bank_total"]+=a
    if src=="lottery": SERVER_ECONOMY["lottery"]+=a
    SERVER_ECONOMY["history"].append(SERVER_ECONOMY["gold"])
    if len(SERVER_ECONOMY["history"])>50: SERVER_ECONOMY["history"]=SERVER_ECONOMY["history"][-50:]
def notify(name,text,typ="info",extra=None):
    if norm(name) in USERS:
        n={"text":text,"time":str(datetime.datetime.now()),"type":typ}
        if extra: n.update(extra)
        USERS[norm(name)]["notifs"].append(n); save_users()
@app.route("/")
def home(): return HOME
@app.route("/api/earning_status")
def earning_status(): return jsonify({"earning_on":EARNING_ON,"active":is_earning_active(),"start":"2026-12-25"})
@app.route("/api/toggle_earning",methods=["POST"])
def toggle_earning():
    global EARNING_ON
    d=request.get_json() or {}
    if norm(d.get("name"))!="dominic" or str(d.get("password"))!="2164": return jsonify({"error":"Only Dominic"}),403
    EARNING_ON=not EARNING_ON; return jsonify({"earning_on":EARNING_ON,"active":is_earning_active()})
@app.route("/api/player")
def get_player():
    n=norm(request.args.get("name","")); pw=request.args.get("password","")
    if n in USERS:
        v=USERS[n]
        if pw and v.get("password") and str(v.get("password"))!=str(pw): return jsonify({"found":True,"password_ok":False,"name":v["display_name"],"player_id":v["player_id"]})
        return jsonify({"found":True,"password_ok":True,"name":v["display_name"],"wins":v["wins"],"losses":v["losses"],"stage":v["stage"],"gold":v["gold"],"gems":v["gems"],"bank_gold":v.get("bank_gold",0),"bank_gems":v.get("bank_gems",0),"player_id":v["player_id"],"bank_id":v.get("bank_id",""),"rank":rank_for(v["wins"]),"classified":is_classified(v["wins"]),"history":v["history"],"friends":v["friends"],"notifs":v.get("notifs",[]),"seen_qs":v.get("seen_qs",[]),"items":v.get("items",[])})
    return jsonify({"found":False})
@app.route("/api/leaderboard")
def leaderboard():
    mode=request.args.get("mode","pvp"); ps=[]
    for k,v in USERS.items(): ps.append({"name":v["display_name"],"wins":v["wins"],"losses":v["losses"],"gold":v.get("gold",0),"gems":v.get("gems",0),"player_id":v.get("player_id",""),"rank":rank_for(v["wins"]),"rank_idx":next((i for i,(rn,_) in enumerate(RANKS) if rn==rank_for(v["wins"])),0)})
    if mode=="gold": ps=sorted(ps,key=lambda x:x["gold"],reverse=True)
    elif mode=="gems": ps=sorted(ps,key=lambda x:x["gems"],reverse=True)
    elif mode=="rank": ps=sorted(ps,key=lambda x:x["rank_idx"],reverse=True)
    else: ps=sorted(ps,key=lambda x:(x["wins"]-x["losses"]),reverse=True)
    return jsonify({"players":ps})
@app.route("/api/score",methods=["POST"])
def score():
    d=request.get_json() or {}; n=norm(d.get("name"))
    if not n: return jsonify({"error":"no name"}),400
    if n not in USERS: USERS[n]=ensure_player({"display_name":d.get("name"),"password":d.get("password","")},d.get("name"))
    v=USERS[n]
    if d.get("password"): v["password"]=d.get("password")
    v["wins"]=d.get("wins",v["wins"]); v["losses"]=d.get("losses",v["losses"]); v["stage"]=d.get("stage",v["stage"])
    if "gold" in d: v["gold"]=d["gold"]
    if "gems" in d: v["gems"]=d["gems"]
    if "seen_qs" in d: v["seen_qs"]=d["seen_qs"]
    if "items" in d: v["items"]=d["items"]
    save_users(); return jsonify({"ok":True,"gold":v["gold"],"gems":v["gems"],"player_id":v["player_id"],"rank":rank_for(v["wins"])})
@app.route("/api/transfer",methods=["POST"])
def transfer():
    d=request.get_json() or {}; sender=norm(d.get("sender")); pin=str(d.get("pin","")); amt=int(d.get("amount",0)); cur=d.get("currency","Gold")
    if not is_earning_active(): return jsonify({"error":"Transfers blocked"}),403
    if sender not in USERS: return jsonify({"error":"Sender not found"}),404
    s=USERS[sender]
    if str(s.get("password"))!=pin: notify(sender,"⚠️ Warning! Pin is wrong.","warn"); return jsonify({"error":"Wrong PIN"}),403
    rid="INF-"+clean_id(d.get("receiver_id","")); recv=None
    for v in USERS.values():
        if v.get("player_id")==rid: recv=v; break
    if not recv: return jsonify({"error":"Receiver ID not found"}),404
    if cur=="Gems":
        if s.get("gems",0)<amt: return jsonify({"error":"Not enough Gems"}),400
        s["gems"]-=amt; recv["gems"]=recv.get("gems",0)+amt
    else:
        if s.get("gold",0)<amt: return jsonify({"error":"Not enough Gold"}),400
        fee=int(amt*0.05); net=amt-fee; s["gold"]-=amt; recv["gold"]=recv.get("gold",0)+net; economy_add(fee,"fees")
    notify(sender,f"Dear player you have successfully sent {amt} {cur} to {rid}.","send")
    notify(recv["display_name"],f"Dear {recv['display_name']} you have received {amt} {cur} from {s.get('player_id')}.","receive")
    save_users(); return jsonify({"ok":True,"sender_gold":s["gold"],"sender_gems":s["gems"]})
@app.route("/api/bank_action",methods=["POST"])
def bank_action():
    d=request.get_json() or {}; n=norm(d.get("name")); pin=str(d.get("pin","")); amt=int(d.get("amount",0)); action=d.get("action","deposit"); cur=d.get("currency","Gold")
    if not is_earning_active(): return jsonify({"error":"Bank blocked"}),403
    if n not in USERS: return jsonify({"error":"Not found"}),404
    v=USERS[n]
    if str(v.get("password"))!=pin: notify(n,"⚠️ Warning! Pin is wrong.","warn"); return jsonify({"error":"Wrong PIN"}),403
    if action=="deposit":
        if cur=="Gems":
            if v.get("gems",0)<amt: return jsonify({"error":"Not enough Gems"}),400
            v["gems"]-=amt; v["bank_gems"]=v.get("bank_gems",0)+amt
        else:
            if v.get("gold",0)<amt: return jsonify({"error":"Not enough Gold"}),400
            v["gold"]-=amt; v["bank_gold"]=v.get("bank_gold",0)+amt; economy_add(amt,"bank")
        notify(n,f"Dear player you have successfully deposited {amt} {cur} to your Bank {v.get('bank_id')}.","deposit")
    elif action=="withdraw":
        if cur=="Gems":
            if v.get("bank_gems",0)<amt: return jsonify({"error":"Not enough in Bank"}),400
            v["bank_gems"]-=amt; v["gems"]=v.get("gems",0)+amt
        else:
            if v.get("bank_gold",0)<amt: return jsonify({"error":"Not enough in Bank"}),400
            v["bank_gold"]-=amt; v["gold"]=v.get("gold",0)+amt
        notify(n,f"Dear player you have successfully withdrawn {amt} {cur}.","withdraw")
    save_users(); return jsonify({"ok":True,"gold":v["gold"],"gems":v["gems"],"bank_gold":v.get("bank_gold",0),"bank_gems":v.get("bank_gems",0)})
@app.route("/api/exchange",methods=["POST"])
def exchange():
    d=request.get_json() or {}; n=norm(d.get("name")); pin=str(d.get("pin","")); amt=int(d.get("amount",0)); direction=d.get("direction","gold_to_gem")
    if not is_earning_active(): return jsonify({"error":"Exchange blocked"}),403
    if n not in USERS: return jsonify({"error":"Not found"}),404
    v=USERS[n]
    if str(v.get("password"))!=pin: return jsonify({"error":"Wrong PIN"}),403
    if direction=="gold_to_gem":
        if v.get("gold",0)<amt: return jsonify({"error":"Not enough Gold"}),400
        gems=amt//100
        if gems<1: return jsonify({"error":"Need at least 100 Gold = 1 Germ"}),400
        v["gold"]-=gems*100; v["gems"]=v.get("gems",0)+gems
    else:
        if v.get("gems",0)<amt: return jsonify({"error":"Not enough Gems"}),400
        v["gems"]-=amt; v["gold"]=v.get("gold",0)+(amt*100)
    save_users(); return jsonify({"ok":True,"gold":v["gold"],"gems":v["gems"]})
@app.route("/api/withdraw",methods=["POST"])
def withdraw():
    d=request.get_json() or {}; n=norm(d.get("name")); pin=str(d.get("pin","")); amt=int(d.get("amount",0)); cur=d.get("currency","Gold")
    if not is_earning_active(): return jsonify({"error":"Withdrawals blocked"}),403
    if n not in USERS: return jsonify({"error":"Not found"}),404
    v=USERS[n]
    if str(v.get("password"))!=pin: return jsonify({"error":"Wrong PIN"}),403
    if cur=="Gold":
        if v.get("gold",0)<amt: return jsonify({"error":"Not enough Gold"}),400
        v["gold"]-=amt
    else:
        if v.get("gems",0)<amt: return jsonify({"error":"Not enough Gems"}),400
        v["gems"]-=amt
    notify(n,f"Dear player you have successfully withdrawn {amt} {cur}.","withdraw")
    save_users(); return jsonify({"ok":True,"gold":v["gold"],"gems":v["gems"]})
@app.route("/api/challenge_send",methods=["POST"])
def challenge_send():
    d=request.get_json() or {}; sender=norm(d.get("sender")); tid="INF-"+clean_id(d.get("target_id","")); game=d.get("game","Galaxy Shooter")
    if sender not in USERS: return jsonify({"error":"Sender not found"}),404
    s=USERS[sender]; target=None
    for v in USERS.values():
        if v.get("player_id")==tid: target=v; break
    if not target: return jsonify({"error":"Target ID not found"}),404
    cid=f"CH-{random.randint(10000000,99999999)}"
    CHALLENGES[cid]={"from":s["display_name"],"from_id":s.get("player_id"),"to":target["display_name"],"to_id":tid,"game":game,"status":"pending"}
    notify(target["display_name"],f"🎮 CHALLENGE REQUEST: {s['display_name']} challenged you to {game}!","challenge",{"challenge_id":cid,"game":game,"from":s["display_name"]})
    return jsonify({"ok":True,"challenge_id":cid})
@app.route("/api/challenge_respond",methods=["POST"])
def challenge_respond():
    d=request.get_json() or {}; cid=d.get("challenge_id")
    if cid in CHALLENGES:
        CHALLENGES[cid]["status"]="accepted" if d.get("accept") else "declined"
        return jsonify({"ok":True,"status":CHALLENGES[cid]["status"]})
    return jsonify({"error":"Not found"}),404
@app.route("/api/review",methods=["POST"])
def review():
    d=request.get_json() or {}
    try:
        with open(os.path.join(BASE,"reviews.json"),"a") as f: f.write(json.dumps({"name":d.get("name"),"type":d.get("type"),"text":d.get("text"),"time":str(datetime.datetime.now())})+"\n")
    except: pass
    return jsonify({"ok":True})
@app.route("/api/server_info")
def server_info():
    if norm(request.args.get("name"))!="dominic" or str(request.args.get("password"))!="2164": return jsonify({"error":"Admin only"}),403
    reviews=[]
    try:
        if os.path.exists(os.path.join(BASE,"reviews.json")):
            with open(os.path.join(BASE,"reviews.json")) as f: reviews=[json.loads(l) for l in f if l.strip()]
    except: pass
    return jsonify({"players":len(USERS),"earning_on":EARNING_ON,"earning_active":is_earning_active(),"reviews":reviews,"economy":SERVER_ECONOMY})
@app.route("/api/buy_item",methods=["POST"])
def buy_item():
    d=request.get_json() or {}; n=norm(d.get("name")); pin=str(d.get("pin","")); item=d.get("item",""); price=int(d.get("price",0))
    if n not in USERS: return jsonify({"error":"Not found"}),404
    v=USERS[n]
    if str(v.get("password"))!=pin: return jsonify({"error":"Wrong PIN"}),403
    if v.get("gold",0)<price: return jsonify({"error":"Not enough Gold"}),400
    v["gold"]-=price; v.setdefault("items",[]).append(item); economy_add(price,"fees")
    notify(n,f"Dear player you bought {item} for {price} Gold.","shop")
    save_users(); return jsonify({"ok":True,"gold":v["gold"],"items":v["items"]})
@app.route("/api/friends")
def friends():
    n=norm(request.args.get("name",""))
    if n not in USERS: return jsonify({"friends":[]})
    out=[]
    for f in USERS[n].get("friends",[]):
        if norm(f) in USERS:
            fv=USERS[norm(f)]; out.append({"name":fv["display_name"],"player_id":fv.get("player_id",""),"rank":rank_for(fv["wins"]),"wins":fv["wins"]})
    if not out:
        for k,vv in USERS.items():
            if k!=n: out.append({"name":vv["display_name"],"player_id":vv.get("player_id",""),"rank":rank_for(vv["wins"]),"wins":vv["wins"]})
    return jsonify({"friends":out})
@app.route("/api/add_friend",methods=["POST"])
def add_friend():
    d=request.get_json() or {}; n=norm(d.get("name")); tid="INF-"+clean_id(d.get("target_id",""))
    if n not in USERS: return jsonify({"error":"Not found"}),404
    for v in USERS.values():
        if v.get("player_id")==tid:
            if v["display_name"] not in USERS[n]["friends"]: USERS[n]["friends"].append(v["display_name"])
            if USERS[n]["display_name"] not in v["friends"]: v["friends"].append(USERS[n]["display_name"])
            notify(v["display_name"],f"👥 {USERS[n]['display_name']} added you as friend!","friend")
            save_users(); return jsonify({"ok":True})
    return jsonify({"error":"ID not found"}),404
@app.route("/api/chat_send",methods=["POST"])
def chat_send():
    d=request.get_json() or {}; sender=norm(d.get("sender")); to=norm(d.get("to")); text=str(d.get("text",""))[:500]; kind=d.get("kind","text")
    if sender not in USERS or to not in USERS: return jsonify({"error":"User not found"}),404
    key="|".join(sorted([sender,to]))
    MESSAGES.setdefault(key,[]).append({"from":USERS[sender]["display_name"],"to":USERS[to]["display_name"],"text":text,"kind":kind,"time":str(datetime.datetime.now())})
    notify(to,f"💬 New message from {USERS[sender]['display_name']}: {text[:60]}","chat")
    try:
        with open(MSG_FILE,"w") as f: f.write(json.dumps(MESSAGES))
    except: pass
    return jsonify({"ok":True})
@app.route("/api/chat_get")
def chat_get():
    a=norm(request.args.get("a","")); b=norm(request.args.get("b",""))
    key="|".join(sorted([a,b]))
    return jsonify({"messages":MESSAGES.get(key,[])})
@app.route("/api/request_money",methods=["POST"])
def request_money():
    d=request.get_json() or {}; n=norm(d.get("name")); amt=d.get("amount"); cur=d.get("currency","Gold"); msg=str(d.get("message",""))[:200]
    if n not in USERS: return jsonify({"error":"Not found"}),404
    v=USERS[n]
    if cur=="Gold" and amt and int(amt)>100000000: return jsonify({"error":"Gold max 100,000,000"}),400
    if cur=="Gems" and amt and int(amt)>100000: return jsonify({"error":"Germ max 100,000"}),400
    rid=f"RQ-{random.randint(10000000,99999999)}"
    REQUESTS.append({"id":rid,"from":v["display_name"],"from_id":v.get("player_id"),"amount":amt,"currency":cur,"message":msg,"status":"pending"})
    notify("dominic",f"💰 REQUEST: Player {v['display_name']} ({v.get('player_id')}) is Requesting for {amt if amt else '— amount not given —'} {cur}. Message: {msg or 'I want money'}","request",{"request_id":rid,"from":v["display_name"],"amount":amt,"currency":cur})
    return jsonify({"ok":True,"id":rid})
@app.route("/api/request_approve",methods=["POST"])
def request_approve():
    d=request.get_json() or {}
    if norm(d.get("admin"))!="dominic" or str(d.get("pin"))!="2164": return jsonify({"error":"Only Dominic 2164"}),403
    rid=d.get("request_id"); amt=int(d.get("amount",0)); cur=d.get("currency","Gold")
    for r in REQUESTS:
        if r["id"]==rid:
            r["status"]="approved"
            if cur=="Gold": SERVER_ECONOMY["gold"]-=amt
            else: SERVER_ECONOMY["gems"]-=amt
            SERVER_ECONOMY["history"].append(SERVER_ECONOMY["gold"])
            for v in USERS.values():
                if v.get("player_id")==r["from_id"]:
                    if cur=="Gold": v["gold"]=v.get("gold",0)+amt
                    else: v["gems"]=v.get("gems",0)+amt
                    notify(v["display_name"],f"Dear player you have received {amt} {cur} from The Servers Economy you request. 💰","request_ok")
            notify("dominic",f"You have sent {amt} {cur} to {r['from']} ({r['from_id']}). From Server Economy.","request_sent")
            save_users(); return jsonify({"ok":True,"economy":SERVER_ECONOMY})
    return jsonify({"error":"Request not found"}),404
@app.route("/api/lottery",methods=["POST"])
def lottery():
    d=request.get_json() or {}; n=norm(d.get("name")); pin=str(d.get("pin","")); bet=int(d.get("bet",0)); cur=d.get("currency","Gold")
    if n not in USERS: return jsonify({"error":"Not found"}),404
    v=USERS[n]
    if str(v.get("password"))!=pin: return jsonify({"error":"Wrong PIN"}),403
    if cur=="Gold":
        if v.get("gold",0)<bet: return jsonify({"error":"Not enough Gold"}),400
        v["gold"]-=bet
    else:
        if v.get("gems",0)<bet: return jsonify({"error":"Not enough Gems"}),400
        v["gems"]-=bet
    win = random.random()<0.5
    if win:
        prize=bet*2
        if cur=="Gold": v["gold"]+=prize; SERVER_ECONOMY["gold"]-=bet; SERVER_ECONOMY["lottery"]-=bet
        else: v["gems"]+=prize; SERVER_ECONOMY["gems"]-=bet
        notify(n,f"🎰 LOTTERY WIN! You won {prize} {cur}!","lottery"); res={"win":True,"prize":prize}
    else:
        if cur=="Gold": SERVER_ECONOMY["gold"]+=bet; SERVER_ECONOMY["lottery"]+=bet
        else: SERVER_ECONOMY["gems"]+=bet
        notify(n,f"🎰 LOTTERY LOSE! You lost {bet} {cur}. It went to Server Economy.","lottery"); res={"win":False,"lost":bet}
    SERVER_ECONOMY["history"].append(SERVER_ECONOMY["gold"])
    save_users(); return jsonify({"ok":True,"result":res,"gold":v["gold"],"gems":v["gems"],"economy":SERVER_ECONOMY["gold"]})
@app.route("/api/economy")
def economy():
    if norm(request.args.get("name"))!="dominic" or str(request.args.get("password"))!="2164": return jsonify({"error":"Admin only"}),403
    return jsonify({"economy":SERVER_ECONOMY,"requests":REQUESTS})
@app.route("/api/emergency",methods=["POST"])
def emergency():
    d=request.get_json() or {}
    if norm(d.get("name"))!="dominic" or str(d.get("pin"))!="2164": return jsonify({"error":"Only Dominic"}),403
    if SERVER_ECONOMY["gold"]>=0: return jsonify({"error":"Emergency only if economy is NEGATIVE"}),400
    if SERVER_ECONOMY["backup"]<10000000000: return jsonify({"error":"Backup not enough - Emergency Sleep Mode"}),400
    SERVER_ECONOMY["gold"]+=500000000000; SERVER_ECONOMY["backup"]-=500000000000
    if SERVER_ECONOMY["backup"]<0: SERVER_ECONOMY["backup"]=0
    SERVER_ECONOMY["history"].append(SERVER_ECONOMY["gold"])
    return jsonify({"ok":True,"economy":SERVER_ECONOMY})
@app.route("/webhook",methods=["GET","POST"])
def webhook():
    if request.method=="GET":
        if request.args.get("hub.mode")=="subscribe" and request.args.get("hub.verify_token")==VERIFY_TOKEN: return request.args.get("hub.challenge"),200
        return "Forbidden",403
    return jsonify({"ok":True})
HOME=r"""<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>INFINITY BOT v13</title>
<link href="https://fonts.googleapis.com/css2?family=Great+Vibes&family=Poppins:wght@400;700;900&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<style>*{box-sizing:border-box}body{margin:0;font-family:Poppins,Arial;color:white;background:radial-gradient(circle at 50% 20%,#3a0a5e,#12002b 70%);min-height:100vh}.cursive{font-family:'Great Vibes',cursive}.topbar{display:flex;justify-content:space-between;align-items:center;padding:8px 14px}.profile{width:46px;height:46px;border-radius:50%;background:linear-gradient(135deg,#ff006e,#ffd700);display:flex;align-items:center;justify-content:center;font-size:20px;border:2px solid #fff;cursor:pointer;position:relative}.notif{position:absolute;top:-6px;right:-6px;background:red;color:white;font-size:11px;width:20px;height:20px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:900}.center{min-height:82vh;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:20px}.crownBig{font-size:90px;filter:drop-shadow(0 0 30px gold)}.enterBtn{margin-top:20px;padding:16px 70px;font-family:'Great Vibes',cursive;font-size:48px;border:none;border-radius:60px;background:linear-gradient(90deg,#ff006e,#ffd700,#00e5ff);color:#000;box-shadow:0 0 40px #ff006e;cursor:pointer}.card{background:rgba(255,255,255,.08);border:2px solid rgba(255,255,255,.35);border-radius:26px;padding:20px;margin:14px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.box{background:linear-gradient(160deg,rgba(255,255,255,.18),rgba(0,0,0,.4));border:2px solid #fff;border-radius:24px;padding:22px 10px;text-align:center;cursor:pointer}.box span{font-size:38px;display:block}.btn{width:100%;padding:14px;border:none;border-radius:25px;font-weight:900;background:#ffd700;margin:6px 0;cursor:pointer}.btn2{width:100%;padding:13px;border-radius:25px;border:2px solid #00e5ff;background:transparent;color:#00e5ff;font-weight:900;margin:6px 0;cursor:pointer}.opt{width:100%;padding:13px;margin:7px 0;border-radius:16px;border:2px solid #fff;background:rgba(0,0,0,.5);color:white;font-weight:700;cursor:pointer;text-align:left}input{width:100%;padding:14px;border-radius:14px;border:2px solid #ffd700;margin:8px 0;font-size:16px;background:#fff;color:#000}.hidden{display:none!important}.leadRow{display:flex;justify-content:space-between;align-items:center;padding:10px 12px;background:rgba(0,0,0,.45);border-radius:14px;margin:6px 0;cursor:pointer}.toast{position:fixed;top:70px;left:50%;transform:translateX(-50%);background:#fff;color:#000;padding:12px 18px;border-radius:20px;font-weight:700;z-index:999;max-width:90%;text-align:center}.gameOverlay{position:fixed;inset:0;background:rgba(0,0,0,.75);display:flex;align-items:center;justify-content:center;padding:16px;z-index:500}.gamePopup{background:linear-gradient(160deg,#2b005e,#12002b);border:3px solid #ffd700;border-radius:28px;padding:22px 18px;max-width:420px;width:100%;text-align:center;box-shadow:0 0 40px #ff006e}.choiceRow{display:flex;gap:12px;margin-top:16px}.choiceBox{flex:1;padding:18px 8px;border-radius:20px;cursor:pointer;font-weight:900;font-size:18px;border:3px solid #fff}.choiceNo{background:linear-gradient(135deg,#ff2222,#ff6b6b);color:#fff}.choiceYes{background:linear-gradient(135deg,#00cc44,#00ff88);color:#000}.warnBar{height:6px;background:rgba(255,255,255,.25);border-radius:99px;overflow:hidden;margin-top:14px}.warnBarFill{height:100%;background:linear-gradient(90deg,#ff006e,#ffd700);width:100%;animation:shrink 5s linear forwards}@keyframes shrink{from{width:100%}to{width:0%}}.bottomNav{position:fixed;bottom:0;left:0;right:0;background:rgba(0,0,0,.85);border-top:2px solid #ffd700;display:flex;justify-content:space-around;padding:10px 0 14px;z-index:100}.bottomNav div{font-size:28px;cursor:pointer;text-align:center}.bottomNav small{display:block;font-size:10px;color:#ffd700}.walletCard{background:linear-gradient(135deg,#ffd700,#ff006e);color:#000;border-radius:24px;padding:18px;text-align:center}.switch{width:70px;height:36px;background:#00cc44;border-radius:99px;position:relative;cursor:pointer;border:2px solid #fff}.switch.off{background:#ff2222}.switchKnob{position:absolute;top:3px;left:34px;width:28px;height:28px;background:#fff;border-radius:50%}.switch.off .switchKnob{left:3px}.spacexScene{background:#000010;border:2px solid #00e5ff;border-radius:20px;padding:16px;text-align:left;font-family:'Share Tech Mono',monospace;color:#00ffaa}.scifiCode{font-family:'Share Tech Mono',monospace;color:#00ffaa;font-size:13px;line-height:1.7;white-space:pre-wrap;border:1px solid #00ffaa;border-radius:14px;padding:12px;background:rgba(0,0,0,.65);text-align:left}.pinInput{font-size:28px;text-align:center;letter-spacing:12px}.tabRow{display:flex;gap:8px}.tabBox{flex:1;padding:12px 4px;border-radius:16px;background:rgba(255,255,255,.15);border:2px solid #ffd700;text-align:center;cursor:pointer;font-weight:900;font-size:13px}.tabBox.active{background:#ffd700;color:#000}.bigBankBox{padding:22px 10px;border-radius:24px;border:2px solid #fff;text-align:center;cursor:pointer;background:linear-gradient(160deg,rgba(255,255,255,.18),rgba(0,0,0,.4))}.idPrefix{display:flex;align-items:center;background:#fff;border-radius:14px;border:2px solid #ffd700;padding:0 10px;margin:8px 0}.idPrefix b{color:#000;white-space:nowrap}.idPrefix input{border:none;flex:1;margin:0}.shopGrid{display:grid;grid-template-columns:1fr 1fr;gap:10px}.shopBox{background:linear-gradient(160deg,rgba(255,255,255,.18),rgba(0,0,0,.4));border:2px solid #fff;border-radius:18px;padding:14px 8px;text-align:center;cursor:pointer}.shopBox .ic{font-size:32px;display:block}.shopBox .nm{font-size:12px;font-weight:900;display:block;margin:6px 0 2px}.shopBox .pr{font-size:11px;color:#ffd700;font-weight:900}.shopBox .pp{font-size:10px;opacity:.7}
</style></head><body>
<div id="topbar" class="topbar"><div id="topLeft"><span style="font-size:11px;background:rgba(0,0,0,.55);border:1px solid #ffd700;padding:4px 8px;border-radius:20px" id="catTime">--:--:-- CAT</span><br><div style="font-weight:900;margin-top:4px">INFINITY BOT</div></div><div id="topRight" class="hidden" style="display:flex;flex-direction:column;align-items:flex-end;gap:2px"><div style="display:flex;gap:8px;align-items:center"><div style="width:32px;height:32px;border-radius:50%;background:rgba(0,0,0,.55);border:1px solid #ffd700;display:flex;align-items:center;justify-content:center;cursor:pointer" id="soundBtn">🔊</div><div style="width:32px;height:32px;border-radius:50%;background:rgba(0,0,0,.55);border:1px solid #ffd700;display:flex;align-items:center;justify-content:center;cursor:pointer" onclick="openShop('Top')">🛍️</div><div class="profile" id="profileBtn">👤<span id="notifBadge" class="notif hidden">1</span></div></div><div style="width:32px;height:32px;border-radius:50%;background:rgba(0,0,0,.55);border:1px solid #ffd700;display:flex;align-items:center;justify-content:center;font-size:20px;cursor:pointer;margin-right:7px" id="menuBtn">⋮</div></div></div>
<div id="menuDrop" class="hidden" style="position:absolute;top:110px;right:10px;background:#1a1a2e;border:2px solid #ffd700;border-radius:16px;padding:8px;z-index:500;min-width:200px"></div>
<div id="toast" class="toast hidden"></div>
<div id="pinOverlay" class="gameOverlay hidden" style="display:none;z-index:900"><div class="gamePopup"><div style="font-size:50px">🔐</div><h2>Enter PIN</h2><p id="pinDesc" style="opacity:.8">Enter your 4-digit PIN</p><input id="pinInput" class="pinInput" placeholder="••••" maxlength="4" inputmode="numeric" type="password"><div class="choiceRow"><div class="choiceBox choiceNo" onclick="closePin()">❌ Cancel</div><div class="choiceBox choiceYes" onclick="confirmPin()">✅ Confirm</div></div></div></div>
<div id="idOverlay" class="gameOverlay hidden" style="display:none;z-index:900"><div class="gamePopup"><div style="font-size:50px">🏷️</div><h2 id="idTitle">Enter Player ID</h2><p style="opacity:.8">Type digits only — INF- is added automatically</p><div class="idPrefix"><b>INF-</b><input id="idInput" placeholder="12345678" inputmode="numeric" maxlength="8" style="font-size:22px;text-align:center;letter-spacing:4px"></div><div class="choiceRow"><div class="choiceBox choiceNo" onclick="closeIdPopup()">❌ Cancel</div><div class="choiceBox choiceYes" onclick="confirmIdPopup()">✅ Confirm</div></div></div></div>
<div id="challengeOverlay" class="gameOverlay hidden" style="display:none;z-index:800"><div class="gamePopup" style="border-color:#00e5ff"><div style="font-size:50px">🎮</div><h2>CHALLENGE REQUEST</h2><p id="challengeText"></p><div class="choiceRow"><div class="choiceBox choiceNo" onclick="respondChallenge(false)">❌<br>No</div><div class="choiceBox choiceYes" onclick="respondChallenge(true)">✅<br>Yes</div></div><p style="font-size:12px;opacity:.7">Auto closes in 5 seconds...</p><div class="warnBar"><div class="warnBarFill"></div></div></div></div>
<div id="page-welcome" class="gameOverlay hidden" style="display:none;z-index:950"><div class="gamePopup"><div style="font-size:56px">👑</div><h2>Do you already have an account?</h2><p>Yes = Login • No = Register</p><div class="choiceRow"><div class="choiceBox choiceNo" onclick="welcomeChoice('no')">❌<br>No</div><div class="choiceBox choiceYes" onclick="welcomeChoice('yes')">✅<br>Yes</div></div></div></div>
<div id="page-home" class="center"><div style="font-size:26px">✨ 💖 ⭐ 🌟 💫</div><div class="crownBig">👑</div><h1 class="cursive" style="font-size:68px;margin:5px">Infinity Bot</h1><p style="letter-spacing:3px;font-weight:900">DOMINIC MASTIRIA</p><p>Riddles • Bible Fight • Sci-Fi • WhatsApp</p><button class="enterBtn" id="enterBtn" onclick="enterClicked()">Enter</button><p style="font-size:12px;opacity:.7;margin-top:12px">Press ENTER to Continue</p></div>
<div id="page-register" class="hidden" style="max-width:520px;margin:0 auto;padding:20px 14px"><div class="card" style="text-align:center"><div style="font-size:60px">👑</div><h1 class="cursive" style="font-size:48px;margin:5px">Register</h1><p id="regSub">Create your Infinity account 👑</p><div id="registerForm"><label style="text-align:left;display:block">Your Name:</label><input id="regName" placeholder="Your Name" maxlength="20"><label style="text-align:left;display:block">4-Digit Password:</label><input id="regPass" placeholder="••••" maxlength="4" inputmode="numeric" type="password"><p style="font-size:12px;color:#ffd700">⚠️ Do NOT use 1234 or 0000</p><button class="btn" onclick="doRegister()">📝 REGISTER</button><p style="font-size:13px;opacity:.8">Already have an account? <b style="color:#ffd700;cursor:pointer" onclick="showLogin()">Click here to Login</b></p></div><div id="loginForm" class="hidden"><label style="text-align:left;display:block">Your Name:</label><input id="loginName" placeholder="Your Name"><label style="text-align:left;display:block">4-Digit Password:</label><input id="loginPass" placeholder="••••" maxlength="4" inputmode="numeric" type="password"><button class="btn" onclick="doLogin()">🔓 LOGIN</button><p style="font-size:13px;opacity:.8">New here? <b style="color:#ffd700;cursor:pointer" onclick="showRegister()">Click here to Register</b></p></div></div></div>
<div id="page-dash" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div style="text-align:center"><h2 class="cursive" style="font-size:44px;margin:10px 0" id="welcomeText">Welcome, Player 👑</h2><span style="display:inline-block;padding:5px 10px;border-radius:20px;background:rgba(0,0,0,.5);border:1px solid #ffd700;font-size:12px">⭐ Rank: <b id="myRank">#-</b></span> <span style="display:inline-block;padding:5px 10px;border-radius:20px;background:rgba(0,0,0,.5);border:1px solid #ffd700;font-size:12px">🎯 <b id="myStage">Beginner</b></span></div><div class="grid"><div class="box" onclick="openRiddles()"><span>🧩</span><b>RIDDLES</b><br><small>5 Types</small></div><div class="box" onclick="openBible()"><span>📖</span><b>BIBLE FIGHT</b><br><small>Old + New + Stories</small></div><div class="box" onclick="openSciFi()"><span>🚀</span><b>SCI-FI</b><br><small>11 Games</small></div><div class="box" onclick="openMessages()"><span>💚</span><b>WHATSAPP</b><br><small>Chat • Call • Voice</small></div></div><div class="card"><h3 style="text-align:center;margin:0">🏆 TOP 5 🏆</h3><div id="leaderList">Loading...</div><button class="btn2" onclick="openFullLeader()">👀 View Full Leaderboard</button></div></div>
<div id="page-leader" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h3 style="text-align:center;margin:0">🏆 LEADERBOARD 🏆</h3><div class="tabRow" style="margin:12px 0"><div class="tabBox" id="tabGold" onclick="setLeaderMode('gold')">🪙<br>Gold</div><div class="tabBox" id="tabGems" onclick="setLeaderMode('gems')">💎<br>Germ</div><div class="tabBox" id="tabRank" onclick="setLeaderMode('rank')">⭐<br>Rank</div><div class="tabBox active" id="tabPvp" onclick="setLeaderMode('pvp')">⚔️<br>PvP</div></div><p id="leaderModeText" style="text-align:center;font-size:12px;opacity:.8">Ranked by Wins - Losses</p><div id="fullLeaderList">Loading...</div></div></div>
<div id="page-game" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 id="gameTitle" style="text-align:center">Game</h2><div id="gameBody"></div></div></div>
<div id="page-coming" class="hidden" style="max-width:520px;margin:0 auto;padding:40px 20px 90px;text-align:center"><div style="font-size:80px">🚀</div><h1 class="cursive" style="font-size:54px">Coming Soon</h1><h2>SCI-FI</h2><p>Launching on<br><b>25th December 2026</b></p><div style="font-size:60px;font-weight:900;color:#ffd700" id="countDown">5</div></div>
<div id="page-bank" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">🧑‍💻 BANK</h2><div class="walletCard"><div>🏦 BANK PROFILE</div><div style="font-size:18px;font-weight:900" id="bankIDShow">Bank INF-0000000000</div><div style="font-size:22px;margin-top:8px">🪙 Bank Gold: <b id="bankGold">0</b></div><div>💎 Bank Germ: <b id="bankGems">0</b></div><div style="margin-top:8px">Wallet — 🪙 <span id="walletGold">0</span> | 💎 <span id="walletGems">0</span></div></div><div class="grid" style="margin-top:14px"><div class="bigBankBox" onclick="openSendPage()"><span style="font-size:36px">💸</span><br><b>Send Gold</b></div><div class="bigBankBox" onclick="openWithdrawPage()"><span style="font-size:36px">🏧</span><br><b>Withdraw</b></div><div class="bigBankBox" onclick="openDepositPage()"><span style="font-size:36px">💰</span><br><b>Deposit</b></div><div class="bigBankBox" onclick="openMyProfile()"><span style="font-size:36px">👤</span><br><b>Bank</b></div></div><div class="bigBankBox" style="margin-top:14px" onclick="openExchangePage()"><span style="font-size:36px">🔄</span><br><b>Exchange</b><br><small>100 Gold = 1 Germ</small></div></div></div>
<div id="page-send" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">💸 SEND GOLD</h2><div class="walletCard"><div>Your Wallet</div><div>🪙 <b id="sendPageGold">0</b> | 💎 <b id="sendPageGems">0</b></div><div>Your ID: <b id="sendPageMyID">INF-00000000</b></div></div><label>Receiver ID:</label><div class="idPrefix"><b>INF-</b><input id="sendDigits" placeholder="12345678" inputmode="numeric" maxlength="8"></div><label>Amount:</label><input id="sendAmt" type="number" placeholder="Amount"><button class="btn" onclick="doSend()">➤ SEND NOW</button><p style="font-size:12px;opacity:.8">Fee 5% to Server Economy</p></div></div>
<div id="page-withdraw" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">🏧 WITHDRAW</h2><div class="walletCard"><div>🏦 Bank: 🪙 <b id="wdBankGold">0</b> | 💎 <b id="wdBankGems">0</b></div><div>Wallet: 🪙 <b id="wdWalletGold">0</b> | 💎 <b id="wdWalletGems">0</b></div><div>Bank ID: <b id="wdBankID">Bank INF-</b></div></div><label>Amount:</label><input id="withdrawAmt" type="number" placeholder="Amount"><select id="withdrawCur" style="width:100%;padding:14px;border-radius:14px"><option>Gold</option><option>Gems</option></select><button class="btn" onclick="doWithdraw()">🏧 WITHDRAW NOW</button></div></div>
<div id="page-deposit" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">💰 DEPOSIT</h2><div class="walletCard"><div>Wallet: 🪙 <b id="depWalletGold">0</b> | 💎 <b id="depWalletGems">0</b></div><div>🏦 Bank: 🪙 <b id="depBankGold">0</b> | 💎 <b id="depBankGems">0</b></div><div>Bank ID: <b id="depBankID">Bank INF-</b></div></div><label>Amount:</label><input id="depositAmt" type="number" placeholder="Amount"><select id="depositCur" style="width:100%;padding:14px;border-radius:14px"><option>Gold</option><option>Gems</option></select><button class="btn" onclick="doDeposit()">💰 DEPOSIT NOW</button></div></div>
<div id="page-exchange" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">🔄 EXCHANGE</h2><div class="walletCard"><div>Wallet: 🪙 <b id="exWalletGold">0</b> | 💎 <b id="exWalletGems">0</b></div></div><div class="bigBankBox" onclick="openExchange('gold_to_gem')"><b>Gold &gt;&gt;&gt;&gt; Germ</b><br><small>100 Gold = 1 Germ</small></div><div class="bigBankBox" style="margin-top:10px" onclick="openExchange('gem_to_gold')"><b>Germ &gt;&gt;&gt;&gt; Gold</b><br><small>1 Germ = 100 Gold</small></div><div id="exchangeForm" style="margin-top:12px"></div></div></div>
<div id="page-profile" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card" style="text-align:center"><div style="font-size:70px">👤</div><h2 id="profName">Player</h2><p style="color:#ffd700" id="profIDShow">ID:INF-00000000</p><p style="color:#ffd700" id="profBankID">Bank INF-0000000000</p><p>⭐ Rank: <b id="profRank">#-</b></p><p>🏆 Wins: <b id="profWins">0</b> | ❌ Losses: <b id="profLoss">0</b></p><p>🎯 Stage: <b id="profStage">Beginner</b></p><p>🪙 Gold: <b id="profGold">0</b> | 💎 Germ: <b id="profGems">0</b></p><p>🏦 Bank: 🪙 <b id="profBankGold">0</b> | 💎 <b id="profBankGems">0</b></p></div><div class="card"><h3>🎒 INVENTORY — My Items</h3><div id="profInventory">No items yet</div></div><div class="card"><h3>💰 REQUEST MONEY FROM SERVER</h3><p style="font-size:12px;opacity:.8">Max: 100,000,000 Gold / 100,000 Germ<br>Type: I want money / I need money — Dominic will set amount if empty</p><input id="reqMsg" placeholder="I want money / I need money..."><input id="reqAmt" type="number" placeholder="Amount (optional)"><select id="reqCur" style="width:100%;padding:14px;border-radius:14px"><option>Gold</option><option>Gems</option></select><button class="btn" onclick="sendMoneyRequest()">📩 SEND REQUEST TO DOMINIC</button></div></div>
<div id="page-other" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card" style="text-align:center"><div style="font-size:70px">👤</div><h2 id="otherName">Player</h2><div id="otherClassified" class="hidden"><div style="font-size:40px">⚠️</div><h3>⚠️ Warning ⚠️</h3><p>You can't view this profile 😉<br>Sorry please level up</p></div><div id="otherNormal"><p>⭐ Rank: <b id="otherRank">#-</b></p><p><b id="otherWins">0</b> Win | <b id="otherLoss">0</b> Lose</p><div id="otherActions"></div></div></div></div>
<div id="page-notifs" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">✉️ NOTIFICATIONS</h2><div id="notifList">No notifications</div></div></div>
<div id="page-menu" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">🎮 MENU - 11 GAMES</h2><div id="menuGamesList"></div></div></div>
<div id="page-economy" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><div style="display:flex;justify-content:space-between;align-items:center"><h2 style="margin:0">💰 SERVER ECONOMY</h2><button id="emergencyBtn" class="btn" style="width:auto;background:#ff2222;color:#fff;padding:10px 14px" onclick="doEmergency()">🚨 Emergency</button></div><p style="font-size:11px;opacity:.7">Emergency Top-Right — Only if NEGATIVE. Backup 10 Billion. Gives 500 Billion. If not enough → Sleep Mode.</p><div class="grid"><div class="walletCard"><div>Server Gold</div><div style="font-size:22px;font-weight:900" id="ecoGold">0</div></div><div class="walletCard"><div>Server Germ</div><div style="font-size:22px;font-weight:900" id="ecoGems">0</div></div><div class="bigBankBox"><div>🏦 From Banks</div><b id="ecoBank">0</b></div><div class="bigBankBox"><div>💸 From Fees</div><b id="ecoFees">0</b></div><div class="bigBankBox"><div>🎰 From Lottery</div><b id="ecoLottery">0</b></div><div class="bigBankBox"><div>🛟 Backup</div><b id="ecoBackup">0</b></div></div><h3>📈 CRYPTO — Economy Since Day 1</h3><p style="font-size:12px;opacity:.8">Server earns → line UP 📈. Dominic gives without checking → line DOWN 📉.</p><canvas id="ecoChart" width="480" height="160" style="width:100%;background:#000;border:2px solid #00ffaa;border-radius:14px"></canvas><h3>💰 MONEY REQUESTS</h3><div id="ecoRequests">No requests</div></div></div>
<div id="page-lottery" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">🎰 LOTTERY</h2><p style="text-align:center">50% Win / 50% Lose<br>Win = 2x bet (from Server Economy, can go negative)<br>Lose = bet to Server Economy</p><label>Your Bet:</label><input id="lotBet" type="number" placeholder="e.g. 1000"><select id="lotCur" style="width:100%;padding:14px;border-radius:14px"><option>Gold</option><option>Gems</option></select><button class="btn" onclick="playLottery()">🎰 SPIN LOTTERY</button><div id="lotResult" style="text-align:center;margin-top:12px"></div></div></div>
<div id="page-update" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">🔄 UPDATE SERVER - DOMINIC ONLY</h2><div class="spacexScene"><p>🚀 SPACEX UPDATE CONSOLE</p><div class="scifiCode">> CHECKING UPDATE...
> DOWNLOADING CHRISTMAS UPDATE v13...
> APPLYING 1000 SHOP PRODUCTS... OK
> APPLYING 11 GAMES... OK
> SYNCING PLAYERS... NO DATA LOST
> READY - Earning</div><div style="display:flex;justify-content:space-between;align-items:center;margin-top:16px;background:rgba(255,255,255,.1);padding:14px;border-radius:16px"><div><div style="font-size:20px;font-weight:900">Earning</div><div style="font-size:12px;opacity:.8" id="earningDesc">ON</div></div><div class="switch" id="earningSwitch" onclick="toggleEarningSwitch()"><div class="switchKnob"></div></div></div></div><button class="btn" onclick="doServerUpdate()">🚀 APPLY UPDATE NOW</button></div></div>
<div id="page-server-info" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">🖥️ SERVER INFO - DOMINIC ONLY</h2><div class="spacexScene"><p>🚀 SPACEX // INFINITY SERVER</p><div>> PLAYERS: <span id="serverPlayers">0</span></div><div>> EARNING: <span id="serverEarningText">ON</span></div></div><h3>📜 Reviews</h3><div id="serverReviewsList">Loading...</div></div></div>
<div id="page-review" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center" id="reviewTitle">⭐ Review</h2><textarea id="reviewText" style="width:100%;height:140px;padding:14px;border-radius:14px;margin:12px 0;font-size:16px" placeholder="Type your review or request..."></textarea><button class="btn" onclick="submitReview()">📩 SEND</button></div></div>
<div id="page-challenge" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">🎮 CHALLENGE DASHBOARD</h2><p id="challengeDashText" style="text-align:center"></p><p style="text-align:center">Pick what to challenge:</p><div class="grid"><div class="box" onclick="startChallengeGame('Galaxy Shooter')"><span>🌌</span><b>Galaxy Shooter</b></div><div class="box" onclick="startChallengeGame('Riddles')"><span>🧩</span><b>Riddles</b></div><div class="box" onclick="startChallengeGame('Bible Fight')"><span>📖</span><b>Bible Fight</b></div><div class="box" onclick="startChallengeGame('Decoding')"><span>💻</span><b>Decoding</b></div></div><button class="btn2" onclick="declineChallengeDash()">❌ Decline / Close</button></div></div>
<div id="page-messages" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h1 style="text-align:center;margin:0">💚 WhatsApp</h1><p style="text-align:center;opacity:.8">Friends • Chat • Voice Call • Voice Notes</p><div style="display:flex;gap:8px"><div class="idPrefix" style="flex:1"><b>INF-</b><input id="addFriendDigits" placeholder="Add friend ID" inputmode="numeric" maxlength="8"></div><button class="btn" style="width:auto;padding:12px 18px" onclick="addFriendById()">➕ Add</button></div><div id="chatFriendList"></div></div></div>
<div id="page-chat" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">💬 <span id="chatWith">Friend</span></h2><div style="display:flex;gap:8px;justify-content:center;margin:10px 0"><button class="btn2" style="width:auto" onclick="startVoiceCall()">📞 Voice Call</button><button class="btn2" style="width:auto" onclick="toggleVoiceNote()">🎙️ Voice Note</button></div><div id="callBanner" class="hidden" style="background:#00cc44;color:#000;padding:12px;border-radius:14px;text-align:center;font-weight:900">📞 Calling... <span id="callTimer">00:00</span> <button onclick="endVoiceCall()" style="background:#ff2222;color:#fff;border:none;padding:8px 14px;border-radius:12px;font-weight:900">End Call</button></div><div id="chatBox" style="background:#1a1a2e;border-radius:20px;padding:12px;min-height:260px;max-height:360px;overflow-y:auto"></div><div style="display:flex;gap:8px;margin-top:10px"><input id="msgInput" placeholder="Message..." style="flex:1"><button class="btn" style="width:70px" onclick="sendMsg()">➤</button></div></div></div>
<div id="backFab" style="position:fixed;left:16px;bottom:16px;width:58px;height:58px;border-radius:50%;background:#1a1a2e;display:none;align-items:center;justify-content:center;font-size:28px;color:#ffd700;border:3px solid #ffd700;cursor:pointer;z-index:60">←</div>
<div id="msgFab" style="position:fixed;right:16px;bottom:16px;width:62px;height:62px;border-radius:50%;background:linear-gradient(135deg,#ff006e,#ffd700,#00e5ff);display:none;align-items:center;justify-content:center;font-size:30px;border:3px solid #fff;cursor:pointer;z-index:60">💬</div>
<div id="bottomNav" class="bottomNav hidden"><div onclick="goDash()">🏡<small>Home</small></div><div onclick="openFullLeader()">🏆<small>Leader</small></div><div onclick="openBank()">🧑‍💻<small>Bank</small></div><div onclick="openNotifs()">✉️<small>Notify</small></div></div>
<script>
var user=null; try{user=JSON.parse(localStorage.getItem('inf_user')||'null')}catch(e){}
var wins=0,losses=0,myGold=0,myGems=0,myPlayerID='',myBankID='';
try{wins=parseInt(localStorage.getItem('inf_wins')||'0')||0;losses=parseInt(localStorage.getItem('inf_loss')||'0')||0;myGold=parseInt(localStorage.getItem('inf_gold')||'0')||0;myGems=parseInt(localStorage.getItem('inf_gems')||'0')||0;myPlayerID=localStorage.getItem('inf_player_id')||'';myBankID=localStorage.getItem('inf_bank_id')||''}catch(e){}
var stageIdx=0,loggedIn=false,currentPage='page-home',seenQs=[]; try{seenQs=JSON.parse(localStorage.getItem('inf_seen')||'[]')}catch(e){seenQs=[]}
var currentChallengeId=null,challengeTimer=null,reviewType='review',pinCallback=null,leaderMode='pvp',idCallback=null,chatWithName='',callInterval=null,callSecs=0,mediaRecorder=null;
function isDominic(){return user&&user.name&&user.name.toLowerCase()==='dominic'&&user.password==='2164'}
var soundOn=true, audioCtx=null;
function beep(f,d){ if(!soundOn) return; try{ if(!audioCtx) audioCtx=new (window.AudioContext||window.webkitAudioContext)(); var o=audioCtx.createOscillator(), g=audioCtx.createGain(); o.connect(g); g.connect(audioCtx.destination); o.frequency.value=f||880; g.gain.value=0.15; o.start(); setTimeout(function(){o.stop()},d||150);}catch(e){} }
function playClick(){ beep(880,120); } function playWin(){ beep(880,120); setTimeout(function(){beep(1100,150)},150); setTimeout(function(){beep(1320,200)},300); } function playLose(){ beep(200,300); }
var DASH_SOUND_URL="https://cdn.pixabay.com/audio/2025/06/12/audio_0ea789b238.mp3";
function playDashSound(){ try{ var a=new Audio(DASH_SOUND_URL); a.volume=0.8; var p=a.play(); if(p&&p.catch) p.catch(function(){ playWin(); }); }catch(e){ playWin(); } }
function specialWelcome(name,pw){ var n=(name||'').toLowerCase().trim(); if(n==="britney"||n==="kayula") return "Welcome MY Fiance 💖"; if(n==="blessing") return "Welcome Avatar ✨"; if(n==="lubuto") return "Welcome Desk Bender 🛠️"; if(n==="dominic"&&pw==="2164") return "Welcome INFINITY EMPEROR ♾"; return "Welcome, "+name+" 👑"; }
function updateCatTime(){ try{ var el=document.getElementById('catTime'); if(!el) return; var t=new Intl.DateTimeFormat('en-GB',{timeZone:'Africa/Lusaka',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false}).format(new Date()); el.textContent=t+' CAT'; }catch(e){ try{ var d=new Date(); el.textContent=String(d.getHours()).padStart(2,'0')+':'+String(d.getMinutes()).padStart(2,'0')+':'+String(d.getSeconds()).padStart(2,'0')+' CAT'; }catch(e2){} } }
updateCatTime(); setInterval(updateCatTime,1000);
function toast(m){var t=document.getElementById('toast'); if(!t) return; t.innerText=m; t.classList.remove('hidden'); setTimeout(function(){t.classList.add('hidden')},4500)}
function updateVisibility(){ var right=document.getElementById('topRight'), nav=document.getElementById('bottomNav'), back=document.getElementById('backFab'), msg=document.getElementById('msgFab'), tl=document.getElementById('topLeft'); if(tl) tl.classList.remove('hidden'); var isEnter=(currentPage==='page-home'||currentPage==='page-register'); var isDash=(currentPage==='page-dash'); if(isEnter){ if(right){right.classList.add('hidden'); right.style.display='none';} if(nav) nav.classList.add('hidden'); if(back) back.style.display='none'; if(msg) msg.style.display='none'; } else if(loggedIn&&isDash){ if(right){right.classList.remove('hidden'); right.style.display='flex';} if(nav) nav.classList.remove('hidden'); if(back) back.style.display='none'; if(msg) msg.style.display='flex'; } else if(loggedIn){ if(right){right.classList.add('hidden'); right.style.display='none';} if(nav) nav.classList.add('hidden'); if(back) back.style.display='flex'; if(msg) msg.style.display='flex'; } else { if(right){right.classList.add('hidden'); right.style.display='none';} if(nav) nav.classList.add('hidden'); if(back) back.style.display='none'; if(msg) msg.style.display='none'; } }
function showPage(id){ currentPage=id; ['page-home','page-register','page-dash','page-leader','page-game','page-coming','page-bank','page-send','page-withdraw','page-deposit','page-exchange','page-profile','page-other','page-notifs','page-menu','page-update','page-server-info','page-review','page-challenge','page-messages','page-chat','page-economy','page-lottery'].forEach(function(p){var el=document.getElementById(p); if(el) el.classList.add('hidden');}); var tg=document.getElementById(id); if(tg) tg.classList.remove('hidden'); window.scrollTo(0,0); updateVisibility(); }
function goDash(){ if(!loggedIn){ showPage('page-register'); return; } showPage('page-dash'); loadLeader(); }
function goBack(){ if(currentPage==='page-register') showPage('page-home'); else if(currentPage==='page-chat') showPage('page-messages'); else goDash(); }
function enterClicked(){ playClick(); goRegister(); }
function goRegister(){ showPage('page-register'); showRegister(); setTimeout(function(){ var ov=document.getElementById('page-welcome'); if(ov){ ov.classList.remove('hidden'); ov.style.display='flex'; beep(880,200); } },100); }
function welcomeChoice(c){ var ov=document.getElementById('page-welcome'); if(ov){ ov.classList.add('hidden'); ov.style.display='none'; } if(c==='yes') showLogin(); else showRegister(); }
function showRegister(){ var a=document.getElementById('registerForm'), b=document.getElementById('loginForm'); if(a) a.classList.remove('hidden'); if(b) b.classList.add('hidden'); }
function showLogin(){ var a=document.getElementById('registerForm'), b=document.getElementById('loginForm'); if(a) a.classList.add('hidden'); if(b) b.classList.remove('hidden'); }
function saveLocal(){ try{ localStorage.setItem('inf_user',JSON.stringify(user)); localStorage.setItem('inf_wins',wins); localStorage.setItem('inf_loss',losses); localStorage.setItem('inf_gold',myGold); localStorage.setItem('inf_gems',myGems); localStorage.setItem('inf_player_id',myPlayerID); localStorage.setItem('inf_bank_id',myBankID); localStorage.setItem('inf_seen',JSON.stringify(seenQs)); }catch(e){} }
function doRegister(){ var n=document.getElementById('regName').value.trim(); var pw=document.getElementById('regPass').value.trim(); if(!n){toast('Enter name');return} if(!pw||pw.length!==4||isNaN(pw)){toast('Password must be exactly 4 digits');return} if(pw==='1234'||pw==='0000'){toast('Password too easy');return} fetch('/api/player?name='+encodeURIComponent(n)).then(function(r){return r.json()}).then(function(d){ if(d&&d.found){ showLogin(); document.getElementById('loginName').value=n; toast('Account found! Please Login'); return; } user={name:n,password:pw}; wins=0; losses=0; myGold=0; myGems=0; seenQs=[]; saveLocal(); syncScore(); enterDashboard(specialWelcome(n,pw)); }); }
function doLogin(){ var n=document.getElementById('loginName').value.trim(); var pw=document.getElementById('loginPass').value.trim(); if(!n||!pw){toast('Enter name + password');return} fetch('/api/player?name='+encodeURIComponent(n)+'&password='+encodeURIComponent(pw)).then(function(r){return r.json()}).then(function(d){ if(d&&d.found&&d.password_ok!==false){ user={name:n,password:pw}; wins=d.wins||0; losses=d.losses||0; myGold=d.gold||0; myGems=d.gems||0; myPlayerID=d.player_id||''; myBankID=d.bank_id||''; seenQs=d.seen_qs||[]; saveLocal(); enterDashboard(specialWelcome(n,pw)); } else { toast('⚠️ Account not found / Wrong password'); } }); }
function enterDashboard(msg){ loggedIn=true; toast(msg); playDashSound(); showPage('page-dash'); document.getElementById('welcomeText').innerText=msg; loadLeader(); loadMyProfileData(); }
function syncScore(){ if(!user) return; fetch('/api/score',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:user.name,password:user.password,wins:wins,losses:losses,stage:stageIdx,gold:myGold,gems:myGems,seen_qs:seenQs})}).catch(function(){}); }
function loadMyProfileData(){ if(!user) return; fetch('/api/player?name='+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){ if(!d||!d.found) return; myPlayerID=d.player_id; myBankID=d.bank_id||myBankID; myGold=d.gold; myGems=d.gems; var e=function(id,v){var x=document.getElementById(id); if(x) x.innerText=v;}; e('myRank','#-'); e('myStage',d.rank||'Beginner'); e('bankGold',d.bank_gold||0); e('bankGems',d.bank_gems||0); e('bankIDShow',d.bank_id||myBankID); e('walletGold',d.gold); e('walletGems',d.gems); }); }
function loadLeader(){ fetch('/api/leaderboard?mode=pvp').then(function(r){return r.json()}).then(function(d){ var ps=d.players||[]; var html=''; ps.slice(0,5).forEach(function(p,i){ html+='<div class="leadRow" onclick="viewOtherPlayer(\''+p.name+'\')"><span>'+(i+1)+'. '+p.name+'</span><span>🏆 '+p.wins+'W • ❌ '+p.losses+'L</span></div>'; }); document.getElementById('leaderList').innerHTML=html||'No players yet'; }); }
function setLeaderMode(m){ leaderMode=m; ['gold','gems','rank','pvp'].forEach(function(x){ var el=document.getElementById('tab'+x.charAt(0).toUpperCase()+x.slice(1)); if(el) el.classList.remove('active'); }); var act=document.getElementById('tab'+m.charAt(0).toUpperCase()+m.slice(1)); if(act) act.classList.add('active'); openFullLeader(); }
function openFullLeader(){ showPage('page-leader'); fetch('/api/leaderboard?mode='+leaderMode).then(function(r){return r.json()}).then(function(d){ var ps=d.players||[]; var html=''; var label=leaderMode==='gold'?'Ranked by Total Gold':leaderMode==='gems'?'Ranked by Total Germ':leaderMode==='rank'?'Ranked by Rank Level':'Ranked by Wins - Losses'; document.getElementById('leaderModeText').innerText=label; ps.forEach(function(p,i){ var extra=leaderMode==='gold'?'🪙 '+p.gold+' Gold':leaderMode==='gems'?'💎 '+p.gems+' Germ':leaderMode==='rank'?'⭐ '+p.rank:'🏆 '+p.wins+'W • ❌ '+p.losses+'L'; html+='<div class="leadRow" onclick="viewOtherPlayer(\''+p.name+'\')"><span>'+(i+1)+'. '+p.name+'<br><small>'+p.player_id+'</small></span><span>'+extra+'</span></div>'; }); document.getElementById('fullLeaderList').innerHTML=html||'No players'; }); }
function viewOtherPlayer(name){ if(!user) return; fetch('/api/player?name='+encodeURIComponent(name)).then(function(r){return r.json()}).then(function(d){ if(!d||!d.found) return; showPage('page-other'); document.getElementById('otherName').innerText=d.name; if(d.classified){ document.getElementById('otherClassified').classList.remove('hidden'); document.getElementById('otherNormal').classList.add('hidden'); } else { document.getElementById('otherClassified').classList.add('hidden'); document.getElementById('otherNormal').classList.remove('hidden'); document.getElementById('otherRank').innerText=d.rank; document.getElementById('otherWins').innerText=d.wins; document.getElementById('otherLoss').innerText=d.losses; document.getElementById('otherActions').innerHTML='<button class="btn" onclick="tagPlayer(\''+d.player_id+'\')">🏷️ Challenge This Player</button><button class="btn2" onclick="openBankSendTo(\''+d.player_id+'\')">💸 Send Gold</button>'; } }); }
function openMyProfile(){ if(!loggedIn) return; showPage('page-profile'); fetch('/api/player?name='+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){ if(!d||!d.found) return; var e=function(id,v){var x=document.getElementById(id); if(x) x.innerText=v;}; e('profName',specialWelcome(d.name,user.password)); e('profIDShow','ID:'+d.player_id); e('profBankID',d.bank_id); e('profRank','#-'); e('profWins',d.wins); e('profLoss',d.losses); e('profStage',d.rank); e('profGold',d.gold); e('profGems',d.gems); e('profBankGold',d.bank_gold||0); e('profBankGems',d.bank_gems||0); var inv=d.items||[]; var ih=''; if(!inv.length) ih='<p>No items yet — buy in Shop 🛍️</p>'; else inv.forEach(function(it){ ih+='<div style="padding:10px;background:rgba(0,0,0,.4);border-radius:12px;margin:6px 0">🎒 '+it+'</div>'; }); document.getElementById('profInventory').innerHTML=ih; }); }
function openBank(){ if(!loggedIn) return; showPage('page-bank'); loadMyProfileData(); }
function openBankSendTo(id){ openSendPage(); var el=document.getElementById('sendDigits'); if(el) el.value=id.replace('INF-',''); }
function loadBankInfo(cb){ fetch('/api/player?name='+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){ if(!d||!d.found) return; myGold=d.gold; myGems=d.gems; if(cb) cb(d); }); }
function openSendPage(){ showPage('page-send'); loadBankInfo(function(d){ document.getElementById('sendPageGold').innerText=d.gold; document.getElementById('sendPageGems').innerText=d.gems; document.getElementById('sendPageMyID').innerText=d.player_id; }); }
function openWithdrawPage(){ showPage('page-withdraw'); loadBankInfo(function(d){ document.getElementById('wdBankGold').innerText=d.bank_gold||0; document.getElementById('wdBankGems').innerText=d.bank_gems||0; document.getElementById('wdWalletGold').innerText=d.gold; document.getElementById('wdWalletGems').innerText=d.gems; document.getElementById('wdBankID').innerText=d.bank_id; }); }
function openDepositPage(){ showPage('page-deposit'); loadBankInfo(function(d){ document.getElementById('depWalletGold').innerText=d.gold; document.getElementById('depWalletGems').innerText=d.gems; document.getElementById('depBankGold').innerText=d.bank_gold||0; document.getElementById('depBankGems').innerText=d.bank_gems||0; document.getElementById('depBankID').innerText=d.bank_id; }); }
function openExchangePage(){ showPage('page-exchange'); loadBankInfo(function(d){ document.getElementById('exWalletGold').innerText=d.gold; document.getElementById('exWalletGems').innerText=d.gems; }); document.getElementById('exchangeForm').innerHTML=''; }
function openExchange(dir){ var h=''; if(dir==='gold_to_gem'){ h='<h3>Gold &gt;&gt;&gt;&gt; Germ</h3><p>100 Gold = 1 Germ</p><label>Enter amount of Gold:</label><input id="exAmt" type="number" placeholder="e.g. 500"><button class="btn" onclick="doExchange(\'gold_to_gem\')">Confirm Exchange</button>'; } else { h='<h3>Germ &gt;&gt;&gt;&gt; Gold</h3><p>1 Germ = 100 Gold</p><label>Enter amount of Germ:</label><input id="exAmt" type="number" placeholder="e.g. 5"><button class="btn" onclick="doExchange(\'gem_to_gold\')">Confirm Exchange</button>'; } document.getElementById('exchangeForm').innerHTML=h; }
function doSend(){ var digits=document.getElementById('sendDigits').value.replace(/[^0-9]/g,''); var amt=parseInt(document.getElementById('sendAmt').value||'0'); if(digits.length<8||!amt){ toast('Enter 8-digit ID + Amount'); return; } openPin('Enter PIN to send '+amt+' Gold',function(pin){ fetch('/api/transfer',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sender:user.name,pin:pin,receiver_id:'INF-'+digits,amount:amt,currency:'Gold'})}).then(function(r){return r.json()}).then(function(d){ if(d.error){ toast('⚠️ '+d.error); return; } myGold=d.sender_gold; saveLocal(); toast('✅ Sent!'); playWin(); openNotifs(); }); }); }
function doWithdraw(){ var amt=parseInt(document.getElementById('withdrawAmt').value||'0'); var cur=document.getElementById('withdrawCur').value; if(!amt){ toast('Enter amount'); return; } openPin('Enter PIN to withdraw '+amt+' '+cur,function(pin){ fetch('/api/bank_action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:user.name,pin:pin,amount:amt,action:'withdraw',currency:cur})}).then(function(r){return r.json()}).then(function(d){ if(d.error){ toast('⚠️ '+d.error); return; } myGold=d.gold; myGems=d.gems; saveLocal(); loadMyProfileData(); toast('✅ Withdrawn!'); openNotifs(); }); }); }
function doDeposit(){ var amt=parseInt(document.getElementById('depositAmt').value||'0'); var cur=document.getElementById('depositCur').value; if(!amt){ toast('Enter amount'); return; } openPin('Enter PIN to deposit '+amt+' '+cur,function(pin){ fetch('/api/bank_action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:user.name,pin:pin,amount:amt,action:'deposit',currency:cur})}).then(function(r){return r.json()}).then(function(d){ if(d.error){ toast('⚠️ '+d.error); return; } myGold=d.gold; myGems=d.gems; saveLocal(); loadMyProfileData(); toast('✅ Deposited!'); openNotifs(); }); }); }
function doExchange(dir){ var amt=parseInt(document.getElementById('exAmt').value||'0'); if(!amt){ toast('Enter amount'); return; } openPin('Enter PIN to confirm Exchange',function(pin){ fetch('/api/exchange',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:user.name,pin:pin,amount:amt,direction:dir})}).then(function(r){return r.json()}).then(function(d){ if(d.error){ toast('⚠️ '+d.error); return; } myGold=d.gold; myGems=d.gems; saveLocal(); toast('✅ Exchange done!'); loadMyProfileData(); }); }); }
function openNotifs(){ if(!loggedIn) return; showPage('page-notifs'); fetch('/api/player?name='+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){ var ns=(d&&d.notifs)||[]; var html=''; ns.slice().reverse().forEach(function(n){ html+='<div style="padding:12px;background:rgba(0,0,0,.4);border-radius:14px;margin:8px 0">'+n.text+'<br><small style="opacity:.7">'+(n.time||'')+'</small></div>'; }); document.getElementById('notifList').innerHTML=html||'No notifications'; var b=document.getElementById('notifBadge'); if(b) b.classList.add('hidden'); }); }
function openMenuPage(){ showPage('page-menu'); renderMenuGames(); }
function openReviewRequest(t){ reviewType=t; document.getElementById('reviewTitle').innerText=t==='request'?'📩 Request':'⭐ Review'; showPage('page-review'); }
function submitReview(){ var txt=document.getElementById('reviewText').value.trim(); if(!txt){ toast('Type something'); return; } fetch('/api/review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:user?user.name:'Guest',type:reviewType,text:txt})}).then(function(){ toast('✅ Sent!'); document.getElementById('reviewText').value=''; goDash(); }); }
function openUpdatePage(){ if(!isDominic()){ toast('🔒 Only Dominic'); return; } showPage('page-update'); refreshEarningSwitch(); }
function refreshEarningSwitch(){ fetch('/api/earning_status').then(function(r){return r.json()}).then(function(d){ var sw=document.getElementById('earningSwitch'); var desc=document.getElementById('earningDesc'); if(d.earning_on){ sw.classList.remove('off'); desc.innerText='ON'; } else { sw.classList.add('off'); desc.innerText='OFF - RED'; } }); }
function toggleEarningSwitch(){ if(!isDominic()) return; fetch('/api/toggle_earning',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:user.name,password:user.password})}).then(function(r){return r.json()}).then(function(d){ refreshEarningSwitch(); toast(d.earning_on?'✅ Earning ON':'🛑 Earning OFF'); }); }
function doServerUpdate(){ if(!isDominic()) return; toast('🚀 Applying Update...'); setTimeout(function(){ refreshEarningSwitch(); toast('✅ Server Updated!'); },1500); }
function openServerInfo(){ if(!isDominic()){ toast('🔒 ADMIN ONLY'); return; } showPage('page-server-info'); fetch('/api/server_info?name=Dominic&password=2164').then(function(r){return r.json()}).then(function(d){ document.getElementById('serverPlayers').innerText=d.players||0; document.getElementById('serverEarningText').innerText=d.earning_on?'ON':'OFF'; var html=''; (d.reviews||[]).forEach(function(rv){ html+='<div style="padding:10px;border-bottom:1px solid #00ffaa">['+rv.type+'] '+rv.name+': '+rv.text+'</div>'; }); document.getElementById('serverReviewsList').innerHTML=html||'No reviews'; }); }
function fmtPrice(n){ if(n>=1000000000000) return (n/1000000000000)+' Trillion Gold'; if(n>=1000000000) return (n/1000000000)+' Billion Gold'; if(n>=1000000) return (n/1000000)+' Million Gold'; if(n>=1000) return (n/1000)+'K Gold'; return n+' Gold'; }
var SHOP_ICONS=["👑","⚔️","🛡️","💎","🔥","🚀","🏆","🎯","💰","🪙","🌟","⚡","🎮","🧩","📖","🚗","🏠","👓","🎧","⌚","📱","💻","🎸","⚽","🏀","🍕","🍔","☕","🌹","🐉"];
function build1000Shop(){
  var items=[]; var prices=[50,100,300,500,700,1000,5000,10000,50000,100000,500000,1000000,5000000,100000000,1000000000,1000000000000];
  for(var i=1;i<=1000;i++){ var p=prices[i%prices.length]; var extra=(i%7===0)?(i*10):0; items.push({name:'Infinity Item '+i,icon:SHOP_ICONS[i%SHOP_ICONS.length],price:p+extra,purpose:'Boost your rank + style. Item #'+i}); }
  return items;
}
var SHOP_ITEMS=build1000Shop();
function openShop(from){ showPage('page-game'); document.getElementById('gameTitle').innerText='🛍️ INFINITY SHOP — 1000 PRODUCTS'; var html='<p style="text-align:center">🪙 Gold: <b>'+myGold+'</b> | 💎 Germ: <b>'+myGems+'</b></p><p style="text-align:center;font-size:12px">Left / Right / Left / Right — 2 per row</p><div class="shopGrid">'; SHOP_ITEMS.forEach(function(it,idx){ html+='<div class="shopBox" onclick="buyItem('+idx+')"><span class="ic">'+it.icon+'</span><span class="nm">'+it.name+'</span><span class="pr">'+fmtPrice(it.price)+'</span><span class="pp">'+it.purpose+'</span><button class="btn" style="margin-top:8px;padding:8px">Buy</button></div>'; }); html+='</div>'; document.getElementById('gameBody').innerHTML=html; }
function buyItem(idx){ var it=SHOP_ITEMS[idx]; if(!it) return; openPin('Enter PIN to buy '+it.name+' for '+fmtPrice(it.price),function(pin){ fetch('/api/buy_item',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:user.name,pin:pin,item:it.name,price:it.price})}).then(function(r){return r.json()}).then(function(d){ if(d.error){ toast('⚠️ '+d.error); return; } myGold=d.gold; saveLocal(); toast('✅ Bought '+it.name); playWin(); loadMyProfileData(); }); }); }
function sendMoneyRequest(){ var msg=document.getElementById('reqMsg').value.trim(); var amt=document.getElementById('reqAmt').value; var cur=document.getElementById('reqCur').value; fetch('/api/request_money',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:user.name,amount:amt?parseInt(amt):null,currency:cur,message:msg||'I want money'})}).then(function(r){return r.json()}).then(function(d){ if(d.error){ toast('⚠️ '+d.error); return; } toast('✅ Request sent to Dominic!'); }); }
function openEconomy(){ if(!isDominic()){ toast('🔒 DOMINIC ONLY'); return; } showPage('page-economy'); fetch('/api/economy?name=Dominic&password=2164').then(function(r){return r.json()}).then(function(d){ var e=d.economy; document.getElementById('ecoGold').innerText=e.gold; document.getElementById('ecoGems').innerText=e.gems; document.getElementById('ecoBank').innerText=e.bank_total; document.getElementById('ecoFees').innerText=e.fees; document.getElementById('ecoLottery').innerText=e.lottery; document.getElementById('ecoBackup').innerText=e.backup; var html=''; (d.requests||[]).forEach(function(rq){ html+='<div style="padding:12px;background:rgba(0,0,0,.4);border-radius:14px;margin:8px 0"><b>'+rq.from+'</b> ('+rq.from_id+') wants <b>'+(rq.amount||'— no amount —')+' '+rq.currency+'</b><br><small>'+(rq.message||'')+'</small><br><input id="ap-'+rq.id+'" type="number" placeholder="Dominic sets amount"><button class="btn" onclick="approveRequest(\''+rq.id+'\',\''+rq.currency+'\')">✅ Send</button></div>'; }); document.getElementById('ecoRequests').innerHTML=html||'No requests'; var cv=document.getElementById('ecoChart'); if(cv){ var ctx=cv.getContext('2d'); var h=e.history||[e.gold]; ctx.clearRect(0,0,480,160); ctx.beginPath(); ctx.strokeStyle='#00ffaa'; ctx.lineWidth=2; var mn=Math.min.apply(null,h), mx=Math.max.apply(null,h); if(mx===mn) mx=mn+1; h.forEach(function(v,i){ var x=(i/(Math.max(1,h.length-1)))*480; var y=150-((v-mn)/(mx-mn))*140; if(i===0) ctx.moveTo(x,y); else ctx.lineTo(x,y); }); ctx.stroke(); } }); }
function approveRequest(rid,cur){ var amt=parseInt(document.getElementById('ap-'+rid).value||'0'); if(!amt){ toast('Enter amount Dominic'); return; } openPin('Enter Dominic PIN 2164 to send '+amt,function(pin){ fetch('/api/request_approve',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({admin:'Dominic',pin:pin,request_id:rid,amount:amt,currency:cur})}).then(function(r){return r.json()}).then(function(d){ if(d.error){ toast('⚠️ '+d.error); return; } toast('✅ Sent!'); openEconomy(); }); }); }
function doEmergency(){ openPin('Enter Dominic PIN for Emergency',function(pin){ fetch('/api/emergency',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:'Dominic',pin:pin})}).then(function(r){return r.json()}).then(function(d){ if(d.error){ toast('⚠️ '+d.error+' — Sleep Mode if backup low'); return; } toast('🚨 Emergency: +500 Billion given!'); openEconomy(); }); }); }
function openLottery(){ showPage('page-lottery'); }
function playLottery(){ var bet=parseInt(document.getElementById('lotBet').value||'0'); var cur=document.getElementById('lotCur').value; if(!bet){ toast('Enter bet'); return; } openPin('Enter PIN to spin Lottery '+bet+' '+cur,function(pin){ fetch('/api/lottery',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:user.name,pin:pin,bet:bet,currency:cur})}).then(function(r){return r.json()}).then(function(d){ if(d.error){ toast('⚠️ '+d.error); return; } myGold=d.gold; myGems=d.gems; saveLocal(); if(d.result.win){ document.getElementById('lotResult').innerHTML='<h2>🎉 YOU WON '+d.result.prize+' '+cur+'!</h2>'; playWin(); } else { document.getElementById('lotResult').innerHTML='<h2>😢 You lost '+d.result.lost+' '+cur+' — went to Server Economy</h2>'; playLose(); } loadMyProfileData(); }); }); }
function P(s){ var p=s.split('|'); return {q:p[0],a:p[1]}; }
var BANK_RIDDLE_GENERAL=["What has keys but cannot open locks?|A piano","What has a face and two hands but no arms?|A clock","What gets wetter the more it dries?|A towel","What has a neck but no head?|A bottle","What runs but never walks?|Water","What has many teeth but cannot bite?|A comb","What can you catch but never throw?|A cold","What has a bed but never sleeps?|A river","What has one eye but cannot see?|A needle","I speak without a mouth, hear without ears, what am I?|An echo","What has 13 hearts but no organs?|A deck of cards","What can fill a room without taking space?|Light","What gets bigger the more you take away?|A hole","What is always coming but never arrives?|Tomorrow"].map(P);
var BANK_RIDDLE_LOVE=["What grows stronger when shared?|Love","What beats but is not a drum?|Heart","What do you give without losing?|A kiss","What makes two become one?|Love","What is sweetest when true?|Love","What never dies if true?|True love"].map(P);
var BANK_RIDDLE_PROGRAMMERS=["What runs without legs?|Code","What has bugs but is not an insect?|Software","What is 0 and 1?|Binary","What do you push to GitHub?|Code","What loops forever if you forget to stop it?|Infinite loop","What does HTML stand for?|HyperText Markup Language"].map(P);
var BANK_RIDDLE_SMART=["What comes once in a minute, twice in a moment, never in 1000 years?|The letter M","What has a head and tail but no body?|A coin","What goes up but never down?|Your age","What can you break without touching?|A promise"].map(P);
var BANK_RIDDLE_FUNNY=["Why did the chicken cross the road?|To get to the other side","What do you call a fish without eyes?|A fsh","Why did the scarecrow win an award?|He was outstanding in his field","What do you call cheese that is not yours?|Nacho cheese"].map(P);
var BANK_BIBLE_OLD=["Who built the ark?|Noah","Who was swallowed by a great fish?|Jonah","Abraham's wife?|Sarah","Who penned most Psalms?|David","Who led Israel out of Egypt?|Moses","Who killed Goliath?|David","Who was thrown into the lions den?|Daniel","First man created?|Adam","Who received the Ten Commandments?|Moses"].map(P);
var BANK_BIBLE_NEW=["First book of New Testament?|Matthew","Mother of Jesus?|Mary","Who betrayed Jesus for 30 silver?|Judas Iscariot","Shortest verse?|Jesus wept","River where Jesus was baptized?|Jordan River","Who wrote Revelation?|John","Where was Jesus born?|Bethlehem","Who denied Jesus three times?|Peter"].map(P);
var BANK_BIBLE_STORIES=["Story of the lost sheep teaches what?|God seeks the lost","Story of David and Goliath teaches what?|Faith beats giants","Story of Noah teaches what?|Obedience saves","Story of the Good Samaritan teaches what?|Love your neighbour","Story of Joseph teaches what?|Forgiveness"].map(P);
var currentMode='',currentCat='',qIndex=0,qList=[],correctCount=0,roundGold=0;
function buildOptions(correct,allAns){ var opts=[correct]; var pool=allAns.filter(function(a){return a!==correct}); for(var i=pool.length-1;i>0;i--){var j=(Math.random()*(i+1))|0;var t=pool[i];pool[i]=pool[j];pool[j]=t} for(var k=0;k<pool.length&&opts.length<3;k++){ if(opts.indexOf(pool[k])<0) opts.push(pool[k]); } while(opts.length<3) opts.push('None of these'); for(var i=opts.length-1;i>0;i--){var j=(Math.random()*(i+1))|0;var t=opts[i];opts[i]=opts[j];opts[j]=t} return {o:opts,a:opts.indexOf(correct)}; }
function pick10(bank){ var fresh=bank.filter(function(x){return seenQs.indexOf(x.q)<0}); if(fresh.length<10){ seenQs=[]; fresh=bank.slice(); } var pool=fresh.slice(); for(var i=pool.length-1;i>0;i--){var j=(Math.random()*(i+1))|0;var t=pool[i];pool[i]=pool[j];pool[j]=t} var picked=pool.slice(0,10); picked.forEach(function(x){ if(seenQs.indexOf(x.q)<0) seenQs.push(x.q); }); saveLocal(); var allAns=bank.map(function(x){return x.a}); return picked.map(function(x){ var oo=buildOptions(x.a,allAns); return {q:x.q,o:oo.o,a:oo.a}; }); }
function startQuiz(mode,cat,bank){ currentMode=mode; currentCat=cat; qList=pick10(bank); qIndex=0; correctCount=0; roundGold=0; showPage('page-game'); document.getElementById('gameTitle').innerText=(mode==='BIBLE'?'📖 BIBLE FIGHT':'🧩 RIDDLES')+' • '+cat; showQuestion(); }
function showQuestion(){ if(qIndex>=qList.length){ finishQuiz(); return; } var q=qList[qIndex]; var html='<p style="font-size:12px">Question '+(qIndex+1)+'/10 • Correct: '+correctCount+' • Gold this round: '+roundGold+'</p><h3>'+q.q+'</h3>'; q.o.forEach(function(opt,i){ html+='<button class="opt" onclick="answerQ('+i+')">'+opt+'</button>'; }); document.getElementById('gameBody').innerHTML=html; }
function answerQ(i){ var q=qList[qIndex]; if(i===q.a){ correctCount++; roundGold+=50; myGold+=50; playWin(); toast('✅ Correct! +50 Gold'); } else { losses++; playLose(); toast('❌ Wrong! Answer: '+q.o[q.a]); } qIndex++; saveLocal(); syncScore(); showQuestion(); }
function finishQuiz(){ wins+=correctCount; saveLocal(); syncScore(); document.getElementById('gameBody').innerHTML='<h2>🎉 Finished!</h2><p>Correct: '+correctCount+'/10</p><p>Gold earned: '+roundGold+'</p><button class="btn" onclick="goDash()">🏠 Back to Dashboard</button>'; loadMyProfileData(); }
function openRiddles(){ showPage('page-game'); document.getElementById('gameTitle').innerText='🧩 RIDDLES — Pick a Type'; document.getElementById('gameBody').innerHTML='<button class="opt" onclick="startQuiz(\'RIDDLE\',\'General\',BANK_RIDDLE_GENERAL)">🧩 General Riddles</button><button class="opt" onclick="startQuiz(\'RIDDLE\',\'Love\',BANK_RIDDLE_LOVE)">💖 Love Riddles</button><button class="opt" onclick="startQuiz(\'RIDDLE\',\'Programmers\',BANK_RIDDLE_PROGRAMMERS)">💻 Programmers</button><button class="opt" onclick="startQuiz(\'RIDDLE\',\'Smart\',BANK_RIDDLE_SMART)">🧠 Smart</button><button class="opt" onclick="startQuiz(\'RIDDLE\',\'Funny\',BANK_RIDDLE_FUNNY)">😂 Funny</button>'; }
function openBible(){ showPage('page-game'); document.getElementById('gameTitle').innerText='📖 BIBLE FIGHT'; document.getElementById('gameBody').innerHTML='<button class="opt" onclick="startQuiz(\'BIBLE\',\'Old Testament\',BANK_BIBLE_OLD)">📜 Old Testament</button><button class="opt" onclick="startQuiz(\'BIBLE\',\'New Testament\',BANK_BIBLE_NEW)">✝️ New Testament</button><button class="opt" onclick="startQuiz(\'BIBLE\',\'Stories\',BANK_BIBLE_STORIES)">📖 Bible Stories</button>'; }
function openSciFi(){ showPage('page-game'); document.getElementById('gameTitle').innerText='🚀 SCI-FI — 11 Games'; document.getElementById('gameBody').innerHTML='<p>HOW TO PLAY: Tap a game, follow the on-screen steps. Win = Gold, Lose = Gold goes to Server Economy.</p><button class="opt" onclick="openGalaxyShooterHard()">🌌 1. Galaxy Shooter — Tap aliens fast before they escape</button><button class="opt" onclick="openDecodingGame()">💻 2. Decoding — Type the code shown</button><button class="opt" onclick="openRiddles()">🧩 3. Riddles</button><button class="opt" onclick="openBible()">📖 4. Bible Fight</button><button class="opt" onclick="openLottery()">🎰 5. Lottery — 50% Win / 50% Lose</button><button class="opt" onclick="openShop(\'SciFi\')">🛍️ 6. Shop — 1000 Products</button><button class="opt" onclick="startQuiz(\'RIDDLE\',\'Smart\',BANK_RIDDLE_SMART)">🧠 7. Smart Quiz</button><button class="opt" onclick="startQuiz(\'RIDDLE\',\'Funny\',BANK_RIDDLE_FUNNY)">😂 8. Funny Quiz</button><button class="opt" onclick="openGalaxyShooterHard()">👽 9. Alien Hunt — Same as Galaxy Shooter</button><button class="opt" onclick="openDecodingGame()">🔐 10. Hack Code</button><button class="opt" onclick="openMessages()">💚 11. WhatsApp Challenge</button>'; }
function renderMenuGames(){ var el=document.getElementById('menuGamesList'); if(!el) return; el.innerHTML='<button class="opt" onclick="openGalaxyShooterHard()">🌌 Galaxy Shooter — Tap aliens fast</button><button class="opt" onclick="openDecodingGame()">💻 Decoding — Type code</button><button class="opt" onclick="openRiddles()">🧩 Riddles</button><button class="opt" onclick="openBible()">📖 Bible Fight</button><button class="opt" onclick="openLottery()">🎰 Lottery — 50/50</button><button class="opt" onclick="openShop(\'Menu\')">🛍️ Shop — 1000 Products</button>'; }
var alienScore=0;
function openGalaxyShooterHard(){ showPage('page-game'); document.getElementById('gameTitle').innerText='🌌 Galaxy Shooter'; alienScore=0; document.getElementById('gameBody').innerHTML='<p>HOW TO PLAY: Tap the 👽 10 times. Each tap = +20 Gold. Miss = nothing.</p><h2>Score: <span id="alienScore">0</span>/10</h2><div id="alienBox" style="font-size:70px;text-align:center;cursor:pointer" onclick="shootAlienHard()">👽</div><button class="btn" onclick="finishShooter()">🏁 Finish</button>'; }
function shootAlienHard(){ alienScore++; myGold+=20; var s=document.getElementById('alienScore'); if(s) s.innerText=alienScore; playWin(); if(alienScore>=10) finishShooter(); }
function finishShooter(){ wins+=1; saveLocal(); syncScore(); document.getElementById('gameBody').innerHTML='<h2>🎉 Galaxy Shooter Done!</h2><p>Score: '+alienScore+' • Gold earned: '+(alienScore*20)+'</p><button class="btn" onclick="goDash()">🏠 Back</button>'; }
var hackCode='';
function openDecodingGame(){ hackCode=''+Math.floor(1000+Math.random()*9000); showPage('page-game'); document.getElementById('gameTitle').innerText='💻 Decoding'; document.getElementById('gameBody').innerHTML='<p>HOW TO PLAY: Memorise the code, type it below. Correct = +100 Gold.</p><div style="font-size:40px;text-align:center;letter-spacing:10px">'+hackCode+'</div><input id="hackInput" placeholder="Type code" inputmode="numeric"><button class="btn" onclick="checkHack()">🔓 Decode</button>'; }
function checkHack(){ var v=document.getElementById('hackInput').value.trim(); if(v===hackCode){ myGold+=100; wins+=1; playWin(); toast('✅ Decoded! +100 Gold'); } else { losses+=1; playLose(); toast('❌ Wrong code!'); } saveLocal(); syncScore(); document.getElementById('gameBody').innerHTML='<h2>Done!</h2><button class="btn" onclick="goDash()">🏠 Back</button>'; }
function tagPlayer(id){ openPin('Enter PIN to send Challenge',function(pin){ fetch('/api/challenge_send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sender:user.name,target_id:id,game:'Galaxy Shooter'})}).then(function(r){return r.json()}).then(function(d){ if(d.error){ toast('⚠️ '+d.error); return; } toast('✅ Challenge sent!'); }); }); }
function tagPlayerForChallenge(){ openIdPopup('Enter Player ID to Challenge',function(fullId){ tagPlayer(fullId); }); }
function showChallengePopup(from,game,cid){ currentChallengeId=cid; document.getElementById('challengeText').innerHTML='🎮 <b>'+from+'</b> challenged you to <b>'+game+'</b>!<br>Do you accept?'; var ov=document.getElementById('challengeOverlay'); ov.classList.remove('hidden'); ov.style.display='flex'; if(challengeTimer) clearTimeout(challengeTimer); challengeTimer=setTimeout(function(){ hideChallengePopup(); },5000); }
function hideChallengePopup(){ var ov=document.getElementById('challengeOverlay'); if(ov){ ov.classList.add('hidden'); ov.style.display='none'; } }
function respondChallenge(accept){ var cid=currentChallengeId; hideChallengePopup(); fetch('/api/challenge_respond',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({challenge_id:cid,accept:accept})}).catch(function(){}); if(accept){ document.getElementById('challengeDashText').innerText='Challenge Accepted!'; showPage('page-challenge'); } else { toast('❌ Challenge declined'); goDash(); } }
function declineChallengeDash(){ showPage('page-dash'); }
function startChallengeGame(g){ toast('🎮 Starting: '+g); if(g==='Galaxy Shooter') openGalaxyShooterHard(); else if(g==='Decoding') openDecodingGame(); else if(g==='Bible Fight') openBible(); else openRiddles(); }
function checkForChallenges(){ if(!loggedIn||!user) return; fetch('/api/player?name='+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){ var ns=(d&&d.notifs)||[]; for(var i=ns.length-1;i>=0;i--){ if(ns[i].type==='challenge'&&ns[i].challenge_id){ showChallengePopup(ns[i].from||'Player',ns[i].game||'Galaxy Shooter',ns[i].challenge_id); break; } } if(ns.length>0){ var b=document.getElementById('notifBadge'); if(b){ b.innerText=ns.length; b.classList.remove('hidden'); } } }); }
function openMessages(){ if(!loggedIn) return; showPage('page-messages'); fetch('/api/friends?name='+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){ var html=''; (d.friends||[]).forEach(function(f){ html+='<div style="display:flex;justify-content:space-between;align-items:center;padding:12px;background:rgba(0,0,0,.4);border-radius:14px;margin:6px 0"><span>👤 '+f.name+'<br><small>'+f.player_id+'</small></span><button class="btn" style="width:auto;padding:8px 14px" onclick="openChat(\''+f.name+'\')">💬 Chat</button></div>'; }); document.getElementById('chatFriendList').innerHTML=html||'No friends yet'; }); }
function addFriendById(){ var d=document.getElementById('addFriendDigits').value.replace(/[^0-9]/g,''); if(d.length<8){ toast('Enter 8 digits'); return; } fetch('/api/add_friend',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:user.name,target_id:'INF-'+d})}).then(function(r){return r.json()}).then(function(dd){ if(dd.error){ toast('⚠️ '+dd.error); return; } toast('✅ Friend added!'); openMessages(); }); }
function openChat(name){ chatWithName=name; showPage('page-chat'); document.getElementById('chatWith').innerText=name; loadChat(); }
function loadChat(){ if(!chatWithName) return; fetch('/api/chat_get?a='+encodeURIComponent(user.name)+'&b='+encodeURIComponent(chatWithName)).then(function(r){return r.json()}).then(function(d){ var html=''; (d.messages||[]).forEach(function(m){ var mine=(m.from===user.name); var bg=mine?'background:#ffd700;color:#000;margin-left:auto':'background:rgba(255,255,255,.2);color:#fff'; html+='<div style="max-width:80%;padding:10px 14px;border-radius:18px;margin:6px 0;font-size:14px;'+bg+'">'+(m.kind==='voice'?'🎙️ Voice Note 🔊':m.text)+'<br><small style="opacity:.7">'+(m.time||'')+'</small></div>'; }); var box=document.getElementById('chatBox'); if(box){ box.innerHTML=html||'No messages yet — say hi!'; box.scrollTop=99999; } }).catch(function(){}); }
function sendMsg(){ var inp=document.getElementById('msgInput'); var txt=inp.value.trim(); if(!txt) return; fetch('/api/chat_send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sender:user.name,to:chatWithName,text:txt,kind:'text'})}).then(function(){ inp.value=''; playClick(); loadChat(); }); }
function startVoiceCall(){ var b=document.getElementById('callBanner'); if(b) b.classList.remove('hidden'); callSecs=0; var ct=document.getElementById('callTimer'); if(ct) ct.innerText='00:00'; if(callInterval) clearInterval(callInterval); callInterval=setInterval(function(){ callSecs++; var m=String(Math.floor(callSecs/60)).padStart(2,'0'); var s=String(callSecs%60).padStart(2,'0'); var el=document.getElementById('callTimer'); if(el) el.innerText=m+':'+s; },1000); toast('📞 Calling '+chatWithName+'...'); beep(880,300); }
function endVoiceCall(){ if(callInterval) clearInterval(callInterval); var b=document.getElementById('callBanner'); if(b) b.classList.add('hidden'); toast('📞 Call ended — '+callSecs+' sec'); fetch('/api/chat_send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sender:user.name,to:chatWithName,text:'📞 Voice Call — '+callSecs+' seconds',kind:'text'})}).then(function(){ loadChat(); }); }
function toggleVoiceNote(){ if(mediaRecorder && mediaRecorder.state==='recording'){ mediaRecorder.stop(); toast('🎙️ Voice note sent!'); return; } try{ navigator.mediaDevices.getUserMedia({audio:true}).then(function(stream){ mediaRecorder=new MediaRecorder(stream); var chunks=[]; mediaRecorder.ondataavailable=function(e){ chunks.push(e.data); }; mediaRecorder.onstop=function(){ fetch('/api/chat_send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sender:user.name,to:chatWithName,text:'🎙️ Voice Note',kind:'voice'})}).then(function(){ loadChat(); }); }; mediaRecorder.start(); toast('🎙️ Recording... Tap again to send'); beep(1200,200); }).catch(function(){ fetch('/api/chat_send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sender:user.name,to:chatWithName,text:'🎙️ Voice Note',kind:'voice'})}).then(function(){ loadChat(); toast('🎙️ Voice note sent'); }); }); }catch(e){ toast('🎙️ Voice note sent'); } }
function toggleMenu(){ var m=document.getElementById('menuDrop'); if(!m) return; var h=''; h+='<div style="padding:12px;cursor:pointer" onclick="openMyProfile();toggleMenu()">👤 My Profile</div>'; h+='<div style="padding:12px;cursor:pointer" onclick="openMessages();toggleMenu()">💬 Messages</div>'; h+='<div style="padding:12px;cursor:pointer" onclick="openFullLeader();toggleMenu()">🏆 Leaderboard</div>'; h+='<div style="padding:12px;cursor:pointer" onclick="goDash();toggleMenu()">🏠 Dashboard</div>'; h+='<div style="padding:12px;cursor:pointer" onclick="openMenuPage();toggleMenu()">🎮 Menu - Games</div>'; h+='<div style="padding:12px;cursor:pointer" onclick="openReviewRequest(\'review\');toggleMenu()">⭐ Review</div>'; h+='<div style="padding:12px;cursor:pointer" onclick="openReviewRequest(\'request\');toggleMenu()">📩 Request</div>'; h+='<div style="padding:12px;cursor:pointer" onclick="openBank();toggleMenu()">🧑‍💻 Bank</div>'; h+='<div style="padding:12px;cursor:pointer" onclick="openShop(\'Top\');toggleMenu()">🛍️ Shop</div>'; h+='<div style="padding:12px;cursor:pointer" onclick="openLottery();toggleMenu()">🎰 Lottery</div>'; if(isDominic()){ h+='<div style="padding:12px;cursor:pointer" onclick="openUpdatePage();toggleMenu()">🔄 Update Server</div>'; h+='<div style="padding:12px;cursor:pointer" onclick="openEconomy();toggleMenu()">💰 Server Economy - DOMINIC ONLY</div>'; h+='<div style="padding:12px;cursor:pointer" onclick="openServerInfo();toggleMenu()">🖥️ Server Info</div>'; } m.innerHTML=h; m.classList.toggle('hidden'); }
function openPin(desc,cb){ pinCallback=cb; var d=document.getElementById('pinDesc'); if(d) d.innerText=desc||'Enter your 4-digit PIN'; var pi=document.getElementById('pinInput'); if(pi) pi.value=''; var ov=document.getElementById('pinOverlay'); if(ov){ ov.classList.remove('hidden'); ov.style.display='flex'; } }
function closePin(){ var ov=document.getElementById('pinOverlay'); if(ov){ ov.classList.add('hidden'); ov.style.display='none'; } pinCallback=null; }
function confirmPin(){ var pin=document.getElementById('pinInput').value.trim(); if(pin.length!==4){ toast('PIN must be 4 digits'); return; } var cb=pinCallback; closePin(); if(cb) cb(pin); }
function openIdPopup(title,cb){ idCallback=cb; var t=document.getElementById('idTitle'); if(t) t.innerText=title||'Enter Player ID'; var ii=document.getElementById('idInput'); if(ii) ii.value=''; var ov=document.getElementById('idOverlay'); if(ov){ ov.classList.remove('hidden'); ov.style.display='flex'; } }
function closeIdPopup(){ var ov=document.getElementById('idOverlay'); if(ov){ ov.classList.add('hidden'); ov.style.display='none'; } idCallback=null; }
function confirmIdPopup(){ var d=document.getElementById('idInput').value.replace(/[^0-9]/g,''); if(d.length<8){ toast('Enter 8 digits'); return; } var cb=idCallback; closeIdPopup(); if(cb) cb('INF-'+d); }
try{ var bf=document.getElementById('backFab'); if(bf) bf.onclick=function(){ playClick(); goBack(); }; var mf=document.getElementById('msgFab'); if(mf) mf.onclick=function(){ playClick(); openMessages(); }; var pb=document.getElementById('profileBtn'); if(pb) pb.onclick=function(){ openMyProfile(); }; var sb=document.getElementById('soundBtn'); if(sb) sb.onclick=function(){ soundOn=!soundOn; this.innerText=soundOn?'🔊':'🔇'; toast(soundOn?'🔊 Sound ON':'🔇 Sound OFF'); beep(880,120); }; var mb=document.getElementById('menuBtn'); if(mb) mb.onclick=function(e){ e.stopPropagation(); toggleMenu(); }; }catch(e){}
document.addEventListener('click',function(e){ var m=document.getElementById('menuDrop'); if(m&&!m.contains(e.target)&&e.target.id!=='menuBtn') m.classList.add('hidden'); });
setInterval(function(){ if(loggedIn) checkForChallenges(); },10000);
setInterval(function(){ if(currentPage==='page-chat' && chatWithName) loadChat(); },5000);
setInterval(function(){ if(loggedIn&&user) syncScore(); },15000);
window.onload=function(){ updateCatTime(); updateVisibility(); showPage('page-home'); };
</script></body></html>
"""
if __name__=="__main__":
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
