from flask import Flask, request, jsonify
import os, json, threading, random, datetime
app = Flask(__name__)
BASE = os.path.dirname(__file__)
LEADER_FILE = os.path.join(BASE, "leaderboard.json")
MSG_FILE = os.path.join(BASE, "messages.json")
USERS = {}; MESSAGES = {}; CHALLENGES = {}; REQUESTS = []
_lock = threading.Lock()
EARNING_ON = True
EARNING_START = datetime.datetime(2026, 1, 1)
RANKS = [("Beginner",0),("Intermediate",200),("Advanced",400),("Expert",800),("Professional",1600),("National",3200),("S Rank",6400),("SS Rank",12800),("SSS Rank",25600),("SSS Classified",51200),("Godly Rank Classified",102400)]
ECO = {"gold":100000000,"gems":1000000,"bank_total":0,"fees":0,"lottery":0,"history":[100000000],"backup":10000000000}
def norm(n): return str(n or "").strip().lower()
def loadj(p):
    try:
        if os.path.exists(p):
            with open(p) as f: d=json.load(f); return d if isinstance(d,dict) else {}
    except: pass
    return {}
def gid(): return "INF-"+"".join(str(random.randint(0,9)) for _ in range(8))
def gbid(): return "Bank INF-"+"".join(str(random.randint(0,9)) for _ in range(10))
def cid(s): return "".join(c for c in str(s or "").upper() if c.isdigit())
def rank_for(w):
    r="Beginner"
    for n,need in RANKS:
        if w>=need: r=n
    return r
def ensure(v,k):
    v.setdefault("display_name",k); v.setdefault("friends",[]); v.setdefault("wins",0); v.setdefault("losses",0); v.setdefault("stage",0); v.setdefault("gold",0); v.setdefault("gems",0); v.setdefault("bank_gold",0); v.setdefault("bank_gems",0); v.setdefault("notifs",[]); v.setdefault("seen_qs",[]); v.setdefault("items",[]); v.setdefault("history",{})
    if not v.get("player_id"): v["player_id"]=gid()
    if not v.get("bank_id"): v["bank_id"]=gbid()
    return v
def load_users():
    global USERS
    d=loadj(LEADER_FILE)
    if d: USERS={norm(v.get("display_name",k) or k):ensure(v,k) for k,v in d.items()}
load_users()
try:
    if os.path.exists(MSG_FILE):
        with open(MSG_FILE) as f: MESSAGES=json.load(f)
except: pass
def save():
    try:
        with _lock:
            with open(LEADER_FILE,"w") as f: f.write(json.dumps(USERS))
    except Exception as e: print(e)
def active(): return datetime.datetime.now()>=EARNING_START and EARNING_ON
def notify(name,text,typ="info",extra=None):
    if norm(name) in USERS:
        n={"text":text,"time":str(datetime.datetime.now()),"type":typ}
        if extra: n.update(extra)
        USERS[norm(name)]["notifs"].append(n); save()
def getp(n): return USERS.get(norm(n))
@app.route("/")
def home(): return HOME
@app.route("/api/earning_status")
def es(): return jsonify({"earning_on":EARNING_ON,"active":active()})
@app.route("/api/toggle_earning",methods=["POST"])
def te():
    global EARNING_ON
    d=request.get_json() or {}
    if norm(d.get("name"))!="dominic" or str(d.get("password"))!="2164": return jsonify({"error":"Only Dominic"}),403
    EARNING_ON=not EARNING_ON; return jsonify({"earning_on":EARNING_ON,"active":active()})
@app.route("/api/player")
def gp():
    n=norm(request.args.get("name","")); pw=request.args.get("password","")
    if n in USERS:
        v=USERS[n]
        if pw and v.get("password") and str(v.get("password"))!=str(pw): return jsonify({"found":True,"password_ok":False,"player_id":v["player_id"]})
        return jsonify({"found":True,"password_ok":True,"name":v["display_name"],"wins":v["wins"],"losses":v["losses"],"stage":v["stage"],"gold":v["gold"],"gems":v["gems"],"bank_gold":v.get("bank_gold",0),"bank_gems":v.get("bank_gems",0),"player_id":v["player_id"],"bank_id":v.get("bank_id",""),"rank":rank_for(v["wins"]),"classified":v["wins"]>=3200,"friends":v["friends"],"notifs":v.get("notifs",[]),"seen_qs":v.get("seen_qs",[]),"items":v.get("items",[])})
    return jsonify({"found":False})
@app.route("/api/leaderboard")
def lb():
    mode=request.args.get("mode","pvp"); ps=[]
    for v in USERS.values(): ps.append({"name":v["display_name"],"wins":v["wins"],"losses":v["losses"],"gold":v.get("gold",0),"gems":v.get("gems",0),"player_id":v.get("player_id",""),"rank":rank_for(v["wins"]),"rank_idx":next((i for i,(rn,_) in enumerate(RANKS) if rn==rank_for(v["wins"])),0)})
    if mode=="gold": ps=sorted(ps,key=lambda x:x["gold"],reverse=True)
    elif mode=="gems": ps=sorted(ps,key=lambda x:x["gems"],reverse=True)
    elif mode=="rank": ps=sorted(ps,key=lambda x:x["rank_idx"],reverse=True)
    else: ps=sorted(ps,key=lambda x:(x["wins"]-x["losses"]),reverse=True)
    return jsonify({"players":ps})
@app.route("/api/score",methods=["POST"])
def sc():
    d=request.get_json() or {}; n=norm(d.get("name"))
    if not n: return jsonify({"error":"no name"}),400
    if n not in USERS: USERS[n]=ensure({"display_name":d.get("name"),"password":d.get("password","")},d.get("name"))
    v=USERS[n]
    if d.get("password"): v["password"]=d.get("password")
    v["wins"]=d.get("wins",v["wins"]); v["losses"]=d.get("losses",v["losses"]); v["stage"]=d.get("stage",v["stage"])
    for k in ("gold","gems","seen_qs","items"):
        if k in d: v[k]=d[k]
    save(); return jsonify({"ok":True,"gold":v["gold"],"gems":v["gems"],"player_id":v["player_id"],"rank":rank_for(v["wins"])})
def check_pin(v,pin):
    if str(v.get("password"))!=str(pin): notify(v["display_name"],"Warning! Pin is wrong.","warn"); return False
    return True
@app.route("/api/transfer",methods=["POST"])
def tr():
    d=request.get_json() or {}; s=getp(d.get("sender")); amt=int(d.get("amount",0))
    if not active(): return jsonify({"error":"Transfers blocked"}),403
    if not s: return jsonify({"error":"Sender not found"}),404
    if not check_pin(s,d.get("pin","")): return jsonify({"error":"Wrong PIN"}),403
    rid="INF-"+cid(d.get("receiver_id","")); recv=None
    for v in USERS.values():
        if v.get("player_id")==rid: recv=v; break
    if not recv: return jsonify({"error":"Receiver ID not found"}),404
    if s.get("gold",0)<amt: return jsonify({"error":"Not enough Gold"}),400
    fee=int(amt*0.05); s["gold"]-=amt; recv["gold"]=recv.get("gold",0)+(amt-fee); ECO["gold"]+=fee; ECO["fees"]+=fee; ECO["history"].append(ECO["gold"])
    notify(s["display_name"],"You sent "+str(amt)+" Gold to "+rid+".","send"); notify(recv["display_name"],"You received "+str(amt)+" Gold.","receive"); save(); return jsonify({"ok":True,"sender_gold":s["gold"]})
@app.route("/api/bank_action",methods=["POST"])
def ba():
    d=request.get_json() or {}; v=getp(d.get("name")); amt=int(d.get("amount",0)); act=d.get("action","deposit"); cur=d.get("currency","Gold")
    if not active(): return jsonify({"error":"Bank blocked"}),403
    if not v: return jsonify({"error":"Not found"}),404
    if not check_pin(v,d.get("pin","")): return jsonify({"error":"Wrong PIN"}),403
    if act=="deposit":
        if cur=="Gems":
            if v.get("gems",0)<amt: return jsonify({"error":"Not enough Gems"}),400
            v["gems"]-=amt; v["bank_gems"]=v.get("bank_gems",0)+amt
        else:
            if v.get("gold",0)<amt: return jsonify({"error":"Not enough Gold"}),400
            v["gold"]-=amt; v["bank_gold"]=v.get("bank_gold",0)+amt; ECO["gold"]+=amt; ECO["bank_total"]+=amt; ECO["history"].append(ECO["gold"])
        notify(v["display_name"],"You deposited "+str(amt)+" "+cur+".","deposit")
    else:
        if cur=="Gems":
            if v.get("bank_gems",0)<amt: return jsonify({"error":"Not enough in Bank"}),400
            v["bank_gems"]-=amt; v["gems"]=v.get("gems",0)+amt
        else:
            if v.get("bank_gold",0)<amt: return jsonify({"error":"Not enough in Bank"}),400
            v["bank_gold"]-=amt; v["gold"]=v.get("gold",0)+amt
        notify(v["display_name"],"You withdrew "+str(amt)+" "+cur+".","withdraw")
    save(); return jsonify({"ok":True,"gold":v["gold"],"gems":v["gems"],"bank_gold":v.get("bank_gold",0),"bank_gems":v.get("bank_gems",0)})
@app.route("/api/exchange",methods=["POST"])
def ex():
    d=request.get_json() or {}; v=getp(d.get("name")); amt=int(d.get("amount",0)); direction=d.get("direction","gold_to_gem")
    if not active(): return jsonify({"error":"Exchange blocked"}),403
    if not v: return jsonify({"error":"Not found"}),404
    if not check_pin(v,d.get("pin","")): return jsonify({"error":"Wrong PIN"}),403
    if direction=="gold_to_gem":
        gems=amt//100
        if gems<1: return jsonify({"error":"Need at least 100 Gold = 1 Germ"}),400
        if v.get("gold",0)<gems*100: return jsonify({"error":"Not enough Gold"}),400
        v["gold"]-=gems*100; v["gems"]=v.get("gems",0)+gems
    else:
        if v.get("gems",0)<amt: return jsonify({"error":"Not enough Gems"}),400
        v["gems"]-=amt; v["gold"]=v.get("gold",0)+amt*100
    save(); return jsonify({"ok":True,"gold":v["gold"],"gems":v["gems"]})
@app.route("/api/challenge_send",methods=["POST"])
def cs():
    d=request.get_json() or {}; s=getp(d.get("sender")); tid="INF-"+cid(d.get("target_id",""))
    if not s: return jsonify({"error":"Sender not found"}),404
    tgt=None
    for v in USERS.values():
        if v.get("player_id")==tid: tgt=v; break
    if not tgt: return jsonify({"error":"Target ID not found"}),404
    cid2="CH-"+str(random.randint(10000000,99999999))
    CHALLENGES[cid2]={"from":s["display_name"],"to":tgt["display_name"],"game":d.get("game","Galaxy Shooter"),"status":"pending","host":s["display_name"],"guest":tgt["display_name"],"host_score":0,"guest_score":0,"q_index":0}
    notify(tgt["display_name"],"CHALLENGE: "+s["display_name"]+" challenged you! Accept or Decline?","challenge",{"challenge_id":cid2,"game":d.get("game","Galaxy Shooter"),"from":s["display_name"]})
    return jsonify({"ok":True,"challenge_id":cid2})
@app.route("/api/challenge_respond",methods=["POST"])
def cr():
    d=request.get_json() or {}; c=CHALLENGES.get(d.get("challenge_id"))
    if not c: return jsonify({"error":"Not found"}),404
    c["status"]="accepted" if d.get("accept") else "declined"; return jsonify({"ok":True,"challenge":c})
@app.route("/api/challenge_pick_mode",methods=["POST"])
def cpm():
    d=request.get_json() or {}; c=CHALLENGES.get(d.get("challenge_id"))
    if not c: return jsonify({"error":"Not found"}),404
    if norm(d.get("name"))!=norm(c.get("host","")): return jsonify({"error":"Only host picks mode"}),403
    c["mode"]=d.get("mode","Riddles"); c["status"]="playing"; notify(c["guest"],"Host picked "+c["mode"]+"! 50 Questions.","challenge_start",{"challenge_id":d.get("challenge_id"),"mode":c["mode"]}); return jsonify({"ok":True,"challenge":c})
