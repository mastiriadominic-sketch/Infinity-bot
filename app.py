from flask import Flask, request, jsonify
import os, requests, time, datetime, json, threading, random
app = Flask(__name__)
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN","infinity")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN","")
PHONE_ID = os.environ.get("PHONE_NUMBER_ID","")
BASE = os.path.dirname(__file__)
LEADER_FILE = os.path.join(BASE, "leaderboard.json")
BACKUP1 = os.path.join(BASE, "leaderboard.json.backup")
BACKUP2 = os.path.join(BASE, "backup_storage.json")
MSG_FILE = os.path.join(BASE, "messages.json")
MSG_BACKUP = os.path.join(BASE, "messages.json.backup")
USERS = {}
MESSAGES = {}
CHALLENGES = {}
_lock = threading.Lock()
EARNING_ON = True
EARNING_START = datetime.datetime(2026,12,25,0,0,0)
def norm(n): return str(n or "").strip().lower()
def load_json_safe(path):
    try:
        if os.path.exists(path):
            with open(path,"r") as f:
                d=json.load(f)
                if isinstance(d,dict): return d
    except: pass
    return {}
def gen_id(): return "INF-" + "".join([str(random.randint(0,9)) for _ in range(8)])
def gen_bank_id(): return "Bank INF-" + "".join([str(random.randint(0,9)) for _ in range(10)])
def ensure_player(v,k):
    if "display_name" not in v: v["display_name"]=k
    if "history" not in v: v["history"]={}
    if "friends" not in v: v["friends"]=[]
    if "requests" not in v: v["requests"]=[]
    if "wins" not in v: v["wins"]=0
    if "losses" not in v: v["losses"]=0
    if "stage" not in v: v["stage"]=0
    if "gold" not in v: v["gold"]=0
    if "gems" not in v: v["gems"]=0
    if "player_id" not in v or not v["player_id"]: v["player_id"]=gen_id()
    if "bank_id" not in v or not v["bank_id"]: v["bank_id"]=gen_bank_id()
    if "notifs" not in v: v["notifs"]=[]
    if "seen_qs" not in v: v["seen_qs"]=[]
    return v
def load_users():
    global USERS
    for p in [LEADER_FILE, BACKUP1, BACKUP2]:
        d=load_json_safe(p)
        if d:
            new={}
            for k,v in d.items():
                nk=norm(v.get("display_name",k) or k)
                v["display_name"]=v.get("display_name",k)
                new[nk]=ensure_player(v,k)
            USERS=new; return
def load_messages():
    global MESSAGES
    for p in [MSG_FILE, MSG_BACKUP]:
        d=load_json_safe(p)
        if d: MESSAGES=d; return
def save_users():
    try:
        with _lock:
            data=json.dumps(USERS)
            for p in [LEADER_FILE, BACKUP1, BACKUP2]:
                with open(p,"w") as f: f.write(data)
    except: pass
def save_messages():
    try:
        with _lock:
            data=json.dumps(MESSAGES)
            for p in [MSG_FILE, MSG_BACKUP]:
                with open(p,"w") as f: f.write(data)
    except: pass
load_users(); load_messages()
def auto_save_loop():
    while True:
        time.sleep(10)
        try: save_users(); save_messages()
        except: pass
threading.Thread(target=auto_save_loop, daemon=True).start()
def is_earning_active():
    now=datetime.datetime.now()
    if now < EARNING_START: return False
    return EARNING_ON
def get_rank(wins):
    if wins>=102400: return "Godly Rank Classified"
    if wins>=51200: return "SSS Classified"
    if wins>=25600: return "SSS Rank"
    if wins>=12800: return "SS Rank"
    if wins>=6400: return "S Rank"
    if wins>=3200: return "National"
    if wins>=1600: return "Professional"
    if wins>=800: return "Expert"
    if wins>=400: return "Advanced"
    if wins>=200: return "Intermediate"
    return "Beginner"
def is_classified(wins): return wins>=3200
@app.route("/api/earning_status")
def earning_status(): return jsonify({"earning_on":EARNING_ON,"active":is_earning_active(),"start":"2026-12-25"})
@app.route("/api/toggle_earning", methods=["POST"])
def toggle_earning():
    global EARNING_ON
    d=request.get_json() or {}
    if norm(d.get("name"))!="dominic" or str(d.get("password"))!="2164": return jsonify({"error":"Only Dominic"}),403
    EARNING_ON = not EARNING_ON
    return jsonify({"earning_on":EARNING_ON,"active":is_earning_active()})
@app.route("/api/player")
def get_player():
    n=norm(request.args.get("name","")); pw=request.args.get("password","")
    if n in USERS:
        v=USERS[n]
        if not v.get("player_id"): v["player_id"]=gen_id()
        if not v.get("bank_id"): v["bank_id"]=gen_bank_id()
        save_users()
        if pw and v.get("password") and str(v.get("password"))!=str(pw): return jsonify({"found":True,"password_ok":False,"name":v["display_name"],"player_id":v["player_id"],"bank_id":v["bank_id"]})
        return jsonify({"found":True,"password_ok":True,"name":v["display_name"],"wins":v["wins"],"losses":v["losses"],"stage":v["stage"],"gold":v["gold"],"gems":v["gems"],"player_id":v["player_id"],"bank_id":v["bank_id"],"history":v["history"],"friends":v["friends"],"notifs":v.get("notifs",[]),"seen_qs":v.get("seen_qs",[]),"rank":get_rank(v["wins"])})
    return jsonify({"found":False})
@app.route("/api/leaderboard")
def leaderboard():
    players=[]
    for k,v in USERS.items(): players.append({"name":v["display_name"],"wins":v["wins"],"losses":v["losses"],"stage":v["stage"],"gold":v.get("gold",0),"gems":v.get("gems",0),"player_id":v.get("player_id",""),"bank_id":v.get("bank_id",""),"rank":get_rank(v["wins"])})
    players=sorted(players,key=lambda x:x["wins"],reverse=True)
    return jsonify({"players":players})
@app.route("/api/score", methods=["POST"])
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
    save_users(); return jsonify({"ok":True,"gold":v["gold"],"gems":v["gems"],"player_id":v["player_id"],"bank_id":v["bank_id"]})
@app.route("/api/transfer", methods=["POST"])
def transfer():
    d=request.get_json() or {}; sender=norm(d.get("sender")); pin=str(d.get("pin","")); recv_id=str(d.get("receiver_id","")).upper(); amt=int(d.get("amount",0)); cur=d.get("currency","Gold")
    if not is_earning_active(): return jsonify({"error":"Transfers blocked - Earning is OFF by Admin"}),403
    if sender not in USERS: return jsonify({"error":"Sender not found"}),404
    s=USERS[sender]
    if str(s.get("password"))!=pin:
        s.setdefault("notifs",[]).append({"text":"⚠️ Warning! Pin is wrong, please check again or try again later.","time":str(datetime.datetime.now()),"type":"warn"}); save_users(); return jsonify({"error":"Wrong PIN"}),403
    recv=None
    for k,v in USERS.items():
        if str(v.get("player_id","")).upper()==recv_id or str(v.get("bank_id","")).upper()==recv_id: recv=v; break
    if not recv: return jsonify({"error":"Receiver ID not found - Check INF- number"}),404
    if cur=="Gold":
        if s.get("gold",0)<amt: return jsonify({"error":"Not enough Gold"}),400
        fee=int(amt*0.05); net=amt-fee; s["gold"]-=amt; recv["gold"]=recv.get("gold",0)+net
    else:
        if s.get("gems",0)<amt: return jsonify({"error":"Not enough Gems"}),400
        fee=0; net=amt; s["gems"]-=amt; recv["gems"]=recv.get("gems",0)+net
    s.setdefault("notifs",[]).append({"text":f"Dear player you have successfully sent {amt} {cur} to {recv_id}. Fee: {fee}. Thanks for your transaction.","time":str(datetime.datetime.now()),"type":"send"})
    recv.setdefault("notifs",[]).append({"text":f"Dear {recv['display_name']} you have received {net} {cur} from {s.get('player_id')}. Thank you.","time":str(datetime.datetime.now()),"type":"receive"})
    save_users(); return jsonify({"ok":True,"sent":amt,"fee":fee,"net":net,"sender_gold":s["gold"],"sender_gems":s["gems"]})
@app.route("/api/withdraw", methods=["POST"])
def withdraw():
    d=request.get_json() or {}; n=norm(d.get("name")); pin=str(d.get("pin","")); amt=int(d.get("amount",0)); cur=d.get("currency","Gold")
    if not is_earning_active(): return jsonify({"error":"Withdrawals blocked - Earning is OFF"}),403
    if n not in USERS: return jsonify({"error":"Not found"}),404
    v=USERS[n]
    if str(v.get("password"))!=pin:
        v.setdefault("notifs",[]).append({"text":"⚠️ Warning! Pin is wrong, please check again or try again later.","time":str(datetime.datetime.now()),"type":"warn"}); save_users(); return jsonify({"error":"Wrong PIN"}),403
    if cur=="Gold":
        if v.get("gold",0)<amt: return jsonify({"error":"Not enough Gold"}),400
        v["gold"]-=amt
    else:
        if v.get("gems",0)<amt: return jsonify({"error":"Not enough Gems"}),400
        v["gems"]-=amt
    v.setdefault("notifs",[]).append({"text":f"Dear player you have successfully withdrawn {amt} {cur} to your Gold/Gems account. Thanks for your transaction.","time":str(datetime.datetime.now()),"type":"withdraw"})
    save_users(); return jsonify({"ok":True,"gold":v["gold"],"gems":v["gems"]})
