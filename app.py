from flask import Flask, request, jsonify
import os, json, threading, random, time, datetime
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
def rank_for(wins):
    r="Beginner"
    for name,need in RANKS:
        if wins>=need: r=name
    return r
def is_classified(wins): return wins>=3200
def ensure_player(v,k):
    v.setdefault("display_name",k); v.setdefault("history",{}); v.setdefault("friends",[]); v.setdefault("requests",[])
    v.setdefault("wins",0); v.setdefault("losses",0); v.setdefault("stage",0); v.setdefault("gold",0); v.setdefault("gems",0)
    v.setdefault("bank_gold",0); v.setdefault("bank_gems",0); v.setdefault("notifs",[]); v.setdefault("seen_qs",[]); v.setdefault("items",[])
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
            for p in [LEADER_FILE, os.path.join(BASE,"leaderboard.json.backup"), os.path.join(BASE,"backup_storage.json")]:
                with open(p,"w") as f: f.write(data)
    except Exception as e: print(e)
def is_earning_active(): return datetime.datetime.now()>=EARNING_START and EARNING_ON
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
    if not is_earning_active(): return jsonify({"error":"Transfers blocked - Earning OFF by Admin"}),403
    if sender not in USERS: return jsonify({"error":"Sender not found"}),404
    s=USERS[sender]
    if str(s.get("password"))!=pin: notify(sender,"⚠️ Warning! Pin is wrong, please check again or try again later.","warn"); return jsonify({"error":"Wrong PIN"}),403
    rid="INF-"+clean_id(d.get("receiver_id","")); recv=None
    for v in USERS.values():
        if v.get("player_id")==rid: recv=v; break
    if not recv: return jsonify({"error":"Receiver ID not found"}),404
    if cur=="Gems":
        if s.get("gems",0)<amt: return jsonify({"error":"Not enough Gems"}),400
        s["gems"]-=amt; recv["gems"]=recv.get("gems",0)+amt
    else:
        if s.get("gold",0)<amt: return jsonify({"error":"Not enough Gold"}),400
        fee=int(amt*0.05); net=amt-fee; s["gold"]-=amt; recv["gold"]=recv.get("gold",0)+net
    notify(sender,f"Dear player you have successfully sent {amt} {cur} to {rid}. Thanks for your transaction.","send")
    notify(recv["display_name"],f"Dear {recv['display_name']} you have received {amt} {cur} from {s.get('player_id')}. Thank you.","receive")
    save_users(); return jsonify({"ok":True,"sender_gold":s["gold"],"sender_gems":s["gems"]})
@app.route("/api/bank_action",methods=["POST"])
def bank_action():
    d=request.get_json() or {}; n=norm(d.get("name")); pin=str(d.get("pin","")); amt=int(d.get("amount",0)); action=d.get("action","deposit"); cur=d.get("currency","Gold")
    if not is_earning_active(): return jsonify({"error":"Bank blocked - Earning OFF"}),403
    if n not in USERS: return jsonify({"error":"Not found"}),404
    v=USERS[n]
    if str(v.get("password"))!=pin: notify(n,"⚠️ Warning! Pin is wrong.","warn"); return jsonify({"error":"Wrong PIN"}),403
    if action=="deposit":
        if cur=="Gems":
            if v.get("gems",0)<amt: return jsonify({"error":"Not enough Gems"}),400
            v["gems"]-=amt; v["bank_gems"]=v.get("bank_gems",0)+amt
        else:
            if v.get("gold",0)<amt: return jsonify({"error":"Not enough Gold"}),400
            v["gold"]-=amt; v["bank_gold"]=v.get("bank_gold",0)+amt
        notify(n,f"Dear player you have successfully deposited {amt} {cur} to your Bank {v.get('bank_id')}.","deposit")
    elif action=="withdraw":
        if cur=="Gems":
            if v.get("bank_gems",0)<amt: return jsonify({"error":"Not enough in Bank"}),400
            v["bank_gems"]-=amt; v["gems"]=v.get("gems",0)+amt
        else:
            if v.get("bank_gold",0)<amt: return jsonify({"error":"Not enough in Bank"}),400
            v["bank_gold"]-=amt; v["gold"]=v.get("gold",0)+amt
        notify(n,f"Dear player you have successfully withdrawn {amt} {cur} from Bank to your Gold/Gems account.","withdraw")
    save_users(); return jsonify({"ok":True,"gold":v["gold"],"gems":v["gems"],"bank_gold":v.get("bank_gold",0),"bank_gems":v.get("bank_gems",0)})
@app.route("/api/exchange",methods=["POST"])
def exchange():
    d=request.get_json() or {}; n=norm(d.get("name")); pin=str(d.get("pin","")); amt=int(d.get("amount",0)); direction=d.get("direction","gold_to_gem")
    if not is_earning_active(): return jsonify({"error":"Exchange blocked - Earning OFF"}),403
    if n not in USERS: return jsonify({"error":"Not found"}),404
    v=USERS[n]
    if str(v.get("password"))!=pin: notify(n,"⚠️ Warning! Pin is wrong.","warn"); return jsonify({"error":"Wrong PIN"}),403
    if direction=="gold_to_gem":
        if v.get("gold",0)<amt: return jsonify({"error":"Not enough Gold"}),400
        gems=amt//100
        if gems<1: return jsonify({"error":"Need at least 100 Gold = 1 Germ"}),400
        v["gold"]-=gems*100; v["gems"]=v.get("gems",0)+gems
        notify(n,f"Dear player you exchanged {gems*100} Gold for {gems} Germ. Rate 100 Gold = 1 Germ.","exchange")
    else:
        if v.get("gems",0)<amt: return jsonify({"error":"Not enough Gems"}),400
        gold=amt*100; v["gems"]-=amt; v["gold"]=v.get("gold",0)+gold
        notify(n,f"Dear player you exchanged {amt} Germ for {gold} Gold. Rate 1 Germ = 100 Gold.","exchange")
    save_users(); return jsonify({"ok":True,"gold":v["gold"],"gems":v["gems"]})
@app.route("/api/withdraw",methods=["POST"])
def withdraw():
    d=request.get_json() or {}; n=norm(d.get("name")); pin=str(d.get("pin","")); amt=int(d.get("amount",0)); cur=d.get("currency","Gold")
    if not is_earning_active(): return jsonify({"error":"Withdrawals blocked - Earning OFF"}),403
    if n not in USERS: return jsonify({"error":"Not found"}),404
    v=USERS[n]
    if str(v.get("password"))!=pin: notify(n,"⚠️ Warning! Pin is wrong.","warn"); return jsonify({"error":"Wrong PIN"}),403
    if cur=="Gold":
        if v.get("gold",0)<amt: return jsonify({"error":"Not enough Gold"}),400
        v["gold"]-=amt
    else:
        if v.get("gems",0)<amt: return jsonify({"error":"Not enough Gems"}),400
        v["gems"]-=amt
    notify(n,f"Dear player you have successfully withdrawn {amt} {cur}. Thanks for your transaction.","withdraw")
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
    return jsonify({"players":len(USERS),"earning_on":EARNING_ON,"earning_active":is_earning_active(),"reviews":reviews})
@app.route("/api/buy_item",methods=["POST"])
def buy_item():
    d=request.get_json() or {}; n=norm(d.get("name")); pin=str(d.get("pin","")); item=d.get("item",""); price=int(d.get("price",0))
    if n not in USERS: return jsonify({"error":"Not found"}),404
    v=USERS[n]
    if str(v.get("password"))!=pin: return jsonify({"error":"Wrong PIN"}),403
    if v.get("gold",0)<price: return jsonify({"error":"Not enough Gold"}),400
    v["gold"]-=price; v.setdefault("items",[]).append(item)
    notify(n,f"Dear player you bought {item} for {price} Gold. Purchase confirmed.","shop")
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
@app.route("/webhook",methods=["GET","POST"])
def webhook():
    if request.method=="GET":
        if request.args.get("hub.mode")=="subscribe" and request.args.get("hub.verify_token")==VERIFY_TOKEN: return request.args.get("hub.challenge"),200
        return "Forbidden",403
    return jsonify({"ok":True})