@app.route("/api/challenge_answer",methods=["POST"])
def ca():
    d=request.get_json() or {}; c=CHALLENGES.get(d.get("challenge_id"))
    if not c: return jsonify({"error":"Not found"}),404
    if d.get("correct"):
        if norm(d.get("name"))==norm(c.get("host","")): c["host_score"]+=1
        elif norm(d.get("name"))==norm(c.get("guest","")): c["guest_score"]+=1
    c["q_index"]+=1
    if c["q_index"]>=50: c["status"]="calculating"
    return jsonify({"ok":True,"challenge":c})
@app.route("/api/challenge_finish",methods=["POST"])
def cf():
    d=request.get_json() or {}; c=CHALLENGES.get(d.get("challenge_id"))
    if not c: return jsonify({"error":"Not found"}),404
    if c.get("status")=="finished": return jsonify({"ok":True,"challenge":c})
    c["status"]="finished"; winner=c["host"] if c["host_score"]>=c["guest_score"] else c["guest"]; c["winner"]=winner; bonus=random.choice([20,50,100]); c["bonus"]=bonus; c["reward_product"]=random.choice(["Infinity Cola","Infinity Burger","Mango Juice","Infinity Pizza","Energy Drink","Infinity Donut"])
    for nm in [c["host"],c["guest"]]:
        if norm(nm) in USERS:
            v=USERS[norm(nm)]; add=bonus if nm==winner else 10; v["wins"]+=add; v.setdefault("items",[]).append(c["reward_product"]); notify(nm,"Duel Finished! Winner: "+winner+". You got "+c["reward_product"]+" - Drink/Eat to claim +"+str(add)+" Wins.","duel_done",{"challenge_id":d.get("challenge_id"),"bonus":add,"product":c["reward_product"]})
    save(); return jsonify({"ok":True,"challenge":c})
@app.route("/api/consume",methods=["POST"])
def co():
    d=request.get_json() or {}; v=getp(d.get("name")); bonus=min(int(d.get("bonus",0)),100)
    if not v: return jsonify({"error":"Not found"}),404
    if not check_pin(v,d.get("pin","")): return jsonify({"error":"Wrong PIN"}),403
    if d.get("product") in v.get("items",[]): v["items"].remove(d.get("product"))
    v["wins"]+=bonus; save(); return jsonify({"ok":True,"wins":v["wins"],"bonus":bonus})
@app.route("/api/review",methods=["POST"])
def rv():
    d=request.get_json() or {}
    try:
        with open(os.path.join(BASE,"reviews.json"),"a") as f: f.write(json.dumps({"name":d.get("name"),"type":d.get("type"),"text":d.get("text"),"time":str(datetime.datetime.now())})+"\n")
    except: pass
    return jsonify({"ok":True})
@app.route("/api/server_info")
def si():
    if norm(request.args.get("name"))!="dominic" or str(request.args.get("password"))!="2164": return jsonify({"error":"Admin only"}),403
    reviews=[]
    try:
        if os.path.exists(os.path.join(BASE,"reviews.json")):
            with open(os.path.join(BASE,"reviews.json")) as f: reviews=[json.loads(l) for l in f if l.strip()]
    except: pass
    return jsonify({"players":len(USERS),"earning_on":EARNING_ON,"earning_active":active(),"reviews":reviews,"economy":ECO})
@app.route("/api/buy_item",methods=["POST"])
def bi():
    d=request.get_json() or {}; v=getp(d.get("name")); price=int(d.get("price",0))
    if not v: return jsonify({"error":"Not found"}),404
    if not check_pin(v,d.get("pin","")): return jsonify({"error":"Wrong PIN"}),403
    if v.get("gold",0)<price: return jsonify({"error":"Not enough Gold"}),400
    v["gold"]-=price; v.setdefault("items",[]).append(d.get("item","")); ECO["gold"]+=price; ECO["fees"]+=price; notify(v["display_name"],"You bought "+str(d.get("item"))+" for "+str(price)+" Gold.","shop"); save(); return jsonify({"ok":True,"gold":v["gold"],"items":v["items"]})
@app.route("/api/friends")
def fr():
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
def af():
    d=request.get_json() or {}; n=norm(d.get("name")); tid="INF-"+cid(d.get("target_id",""))
    if n not in USERS: return jsonify({"error":"Not found"}),404
    for v in USERS.values():
        if v.get("player_id")==tid:
            if v["display_name"] not in USERS[n]["friends"]: USERS[n]["friends"].append(v["display_name"])
            if USERS[n]["display_name"] not in v["friends"]: v["friends"].append(USERS[n]["display_name"])
            notify(v["display_name"],USERS[n]["display_name"]+" added you as friend!","friend"); save(); return jsonify({"ok":True})
    return jsonify({"error":"ID not found"}),404
@app.route("/api/chat_send",methods=["POST"])
def chats():
    d=request.get_json() or {}; s=norm(d.get("sender")); t=norm(d.get("to")); text=str(d.get("text",""))[:500]
    if s not in USERS or t not in USERS: return jsonify({"error":"User not found"}),404
    key="|".join(sorted([s,t])); MESSAGES.setdefault(key,[]).append({"from":USERS[s]["display_name"],"to":USERS[t]["display_name"],"text":text,"kind":d.get("kind","text"),"time":str(datetime.datetime.now())}); notify(t,"New message from "+USERS[s]["display_name"]+": "+text[:60],"chat")
    try:
        with open(MSG_FILE,"w") as f: f.write(json.dumps(MESSAGES))
    except: pass
    return jsonify({"ok":True})
@app.route("/api/chat_get")
def chatg():
    a=norm(request.args.get("a","")); b=norm(request.args.get("b","")); return jsonify({"messages":MESSAGES.get("|".join(sorted([a,b])),[])})
@app.route("/api/request_money",methods=["POST"])
def rm():
    d=request.get_json() or {}; v=getp(d.get("name")); amt=d.get("amount"); cur=d.get("currency","Gold")
    if not v: return jsonify({"error":"Not found"}),404
    if cur=="Gold" and amt and int(amt)>100000000: return jsonify({"error":"Gold max 100,000,000"}),400
    if cur=="Gems" and amt and int(amt)>100000: return jsonify({"error":"Germ max 100,000"}),400
    rid="RQ-"+str(random.randint(10000000,99999999)); REQUESTS.append({"id":rid,"from":v["display_name"],"from_id":v.get("player_id"),"amount":amt,"currency":cur,"message":str(d.get("message",""))[:200],"status":"pending"}); notify("dominic","SECRET REQUEST: "+v["display_name"]+" ("+str(v.get("player_id"))+") wants "+str(amt or "amount not given")+" "+cur+".","request",{"request_id":rid,"from":v["display_name"],"amount":amt,"currency":cur}); return jsonify({"ok":True,"id":rid})
@app.route("/api/request_approve",methods=["POST"])
def ra():
    d=request.get_json() or {}
    if norm(d.get("admin"))!="dominic" or str(d.get("pin"))!="2164": return jsonify({"error":"Only Dominic 2164"}),403
    amt=int(d.get("amount",0)); cur=d.get("currency","Gold")
    for r in REQUESTS:
        if r["id"]==d.get("request_id"):
            r["status"]="approved"
            if cur=="Gold": ECO["gold"]-=amt
            else: ECO["gems"]-=amt
            ECO["history"].append(ECO["gold"])
            for v in USERS.values():
                if v.get("player_id")==r["from_id"]:
                    if cur=="Gold": v["gold"]=v.get("gold",0)+amt
                    else: v["gems"]=v.get("gems",0)+amt
                    notify(v["display_name"],"You received "+str(amt)+" "+cur+" from Server Economy.","request_ok")
            notify("dominic","You sent "+str(amt)+" "+cur+" to "+r["from"]+".","request_sent"); save(); return jsonify({"ok":True,"economy":ECO})
    return jsonify({"error":"Request not found"}),404
@app.route("/api/lottery",methods=["POST"])
def lo():
    d=request.get_json() or {}; v=getp(d.get("name")); bet=int(d.get("bet",0)); cur=d.get("currency","Gold")
    if not v: return jsonify({"error":"Not found"}),404
    if not check_pin(v,d.get("pin","")): return jsonify({"error":"Wrong PIN"}),403
    if cur=="Gold":
        if v.get("gold",0)<bet: return jsonify({"error":"Not enough Gold"}),400
        v["gold"]-=bet
    else:
        if v.get("gems",0)<bet: return jsonify({"error":"Not enough Gems"}),400
        v["gems"]-=bet
    win=random.random()<0.5
    if win:
        prize=bet*2
        if cur=="Gold": v["gold"]+=prize; ECO["gold"]-=bet; ECO["lottery"]-=bet
        else: v["gems"]+=prize; ECO["gems"]-=bet
        notify(v["display_name"],"LOTTERY WIN! You won "+str(prize)+" "+cur+"!","lottery"); res={"win":True,"prize":prize}
    else:
        if cur=="Gold": ECO["gold"]+=bet; ECO["lottery"]+=bet
        else: ECO["gems"]+=bet
        notify(v["display_name"],"LOTTERY LOSE! You lost "+str(bet)+" "+cur+".","lottery"); res={"win":False,"lost":bet}
    ECO["history"].append(ECO["gold"]); save(); return jsonify({"ok":True,"result":res,"gold":v["gold"],"gems":v["gems"]})
@app.route("/api/economy")
def ec():
    if norm(request.args.get("name"))!="dominic" or str(request.args.get("password"))!="2164": return jsonify({"error":"Admin only"}),403
    return jsonify({"economy":ECO,"requests":REQUESTS})
@app.route("/api/emergency",methods=["POST"])
def em():
    d=request.get_json() or {}
    if norm(d.get("name"))!="dominic" or str(d.get("pin"))!="2164": return jsonify({"error":"Only Dominic"}),403
    if ECO["gold"]>=0: return jsonify({"error":"Emergency only if economy is NEGATIVE"}),400
    if ECO["backup"]<10000000000: return jsonify({"error":"Backup not enough"}),400
    ECO["gold"]+=500000000000; ECO["backup"]-=500000000000
    if ECO["backup"]<0: ECO["backup"]=0
    ECO["history"].append(ECO["gold"]); return jsonify({"ok":True,"economy":ECO})
@app.route("/webhook",methods=["GET","POST"])
def wh():
    if request.method=="GET":
        if request.args.get("hub.mode")=="subscribe" and request.args.get("hub.verify_token")=="infinity": return request.args.get("hub.challenge"),200
        return "Forbidden",403
    return jsonify({"ok":True})
