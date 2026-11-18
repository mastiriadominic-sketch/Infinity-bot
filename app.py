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
NOTIFS = {}
CHALLENGES = {}
_lock = threading.Lock()
# GLOBAL EARNING SWITCH - Dominic controls it
EARNING_ON = True
EARNING_START = datetime.datetime(2026,12,25,0,0,0)

def norm(n):
    return str(n or "").strip().lower()
def load_json_safe(path):
    try:
        if os.path.exists(path):
            with open(path,"r") as f:
                d=json.load(f)
                if isinstance(d,dict): return d
    except: pass
    return {}
def gen_id():
    # 8 digits minimum
    return "INF-" + "".join([str(random.randint(0,9)) for _ in range(8)])
def ensure_player(v, k):
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
    if "notifs" not in v: v["notifs"]=[]
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
            USERS=new
            print(f"LOADED {len(USERS)} players from {p}")
            return
    print("No players - fresh start")
def load_messages():
    global MESSAGES
    for p in [MSG_FILE, MSG_BACKUP]:
        d=load_json_safe(p)
        if d:
            MESSAGES=d
            print(f"LOADED {len(MESSAGES)} chats")
            return
def save_users():
    try:
        with _lock:
            data=json.dumps(USERS)
            with open(LEADER_FILE,"w") as f: f.write(data)
            with open(BACKUP1,"w") as f: f.write(data)
            with open(BACKUP2,"w") as f: f.write(data)
    except Exception as e: print("Save failed:",e)
def save_messages():
    try:
        with _lock:
            data=json.dumps(MESSAGES)
            with open(MSG_FILE,"w") as f: f.write(data)
            with open(MSG_BACKUP,"w") as f: f.write(data)
    except Exception as e: print("Save msg failed:",e)
load_users()
load_messages()
def auto_save_loop():
    while True:
        time.sleep(10)
        try:
            save_users(); save_messages()
            print(f"AUTO-SAVED: {len(USERS)} players")
        except Exception as e: print("Auto-save error:",e)
threading.Thread(target=auto_save_loop, daemon=True).start()
def is_earning_active():
    # Earning only after 25 Dec 2026 AND switch ON
    now=datetime.datetime.now()
    if now < EARNING_START: return False
    return EARNING_ON
def calc_reward(correct_count, total=10):
    # Each correct = random 50-150, sum together, if not all correct, reduced proportionally
    # Lose (correct < 6) = 0
    if correct_count < 6:
        return {"gold":0,"gems":0,"per_q":[]}
    per=[]
    total_gold=0
    for i in range(correct_count):
        amt=random.randint(50,150)
        per.append(amt)
        total_gold+=amt
    # If missed some, final is reduced - already only correct count added
    gems = total_gold // 10
    return {"gold":total_gold,"gems":gems,"per_q":per}
def send_whatsapp(to,text):
    if not WHATSAPP_TOKEN or not PHONE_ID: return
    try: requests.post(f"https://graph.facebook.com/v21.0/{PHONE_ID}/messages",headers={"Authorization":f"Bearer {WHATSAPP_TOKEN}","Content-Type":"application/json"},json={"messaging_product":"whatsapp","to":to,"type":"text","text":{"body":text}},timeout=10)
    except: pass
        @app.route("/")
def home(): return HOME
@app.route("/api/earning_status")
def earning_status():
    return jsonify({"earning_on":EARNING_ON,"active":is_earning_active(),"start":"2026-12-25"})
@app.route("/api/toggle_earning", methods=["POST"])
def toggle_earning():
    global EARNING_ON
    d=request.get_json() or {}
    # Only Dominic 2164
    if norm(d.get("name"))!="dominic" or str(d.get("password"))!="2164":
        return jsonify({"error":"Only Dominic can toggle"}),403
    EARNING_ON = not EARNING_ON
    return jsonify({"earning_on":EARNING_ON,"active":is_earning_active()})
@app.route("/api/player")
def get_player():
    n=norm(request.args.get("name",""))
    pw=request.args.get("password","")
    if n in USERS:
        v=USERS[n]
        # Give ID if missing - auto on 24 Dec
        if not v.get("player_id"): v["player_id"]=gen_id(); save_users()
        if pw and v.get("password") and str(v.get("password"))!=str(pw):
            return jsonify({"found":True,"password_ok":False,"name":v["display_name"],"player_id":v["player_id"]})
        return jsonify({"found":True,"password_ok":True,"name":v["display_name"],"wins":v["wins"],"losses":v["losses"],"stage":v["stage"],"gold":v["gold"],"gems":v["gems"],"player_id":v["player_id"],"history":v["history"],"friends":v["friends"],"notifs":v.get("notifs",[])})
    return jsonify({"found":False})
@app.route("/api/leaderboard")
def leaderboard():
    players=[]
    for k,v in USERS.items():
        players.append({"name":v["display_name"],"wins":v["wins"],"losses":v["losses"],"stage":v["stage"],"gold":v.get("gold",0),"gems":v.get("gems",0),"player_id":v.get("player_id","")})
    players=sorted(players,key=lambda x:x["wins"],reverse=True)
    return jsonify({"players":players})
@app.route("/api/score", methods=["POST"])
def score():
    d=request.get_json() or {}
    n=norm(d.get("name"))
    if not n: return jsonify({"error":"no name"}),400
    if n not in USERS:
        USERS[n]=ensure_player({"display_name":d.get("name"),"password":d.get("password","")},d.get("name"))
    v=USERS[n]
    if d.get("password"): v["password"]=d.get("password")
    v["wins"]=d.get("wins",v["wins"]); v["losses"]=d.get("losses",v["losses"]); v["stage"]=d.get("stage",v["stage"])
    if "gold" in d: v["gold"]=d["gold"]
    if "gems" in d: v["gems"]=d["gems"]
    save_users()
    return jsonify({"ok":True,"gold":v["gold"],"gems":v["gems"],"player_id":v["player_id"]})
@app.route("/api/transfer", methods=["POST"])
def transfer():
    d=request.get_json() or {}
    sender=norm(d.get("sender")); pin=str(d.get("pin","")); recv_id=str(d.get("receiver_id","")).upper(); amt=int(d.get("amount",0))
    # Block if earning OFF - Dominic switch
    if not is_earning_active():
        return jsonify({"error":"Transfers blocked - Earning is OFF by Admin"}),403
    if sender not in USERS: return jsonify({"error":"Sender not found"}),404
    s=USERS[sender]
    if str(s.get("password"))!=pin:
        # Wrong PIN notification
        s.setdefault("notifs",[]).append({"text":"⚠️ Warning! Pin is wrong, please check again or try again later.","time":str(datetime.datetime.now()),"type":"warn"})
        save_users()
        return jsonify({"error":"Wrong PIN"}),403
    # Find receiver by ID - 8 digits
    recv=None
    for k,v in USERS.items():
        if str(v.get("player_id","")).upper()==recv_id:
            recv=v; break
    if not recv: return jsonify({"error":"Receiver ID not found"}),404
    if s.get("gold",0) < amt: return jsonify({"error":"Not enough Gold"}),400
    fee=int(amt*0.05) # 5% fee to Server Economy
    net=amt-fee
    s["gold"]-=amt; recv["gold"]=recv.get("gold",0)+net
    # Notifications
    s.setdefault("notifs",[]).append({"text":f"Dear player you have successfully sent {amt} Gold to {recv_id}. Thanks for your transaction.","time":str(datetime.datetime.now()),"type":"send"})
    recv.setdefault("notifs",[]).append({"text":f"Dear {recv['display_name']} you have received {net} Gold from {s.get('player_id')}. Thank you.","time":str(datetime.datetime.now()),"type":"receive"})
    save_users()
    return jsonify({"ok":True,"sent":amt,"fee":fee,"net":net,"sender_gold":s["gold"],"receiver_gold":recv["gold"]})
@app.route("/api/withdraw", methods=["POST"])
def withdraw():
    d=request.get_json() or {}
    n=norm(d.get("name")); pin=str(d.get("pin","")); amt=int(d.get("amount",0)); cur=d.get("currency","Gold")
    if not is_earning_active():
        return jsonify({"error":"Withdrawals blocked - Earning is OFF"}),403
    if n not in USERS: return jsonify({"error":"Not found"}),404
    v=USERS[n]
    if str(v.get("password"))!=pin:
        v.setdefault("notifs",[]).append({"text":"⚠️ Warning! Pin is wrong, please check again or try again later.","time":str(datetime.datetime.now()),"type":"warn"})
        save_users(); return jsonify({"error":"Wrong PIN"}),403
    if cur=="Gold":
        if v.get("gold",0)<amt: return jsonify({"error":"Not enough Gold"}),400
        v["gold"]-=amt
    else:
        if v.get("gems",0)<amt: return jsonify({"error":"Not enough Gems"}),400
        v["gems"]-=amt
    v.setdefault("notifs",[]).append({"text":f"Dear player you have successfully withdrawn {amt} {cur}. Thanks for your transaction.","time":str(datetime.datetime.now()),"type":"withdraw"})
    save_users()
    return jsonify({"ok":True,"gold":v["gold"],"gems":v["gems"]})
@app.route("/api/challenge_send", methods=["POST"])
def challenge_send():
    d=request.get_json() or {}
    sender=norm(d.get("sender")); target_id=str(d.get("target_id","")).upper(); game=d.get("game","Galaxy Shooter")
    if sender not in USERS: return jsonify({"error":"Sender not found"}),404
    s=USERS[sender]
    target=None
    for k,v in USERS.items():
        if str(v.get("player_id","")).upper()==target_id: target=v; break
    if not target: return jsonify({"error":"Target ID not found"}),404
    cid=f"CH-{random.randint(10000000,99999999)}"
    CHALLENGES[cid]={"from":s["display_name"],"from_id":s.get("player_id"),"to":target["display_name"],"to_id":target_id,"game":game,"status":"pending","time":str(datetime.datetime.now())}
    target.setdefault("notifs",[]).append({"text":f"🎮 CHALLENGE REQUEST: {s['display_name']} ({s.get('player_id')}) challenged you to {game}!","time":str(datetime.datetime.now()),"type":"challenge","challenge_id":cid,"game":game,"from":s["display_name"]})
    save_users()
    return jsonify({"ok":True,"challenge_id":cid})
@app.route("/api/challenge_respond", methods=["POST"])
def challenge_respond():
    d=request.get_json() or {}
    cid=d.get("challenge_id"); accept=d.get("accept",False)
    if cid in CHALLENGES:
        CHALLENGES[cid]["status"]="accepted" if accept else "declined"
        return jsonify({"ok":True,"status":CHALLENGES[cid]["status"]})
    return jsonify({"error":"Not found"}),404