HOME=r"""<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>INFINITY BOT v11 - 100 SHOP</title>
<link href="https://fonts.googleapis.com/css2?family=Great+Vibes&family=Poppins:wght@400;700;900&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<style>*{box-sizing:border-box}body{margin:0;font-family:Poppins,Arial;color:white;background:radial-gradient(circle at 50% 20%,#3a0a5e,#12002b 70%);min-height:100vh}.cursive{font-family:'Great Vibes',cursive}.topbar{display:flex;justify-content:space-between;align-items:center;padding:8px 14px}.profile{width:46px;height:46px;border-radius:50%;background:linear-gradient(135deg,#ff006e,#ffd700);display:flex;align-items:center;justify-content:center;font-size:20px;border:2px solid #fff;cursor:pointer;position:relative}.notif{position:absolute;top:-6px;right:-6px;background:red;color:white;font-size:11px;width:20px;height:20px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:900}.center{min-height:82vh;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:20px}.crownBig{font-size:90px;filter:drop-shadow(0 0 30px gold)}.enterBtn{margin-top:20px;padding:16px 70px;font-family:'Great Vibes',cursive;font-size:48px;border:none;border-radius:60px;background:linear-gradient(90deg,#ff006e,#ffd700,#00e5ff);color:#000;box-shadow:0 0 40px #ff006e;cursor:pointer}.card{background:rgba(255,255,255,.08);border:2px solid rgba(255,255,255,.35);border-radius:26px;padding:20px;margin:14px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.box{background:linear-gradient(160deg,rgba(255,255,255,.18),rgba(0,0,0,.4));border:2px solid #fff;border-radius:24px;padding:22px 10px;text-align:center;cursor:pointer}.box span{font-size:38px;display:block}.btn{width:100%;padding:14px;border:none;border-radius:25px;font-weight:900;background:#ffd700;margin:6px 0;cursor:pointer}.btn2{width:100%;padding:13px;border-radius:25px;border:2px solid #00e5ff;background:transparent;color:#00e5ff;font-weight:900;margin:6px 0;cursor:pointer}.opt{width:100%;padding:13px;margin:7px 0;border-radius:16px;border:2px solid #fff;background:rgba(0,0,0,.5);color:white;font-weight:700;cursor:pointer;text-align:left}input{width:100%;padding:14px;border-radius:14px;border:2px solid #ffd700;margin:8px 0;font-size:16px;background:#fff;color:#000}.hidden{display:none}.leadRow{display:flex;justify-content:space-between;align-items:center;padding:10px 12px;background:rgba(0,0,0,.45);border-radius:14px;margin:6px 0;cursor:pointer}.toast{position:fixed;top:70px;left:50%;transform:translateX(-50%);background:#fff;color:#000;padding:12px 18px;border-radius:20px;font-weight:700;z-index:999;max-width:90%;text-align:center}.gameOverlay{position:fixed;inset:0;background:rgba(0,0,0,.75);display:flex;align-items:center;justify-content:center;padding:16px;z-index:500}.gamePopup{background:linear-gradient(160deg,#2b005e,#12002b);border:3px solid #ffd700;border-radius:28px;padding:22px 18px;max-width:420px;width:100%;text-align:center;box-shadow:0 0 40px #ff006e}.choiceRow{display:flex;gap:12px;margin-top:16px}.choiceBox{flex:1;padding:18px 8px;border-radius:20px;cursor:pointer;font-weight:900;font-size:18px;border:3px solid #fff}.choiceNo{background:linear-gradient(135deg,#ff2222,#ff6b6b);color:#fff}.choiceYes{background:linear-gradient(135deg,#00cc44,#00ff88);color:#000}.warnBar{height:6px;background:rgba(255,255,255,.25);border-radius:99px;overflow:hidden;margin-top:14px}.warnBarFill{height:100%;background:linear-gradient(90deg,#ff006e,#ffd700);width:100%;animation:shrink 5s linear forwards}@keyframes shrink{from{width:100%}to{width:0%}}.bottomNav{position:fixed;bottom:0;left:0;right:0;background:rgba(0,0,0,.85);border-top:2px solid #ffd700;display:flex;justify-content:space-around;padding:10px 0 14px;z-index:100}.bottomNav div{font-size:28px;cursor:pointer;text-align:center}.bottomNav small{display:block;font-size:10px;color:#ffd700}.walletCard{background:linear-gradient(135deg,#ffd700,#ff006e);color:#000;border-radius:24px;padding:18px;text-align:center}.switch{width:70px;height:36px;background:#00cc44;border-radius:99px;position:relative;cursor:pointer;border:2px solid #fff}.switch.off{background:#ff2222}.switchKnob{position:absolute;top:3px;left:34px;width:28px;height:28px;background:#fff;border-radius:50%}.switch.off .switchKnob{left:3px}.spacexScene{background:#000010;border:2px solid #00e5ff;border-radius:20px;padding:16px;text-align:left;font-family:'Share Tech Mono',monospace;color:#00ffaa}.scifiCode{font-family:'Share Tech Mono',monospace;color:#00ffaa;font-size:13px;line-height:1.7;white-space:pre-wrap;border:1px solid #00ffaa;border-radius:14px;padding:12px;background:rgba(0,0,0,.65);text-align:left}.pinInput{font-size:28px;text-align:center;letter-spacing:12px}.tabRow{display:flex;gap:8px}.tabBox{flex:1;padding:12px 4px;border-radius:16px;background:rgba(255,255,255,.15);border:2px solid #ffd700;text-align:center;cursor:pointer;font-weight:900;font-size:13px}.tabBox.active{background:#ffd700;color:#000}.bigBankBox{padding:22px 10px;border-radius:24px;border:2px solid #fff;text-align:center;cursor:pointer;background:linear-gradient(160deg,rgba(255,255,255,.18),rgba(0,0,0,.4))}.idPrefix{display:flex;align-items:center;background:#fff;border-radius:14px;border:2px solid #ffd700;padding:0 10px;margin:8px 0}.idPrefix b{color:#000;white-space:nowrap}.idPrefix input{border:none;flex:1;margin:0}.shopItem{display:flex;justify-content:space-between;align-items:center;padding:12px;background:rgba(0,0,0,.45);border-radius:14px;margin:6px 0}
</style></head><body>
<div id="topbar" class="topbar hidden"><div><div style="font-weight:900">INFINITY BOT</div><span style="font-size:11px;background:rgba(0,0,0,.55);border:1px solid #ffd700;padding:4px 8px;border-radius:20px" id="catTime">--:--:--</span></div><div style="display:flex;flex-direction:column;align-items:flex-end;gap:2px"><div style="display:flex;gap:8px;align-items:center"><div style="width:32px;height:32px;border-radius:50%;background:rgba(0,0,0,.55);border:1px solid #ffd700;display:flex;align-items:center;justify-content:center;cursor:pointer" id="soundBtn">🔊</div><div class="profile" id="profileBtn">👤<span id="notifBadge" class="notif hidden">1</span></div></div><div style="width:32px;height:32px;border-radius:50%;background:rgba(0,0,0,.55);border:1px solid #ffd700;display:flex;align-items:center;justify-content:center;font-size:20px;cursor:pointer;margin-right:7px" id="menuBtn">⋮</div></div></div>
<div id="menuDrop" class="hidden" style="position:absolute;top:110px;right:10px;background:#1a1a2e;border:2px solid #ffd700;border-radius:16px;padding:8px;z-index:500;min-width:200px"></div>
<div id="toast" class="toast hidden"></div>
<div id="pinOverlay" class="gameOverlay hidden" style="display:none;z-index:900"><div class="gamePopup"><div style="font-size:50px">🔐</div><h2>Enter PIN</h2><p id="pinDesc" style="opacity:.8">Enter your 4-digit PIN to confirm</p><input id="pinInput" class="pinInput" placeholder="••••" maxlength="4" inputmode="numeric" type="password"><div class="choiceRow"><div class="choiceBox choiceNo" onclick="closePin()">❌ Cancel</div><div class="choiceBox choiceYes" onclick="confirmPin()">✅ Confirm</div></div></div></div>
<div id="idOverlay" class="gameOverlay hidden" style="display:none;z-index:900"><div class="gamePopup"><div style="font-size:50px">🏷️</div><h2 id="idTitle">Enter Player ID</h2><p style="opacity:.8">Type digits only — INF- is added automatically</p><div class="idPrefix"><b>INF-</b><input id="idInput" placeholder="12345678" inputmode="numeric" maxlength="8" style="font-size:22px;text-align:center;letter-spacing:4px"></div><div class="choiceRow"><div class="choiceBox choiceNo" onclick="closeIdPopup()">❌ Cancel</div><div class="choiceBox choiceYes" onclick="confirmIdPopup()">✅ Confirm</div></div></div></div>
<div id="challengeOverlay" class="gameOverlay hidden" style="display:none;z-index:800"><div class="gamePopup" style="border-color:#00e5ff"><div style="font-size:50px">🎮</div><h2>CHALLENGE REQUEST</h2><p id="challengeText"></p><div class="choiceRow"><div class="choiceBox choiceNo" onclick="respondChallenge(false)">❌<br>No</div><div class="choiceBox choiceYes" onclick="respondChallenge(true)">✅<br>Yes</div></div><p style="font-size:12px;opacity:.7">Auto closes in 5 seconds...</p><div class="warnBar"><div class="warnBarFill"></div></div></div></div>
<div id="page-home" class="center"><div style="font-size:26px">✨ 💖 ⭐ 🌟 💫</div><div class="crownBig">👑</div><h1 class="cursive" style="font-size:68px;margin:5px">Infinity Bot</h1><p style="letter-spacing:3px;font-weight:900">DOMINIC MASTIRIA</p><p>Riddles • Bible Fight • Sci-Fi • WhatsApp</p><button class="enterBtn" id="enterBtn">Enter</button><p style="font-size:12px;opacity:.7;margin-top:12px">Press ENTER to Continue</p></div>
<div id="page-register" class="hidden" style="max-width:520px;margin:0 auto;padding:20px 14px"><div class="card" style="text-align:center"><div style="font-size:60px">👑</div><h1 class="cursive" style="font-size:48px;margin:5px">Register</h1><p id="regSub">Create your Infinity account 👑</p><div id="registerForm"><label style="text-align:left;display:block">Your Name:</label><input id="regName" placeholder="Your Name" maxlength="20"><label style="text-align:left;display:block">4-Digit Password:</label><input id="regPass" placeholder="••••" maxlength="4" inputmode="numeric" type="password"><p style="font-size:12px;color:#ffd700">⚠️ Do NOT use 1234 or 0000</p><button class="btn" onclick="doRegister()">📝 REGISTER</button><p style="font-size:13px;opacity:.8">Already have an account? <b style="color:#ffd700;cursor:pointer" onclick="showLogin()">Click here to Login</b></p></div><div id="loginForm" class="hidden"><label style="text-align:left;display:block">Your Name:</label><input id="loginName" placeholder="Your Name"><label style="text-align:left;display:block">4-Digit Password:</label><input id="loginPass" placeholder="••••" maxlength="4" inputmode="numeric" type="password"><button class="btn" onclick="doLogin()">🔓 LOGIN</button><p style="font-size:13px;opacity:.8">New here? <b style="color:#ffd700;cursor:pointer" onclick="showRegister()">Click here to Register</b></p></div></div></div>
<div id="page-dash" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div style="text-align:center"><h2 class="cursive" style="font-size:44px;margin:10px 0" id="welcomeText">Welcome, Player 👑</h2><span style="display:inline-block;padding:5px 10px;border-radius:20px;background:rgba(0,0,0,.5);border:1px solid #ffd700;font-size:12px">⭐ Rank: <b id="myRank">#-</b></span> <span style="display:inline-block;padding:5px 10px;border-radius:20px;background:rgba(0,0,0,.5);border:1px solid #ffd700;font-size:12px">🎯 <b id="myStage">Beginner</b></span></div><div class="grid"><div class="box" onclick="openRiddles()"><span>🧩</span><b>RIDDLES</b><br><small>5 Types • EASY + HARD</small></div><div class="box" onclick="openBible()"><span>📖</span><b>BIBLE FIGHT</b><br><small>Old + New + Stories</small></div><div class="box" onclick="openSciFi()"><span>🚀</span><b>SCI-FI</b><br><small>10 Games • HARD</small></div><div class="box" onclick="openMessages()"><span>💚</span><b>WHATSAPP</b><br><small>Chat • Call • Voice</small></div></div><div class="card"><h3 style="text-align:center;margin:0">🛍️ MEGA SHOP — 100 PRODUCTS</h3><p style="text-align:center;font-size:12px;opacity:.8">200 Gold → 1 Trillion Gold</p><button class="btn" onclick="openShop('Dashboard')">🛍️ OPEN SHOP — 100 PRODUCTS</button></div><div class="card"><h3 style="text-align:center;margin:0">🏆 TOP 5 🏆</h3><div id="leaderList">Loading...</div><button class="btn2" onclick="openFullLeader()">👀 View Full Leaderboard</button></div></div>
<div id="page-leader" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h3 style="text-align:center;margin:0">🏆 LEADERBOARD 🏆</h3><div class="tabRow" style="margin:12px 0"><div class="tabBox" id="tabGold" onclick="setLeaderMode('gold')">🪙<br>Gold</div><div class="tabBox" id="tabGems" onclick="setLeaderMode('gems')">💎<br>Germ</div><div class="tabBox" id="tabRank" onclick="setLeaderMode('rank')">⭐<br>Rank</div><div class="tabBox active" id="tabPvp" onclick="setLeaderMode('pvp')">⚔️<br>PvP</div></div><p id="leaderModeText" style="text-align:center;font-size:12px;opacity:.8">Ranked by Wins - Losses</p><div id="fullLeaderList">Loading...</div></div></div>
<div id="page-game" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 id="gameTitle" style="text-align:center">Game</h2><div id="gameBody"></div></div></div>
<div id="page-coming" class="hidden" style="max-width:520px;margin:0 auto;padding:40px 20px 90px;text-align:center"><div style="font-size:80px">🚀</div><h1 class="cursive" style="font-size:54px">Coming Soon</h1><h2>SCI-FI</h2><p>Launching on<br><b>25th December 2026</b></p><div style="font-size:60px;font-weight:900;color:#ffd700" id="countDown">5</div></div>
<div id="page-bank" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">🧑‍💻 BANK</h2><div class="walletCard"><div>🏦 BANK PROFILE</div><div style="font-size:18px;font-weight:900" id="bankIDShow">Bank INF-0000000000</div><div style="font-size:22px;margin-top:8px">🪙 Bank Gold: <b id="bankGold">0</b></div><div>💎 Bank Germ: <b id="bankGems">0</b></div><div style="margin-top:8px">Wallet — 🪙 <span id="walletGold">0</span> | 💎 <span id="walletGems">0</span></div></div><div class="grid" style="margin-top:14px"><div class="bigBankBox" onclick="openSendPage()"><span style="font-size:36px">💸</span><br><b>Send Gold</b></div><div class="bigBankBox" onclick="openWithdrawPage()"><span style="font-size:36px">🏧</span><br><b>Withdraw</b></div><div class="bigBankBox" onclick="openDepositPage()"><span style="font-size:36px">💰</span><br><b>Deposit</b></div><div class="bigBankBox" onclick="openMyProfile()"><span style="font-size:36px">👤</span><br><b>Bank</b></div></div><div class="bigBankBox" style="margin-top:14px" onclick="openExchangePage()"><span style="font-size:36px">🔄</span><br><b>Exchange</b><br><small>100 Gold = 1 Germ</small></div></div></div>
<div id="page-send" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">💸 SEND GOLD</h2><div class="walletCard"><div>Your Wallet</div><div>🪙 <b id="sendPageGold">0</b> Gold | 💎 <b id="sendPageGems">0</b> Germ</div><div>Your ID: <b id="sendPageMyID">INF-00000000</b></div></div><label>Receiver ID — type digits only:</label><div class="idPrefix"><b>INF-</b><input id="sendDigits" placeholder="12345678" inputmode="numeric" maxlength="8"></div><p id="sendReceiverName" style="color:#00ffaa;font-weight:900"></p><label>Amount:</label><input id="sendAmt" type="number" placeholder="Amount"><button class="btn" onclick="doSend()">➤ SEND NOW</button><p style="font-size:12px;opacity:.8">Fee 5% to Server Economy</p></div></div>
<div id="page-withdraw" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">🏧 WITHDRAW</h2><div class="walletCard"><div>🏦 Bank: 🪙 <b id="wdBankGold">0</b> | 💎 <b id="wdBankGems">0</b></div><div>Wallet: 🪙 <b id="wdWalletGold">0</b> | 💎 <b id="wdWalletGems">0</b></div><div>Bank ID: <b id="wdBankID">Bank INF-</b></div></div><label>Amount:</label><input id="withdrawAmt" type="number" placeholder="Amount"><select id="withdrawCur" style="width:100%;padding:14px;border-radius:14px"><option>Gold</option><option>Gems</option></select><button class="btn" onclick="doWithdraw()">🏧 WITHDRAW NOW</button></div></div>
<div id="page-deposit" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">💰 DEPOSIT</h2><div class="walletCard"><div>Wallet: 🪙 <b id="depWalletGold">0</b> | 💎 <b id="depWalletGems">0</b></div><div>🏦 Bank: 🪙 <b id="depBankGold">0</b> | 💎 <b id="depBankGems">0</b></div><div>Bank ID: <b id="depBankID">Bank INF-</b></div></div><label>Amount:</label><input id="depositAmt" type="number" placeholder="Amount"><select id="depositCur" style="width:100%;padding:14px;border-radius:14px"><option>Gold</option><option>Gems</option></select><button class="btn" onclick="doDeposit()">💰 DEPOSIT NOW</button></div></div>
<div id="page-exchange" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">🔄 EXCHANGE</h2><div class="walletCard"><div>Wallet: 🪙 <b id="exWalletGold">0</b> | 💎 <b id="exWalletGems">0</b></div></div><div class="bigBankBox" onclick="openExchange('gold_to_gem')"><b>Gold &gt;&gt;&gt;&gt; Germ</b><br><small>100 Gold = 1 Germ</small></div><div class="bigBankBox" style="margin-top:10px" onclick="openExchange('gem_to_gold')"><b>Germ &gt;&gt;&gt;&gt; Gold</b><br><small>1 Germ = 100 Gold</small></div><div id="exchangeForm" style="margin-top:12px"></div></div></div>
<div id="page-profile" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card" style="text-align:center"><div style="font-size:70px">👤</div><h2 id="profName">Player</h2><p style="color:#ffd700" id="profIDShow">ID:INF-00000000</p><p style="color:#ffd700" id="profBankID">Bank INF-0000000000</p><p>⭐ Rank: <b id="profRank">#-</b></p><p>🏆 Wins: <b id="profWins">0</b> | ❌ Losses: <b id="profLoss">0</b></p><p>🎯 Stage: <b id="profStage">Beginner</b></p><p>🪙 Gold: <b id="profGold">0</b> | 💎 Germ: <b id="profGems">0</b></p><p>🏦 Bank: 🪙 <b id="profBankGold">0</b> | 💎 <b id="profBankGems">0</b></p></div></div>
<div id="page-other" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card" style="text-align:center"><div style="font-size:70px">👤</div><h2 id="otherName">Player</h2><div id="otherClassified" class="hidden"><div style="font-size:40px">⚠️</div><h3>⚠️ Warning ⚠️</h3><p>You can't view this profile 😉<br>Sorry please level up</p></div><div id="otherNormal"><p>⭐ Rank: <b id="otherRank">#-</b></p><p><b id="otherWins">0</b> Win | <b id="otherLoss">0</b> Lose</p><div id="otherActions"></div></div></div></div>
<div id="page-notifs" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">✉️ NOTIFICATIONS</h2><div id="notifList">No notifications</div></div></div>
<div id="page-menu" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">🎮 MENU - 10 HARD GAMES</h2><div id="menuGamesList"></div></div></div>
<div id="page-update" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">🔄 UPDATE SERVER - DOMINIC ONLY</h2><div class="spacexScene"><p>🚀 SPACEX UPDATE CONSOLE</p><div class="scifiCode">> CHECKING UPDATE...
> DOWNLOADING CHRISTMAS UPDATE v11...
> APPLYING 100 SHOP PRODUCTS... OK
> APPLYING 10 HARD GAMES... OK
> SYNCING PLAYERS... NO DATA LOST
> READY - Earning</div><div style="display:flex;justify-content:space-between;align-items:center;margin-top:16px;background:rgba(255,255,255,.1);padding:14px;border-radius:16px"><div><div style="font-size:20px;font-weight:900">Earning</div><div style="font-size:12px;opacity:.8" id="earningDesc">ON</div></div><div class="switch" id="earningSwitch" onclick="toggleEarningSwitch()"><div class="switchKnob"></div></div></div><p style="font-size:12px;opacity:.8">OFF = RED • Earning stops • Transfers + Withdraws blocked<br>ON = GREEN • Everything back to normal</p></div><button class="btn" onclick="doServerUpdate()">🚀 APPLY UPDATE NOW</button></div></div>
<div id="page-server-info" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">🖥️ SERVER INFO - DOMINIC ONLY</h2><div class="spacexScene"><p>🚀 SPACEX // INFINITY SERVER</p><div>> PLAYERS: <span id="serverPlayers">0</span></div><div>> EARNING: <span id="serverEarningText">ON</span></div></div><h3>📜 Reviews</h3><div id="serverReviewsList">Loading...</div></div></div>
<div id="page-review" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center" id="reviewTitle">⭐ Review</h2><textarea id="reviewText" style="width:100%;height:140px;padding:14px;border-radius:14px;margin:12px 0;font-size:16px" placeholder="Type your review or request..."></textarea><button class="btn" onclick="submitReview()">📩 SEND</button></div></div>
<div id="page-challenge" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">🎮 CHALLENGE DASHBOARD</h2><p id="challengeDashText" style="text-align:center"></p><p style="text-align:center">Pick what to challenge each other:</p><div class="grid"><div class="box" onclick="startChallengeGame('Galaxy Shooter')"><span>🌌</span><b>Galaxy Shooter</b></div><div class="box" onclick="startChallengeGame('Riddles')"><span>🧩</span><b>Riddles</b></div><div class="box" onclick="startChallengeGame('Bible Fight')"><span>📖</span><b>Bible Fight</b></div><div class="box" onclick="startChallengeGame('Decoding')"><span>💻</span><b>Decoding</b></div></div><button class="btn2" onclick="declineChallengeDash()">❌ Decline / Close</button></div></div>
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
var currentChallengeId=null,challengeTimer=null,reviewType='review',pinCallback=null,leaderMode='pvp',idCallback=null;
function isDominic(){return user&&user.name&&user.name.toLowerCase()==='dominic'&&user.password==='2164'}
// SOUND - WebAudio beep, works in Opera Mini
var soundOn=true, audioCtx=null;
function beep(freq,dur){ if(!soundOn) return; try{ if(!audioCtx) audioCtx=new (window.AudioContext||window.webkitAudioContext)(); var o=audioCtx.createOscillator(), g=audioCtx.createGain(); o.connect(g); g.connect(audioCtx.destination); o.frequency.value=freq||880; g.gain.value=0.15; o.start(); setTimeout(function(){o.stop()},dur||150);}catch(e){} }
function playClick(){ beep(880,120); } function playWin(){ beep(880,120); setTimeout(function(){beep(1100,150)},150); setTimeout(function(){beep(1320,200)},300); } function playLose(){ beep(200,300); }
// CAT - NO ZAMBIA, ONLY TIME
function updateCatTime(){ try{ var d=new Date(); var t=String(d.getHours()).padStart(2,'0')+':'+String(d.getMinutes()).padStart(2,'0')+':'+String(d.getSeconds()).padStart(2,'0'); var el=document.getElementById('catTime'); if(el) el.textContent=t; }catch(e){} }
setInterval(updateCatTime,1000); updateCatTime();
function toast(m){var t=document.getElementById('toast');t.innerText=m;t.classList.remove('hidden');setTimeout(function(){t.classList.add('hidden')},4500)}
function updateVisibility(){ var top=document.getElementById('topbar'), nav=document.getElementById('bottomNav'), back=document.getElementById('backFab'), msg=document.getElementById('msgFab'); var isDash=currentPage==='page-dash'; var isHomeOrReg=currentPage==='page-home'||currentPage==='page-register'; if(loggedIn&&isDash){ top.classList.remove('hidden'); nav.classList.remove('hidden'); back.style.display='none'; msg.style.display='flex'; } else if(loggedIn&&!isHomeOrReg){ top.classList.add('hidden'); nav.classList.add('hidden'); back.style.display='flex'; msg.style.display='flex'; } else { top.classList.add('hidden'); nav.classList.add('hidden'); back.style.display='none'; msg.style.display='none'; } }
function showPage(id){ currentPage=id; ['page-home','page-register','page-dash','page-leader','page-game','page-coming','page-bank','page-send','page-withdraw','page-deposit','page-exchange','page-profile','page-other','page-notifs','page-menu','page-update','page-server-info','page-review','page-challenge','page-messages','page-chat'].forEach(function(p){var el=document.getElementById(p); if(el) el.classList.add('hidden');}); var tg=document.getElementById(id); if(tg) tg.classList.remove('hidden'); window.scrollTo(0,0); updateVisibility(); }
function goDash(){ if(!loggedIn){ showPage('page-register'); return; } showPage('page-dash'); loadLeader(); }
function goBack(){ if(currentPage==='page-register') showPage('page-home'); else if(currentPage==='page-chat') showPage('page-messages'); else goDash(); }
document.getElementById('backFab').onclick=function(){ playClick(); goBack(); };
document.getElementById('msgFab').onclick=function(){ playClick(); openMessages(); };
document.getElementById('profileBtn').onclick=function(){ openMyProfile(); };
document.getElementById('soundBtn').onclick=function(){ soundOn=!soundOn; this.innerText=soundOn?'🔊':'🔇'; toast(soundOn?'🔊 Sound ON':'🔇 Sound OFF'); beep(880,120); };
// PIN + ID POPUPS - IN-GAME ONLY, NO window.prompt
function openPin(desc,cb){ pinCallback=cb; document.getElementById('pinDesc').innerText=desc||'Enter your 4-digit PIN to confirm'; document.getElementById('pinInput').value=''; var ov=document.getElementById('pinOverlay'); ov.classList.remove('hidden'); ov.style.display='flex'; setTimeout(function(){document.getElementById('pinInput').focus()},200); }
function closePin(){ var ov=document.getElementById('pinOverlay'); ov.classList.add('hidden'); ov.style.display='none'; pinCallback=null; }
function confirmPin(){ var pin=document.getElementById('pinInput').value.trim(); if(pin.length!==4){ toast('PIN must be 4 digits'); return; } var cb=pinCallback; closePin(); if(cb) cb(pin); }
function openIdPopup(title,cb){ idCallback=cb; document.getElementById('idTitle').innerText=title||'Enter Player ID'; document.getElementById('idInput').value=''; var ov=document.getElementById('idOverlay'); ov.classList.remove('hidden'); ov.style.display='flex'; }
function closeIdPopup(){ var ov=document.getElementById('idOverlay'); ov.classList.add('hidden'); ov.style.display='none'; idCallback=null; }
function confirmIdPopup(){ var d=document.getElementById('idInput').value.replace(/[^0-9]/g,''); if(d.length<8){ toast('Enter 8 digits'); return; } var cb=idCallback; closeIdPopup(); if(cb) cb('INF-'+d); }
function toggleMenu(){ var m=document.getElementById('menuDrop'); if(!m) return; var h=''; h+='<div style="padding:12px;cursor:pointer" onclick="openMyProfile();toggleMenu()">👤 My Profile</div>'; h+='<div style="padding:12px;cursor:pointer" onclick="openMessages();toggleMenu()">💬 Messages</div>'; h+='<div style="padding:12px;cursor:pointer" onclick="openFullLeader();toggleMenu()">🏆 Leaderboard</div>'; h+='<div style="padding:12px;cursor:pointer" onclick="goDash();toggleMenu()">🏠 Dashboard</div>'; h+='<div style="padding:12px;cursor:pointer" onclick="openMenuPage();toggleMenu()">🎮 Menu - New Games</div>'; h+='<div style="padding:12px;cursor:pointer" onclick="openReviewRequest(\'review\');toggleMenu()">⭐ Review</div>'; h+='<div style="padding:12px;cursor:pointer" onclick="openReviewRequest(\'request\');toggleMenu()">📩 Request</div>'; h+='<div style="padding:12px;cursor:pointer" onclick="openBank();toggleMenu()">🧑‍💻 Bank</div>'; h+='<div style="padding:12px;cursor:pointer" onclick="openShop(\'Dashboard\');toggleMenu()">🛍️ Mega Shop 100</div>'; if(isDominic()){ h+='<div style="padding:12px;cursor:pointer" onclick="openUpdatePage();toggleMenu()">🔄 Update Server</div>'; h+='<div style="padding:12px;cursor:pointer" onclick="openServerInfo();toggleMenu()">🖥️ Server Info - ADMIN ONLY</div>'; } m.innerHTML=h; m.classList.toggle('hidden'); }
document.getElementById('menuBtn').onclick=function(e){ e.stopPropagation(); toggleMenu(); };
document.addEventListener('click',function(e){ var m=document.getElementById('menuDrop'); if(m&&!m.contains(e.target)&&e.target.id!=='menuBtn') m.classList.add('hidden'); });
function showRegister(){ document.getElementById('registerForm').classList.remove('hidden'); document.getElementById('loginForm').classList.add('hidden'); }
function showLogin(){ document.getElementById('registerForm').classList.add('hidden'); document.getElementById('loginForm').classList.remove('hidden'); }
function goRegister(){ showPage('page-register'); showRegister(); }
document.getElementById('enterBtn').addEventListener('click',function(){ playClick(); goRegister(); });
function saveLocal(){ try{ localStorage.setItem('inf_user',JSON.stringify(user)); localStorage.setItem('inf_wins',wins); localStorage.setItem('inf_loss',losses); localStorage.setItem('inf_gold',myGold); localStorage.setItem('inf_gems',myGems); localStorage.setItem('inf_player_id',myPlayerID); localStorage.setItem('inf_bank_id',myBankID); localStorage.setItem('inf_seen',JSON.stringify(seenQs)); localStorage.setItem('inf_has_account','yes'); }catch(e){} }
function doRegister(){ var n=document.getElementById('regName').value.trim(); var pw=document.getElementById('regPass').value.trim(); if(!n){toast('Enter name');return} if(!pw||pw.length!==4||isNaN(pw)){toast('Password must be exactly 4 digits');return} if(pw==='1234'||pw==='0000'){toast('Password too easy');return} fetch('/api/player?name='+encodeURIComponent(n)).then(function(r){return r.json()}).then(function(d){ if(d&&d.found){ showLogin(); document.getElementById('loginName').value=n; toast('Account found! Please Login'); return; } user={name:n,password:pw}; wins=0; losses=0; myGold=0; myGems=0; seenQs=[]; saveLocal(); syncScore(); enterDashboard('Welcome '+n+'! Registered 👑'); }); }
function doLogin(){ var n=document.getElementById('loginName').value.trim(); var pw=document.getElementById('loginPass').value.trim(); if(!n||!pw){toast('Enter name + password');return} fetch('/api/player?name='+encodeURIComponent(n)+'&password='+encodeURIComponent(pw)).then(function(r){return r.json()}).then(function(d){ if(d&&d.found&&d.password_ok!==false){ user={name:n,password:pw}; wins=d.wins||0; losses=d.losses||0; myGold=d.gold||0; myGems=d.gems||0; myPlayerID=d.player_id||''; myBankID=d.bank_id||''; seenQs=d.seen_qs||[]; saveLocal(); enterDashboard('Welcome back '+n+'! 👑'); } else { toast('⚠️ Account not found / Wrong password'); } }); }
function enterDashboard(msg){ loggedIn=true; toast(msg); playWin(); showPage('page-dash'); document.getElementById('welcomeText').innerText='Welcome, '+(user?user.name:'Player')+' 👑'; updateGoldUI(); loadLeader(); loadMyProfileData(); }
function syncScore(){ if(!user) return; fetch('/api/score',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:user.name,password:user.password,wins:wins,losses:losses,stage:stageIdx,gold:myGold,gems:myGems,seen_qs:seenQs})}).catch(function(){}); }
function updateGoldUI(){}
function loadMyProfileData(){ if(!user) return; fetch('/api/player?name='+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){ if(!d||!d.found) return; myPlayerID=d.player_id; myBankID=d.bank_id||myBankID; document.getElementById('myRank').innerText='#-'; document.getElementById('myStage').innerText=d.rank||'Beginner'; var bg=document.getElementById('bankGold'); if(bg) bg.innerText=d.bank_gold||0; var bg2=document.getElementById('bankGems'); if(bg2) bg2.innerText=d.bank_gems||0; var bi=document.getElementById('bankIDShow'); if(bi) bi.innerText=d.bank_id||myBankID; var wg=document.getElementById('walletGold'); if(wg) wg.innerText=d.gold; var wg2=document.getElementById('walletGems'); if(wg2) wg2.innerText=d.gems; }); }
function loadLeader(){ fetch('/api/leaderboard?mode=pvp').then(function(r){return r.json()}).then(function(d){ var ps=d.players||[]; var html=''; ps.slice(0,5).forEach(function(p,i){ html+='<div class="leadRow" onclick="viewOtherPlayer(\''+p.name+'\')"><span>'+(i+1)+'. '+p.name+'</span><span>🏆 '+p.wins+'W • ❌ '+p.losses+'L</span></div>'; }); document.getElementById('leaderList').innerHTML=html||'No players yet'; }); }
function setLeaderMode(m){ leaderMode=m; ['gold','gems','rank','pvp'].forEach(function(x){ var el=document.getElementById('tab'+x.charAt(0).toUpperCase()+x.slice(1)); if(el) el.classList.remove('active'); }); var act=document.getElementById('tab'+m.charAt(0).toUpperCase()+m.slice(1)); if(act) act.classList.add('active'); openFullLeader(); }
function openFullLeader(){ showPage('page-leader'); fetch('/api/leaderboard?mode='+leaderMode).then(function(r){return r.json()}).then(function(d){ var ps=d.players||[]; var html=''; var label=leaderMode==='gold'?'Ranked by Total Gold':leaderMode==='gems'?'Ranked by Total Germ':leaderMode==='rank'?'Ranked by Rank Level':'Ranked by Wins - Losses'; document.getElementById('leaderModeText').innerText=label; ps.forEach(function(p,i){ var extra=leaderMode==='gold'?'🪙 '+p.gold+' Gold':leaderMode==='gems'?'💎 '+p.gems+' Germ':leaderMode==='rank'?'⭐ '+p.rank:'🏆 '+p.wins+'W • ❌ '+p.losses+'L'; html+='<div class="leadRow" onclick="viewOtherPlayer(\''+p.name+'\')"><span>'+(i+1)+'. '+p.name+'<br><small>'+p.player_id+'</small></span><span>'+extra+'</span></div>'; }); document.getElementById('fullLeaderList').innerHTML=html||'No players'; }); }
function viewOtherPlayer(name){ if(!user) return; fetch('/api/player?name='+encodeURIComponent(name)).then(function(r){return r.json()}).then(function(d){ if(!d||!d.found) return; showPage('page-other'); document.getElementById('otherName').innerText=d.name; if(d.classified){ document.getElementById('otherClassified').classList.remove('hidden'); document.getElementById('otherNormal').classList.add('hidden'); } else { document.getElementById('otherClassified').classList.add('hidden'); document.getElementById('otherNormal').classList.remove('hidden'); document.getElementById('otherRank').innerText=d.rank; document.getElementById('otherWins').innerText=d.wins; document.getElementById('otherLoss').innerText=d.losses; document.getElementById('otherActions').innerHTML='<button class="btn" onclick="tagPlayer(\''+d.player_id+'\')">🏷️ Challenge This Player</button><button class="btn2" onclick="openBankSendTo(\''+d.player_id+'\')">💸 Send Gold</button>'; } }); }
function openMyProfile(){ if(!loggedIn) return; showPage('page-profile'); fetch('/api/player?name='+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){ if(!d||!d.found) return; document.getElementById('profName').innerText=d.name; document.getElementById('profIDShow').innerText='ID:'+d.player_id; document.getElementById('profBankID').innerText=d.bank_id; document.getElementById('profRank').innerText='#-'; document.getElementById('profWins').innerText=d.wins; document.getElementById('profLoss').innerText=d.losses; document.getElementById('profStage').innerText=d.rank; document.getElementById('profGold').innerText=d.gold; document.getElementById('profGems').innerText=d.gems; document.getElementById('profBankGold').innerText=d.bank_gold||0; document.getElementById('profBankGems').innerText=d.bank_gems||0; }); }
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
function refreshEarningSwitch(){ fetch('/api/earning_status').then(function(r){return r.json()}).then(function(d){ var sw=document.getElementById('earningSwitch'); var desc=document.getElementById('earningDesc'); if(d.earning_on){ sw.classList.remove('off'); desc.innerText='ON - Players earn Gold + Gems'; } else { sw.classList.add('off'); desc.innerText='OFF - RED • Earning stopped • Transfers + Withdraws blocked'; } }); }
function toggleEarningSwitch(){ if(!isDominic()) return; fetch('/api/toggle_earning',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:user.name,password:user.password})}).then(function(r){return r.json()}).then(function(d){ refreshEarningSwitch(); toast(d.earning_on?'✅ Earning ON':'🛑 Earning OFF - RED'); }); }
function doServerUpdate(){ if(!isDominic()) return; toast('🚀 Applying Update...'); setTimeout(function(){ refreshEarningSwitch(); toast('✅ Server Updated! Earning starts 25 Dec 2026'); },1500); }
function openServerInfo(){ if(!isDominic()){ toast('🔒 ADMIN ONLY'); return; } showPage('page-server-info'); fetch('/api/server_info?name=Dominic&password=2164').then(function(r){return r.json()}).then(function(d){ document.getElementById('serverPlayers').innerText=d.players||0; document.getElementById('serverEarningText').innerText=d.earning_on?'ON':'OFF'; var html=''; (d.reviews||[]).forEach(function(rv){ html+='<div style="padding:10px;border-bottom:1px solid #00ffaa">['+rv.type+'] '+rv.name+': '+rv.text+'</div>'; }); document.getElementById('serverReviewsList').innerHTML=html||'No reviews'; }); }
function tagPlayer(id){ openPin('Enter your PIN to send Challenge',function(pin){ fetch('/api/challenge_send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sender:user.name,target_id:id,game:'Galaxy Shooter'})}).then(function(r){return r.json()}).then(function(d){ if(d.error){ toast('⚠️ '+d.error); return; } toast('✅ Challenge sent!'); }); }); }
function tagPlayerForChallenge(){ openIdPopup('Enter Player ID to Challenge',function(fullId){ tagPlayer(fullId); }); }
function showChallengePopup(from,game,cid){ currentChallengeId=cid; document.getElementById('challengeText').innerHTML='🎮 <b>'+from+'</b> challenged you to <b>'+game+'</b>!<br>Do you accept?'; var ov=document.getElementById('challengeOverlay'); ov.classList.remove('hidden'); ov.style.display='flex'; if(challengeTimer) clearTimeout(challengeTimer); challengeTimer=setTimeout(function(){ hideChallengePopup(); },5000); }
function hideChallengePopup(){ var ov=document.getElementById('challengeOverlay'); if(ov){ ov.classList.add('hidden'); ov.style.display='none'; } }
function respondChallenge(accept){ var cid=currentChallengeId; hideChallengePopup(); fetch('/api/challenge_respond',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({challenge_id:cid,accept:accept})}).catch(function(){}); if(accept){ document.getElementById('challengeDashText').innerText='Challenge Accepted! Pick what to challenge:'; showPage('page-challenge'); } else { toast('❌ Challenge declined - Dashboard removed'); goDash(); } }
function declineChallengeDash(){ showPage('page-dash'); }
function startChallengeGame(g){ toast('🎮 Starting Challenge: '+g); if(g==='Galaxy Shooter') openGalaxyShooterHard(); else if(g==='Decoding') openDecodingGame(); else if(g==='Bible Fight') openBible(); else openRiddles(); }
function checkForChallenges(){ if(!loggedIn||!user) return; fetch('/api/player?name='+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){ var ns=(d&&d.notifs)||[]; for(var i=ns.length-1;i>=0;i--){ if(ns[i].type==='challenge'&&ns[i].challenge_id){ showChallengePopup(ns[i].from||'Player',ns[i].game||'Galaxy Shooter',ns[i].challenge_id); break; } } if(ns.length>0){ var b=document.getElementById('notifBadge'); if(b){ b.innerText=ns.length; b.classList.remove('hidden'); } } }); }
setInterval(function(){ if(loggedIn) checkForChallenges(); },10000);
function P(s){ var p=s.split('|'); return {q:p[0],a:p[1]}; }
var BANK_RIDDLE_GENERAL=["What has keys but cannot open locks?|A piano","What has a face and two hands but no arms?|A clock","What gets wetter the more it dries?|A towel","What has a neck but no head?|A bottle","What runs but never walks?|Water","What has many teeth but cannot bite?|A comb","What can you catch but never throw?|A cold","What has a bed but never sleeps?|A river","What has one eye but cannot see?|A needle","I speak without a mouth, hear without ears, what am I?|An echo"].map(P);
var BANK_RIDDLE_LOVE=["What grows stronger when shared?|Love","What is blind but sees the heart?|Love","What beats but is not a drum?|Heart","What do you give without losing?|A kiss","What makes two become one?|Love","What is sweetest when true?|Love","What never dies if true?|True love","What makes time fly?|Love","What is the language of the heart?|Love","What heals a broken heart?|Time and love"].map(P);
var BANK_RIDDLE_PROGRAMMERS=["What runs without legs?|Code","What has bugs but is not an insect?|Software","What do you debug?|Code","What language has no words?|Python","What is 0 and 1?|Binary","What do you push to GitHub?|Code","What loops forever if you forget to stop it?|Infinite loop","What is a variable?|A container for data","What does HTML stand for?|HyperText Markup Language","What do programmers drink?|Coffee"].map(P);
var BANK_RIDDLE_SMART=["What comes once in a minute, twice in a moment, never in 1000 years?|The letter M","What has 13 hearts but no organs?|A deck of cards","What can fill a room without taking space?|Light","What gets bigger the more you take away?|A hole","What is always coming but never arrives?|Tomorrow","What has hands but cannot clap?|A clock","What is black when clean, white when dirty?|A blackboard","What can you break without touching?|A promise","What goes up but never down?|Your age","What has a head and tail but no body?|A coin"].map(P);
var BANK_RIDDLE_FUNNY=["Why did the chicken cross the road?|To get to the other side","What do you call a fish without eyes?|A fsh","Why did the scarecrow win an award?|He was outstanding in his field","What do you call cheese that is not yours?|Nacho cheese","Why did the math book look sad?|Too many problems","What do cows read?|Cattle-logs","Why did the banana go to the doctor?|It was not peeling well","What do you call a sleeping bull?|A bulldozer","Why did the bicycle fall?|It was two-tired","What do you call a fake noodle?|An impasta"].map(P);
var BANK_BIBLE_OLD=["Who built the ark?|Noah","Who was swallowed by a great fish?|Jonah","Abraham's wife?|Sarah","Who penned most Psalms?|David","Who led Israel out of Egypt?|Moses","Who killed Goliath?|David","Who was thrown into the lions den?|Daniel","Who built the Temple in Jerusalem?|Solomon","First man created?|Adam","Who received the Ten Commandments?|Moses"].map(P);
var BANK_BIBLE_NEW=["First book of New Testament?|Matthew","Mother of Jesus?|Mary","Who betrayed Jesus for 30 silver?|Judas Iscariot","Shortest verse?|Jesus wept","River where Jesus was baptized?|Jordan River","Who wrote Revelation?|John","How many books in Protestant Bible?|66","Who was Paul before conversion?|Saul","Where was Jesus born?|Bethlehem","Who denied Jesus three times?|Peter"].map(P);
var BANK_BIBLE_STORIES=["Story of the lost sheep teaches what?|God seeks the lost","Story of David and Goliath teaches what?|Faith beats giants","Story of Noah teaches what?|Obedience saves","Story of Jonah teaches what?|Obedience to God","Story of the Good Samaritan teaches what?|Love your neighbour","Story of Daniel teaches what?|Faith under pressure","Story of Joseph teaches what?|Forgiveness","Story of Moses teaches what?|Deliverance","Story of Ruth teaches what?|Loyalty","Story of Esther teaches what?|Courage"].map(P);
var currentMode='',currentCat='',qIndex=0,qList=[],correctCount=0,roundGold=0;
function buildOptions(correct,allAns){ var opts=[correct]; var pool=allAns.filter(function(a){return a!==correct}); for(var i=pool.length-1;i>0;i--){var j=(Math.random()*(i+1))|0;var t=pool[i];pool[i]=pool[j];pool[j]=t} for(var k=0;k<pool.length&&opts.length<3;k++){ if(opts.indexOf(pool[k])<0) opts.push(pool[k]); } while(opts.length<3) opts.push('None of these'); for(var i=opts.length-1;i>0;i--){var j=(Math.random()*(i+1))|0;var t=opts[i];opts[i]=opts[j];opts[j]=t} return {o:opts,a:opts.indexOf(correct)}; }
function pick10(bank){ var fresh=bank.filter(function(x){return seenQs.indexOf(x.q)<0}); if(fresh.length<10){ seenQs=[]; fresh=bank.slice(); } var pool=fresh.slice(); for(var i=pool.length-1;i>0;i--){var j=(Math.random()*(i+1))|0;var t=pool[i];pool[i]=pool[j];pool[j]=t} var picked=pool.slice(0,10); picked.forEach(function(x){ if(seenQs.indexOf(x.q)<0) seenQs.push(x.q); }); saveLocal(); var allAns=bank.map(function(x){return x.a}); return picked.map(function(x){ var oo=buildOptions(x.a,allAns); return {q:x.q,o:oo.o,a:oo.a}; }); }
function startQuiz(mode,cat,bank){ currentMode=mode; currentCat=cat; qList=pick10(bank); qIndex=0; correctCount=0; roundGold=0; showPage('page-game'); document.getElementById('gameTitle').innerText=(mode==='BIBLE'?'📖 BIBLE FIGHT':'🧩 RIDDLES')+' • '+cat; showQuestion(); }
function showQuestion(){ if(qIndex>=qList.length){ finishQuiz(); return; } var q=qList[qIndex]; var html='<p>Question '+(qIndex+1)+' / 10 • Correct: '+correctCount+'</p><h3>'+q.q+'</h3>'; q.o.forEach(function(opt,i){ html+='<button class="opt" onclick="answerQ('+i+')">'+opt+'</button>'; }); html+='<p style="font-size:12px;color:#ffd700">🪙 Each correct = 50-150 • Lose (&lt;6) = 0</p><button class="btn2" onclick="openShop(\''+currentMode+'\')">🛍️ Shop — 100 Products</button>'; document.getElementById('gameBody').innerHTML=html; }
function answerQ(i){ var q=qList[qIndex]; if(i===q.a){ correctCount++; var amt=Math.floor(Math.random()*101)+50; roundGold+=amt; playWin(); toast('✅ Correct! +'+amt+' (pending)'); } else { playLose(); toast('❌ Wrong! Correct: '+q.o[q.a]); } qIndex++; setTimeout(showQuestion,800); }
function finishQuiz(){ var isWin=correctCount>=6; var finalGold=isWin?roundGold:0; var finalGems=isWin?Math.floor(finalGold/10):0; var html='<div style="text-align:center"><div style="font-size:60px">'+(isWin?'🏆':'💔')+'</div><h2>'+(isWin?'YOU WIN!':'YOU LOSE')+'</h2><p>Correct: '+correctCount+' / 10</p>'; if(isWin) html+='<p style="font-size:20px;color:#ffd700">🪙 '+finalGold+' Gold<br>💎 '+finalGems+' Germ</p>'; else html+='<p style="color:#ff6666">Lose = 0 Gold / 0 Germ</p>'; html+='<button class="btn" onclick="goDash()">🏠 Dashboard</button></div>'; document.getElementById('gameBody').innerHTML=html; if(isWin){ myGold+=finalGold; myGems+=finalGems; wins++; } else { losses++; } saveLocal(); syncScore(); loadLeader(); }
function openRiddles(){ showPage('page-game'); document.getElementById('gameTitle').innerText='🧩 RIDDLES • Choose Difficulty'; document.getElementById('gameBody').innerHTML='<h3>Pick Category — EASY or HARD</h3><p style="font-size:12px">HARD = 15 Qs, 15 sec each</p><button class="opt" onclick="startQuiz(\'RIDDLE\',\'General\',BANK_RIDDLE_GENERAL)">🧩 General — EASY</button><button class="opt" onclick="startHardQuiz(\'RIDDLE\',\'General HARD\',BANK_RIDDLE_GENERAL)">🔥 General — HARD</button><button class="opt" onclick="startQuiz(\'RIDDLE\',\'Love\',BANK_RIDDLE_LOVE)">💖 Love — EASY</button><button class="opt" onclick="startHardQuiz(\'RIDDLE\',\'Love HARD\',BANK_RIDDLE_LOVE)">🔥 Love — HARD</button><button class="opt" onclick="startQuiz(\'RIDDLE\',\'Programmers\',BANK_RIDDLE_PROGRAMMERS)">💻 Programmers — EASY</button><button class="opt" onclick="startHardQuiz(\'RIDDLE\',\'Programmers HARD\',BANK_RIDDLE_PROGRAMMERS)">🔥 Programmers — HARD</button><button class="opt" onclick="startQuiz(\'RIDDLE\',\'Smart\',BANK_RIDDLE_SMART)">🧠 Smart — EASY</button><button class="opt" onclick="startHardQuiz(\'RIDDLE\',\'Smart HARD\',BANK_RIDDLE_SMART)">🔥 Smart — HARD</button><button class="opt" onclick="startQuiz(\'RIDDLE\',\'Funny\',BANK_RIDDLE_FUNNY)">😂 Funny — EASY</button><button class="opt" onclick="startHardQuiz(\'RIDDLE\',\'Funny HARD\',BANK_RIDDLE_FUNNY)">🔥 Funny — HARD</button><button class="btn2" onclick="openShop(\'Riddles\')">🛍️ Mega Shop 100</button>'; }
function openBible(){ showPage('page-game'); document.getElementById('gameTitle').innerText='📖 BIBLE FIGHT • Choose Difficulty'; document.getElementById('gameBody').innerHTML='<h3>Pick Category</h3><button class="opt" onclick="startQuiz(\'BIBLE\',\'Old Testament\',BANK_BIBLE_OLD)">📜 Old Testament — EASY</button><button class="opt" onclick="startHardQuiz(\'BIBLE\',\'Old HARD\',BANK_BIBLE_OLD)">🔥 Old Testament — HARD</button><button class="opt" onclick="startQuiz(\'BIBLE\',\'New Testament\',BANK_BIBLE_NEW)">✝️ New Testament — EASY</button><button class="opt" onclick="startHardQuiz(\'BIBLE\',\'New HARD\',BANK_BIBLE_NEW)">🔥 New Testament — HARD</button><button class="opt" onclick="startQuiz(\'BIBLE\',\'Stories\',BANK_BIBLE_STORIES)">📖 Stories — EASY</button><button class="opt" onclick="startHardQuiz(\'BIBLE\',\'Stories HARD\',BANK_BIBLE_STORIES)">🔥 Stories — HARD</button><button class="btn2" onclick="openShop(\'Bible\')">🛍️ Mega Shop 100</button>'; }
function openSciFi(){ if(new Date()<new Date(2026,11,25)){ showPage('page-coming'); var cd=document.getElementById('countDown'); if(cd) cd.innerText='5'; setTimeout(function(){ goDash(); },5000); return; } openMenuPage(); }
// --- 100 SHOP PRODUCTS ---
function fmtPrice(p){ if(p>=1000000000000) return (p/1000000000000)+' Trillion'; if(p>=1000000000) return (p/1000000000)+' Billion'; if(p>=1000000) return (p/1000000)+' Million'; if(p>=1000) return (p/1000)+'K'; return p+''; }
function buildShopItems(){
  var names=['⚡ Power Boost','🛡️ Shield','💎 Double Gold','👑 Bronze Crown','🚀 Speed Boost','🔥 Fire Power','🧪 XP Potion','🎯 Aim Assist','🪖 Galaxy Helmet','⚔️ Laser Sword','🛸 Mini UFO','👑 Silver Crown','💎 Gem Pack','🏰 Mini Castle','🦁 Lion Pet','🐉 Dragon Pet','👑 Gold Crown','🚀 SpaceX Rocket','🌌 Galaxy Pass','💎 Diamond Vault','🏆 Champion Trophy','👑 Platinum Crown','🪐 Planet Owner','💰 Billionaire Vault','🌟 Star Empire','👑 King of Infinity','🚀 SpaceX Fleet','🏰 Infinity Castle','💎 Godly Gem','👑 GODLY CROWN','⚡ Mega Boost','🛡️ Titan Shield','🔥 Inferno Blade','🧊 Ice Shield','🌪️ Storm Power','💜 Void Crystal','🖤 Dark Crown','🤍 Light Crown','🦅 Phoenix','🐺 Wolf Pet','🐯 Tiger Pet','🦄 Unicorn','👽 Alien Pet','🤖 Robot Helper','👾 Alien Blaster','🎮 Pro Controller','🕶️ Galaxy Glasses','🧢 Infinity Cap','👕 Infinity Shirt','👟 Speed Shoes','⌚ Time Watch','📱 Galaxy Phone','💻 Hacking Laptop','🎧 Music Boost','🎸 Rock Guitar','🎤 Mic Star','🏀 Star Ball','⚽ Galaxy Ball','🎯 Sniper Scope','🏹 Galaxy Bow','🗡️ Shadow Blade','🔮 Magic Orb','🧿 Evil Eye','🪄 Magic Wand','📚 Wisdom Book','🎓 Genius Hat','🏅 Gold Medal','🥇 Champion Medal','🎖️ Hero Badge','🏆 Infinity Trophy','💰 Money Magnet','🧲 Gold Magnet','🔑 Vault Key','🗝️ Secret Key','🔓 Unlock All','🚁 Galaxy Copter','✈️ Galaxy Jet','🚢 Star Ship','🚀 Mega Rocket','🛰️ Satellite','🌙 Moon Base','☀️ Sun Power','⭐ Super Star','🌟 Mega Star','💫 Shooting Star','🌠 Comet Power','🪐 Saturn Ring','🌍 Earth Owner','🌎 World Owner','🌏 Universe Owner','♾️ Infinity Stone','💎 Infinity Gem','👑 Emperor Crown','🤴 King Crown','👸 Queen Crown','🧝 Elf Power','🧙 Wizard Power','🦸 Super Hero','🦹 Villain Power','👼 Angel Wings','😈 Demon Power','🧞 Genie Lamp','🎁 Mystery Box','🪙 Gold Mine','🏦 Gold Bank','💳 Infinity Card','🔱 Trident','⚜️ Royal Emblem','🏛️ Infinity Palace','🌋 Volcano Power'];
  var items=[]; var price=200;
  for(var i=0;i<100;i++){ var nm=names[i]||('🎁 Product '+(i+1)); items.push([nm, price]); if(price<1000) price*=2; else if(price<1000000) price=Math.floor(price*2.2); else if(price<1000000000) price=Math.floor(price*2.5); else price=Math.floor(price*1.8); if(price>1000000000000) price=1000000000000; }
  items[99]=['👑 GODLY CROWN — 1 TRILLION',1000000000000];
  return items;
}
var SHOP_ITEMS=buildShopItems();
function openShop(game){ showPage('page-game'); document.getElementById('gameTitle').innerText='🛍️ SHOP - '+game+' • 100 PRODUCTS'; var h='<p>Your Gold: 🪙 '+myGold+' | PIN required • Scroll for all 100</p><p style="font-size:12px;color:#ffd700">Products 1-100: 200 Gold → 1 Trillion Gold</p>'; SHOP_ITEMS.forEach(function(it,idx){ h+='<div class="shopItem"><span><b>#'+(idx+1)+'</b> '+it[0]+'<br><small>🪙 '+fmtPrice(it[1])+' Gold</small></span><button class="btn" style="width:auto;padding:10px 16px" onclick="buyItem(\''+it[0].replace(/'/g,'')+'\','+it[1]+')">BUY</button></div>'; }); h+='<button class="btn2" onclick="goDash()">← Back</button>'; document.getElementById('gameBody').innerHTML=h; }
function buyItem(name,price){ openPin('Enter PIN to buy '+name+' for '+fmtPrice(price)+' Gold',function(pin){ fetch('/api/buy_item',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:user.name,pin:pin,item:name,price:price})}).then(function(r){return r.json()}).then(function(d){ if(d.error){ toast('⚠️ '+d.error); return; } myGold=d.gold; saveLocal(); toast('✅ Purchase confirmed: '+name); playWin(); }); }); }
// HARD QUIZ
var hardTimer=null, hardTimeLeft=15;
function startHardQuiz(mode,cat,bank){ currentMode=mode; currentCat=cat; qList=pick15(bank); qIndex=0; correctCount=0; roundGold=0; showPage('page-game'); document.getElementById('gameTitle').innerText='🔥 HARD • '+(mode==='BIBLE'?'📖 BIBLE FIGHT':'🧩 RIDDLES')+' • '+cat+' • 15 Qs • 15s each'; showHardQuestion(); }
function pick15(bank){ var fresh=bank.concat(bank).filter(function(x){return seenQs.indexOf(x.q+'-hard')<0}); if(fresh.length<15){ seenQs=[]; fresh=bank.concat(bank); } var pool=fresh.slice(); for(var i=pool.length-1;i>0;i--){var j=(Math.random()*(i+1))|0;var t=pool[i];pool[i]=pool[j];pool[j]=t} var picked=pool.slice(0,15); picked.forEach(function(x){ seenQs.push(x.q+'-hard'); }); saveLocal(); var allAns=bank.map(function(x){return x.a}); return picked.map(function(x){ var oo=buildOptions(x.a,allAns); return {q:x.q,o:oo.o,a:oo.a}; }); }
function showHardQuestion(){ if(qIndex>=qList.length){ finishHardQuiz(); return; } var q=qList[qIndex]; hardTimeLeft=15; var html='<p>🔥 HARD Question '+(qIndex+1)+' / 15 • ⏱️ <b id="hardTimerTxt">15s</b> • Correct: '+correctCount+'</p><h3>'+q.q+'</h3>'; q.o.forEach(function(opt,i){ html+='<button class="opt" onclick="answerHardQ('+i+')"> '+opt+'</button>'; }); html+='<p style="font-size:12px;color:#ffd700">HARD: 15 sec only! Each correct 50-150</p><button class="btn2" onclick="openShop(\'Hard Game\')">🛍️ Shop 100</button>'; document.getElementById('gameBody').innerHTML=html; if(hardTimer) clearInterval(hardTimer); hardTimer=setInterval(function(){ hardTimeLeft--; var el=document.getElementById('hardTimerTxt'); if(el) el.innerText=hardTimeLeft+'s'; if(hardTimeLeft<=0){ clearInterval(hardTimer); toast('⏰ Time up!'); qIndex++; showHardQuestion(); } },1000); }
function answerHardQ(i){ if(hardTimer) clearInterval(hardTimer); var q=qList[qIndex]; if(i===q.a){ correctCount++; var amt=Math.floor(Math.random()*101)+50; roundGold+=amt; playWin(); toast('✅ Correct! +'+amt); } else { playLose(); toast('❌ Wrong! Correct: '+q.o[q.a]); } qIndex++; setTimeout(showHardQuestion,600); }
function finishHardQuiz(){ var isWin=correctCount>=10; var finalGold=isWin?roundGold:0; var finalGems=isWin?Math.floor(finalGold/10):0; var html='<div style="text-align:center"><div style="font-size:60px">'+(isWin?'🏆':'💔')+'</div><h2>'+(isWin?'HARD WIN!':'HARD LOSE')+'</h2><p>Correct: '+correctCount+' / 15</p><p>'+(isWin?'🪙 '+finalGold+' • 💎 '+finalGems:'Lose = 0')+'</p><button class="btn" onclick="goDash()">🏠 Dashboard</button></div>'; document.getElementById('gameBody').innerHTML=html; if(isWin){ myGold+=finalGold; myGems+=finalGems; wins++; } else losses++; saveLocal(); syncScore(); }
function renderMenuGames(){ var games=[['🌌','Galaxy Shooter','HARD: 20 aliens','openGalaxyShooterHard()'],['💻','Decoding / Hacking','HARD: 12-char code, 60s','openDecodingGame()'],['👽','Alien Riddles','HARD 15 Qs','openHardAlien()'],['🧩','Code Breaker','HARD: 15 Qs','openCodeBreakerHard()'],['🧠','Space Memory','HARD: 15 Qs','openMemoryHard()'],['🔢','Laser Math','HARD: 15 Qs','openLaserMathHard()'],['🧩','Cyber Puzzle','HARD','openCyberHard()'],['⭐','Star Trader','HARD','openStarTraderHard()'],['🤖','AI Quiz Battle','HARD vs AI','openAIHard()'],['🚀','Robot Racer','HARD race','openRobotRacerHard()']]; var html=''; games.forEach(function(g){ html+='<div style="background:linear-gradient(160deg,#1a0033,#2b005e);border:2px solid #ffd700;border-radius:22px;padding:16px;margin:10px 0;cursor:pointer" onclick="'+g[3]+'"><div style="font-size:36px">'+g[0]+'</div><h3>'+g[1]+'</h3><p style="font-size:13px;opacity:.8">'+g[2]+'</p><button class="btn2">▶ PLAY HARD • 🛍️ Shop 100 inside</button></div>'; }); document.getElementById('menuGamesList').innerHTML=html; }
function openGalaxyShooterHard(){ showPage('page-game'); document.getElementById('gameTitle').innerText='🌌 GALAXY SHOOTER • HARD'; window.shootHits=0; window.shootGold=0; document.getElementById('gameBody').innerHTML='<div style="text-align:center"><div style="font-size:60px">🌌🚀👾</div><p>HARD: Destroy 20 aliens! Each hit 50-150</p><div style="font-size:60px;cursor:pointer" id="alienTarget" onclick="shootAlienHard()">👾</div><p>Hits: <b id="shootHits">0</b>/20 • Gold: <b id="shootGold">0</b></p><button class="btn" onclick="tagPlayerForChallenge()">🏷️ Tag Player to Challenge</button><button class="btn2" onclick="openShop(\'Galaxy Shooter\')">🛍️ Shop 100</button></div>'; }
function shootAlienHard(){ window.shootHits++; var amt=Math.floor(Math.random()*101)+50; window.shootGold+=amt; document.getElementById('shootHits').innerText=window.shootHits; document.getElementById('shootGold').innerText=window.shootGold; var a=['👾','👽','🛸','🌟','☄️','👹']; document.getElementById('alienTarget').innerText=a[Math.floor(Math.random()*a.length)]; playClick(); if(window.shootHits>=20){ var gold=window.shootGold; var gems=Math.floor(gold/10); myGold+=gold; myGems+=gems; wins++; saveLocal(); syncScore(); playWin(); document.getElementById('gameBody').innerHTML='<div style="text-align:center"><h2>🏆 HARD WIN!</h2><p>🪙 '+gold+' • 💎 '+gems+'</p><button class="btn" onclick="goDash()">🏠 Dashboard</button></div>'; } }
var hackTarget='',hackInput='';
function openDecodingGame(){ hackTarget='INFINITY'+Math.floor(Math.random()*9000+1000); hackInput=''; showPage('page-game'); document.getElementById('gameTitle').innerText='💻 DECODING • HARD'; document.getElementById('gameBody').innerHTML='<div style="text-align:center"><div style="background:#000;color:#00ff00;font-family:monospace;padding:14px;border-radius:16px;border:2px solid #00ff00;text-align:left">> HACKING FAKE ACCOUNT...<br>> HINT: '+hackTarget.length+' chars, starts INFINITY<br>> INPUT: <span id="hackInputShow"></span>_</div><div id="hackKeyboard" style="margin:10px 0"></div><button class="btn" onclick="checkHack()">🔓 HACK NOW</button><button class="btn2" onclick="openShop(\'Decoding\')">🛍️ Shop 100</button></div>'; var keys='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'; var kh=''; keys.split('').forEach(function(k){ kh+='<button style="width:44px;height:48px;margin:3px;border-radius:10px;border:2px solid #00ffaa;background:#001a12;color:#00ffaa;font-weight:900" onclick="pressHackKey(\''+k+'\')">'+k+'</button>'; }); kh+='<button style="width:70px;height:48px" onclick="backHack()">⌫</button>'; document.getElementById('hackKeyboard').innerHTML=kh; }
function pressHackKey(k){ hackInput+=k; document.getElementById('hackInputShow').innerText=hackInput; }
function backHack(){ hackInput=hackInput.slice(0,-1); document.getElementById('hackInputShow').innerText=hackInput; }
function checkHack(){ if(hackInput===hackTarget){ var gold=Math.floor(Math.random()*101)+500; var gems=Math.floor(gold/10); myGold+=gold; myGems+=gems; wins++; saveLocal(); syncScore(); playWin(); document.getElementById('gameBody').innerHTML='<div style="text-align:center"><h2>✅ HACK SUCCESS!</h2><p>🪙 +'+gold+' • 💎 +'+gems+'</p><button class="btn" onclick="goDash()">🏠 Dashboard</button></div>'; } else { losses++; saveLocal(); playLose(); document.getElementById('gameBody').innerHTML='<div style="text-align:center"><h2>❌ HACK FAILED</h2><p>Target was '+hackTarget+'</p><p>Lose = 0</p><button class="btn" onclick="openDecodingGame()">🔁 Try Again</button></div>'; } }
function openHardAlien(){ startHardQuiz('RIDDLE','Alien HARD',BANK_RIDDLE_GENERAL); }
function openCodeBreakerHard(){ startHardQuiz('RIDDLE','Code Breaker HARD',BANK_RIDDLE_SMART); }
function openMemoryHard(){ startHardQuiz('RIDDLE','Memory HARD',BANK_RIDDLE_SMART); }
function openLaserMathHard(){ startHardQuiz('RIDDLE','Laser Math HARD',BANK_RIDDLE_SMART); }
function openCyberHard(){ startHardQuiz('RIDDLE','Cyber HARD',BANK_RIDDLE_PROGRAMMERS); }
function openStarTraderHard(){ startHardQuiz('RIDDLE','Star Trader HARD',BANK_RIDDLE_GENERAL); }
function openAIHard(){ startHardQuiz('BIBLE','AI HARD',BANK_BIBLE_NEW); }
function openRobotRacerHard(){ startHardQuiz('RIDDLE','Robot Racer HARD',BANK_RIDDLE_FUNNY); }
// WHATSAPP
var chatWithName='', callInterval=null, callSecs=0, mediaRecorder=null, voiceChunks=[];
function openMessages(){ if(!loggedIn) return; showPage('page-messages'); fetch('/api/friends?name='+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){ var html=''; (d.friends||[]).forEach(function(f){ html+='<div style="display:flex;justify-content:space-between;align-items:center;padding:12px;background:rgba(0,0,0,.45);border-radius:16px;margin:8px 0"><span>👤 '+f.name+'<br><small>'+f.player_id+' • ⭐ '+f.rank+'</small></span><button class="btn" style="width:auto;padding:10px 16px" onclick="openChat(\''+f.name+'\')">💬 Chat</button></div>'; }); if(!html) html='<p>No friends yet — add by ID above</p>'; document.getElementById('chatFriendList').innerHTML=html; }); }
function addFriendById(){ var d=document.getElementById('addFriendDigits').value.replace(/[^0-9]/g,''); if(d.length<8){ toast('Enter 8 digits'); return; } fetch('/api/add_friend',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:user.name,target_id:'INF-'+d})}).then(function(r){return r.json()}).then(function(dd){ if(dd.error){ toast('⚠️ '+dd.error); return; } toast('✅ Friend added!'); openMessages(); }); }
function openChat(name){ chatWithName=name; showPage('page-chat'); document.getElementById('chatWith').innerText=name; loadChat(); }
function loadChat(){ if(!chatWithName) return; fetch('/api/chat_get?a='+encodeURIComponent(user.name)+'&b='+encodeURIComponent(chatWithName)).then(function(r){return r.json()}).then(function(d){ var html=''; (d.messages||[]).forEach(function(m){ var mine=m.from===user.name; html+='<div style="max-width:80%;padding:10px 14px;border-radius:18px;margin:6px 0;font-size:14px;'+(mine?'background:#ffd700;color:#000;margin-left:auto':'background:rgba(255,255,255,.2)')+'">'+(m.kind==='voice'?'🎙️ Voice Note 🔊':m.text)+'<br><small style="opacity:.7">'+(m.time||'')+'</small></div>'; }); document.getElementById('chatBox').innerHTML=html||'No messages yet — say hi!'; document.getElementById('chatBox').scrollTop=99999; }); }
function sendMsg(){ var txt=document.getElementById('msgInput').value.trim(); if(!txt) return; fetch('/api/chat_send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sender:user.name,to:chatWithName,text:txt,kind:'text'})}).then(function(){ document.getElementById('msgInput').value=''; playClick(); loadChat(); }); }
function startVoiceCall(){ var b=document.getElementById('callBanner'); b.classList.remove('hidden'); callSecs=0; document.getElementById('callTimer').innerText='00:00'; if(callInterval) clearInterval(callInterval); callInterval=setInterval(function(){ callSecs++; var m=String(Math.floor(callSecs/60)).padStart(2,'0'); var s=String(callSecs%60).padStart(2,'0'); document.getElementById('callTimer').innerText=m+':'+s; },1000); toast('📞 Calling '+chatWithName+'...'); beep(880,300); }
function endVoiceCall(){ if(callInterval) clearInterval(callInterval); document.getElementById('callBanner').classList.add('hidden'); toast('📞 Call ended — '+callSecs+' sec'); fetch('/api/chat_send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sender:user.name,to:chatWithName,text:'📞 Voice Call — '+callSecs+' seconds',kind:'text'})}).then(function(){ loadChat(); }); }
function toggleVoiceNote(){ if(mediaRecorder && mediaRecorder.state==='recording'){ mediaRecorder.stop(); toast('🎙️ Voice note sent!'); return; } try{ navigator.mediaDevices.getUserMedia({audio:true}).then(function(stream){ mediaRecorder=new MediaRecorder(stream); voiceChunks=[]; mediaRecorder.ondataavailable=function(e){ voiceChunks.push(e.data); }; mediaRecorder.onstop=function(){ fetch('/api/chat_send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sender:user.name,to:chatWithName,text:'🎙️ Voice Note',kind:'voice'})}).then(function(){ loadChat(); }); }; mediaRecorder.start(); toast('🎙️ Recording... Tap again to send'); beep(1200,200); }).catch(function(){ fetch('/api/chat_send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sender:user.name,to:chatWithName,text:'🎙️ Voice Note — (mic blocked)',kind:'voice'})}).then(function(){ loadChat(); toast('🎙️ Voice note sent'); }); }); }catch(e){ toast('🎙️ Voice note sent'); } }
setInterval(function(){ if(currentPage==='page-chat' && chatWithName) loadChat(); },5000);
setInterval(function(){ if(loggedIn&&user) syncScore(); },15000);
window.onload=function(){ if(user&&user.name) document.getElementById('regSub').innerText='Welcome back! Please Login 👑'; };
</script></body></html>
"""
if __name__=="__main__":
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