HOME=r"""<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>INFINITY BOT v19</title><link href="https://fonts.googleapis.com/css2?family=Great+Vibes&family=Poppins:wght@400;700;900&display=swap" rel="stylesheet"><style>*{box-sizing:border-box}body{margin:0;font-family:Poppins,Arial;color:#fff;background:radial-gradient(circle at 50% 20%,#3a0a5e,#12002b 70%);min-height:100vh}.cursive{font-family:'Great Vibes',cursive}.topbar{display:flex;justify-content:space-between;align-items:center;padding:8px 14px}.profile{width:46px;height:46px;border-radius:50%;background:linear-gradient(135deg,#ff006e,#ffd700);display:flex;align-items:center;justify-content:center;font-size:20px;border:2px solid #fff;cursor:pointer}.center{min-height:82vh;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:20px}.crownBig{font-size:90px}.enterBtn{margin-top:20px;padding:16px 70px;font-family:'Great Vibes',cursive;font-size:48px;border:none;border-radius:60px;background:linear-gradient(90deg,#ff006e,#ffd700,#00e5ff);color:#000;cursor:pointer}.card{background:rgba(255,255,255,.08);border:2px solid rgba(255,255,255,.35);border-radius:26px;padding:20px;margin:14px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.box{background:rgba(255,255,255,.15);border:2px solid #fff;border-radius:24px;padding:22px 10px;text-align:center;cursor:pointer}.box span{font-size:38px;display:block}.btn{width:100%;padding:14px;border:none;border-radius:25px;font-weight:900;background:#ffd700;margin:6px 0;cursor:pointer}.btn2{width:100%;padding:13px;border-radius:25px;border:2px solid #00e5ff;background:transparent;color:#00e5ff;font-weight:900;margin:6px 0;cursor:pointer}.opt{width:100%;padding:13px;margin:7px 0;border-radius:16px;border:2px solid #fff;background:rgba(0,0,0,.5);color:#fff;font-weight:700;cursor:pointer;text-align:left}input,select,textarea{width:100%;padding:14px;border-radius:14px;border:2px solid #ffd700;margin:8px 0;font-size:16px;background:#fff;color:#000}.hidden{display:none!important}.leadRow{display:flex;justify-content:space-between;align-items:center;padding:10px 12px;background:rgba(0,0,0,.45);border-radius:14px;margin:6px 0;cursor:pointer}.toast{position:fixed;top:70px;left:50%;transform:translateX(-50%);background:#fff;color:#000;padding:12px 18px;border-radius:20px;font-weight:700;z-index:999;max-width:90%;text-align:center}.gameOverlay{position:fixed;inset:0;background:rgba(0,0,0,.75);display:flex;align-items:center;justify-content:center;padding:16px;z-index:500}.gamePopup{background:#2b005e;border:3px solid #ffd700;border-radius:28px;padding:22px 18px;max-width:420px;width:100%;text-align:center}.choiceRow{display:flex;gap:12px;margin-top:16px}.choiceBox{flex:1;padding:18px 8px;border-radius:20px;cursor:pointer;font-weight:900;font-size:18px;border:3px solid #fff}.choiceNo{background:#ff2222;color:#fff}.choiceYes{background:#00cc44;color:#000}.bottomNav{position:fixed;bottom:0;left:0;right:0;background:rgba(0,0,0,.85);border-top:2px solid #ffd700;display:flex;justify-content:space-around;padding:10px 0 14px;z-index:100}.bottomNav div{font-size:28px;cursor:pointer;text-align:center}.bottomNav small{display:block;font-size:10px;color:#ffd700}.walletCard{background:linear-gradient(135deg,#ffd700,#ff006e);color:#000;border-radius:24px;padding:18px;text-align:center}.switch{width:70px;height:36px;background:#00cc44;border-radius:99px;position:relative;cursor:pointer;border:2px solid #fff}.switch.off{background:#ff2222}.switchKnob{position:absolute;top:3px;left:34px;width:28px;height:28px;background:#fff;border-radius:50%}.switch.off .switchKnob{left:3px}.pinInput{font-size:28px;text-align:center;letter-spacing:12px}.tabRow{display:flex;gap:8px}.tabBox{flex:1;padding:12px 4px;border-radius:16px;background:rgba(255,255,255,.15);border:2px solid #ffd700;text-align:center;cursor:pointer;font-weight:900;font-size:13px}.tabBox.active{background:#ffd700;color:#000}.bigBankBox{padding:22px 10px;border-radius:24px;border:2px solid #fff;text-align:center;cursor:pointer;background:rgba(255,255,255,.15)}.idPrefix{display:flex;align-items:center;background:#fff;border-radius:14px;border:2px solid #ffd700;padding:0 10px;margin:8px 0}.idPrefix b{color:#000}.idPrefix input{border:none;flex:1;margin:0}.shopGrid{display:grid;grid-template-columns:1fr 1fr;gap:10px}.shopBox{background:rgba(255,255,255,.15);border:2px solid #fff;border-radius:18px;padding:14px 8px;text-align:center;cursor:pointer}.catBox{padding:10px 6px;border-radius:16px;border:2px solid #ffd700;background:rgba(255,255,255,.12);text-align:center;cursor:pointer;font-size:12px;font-weight:900}.catBox.active{background:#ffd700;color:#000}</style></head><body>
<div class="topbar"><div><span id="catTime" style="font-size:12px;background:rgba(0,0,0,.55);border:1px solid #ffd700;padding:5px 9px;border-radius:20px;display:inline-block">00:00:00 CAT</span><br><span id="catDate" style="font-size:10px;background:rgba(0,0,0,.45);border:1px solid rgba(255,215,0,.6);padding:3px 8px;border-radius:20px;display:inline-block;margin-top:4px">Central Africa</span><br><div style="font-weight:900;margin-top:4px">INFINITY BOT</div></div><div id="topRight" class="hidden" style="display:flex;flex-direction:column;align-items:flex-end;gap:2px"><div style="display:flex;gap:8px;align-items:center"><div id="soundBtn" style="width:32px;height:32px;border-radius:50%;background:rgba(0,0,0,.55);border:1px solid #ffd700;display:flex;align-items:center;justify-content:center;cursor:pointer">SOUND</div><div onclick="openShop()" style="width:32px;height:32px;border-radius:50%;background:rgba(0,0,0,.55);border:1px solid #ffd700;display:flex;align-items:center;justify-content:center;cursor:pointer">SHOP</div><div class="profile" id="profileBtn">USER</div></div><div id="menuBtn" style="width:32px;height:32px;border-radius:50%;background:rgba(0,0,0,.55);border:1px solid #ffd700;display:flex;align-items:center;justify-content:center;cursor:pointer;margin-right:7px">MENU</div></div></div>
<script>function pad2(n){return(n<10?"0":"")+n}function updateCatTime(){try{var now=new Date();var cat=new Date(now.getTime()+now.getTimezoneOffset()*60000+2*3600000);var days=["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];var months=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];document.getElementById("catTime").textContent=pad2(cat.getHours())+":"+pad2(cat.getMinutes())+":"+pad2(cat.getSeconds())+" CAT";document.getElementById("catDate").textContent=days[cat.getDay()]+", "+pad2(cat.getDate())+" "+months[cat.getMonth()]+" "+cat.getFullYear()+" - Central Africa"}catch(e){}}updateCatTime();setInterval(updateCatTime,1000);</script>
<div id="menuDrop" class="hidden" style="position:absolute;top:130px;right:10px;background:#1a1a2e;border:2px solid #ffd700;border-radius:16px;padding:8px;z-index:500;min-width:200px"></div><div id="toast" class="toast hidden"></div>
<div id="pinOverlay" class="gameOverlay hidden" style="display:none;z-index:900"><div class="gamePopup"><h2>Enter PIN</h2><p id="pinDesc">Enter your 4-digit PIN</p><input id="pinInput" class="pinInput" placeholder="...." maxlength="4" inputmode="numeric" type="password"><div class="choiceRow"><div class="choiceBox choiceNo" onclick="closePin()">Cancel</div><div class="choiceBox choiceYes" onclick="confirmPin()">Confirm</div></div></div></div>
<div id="secretOverlay" class="gameOverlay hidden" style="display:none;z-index:920"><div class="gamePopup"><h2>Secret Request</h2><p style="font-size:12px">Secret - only you + Dominic can see this. Masked</p><input id="reqMsg" type="password" placeholder="Secret message"><input id="reqAmt" type="password" inputmode="numeric" placeholder="Amount (optional)"><select id="reqCur"><option>Gold</option><option>Gems</option></select><div class="choiceRow"><div class="choiceBox choiceNo" onclick="closeSecret()">Cancel</div><div class="choiceBox choiceYes" onclick="sendMoneyRequest()">Send Secret</div></div></div></div>
<div id="idOverlay" class="gameOverlay hidden" style="display:none;z-index:900"><div class="gamePopup"><h2 id="idTitle">Enter Player ID</h2><p>Type digits only - INF- is added automatically</p><div class="idPrefix"><b>INF-</b><input id="idInput" placeholder="12345678" inputmode="numeric" maxlength="8"></div><div class="choiceRow"><div class="choiceBox choiceNo" onclick="closeIdPopup()">Cancel</div><div class="choiceBox choiceYes" onclick="confirmIdPopup()">Confirm</div></div></div></div>
<div id="challengeOverlay" class="gameOverlay hidden" style="display:none;z-index:800"><div class="gamePopup"><h2>CHALLENGE REQUEST</h2><p id="challengeText"></p><div class="choiceRow"><div class="choiceBox choiceNo" onclick="respondChallenge(false)">Decline</div><div class="choiceBox choiceYes" onclick="respondChallenge(true)">Accept</div></div><p style="font-size:12px">Auto closes in 5 seconds...</p></div></div>
<div id="page-welcome" class="gameOverlay hidden" style="display:none;z-index:950"><div class="gamePopup"><h2>Do you already have an account?</h2><p>Yes = Login - No = Register</p><div class="choiceRow"><div class="choiceBox choiceNo" onclick="welcomeChoice('no')">No</div><div class="choiceBox choiceYes" onclick="welcomeChoice('yes')">Yes</div></div></div></div>
<div id="page-home" class="center"><div style="font-size:26px">STAR HEART</div><div class="crownBig">CROWN</div><h1 class="cursive" style="font-size:68px;margin:5px">Infinity Bot</h1><p style="letter-spacing:3px;font-weight:900">DOMINIC MASTIRIA</p><p>Riddles - Bible Fight - Sci-Fi - WhatsApp</p><button class="enterBtn" id="enterBtn" type="button" onclick="enterClicked();return false;">Enter</button><p style="font-size:12px;margin-top:12px">Press ENTER to Continue</p><p id="jsError" style="color:#ff8888;font-size:12px"></p></div>
<div id="page-register" class="hidden" style="max-width:520px;margin:0 auto;padding:20px 14px"><div class="card" style="text-align:center"><h1 class="cursive" style="font-size:48px;margin:5px">Register</h1><div id="registerForm"><label>Your Name:</label><input id="regName" placeholder="Your Name" maxlength="20"><label>4-Digit Password:</label><input id="regPass" placeholder="...." maxlength="4" inputmode="numeric" type="password"><p style="font-size:12px;color:#ffd700">Do NOT use 1234 or 0000</p><button class="btn" type="button" onclick="doRegister()">REGISTER</button><p>Already have an account? <b style="color:#ffd700;cursor:pointer" onclick="showLogin()">Click here to Login</b></p></div><div id="loginForm" class="hidden"><label>Your Name:</label><input id="loginName" placeholder="Your Name"><label>4-Digit Password:</label><input id="loginPass" placeholder="...." maxlength="4" inputmode="numeric" type="password"><button class="btn" type="button" onclick="doLogin()">LOGIN</button><p>New here? <b style="color:#ffd700;cursor:pointer" onclick="showRegister()">Click here to Register</b></p></div></div></div>
<div id="page-dash" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div style="text-align:center"><h2 class="cursive" style="font-size:44px;margin:10px 0" id="welcomeText">Welcome, Player</h2><span>Rank: <b id="myRank">#-</b></span> <span>Stage: <b id="myStage">Beginner</b></span></div><div class="grid"><div class="box" onclick="openRiddles()"><span>RIDDLE</span><b>RIDDLES</b></div><div class="box" onclick="openBible()"><span>BIBLE</span><b>BIBLE FIGHT</b></div><div class="box" onclick="openSciFi()"><span>SCI-FI</span><b>SCI-FI</b></div><div class="box" onclick="openMessages()"><span>CHAT</span><b>WHATSAPP</b></div></div><div class="card"><h3 style="text-align:center;margin:0">TOP 5</h3><div id="leaderList">Loading...</div><button class="btn2" onclick="openFullLeader()">View Full Leaderboard</button></div></div>
<div id="page-leader" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h3 style="text-align:center;margin:0">LEADERBOARD</h3><div class="tabRow" style="margin:12px 0"><div class="tabBox" id="tabGold" onclick="setLeaderMode('gold')">Gold</div><div class="tabBox" id="tabGems" onclick="setLeaderMode('gems')">Germ</div><div class="tabBox" id="tabRank" onclick="setLeaderMode('rank')">Rank</div><div class="tabBox active" id="tabPvp" onclick="setLeaderMode('pvp')">PvP</div></div><p id="leaderModeText" style="text-align:center;font-size:12px">Ranked by Wins - Losses</p><div id="fullLeaderList">Loading...</div></div></div>
<div id="page-game" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 id="gameTitle" style="text-align:center">Game</h2><div id="gameBody"></div></div></div>
<div id="page-coming" class="hidden" style="max-width:520px;margin:0 auto;padding:40px 20px 90px;text-align:center"><h1 class="cursive" style="font-size:54px">Coming Soon</h1><h2>SCI-FI</h2><p>Launching on <b>25th December 2026</b></p><div style="font-size:60px;font-weight:900;color:#ffd700" id="countDown">5</div></div>
<div id="page-bank" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">BANK</h2><div class="walletCard"><div>BANK PROFILE</div><div id="bankIDShow">Bank INF-0000000000</div><div>Bank Gold: <b id="bankGold">0</b></div><div>Bank Germ: <b id="bankGems">0</b></div><div>Wallet - <span id="walletGold">0</span> | <span id="walletGems">0</span></div></div><div class="grid" style="margin-top:14px"><div class="bigBankBox" onclick="openSendPage()">Send Gold</div><div class="bigBankBox" onclick="openWithdrawPage()">Withdraw</div><div class="bigBankBox" onclick="openDepositPage()">Deposit</div><div class="bigBankBox" onclick="openMyProfile()">Profile</div></div><div class="bigBankBox" style="margin-top:14px" onclick="openExchangePage()">Exchange<br><small>100 Gold = 1 Germ</small></div></div></div>
<div id="page-send" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">SEND GOLD</h2><div class="walletCard"><div>Your Wallet</div><div><b id="sendPageGold">0</b> | <b id="sendPageGems">0</b></div><div>Your ID: <b id="sendPageMyID">INF-00000000</b></div></div><label>Receiver ID:</label><div class="idPrefix"><b>INF-</b><input id="sendDigits" placeholder="12345678" inputmode="numeric" maxlength="8"></div><label>Amount:</label><input id="sendAmt" type="number" placeholder="Amount"><button class="btn" onclick="doSend()">SEND NOW</button><p style="font-size:12px">Fee 5% to Server Economy</p></div></div>
<div id="page-withdraw" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">WITHDRAW</h2><div class="walletCard"><div>Bank: <b id="wdBankGold">0</b> | <b id="wdBankGems">0</b></div><div>Wallet: <b id="wdWalletGold">0</b> | <b id="wdWalletGems">0</b></div><div>Bank ID: <b id="wdBankID">Bank INF-</b></div></div><label>Amount:</label><input id="withdrawAmt" type="number" placeholder="Amount"><select id="withdrawCur"><option>Gold</option><option>Gems</option></select><button class="btn" onclick="doWithdraw()">WITHDRAW NOW</button></div></div>
<div id="page-deposit" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">DEPOSIT</h2><div class="walletCard"><div>Wallet: <b id="depWalletGold">0</b> | <b id="depWalletGems">0</b></div><div>Bank: <b id="depBankGold">0</b> | <b id="depBankGems">0</b></div><div>Bank ID: <b id="depBankID">Bank INF-</b></div></div><label>Amount:</label><input id="depositAmt" type="number" placeholder="Amount"><select id="depositCur"><option>Gold</option><option>Gems</option></select><button class="btn" onclick="doDeposit()">DEPOSIT NOW</button></div></div>
<div id="page-exchange" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">EXCHANGE</h2><div class="walletCard"><div>Wallet: <b id="exWalletGold">0</b> | <b id="exWalletGems">0</b></div></div><div class="bigBankBox" onclick="openExchange('gold_to_gem')"><b>Gold to Germ</b><br><small>100 Gold = 1 Germ</small></div><div class="bigBankBox" style="margin-top:10px" onclick="openExchange('gem_to_gold')"><b>Germ to Gold</b><br><small>1 Germ = 100 Gold</small></div><div id="exchangeForm" style="margin-top:12px"></div></div></div>
<div id="page-profile" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card" style="text-align:center"><h2 id="profName">Player</h2><p id="profIDShow">ID:INF-00000000</p><p id="profBankID">Bank INF-0000000000</p><p>Rank: <b id="profRank">#-</b></p><p>Wins: <b id="profWins">0</b> | Losses: <b id="profLoss">0</b></p><p>Stage: <b id="profStage">Beginner</b></p><p>Gold: <b id="profGold">0</b> | Germ: <b id="profGems">0</b></p><p>Bank: <b id="profBankGold">0</b> | <b id="profBankGems">0</b></p><button class="btn2" onclick="openSecret()">Secret</button></div><div class="card"><h3>INVENTORY - My Items</h3><div id="profInventory">No items yet</div><div id="consumeBox"></div></div></div>
<div id="page-other" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card" style="text-align:center"><h2 id="otherName">Player</h2><div id="otherClassified" class="hidden"><h3>Warning</h3><p>You cannot view this profile. Sorry please level up</p></div><div id="otherNormal"><p>Rank: <b id="otherRank">#-</b></p><p><b id="otherWins">0</b> Win | <b id="otherLoss">0</b> Lose</p><div id="otherActions"></div></div></div></div>
<div id="page-notifs" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">NOTIFICATIONS</h2><div id="notifList">No notifications</div></div></div>
<div id="page-menu" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">MENU - 11 GAMES</h2><div id="menuGamesList"></div></div></div>
<div id="page-economy" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><div style="display:flex;justify-content:space-between;align-items:center"><h2 style="margin:0">SERVER ECONOMY</h2><button class="btn" style="width:auto;background:#ff2222;color:#fff;padding:10px 14px" onclick="doEmergency()">Emergency</button></div><div class="grid"><div class="walletCard"><div>Server Gold</div><div id="ecoGold">0</div></div><div class="walletCard"><div>Server Germ</div><div id="ecoGems">0</div></div><div class="bigBankBox"><div>From Banks</div><b id="ecoBank">0</b></div><div class="bigBankBox"><div>From Fees</div><b id="ecoFees">0</b></div><div class="bigBankBox"><div>From Lottery</div><b id="ecoLottery">0</b></div><div class="bigBankBox"><div>Backup</div><b id="ecoBackup">0</b></div></div><h3>CRYPTO - Economy Since Day 1</h3><canvas id="ecoChart" width="480" height="160" style="width:100%;background:#000;border:2px solid #00ffaa;border-radius:14px"></canvas><h3>SECRET MONEY REQUESTS - DOMINIC ONLY</h3><div id="ecoRequests">No requests</div></div></div>
<div id="page-lottery" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">LOTTERY</h2><p style="text-align:center">50% Win / 50% Lose<br>Win = 2x bet</p><label>Your Bet:</label><input id="lotBet" type="number" placeholder="e.g. 1000"><select id="lotCur"><option>Gold</option><option>Gems</option></select><button class="btn" onclick="playLottery()">SPIN LOTTERY</button><div id="lotResult" style="text-align:center;margin-top:12px"></div></div></div>
<div id="page-update" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">UPDATE SERVER - DOMINIC ONLY</h2><div style="background:#000010;border:2px solid #00e5ff;border-radius:20px;padding:16px"><p>SPACEX UPDATE CONSOLE</p><p>CHECKING UPDATE... DOWNLOADING CHRISTMAS UPDATE v19... APPLYING 10000 SHOP PRODUCTS... OK APPLYING 11 GAMES... OK SYNCING PLAYERS... NO DATA LOST READY - Earning</p><div style="display:flex;justify-content:space-between;align-items:center;margin-top:16px;background:rgba(255,255,255,.1);padding:14px;border-radius:16px"><div><div style="font-size:20px;font-weight:900">Earning</div><div id="earningDesc">ON</div></div><div class="switch" id="earningSwitch" onclick="toggleEarningSwitch()"><div class="switchKnob"></div></div></div></div><button class="btn" onclick="doServerUpdate()">APPLY UPDATE NOW</button></div></div>
<div id="page-server-info" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">SERVER INFO - DOMINIC ONLY</h2><div>PLAYERS: <span id="serverPlayers">0</span></div><div>EARNING: <span id="serverEarningText">ON</span></div><h3>Reviews</h3><div id="serverReviewsList">Loading...</div></div></div>
<div id="page-review" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center" id="reviewTitle">Review</h2><textarea id="reviewText" style="height:140px" placeholder="Type your review or request..."></textarea><button class="btn" onclick="submitReview()">SEND</button></div></div>
<div id="page-challenge" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">CHALLENGE DASHBOARD</h2><p id="challengeDashText" style="text-align:center"></p><p style="text-align:center">Host picks mode - 50 Questions, first to answer wins point</p><div class="grid"><div class="box" onclick="hostPickMode('Bible Fight')"><span>BIBLE</span><b>Bible Fight</b></div><div class="box" onclick="hostPickMode('Riddles')"><span>RIDDLE</span><b>Riddles</b></div><div class="box" onclick="hostPickMode('Galaxy Shooter')"><span>GALAXY</span><b>Galaxy Shooter</b></div><div class="box" onclick="hostPickMode('Decoding')"><span>CODE</span><b>Decoding</b></div></div><div id="duelBox"></div><button class="btn2" onclick="declineChallengeDash()">Decline / Close</button></div></div>
<div id="page-messages" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h1 style="text-align:center;margin:0">WhatsApp</h1><p style="text-align:center">Friends - Chat - Voice Call - Voice Notes</p><div style="display:flex;gap:8px"><div class="idPrefix" style="flex:1"><b>INF-</b><input id="addFriendDigits" placeholder="Add friend ID" inputmode="numeric" maxlength="8"></div><button class="btn" style="width:auto;padding:12px 18px" onclick="addFriendById()">Add</button></div><div id="chatFriendList"></div></div></div>
<div id="page-chat" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">Chat <span id="chatWith">Friend</span></h2><div style="display:flex;gap:8px;justify-content:center;margin:10px 0"><button class="btn2" style="width:auto" onclick="startVoiceCall()">Voice Call</button><button class="btn2" style="width:auto" onclick="toggleVoiceNote()">Voice Note</button></div><div id="callBanner" class="hidden" style="background:#00cc44;color:#000;padding:12px;border-radius:14px;text-align:center;font-weight:900">Calling... <span id="callTimer">00:00</span> <button onclick="endVoiceCall()" style="background:#ff2222;color:#fff;border:none;padding:8px 14px;border-radius:12px;font-weight:900">End Call</button></div><div id="chatBox" style="background:#1a1a2e;border-radius:20px;padding:12px;min-height:260px;max-height:360px;overflow-y:auto"></div><div style="display:flex;gap:8px;margin-top:10px"><input id="msgInput" placeholder="Message..." style="flex:1"><button class="btn" style="width:70px" onclick="sendMsg()">Send</button></div></div></div>
<div id="backFab" style="position:fixed;left:16px;bottom:16px;width:58px;height:58px;border-radius:50%;background:#1a1a2e;display:none;align-items:center;justify-content:center;font-size:28px;color:#ffd700;border:3px solid #ffd700;cursor:pointer;z-index:60">Back</div>
<div id="msgFab" style="position:fixed;right:16px;bottom:16px;width:62px;height:62px;border-radius:50%;background:linear-gradient(135deg,#ff006e,#ffd700,#00e5ff);display:none;align-items:center;justify-content:center;font-size:30px;border:3px solid #fff;cursor:pointer;z-index:60">Chat</div>
<div id="bottomNav" class="bottomNav hidden"><div onclick="goDash()">Home</div><div onclick="openFullLeader()">Leader</div><div onclick="openBank()">Bank</div><div onclick="openNotifs()">Notify</div></div>
<audio id="dashAudio" loop preload="auto" style="display:none"></audio>
<script>
window.addEventListener("error",function(e){var el=document.getElementById("jsError");if(el)el.textContent="JS Error: "+e.message});
var user=null;try{user=JSON.parse(localStorage.getItem("inf_user")||"null")}catch(e){}
var wins=0,losses=0,myGold=0,myGems=0,myPlayerID="",myBankID="";
try{wins=parseInt(localStorage.getItem("inf_wins")||"0")||0;losses=parseInt(localStorage.getItem("inf_loss")||"0")||0;myGold=parseInt(localStorage.getItem("inf_gold")||"0")||0;myGems=parseInt(localStorage.getItem("inf_gems")||"0")||0;myPlayerID=localStorage.getItem("inf_player_id")||"";myBankID=localStorage.getItem("inf_bank_id")||""}catch(e){}
var stageIdx=0,loggedIn=false,currentPage="page-home",seenQs=[];try{seenQs=JSON.parse(localStorage.getItem("inf_seen")||"[]")}catch(e){seenQs=[]}
var currentChallengeId=null,challengeTimer=null,reviewType="review",pinCallback=null,leaderMode="pvp",idCallback=null,chatWithName="",callInterval=null,callSecs=0,mediaRecorder=null,shopCat="All",duel=null,duelTimer=null;
function isDominic(){return user&&user.name&&user.name.toLowerCase()==="dominic"&&user.password==="2164"}
var soundOn=true,audioCtx=null,dashAudio=null;
function beep(f,d){if(!soundOn)return;try{if(!audioCtx)audioCtx=new(window.AudioContext||window.webkitAudioContext)();var o=audioCtx.createOscillator(),g=audioCtx.createGain();o.connect(g);g.connect(audioCtx.destination);o.frequency.value=f||880;g.gain.value=0.12;o.start();setTimeout(function(){o.stop()},d||150)}catch(e){}}
function playClick(){beep(880,120)}function playWin(){beep(880,120);setTimeout(function(){beep(1100,150)},150);setTimeout(function(){beep(1320,200)},300)}function playLose(){beep(200,300)}
function startDashLoop(){try{if(!dashAudio)dashAudio=document.getElementById("dashAudio");if(!dashAudio)return;if(!dashAudio.src)dashAudio.src="https://cdn.pixabay.com/audio/2025/06/12/audio_0ea789b238.mp3";dashAudio.loop=true;dashAudio.volume=0.6;if(soundOn){var p=dashAudio.play();if(p&&p.catch)p.catch(function(){})}}catch(e){}}
function stopDashLoop(){try{if(dashAudio)dashAudio.pause()}catch(e){}}
function specialWelcome(n,pw){var x=(n||"").toLowerCase().trim();if(x==="britney"||x==="kayula")return"Welcome MY Fiance";if(x==="blessing")return"Welcome Avatar";if(x==="lubuto")return"Welcome Desk Bender";if(x==="dominic"&&pw==="2164")return"Welcome Infinity Emperor";return"Welcome, "+n}
function toast(m){var t=document.getElementById("toast");if(!t)return;t.innerText=m;t.classList.remove("hidden");setTimeout(function(){t.classList.add("hidden")},4500)}
function showPage(id){currentPage=id;var pages=["page-home","page-register","page-dash","page-leader","page-game","page-coming","page-bank","page-send","page-withdraw","page-deposit","page-exchange","page-profile","page-other","page-notifs","page-menu","page-update","page-server-info","page-review","page-challenge","page-messages","page-chat","page-economy","page-lottery"];pages.forEach(function(p){var el=document.getElementById(p);if(el){el.classList.add("hidden");el.style.display="none"}});var tg=document.getElementById(id);if(tg){tg.classList.remove("hidden");tg.style.display="block"}window.scrollTo(0,0);updateVisibility()}
function updateVisibility(){var r=document.getElementById("topRight"),nv=document.getElementById("bottomNav"),b=document.getElementById("backFab"),msg=document.getElementById("msgFab");var isEnter=(currentPage==="page-home"||currentPage==="page-register");var isDash=(currentPage==="page-dash");if(isEnter){if(r){r.classList.add("hidden");r.style.display="none"}if(nv)nv.classList.add("hidden");if(b)b.style.display="none";if(msg)msg.style.display="none";stopDashLoop()}else if(loggedIn&&isDash){if(r){r.classList.remove("hidden");r.style.display="flex"}if(nv)nv.classList.remove("hidden");if(b)b.style.display="none";if(msg)msg.style.display="flex";startDashLoop()}else if(loggedIn){if(r){r.classList.add("hidden");r.style.display="none"}if(nv)nv.classList.add("hidden");if(b)b.style.display="flex";if(msg)msg.style.display="flex";stopDashLoop()}else{if(r){r.classList.add("hidden");r.style.display="none"}if(nv)nv.classList.add("hidden");if(b)b.style.display="none";if(msg)msg.style.display="none";stopDashLoop()}}
function goDash(){if(!loggedIn){showPage("page-register");return}showPage("page-dash");loadLeader()}
function goBack(){if(currentPage==="page-register")showPage("page-home");else if(currentPage==="page-chat")showPage("page-messages");else goDash()}
function enterClicked(){playClick();goRegister()}
function goRegister(){showPage("page-register");showRegister();setTimeout(function(){var ov=document.getElementById("page-welcome");if(ov){ov.classList.remove("hidden");ov.style.display="flex";beep(880,200)}},100)}
function welcomeChoice(c){var ov=document.getElementById("page-welcome");if(ov){ov.classList.add("hidden");ov.style.display="none"}if(c==="yes")showLogin();else showRegister()}
function showRegister(){var a=document.getElementById("registerForm"),b=document.getElementById("loginForm");if(a){a.classList.remove("hidden");a.style.display="block"}if(b){b.classList.add("hidden");b.style.display="none"}}
function showLogin(){var a=document.getElementById("registerForm"),b=document.getElementById("loginForm");if(a){a.classList.add("hidden");a.style.display="none"}if(b){b.classList.remove("hidden");b.style.display="block"}}
function saveLocal(){try{localStorage.setItem("inf_user",JSON.stringify(user));localStorage.setItem("inf_wins",wins);localStorage.setItem("inf_loss",losses);localStorage.setItem("inf_gold",myGold);localStorage.setItem("inf_gems",myGems);localStorage.setItem("inf_player_id",myPlayerID);localStorage.setItem("inf_bank_id",myBankID);localStorage.setItem("inf_seen",JSON.stringify(seenQs))}catch(e){}}
function doRegister(){var n=document.getElementById("regName").value.trim();var pw=document.getElementById("regPass").value.trim();if(!n){toast("Enter name");return}if(!pw||pw.length!==4||isNaN(pw)){toast("Password must be exactly 4 digits");return}if(pw==="1234"||pw==="0000"){toast("Password too easy");return}fetch("/api/player?name="+encodeURIComponent(n)).then(function(r){return r.json()}).then(function(d){if(d&&d.found){showLogin();document.getElementById("loginName").value=n;toast("Account found! Please Login");return}user={name:n,password:pw};wins=0;losses=0;myGold=0;myGems=0;seenQs=[];saveLocal();syncScore();enterDashboard(specialWelcome(n,pw))}).catch(function(){user={name:n,password:pw};saveLocal();enterDashboard(specialWelcome(n,pw))})}
function doLogin(){var n=document.getElementById("loginName").value.trim();var pw=document.getElementById("loginPass").value.trim();if(!n||!pw){toast("Enter name + password");return}fetch("/api/player?name="+encodeURIComponent(n)+"&password="+encodeURIComponent(pw)).then(function(r){return r.json()}).then(function(d){if(d&&d.found&&d.password_ok!==false){user={name:n,password:pw};wins=d.wins||0;losses=d.losses||0;myGold=d.gold||0;myGems=d.gems||0;myPlayerID=d.player_id||"";myBankID=d.bank_id||"";seenQs=d.seen_qs||[];saveLocal();enterDashboard(specialWelcome(n,pw))}else{toast("Account not found / Wrong password")}})}
function enterDashboard(msg){loggedIn=true;toast(msg);startDashLoop();showPage("page-dash");document.getElementById("welcomeText").innerText=msg;loadLeader();loadMyProfileData()}
function syncScore(){if(!user)return;fetch("/api/score",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,password:user.password,wins:wins,losses:losses,stage:stageIdx,gold:myGold,gems:myGems,seen_qs:seenQs})}).catch(function(){})}
function loadMyProfileData(){if(!user)return;fetch("/api/player?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){if(!d||!d.found)return;myPlayerID=d.player_id;myBankID=d.bank_id||myBankID;myGold=d.gold;myGems=d.gems;var e=function(id,v){var x=document.getElementById(id);if(x)x.innerText=v};e("myRank","#-");e("myStage",d.rank||"Beginner");e("bankGold",d.bank_gold||0);e("bankGems",d.bank_gems||0);e("bankIDShow",d.bank_id||myBankID);e("walletGold",d.gold);e("walletGems",d.gems)}).catch(function(){})}
function loadLeader(){fetch("/api/leaderboard?mode=pvp").then(function(r){return r.json()}).then(function(d){var ps=d.players||[];var html="";ps.slice(0,5).forEach(function(p,i){html+="<div class=\"leadRow\" onclick=\"viewOtherPlayer('"+p.name+"')\"><span>"+(i+1)+". "+p.name+"</span><span>"+p.wins+"W - "+p.losses+"L</span></div>"});document.getElementById("leaderList").innerHTML=html||"No players yet"}).catch(function(){document.getElementById("leaderList").innerHTML="No players yet"})}
function setLeaderMode(m){leaderMode=m;["gold","gems","rank","pvp"].forEach(function(x){var el=document.getElementById("tab"+x.charAt(0).toUpperCase()+x.slice(1));if(el)el.classList.remove("active")});var act=document.getElementById("tab"+m.charAt(0).toUpperCase()+m.slice(1));if(act)act.classList.add("active");openFullLeader()}
function openFullLeader(){showPage("page-leader");fetch("/api/leaderboard?mode="+leaderMode).then(function(r){return r.json()}).then(function(d){var ps=d.players||[];var html="";var label=leaderMode==="gold"?"Ranked by Total Gold":leaderMode==="gems"?"Ranked by Total Germ":leaderMode==="rank"?"Ranked by Rank Level":"Ranked by Wins - Losses";document.getElementById("leaderModeText").innerText=label;ps.forEach(function(p,i){var extra=leaderMode==="gold"?p.gold+" Gold":leaderMode==="gems"?p.gems+" Germ":leaderMode==="rank"?p.rank:p.wins+"W - "+p.losses+"L";html+="<div class=\"leadRow\" onclick=\"viewOtherPlayer('"+p.name+"')\"><span>"+(i+1)+". "+p.name+"<br><small>"+p.player_id+"</small></span><span>"+extra+"</span></div>"});document.getElementById("fullLeaderList").innerHTML=html||"No players"})}
function viewOtherPlayer(name){if(!user)return;fetch("/api/player?name="+encodeURIComponent(name)).then(function(r){return r.json()}).then(function(d){if(!d||!d.found)return;showPage("page-other");document.getElementById("otherName").innerText=d.name;if(d.classified){document.getElementById("otherClassified").classList.remove("hidden");document.getElementById("otherNormal").classList.add("hidden")}else{document.getElementById("otherClassified").classList.add("hidden");document.getElementById("otherNormal").classList.remove("hidden");document.getElementById("otherRank").innerText=d.rank;document.getElementById("otherWins").innerText=d.wins;document.getElementById("otherLoss").innerText=d.losses;document.getElementById("otherActions").innerHTML="<button class=\"btn\" onclick=\"tagPlayer('"+d.player_id+"')\">Challenge / Invite This Player</button><button class=\"btn2\" onclick=\"openBankSendTo('"+d.player_id+"')\">Send Gold</button>"}})}
function openMyProfile(){if(!loggedIn)return;showPage("page-profile");fetch("/api/player?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){if(!d||!d.found)return;var e=function(id,v){var x=document.getElementById(id);if(x)x.innerText=v};e("profName",specialWelcome(d.name,user.password));e("profIDShow","ID:"+d.player_id);e("profBankID",d.bank_id);e("profRank","#-");e("profWins",d.wins);e("profLoss",d.losses);e("profStage",d.rank);e("profGold",d.gold);e("profGems",d.gems);e("profBankGold",d.bank_gold||0);e("profBankGems",d.bank_gems||0);var inv=d.items||[];var ih="";if(!inv.length)ih="<p>No items yet - buy in Shop</p>";else inv.forEach(function(it){ih+="<div style=\"padding:10px;background:rgba(0,0,0,.4);border-radius:12px;margin:6px 0\">"+it+"</div>"});document.getElementById("profInventory").innerHTML=ih;var cb=document.getElementById("consumeBox");if(cb){var drink=inv.find(function(x){return x.indexOf("Cola")>=0||x.indexOf("Juice")>=0||x.indexOf("Drink")>=0});var food=inv.find(function(x){return x.indexOf("Burger")>=0||x.indexOf("Pizza")>=0||x.indexOf("Donut")>=0});var h2="";if(drink)h2+="<button class=\"btn\" onclick=\"consumeProduct('"+drink+"')\">Drink "+drink+" - Claim Wins</button>";if(food)h2+="<button class=\"btn2\" onclick=\"consumeProduct('"+food+"')\">Eat "+food+" - Claim Wins</button>";cb.innerHTML=h2}})}
function openSecret(){var ov=document.getElementById("secretOverlay");if(ov){ov.classList.remove("hidden");ov.style.display="flex"}}
function closeSecret(){var ov=document.getElementById("secretOverlay");if(ov){ov.classList.add("hidden");ov.style.display="none"}}
function sendMoneyRequest(){var msg=document.getElementById("reqMsg").value;var amt=document.getElementById("reqAmt").value;var cur=document.getElementById("reqCur").value;closeSecret();fetch("/api/request_money",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,amount:amt||"",currency:cur,message:msg})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}toast("Secret request sent to Dominic");document.getElementById("reqMsg").value="";document.getElementById("reqAmt").value=""})}
function consumeProduct(product){openPin("Enter PIN to Drink/Eat "+product,function(pin){var bonus=[20,50,100][Math.floor(Math.random()*3)];fetch("/api/consume",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,product:product,bonus:bonus})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}wins=d.wins;saveLocal();syncScore();toast("You consumed "+product+" +"+bonus+" Wins! (Max 100)");playWin();openMyProfile()})})}
function openBank(){if(!loggedIn)return;showPage("page-bank");loadMyProfileData()}
function openBankSendTo(id){openSendPage();var el=document.getElementById("sendDigits");if(el)el.value=id.replace("INF-","")}
function loadBankInfo(cb){fetch("/api/player?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){if(!d||!d.found)return;myGold=d.gold;myGems=d.gems;if(cb)cb(d)})}
function openSendPage(){showPage("page-send");loadBankInfo(function(d){document.getElementById("sendPageGold").innerText=d.gold;document.getElementById("sendPageGems").innerText=d.gems;document.getElementById("sendPageMyID").innerText=d.player_id})}
function openWithdrawPage(){showPage("page-withdraw");loadBankInfo(function(d){document.getElementById("wdBankGold").innerText=d.bank_gold||0;document.getElementById("wdBankGems").innerText=d.bank_gems||0;document.getElementById("wdWalletGold").innerText=d.gold;document.getElementById("wdWalletGems").innerText=d.gems;document.getElementById("wdBankID").innerText=d.bank_id})}
function openDepositPage(){showPage("page-deposit");loadBankInfo(function(d){document.getElementById("depWalletGold").innerText=d.gold;document.getElementById("depWalletGems").innerText=d.gems;document.getElementById("depBankGold").innerText=d.bank_gold||0;document.getElementById("depBankGems").innerText=d.bank_gems||0;document.getElementById("depBankID").innerText=d.bank_id})}
function openExchangePage(){showPage("page-exchange");loadBankInfo(function(d){document.getElementById("exWalletGold").innerText=d.gold;document.getElementById("exWalletGems").innerText=d.gems});document.getElementById("exchangeForm").innerHTML=""}
function openExchange(dir){var h="";if(dir==="gold_to_gem"){h="<h3>Gold to Germ</h3><p>100 Gold = 1 Germ</p><label>Enter amount of Gold:</label><input id=\"exAmt\" type=\"number\" placeholder=\"e.g. 500\"><button class=\"btn\" onclick=\"doExchange('gold_to_gem')\">Confirm Exchange</button>"}else{h="<h3>Germ to Gold</h3><p>1 Germ = 100 Gold</p><label>Enter amount of Germ:</label><input id=\"exAmt\" type=\"number\" placeholder=\"e.g. 5\"><button class=\"btn\" onclick=\"doExchange('gem_to_gold')\">Confirm Exchange</button>"}document.getElementById("exchangeForm").innerHTML=h}
function doSend(){var digits=document.getElementById("sendDigits").value.replace(/[^0-9]/g,"");var amt=parseInt(document.getElementById("sendAmt").value||"0");if(digits.length<8||!amt){toast("Enter 8-digit ID + Amount");return}openPin("Enter PIN to send "+amt+" Gold",function(pin){fetch("/api/transfer",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({sender:user.name,pin:pin,receiver_id:"INF-"+digits,amount:amt,currency:"Gold"})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.sender_gold;saveLocal();toast("Sent!");playWin();openNotifs()})})}
function doWithdraw(){var amt=parseInt(document.getElementById("withdrawAmt").value||"0");var cur=document.getElementById("withdrawCur").value;if(!amt){toast("Enter amount");return}openPin("Enter PIN to withdraw "+amt+" "+cur,function(pin){fetch("/api/bank_action",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,amount:amt,action:"withdraw",currency:cur})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.gold;myGems=d.gems;saveLocal();loadMyProfileData();toast("Withdrawn!");openNotifs()})})}
function doDeposit(){var amt=parseInt(document.getElementById("depositAmt").value||"0");var cur=document.getElementById("depositCur").value;if(!amt){toast("Enter amount");return}openPin("Enter PIN to deposit "+amt+" "+cur,function(pin){fetch("/api/bank_action",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,amount:amt,action:"deposit",currency:cur})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.gold;myGems=d.gems;saveLocal();loadMyProfileData();toast("Deposited!");openNotifs()})})}
function doExchange(dir){var amt=parseInt(document.getElementById("exAmt").value||"0");if(!amt){toast("Enter amount");return}openPin("Enter PIN to confirm Exchange",function(pin){fetch("/api/exchange",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,amount:amt,direction:dir})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.gold;myGems=d.gems;saveLocal();toast("Exchange done!");loadMyProfileData()})})}
function openNotifs(){if(!loggedIn)return;showPage("page-notifs");fetch("/api/player?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){var ns=(d&&d.notifs)||[];var html="";ns.slice().reverse().forEach(function(n){html+="<div style=\"padding:12px;background:rgba(0,0,0,.4);border-radius:14px;margin:8px 0\">"+n.text+"<br><small>"+(n.time||"")+"</small></div>"});document.getElementById("notifList").innerHTML=html||"No notifications";var b=document.getElementById("notifBadge");if(b)b.classList.add("hidden")})}
function openMenuPage(){showPage("page-menu");renderMenuGames()}
function renderMenuGames(){var games=[["Riddles","openRiddles()"],["Bible Fight","openBible()"],["Sci-Fi","openSciFi()"],["Galaxy Shooter","openGalaxyShooter()"],["Lottery","openLottery()"],["Shop","openShop()"],["Bank","openBank()"],["WhatsApp","openMessages()"],["Challenge","openChallengeDash()"],["Economy","openEconomy()"]];var h="";games.forEach(function(g){h+="<button class=\"btn2\" onclick=\""+g[1]+"\">"+g[0]+"</button>"});document.getElementById("menuGamesList").innerHTML=h}
function openReviewRequest(t){reviewType=t;document.getElementById("reviewTitle").innerText=t==="request"?"Request":"Review";showPage("page-review")}
function submitReview(){var txt=document.getElementById("reviewText").value.trim();if(!txt){toast("Type something");return}fetch("/api/review",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user?user.name:"Guest",type:reviewType,text:txt})}).then(function(){toast("Sent!");document.getElementById("reviewText").value="";goDash()})}
function openUpdatePage(){if(!isDominic()){toast("Only Dominic");return}showPage("page-update");refreshEarningSwitch()}
function refreshEarningSwitch(){fetch("/api/earning_status").then(function(r){return r.json()}).then(function(d){var sw=document.getElementById("earningSwitch");var desc=document.getElementById("earningDesc");if(!sw||!desc)return;if(d.earning_on){sw.classList.remove("off");desc.innerText="ON"}else{sw.classList.add("off");desc.innerText="OFF - RED"}})}
function toggleEarningSwitch(){if(!isDominic())return;fetch("/api/toggle_earning",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,password:user.password})}).then(function(r){return r.json()}).then(function(d){refreshEarningSwitch();toast(d.earning_on?"Earning ON":"Earning OFF")})}
function doServerUpdate(){if(!isDominic())return;toast("Applying Update...");setTimeout(function(){refreshEarningSwitch();toast("Server Updated!")},1500)}
function openServerInfo(){if(!isDominic()){toast("ADMIN ONLY");return}showPage("page-server-info");fetch("/api/server_info?name=Dominic&password=2164").then(function(r){return r.json()}).then(function(d){document.getElementById("serverPlayers").innerText=d.players||0;document.getElementById("serverEarningText").innerText=d.earning_on?"ON":"OFF";var html="";(d.reviews||[]).forEach(function(rv){html+="<div style=\"padding:10px;border-bottom:1px solid #00ffaa\">["+rv.type+"] "+rv.name+": "+rv.text+"</div>"});document.getElementById("serverReviewsList").innerHTML=html||"No reviews"})}
function fmtPrice(n){if(n>=1000000000000)return(n/1000000000000)+" Trillion Gold";if(n>=1000000000)return(n/1000000000)+" Billion Gold";if(n>=1000000)return(n/1000000)+" Million Gold";if(n>=1000)return(n/1000)+"K Gold";return n+" Gold"}
function openLottery(){if(!loggedIn)return;showPage("page-lottery")}
function playLottery(){var bet=parseInt(document.getElementById("lotBet").value||"0");var cur=document.getElementById("lotCur").value;if(!bet){toast("Enter bet");return}openPin("Enter PIN to spin Lottery "+bet+" "+cur,function(pin){fetch("/api/lottery",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,bet:bet,currency:cur})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.gold;myGems=d.gems;saveLocal();document.getElementById("lotResult").innerHTML=d.result.win?"<h2 style=\"color:#00ff88\">YOU WON "+d.result.prize+" "+cur+"!</h2>":"<h2 style=\"color:#ff5555\">You lost "+d.result.lost+" "+cur+"</h2>";if(d.result.win)playWin();else playLose()})})}
function openEconomy(){if(!isDominic()){toast("Dominic only");return}showPage("page-economy");fetch("/api/economy?name=Dominic&password=2164").then(function(r){return r.json()}).then(function(d){var e=d.economy||{};document.getElementById("ecoGold").innerText=e.gold||0;document.getElementById("ecoGems").innerText=e.gems||0;document.getElementById("ecoBank").innerText=e.bank_total||0;document.getElementById("ecoFees").innerText=e.fees||0;document.getElementById("ecoLottery").innerText=e.lottery||0;document.getElementById("ecoBackup").innerText=e.backup||0;var req=d.requests||[];var h="";req.forEach(function(rq){h+="<div style=\"padding:12px;background:rgba(0,0,0,.4);border-radius:14px;margin:8px 0\">"+rq.from+" ("+rq.from_id+") wants "+rq.amount+" "+rq.currency+" - "+rq.message+" <button class=\"btn\" style=\"margin-top:8px\" onclick=\"approveReq('"+rq.id+"',"+rq.amount+",'"+rq.currency+"')\">Approve</button></div>"});document.getElementById("ecoRequests").innerHTML=h||"No requests";var cv=document.getElementById("ecoChart");if(cv){var ctx=cv.getContext("2d");ctx.clearRect(0,0,480,160);ctx.strokeStyle="#00ffaa";ctx.lineWidth=3;ctx.beginPath();var hist=e.history||[0];hist.forEach(function(v,i){var x=i/(Math.max(1,hist.length-1))*460+10;var y=150-(v/(Math.max(1,Math.max.apply(null,hist)))*120);if(i===0)ctx.moveTo(x,y);else ctx.lineTo(x,y)});ctx.stroke()}})}
function approveReq(id,amt,cur){openPin("Enter PIN to approve "+amt+" "+cur,function(pin){fetch("/api/request_approve",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({admin:"dominic",pin:pin,request_id:id,amount:amt,currency:cur})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}toast("Approved!");openEconomy()})})}
function doEmergency(){if(!isDominic())return;openPin("Enter PIN for Emergency",function(pin){fetch("/api/emergency",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}toast("Emergency: +500 Billion!");openEconomy()})})}
var RIDDLES=[["I speak without a mouth and hear without ears. What am I?","Echo","Voice","Shadow","Wind",0],["What has keys but cannot open locks?","Piano","Door","Map","Book",0],["The more you take, the more you leave behind. What am I?","Footsteps","Time","Money","Water",0],["What has a face and two hands but no arms or legs?","Clock","Man","Robot","Mirror",0],["What gets wetter the more it dries?","Towel","Rain","Sponge","Soap",0],["What has a neck but no head?","Bottle","Guitar","Shirt","Snake",0],["What comes once in a minute, twice in a moment, but never in a thousand years?","Letter M","Time","Sun","Moon",0],["I am tall when I am young and short when I am old. What am I?","Candle","Tree","Man","Shadow",0],["What has many needles but never sews?","Christmas Tree","Cactus","Pine","Sewing",0],["What can you catch but never throw?","Cold","Ball","Fish","Dream",0]];
var BIBLE_Q=[["Who built the ark?","Noah","Moses","Abraham","David",0],["Who killed Goliath?","David","Saul","Solomon","Samson",0],["Who was swallowed by a big fish?","Jonah","Peter","Paul","Daniel",0],["How many days did God create the world?","7","6","5","3",0],["Who led Israel out of Egypt?","Moses","Aaron","Joshua","Joseph",0],["Who betrayed Jesus?","Judas","Peter","Thomas","John",0],["Where was Jesus born?","Bethlehem","Nazareth","Jerusalem","Egypt",0],["Who was the first man?","Adam","Noah","Abraham","Moses",0],["How many disciples did Jesus have?","12","10","11","7",0],["Who wrote most Psalms?","David","Solomon","Moses","Asaph",0]];
var currentQ=null,currentGame="";
function showQuiz(title,pool){currentGame=title;showPage("page-game");document.getElementById("gameTitle").innerText=title;var idx=Math.floor(Math.random()*pool.length);currentQ=pool[idx];var h="<p style=\"font-size:18px;font-weight:700\">"+currentQ[0]+"</p><p>Wins: "+wins+" | Gold: "+myGold+"</p>";for(var i=1;i<=4;i++){h+="<button class=\"opt\" onclick=\"answerQuiz("+i+")\">"+currentQ[i]+"</button>"}h+="<button class=\"btn2\" onclick=\"goDash()\">Back to Dashboard</button>";document.getElementById("gameBody").innerHTML=h}
function answerQuiz(choice){if(!currentQ)return;var correct=(choice===currentQ[5]+1);if(correct){wins+=1;myGold+=50;playWin();toast("Correct! +1 Win +50 Gold")}else{losses+=1;playLose();toast("Wrong! Correct: "+currentQ[currentQ[5]+1])}saveLocal();syncScore();setTimeout(function(){if(currentGame.indexOf("Riddle")>=0)showQuiz("RIDDLES",RIDDLES);else if(currentGame.indexOf("Bible")>=0)showQuiz("BIBLE FIGHT",BIBLE_Q);else showQuiz(currentGame,RIDDLES)},900)}
function openRiddles(){showQuiz("RIDDLES",RIDDLES)}
function openBible(){showQuiz("BIBLE FIGHT",BIBLE_Q)}
function openSciFi(){showPage("page-game");document.getElementById("gameTitle").innerText="SCI-FI - 11 GAMES";var games=[["Galaxy Shooter","openGalaxyShooter()"],["Decoding","openSciFi()"],["Riddles","openRiddles()"],["Bible Fight","openBible()"],["Lottery","openLottery()"],["Shop","openShop()"],["Challenge","openChallengeDash()"],["WhatsApp","openMessages()"],["Bank","openBank()"],["Menu","openMenuPage()"],["Coming Soon","openComing()"]];var h="<p>Pick a game:</p>";games.forEach(function(g){h+="<button class=\"btn2\" onclick=\""+g[1]+"\">"+g[0]+"</button>"});document.getElementById("gameBody").innerHTML=h}
function openComing(){showPage("page-coming");var c=5;var el=document.getElementById("countDown");if(el)el.innerText=c;var iv=setInterval(function(){c--;if(el)el.innerText=c;if(c<=0){clearInterval(iv);goDash()}},1000)}
function openGalaxyShooter(){showPage("page-game");document.getElementById("gameTitle").innerText="GALAXY SHOOTER";document.getElementById("gameBody").innerHTML="<p style=\"text-align:center\">Shoot the aliens! Tap SHOOT to earn Gold.</p><p style=\"text-align:center\">Wins: "+wins+" | Gold: "+myGold+"</p><button class=\"btn\" onclick=\"shootAlien()\">SHOOT ALIEN +50 Gold</button><button class=\"btn2\" onclick=\"openChallengeDash()\">Invite Player to Duel</button><button class=\"btn2\" onclick=\"goDash()\">Back</button>"}
function shootAlien(){myGold+=50;wins+=1;saveLocal();syncScore();playWin();toast("Alien destroyed! +50 Gold +1 Win");openGalaxyShooter()}
var SHOP_CATS=[["All","SHOP"],["Food","FOOD"],["Drinks","DRINK"],["Cars","CAR"],["House","HOUSE"],["Equipment","EQUIP"],["Clothes","CLOTHES"],["Tech","TECH"],["Sport","SPORT"],["Beauty","BEAUTY"],["Pets","PET"],["Games","GAME"]];
var SHOP_DATA={Food:["Burger","Pizza","Shawarma","Chicken","Rice","Pasta","Donut","Cake","Samosa","Fries"],Drinks:["Cola","Mango Juice","Energy Drink","Water","Milkshake","Coffee","Tea","Orange Juice","Lemonade","Smoothie"],Cars:["Toyota","BMW","Lamborghini","Ferrari","Tesla","Mercedes","Audi","Range Rover","Hilux","Nissan"],House:["Villa","Mansion","Apartment","Cottage","Bungalow","Penthouse","Farm House","Beach House","Castle","Studio"],Equipment:["Sword","Shield","Laser Gun","Helmet","Armor","Bow","Axe","Rocket","Drone","Spaceship"],Clothes:["Jacket","T-Shirt","Jeans","Dress","Shoes","Cap","Hoodie","Suit","Sneakers","Watch"],Tech:["Phone","Laptop","Tablet","PS5","Headphones","Camera","Smart TV","Drone","VR Headset","Keyboard"],Sport:["Football","Basketball","Tennis Racket","Bicycle","Gym Kit","Skateboard","Boxing Gloves","Dumbbells","Jersey","Boots"],Beauty:["Perfume","Lipstick","Face Cream","Hair Oil","Makeup Kit","Nails","Lotion","Shampoo","Mirror","Brush"],Pets:["Dog","Cat","Parrot","Fish","Rabbit","Horse","Monkey","Turtle","Hamster","Bird"],Games:["Galaxy Shooter","Bible Fight","Riddles","Decoding","Space Race","Puzzle","Chess","Cards","Racing","Fighting"]};
function getShopItems(cat){var out=[];var cats=cat==="All"?Object.keys(SHOP_DATA):[cat];cats.forEach(function(c){var base=SHOP_DATA[c]||[];for(var i=0;i<1000;i++){var name=base[i%base.length]+" "+(i+1);var price=100+(i*37)%90000;out.push({name:name,cat:c,price:price})}});return out}
function openShop(){showPage("page-game");document.getElementById("gameTitle").innerText="INFINITY SHOP - 10000 Products";renderShop()}
function renderShop(){var h="<p style=\"text-align:center\">Gold: "+myGold+" | Tap a category:</p><div style=\"display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px\">";SHOP_CATS.forEach(function(c){h+="<div class=\"catBox "+(shopCat===c[0]?"active":"")+"\" onclick=\"setShopCat('"+c[0]+"')\">"+c[1]+"<br>"+c[0]+"</div>"});h+="</div><input id=\"shopSearch\" placeholder=\"Search shop...\" oninput=\"renderShopList()\" style=\"margin-top:12px\"><div id=\"shopList\" class=\"shopGrid\" style=\"margin-top:10px\"></div><button class=\"btn2\" onclick=\"goDash()\">Back</button>";document.getElementById("gameBody").innerHTML=h;renderShopList()}
function setShopCat(c){shopCat=c;renderShop()}
function renderShopList(){var list=document.getElementById("shopList");if(!list)return;var q=(document.getElementById("shopSearch")?document.getElementById("shopSearch").value.toLowerCase():"");var items=getShopItems(shopCat);if(q)items=items.filter(function(it){return it.name.toLowerCase().indexOf(q)>=0});var show=items.slice(0,60);var h="";show.forEach(function(it){h+="<div class=\"shopBox\" onclick=\"buyShopItem('"+it.name.replace(/'/g,"")+"',"+it.price+")\"><div>"+it.name+"</div><div>"+fmtPrice(it.price)+"</div><div>"+it.cat+"</div></div>"});h+="<p style=\"grid-column:1/-1;text-align:center;font-size:12px\">Showing "+show.length+" of "+items.length+" (10000 total in shop)</p>";list.innerHTML=h}
function buyShopItem(name,price){openPin("Enter PIN to buy "+name+" for "+price+" Gold",function(pin){fetch("/api/buy_item",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,item:name,price:price})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.gold;saveLocal();toast("Bought "+name+"!");playWin();renderShop()})})}
function openChallengeDash(){if(!loggedIn)return;showPage("page-challenge");document.getElementById("challengeDashText").innerText="You: "+user.name+" ("+myPlayerID+") - Wins: "+wins;document.getElementById("duelBox").innerHTML="<p style=\"text-align:center\">Invite a friend by ID, or challenge from Leaderboard.</p><button class=\"btn\" onclick=\"inviteById()\">Invite by Player ID</button>"}
function inviteById(){openIdPopup("Enter Friend INF- ID to Invite",function(fullId){fetch("/api/challenge_send",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({sender:user.name,target_id:fullId,game:"Galaxy Shooter"})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}currentChallengeId=d.challenge_id;toast("Invite sent! Waiting for Accept...");openChallengeDash()})})}
function tagPlayer(pid){fetch("/api/challenge_send",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({sender:user.name,target_id:pid,game:"Galaxy Shooter"})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}currentChallengeId=d.challenge_id;toast("Challenge sent!");openChallengeDash()})}
function checkForChallenges(){if(!user)return;fetch("/api/player?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){if(!d||!d.notifs)return;var ch=d.notifs.slice().reverse().find(function(n){return n.type==="challenge"&&n.challenge_id});if(ch){currentChallengeId=ch.challenge_id;var ov=document.getElementById("challengeOverlay");document.getElementById("challengeText").innerText=ch.text;if(ov){ov.classList.remove("hidden");ov.style.display="flex";if(challengeTimer)clearTimeout(challengeTimer);challengeTimer=setTimeout(function(){ov.classList.add("hidden");ov.style.display="none"},5000)}}})}
function respondChallenge(accept){var ov=document.getElementById("challengeOverlay");if(ov){ov.classList.add("hidden");ov.style.display="none"}if(challengeTimer)clearTimeout(challengeTimer);fetch("/api/challenge_respond",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({challenge_id:currentChallengeId,accept:accept})}).then(function(r){return r.json()}).then(function(d){if(!accept){toast("You Declined");return}toast("You Accepted! Host picks mode...");openChallengeDash()})}
function hostPickMode(mode){if(!currentChallengeId){duel={mode:mode,hostScore:0,guestScore:0,q:0,questions:[]};for(var i=0;i<50;i++){var pool=mode==="Bible Fight"?BIBLE_Q:RIDDLES;duel.questions.push(pool[Math.floor(Math.random()*pool.length)])}showPage("page-challenge");document.getElementById("challengeDashText").innerText="Duel: "+mode+" - 50 Questions";startDuel();return}fetch("/api/challenge_pick_mode",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({challenge_id:currentChallengeId,mode:mode,name:user.name})}).then(function(r){return r.json()}).then(function(d){duel={mode:mode,hostScore:0,guestScore:0,q:0,questions:[]};for(var i=0;i<50;i++){var pool2=mode==="Bible Fight"?BIBLE_Q:RIDDLES;duel.questions.push(pool2[Math.floor(Math.random()*pool2.length)])}startDuel()})}
function startDuel(){if(!duel)return;showPage("page-challenge");showDuelQ()}
function showDuelQ(){if(!duel)return;if(duel.q>=50){finishDuelCalculating();return}var q=duel.questions[duel.q];currentQ=q;document.getElementById("challengeDashText").innerText="Duel: "+duel.mode+" - Question "+(duel.q+1)+"/50 - You: "+duel.hostScore+" - Opponent: "+duel.guestScore;var h="<p style=\"font-size:18px;font-weight:700\">"+q[0]+"</p><p>First to answer correctly wins the point!</p>";for(var i=1;i<=4;i++){h+="<button class=\"opt\" onclick=\"answerDuel("+i+")\">"+q[i]+"</button>"}document.getElementById("duelBox").innerHTML=h}
function answerDuel(choice){if(!duel)return;var q=duel.questions[duel.q];var correct=(choice===q[5]+1);var oppWins=Math.random()<0.4;if(correct&&!oppWins){duel.hostScore++;toast("You were faster! +1")}else if(correct&&oppWins){duel.guestScore++;toast("Opponent was faster!")}else if(!correct){duel.guestScore++;toast("Wrong! Opponent gets point")}else{duel.hostScore++}duel.q++;if(currentChallengeId){fetch("/api/challenge_answer",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({challenge_id:currentChallengeId,name:user.name,correct:correct})}).catch(function(){})}setTimeout(function(){showDuelQ()},700)}
function finishDuelCalculating(){showPage("page-challenge");var left=30;document.getElementById("duelBox").innerHTML="<h2>Bot Calculating...</h2><p>Checking 50 answers... Please wait <b id=\"duelCount\">30</b> seconds</p>";if(duelTimer)clearInterval(duelTimer);duelTimer=setInterval(function(){left--;var el=document.getElementById("duelCount");if(el)el.innerText=left;if(left<=0){clearInterval(duelTimer);if(currentChallengeId){fetch("/api/challenge_finish",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({challenge_id:currentChallengeId})}).then(function(r){return r.json()}).then(function(d){showDuelResult(d.challenge||{winner:duel.hostScore>=duel.guestScore?user.name:"Opponent",bonus:50,reward_product:"Infinity Cola"})})}else{showDuelResult({winner:duel.hostScore>=duel.guestScore?user.name:"Opponent",bonus:50,reward_product:"Infinity Cola"})}}},1000)}
function showDuelResult(c){var winner=c.winner||(duel.hostScore>=duel.guestScore?user.name:"Opponent");var bonus=c.bonus||50;var prod=c.reward_product||"Infinity Cola";wins+=bonus;saveLocal();syncScore();document.getElementById("duelBox").innerHTML="<h2>Winner: "+winner+"</h2><p>Final: You "+duel.hostScore+" - Opponent "+duel.guestScore+"</p><p>Reward: "+prod+"</p><p>Tap Drink/Eat in Profile to claim +"+bonus+" Wins (max 100)</p><button class=\"btn\" onclick=\"openMyProfile()\">Go to Profile - Drink / Eat</button><button class=\"btn2\" onclick=\"goDash()\">Dashboard</button>";playWin();duel=null;currentChallengeId=null}
function declineChallengeDash(){if(currentChallengeId){fetch("/api/challenge_respond",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({challenge_id:currentChallengeId,accept:false})}).catch(function(){})}currentChallengeId=null;duel=null;goDash()}
function openMessages(){if(!loggedIn)return;showPage("page-messages");fetch("/api/friends?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){var html="";(d.friends||[]).forEach(function(f){html+="<div class=\"leadRow\" onclick=\"openChatWith('"+f.name+"')\"><span>"+f.name+"<br><small>"+f.player_id+" - "+f.rank+"</small></span><span>Chat</span></div>"});document.getElementById("chatFriendList").innerHTML=html||"No friends yet - add by ID above"})}
function addFriendById(){var digits=document.getElementById("addFriendDigits").value.replace(/[^0-9]/g,"");if(digits.length!==8){toast("Enter 8 digits");return}fetch("/api/add_friend",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,target_id:"INF-"+digits})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}toast("Friend added!");openMessages()})}
function openChatWith(name){chatWithName=name;showPage("page-chat");document.getElementById("chatWith").innerText=name;loadChat()}
function loadChat(){if(!chatWithName)return;fetch("/api/chat_get?a="+encodeURIComponent(user.name)+"&b="+encodeURIComponent(chatWithName)).then(function(r){return r.json()}).then(function(d){var html="";(d.messages||[]).forEach(function(m){var mine=(m.from===user.name);var bg=mine?"background:#ffd700;color:#000;margin-left:auto":"background:rgba(255,255,255,.2);color:#fff";html+="<div style=\"max-width:80%;padding:10px 14px;border-radius:18px;margin:6px 0;font-size:14px;"+bg+"\">"+(m.kind==="voice"?"Voice Note":m.text)+"<br><small>"+(m.time||"")+"</small></div>"});var box=document.getElementById("chatBox");if(box){box.innerHTML=html||"No messages yet";box.scrollTop=box.scrollHeight}})}
function sendMsg(){var txt=document.getElementById("msgInput").value.trim();if(!txt)return;fetch("/api/chat_send",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({sender:user.name,to:chatWithName,text:txt,kind:"text"})}).then(function(){document.getElementById("msgInput").value="";loadChat()})}
function startVoiceCall(){var b=document.getElementById("callBanner");if(b)b.classList.remove("hidden");callSecs=0;if(callInterval)clearInterval(callInterval);callInterval=setInterval(function(){callSecs++;var t=document.getElementById("callTimer");if(t)t.innerText=String(Math.floor(callSecs/60)).padStart(2,"0")+":"+String(callSecs%60).padStart(2,"0")},1000);toast("Calling "+chatWithName+"...")}
function endVoiceCall(){if(callInterval)clearInterval(callInterval);var b=document.getElementById("callBanner");if(b)b.classList.add("hidden");toast("Call ended")}
function toggleVoiceNote(){try{if(mediaRecorder&&mediaRecorder.state==="recording"){mediaRecorder.stop();return}navigator.mediaDevices.getUserMedia({audio:true}).then(function(stream){mediaRecorder=new MediaRecorder(stream);mediaRecorder.start();toast("Recording... tap again to send");mediaRecorder.onstop=function(){fetch("/api/chat_send",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({sender:user.name,to:chatWithName,text:"Voice Note",kind:"voice"})}).then(function(){loadChat();toast("Voice Note sent")})};setTimeout(function(){if(mediaRecorder&&mediaRecorder.state==="recording")mediaRecorder.stop()},3000)}).catch(function(){fetch("/api/chat_send",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({sender:user.name,to:chatWithName,text:"Voice Note",kind:"voice"})}).then(function(){loadChat()})})}catch(e){toast("Voice Note sent")}}
function openPin(desc,cb){pinCallback=cb;document.getElementById("pinDesc").innerText=desc||"Enter your 4-digit PIN";document.getElementById("pinInput").value="";var ov=document.getElementById("pinOverlay");ov.classList.remove("hidden");ov.style.display="flex";setTimeout(function(){var i=document.getElementById("pinInput");if(i)i.focus()},100)}
function closePin(){var ov=document.getElementById("pinOverlay");ov.classList.add("hidden");ov.style.display="none";pinCallback=null}
function confirmPin(){var v=document.getElementById("pinInput").value.trim();if(!v||v.length!==4){toast("PIN must be 4 digits");return}var cb=pinCallback;closePin();if(cb)cb(v)}
function openIdPopup(title,cb){idCallback=cb;document.getElementById("idTitle").innerText=title||"Enter Player ID";document.getElementById("idInput").value="";var ov=document.getElementById("idOverlay");ov.classList.remove("hidden");ov.style.display="flex"}
function closeIdPopup(){var ov=document.getElementById("idOverlay");ov.classList.add("hidden");ov.style.display="none";idCallback=null}
function confirmIdPopup(){var v=document.getElementById("idInput").value.replace(/[^0-9]/g,"");if(v.length!==8){toast("Enter exactly 8 digits");return}var cb=idCallback;closeIdPopup();if(cb)cb("INF-"+v)}
function toggleMenu(){var m=document.getElementById("menuDrop");if(!m)return;if(!m.classList.contains("hidden")){m.classList.add("hidden");return}var items="";items+="<div style=\"padding:10px;cursor:pointer;border-bottom:1px solid #333\" onclick=\"openMyProfile();toggleMenu()\">My Profile</div>";items+="<div style=\"padding:10px;cursor:pointer;border-bottom:1px solid #333\" onclick=\"openBank();toggleMenu()\">Bank</div>";items+="<div style=\"padding:10px;cursor:pointer;border-bottom:1px solid #333\" onclick=\"openMenuPage();toggleMenu()\">Menu - 11 Games</div>";items+="<div style=\"padding:10px;cursor:pointer;border-bottom:1px solid #333\" onclick=\"openShop();toggleMenu()\">Shop</div>";items+="<div style=\"padding:10px;cursor:pointer;border-bottom:1px solid #333\" onclick=\"openEconomy();toggleMenu()\">Server Economy (Dominic)</div>";items+="<div style=\"padding:10px;cursor:pointer;border-bottom:1px solid #333\" onclick=\"openLottery();toggleMenu()\">Lottery</div>";items+="<div style=\"padding:10px;cursor:pointer;border-bottom:1px solid #333\" onclick=\"openUpdatePage();toggleMenu()\">Update Server (Dominic)</div>";items+="<div style=\"padding:10px;cursor:pointer;border-bottom:1px solid #333\" onclick=\"openServerInfo();toggleMenu()\">Server Info (Dominic)</div>";items+="<div style=\"padding:10px;cursor:pointer;border-bottom:1px solid #333\" onclick=\"openReviewRequest('review');toggleMenu()\">Review</div>";items+="<div style=\"padding:10px;cursor:pointer\" onclick=\"openReviewRequest('request');toggleMenu()\">Request</div>";m.innerHTML=items;m.classList.remove("hidden")}
document.addEventListener("click",function(e){var m=document.getElementById("menuDrop");var b=document.getElementById("menuBtn");if(m&&!m.classList.contains("hidden")&&b&&!b.contains(e.target)&&!m.contains(e.target))m.classList.add("hidden")});
document.addEventListener("DOMContentLoaded",function(){try{updateCatTime()}catch(e){}var pb=document.getElementById("profileBtn");if(pb)pb.onclick=function(){openMyProfile()};var mb=document.getElementById("menuBtn");if(mb)mb.onclick=function(e){e.stopPropagation();toggleMenu()};var sb=document.getElementById("soundBtn");if(sb)sb.onclick=function(){soundOn=!soundOn;if(!soundOn)stopDashLoop();else if(currentPage==="page-dash")startDashLoop()};var bf=document.getElementById("backFab");if(bf)bf.onclick=function(){goBack()};var mf=document.getElementById("msgFab");if(mf)mf.onclick=function(){openMessages()};var eb=document.getElementById("enterBtn");if(eb)eb.onclick=function(){enterClicked()};document.addEventListener("keydown",function(e){if(e.key==="Enter"&&currentPage==="page-home")enterClicked()});if(user&&user.name){loggedIn=true;showPage("page-dash");document.getElementById("welcomeText").innerText=specialWelcome(user.name,user.password);loadLeader();loadMyProfileData()}else{showPage("page-home")}setInterval(function(){if(loggedIn)checkForChallenges()},15000)});
</script></body></html>"""
if __name__=="__main__":
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