@app.route("/api/deposit", methods=["POST"])
def deposit():
    d=request.get_json() or {}; n=norm(d.get("name")); pin=str(d.get("pin","")); amt=int(d.get("amount",0)); target_id=str(d.get("target_id","")).upper()
    if n not in USERS: return jsonify({"error":"Not found"}),404
    v=USERS[n]
    if str(v.get("password"))!=pin: return jsonify({"error":"Wrong PIN"}),403
    target=v
    if target_id:
        for k,x in USERS.items():
            if str(x.get("player_id","")).upper()==target_id or str(x.get("bank_id","")).upper()==target_id: target=x; break
        else: return jsonify({"error":"Target Bank ID not found"}),404
    # Deposit = move from wallet to bank display (for demo, keep gold same, just notify)
    v.setdefault("notifs",[]).append({"text":f"Dear player you have successfully deposited {amt} Gold into {target.get('bank_id')} bank account. Thanks.","time":str(datetime.datetime.now()),"type":"deposit"})
    if target is not v: target.setdefault("notifs",[]).append({"text":f"Dear {target['display_name']} you received a deposit of {amt} Gold from {v['display_name']}.","time":str(datetime.datetime.now()),"type":"deposit"})
    save_users(); return jsonify({"ok":True})
@app.route("/api/exchange", methods=["POST"])
def exchange():
    d=request.get_json() or {}; n=norm(d.get("name")); pin=str(d.get("pin","")); amt=int(d.get("amount",0)); direction=d.get("direction","gold_to_gem")
    if n not in USERS: return jsonify({"error":"Not found"}),404
    v=USERS[n]
    if str(v.get("password"))!=pin: return jsonify({"error":"Wrong PIN"}),403
    if direction=="gold_to_gem":
        if v.get("gold",0)<amt: return jsonify({"error":"Not enough Gold"}),400
        gems=amt//100; v["gold"]-=amt; v["gems"]=v.get("gems",0)+gems
        v.setdefault("notifs",[]).append({"text":f"✅ Exchanged {amt} Gold → {gems} Gems. Rate 100 Gold = 1 Gem.","time":str(datetime.datetime.now()),"type":"exchange"})
    else:
        if v.get("gems",0)<amt: return jsonify({"error":"Not enough Gems"}),400
        gold=amt*100; v["gems"]-=amt; v["gold"]=v.get("gold",0)+gold
        v.setdefault("notifs",[]).append({"text":f"✅ Exchanged {amt} Gems → {gold} Gold. Rate 1 Gem = 100 Gold.","time":str(datetime.datetime.now()),"type":"exchange"})
    save_users(); return jsonify({"ok":True,"gold":v["gold"],"gems":v["gems"]})
@app.route("/api/challenge_send", methods=["POST"])
def challenge_send():
    d=request.get_json() or {}; sender=norm(d.get("sender")); target_id=str(d.get("target_id","")).upper(); game=d.get("game","Galaxy Shooter")
    if sender not in USERS: return jsonify({"error":"Sender not found"}),404
    s=USERS[sender]; target=None
    for k,v in USERS.items():
        if str(v.get("player_id","")).upper()==target_id: target=v; break
    if not target: return jsonify({"error":"Target ID not found"}),404
    cid=f"CH-{random.randint(10000000,99999999)}"
    CHALLENGES[cid]={"from":s["display_name"],"from_id":s.get("player_id"),"to":target["display_name"],"to_id":target_id,"game":game,"status":"pending","time":str(datetime.datetime.now())}
    target.setdefault("notifs",[]).append({"text":f"🎮 CHALLENGE REQUEST: {s['display_name']} ({s.get('player_id')}) challenged you to {game}!","time":str(datetime.datetime.now()),"type":"challenge","challenge_id":cid,"game":game,"from":s["display_name"]})
    save_users(); return jsonify({"ok":True,"challenge_id":cid})
@app.route("/api/challenge_respond", methods=["POST"])
def challenge_respond():
    d=request.get_json() or {}; cid=d.get("challenge_id"); accept=d.get("accept",False)
    if cid in CHALLENGES: CHALLENGES[cid]["status"]="accepted" if accept else "declined"; return jsonify({"ok":True,"status":CHALLENGES[cid]["status"]})
    return jsonify({"error":"Not found"}),404
@app.route("/api/review", methods=["POST"])
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
    return jsonify({"players":len(USERS),"earning_on":EARNING_ON,"earning_active":is_earning_active(),"reviews":reviews,"challenges":list(CHALLENGES.values())})
@app.route("/api/answer", methods=["POST"])
def answer():
    d=request.get_json() or {}; n=norm(d.get("name"))
    if n in USERS:
        h=USERS[n].setdefault("history",{}); q=d.get("question","")
        if q not in h: h[q]={"asked":0,"correct":0,"wrong":0}
        h[q]["asked"]+=1
        if d.get("correct"): h[q]["correct"]+=1
        else: h[q]["wrong"]+=1
        save_users()
    return jsonify({"ok":True})