@app.route("/api/review", methods=["POST"])
def review():
    d=request.get_json() or {}
    # Save to Server Info - Dominic sees it
    try:
        with open(os.path.join(BASE,"reviews.json"),"a") as f: f.write(json.dumps({"name":d.get("name"),"type":d.get("type"),"text":d.get("text"),"time":str(datetime.datetime.now())})+"\n")
    except: pass
    return jsonify({"ok":True})
@app.route("/api/server_info")
def server_info():
    # Only Dominic check in frontend, backend also checks query
    if norm(request.args.get("name"))!="dominic" or str(request.args.get("password"))!="2164":
        return jsonify({"error":"Admin only"}),403
    reviews=[]
    try:
        if os.path.exists(os.path.join(BASE,"reviews.json")):
            with open(os.path.join(BASE,"reviews.json")) as f: reviews=[json.loads(l) for l in f if l.strip()]
    except: pass
    return jsonify({"players":len(USERS),"earning_on":EARNING_ON,"earning_active":is_earning_active(),"reviews":reviews,"challenges":list(CHALLENGES.values())})
HOME=r"""<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>INFINITY BOT v9.0 - CHRISTMAS</title>
<link href="https://fonts.googleapis.com/css2?family=Great+Vibes&family=Poppins:wght@400;700;900&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<style>*{box-sizing:border-box}body{margin:0;font-family:Poppins,Arial;color:white;background:radial-gradient(circle at 50% 20%,#3a0a5e,#12002b 70%);min-height:100vh}.cursive{font-family:'Great Vibes',cursive}.topbar{display:flex;justify-content:space-between;align-items:center;padding:8px 14px}.profile{width:46px;height:46px;border-radius:50%;background:linear-gradient(135deg,#ff006e,#ffd700);display:flex;align-items:center;justify-content:center;font-size:20px;border:2px solid #fff;cursor:pointer;position:relative}.notif{position:absolute;top:-6px;right:-6px;background:red;color:white;font-size:11px;width:20px;height:20px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:900}.center{min-height:82vh;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:20px}.crownBig{font-size:90px;filter:drop-shadow(0 0 30px gold)}.enterBtn{margin-top:20px;padding:16px 70px;font-family:'Great Vibes',cursive;font-size:48px;border:none;border-radius:60px;background:linear-gradient(90deg,#ff006e,#ffd700,#00e5ff);color:#000;box-shadow:0 0 40px #ff006e;cursor:pointer}.card{background:rgba(255,255,255,.08);border:2px solid rgba(255,255,255,.35);border-radius:26px;padding:20px;margin:14px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.box{background:linear-gradient(160deg,rgba(255,255,255,.18),rgba(0,0,0,.4));border:2px solid #fff;border-radius:24px;padding:22px 10px;text-align:center;cursor:pointer}.box span{font-size:38px;display:block}.btn{width:100%;padding:14px;border:none;border-radius:25px;font-weight:900;background:#ffd700;margin:6px 0;cursor:pointer}.btn2{width:100%;padding:13px;border-radius:25px;border:2px solid #00e5ff;background:transparent;color:#00e5ff;font-weight:900;margin:6px 0;cursor:pointer}.opt{width:100%;padding:13px;margin:7px 0;border-radius:16px;border:2px solid #fff;background:rgba(0,0,0,.5);color:white;font-weight:700;cursor:pointer;text-align:left}input{width:100%;padding:14px;border-radius:14px;border:2px solid #ffd700;margin:8px 0;font-size:16px;background:#fff;color:#000}.hidden{display:none}.leadRow{display:flex;justify-content:space-between;align-items:center;padding:10px 12px;background:rgba(0,0,0,.45);border-radius:14px;margin:6px 0;cursor:pointer}.dot{width:12px;height:12px;border-radius:50%;display:inline-block}.green{background:#00ff00;box-shadow:0 0 10px #00ff00}.red{background:#ff2222}.badge{display:inline-block;padding:5px 10px;border-radius:20px;background:rgba(0,0,0,.5);border:1px solid #ffd700;font-size:12px;margin:3px}.count{font-size:60px;font-weight:900;color:#ffd700}.toast{position:fixed;top:70px;left:50%;transform:translateX(-50%);background:#fff;color:#000;padding:12px 18px;border-radius:20px;font-weight:700;z-index:900;max-width:90%;text-align:center}.regInput{font-size:18px;text-align:center;letter-spacing:2px}.msgFab{position:fixed;right:16px;bottom:16px;width:62px;height:62px;border-radius:50%;background:linear-gradient(135deg,#ff006e,#ffd700,#00e5ff);display:flex;align-items:center;justify-content:center;font-size:30px;border:3px solid #fff;cursor:pointer;z-index:50}.backFab{position:fixed;left:16px;bottom:16px;width:58px;height:58px;border-radius:50%;background:#1a1a2e;display:none;align-items:center;justify-content:center;font-size:28px;color:#ffd700;border:3px solid #ffd700;cursor:pointer;z-index:60}.chatRow{display:flex;justify-content:space-between;align-items:center;padding:12px;background:rgba(0,0,0,.45);border-radius:16px;margin:8px 0}.chatBox{background:#1a1a2e;border-radius:20px;padding:12px;min-height:320px;max-height:380px;overflow-y:auto}.bubble{max-width:80%;padding:10px 14px;border-radius:18px;margin:6px 0;font-size:14px}.mine{background:#ffd700;color:#000;margin-left:auto}.theirs{background:rgba(255,255,255,.2)}.msgBarWrap{display:flex;gap:8px;margin-top:12px}.msgBar{flex:1;display:flex;align-items:center;gap:10px;background:#2b2b33;border-radius:999px;padding:10px 12px}.msgBar input{flex:1;background:transparent;border:none;outline:none;color:#fff;font-size:16px;padding:0;margin:0}.catTimeTop{font-size:11px;background:rgba(0,0,0,.55);border:1px solid #ffd700;padding:4px 8px;border-radius:20px;display:inline-block}.topRight{display:flex;align-items:center;gap:6px}.soundSmall{width:32px;height:32px;border-radius:50%;background:rgba(0,0,0,.55);border:1px solid #ffd700;display:flex;align-items:center;justify-content:center;font-size:16px;cursor:pointer}.leaderScroll{max-height:480px;overflow-y:auto}.myRankBar{position:sticky;bottom:0;background:linear-gradient(90deg,#ffd700,#ff006e);color:#000;padding:12px;border-radius:16px;font-weight:900;text-align:center;cursor:pointer;margin-top:10px;border:2px solid #fff}.profileCol{display:flex;flex-direction:column;align-items:center;gap:2px}.menuBtn{width:32px;height:32px;border-radius:50%;background:rgba(0,0,0,.55);border:1px solid #ffd700;display:flex;align-items:center;justify-content:center;font-size:20px;color:#fff;cursor:pointer}.menuDrop{position:absolute;top:96px;right:10px;background:#1a1a2e;border:2px solid #ffd700;border-radius:16px;padding:8px;z-index:500;min-width:200px}.menuDrop div{padding:12px 10px;border-radius:12px;cursor:pointer;font-weight:700}.gameOverlay{position:fixed;inset:0;background:rgba(0,0,0,.65);display:flex;align-items:center;justify-content:center;padding:16px}#gameWarnOverlay{z-index:200}#welcomeOverlay{z-index:300}.gamePopup{background:linear-gradient(160deg,#2b005e,#12002b);border:3px solid #ffd700;border-radius:28px;padding:22px 18px;max-width:420px;width:100%;text-align:center;box-shadow:0 0 40px #ff006e}.choiceRow{display:flex;gap:12px;margin-top:16px}.choiceBox{flex:1;padding:18px 8px;border-radius:20px;cursor:pointer;font-weight:900;font-size:18px;border:3px solid #fff}.choiceNo{background:linear-gradient(135deg,#ff2222,#ff6b6b);color:#fff}.choiceYes{background:linear-gradient(135deg,#00cc44,#00ff88);color:#000}.warnBar{height:6px;background:rgba(255,255,255,.25);border-radius:99px;overflow:hidden;margin-top:14px}.warnBarFill{height:100%;background:linear-gradient(90deg,#ff006e,#ffd700);width:100%;animation:shrink 1s linear forwards}@keyframes shrink{from{width:100%}to{width:0%}}.loadingBar{width:100%;height:10px;background:rgba(255,255,255,.2);border-radius:99px;overflow:hidden;margin:10px 0}.loadingFill{height:100%;background:linear-gradient(90deg,#ff006e,#ffd700,#00e5ff);width:0%;transition:width .3s}body.scifi-mode{background:#000510 !important;background-image:linear-gradient(rgba(0,255,170,.18) 1px,transparent 1px),linear-gradient(90deg,rgba(0,255,170,.18) 1px,transparent 1px) !important;background-size:44px 44px,44px 44px !important}.scifiCode{font-family:'Share Tech Mono',monospace;color:#00ffaa;font-size:13px;line-height:1.7;white-space:pre-wrap;border:1px solid #00ffaa;border-radius:14px;padding:12px;background:rgba(0,0,0,.65);text-align:left}.scifiTag{display:inline-block;padding:6px 12px;border:1px solid #00e5ff;color:#00e5ff;border-radius:99px;font-size:12px;margin:3px;background:rgba(0,0,0,.6)}
/* NEW - BOTTOM NAV + BANK + CHALLENGE + EARNING SWITCH */
.bottomNav{position:fixed;bottom:0;left:0;right:0;background:rgba(0,0,0,.85);border-top:2px solid #ffd700;display:flex;justify-content:space-around;padding:10px 0 14px;z-index:100}.bottomNav div{font-size:32px;cursor:pointer;text-align:center}.bottomNav small{display:block;font-size:10px;color:#ffd700}.walletCard{background:linear-gradient(135deg,#ffd700,#ff006e);color:#000;border-radius:24px;padding:18px;text-align:center}.goldBig{font-size:42px;font-weight:900}.switch{width:70px;height:36px;background:#00cc44;border-radius:99px;position:relative;cursor:pointer;border:2px solid #fff;transition:.3s}.switch.off{background:#ff2222}.switchKnob{position:absolute;top:3px;left:34px;width:28px;height:28px;background:#fff;border-radius:50%;transition:.3s}.switch.off .switchKnob{left:3px}.spacexScene{background:#000010;border:2px solid #00e5ff;border-radius:20px;padding:16px;text-align:left;font-family:'Share Tech Mono',monospace;color:#00ffaa;overflow:hidden}.codeScroll{height:180px;overflow:hidden;position:relative}.codeScrollInner{animation:scrollUp 12s linear infinite}@keyframes scrollUp{from{transform:translateY(0)}to{transform:translateY(-50%)}}.challengePopup{border:3px solid #00e5ff;box-shadow:0 0 40px #00e5ff}.gameBoxNew{background:linear-gradient(160deg,#1a0033,#2b005e);border:2px solid #ffd700;border-radius:22px;padding:16px;margin:10px 0;cursor:pointer}.hackKey{width:48px;height:52px;margin:4px;border-radius:12px;border:2px solid #00ffaa;background:#001a12;color:#00ffaa;font-weight:900;font-size:18px;cursor:pointer}.hackScreen{background:#000;color:#00ff00;font-family:'Share Tech Mono',monospace;padding:14px;border-radius:16px;min-height:140px;border:2px solid #00ff00;text-align:left}
</style></head><body>
<audio id="enterAudio" src="https://cdn.pixabay.com/audio/2025/07/09/audio_121db7b43f.mp3" preload="auto" playsinline></audio>
<audio id="dashAudio" src="https://cdn.pixabay.com/audio/2025/06/12/audio_0ea789b238.mp3" preload="auto" playsinline></audio>
<audio id="popupAudio" src="https://cdn.pixabay.com/audio/2022/03/10/audio_2c8c2adfb0.mp3" preload="auto" playsinline></audio>
<audio id="warnAudio" src="https://cdn.pixabay.com/audio/2026/06/02/audio_26933dce5c.mp3" preload="auto" playsinline></audio>
<div class="topbar"><div><span class="catTimeTop" id="catTime">Loading CAT...</span><br><div style="font-weight:900;margin-top:4px">INFINITY BOT</div></div><div class="topRight"><div class="soundSmall" id="soundBtn">🔊</div><div class="profileCol"><div class="profile" id="profileBtn">👤<span id="notifBadge" class="notif hidden">1</span></div><div class="menuBtn" id="menuBtn">⋮</div></div></div></div>
<div id="menuDrop" class="menuDrop hidden"></div>
<div id="toast" class="toast hidden"></div>
<div id="gameWarnOverlay" class="gameOverlay hidden" style="display:none"><div class="gamePopup" id="gameWarnBox"><div style="font-size:54px">⚠️</div><h2>⚠️ Warning ⚠️</h2><p id="gameWarnText">Account not found</p><div class="warnBar"><div class="warnBarFill"></div></div><p style="font-size:12px;opacity:.7">Closing in 1 second...</p></div></div>
<div id="welcomeOverlay" class="gameOverlay hidden" style="display:none"><div class="gamePopup"><div style="font-size:56px">👑</div><h2>Welcome to Infinity Game Play Bot</h2><p style="font-size:18px;font-weight:700">Do you already have an account?</p><div class="choiceRow"><div class="choiceBox choiceNo" id="choiceNoBtn">❌<br>No</div><div class="choiceBox choiceYes" id="choiceYesBtn">✅<br>Yes</div></div><p style="font-size:12px;opacity:.7">Yes = Login • No = Stay to Register</p></div></div>
<!-- CHALLENGE REQUEST POPUP - 5 SECONDS -->
<div id="challengeOverlay" class="gameOverlay hidden" style="display:none;z-index:800"><div class="gamePopup challengePopup"><div style="font-size:50px">🎮</div><h2>CHALLENGE REQUEST</h2><p id="challengeText" style="font-size:16px;line-height:1.5"></p><div class="choiceRow"><div class="choiceBox choiceNo" onclick="respondChallenge(false)">❌<br>No</div><div class="choiceBox choiceYes" onclick="respondChallenge(true)">✅<br>Yes</div></div><p style="font-size:12px;opacity:.7">Auto closes in 5 seconds...</p><div class="warnBar"><div class="warnBarFill" style="animation-duration:5s"></div></div></div></div>
<div id="page-home" class="center"><div style="font-size:26px">✨ 💖 ⭐ 🌟 💫</div><div class="crownBig">👑</div><h1 class="cursive" style="font-size:68px;margin:5px">Infinity Bot</h1><p style="letter-spacing:3px;font-weight:900">DOMINIC MASTIRIA</p><p>Riddles • Bible Fight • Sci-Fi • WhatsApp</p><button class="enterBtn" id="enterBtn">Enter</button><div style="margin-top:16px;font-size:26px">✨ 💖 👑 💖 ✨</div><p style="font-size:12px;opacity:.7">Press ENTER to Continue</p></div>
<div id="page-register" class="hidden" style="max-width:520px;margin:0 auto;padding:20px 14px"><div class="card" style="text-align:center"><div style="font-size:60px">👑</div><h1 class="cursive" style="font-size:48px;margin:5px">Register</h1><p id="regSub">Create your Infinity account 👑</p><div id="registerForm"><label style="text-align:left;display:block">Your Name:</label><input id="regName" placeholder="Your Name" maxlength="20"><label style="text-align:left;display:block">4-Digit Password:</label><input id="regPass" placeholder="••••" maxlength="4" inputmode="numeric" type="password" class="regInput"><p style="font-size:12px;color:#ffd700">⚠️ Do NOT use 1234 or 0000</p><button class="btn" onclick="doRegister()">📝 REGISTER</button><p style="font-size:13px;opacity:.8">Already have an account? <b style="color:#ffd700;cursor:pointer" onclick="showLogin()">Click here to Login</b></p></div><div id="loginForm" class="hidden"><label style="text-align:left;display:block">Your Name:</label><input id="loginName" placeholder="Your Name"><label style="text-align:left;display:block">4-Digit Password:</label><input id="loginPass" placeholder="••••" maxlength="4" inputmode="numeric" type="password" class="regInput"><button class="btn" onclick="doLogin()">🔓 LOGIN</button><p style="font-size:13px;opacity:.8">New here? <b style="color:#ffd700;cursor:pointer" onclick="showRegister()">Click here to Register</b></p></div></div></div>
<div id="page-dash" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 80px"><div style="text-align:center"><h2 class="cursive" style="font-size:44px;margin:10px 0" id="welcomeText">Welcome, Player 👑</h2><span class="badge">⭐ Rank: <b id="myRank">#-</b></span><span class="badge">🎯 <b id="myStage">Beginner</b></span><span class="badge">🪙 <b id="myGoldTop">0 Gold</b></span><span class="badge">💎 <b id="myGemsTop">0 Gems</b></span></div><div class="grid"><div class="box" onclick="openRiddles()"><span>🧩</span><b>RIDDLES</b><br><small>5 Types • 10 Qs</small></div><div class="box" onclick="openBible()"><span>📖</span><b>BIBLE FIGHT</b><br><small>4 Types • 10 Qs</small></div><div class="box" onclick="openComing('SCI-FI')"><span>🚀</span><b>SCI-FI</b><br><small>10 Games • 25 Dec</small></div><div class="box" onclick="openComing('WHATSAPP')"><span>💚</span><b>WHATSAPP</b><br><small>Chats • Calls</small></div></div><div class="card"><h3 style="text-align:center;margin:0">🏆 TOP 5 🏆</h3><div id="leaderList">Loading...</div><button class="btn2" onclick="openFullLeader()">👀 View Full Leaderboard</button></div></div>
<div id="page-leader" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 80px"><div class="card"><h3 style="text-align:center;margin:0">🏆 GLOBAL LEADERBOARD 🏆</h3><p style="text-align:center;font-size:12px;opacity:.8">All players • All games • Wins from everything</p><div class="leaderScroll" id="fullLeaderList">Loading...</div><div id="myRankJump"></div></div></div>
<div id="page-game" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 80px"><div class="card" style="position:relative"><h2 id="gameTitle" style="text-align:center">🧩 RIDDLES</h2><div id="gameBody"></div></div></div>
<div id="page-coming" class="hidden" style="max-width:520px;margin:0 auto;padding:40px 20px 80px;text-align:center"><div style="font-size:80px" id="comingIcon">🚀</div><h1 class="cursive" style="font-size:54px">Coming Soon</h1><h2 id="comingName">SCI-FI</h2><div id="scifiExtra" class="hidden"><div style="display:flex;justify-content:space-between;align-items:center;margin:10px 0"><button class="btn2" style="width:auto;padding:10px 16px" onclick="openBank()">💰 Bank (Wallet)</button><button class="btn2" style="width:auto;padding:10px 16px" onclick="openMyProfile()">👤 Profile</button></div><div class="scifiCode" id="scifiCodeText">> INITIALIZING INFINITY_OS v9.0...
> LOADING ROBOTIC CORE... OK
> SCANNING GALAXY... 42%
> AI ONLINE // CODE RUNNING</div><div id="scifiGamesList"></div></div><p>Launching on<br><b>25th December 2026</b></p><p>Returning in:</p><div class="count" id="countDown">5</div></div>
<!-- NEW PAGES -->
<div id="page-menu" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 80px"><div class="card"><h2 style="text-align:center">🎮 MENU - NEW GAMES</h2><p style="text-align:center;opacity:.8">10 Sci-Fi Games • Earn Gold + Gems • Starts 25 Dec 2026</p><div id="menuGamesList"></div></div></div>
<div id="page-profile-full" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 80px"><div class="card" style="text-align:center"><div style="font-size:70px">👤</div><h2 id="profFullName">Player</h2><p style="font-size:18px;color:#ffd700" id="profFullID">ID:INF-00000000</p><p>⭐ Rank: <b id="profFullRank">#-</b></p><p>🏆 Wins: <b id="profFullWins">0</b> | ❌ Losses: <b id="profFullLoss">0</b></p><div class="walletCard"><div>💰 BANK BALANCE</div><div class="goldBig">🪙 <span id="profFullGold">0</span> Gold</div><div style="font-size:20px;font-weight:900">💎 <span id="profFullGems">0</span> Gems</div></div><p>🎯 Stage: <b id="profFullStage">Beginner</b></p><p>📅 Member Since: <b id="profFullSince">2026</b></p></div><div class="card"><h3>📜 HISTORY SINCE START</h3><div id="profFullHistory">No history yet</div></div></div>
<div id="page-bank" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 80px"><div class="card"><h2 style="text-align:center">🧑‍💻 BANK DASHBOARD</h2><div class="walletCard"><div>🪙 Gold</div><div class="goldBig" id="bankGold">0</div><div>💎 Gems: <b id="bankGems">0</b></div><p id="bankIDShow">ID:INF-00000000</p></div><h3>💸 Send Money</h3><label>Receiver ID (8 digits):</label><input id="sendID" placeholder="INF-12345678"><p id="sendReceiverName" style="color:#00ffaa;font-weight:900"></p><label>Amount (Gold):</label><input id="sendAmt" type="number" placeholder="Enter amount"><button class="btn" onclick="startSend()">➤ SEND</button><h3>🏧 Withdraw</h3><label>Amount:</label><input id="withdrawAmt" type="number" placeholder="Enter amount"><select id="withdrawCur" style="width:100%;padding:14px;border-radius:14px;margin:8px 0"><option>Gold</option><option>Gems</option></select><button class="btn" onclick="startWithdraw()">🏧 WITHDRAW</button><h3>💰 Deposit (Game Money)</h3><label>Amount:</label><input id="depositAmt" type="number" placeholder="Enter amount"><button class="btn2" onclick="doDeposit()">💰 DEPOSIT</button></div></div>
<div id="page-notifs" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 80px"><div class="card"><h2 style="text-align:center">✉️ NOTIFICATIONS / MESSAGES</h2><p style="text-align:center;opacity:.8">Announcements • Game Messages • Transfers</p><div id="notifList">No notifications</div></div></div>
<div id="page-server-info" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 80px"><div class="card"><h2 style="text-align:center">🖥️ SERVER INFO - DOMINIC ONLY</h2><div class="spacexScene"><p>🚀 SPACEX // INFINITY SERVER</p><div>> SERVER STATUS: <span id="serverStatusText">ONLINE</span></div><div>> PLAYERS: <span id="serverPlayers">0</span></div><div>> EARNING: <span id="serverEarningText">ON</span></div><div>> UPTIME: <span id="serverUptime">99.9%</span></div></div><h3>📜 Reviews + Requests - Auto Scrolling</h3><div class="codeScroll"><div class="codeScrollInner" id="serverReviewsList">Loading reviews...</div></div></div></div>
<div id="page-server-economy" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 80px"><div class="card"><h2 style="text-align:center">💰 SERVER ECONOMY - DOMINIC ONLY</h2><p>Total Fees Collected: <b id="econFees">0 Gold</b></p><p>Total Players: <b id="econPlayers">0</b></p><p>Total Gold in Game: <b id="econGold">0</b></p><p>Total Gems in Game: <b id="econGems">0</b></p></div></div>
<div id="page-update" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 80px"><div class="card"><h2 style="text-align:center">🔄 UPDATE SERVER - DOMINIC ONLY</h2><div class="spacexScene"><p>🚀 SPACEX UPDATE CONSOLE</p><div class="scifiCode">> CHECKING UPDATE...
> DOWNLOADING CHRISTMAS UPDATE v9.0...
> APPLYING SCI-FI GAMES... OK
> SYNCING PLAYERS... NO DATA LOST
> READY</div><div style="display:flex;justify-content:space-between;align-items:center;margin-top:16px;background:rgba(255,255,255,.1);padding:14px;border-radius:16px"><div><div style="font-size:20px;font-weight:900">Earning</div><div style="font-size:12px;opacity:.8" id="earningDesc">ON - Players earn Gold + Gems</div></div><div class="switch" id="earningSwitch" onclick="toggleEarningSwitch()"><div class="switchKnob"></div></div></div><p style="font-size:12px;opacity:.8;margin-top:10px">OFF = RED • Earning stops • Transfers blocked • Withdraws blocked<br>ON = GREEN • Everything back to normal</p></div><button class="btn" onclick="doServerUpdate()">🚀 APPLY UPDATE NOW</button></div></div>
<div id="page-review" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 80px"><div class="card"><h2 style="text-align:center" id="reviewTitle">⭐ Review</h2><div class="spacexScene"><div class="scifiCode">> INFINITY_OS // FEEDBACK TERMINAL
> TYPE YOUR REVIEW OR REQUEST
> PRESS SEND TO DEPLOY TO SERVER
> Dominic will see it in Server Info</div></div><textarea id="reviewText" style="width:100%;height:140px;padding:14px;border-radius:14px;margin:12px 0;font-size:16px" placeholder="Type your review or request here..."></textarea><button class="btn" onclick="submitReview()">📩 SEND</button></div></div>
<div id="page-challenge" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 80px"><div class="card"><h2 style="text-align:center">🎮 CHALLENGE DASHBOARD</h2><p id="challengeDashText" style="text-align:center"></p><p style="text-align:center">Pick what to challenge each other:</p><div class="grid"><div class="box" onclick="startChallengeGame('Galaxy Shooter')"><span>🌌</span><b>Galaxy Shooter</b></div><div class="box" onclick="startChallengeGame('Riddles')"><span>🧩</span><b>Riddles</b></div><div class="box" onclick="startChallengeGame('Bible Fight')"><span>📖</span><b>Bible Fight</b></div><div class="box" onclick="startChallengeGame('Decoding')"><span>💻</span><b>Decoding</b></div></div><button class="btn2" onclick="declineChallengeDash()">❌ Decline / Close</button></div></div>
<div id="page-profile" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 80px"><div class="card" style="text-align:center"><div style="font-size:70px">👤</div><h2 id="profName">Player</h2><p style="color:#ffd700" id="profIDShow">ID:INF-00000000</p><p><span id="profDot" class="dot green"></span> <span id="profStatus">Online</span></p><p>⭐ Rank: <b id="profRank">#-</b></p><p>🏆 Wins: <b id="profWins">0</b> | ❌ Losses: <b id="profLoss">0</b></p><p>🪙 Gold: <b id="profGold">0</b> | 💎 Gems: <b id="profGems">0</b></p><p>🎯 Stage: <b id="profStage">Beginner</b></p></div><div class="card"><h3>📩 Friend Requests</h3><div id="reqList"><p>No requests</p></div></div><div class="card"><h3>👥 My Friends</h3><div id="friendList"></div></div></div>
<div id="page-other" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 80px"><div class="card" style="text-align:center"><div style="font-size:70px">👤</div><h2 id="otherName">Player</h2><p>⭐ Rank: <b id="otherRank">#-</b></p><p><b id="otherWins">0</b> Win | <b id="otherLoss">0</b> Lose</p><div id="otherActions"></div></div></div>
<div id="page-messages" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 80px"><div class="card"><h1 style="text-align:center;margin:0;font-size:34px">Message</h1><p style="text-align:center;opacity:.8">chats • Saved + Backup</p><div id="chatFriendList"></div></div></div>
<div id="page-chat" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 80px"><div class="card"><h2 style="text-align:center;margin:0">💬 <span id="chatWith">Friend</span></h2><div class="chatBox" id="chatBox"></div><div class="msgBarWrap"><div class="msgBar"><button onclick="addEmoji()">😊</button><input id="msgInput" placeholder="Message" oninput="toggleSend()"><button onclick="blockedFeature('Picture')">📎</button></div><button id="sendBtnSmall" onclick="sendMsg()" style="display:none">➤</button></div></div></div>
<div id="page-send-money" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 80px"><div class="card"><h2 style="text-align:center">💸 SEND PANEL - Like Airtel</h2><label>Receiver ID:</label><input id="airtelID" placeholder="INF-12345678" oninput="lookupAirtelID()"><p id="airtelNameShow" style="color:#00ffaa;font-weight:900"></p><p>Receiver ID: <b id="airtelIDShow">...</b><br>Name: <b id="airtelName2">...</b></p><label>Please enter amount:</label><input id="airtelAmt" type="number" placeholder="Amount"><button class="btn" onclick="confirmAirtelSend()">Confirm</button></div></div>
<div class="msgFab" id="msgFab">💬</div><div class="backFab" id="backFab">←</div>
<!-- BOTTOM NAV - SHOWS AFTER 25 DEC -->
<div id="bottomNav" class="bottomNav hidden"><div onclick="goDash()">🏡<small>Home</small></div><div onclick="openFullLeader()">🏆<small>Leader</small></div><div onclick="openBank()">🧑‍💻<small>Bank</small></div><div onclick="openNotifs()">✉️<small>Notify</small></div></div>
<script>
var user=null; try{ user=JSON.parse(localStorage.getItem('inf_user')||'null'); }catch(e){ user=null; }
var wins=0, losses=0, myGold=0, myGems=0, myPlayerID='';
try{ wins=parseInt(localStorage.getItem('inf_wins')||'0')||0; losses=parseInt(localStorage.getItem('inf_loss')||'0')||0; myGold=parseInt(localStorage.getItem('inf_gold')||'0')||0; myGems=parseInt(localStorage.getItem('inf_gems')||'0')||0; myPlayerID=localStorage.getItem('inf_player_id')||''; }catch(e){}
var stageIdx=parseInt(localStorage.getItem('inf_stage')||'0')||0; var loggedIn=false;
var STAGES=['Beginner','Intermediate','Advanced','Expert','Professional'];
var currentPage='page-home'; var fullLeaderData=[]; var currentChallengeId=null; var challengeTimer=null; var reviewType='review';
function isDominic(){ return user && user.name && user.name.toLowerCase()==='dominic' && user.password==='2164'; }
function isMenuAllowed(){ if(isDominic()) return true; var now=catNow(); var unlock=new Date(2026,11,25,0,0,0); return now>=unlock; }
function isAfter25Dec(){ var now=catNow(); return now>=new Date(2026,11,25,0,0,0); }
function catNow(){ try{ return new Date(new Date().toLocaleString('en-US',{timeZone:'Africa/Lusaka'})); }catch(e){ return new Date(); } }
function updateCatTime(){ try{ var d=catNow(); var ts=d.toLocaleTimeString('en-GB',{hour:'2-digit',minute:'2-digit',second:'2-digit'}); var ds=('0'+d.getDate()).slice(-2)+'/'+('0'+(d.getMonth()+1)).slice(-2)+'/'+d.getFullYear(); var el=document.getElementById('catTime'); if(el) el.innerText='🕐 '+ts+' • '+ds+' CAT'; }catch(e){} }
try{ setInterval(updateCatTime,1000); updateCatTime(); }catch(e){}
function toast(m){ var t=document.getElementById('toast'); t.innerText=m; t.classList.remove('hidden'); setTimeout(function(){ t.classList.add('hidden'); },4500); }
function playSoundNow(id,vol){ var a=document.getElementById(id); if(!a) return; try{ a.pause(); a.currentTime=0; a.volume=vol||0.8; var p=a.play(); if(p&&p.catch) p.catch(function(){}); }catch(e){} }
function playPopupSound(){ playSoundNow('popupAudio',0.9); }
function playWarnSound(){ playSoundNow('warnAudio',0.9); }
var warnTimer=null;
function hideWarnNow(){ var ov=document.getElementById('gameWarnOverlay'); if(ov){ ov.classList.add('hidden'); ov.style.display='none'; } if(warnTimer){ clearTimeout(warnTimer); warnTimer=null; } }
function hideWelcomeNow(){ var ov=document.getElementById('welcomeOverlay'); if(ov){ ov.classList.add('hidden'); ov.style.display='none'; } }
function showGameWarn(msg,goToLogin){ if(goToLogin===undefined) goToLogin=true; hideWelcomeNow(); playWarnSound(); var ov=document.getElementById('gameWarnOverlay'); var txt=document.getElementById('gameWarnText'); txt.innerHTML=msg||'⚠️ Warning'; ov.classList.remove('hidden'); ov.style.display='flex'; var bar=ov.querySelector('.warnBarFill'); if(bar){ var nb=bar.cloneNode(true); bar.parentNode.replaceChild(nb,bar); } if(warnTimer) clearTimeout(warnTimer); warnTimer=setTimeout(function(){ hideWarnNow(); if(goToLogin){ showPage('page-register'); showLogin(); } },1000); }
function showWelcomePopup(){ hideWarnNow(); var ov=document.getElementById('welcomeOverlay'); if(!ov) return; ov.classList.remove('hidden'); ov.style.display='flex'; playPopupSound(); }
function showPage(id){ currentPage=id; ['page-home','page-register','page-dash','page-leader','page-game','page-coming','page-menu','page-profile-full','page-bank','page-notifs','page-server-info','page-server-economy','page-update','page-review','page-challenge','page-profile','page-other','page-messages','page-chat','page-send-money'].forEach(function(p){ var el=document.getElementById(p); if(el) el.classList.add('hidden'); }); var target=document.getElementById(id); if(target) target.classList.remove('hidden'); window.scrollTo(0,0); updateBackFab(); updateBottomNav(); if(id!=='page-coming'){ try{ document.body.classList.remove('scifi-mode'); }catch(e){} } }
function updateBackFab(){ var fab=document.getElementById('backFab'); if(!fab) return; if(currentPage==='page-home'||currentPage==='page-dash'){ fab.style.display='none'; } else { fab.style.display='flex'; } }
function updateBottomNav(){ var nav=document.getElementById('bottomNav'); var fab=document.getElementById('msgFab'); if(!nav) return; if(isAfter25Dec() && loggedIn){ nav.classList.remove('hidden'); if(fab) fab.style.display='none'; } else { nav.classList.add('hidden'); if(fab) fab.style.display='flex'; } }
function goBack(){ if(currentPage==='page-register'){ showPage('page-home'); } else if(currentPage==='page-leader'){ goDash(); } else if(currentPage==='page-game'){ showPage('page-dash'); } else if(currentPage==='page-coming'){ goDash(); } else if(currentPage==='page-profile'||currentPage==='page-profile-full'||currentPage==='page-menu'||currentPage==='page-bank'||currentPage==='page-notifs'||currentPage==='page-server-info'||currentPage==='page-server-economy'||currentPage==='page-update'||currentPage==='page-review'||currentPage==='page-challenge'||currentPage==='page-send-money'){ goDash(); } else if(currentPage==='page-messages'){ goDash(); } else if(currentPage==='page-chat'){ showPage('page-messages'); } else { showPage('page-dash'); } }
function toggleMenu(forceClose){ if(!isMenuAllowed()){ toast('🔒 Menu locked until 25 Dec 2026'); return; } var m=document.getElementById('menuDrop'); if(!m) return; if(forceClose){ m.classList.add('hidden'); return; } var html=''; html+='<div onclick="openMyProfile();toggleMenu(true)">👤 My Profile</div>'; html+='<div onclick="openMessages();toggleMenu(true)">💬 Messages</div>'; html+='<div onclick="openFullLeader();toggleMenu(true)">🏆 Leaderboard</div>'; html+='<div onclick="goDash();toggleMenu(true)">🏠 Dashboard</div>'; html+='<div onclick="openMenuPage();toggleMenu(true)">🎮 Menu - New Games</div>'; html+='<div onclick="openProfileFull();toggleMenu(true)">👤 Profile - Full History</div>'; html+='<div onclick="openReviewRequest(\'review\');toggleMenu(true)">⭐ Review</div>'; html+='<div onclick="openReviewRequest(\'request\');toggleMenu(true)">📩 Request</div>'; if(isDominic()){ html+='<div onclick="openUpdatePage();toggleMenu(true)">🔄 Update Server</div>'; html+='<div onclick="openServerEconomy();toggleMenu(true)">💰 Server Economy - ADMIN ONLY</div>'; html+='<div onclick="openServerInfo();toggleMenu(true)">🖥️ Server Info - ADMIN ONLY</div>'; } m.innerHTML=html; m.classList.toggle('hidden'); }
document.getElementById('menuBtn').onclick=function(e){ e.stopPropagation(); toggleMenu(); };
document.addEventListener('click',function(e){ var b=document.getElementById('menuBtn'); var m=document.getElementById('menuDrop'); if(!b||!m) return; if(b.contains(e.target)) return; if(!m.contains(e.target)) m.classList.add('hidden'); });
function hasLoggedInBefore(){ try{ if(localStorage.getItem('inf_has_account')==='yes') return true; if(user && user.name) return true; }catch(e){} return false; }
function goRegister(){ playSoundNow('enterAudio',0.45); if(hasLoggedInBefore() && user && user.name){ showPage('page-register'); document.getElementById('regSub').innerText='Checking your account...'; fetch('/api/player?name='+encodeURIComponent(user.name)).then(function(r){return r.json();}).then(function(d){ if(d && d.found){ showLogin(); document.getElementById('regSub').innerText='Welcome back! Please Login 👑'; var ln=document.getElementById('loginName'); if(ln) ln.value=user.name; } else { showRegister(); setTimeout(function(){ showWelcomePopup(); },2000); } }).catch(function(){ showRegister(); }); return; } showPage('page-register'); showRegister(); setTimeout(function(){ showWelcomePopup(); },2000); }
function showRegister(){ document.getElementById('registerForm').classList.remove('hidden'); document.getElementById('loginForm').classList.add('hidden'); document.getElementById('regSub').innerText='Create your Infinity account 👑'; }
function showLogin(){ document.getElementById('registerForm').classList.add('hidden'); document.getElementById('loginForm').classList.remove('hidden'); document.getElementById('regSub').innerText='Login to your account 👑'; }
window.welcomeChoice=function(choice){ hideWelcomeNow(); if(choice==='yes'){ setTimeout(function(){ showLogin(); var ln=document.getElementById('loginName'); if(ln && user) ln.value=user.name; },500); } else { showRegister(); } };
document.getElementById('choiceYesBtn').onclick=function(){ window.welcomeChoice('yes'); };
document.getElementById('choiceNoBtn').onclick=function(){ window.welcomeChoice('no'); };
document.getElementById('enterBtn').addEventListener('click',function(){ goRegister(); });
function saveLocal(){ try{ localStorage.setItem('inf_user',JSON.stringify(user)); localStorage.setItem('inf_wins',wins); localStorage.setItem('inf_loss',losses); localStorage.setItem('inf_stage',stageIdx); localStorage.setItem('inf_gold',myGold); localStorage.setItem('inf_gems',myGems); localStorage.setItem('inf_player_id',myPlayerID); localStorage.setItem('inf_has_account','yes'); }catch(e){} }
function doRegister(){ var n=document.getElementById('regName').value.trim(); var pw=document.getElementById('regPass').value.trim(); if(!n){ toast('Please enter your name!'); return; } if(!pw||pw.length!==4||isNaN(pw)){ toast('Password must be exactly 4 digits!'); return; } if(pw==='1234'||pw==='0000'){ toast('Password too easy!'); return; } fetch('/api/player?name='+encodeURIComponent(n)).then(function(r){return r.json();}).then(function(d){ if(d && d.found){ showLogin(); document.getElementById('loginName').value=n; toast('Account found! Please Login 👑'); return; } user={name:n,password:pw}; wins=0; losses=0; stageIdx=0; myGold=0; myGems=0; saveLocal(); syncScore(); enterDashboard('Welcome '+n+'! Registered 👑'); }).catch(function(){ user={name:n,password:pw}; saveLocal(); enterDashboard('Welcome '+n+'! Registered 👑'); }); }
function doLogin(){ var n=document.getElementById('loginName').value.trim(); var pw=document.getElementById('loginPass').value.trim(); if(!n||!pw){ toast('Enter name + password!'); return; } if(pw.length!==4){ toast('Password must be 4 digits!'); return; } fetch('/api/player?name='+encodeURIComponent(n)+'&password='+encodeURIComponent(pw)).then(function(r){return r.json();}).then(function(d){ if(d && d.found && d.password_ok!==false){ user={name:n,password:pw}; wins=d.wins||0; losses=d.losses||0; stageIdx=d.stage||0; myGold=d.gold||0; myGems=d.gems||0; myPlayerID=d.player_id||''; saveLocal(); enterDashboard('Welcome back '+n+'! 👑'); } else { showGameWarn('⚠️ Account not found / Wrong password<br>Try again or Register',true); } }).catch(function(){ toast('Network error, try again'); }); }
function enterDashboard(msg){ loggedIn=true; toast(msg); showPage('page-dash'); document.getElementById('welcomeText').innerText='Welcome, '+ (user?user.name:'Player') +' 👑'; updateGoldUI(); loadLeader(); loadMyProfile(); updateBottomNav(); }
function syncScore(){ if(!user||!loggedIn) return; fetch('/api/score',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:user.name,password:user.password,wins:wins,losses:losses,stage:stageIdx,gold:myGold,gems:myGems})}).catch(function(){}); }
function updateGoldUI(){ var g1=document.getElementById('myGoldTop'); if(g1) g1.innerText=myGold+' Gold'; var g2=document.getElementById('myGemsTop'); if(g2) g2.innerText=myGems+' Gems'; var b1=document.getElementById('bankGold'); if(b1) b1.innerText=myGold; var b2=document.getElementById('bankGems'); if(b2) b2.innerText=myGems; var p1=document.getElementById('profFullGold'); if(p1) p1.innerText=myGold; var p2=document.getElementById('profFullGems'); if(p2) p2.innerText=myGems; var p3=document.getElementById('profGold'); if(p3) p3.innerText=myGold; var p4=document.getElementById('profGems'); if(p4) p4.innerText=myGems; var id1=document.getElementById('profFullID'); if(id1) id1.innerText='ID:'+myPlayerID; var id2=document.getElementById('profIDShow'); if(id2) id2.innerText='ID:'+myPlayerID; var id3=document.getElementById('bankIDShow'); if(id3) id3.innerText='ID:'+myPlayerID; }
function goDash(){ if(!loggedIn){ showPage('page-register'); return; } showPage('page-dash'); loadLeader(); }
function loadLeader(){ fetch('/api/leaderboard').then(function(r){return r.json();}).then(function(d){ fullLeaderData=d.players||[]; var html=''; var top5=fullLeaderData.slice(0,5); top5.forEach(function(p,i){ html+='<div class="leadRow" onclick="viewOtherPlayer(\''+p.name+'\')"><span>'+(i+1)+'. '+p.name+' <small>'+p.player_id+'</small></span><span>🏆 '+p.wins+' • 🪙 '+p.gold+'</span></div>'; }); if(!html) html='No players yet'; document.getElementById('leaderList').innerHTML=html; var myRank='#-'; fullLeaderData.forEach(function(p,i){ if(user && p.name.toLowerCase()===user.name.toLowerCase()) myRank='#'+(i+1); }); var mr=document.getElementById('myRank'); if(mr) mr.innerText=myRank; }).catch(function(){}); }
function openFullLeader(){ showPage('page-leader'); fetch('/api/leaderboard').then(function(r){return r.json();}).then(function(d){ var players=d.players||[]; var html=''; players.forEach(function(p,i){ html+='<div class="leadRow" onclick="viewOtherPlayer(\''+p.name+'\')"><span>'+(i+1)+'. '+p.name+'<br><small>'+p.player_id+' • 🪙 '+p.gold+' • 💎 '+p.gems+'</small></span><span>🏆 '+p.wins+'W</span></div>'; }); document.getElementById('fullLeaderList').innerHTML=html||'No players'; }).catch(function(){}); }
function openMyProfile(){ if(!loggedIn) return; showPage('page-profile'); document.getElementById('profName').innerText=user.name; document.getElementById('profRank').innerText=document.getElementById('myRank').innerText; document.getElementById('profWins').innerText=wins; document.getElementById('profLoss').innerText=losses; updateGoldUI(); }
function openProfileFull(){ if(!loggedIn) return; showPage('page-profile-full'); document.getElementById('profFullName').innerText=user.name; document.getElementById('profFullRank').innerText=document.getElementById('myRank').innerText; document.getElementById('profFullWins').innerText=wins; document.getElementById('profFullLoss').innerText=losses; document.getElementById('profFullStage').innerText=STAGES[stageIdx]||'Beginner'; updateGoldUI(); fetch('/api/player?name='+encodeURIComponent(user.name)).then(function(r){return r.json();}).then(function(d){ if(d && d.history){ var h=''; for(var k in d.history){ h+='<div style="padding:8px;background:rgba(0,0,0,.4);border-radius:10px;margin:5px 0;font-size:13px">'+k+' — Asked: '+(d.history[k].asked||0)+' • Correct: '+(d.history[k].correct||0)+'</div>'; } document.getElementById('profFullHistory').innerHTML=h||'No history yet'; } }).catch(function(){}); }
function openBank(){ if(!loggedIn) return; showPage('page-bank'); updateGoldUI(); }
function openNotifs(){ if(!loggedIn) return; showPage('page-notifs'); fetch('/api/player?name='+encodeURIComponent(user.name)).then(function(r){return r.json();}).then(function(d){ var notifs=(d&&d.notifs)||[]; var html=''; notifs.slice().reverse().forEach(function(n){ html+='<div style="padding:12px;background:rgba(0,0,0,.4);border-radius:14px;margin:8px 0">'+n.text+'<br><small style="opacity:.7">'+(n.time||'')+'</small></div>'; }); document.getElementById('notifList').innerHTML=html||'No notifications'; var badge=document.getElementById('notifBadge'); if(badge) badge.classList.add('hidden'); }).catch(function(){}); }
function openMenuPage(){ showPage('page-menu'); renderMenuGames(); }
function openReviewRequest(type){ reviewType=type; document.getElementById('reviewTitle').innerText=type==='request'?'📩 Request':'⭐ Review'; document.getElementById('reviewText').placeholder=type==='request'?'Type your request here...':'Type your review here...'; showPage('page-review'); }
function submitReview(){ var txt=document.getElementById('reviewText').value.trim(); if(!txt){ toast('Type something first!'); return; } fetch('/api/review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:user?user.name:'Guest',type:reviewType,text:txt})}).then(function(){ toast('✅ Sent! Dominic will see it in Server Info'); document.getElementById('reviewText').value=''; goDash(); }).catch(function(){ toast('Sent!'); }); }
function openUpdatePage(){ if(!isDominic()){ toast('🔒 Only Dominic can open Update'); return; } showPage('page-update'); refreshEarningSwitch(); }
function refreshEarningSwitch(){ fetch('/api/earning_status').then(function(r){return r.json();}).then(function(d){ var sw=document.getElementById('earningSwitch'); var desc=document.getElementById('earningDesc'); if(d.earning_on){ sw.classList.remove('off'); desc.innerText='ON - Players earn Gold + Gems'; } else { sw.classList.add('off'); desc.innerText='OFF - RED • Earning stopped • Transfers + Withdraws blocked'; } }).catch(function(){}); }
function toggleEarningSwitch(){ if(!isDominic()) return; fetch('/api/toggle_earning',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:user.name,password:user.password})}).then(function(r){return r.json();}).then(function(d){ refreshEarningSwitch(); toast(d.earning_on?'✅ Earning ON - Everything back to normal':'🛑 Earning OFF - RED - Transfers + Withdraws blocked'); playWarnSound(); }).catch(function(){ toast('Toggle failed'); }); }
function doServerUpdate(){ if(!isDominic()) return; toast('🚀 Applying Update... No data lost!'); playPopupSound(); setTimeout(function(){ refreshEarningSwitch(); toast('✅ Server Updated! Earning starts 25 Dec 2026'); },1500); }
function openServerEconomy(){ if(!isDominic()){ toast('🔒 ADMIN ONLY'); return; } showPage('page-server-economy'); fetch('/api/leaderboard').then(function(r){return r.json();}).then(function(d){ var players=d.players||[]; var totalGold=0,totalGems=0; players.forEach(function(p){ totalGold+=p.gold||0; totalGems+=p.gems||0; }); document.getElementById('econPlayers').innerText=players.length; document.getElementById('econGold').innerText=totalGold; document.getElementById('econGems').innerText=totalGems; document.getElementById('econFees').innerText='5% fee on transfers - See Server Info'; }).catch(function(){}); }
function openServerInfo(){ if(!isDominic()){ toast('🔒 ADMIN ONLY'); return; } showPage('page-server-info'); fetch('/api/server_info?name=Dominic&password=2164').then(function(r){return r.json();}).then(function(d){ document.getElementById('serverPlayers').innerText=d.players||0; document.getElementById('serverEarningText').innerText=d.earning_on?'ON':'OFF'; var html=''; (d.reviews||[]).forEach(function(rv){ html+='<div style="padding:10px;border-bottom:1px solid #00ffaa">['+rv.type+'] '+rv.name+': '+rv.text+'<br><small>'+rv.time+'</small></div>'; }); html+=html; document.getElementById('serverReviewsList').innerHTML=html||'No reviews yet'; }).catch(function(){}); }
// BANK - SEND / WITHDRAW / DEPOSIT
function startSend(){ var rid=document.getElementById('sendID').value.trim().toUpperCase(); var amt=parseInt(document.getElementById('sendAmt').value||'0'); if(!rid||!amt){ toast('Enter ID + Amount'); return; } var pin=prompt('Please enter 4-Digit PIN'); if(!pin) return; fetch('/api/transfer',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sender:user.name,pin:pin,receiver_id:rid,amount:amt})}).then(function(r){return r.json();}).then(function(d){ if(d.error){ toast('⚠️ '+d.error); if(d.error.indexOf('PIN')!==-1) showGameWarn('⚠️ Warning! Pin is wrong, please check again or try again later',false); return; } myGold=d.sender_gold; saveLocal(); updateGoldUI(); toast('✅ Sent '+amt+' Gold! Fee: '+d.fee); openNotifs(); }).catch(function(){ toast('Send failed'); }); }
function startWithdraw(){ var amt=parseInt(document.getElementById('withdrawAmt').value||'0'); var cur=document.getElementById('withdrawCur').value; if(!amt){ toast('Enter amount'); return; } var pin=prompt('Please enter 4-Digit PIN for Withdraw'); if(!pin) return; fetch('/api/withdraw',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:user.name,pin:pin,amount:amt,currency:cur})}).then(function(r){return r.json();}).then(function(d){ if(d.error){ toast('⚠️ '+d.error); return; } myGold=d.gold; myGems=d.gems; saveLocal(); updateGoldUI(); toast('✅ Withdrawn '+amt+' '+cur); }).catch(function(){ toast('Withdraw failed'); }); }
function doDeposit(){ var amt=parseInt(document.getElementById('depositAmt').value||'0'); if(!amt){ toast('Enter amount'); return; } myGold+=amt; saveLocal(); updateGoldUI(); syncScore(); toast('✅ Deposited '+amt+' Gold (Game Money)'); }
function lookupAirtelID(){ var id=document.getElementById('airtelID').value.trim().toUpperCase(); document.getElementById('airtelIDShow').innerText=id||'...'; if(id.length<8) return; fetch('/api/leaderboard').then(function(r){return r.json();}).then(function(d){ var found=null; (d.players||[]).forEach(function(p){ if(p.player_id && p.player_id.toUpperCase()===id) found=p; }); if(found){ document.getElementById('airtelNameShow').innerText='✅ Found: '+found.name; document.getElementById('airtelName2').innerText=found.name; } else { document.getElementById('airtelNameShow').innerText='🔍 Searching...'; } }).catch(function(){}); }
function confirmAirtelSend(){ var rid=document.getElementById('airtelID').value.trim().toUpperCase(); var amt=parseInt(document.getElementById('airtelAmt').value||'0'); if(!rid||!amt){ toast('Enter ID + Amount'); return; } setTimeout(function(){ var pin=prompt('Please enter 4-Digit PIN'); if(!pin) return; fetch('/api/transfer',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sender:user.name,pin:pin,receiver_id:rid,amount:amt})}).then(function(r){return r.json();}).then(function(d){ if(d.error){ toast('⚠️ '+d.error); return; } myGold=d.sender_gold; saveLocal(); updateGoldUI(); toast('✅ Sent! You will receive a notification'); openNotifs(); }); },500); }
// CHALLENGE - GALAXY SHOOTER TAG
function tagPlayerForChallenge(){ var id=prompt('Enter Player ID to challenge (INF-12345678)'); if(!id) return; var game=prompt('Game? Type: Galaxy Shooter'); if(!game) game='Galaxy Shooter'; fetch('/api/challenge_send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sender:user.name,target_id:id.toUpperCase(),game:game})}).then(function(r){return r.json();}).then(function(d){ if(d.error){ toast('⚠️ '+d.error); return; } toast('✅ Challenge sent! Waiting...'); }).catch(function(){ toast('Challenge failed'); }); }
function showChallengePopup(from,game,cid){ currentChallengeId=cid; document.getElementById('challengeText').innerHTML='🎮 <b>'+from+'</b> challenged you to <b>'+game+'</b>!<br>Do you accept?'; var ov=document.getElementById('challengeOverlay'); ov.classList.remove('hidden'); ov.style.display='flex'; playPopupSound(); if(challengeTimer) clearTimeout(challengeTimer); challengeTimer=setTimeout(function(){ hideChallengePopup(); },5000); }
function hideChallengePopup(){ var ov=document.getElementById('challengeOverlay'); if(ov){ ov.classList.add('hidden'); ov.style.display='none'; } }
function respondChallenge(accept){ var cid=currentChallengeId; hideChallengePopup(); if(challengeTimer) clearTimeout(challengeTimer); fetch('/api/challenge_respond',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({challenge_id:cid,accept:accept})}).catch(function(){}); if(accept){ document.getElementById('challengeDashText').innerText='Challenge Accepted! Pick what to challenge:'; showPage('page-challenge'); } else { toast('❌ Challenge declined - Dashboard removed'); goDash(); } }
function declineChallengeDash(){ showPage('page-dash'); }
function startChallengeGame(game){ toast('🎮 Starting Challenge: '+game); if(game==='Galaxy Shooter') openGalaxyShooter(); else if(game==='Decoding') openDecodingGame(); else openRiddles(); }
function checkForChallenges(){ if(!loggedIn||!user) return; fetch('/api/player?name='+encodeURIComponent(user.name)).then(function(r){return r.json();}).then(function(d){ var notifs=(d&&d.notifs)||[]; for(var i=notifs.length-1;i>=0;i--){ if(notifs[i].type==='challenge' && notifs[i].challenge_id){ showChallengePopup(notifs[i].from||'Player',notifs[i].game||'Galaxy Shooter',notifs[i].challenge_id); break; } } if(d && d.notifs && d.notifs.length>0){ var badge=document.getElementById('notifBadge'); if(badge){ badge.innerText=d.notifs.length; badge.classList.remove('hidden'); } } }).catch(function(){}); }
setInterval(function(){ if(loggedIn) checkForChallenges(); },10000);
function openMessages(){ if(!loggedIn) return; showPage('page-messages'); document.getElementById('chatFriendList').innerHTML='<div class="card"><p>Chats load here</p><button class="btn" onclick="showPage(\'page-send-money\')">💸 Send Panel - Airtel Style</button></div>'; }
function viewOtherPlayer(name){ toast('Viewing '+name); }
function addEmoji(){ var inp=document.getElementById('msgInput'); if(inp){ inp.value+='😊'; } }
function toggleSend(){ var v=document.getElementById('msgInput').value.trim(); document.getElementById('sendBtnSmall').style.display=v?'block':'none'; }
function sendMsg(){ toast('Message sent!'); document.getElementById('msgInput').value=''; }
function blockedFeature(name){ toast('🔒 '+name+' locked until 24 Jan 2027'); }
function loadMyProfile(){ openMyProfile(); showPage('page-dash'); }
// ===== BANKS + GAME ENGINE + REWARDS =====
function P(s){ var p=s.split('|'); return {q:p[0],a:p[1],lvl:parseInt(p[2]||'0')}; }
var BANK_RIDDLE=["What has keys but cannot open locks?|A piano|0","What has a face and two hands but no arms or legs?|A clock|0","What gets wetter the more it dries?|A towel|0","What has a neck but no head?|A bottle|0","What runs but never walks?|Water|0","What has many teeth but cannot bite?|A comb|0","What can you catch but never throw?|A cold|0","What has a bed but never sleeps?|A river|0","What comes once in a minute, twice in a moment, but never in a thousand years?|The letter M|0","What has one eye but cannot see?|A needle|0"].map(P);
var BANK_BIBLE=["Who penned most Psalms?|David|0","First book of New Testament?|Matthew|0","Who was swallowed by great fish?|Jonah|0","Abraham's wife?|Sarah|0","Who betrayed Jesus for 30 silver?|Judas Iscariot|0","Shortest verse?|Jesus wept|0","Who built the ark?|Noah|0","River where Jesus was baptized?|Jordan River|0","Mother of Jesus?|Mary|0","How many books in Protestant Bible?|66|0"].map(P);
var currentMode='',currentCat='',qIndex=0,qList=[],score=0,correctCount=0,roundGold=0;
function buildOptions(correct,allAnswers){ var opts=[correct]; var pool=allAnswers.filter(function(a){return a!==correct;}); for(var i=pool.length-1;i>0;i--){ var j=(Math.random()*(i+1))|0; var t=pool[i]; pool[i]=pool[j]; pool[j]=t; } for(var k=0;k<pool.length&&opts.length<3;k++){ if(opts.indexOf(pool[k])<0) opts.push(pool[k]); } while(opts.length<3) opts.push('None of these'); for(var i=opts.length-1;i>0;i--){ var j=(Math.random()*(i+1))|0; var t=opts[i]; opts[i]=opts[j]; opts[j]=t; } return {o:opts,a:opts.indexOf(correct)}; }
function pick10(bank){ var pool=bank.slice(); for(var s=0;s<3;s++){ for(var i=pool.length-1;i>0;i--){ var j=(Math.random()*(i+1))|0; var t=pool[i]; pool[i]=pool[j]; pool[j]=t; } } var picked=pool.slice(0,10); var allAns=bank.map(function(x){return x.a;}); return picked.map(function(x){ var oo=buildOptions(x.a,allAns); return {q:x.q,o:oo.o,a:oo.a}; }); }
function startQuiz(mode,cat,bank){ currentMode=mode; currentCat=cat; qList=pick10(bank); qIndex=0; score=0; correctCount=0; roundGold=0; showPage('page-game'); document.getElementById('gameTitle').innerText=(mode==='BIBLE'?'📖 BIBLE FIGHT':'🧩 RIDDLES')+' • '+cat; showQuestion(); }
function showQuestion(){ if(qIndex>=qList.length){ finishQuiz(); return; } var q=qList[qIndex]; var html='<p style="font-size:12px;opacity:.8">Question '+(qIndex+1)+' / 10 • Correct: '+correctCount+'</p><h3>'+q.q+'</h3>'; q.o.forEach(function(opt,i){ html+='<button class="opt" onclick="answerQ('+i+')">'+opt+'</button>'; }); html+='<p style="font-size:12px;color:#ffd700">🪙 Each correct = random 50-150 Gold/Gems • Lose (less than 6 correct) = 0</p>'; document.getElementById('gameBody').innerHTML=html; }
function answerQ(i){ var q=qList[qIndex]; var wasCorrect=(i===q.a); if(wasCorrect){ correctCount++; score++; var amt=Math.floor(Math.random()*101)+50; roundGold+=amt; toast('✅ Correct! +'+amt+' Gold (pending)'); playPopupSound(); } else { toast('❌ Wrong! Correct: '+q.o[q.a]); } qIndex++; setTimeout(showQuestion,800); }
function finishQuiz(){ var isWin=correctCount>=6; var finalGold=isWin?roundGold:0; var finalGems=isWin?Math.floor(finalGold/10):0; var html='<div style="text-align:center"><div style="font-size:60px">'+(isWin?'🏆':'💔')+'</div><h2>'+(isWin?'YOU WIN!':'YOU LOSE')+'</h2><p>Correct: '+correctCount+' / 10</p>'; if(isWin){ html+='<p style="font-size:20px;color:#ffd700">🪙 Earned: '+finalGold+' Gold<br>💎 Earned: '+finalGems+' Gems</p><p style="font-size:12px;opacity:.8">Each correct gave 50-150, added together. Missed questions reduced total.</p>'; } else { html+='<p style="color:#ff6666">Lose = 0 Gold / 0 Gems<br>Win needs 6+ correct</p>'; } html+='<button class="btn" onclick="goDash()">🏠 Back to Dashboard</button></div>'; document.getElementById('gameBody').innerHTML=html; if(isWin){ myGold+=finalGold; myGems+=finalGems; saveLocal(); updateGoldUI(); syncScore(); } else { losses++; saveLocal(); syncScore(); } wins+=isWin?1:0; if(!isWin) losses++; saveLocal(); updateGoldUI(); loadLeader(); }
function openRiddles(){ showPage('page-game'); document.getElementById('gameBody').innerHTML='<h3>🧩 Pick Category</h3><button class="opt" onclick="startQuiz(\'RIDDLE\',\'General\',BANK_RIDDLE)">🧩 General Riddles</button><button class="opt" onclick="startQuiz(\'RIDDLE\',\'Funny\',BANK_RIDDLE)">😂 Funny</button><button class="opt" onclick="startQuiz(\'RIDDLE\',\'Smart\',BANK_RIDDLE)">🧠 Smart</button>'; }
function openBible(){ showPage('page-game'); document.getElementById('gameBody').innerHTML='<h3>📖 Pick Category</h3><button class="opt" onclick="startQuiz(\'BIBLE\',\'Bible\',BANK_BIBLE)">📖 Bible Fight</button>'; }
function openComing(name){ showPage('page-coming'); document.getElementById('comingName').innerText=name; if(name==='SCI-FI'){ document.getElementById('comingIcon').innerText='🚀'; document.getElementById('scifiExtra').classList.remove('hidden'); document.body.classList.add('scifi-mode'); renderSciFiGames(); var cd=document.getElementById('countDown'); if(cd) cd.innerText='5'; setTimeout(function(){ goDash(); },5000); } else { document.getElementById('comingIcon').innerText='💚'; document.getElementById('scifiExtra').classList.add('hidden'); showPage('page-messages'); openMessages(); } }
function renderMenuGames(){ var games=[['🌌','Galaxy Shooter','Tag + Challenge Online Player','openGalaxyShooter()'],['💻','Decoding / Hacking','Hack fake account with keyboard','openDecodingGame()'],['👽','Alien Riddles','10 Alien Riddles','openAlienGame()'],['🧩','Code Breaker','Break the code','openCodeBreaker()'],['🧠','Space Memory','Match the stars','openMemoryGame()'],['🔢','Laser Math','Fast math battle','openLaserMath()'],['🧩','Cyber Puzzle','Cyber puzzle 10 Qs','openCyberPuzzle()'],['⭐','Star Trader','Trade stars for Gold','openStarTrader()'],['🤖','AI Quiz Battle','Battle the AI','openAIQuiz()'],['🚀','Robot Racer','Race the robot','openRobotRacer()']]; var html=''; games.forEach(function(g){ html+='<div class="gameBoxNew" onclick="'+g[3]+'"><div style="font-size:36px">'+g[0]+'</div><h3 style="margin:5px 0">'+g[1]+'</h3><p style="font-size:13px;opacity:.8">'+g[2]+'</p><button class="btn2">▶ PLAY - Earn Gold + Gems</button></div>'; }); var el=document.getElementById('menuGamesList'); if(el) el.innerHTML=html; var el2=document.getElementById('scifiGamesList'); if(el2) el2.innerHTML=html; }
function renderSciFiGames(){ renderMenuGames(); }
// ===== GALAXY SHOOTER + CHALLENGE TAG =====
function openGalaxyShooter(){ showPage('page-game'); document.getElementById('gameTitle').innerText='🌌 GALAXY SHOOTER'; document.getElementById('gameBody').innerHTML='<div style="text-align:center"><div style="font-size:60px">🌌🚀👾</div><p>Destroy 10 aliens! Each hit = 50-150 Gold</p><div style="font-size:40px" id="alienTarget" onclick="shootAlien()">👾</div><p>Hits: <b id="shootHits">0</b> / 10 • Gold Pending: <b id="shootGold">0</b></p><button class="btn" onclick="tagPlayerForChallenge()">🏷️ Tag Online Player to Challenge</button><p style="font-size:12px;opacity:.8">Tag = sends Challenge Request popup (5 sec) to that player</p><button class="btn2" onclick="finishShooter()">🏁 Finish Game</button></div>'; window.shootHits=0; window.shootGold=0; }
function shootAlien(){ window.shootHits=(window.shootHits||0)+1; var amt=Math.floor(Math.random()*101)+50; window.shootGold=(window.shootGold||0)+amt; document.getElementById('shootHits').innerText=window.shootHits; document.getElementById('shootGold').innerText=window.shootGold; playPopupSound(); var aliens=['👾','👽','🛸','🌟','☄️']; document.getElementById('alienTarget').innerText=aliens[Math.floor(Math.random()*aliens.length)]; if(window.shootHits>=10) finishShooter(); }
function finishShooter(){ var hits=window.shootHits||0; var isWin=hits>=6; var gold=isWin?(window.shootGold||0):0; var gems=isWin?Math.floor(gold/10):0; if(isWin){ myGold+=gold; myGems+=gems; wins++; } else { losses++; } saveLocal(); updateGoldUI(); syncScore(); document.getElementById('gameBody').innerHTML='<div style="text-align:center"><h2>'+(isWin?'🏆 YOU WIN!':'💔 YOU LOSE')+'</h2><p>Hits: '+hits+' / 10</p><p>🪙 '+(isWin?gold:0)+' Gold • 💎 '+(isWin?gems:0)+' Gems</p><p style="font-size:12px">'+(isWin?'':'Lose = 0 Gold / 0 Gems')+'</p><button class="btn" onclick="goDash()">🏠 Dashboard</button></div>'; }
// ===== DECODING / HACKING GAME =====
var hackTarget=''; var hackInput='';
function openDecodingGame(){ hackTarget='INFINITY'+Math.floor(Math.random()*9000+1000); hackInput=''; showPage('page-game'); document.getElementById('gameTitle').innerText='💻 DECODING / HACKING'; document.getElementById('gameBody').innerHTML='<div style="text-align:center"><div class="hackScreen" id="hackScreen">> HACKING FAKE ACCOUNT...<br>> TARGET: ****<br>> TYPE THE CODE TO HACK<br>> HINT: Code is '+hackTarget.length+' chars, starts with INFINITY<br>> YOUR INPUT: <span id="hackInputShow"></span><span style="animation:blink 1s infinite">_</span></div><p style="font-size:12px;color:#00ffaa">Use keyboard below to type. Hack the fake account!</p><div id="hackKeyboard"></div><button class="btn" onclick="checkHack()">🔓 HACK NOW</button><button class="btn2" onclick="goDash()">❌ Abort Hack</button></div>'; var keys='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'; var kh=''; keys.split('').forEach(function(k){ kh+='<button class="hackKey" onclick="pressHackKey(\''+k+'\')">'+k+'</button>'; }); kh+='<button class="hackKey" style="width:80px" onclick="backHack()">⌫</button>'; document.getElementById('hackKeyboard').innerHTML=kh; }
function pressHackKey(k){ hackInput+=k; document.getElementById('hackInputShow').innerText=hackInput; playPopupSound(); }
function backHack(){ hackInput=hackInput.slice(0,-1); document.getElementById('hackInputShow').innerText=hackInput; }
function checkHack(){ if(hackInput===hackTarget){ var gold=Math.floor(Math.random()*101)+500; var gems=Math.floor(gold/10); myGold+=gold; myGems+=gems; wins++; saveLocal(); updateGoldUI(); syncScore(); document.getElementById('gameBody').innerHTML='<div style="text-align:center"><div style="font-size:60px">✅</div><h2>HACK SUCCESSFUL!</h2><p>Fake account hacked!</p><p>🪙 +'+gold+' Gold • 💎 +'+gems+' Gems</p><button class="btn" onclick="goDash()">🏠 Dashboard</button></div>'; } else { losses++; saveLocal(); document.getElementById('gameBody').innerHTML='<div style="text-align:center"><h2>❌ HACK FAILED</h2><p>Wrong code! Target was '+hackTarget+'</p><p>Lose = 0 Gold / 0 Gems</p><button class="btn" onclick="openDecodingGame()">🔁 Try Again</button><button class="btn2" onclick="goDash()">🏠 Dashboard</button></div>'; } }
function openAlienGame(){ startQuiz('RIDDLE','Alien',BANK_RIDDLE); }
function openCodeBreaker(){ startQuiz('RIDDLE','Code Breaker',BANK_RIDDLE); }
function openMemoryGame(){ showPage('page-game'); document.getElementById('gameTitle').innerText='🧠 SPACE MEMORY'; document.getElementById('gameBody').innerHTML='<p>Tap pairs! Demo - You Win!</p><button class="btn" onclick="winGenericGame(\'Space Memory\')">🏆 Claim Win</button>'; }
function openLaserMath(){ startQuiz('RIDDLE','Laser Math',BANK_RIDDLE); }
function openCyberPuzzle(){ startQuiz('RIDDLE','Cyber Puzzle',BANK_RIDDLE); }
function openStarTrader(){ showPage('page-game'); document.getElementById('gameTitle').innerText='⭐ STAR TRADER'; document.getElementById('gameBody').innerHTML='<p>Trade stars! You earned Gold!</p><button class="btn" onclick="winGenericGame(\'Star Trader\')">🏆 Claim Win</button>'; }
function openAIQuiz(){ startQuiz('BIBLE','AI Quiz',BANK_BIBLE); }
function openRobotRacer(){ showPage('page-game'); document.getElementById('gameTitle').innerText='🚀 ROBOT RACER'; document.getElementById('gameBody').innerHTML='<p>Race! Tap to boost!</p><button class="btn" onclick="winGenericGame(\'Robot Racer\')">🏆 Claim Win</button>'; }
function winGenericGame(name){ var gold=Math.floor(Math.random()*800)+500; var gems=Math.floor(gold/10); myGold+=gold; myGems+=gems; wins++; saveLocal(); updateGoldUI(); syncScore(); toast('🏆 '+name+' Win! +'+gold+' Gold'); goDash(); }
document.getElementById('msgFab').onclick=function(){ openMessages(); };
document.getElementById('backFab').onclick=function(){ goBack(); };
document.getElementById('profileBtn').onclick=function(){ openMyProfile(); };
document.getElementById('soundBtn').onclick=function(){ toast('🔊 Sound ON/OFF'); };
setInterval(function(){ if(loggedIn && user){ syncScore(); } },10000);
setInterval(function(){ if(loggedIn){ loadLeader(); } },20000);
window.onload=function(){ updateBottomNav(); if(user && user.name){ document.getElementById('regSub').innerText='Welcome back! Please Login 👑'; } };
</script>
</body></html>
"""
@app.route("/webhook", methods=["GET","POST"])
def webhook():
    if request.method=="GET":
        mode=request.args.get("hub.mode"); token=request.args.get("hub.verify_token"); chal=request.args.get("hub.challenge")
        if mode=="subscribe" and token==VERIFY_TOKEN: return chal,200
        return "Forbidden",403
    return jsonify({"ok":True})
@app.route("/api/logout", methods=["POST"])
def logout():
    return jsonify({"ok":True})
@app.route("/api/load_all")
def load_all():
    n=norm(request.args.get("name",""))
    if n in USERS:
        v=USERS[n]
        return jsonify({"found":True,"wins":v["wins"],"losses":v["losses"],"stage":v["stage"],"history":v.get("history",{}),"friends":v.get("friends",[]),"chats":{},"gold":v.get("gold",0),"gems":v.get("gems",0),"player_id":v.get("player_id","")})
    return jsonify({"found":False})
@app.route("/api/answer", methods=["POST"])
def answer():
    d=request.get_json() or {}
    n=norm(d.get("name"))
    if n in USERS:
        h=USERS[n].setdefault("history",{})
        q=d.get("question","")
        if q not in h: h[q]={"asked":0,"correct":0,"wrong":0}
        h[q]["asked"]+=1
        if d.get("correct"): h[q]["correct"]+=1
        else: h[q]["wrong"]+=1
        save_users()
    return jsonify({"ok":True})
if __name__=="__main__":
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