HOME=r"""<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>INFINITY BOT v10 - CHRISTMAS</title>
<link href="https://fonts.googleapis.com/css2?family=Great+Vibes&family=Poppins:wght@400;700;900&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<style>*{box-sizing:border-box}body{margin:0;font-family:Poppins,Arial;color:white;background:radial-gradient(circle at 50% 20%,#3a0a5e,#12002b 70%);min-height:100vh;padding-bottom:90px}.cursive{font-family:'Great Vibes',cursive}.topbar{display:flex;justify-content:space-between;align-items:center;padding:8px 14px}.profile{width:46px;height:46px;border-radius:50%;background:linear-gradient(135deg,#ff006e,#ffd700);display:flex;align-items:center;justify-content:center;font-size:20px;border:2px solid #fff;cursor:pointer;position:relative}.notif{position:absolute;top:-6px;right:-6px;background:red;color:#fff;font-size:11px;width:20px;height:20px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:900}.center{min-height:82vh;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:20px}.crownBig{font-size:90px;filter:drop-shadow(0 0 30px gold)}.enterBtn{margin-top:20px;padding:16px 70px;font-family:'Great Vibes',cursive;font-size:48px;border:none;border-radius:60px;background:linear-gradient(90deg,#ff006e,#ffd700,#00e5ff);color:#000;box-shadow:0 0 40px #ff006e;cursor:pointer}.card{background:rgba(255,255,255,.08);border:2px solid rgba(255,255,255,.35);border-radius:26px;padding:20px;margin:14px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.box{background:linear-gradient(160deg,rgba(255,255,255,.18),rgba(0,0,0,.4));border:2px solid #fff;border-radius:24px;padding:22px 10px;text-align:center;cursor:pointer}.box span{font-size:38px;display:block}.btn{width:100%;padding:14px;border:none;border-radius:25px;font-weight:900;background:#ffd700;margin:6px 0;cursor:pointer}.btn2{width:100%;padding:13px;border-radius:25px;border:2px solid #00e5ff;background:transparent;color:#00e5ff;font-weight:900;margin:6px 0;cursor:pointer}.opt{width:100%;padding:13px;margin:7px 0;border-radius:16px;border:2px solid #fff;background:rgba(0,0,0,.5);color:#fff;font-weight:700;cursor:pointer;text-align:left}input{width:100%;padding:14px;border-radius:14px;border:2px solid #ffd700;margin:8px 0;font-size:16px;background:#fff;color:#000}.hidden{display:none}.leadRow{display:flex;justify-content:space-between;align-items:center;padding:10px 12px;background:rgba(0,0,0,.45);border-radius:14px;margin:6px 0;cursor:pointer}.badge{display:inline-block;padding:5px 10px;border-radius:20px;background:rgba(0,0,0,.5);border:1px solid #ffd700;font-size:12px;margin:3px}.toast{position:fixed;top:70px;left:50%;transform:translateX(-50%);background:#fff;color:#000;padding:12px 18px;border-radius:20px;font-weight:700;z-index:900;max-width:90%;text-align:center}.regInput{font-size:18px;text-align:center;letter-spacing:2px}.msgFab{position:fixed;right:16px;bottom:16px;width:62px;height:62px;border-radius:50%;background:linear-gradient(135deg,#ff006e,#ffd700,#00e5ff);display:flex;align-items:center;justify-content:center;font-size:30px;border:3px solid #fff;cursor:pointer;z-index:50}.backFab{position:fixed;left:16px;bottom:16px;width:58px;height:58px;border-radius:50%;background:#1a1a2e;display:none;align-items:center;justify-content:center;font-size:28px;color:#ffd700;border:3px solid #ffd700;cursor:pointer;z-index:60}.gameOverlay{position:fixed;inset:0;background:rgba(0,0,0,.85);display:flex;align-items:center;justify-content:center;padding:16px;z-index:999}.gamePopup{background:linear-gradient(160deg,#2b005e,#12002b);border:3px solid #ffd700;border-radius:28px;padding:22px 18px;max-width:420px;width:100%;text-align:center;box-shadow:0 0 40px #ff006e}.choiceRow{display:flex;gap:12px;margin-top:16px}.choiceBox{flex:1;padding:18px 8px;border-radius:20px;cursor:pointer;font-weight:900;font-size:18px;border:3px solid #fff}.choiceNo{background:linear-gradient(135deg,#ff2222,#ff6b6b);color:#fff}.choiceYes{background:linear-gradient(135deg,#00cc44,#00ff88);color:#000}.warnBar{height:6px;background:rgba(255,255,255,.25);border-radius:99px;overflow:hidden;margin-top:14px}.warnBarFill{height:100%;background:linear-gradient(90deg,#ff006e,#ffd700);width:100%;animation:shrink 1s linear forwards}@keyframes shrink{from{width:100%}to{width:0%}}.bottomNav{position:fixed;bottom:0;left:0;right:0;background:rgba(0,0,0,.9);border-top:2px solid #ffd700;display:flex;justify-content:space-around;padding:10px 0 14px;z-index:100}.bottomNav div{font-size:28px;cursor:pointer;text-align:center}.bottomNav small{display:block;font-size:10px;color:#ffd700}.walletCard{background:linear-gradient(135deg,#ffd700,#ff006e);color:#000;border-radius:24px;padding:18px;text-align:center}.goldBig{font-size:38px;font-weight:900}.switch{width:70px;height:36px;background:#00cc44;border-radius:99px;position:relative;cursor:pointer;border:2px solid #fff}.switch.off{background:#ff2222}.switchKnob{position:absolute;top:3px;left:34px;width:28px;height:28px;background:#fff;border-radius:50%}.switch.off .switchKnob{left:3px}.spacexScene{background:#000010;border:2px solid #00e5ff;border-radius:20px;padding:16px;text-align:left;font-family:'Share Tech Mono',monospace;color:#00ffaa}.scifiCode{font-family:'Share Tech Mono',monospace;color:#00ffaa;font-size:13px;line-height:1.7;white-space:pre-wrap;border:1px solid #00ffaa;border-radius:14px;padding:12px;background:rgba(0,0,0,.65);text-align:left}.pinBox{background:linear-gradient(160deg,#2b005e,#12002b);border:3px solid #ffd700;border-radius:28px;padding:28px 22px;max-width:360px;width:100%;text-align:center}.pinInput{font-size:30px;text-align:center;letter-spacing:14px;background:#fff!important}.tabBtn{flex:1;padding:10px 4px;border-radius:14px;border:2px solid #ffd700;background:rgba(0,0,0,.4);color:#fff;font-weight:900;cursor:pointer;font-size:13px}.tabBtn.active{background:#ffd700;color:#000}
</style></head><body>
<div class="topbar"><div><span style="font-size:11px;background:rgba(0,0,0,.55);border:1px solid #ffd700;padding:4px 8px;border-radius:20px" id="catTime">Loading CAT...</span><br><div style="font-weight:900;margin-top:4px">INFINITY BOT</div></div><div style="display:flex;gap:6px;align-items:center"><div class="profile" id="profileBtn" style="width:38px;height:38px">👤<span id="notifBadge" class="notif hidden">1</span></div><div class="profile" id="menuBtn" style="width:38px;height:38px">⋮</div></div></div>
<div id="menuDrop" class="hidden" style="position:absolute;top:96px;right:10px;background:#1a1a2e;border:2px solid #ffd700;border-radius:16px;padding:8px;z-index:500;min-width:210px"></div>
<div id="toast" class="toast hidden"></div>
<div id="gameWarnOverlay" class="gameOverlay hidden" style="display:none"><div class="gamePopup"><div style="font-size:54px">⚠️</div><h2>⚠️ Warning ⚠️</h2><p id="gameWarnText">Account not found</p><div class="warnBar"><div class="warnBarFill"></div></div></div></div>
<div id="welcomeOverlay" class="gameOverlay hidden" style="display:none"><div class="gamePopup"><div style="font-size:56px">👑</div><h2>Welcome to Infinity</h2><p>Do you already have an account?</p><div class="choiceRow"><div class="choiceBox choiceNo" id="choiceNoBtn">❌<br>No</div><div class="choiceBox choiceYes" id="choiceYesBtn">✅<br>Yes</div></div><p style="font-size:12px;opacity:.7">Yes = Login • No = Register</p></div></div>
<div id="challengeOverlay" class="gameOverlay hidden" style="display:none;z-index:800"><div class="gamePopup" style="border-color:#00e5ff"><div style="font-size:50px">🎮</div><h2>CHALLENGE REQUEST</h2><p id="challengeText" style="font-size:16px;line-height:1.5"></p><div class="choiceRow"><div class="choiceBox choiceNo" onclick="respondChallenge(false)">❌<br>No</div><div class="choiceBox choiceYes" onclick="respondChallenge(true)">✅<br>Yes</div></div><p style="font-size:12px;opacity:.7">Auto closes in 5 seconds...</p><div class="warnBar"><div class="warnBarFill" style="animation-duration:5s"></div></div></div></div>
<div id="pinOverlay" class="gameOverlay hidden" style="display:none;z-index:950"><div class="pinBox"><div style="font-size:50px">🔐</div><h2 style="color:#ffd700;margin:8px 0">Enter PIN</h2><p id="pinTitle" style="opacity:.8;font-size:13px">Confirm transaction</p><input id="pinInput" class="pinInput" type="password" maxlength="4" inputmode="numeric" placeholder="• • • •"><div style="display:flex;gap:10px;margin-top:10px"><button class="btn2" style="flex:1" onclick="closePin()">Cancel</button><button class="btn" style="flex:1" id="pinConfirmBtn">✅ Confirm</button></div></div></div>
<div id="page-home" class="center"><div style="font-size:26px">✨ 💖 ⭐ 🌟 💫</div><div class="crownBig">👑</div><h1 class="cursive" style="font-size:68px;margin:5px">Infinity Bot</h1><p style="letter-spacing:3px;font-weight:900">DOMINIC MASTIRIA</p><p>Riddles • Bible Fight • Sci-Fi • WhatsApp</p><button class="enterBtn" id="enterBtn">Enter</button><div style="margin-top:16px;font-size:26px">✨ 💖 👑 💖 ✨</div><p style="font-size:12px;opacity:.7">Press ENTER to Continue</p></div>
<div id="page-register" class="hidden" style="max-width:520px;margin:0 auto;padding:20px 14px"><div class="card" style="text-align:center"><div style="font-size:60px">👑</div><h1 class="cursive" style="font-size:48px;margin:5px">Register</h1><p id="regSub">Create your Infinity account 👑</p><div id="registerForm"><label style="text-align:left;display:block">Your Name:</label><input id="regName" placeholder="Your Name" maxlength="20"><label style="text-align:left;display:block">4-Digit Password:</label><input id="regPass" placeholder="••••" maxlength="4" inputmode="numeric" type="password" class="regInput"><p style="font-size:12px;color:#ffd700">⚠️ Do NOT use 1234 or 0000</p><button class="btn" onclick="doRegister()">📝 REGISTER</button><p style="font-size:13px;opacity:.8">Already have an account? <b style="color:#ffd700;cursor:pointer" onclick="showLogin()">Click here to Login</b></p></div><div id="loginForm" class="hidden"><label style="text-align:left;display:block">Your Name:</label><input id="loginName" placeholder="Your Name"><label style="text-align:left;display:block">4-Digit Password:</label><input id="loginPass" placeholder="••••" maxlength="4" inputmode="numeric" type="password" class="regInput"><button class="btn" onclick="doLogin()">🔓 LOGIN</button><p style="font-size:13px;opacity:.8">New here? <b style="color:#ffd700;cursor:pointer" onclick="showRegister()">Click here to Register</b></p></div></div></div>
<div id="page-dash" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 80px"><div style="text-align:center"><h2 class="cursive" style="font-size:44px;margin:10px 0" id="welcomeText">Welcome, Player 👑</h2><span class="badge">⭐ Rank: <b id="myRank">#-</b></span><span class="badge">🎯 <b id="myStage">Beginner</b></span></div><div class="grid"><div class="box" onclick="openRiddles()"><span>🧩</span><b>RIDDLES</b><br><small>5 Types • 10 Qs</small></div><div class="box" onclick="openBible()"><span>📖</span><b>BIBLE FIGHT</b><br><small>3 Types • 10 Qs</small></div><div class="box" onclick="openComing('SCI-FI')"><span>🚀</span><b>SCI-FI</b><br><small>10 Games • 25 Dec</small></div><div class="box" onclick="openComing('WHATSAPP')"><span>💚</span><b>WHATSAPP</b><br><small>Chats • Calls</small></div></div><div class="card"><h3 style="text-align:center;margin:0">🏆 TOP 5 🏆</h3><div id="leaderList">Loading...</div><button class="btn2" onclick="openFullLeader()">👀 View Full Leaderboard</button></div></div>
<div id="page-leader" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 80px"><div class="card"><h3 style="text-align:center;margin:0">🏆 GLOBAL LEADERBOARD 🏆</h3><div style="display:flex;gap:8px;margin:12px 0"><button class="tabBtn" id="tab-gold" onclick="renderLeaderTabs('gold')">🪙 Gold</button><button class="tabBtn" id="tab-gems" onclick="renderLeaderTabs('gems')">💎 Gems</button><button class="tabBtn" id="tab-rank" onclick="renderLeaderTabs('rank')">⭐ Rank</button><button class="tabBtn active" id="tab-pvp" onclick="renderLeaderTabs('pvp')">⚔️ PvP</button></div><div id="leaderTabsTitle" style="text-align:center;font-weight:900;color:#ffd700">⚔️ PvP RANKING</div><div id="fullLeaderList">Loading...</div><div id="myRankJump"></div></div></div>
<div id="page-game" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 80px"><div class="card"><h2 id="gameTitle" style="text-align:center">🧩 Game</h2><div id="gameBody"></div></div></div>
<div id="page-coming" class="hidden" style="max-width:520px;margin:0 auto;padding:40px 20px 80px;text-align:center"><div style="font-size:80px" id="comingIcon">🚀</div><h1 class="cursive" style="font-size:54px">Coming Soon</h1><h2 id="comingName">SCI-FI</h2><p>Launching on<br><b>25th December 2026</b></p><p>Returning in:</p><div style="font-size:60px;font-weight:900;color:#ffd700" id="countDown">5</div></div>
<div id="page-bank" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 80px"><div class="card"><h2 style="text-align:center">🧑‍
<div id="bottomNav" class="bottomNav hidden">... Notify ...</div>
    <script>
var user=null; try{ user=JSON.parse(localStorage.getItem('inf_user')||'null'); }catch(e){ user=null; }
var wins=0, losses=0, myGold=0, myGems=0, myPlayerID='', myBankID='';
try{ wins=parseInt(localStorage.getItem('inf_wins')||'0')||0; losses=parseInt(localStorage.getItem('inf_loss')||'0')||0; myGold=parseInt(localStorage.getItem('inf_gold')||'0')||0; myGems=parseInt(localStorage.getItem('inf_gems')||'0')||0; myPlayerID=localStorage.getItem('inf_player_id')||''; myBankID=localStorage.getItem('inf_bank_id')||''; }catch(e){}
var seenQs=[]; try{ seenQs=JSON.parse(localStorage.getItem('inf_seen_qs')||'[]'); }catch(e){ seenQs=[]; }
var stageIdx=0, loggedIn=false, currentPage='page-home', fullLeaderData=[], currentChallengeId=null, reviewType='review';
function isDominic(){ return user && user.name && user.name.toLowerCase()==='dominic' && user.password==='2164'; }
function getRankByWins(w){ if(w>=102400) return "Godly Rank Classified"; if(w>=51200) return "SSS Classified"; if(w>=25600) return "SSS Rank"; if(w>=12800) return "SS Rank"; if(w>=6400) return "S Rank"; if(w>=3200) return "National"; if(w>=1600) return "Professional"; if(w>=800) return "Expert"; if(w>=400) return "Advanced"; if(w>=200) return "Intermediate"; return "Beginner"; }
function isClassified(w){ return w>=3200; }
function isUnlocked25Dec(){ var now=catNow(); return now>=new Date(2026,11,25,0,0,0); }
function catNow(){ return new Date(); }
function updateCatTime(){ try{ var d=new Date(); var el=document.getElementById('catTime'); if(el){ el.textContent='CAT ' + d.getHours().toString().padStart(2,'0') + ':' + d.getMinutes().toString().padStart(2,'0') + ':' + d.getSeconds().toString().padStart(2,'0'); } }catch(e){} }
setInterval(updateCatTime,1000); updateCatTime();
function toast(m){ var t=document.getElementById('toast'); t.innerText=m; t.classList.remove('hidden'); setTimeout(function(){ t.classList.add('hidden'); },4500); }
function hideWarnNow(){ var ov=document.getElementById('gameWarnOverlay'); if(ov){ ov.classList.add('hidden'); ov.style.display='none'; } }
function hideWelcomeNow(){ var ov=document.getElementById('welcomeOverlay'); if(ov){ ov.classList.add('hidden'); ov.style.display='none'; } }
function showGameWarn(msg){ hideWelcomeNow(); var ov=document.getElementById('gameWarnOverlay'); document.getElementById('gameWarnText').innerHTML=msg; ov.classList.remove('hidden'); ov.style.display='flex'; setTimeout(function(){ hideWarnNow(); },1200); }
function showWelcomePopup(){ var ov=document.getElementById('welcomeOverlay'); if(!ov) return; ov.classList.remove('hidden'); ov.style.display='flex'; }
function showPage(id){ currentPage=id; ['page-home','page-register','page-dash','page-leader','page-game','page-coming','page-bank','page-notifs','page-server-info','page-update','page-review','page-challenge','page-profile','page-other','page-messages'].forEach(function(p){ var el=document.getElementById(p); if(el) el.classList.add('hidden'); }); var t=document.getElementById(id); if(t) t.classList.remove('hidden'); window.scrollTo(0,0); updateBackFab(); }
function updateBackFab(){ var f=document.getElementById('backFab'); if(!f) return; f.style.display=(currentPage==='page-home'||currentPage==='page-dash')?'none':'flex'; }
function goBack(){ if(currentPage==='page-register') showPage('page-home'); else if(currentPage==='page-leader'||currentPage==='page-game'||currentPage==='page-coming'||currentPage==='page-bank'||currentPage==='page-notifs'||currentPage==='page-server-info'||currentPage==='page-update'||currentPage==='page-review'||currentPage==='page-challenge'||currentPage==='page-profile'||currentPage==='page-other'||currentPage==='page-messages') goDash(); else showPage('page-dash'); }
function toggleMenu(forceClose){ var m=document.getElementById('menuDrop'); if(!m) return; if(forceClose){ m.classList.add('hidden'); return; } var h=''; h+='<div onclick="openMyProfile();toggleMenu(true)">👤 My Profile</div>'; h+='<div onclick="openNotifs();toggleMenu(true)">✉️ Notifications</div>'; h+='<div onclick="openFullLeader();toggleMenu(true)">🏆 Leaderboard</div>'; h+='<div onclick="goDash();toggleMenu(true)">🏠 Dashboard</div>'; h+='<div onclick="openBank();toggleMenu(true)">🏦 Bank</div>'; h+='<div onclick="openReviewRequest(\'review\');toggleMenu(true)">⭐ Review</div>'; h+='<div onclick="openReviewRequest(\'request\');toggleMenu(true)">📩 Request</div>'; if(isDominic()){ h+='<div style="color:#ffd700;border-top:1px solid #ffd700">👑 DOMINIC ADMIN - PIN 2164</div>'; h+='<div onclick="openUpdatePage();toggleMenu(true)">🔄 Update Server + Earning Switch</div>'; h+='<div onclick="openServerInfo();toggleMenu(true)">🖥️ Server Info</div>'; } m.innerHTML=h; m.classList.toggle('hidden'); }
document.getElementById('menuBtn').onclick=function(e){ e.stopPropagation(); toggleMenu(); };
document.addEventListener('click',function(e){ var b=document.getElementById('menuBtn'); var m=document.getElementById('menuDrop'); if(!b||!m) return; if(b.contains(e.target)) return; if(!m.contains(e.target)) m.classList.add('hidden'); });
document.getElementById('profileBtn').onclick=function(){ openMyProfile(); };
document.getElementById('backFab').onclick=function(){ goBack(); };
document.getElementById('msgFab').onclick=function(){ openNotifs(); };
document.getElementById('enterBtn').addEventListener('click',function(){ goRegister(); });
document.getElementById('choiceYesBtn').onclick=function(){ hideWelcomeNow(); setTimeout(function(){ showLogin(); },300); };
document.getElementById('choiceNoBtn').onclick=function(){ hideWelcomeNow(); showRegister(); };
function goRegister(){ if(user && user.name){ showPage('page-register'); fetch('/api/player?name='+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){ if(d&&d.found){ showLogin(); document.getElementById('loginName').value=user.name; } else { showRegister(); setTimeout(showWelcomePopup,500); } }).catch(function(){ showRegister(); }); return; } showPage('page-register'); showRegister(); setTimeout(showWelcomePopup,500); }
function showRegister(){ document.getElementById('registerForm').classList.remove('hidden'); document.getElementById('loginForm').classList.add('hidden'); }
function showLogin(){ document.getElementById('registerForm').classList.add('hidden'); document.getElementById('loginForm').classList.remove('hidden'); }
function saveLocal(){ try{ localStorage.setItem('inf_user',JSON.stringify(user)); localStorage.setItem('inf_wins',wins); localStorage.setItem('inf_loss',losses); localStorage.setItem('inf_gold',myGold); localStorage.setItem('inf_gems',myGems); localStorage.setItem('inf_player_id',myPlayerID); localStorage.setItem('inf_bank_id',myBankID); localStorage.setItem('inf_seen_qs',JSON.stringify(seenQs)); localStorage.setItem('inf_has_account','yes'); }catch(e){} }
function doRegister(){ var n=document.getElementById('regName').value.trim(); var pw=document.getElementById('regPass').value.trim(); if(!n){ toast('Please enter your name!'); return; } if(!pw||pw.length!==4||isNaN(pw)){ toast('Password must be exactly 4 digits!'); return; } if(pw==='1234'||pw==='0000'){ toast('Password too easy!'); return; } fetch('/api/player?name='+encodeURIComponent(n)).then(function(r){return r.json()}).then(function(d){ if(d&&d.found){ showLogin(); document.getElementById('loginName').value=n; toast('Account found! Please Login 👑'); return; } user={name:n,password:pw}; wins=0; losses=0; myGold=0; myGems=0; saveLocal(); syncScore(); enterDashboard('Welcome '+n+'! Registered 👑'); }).catch(function(){ user={name:n,password:pw}; saveLocal(); enterDashboard('Welcome '+n+'!'); }); }
function doLogin(){ var n=document.getElementById('loginName').value.trim(); var pw=document.getElementById('loginPass').value.trim(); if(!n||!pw){ toast('Enter name + password!'); return; } fetch('/api/player?name='+encodeURIComponent(n)+'&password='+encodeURIComponent(pw)).then(function(r){return r.json()}).then(function(d){ if(d&&d.found&&d.password_ok!==false){ user={name:n,password:pw}; wins=d.wins||0; losses=d.losses||0; myGold=d.gold||0; myGems=d.gems||0; myPlayerID=d.player_id||''; myBankID=d.bank_id||''; seenQs=d.seen_qs||seenQs; saveLocal(); enterDashboard('Welcome back '+n+'! 👑'); } else { showGameWarn('⚠️ Account not found / Wrong password<br>Try again or Register'); } }).catch(function(){ toast('Network error'); }); }
function enterDashboard(msg){ loggedIn=true; toast(msg); showPage('page-dash'); document.getElementById('welcomeText').innerText='Welcome, '+(user?user.name:'Player')+' 👑'; updateGoldUI(); loadLeader(); }
function syncScore(){ if(!user||!loggedIn) return; fetch('/api/score',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:user.name,password:user.password,wins:wins,losses:losses,stage:stageIdx,gold:myGold,gems:myGems,seen_qs:seenQs})}).catch(function(){}); }
function updateGoldUI(){ var mr=document.getElementById('myRank'); if(mr) mr.innerText='#-'; var st=document.getElementById('myStage'); if(st) st.innerText=getRankByWins(wins); var b1=document.getElementById('bankGold'); if(b1) b1.innerText=myGold; var b2=document.getElementById('bankGems'); if(b2) b2.innerText=myGems; var p1=document.getElementById('profGold'); if(p1) p1.innerText=myGold; var p2=document.getElementById('profGems'); if(p2) p2.innerText=myGems; var id1=document.getElementById('profIDShow'); if(id1) id1.innerText='ID: '+myPlayerID; var id2=document.getElementById('profBankIDShow'); if(id2) id2.innerText='Bank: '+myBankID; var id3=document.getElementById('bankIDShow'); if(id3) id3.innerText='ID: '+myBankID; var id4=document.getElementById('bankPlayerIDShow'); if(id4) id4.innerText='Player: '+myPlayerID; }
function goDash(){ if(!loggedIn){ showPage('page-register'); return; } showPage('page-dash'); loadLeader(); }
function loadLeader(){ fetch('/api/leaderboard').then(function(r){return r.json()}).then(function(d){ fullLeaderData=d.players||[]; var html=''; fullLeaderData.slice(0,5).forEach(function(p,i){ html+='<div class="leadRow" onclick="viewOtherPlayer(\''+p.name+'\')"><span>'+(i+1)+'. '+p.name+'</span><span>🏆 '+p.wins+'W • 💔 '+p.losses+'L</span></div>'; }); document.getElementById('leaderList').innerHTML=html||'No players yet'; var mr=document.getElementById('myRank'); if(mr && user){ fullLeaderData.forEach(function(p,i){ if(p.name.toLowerCase()===user.name.toLowerCase()) mr.innerText='#'+(i+1); }); } }).catch(function(){}); }
function openFullLeader(){ showPage('page-leader'); renderLeaderTabs('pvp'); }
function renderLeaderTabs(tab){ var players=fullLeaderData.slice(); var title='⚔️ PvP RANKING'; ['gold','gems','rank','pvp'].forEach(function(t){ var b=document.getElementById('tab-'+t); if(b) b.classList.remove('active'); }); var act=document.getElementById('tab-'+tab); if(act) act.classList.add('active'); if(tab==='gold'){ players.sort(function(a,b){return b.gold-a.gold}); title='🪙 GOLD RANKING - Total Gold Earned'; } else if(tab==='gems'){ players.sort(function(a,b){return b.gems-a.gems}); title='💎 GEMS RANKING - Total Gems'; } else if(tab==='rank'){ players.sort(function(a,b){return b.wins-a.wins}); title='⭐ RANK RANKING - Beginner → Godly'; } else { players.sort(function(a,b){return (b.wins-b.losses)-(a.wins-a.losses)}); } document.getElementById('leaderTabsTitle').innerText=title; var html=''; players.forEach(function(p,i){ var dn=isClassified(p.wins)?'🔒 Profile Classified':p.name; var extra=tab==='gold'?'🪙 '+p.gold+' Gold':tab==='gems'?'💎 '+p.gems+' Gems':tab==='rank'?getRankByWins(p.wins):'🏆 '+p.wins+'W • 💔 '+p.losses+'L'; html+='<div class="leadRow" onclick="viewOtherPlayer(\''+p.name+'\')"><span>'+(i+1)+'. '+dn+'<br><small>'+extra+'</small></span><span>#'+(i+1)+'</span></div>'; }); document.getElementById('fullLeaderList').innerHTML=html||'No players'; if(user){ var me=players.findIndex(function(p){return p.name.toLowerCase()===user.name.toLowerCase()}); document.getElementById('myRankJump').innerHTML=me>=0?'<div style="background:#ffd700;color:#000;padding:12px;border-radius:16px;font-weight:900;text-align:center;margin-top:10px">Your Rank: #'+(me+1)+' • '+getRankByWins(wins)+'</div>':''; } }
function viewOtherPlayer(name){ var p=null; fullLeaderData.forEach(function(x){if(x.name===name)p=x}); if(!p){toast(name);return;} if(isClassified(p.wins) && !(user&&user.name===name) && !isDominic()){ showGameWarn('⚠️ Warning ⚠️<br>You can\'t view this profile 😉<br>Sorry please level up<br>Need to reach National level to view'); return; } if(user&&user.name===name){ openMyProfile(); return; } showPage('page-other'); document.getElementById('otherName').innerText=p.name; document.getElementById('otherRank').innerText=getRankByWins(p.wins); document.getElementById('otherWins').innerText=p.wins; document.getElementById('
function doServerUpdate(){ toast('🚀 Update Applied!...'); ... }
    var pinCallback=null;
function askPin(title,cb){ pinCallback=cb; document.getElementById('pinTitle').innerText=title; var ov=document.getElementById('pinOverlay'); ov.classList.remove('hidden'); ov.style.display='flex'; var inp=document.getElementById('pinInput'); inp.value=''; inp.focus(); }
function closePin(){ var ov=document.getElementById('pinOverlay'); ov.classList.add('hidden'); ov.style.display='none'; pinCallback=null; }
document.getElementById('pinConfirmBtn').onclick=function(){ var v=document.getElementById('pinInput').value.trim(); if(v.length!==4){ toast('PIN must be 4 digits'); return; } var cb=pinCallback; closePin(); if(cb) cb(v); };
function openBank(){ showPage('page-bank'); updateGoldUI(); document.getElementById('bankBoxes').innerHTML='<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px"><div class="card" onclick="bankForm(\'withdraw\')" style="cursor:pointer;text-align:center"><div style="font-size:32px">🏧</div><h3>Withdraw Gold</h3></div><div class="card" onclick="bankForm(\'send\')" style="cursor:pointer;text-align:center"><div style="font-size:32px">💸</div><h3>Send Gold</h3></div><div class="card" onclick="bankForm(\'deposit\')" style="cursor:pointer;text-align:center"><div style="font-size:32px">💰</div><h3>Deposit</h3></div><div class="card" onclick="bankForm(\'bank\')" style="cursor:pointer;text-align:center"><div style="font-size:32px">🏦</div><h3>Bank</h3><p style="font-size:12px">'+myBankID+'</p></div></div><div class="card" onclick="openExchange()" style="cursor:pointer;text-align:center"><div style="font-size:32px">🔄</div><h3>Exchange</h3><p>100 Gold = 1 Gem • 1 Gem = 100 Gold</p></div>'; document.getElementById('bankForms').innerHTML=''; }
function bankForm(t){ var f=document.getElementById('bankForms'); if(t==='send'){ f.innerHTML='<div class="card"><h3>💸 Send Gold</h3><p style="font-size:12px">Type numbers only - INF- auto added</p><p style="background:#fff;color:#000;padding:10px;border-radius:10px;font-weight:900">INF- <input id="sendID" placeholder="12345678" inputmode="numeric" style="display:inline;width:140px;border:none;margin:0;padding:0"></p><input id="sendAmt" placeholder="Amount" type="number"><button class="btn" onclick="doSend()">Send</button></div>'; } else if(t==='withdraw'){ f.innerHTML='<div class="card"><h3>🏧 Withdraw - Bank to Gold/Gems Account</h3><input id="withdrawAmt" placeholder="Amount" type="number"><select id="withdrawCur" style="width:100%;padding:14px;border-radius:14px;margin:8px 0"><option>Gold</option><option>Gems</option></select><button class="btn" onclick="doWithdraw()">Withdraw</button></div>'; } else if(t==='deposit'){ f.innerHTML='<div class="card"><h3>💰 Deposit - To Your Bank or Someone\\'s Bank</h3><p style="font-size:12px">Type numbers only - Bank INF- auto added. Leave blank = yours</p><p style="background:#fff;color:#000;padding:10px;border-radius:10px;font-weight:900">Bank INF- <input id="depositID" placeholder="1234567890" inputmode="numeric" style="display:inline;width:140px;border:none;margin:0;padding:0"></p><input id="depositAmt" placeholder="Amount" type="number"><button class="btn" onclick="doDeposit()">Deposit</button></div>'; } else { f.innerHTML='<div class="card"><h3>🏦 My Bank Account</h3><p>'+myBankID+'</p><p>Player: '+myPlayerID+'</p><p>🪙 Gold: '+myGold+' • 💎 Gems: '+myGems+'</p></div>'; } }
function doSend(){ var rid=document.getElementById('sendID').value.replace(/[^0-9]/g,''); var amt=parseInt(document.getElementById('sendAmt').value||'0'); if(!rid||rid.length<8){ toast('Enter 8-digit ID numbers only'); return; } if(!amt){ toast('Enter Amount'); return; } if(myGold<amt){ toast('Not enough Gold'); return; } askPin('Enter PIN - Send '+amt+' Gold to INF-'+rid,function(pin){ fetch('/api/transfer',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sender:user.name,pin:pin,receiver_id:'INF-'+rid,amount:amt,currency:'Gold'})}).then(function(r){return r.json()}).then(function(d){ if(d.error){ toast(d.error); return; } myGold=d.sender_gold; saveLocal(); syncScore(); updateGoldUI(); toast('✅ Sent '+amt+' Gold to INF-'+rid+' (Fee '+d.fee+')'); openBank(); }); }); }
function doWithdraw(){ var amt=parseInt(document.getElementById('withdrawAmt').value||'0'); var cur=document.getElementById('withdrawCur').value; if(!amt){ toast('Enter amount'); return; } askPin('Enter PIN - Withdraw '+amt+' '+cur,function(pin){ fetch('/api/withdraw',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:user.name,pin:pin,amount:amt,currency:cur})}).then(function(r){return r.json()}).then(function(d){ if(d.error){ toast(d.error); return; } myGold=d.gold; myGems=d.gems; saveLocal(); syncScore(); updateGoldUI(); toast('✅ Withdrawn '+amt+' '+cur); openBank(); }); }); }
function doDeposit(){ var amt=parseInt(document.getElementById('depositAmt').value||'0'); var tid=document.getElementById('depositID').value.replace(/[^0-9]/g,''); if(!amt){ toast('Enter amount'); return; } askPin('Enter PIN - Deposit '+amt+' Gold',function(pin){ fetch('/api/deposit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:user.name,pin:pin,amount:amt,target_id:tid?('Bank INF-'+tid):''})}).then(function(r){return r.json()}).then(function(d){ if(d.error){ toast(d.error); return; } toast('✅ Deposited '+amt+' Gold'); openBank(); }); }); }
function openExchange(){ var f=document.getElementById('bankForms'); f.innerHTML='<div class="card" style="text-align:center"><h2>🔄 Exchange</h2><button class="btn" onclick="doExchangeForm(\'gold_to_gem\')">🪙 Gold >>>> 💎 Gems<br><small>100 Gold = 1 Gem</small></button><button class="btn2" onclick="doExchangeForm(\'gem_to_gold\')">💎 Gems >>>> 🪙 Gold<br><small>1 Gem = 100 Gold</small></button></div>'; }
function doExchangeForm(dir){ var f=document.getElementById('bankForms'); var label=dir==='gold_to_gem'?'Gold':'Gems'; var to=dir==='gold_to_gem'?'Gems':'Gold'; var rate=dir==='gold_to_gem'?'100 Gold = 1 Gem':'1 Gem = 100 Gold'; f.innerHTML='<div class="card"><h3>🔄 Exchange '+label+' → '+to+'</h3><p>'+rate+'</p><p>Enter the amount of '+label+' you want to exchange:</p><input id="exAmt" type="number" placeholder="Amount of '+label+'"><button class="btn" onclick="confirmExchange(\''+dir+'\')">Confirm</button></div>'; }
function confirmExchange(dir){ var amt=parseInt(document.getElementById('exAmt').value||'0'); if(!amt){ toast('Enter amount'); return; } if(dir==='gold_to_gem' && myGold<amt){ toast('Not enough Gold - You have '+myGold); return; } if(dir==='gem_to_gold' && myGems<amt){ toast('Not enough Gems - You have '+myGems); return; } askPin('Enter PIN - Exchange '+amt+' '+(dir==='gold_to_gem'?'Gold':'Gems'),function(pin){ fetch('/api/exchange',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:user.name,pin:pin,amount:amt,direction:dir})}).then(function(r){return r.json()}).then(function(d){ if(d.error){ toast(d.error); return; } myGold=d.gold; myGems=d.gems; saveLocal(); syncScore(); updateGoldUI(); toast('✅ Exchange done! Gold: '+myGold+' • Gems: '+myGems); openBank(); }); }); }
function tagPlayer(id,name){ if(!id){ toast('No ID'); return; } askPin('Enter PIN - Challenge '+name,function(pin){ fetch('/api/challenge_send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sender:user.name,target_id:id,game:'Galaxy Shooter'})}).then(function(r){return r.json()}).then(function(d){ if(d.error){ toast(d.error); return; } toast('🎮 Challenge sent to '+name+'! Waiting 5 sec...'); }); }); }
function showChallengePopup(from,game,cid){ currentChallengeId=cid; document.getElementById('challengeText').innerHTML='<b>'+from+'</b> challenged you to<br><b>'+game+'</b><br><br>Do you accept?'; var ov=document.getElementById('challengeOverlay'); ov.classList.remove('hidden'); ov.style.display='flex'; setTimeout(function(){ if(ov.style.display!=='none'){ ov.classList.add('hidden'); ov.style.display='none'; } },5000); }
function respondChallenge(accept){ var ov=document.getElementById('challengeOverlay'); ov.classList.add('hidden'); ov.style.display='none'; fetch('/api/challenge_respond',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({challenge_id:currentChallengeId,accept:accept})}); if(accept){ showPage('page-challenge'); document.getElementById('challengeDashText').innerText='🎮 Challenge Accepted! Pick a game:'; } else { toast('❌ Challenge Declined'); goDash(); } }
function declineChallengeDash(){ showPage('page-dash'); toast('Challenge closed'); }
function startChallengeGame(g){ if(g==='Galaxy Shooter') openGalaxyShooter(); else if(g==='Riddles') openRiddles(); else if(g==='Bible Fight') openBible(); else openDecoding(); }
function openSciFiGames(){ showPage('page-game'); document.getElementById('gameTitle').innerText='🚀 SCI-FI - 10 Games'; document.getElementById('gameBody').innerHTML='<div class="card" onclick="openGalaxyShooter()"><h3>🌌 Galaxy Shooter - Lv 1-10</h3><p>Shoot asteroids • Tag player to Challenge</p></div><div class="card" onclick="openDecoding()"><h3>💻 Decoding - Lv 1-10</h3><p>Crack codes • Hard levels</p></div><div class="card" onclick="openRiddles()"><h3>🧩 Riddles</h3><p>5 Types • 10 Qs</p></div><div class="card" onclick="openBible()"><h3>📖 Bible Fight</h3><p>3 Types • 10 Qs</p></div><div class="card"><h3>🤖 Robot Wars - Coming in Update</h3></div><div class="card"><h3>🏎️ Space Race - Coming in Update</h3></div><div class="card"><h3>👾 Alien Invasion - Coming in Update</h3></div><div class="card"><h3>🧠 Mind Maze - Coming in Update</h3></div><div class="card"><h3>⚡ Laser Duel - Coming in Update</h3></div><div class="card"><h3>🪐 Planet Quest - Coming in Update</h3></div>'; }
var RIDDLE_SETS={General:[{q:"What has keys but can't open locks?",a:["Piano","Door","Map","Book"],c:0},{q:"What gets wetter the more it dries?",a:["Towel","Rain","Sponge","Soap"],c:0},{q:"I speak without a mouth, hear without ears. What am I?",a:["Echo","Wind","Shadow","Dream"],c:0},{q:"What has a neck but no head?",a:["Bottle","Guitar","Shirt","Snake"],c:0},{q:"What has a face and two hands but no arms?",a:["Clock","Robot","Mirror","Mask"],c:0},{q:"The more you take, the more you leave behind. What?",a:["Footsteps","Money","Time","Photos"],c:0},{q:"What can you catch but never throw?",a:["A Cold","Ball","Fish","Butterfly"],c:0},{q:"What goes up but never comes down?",a:["Your Age","Balloon","Smoke","Price"],c:0},{q:"What has one eye but can't see?",a:["Needle","Camera","Cyclops","Potato"],c:0},{q:"What is full of holes but holds water?",a:["Sponge","Bucket","Net","Strainer"],c:0}],Love:[{q:"What is the symbol of love?",a:["Heart","Star","Moon","Rose"],c:0},{q:"What do you give on Valentine's?",a:["Chocolate","Homework","Shoes","Keys"],c:0},{q:"Love is...",a:["Patient & Kind","Loud","Fast","Expensive"],c:0},{q:"Who is Romeo's love?",a:["Juliet","Mary","Esther","Ruth"],c:0},{q:"What colour is love?",a:["Red","Blue","Green","Black"],c:0},{q:"Best gift for love?",a:["Time","Money","Car","Phone"],c:1},{q:"Love never...",a:["Fails","Wins","Runs","Sleeps"],c:0},{q:"What makes love grow?",a:["Trust","Fighting","Lying","Hiding"],c:0},{q:"First love letter was written by?",a:["A Poet","A King","A Soldier","A Farmer"],c:0},{q:"Love is patient - from which book?",a:["1 Corinthians","Genesis","Psalms","Revelation"],c:0}],Programmers:[{q:"What does HTML stand for?",a:["HyperText Markup Language","HighTech Machine Language","HyperTool Made Language","Home Text Made Language"],c:0},{q:"Which language runs in browser?",a:["JavaScript","Python","C++","Java"],c:0},{q:"What is a bug?",a:["An error in code","An insect","A virus","A feature"],c:0},{q:"What does CSS do?",a:["Styles a page","Runs server","Stores data","Sends email"],c:0},{q:"Which is a loop?",a:["for","if","and","or"],c:0},{q:"What is Python?",a:["Programming language","Snake only","Game","App"],c:0},{q:"What stores data?",a:["Variable","Function","Loop","Tag"],c:0},{q:"What is Git?",a:["Version control","Chat app","Game","Browser"],c:0},{q:"Binary of 2?",a:["10","01","11","00"],c:0},{q:"What is an API?",a:["Way for apps to talk","A game","A phone","A virus"],c:0}],Smart:[{q:"If 2+2=4, what is 10x10?",a:["100","20","10","1000"],c:0},{q:"What is the next number: 2,4,8,16?",a:["32","20","24","18"],c:0},{q:"How many sides does a hexagon have?",a:["6","5","7","8"],c:0},{q:"What is 15% of 200?",a:["30","15","20","25"],c:0},{q:"Which is prime?",a:["7","9","15","21"],c:0},{q:"Square root of 144?",a:["12","14","16","11"],c:0},{q:"What is 7x8?",a:["56","54","64","48"],c:0},{q:"How many minutes in 2 hours?",a:["120","100","60","180"],c:0},{q:"What is the capital of France?",a:["Paris","London","Rome","Berlin"],c:0},{q:"Water formula?",a:["H2O","CO2","O2","NaCl"],c:0}],Funny:[{q:"Why did the chicken cross the road?",a:["To get to the other side","To sleep","To eat","To hide"],c:0},{q:"What do you call a fish without eyes?",a:["A fsh","A shark","A whale","A crab"],c:0},{q:"Why is 6 afraid of 7?",a:["Because 7 ate 9","Because 7 is big","Because 6 is small","Because 7 runs"],c:0},{q:"What is a skeleton's favourite snack?",a:["Spare ribs","Chips","Pizza","Cake"],c:0},{q:"Why did the scarecrow win an award?",a:["He was outstanding in his field","He was funny","He was tall","He was scary"],c:0},{q:"What do you call cheese that isn't yours?",a:["Nacho cheese","My cheese","Old cheese","Big cheese"],c:0},{q:"Why don't skeletons fight?",a:["They don't have the guts","They are shy","They are weak","They are slow"],c:0},{q:"What did one wall say to the other?",a:["I'll meet you at the corner","Hello","Goodbye","Stay"],c:0},{q:"Why did the bicycle fall?",a:["It was two-tired","It was old","It was broken","It was heavy"],c:0},{q:"What is orange and sounds like a parrot?",a:["A carrot","An apple","A banana","A mango"],c:0}]};
var BIBLE_SETS={"Old Testament":[{q:"Who built the Ark?",a:["Noah","Moses","David","Abraham"],c:0},{q:"Who defeated Goliath?",a:["David","Samson","Saul","Solomon"],c:0},{q:"Who was thrown into lions den?",a:["Daniel","Joseph","Jonah","Peter"],c:0},{q:"Who led Israel out of Egypt?",a:["Moses","Aaron","Joshua","David"],c:0},{q:"How many days did God create world?",a:["6","7","5","40"],c:0},{q:"Who was the first man?",a:["Adam","Noah","Abraham","Moses"],c:0},{q:"Who dreamed of a ladder to heaven?",a:["Jacob","Joseph","Isaac","Esau"],c:0},{q:"What did David use to kill Goliath?",a:["Stone + Sling","Sword","Spear","Bow"],c:0},{q:"Who was swallowed by a big fish?",a:["Jonah","Daniel","Peter","Paul"],c:0},{q:"Ten Commandments given on which mountain?",a:["Mount Sinai","Mount Zion","Mount Olive","Mount Carmel"],c:0}],"New Testament":[{q:"Who was born in Bethlehem?",a:["Jesus","Peter","Paul","John"],c:0},{q:"Who betrayed Jesus?",a:["Judas","Peter","Thomas","James"],c:0},{q:"How many disciples did Jesus have?",a:["12","10","7","40"],c:0},{q:"Who wrote most New Testament letters?",a:["Paul","Peter","John","Luke"],c:0},{q:"Jesus turned water into?",a:["Wine","Milk","Juice","Oil"],c:0},{q:"Who denied Jesus 3 times?",a:["Peter","John","James","Thomas"],c:0},{q:"Where did Jesus grow up?",a:["Nazareth","Bethlehem","Jerusalem","Egypt"],c:0},{q:"First miracle of Jesus?",a:["Water to Wine","Healing Blind","Feeding 5000","Walking on Water"],c:0},{q:"Who was the first martyr?",a:["Stephen","Peter","Paul","James"],c:0},{q:"Book of Revelation written by?",a:["John","Paul","Peter","Luke"],c:0}],"Stories":[{q:"Good Samaritan helped who?",a:["A wounded man","A king","A priest","A soldier"],c:0},{q:"Prodigal Son returned to?",a:["His Father","His Brother","His Friend","His King"],c:0},{q:"David was a?",a:["Shepherd then King","Farmer","Priest","Fisherman"],c:0},{q:"Jesus fed 5000 with?",a:["5 loaves + 2 fish","10 loaves","Bread only","Fish only"],c:0},{q:"Noah's Ark saved?",a:["Animals + Family","Only Noah","Only Animals","Only Birds"],c:0},{q:"Moses parted which sea?",a:["Red Sea","Dead Sea","Galilee","Jordan"],c:0},{q:"Daniel survived?",a:["Lions","Fire","Snakes","Storm"],c:0},{q:"Samson strength was in?",a:["His Hair","His Sword","His Shield","His Shoes"],c:0},{q:"Joseph's coat was?",a:["Many Colours","White","Black","Gold"],c:0},{q:"Jonah was in fish for?",a:["3 days","1 day","7 days","40 days"],c:0}]};
var curGame=null, curQs=[], curIdx=0, curScore=0, curRewards=[], curType='';
function pickQs(list){ var pool=list.filter(function(q){return seenQs.indexOf(q.q)===-1}); if(pool.length<10){ seenQs=[]; pool=list.slice(); } pool=pool.slice().sort(function(){return Math.random()-0.5}); return pool.slice(0,10); }
function openRiddles(){ showPage('page-game'); document.getElementById('gameTitle').innerText='🧩 RIDDLES - Pick a Type'; var h='<p style="text-align:center">Pick a type - 10 Questions • Win = Earn</p>'; Object.keys(RIDDLE_SETS).forEach(function(k){ h+='<button class="btn2" onclick="startRiddleType(\''+k+'\')">🧩 '+k+' Riddles</button>'; }); h+='<button class="btn" onclick="openShop(\'Riddles\')">🛒 Shop - Riddles</button>'; document.getElementById('gameBody').innerHTML=h; }
function startRiddleType(t){ curGame='riddles'; curType=t; curQs=pickQs(RIDDLE_SETS[t]); curIdx=0; curScore=0; curRewards=[]; document.getElementById('gameTitle').innerText='🧩 Riddles - '+t; showQ(); }
function openBible(){ showPage('page-game'); document.getElementById('gameTitle').innerText='📖 BIBLE FIGHT - Pick a Type'; var h='<p style="text-align:center">Pick a type - 10 Questions • Win = Earn</p>'; Object.keys(BIBLE_SETS).forEach(function(k){ h+='<button class="btn2" onclick="startBibleType(\''+k+'\')">📖 '+k+'</button>'; }); h+='<button class="btn" onclick="openShop(\'Bible Fight\')">🛒 Shop - Bible Fight</button>'; document.getElementById('gameBody').innerHTML=h; }
function startBibleType(t){ curGame='bible'; curType=t; curQs=pickQs(BIBLE_SETS[t]); curIdx=0; curScore=0; curRewards=[]; document.getElementById('gameTitle').innerText='📖 Bible - '+t; showQ(); }
function showQ(){ if(curIdx>=curQs.length){ finishGame(); return; } var q=curQs[curIdx]; var h='<div class="card"><p style="text-align:center">Question '+(curIdx+1)+'/10 • Score: '+curScore+'</p><h3>'+q.q+'</h3>'; q.a.forEach(function(opt,i){ h+='<button class="opt" onclick="answerQ('+i+')">'+opt+'</button>'; }); h+='</div>'; document.getElementById('gameBody').innerHTML=h; }
function answerQ(i){ var q=curQs[curIdx]; if(i===q.c){ curScore++; var amt=Math.floor(Math.random()*101)+50; curRewards.push(amt); toast('✅ Correct! +'+amt+' Gold'); } else { toast('❌ Wrong! Answer: '+q.a[q.c]); } if(seenQs.indexOf(q.q)===-1) seenQs.push(q.q); saveLocal(); curIdx++; showQ(); }
function finishGame(){ var total=0; curRewards.forEach(function(a){ total+=a; }); var won=curScore>=6; if(won){ myWins++; if(is_earning_active_front()){ myGold+=total; myGems+=Math.floor(total/10); } } else { myLosses++; total=0; } saveLocal(); syncScore(); updateGoldUI(); var msg=won?'<h2>🏆 YOU WON!</h2><p>Score: '+curScore+'/10</p><p>Correct answers earned:</p><p style="font-size:22px;font-weight:900;color:#ffd700">+'+total+' Gold 🪙</p><p>+'+Math.floor(total/10)+' Gems 💎</p><p style="font-size:12px">Each correct = 50-150 Gold • Total added together • Missed = Reduced</p>':'<h2>💔 You Lost</h2><p>Score: '+curScore+'/10</p><p>Need 6+ to earn. Lose = 0 Gold/Gems.</p>'; if(!is_earning_active_front()) msg+='<p style="color:#ff8888">⏳ Earning starts 25 Dec 2026 + Dominic Switch ON</p>'; document.getElementById('gameBody').innerHTML='<div class="card" style="text-align:center">'+msg+'<button class="btn" onclick="'+(curGame==='riddles'?'openRiddles()':'openBible()')+'">Play Again - New Questions</button><button class="btn2" onclick="openShop(\''+(curGame==='riddles'?'Riddles':'Bible Fight')+'\')">🛒 Open Shop</button></div>'; }
function is_earning_active_front(){ return isUnlocked25Dec(); }
function openGalaxyShooter(){ if(!isUnlocked25Dec()){ showGameWarn('🔒 GALAXY SHOOTER LOCKED<br>⏳ Coming 25 Dec 2026'); return; } showPage('page-game'); document.getElementById('gameTitle').innerText='🌌 GALAXY SHOOTER - Lv 1'; document.getElementById('gameBody').innerHTML='<div class="card" style="text-align:center"><div style="font-size:70px">🌌🚀👾</div><h3>Galaxy Shooter</h3><p>Level 1: Tap the Asteroid!</p><div style="font-size:60px;cursor:pointer" onclick="shooterHit(this)">☄️</div><p>Score: <b id="shooterScore">0</b></p><button class="btn" onclick="tagPlayerPrompt()">🏷️ Tag Player to Challenge</button><button class="btn2" onclick="openShop(\'Galaxy Shooter\')">🛒 Shop - Galaxy Shooter</button><p style="font-size:12px">Tag = Enter ID → Other player gets CHALLENGE REQUEST popup for 5 seconds</p></div>'; window._shooter=0; }
function shooterHit(el){ window._shooter++; document.getElementById('shooterScore').innerText=window._shooter; el.innerText='💥'; setTimeout(function(){ el.innerText='☄️'; },300); if(window._shooter>=5){ myWins++; var amt=Math.floor(Math.random()*101)+50; if(is_earning_active_front()){ myGold+=amt; toast('🏆 Galaxy Shooter WIN! +'+amt+' Gold'); } else toast('🏆 Galaxy Shooter WIN! Earning starts 25 Dec'); saveLocal(); syncScore(); updateGoldUI(); window._shooter=0; } }
function tagPlayerPrompt(){ var id=prompt('Enter Player ID numbers only (8 digits):'); if(!id) return; var clean=id.replace(/[^0-9]/g,''); if(clean.length<8){ toast('Enter 8 digits'); return; } var name=prompt('Enter Player Name to challenge:')||'Player'; tagPlayer('INF-'+clean,name); }
function openDecoding(){ if(!isUnlocked25Dec()){ showGameWarn('🔒 DECODING LOCKED<br>⏳ Coming 25 Dec 2026'); return; } showPage('page-game'); document.getElementById('gameTitle').innerText='💻 DECODING - Lv 1'; document.getElementById('gameBody').innerHTML='<div class="card" style="text-align:center"><h3>💻 Decode This!</h3><p style="font-size:20px;font-weight:900;letter-spacing:4px">01001000 01001001</p><p>What word is this?</p><button class="opt" onclick="decodeAns(true)">HI</button><button class="opt" onclick="decodeAns(false)">BYE</button><button class="opt" onclick="decodeAns(false)">GO</button><button class="btn2" onclick="openShop(\'Decoding\')">🛒 Shop - Decoding</button></div>'; }
function decodeAns(ok){ if(ok){ myWins++; toast('✅ Correct! Decoding WIN!'); } else { myLosses++; toast('❌ Wrong! Try again'); } saveLocal(); syncScore(); updateGoldUI(); }
function openShop(gameName){ showPage('page-game'); document.getElementById('gameTitle').innerText='🛒 Shop - '+gameName; document.getElementById('gameBody').innerHTML='<div class="card" onclick="buyItem(\'Power Sword\',\'500 Gold\')"><h3>⚔️ Power Sword</h3><p>500 Gold - Tap to Buy</p></div><div class="card" onclick="buyItem(\'Galaxy Shield\',\'800 Gold\')"><h3>🛡️ Galaxy Shield</h3><p>800 Gold - Tap to Buy</p></div><div class="card" onclick="buyItem(\'Turbo Boost\',\'300 Gold\')"><h3>🚀 Turbo Boost</h3><p>300 Gold - Tap to Buy</p></div><div class="card" onclick="buyItem(\'Lucky Charm\',\'2 Gems\')"><h3>💎 Lucky Charm</h3><p>2 Gems - Tap to Buy</p></div><button class="btn2" onclick="goDash()">Back to Dashboard</button>'; }
function buyItem(name,price){ askPin('Enter PIN - Buy '+name+' ('+price+')',function(pin){ toast('✅ Purchased '+name+'! PIN Confirmed'); }); }
function openMessages(){ openNotifs(); }
window.onload=function(){ try{ var s=JSON.parse(localStorage.getItem('inf_user')||'null'); if(s&&s.name){ user={name:s.name,password:s.password||''}; wins=parseInt(localStorage.getItem('inf_wins')||'0')||0; losses=parseInt(localStorage.getItem('inf_loss')||'0')||0; myGold=parseInt(localStorage.getItem('inf_gold')||'0')||0; myGems=parseInt(localStorage.getItem('inf_gems')||'0')||0; myPlayerID=localStorage.getItem('inf_player_id')||''; myBankID=localStorage.getItem('inf_bank_id')||''; loggedIn=true; goDash(); } else { showPage('page-home'); } }catch(e){ showPage('page-home'); } };
</script></body></html>
"""
@app.route("/")
def home(): return HOME
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
