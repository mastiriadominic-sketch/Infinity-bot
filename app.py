from flask import Flask,request,jsonify
import os,json,random,datetime,time
app=Flask(__name__)
BASE=os.path.dirname(__file__);LF=os.path.join(BASE,"leaderboard.json");MF=os.path.join(BASE,"messages.json")
USERS={};MESSAGES={};CH={};REQ=[];LOANS=[];ANN=[]
ECO={"gold":100000000,"gems":1000000,"bank":0,"fees":0,"lottery":0,"hist":[100000000,100010000,99950000],"backup":10000000000,"tick":time.time()}
RANKS=[("Beginner",0),("Intermediate",200),("Advanced",400),("Expert",800),("Professional",1600),("National",3200),("S Rank",6400),("SS Rank",12800),("SSS Rank",25600),("SSS Classified",51200),("Godly",102400)]
def norm(n): return str(n or "").strip().lower()
def gid(): return "INF-"+"".join(str(random.randint(0,9)) for _ in range(8))
def gbid(): return "Bank INF-"+"".join(str(random.randint(0,9)) for _ in range(10))
def cid(s): return "".join(c for c in str(s or "").upper() if c.isdigit())
def rank(w):
 r="Beginner"
 for n,need in RANKS:
  if w>=need: r=n
 return r
def ensure(v,k):
 for a,b in [("display_name",k),("friends",[]),("wins",0),("losses",0),("stage",0),("gold",0),("gems",0),("bank_gold",0),("bank_gems",0),("notifs",[]),("seen",[]),("items",[]),("cars",[]),("loans",[]),("glevel",1),("gkills",0)]: v.setdefault(a,b)
 if not v.get("player_id"): v["player_id"]=gid()
 if not v.get("bank_id"): v["bank_id"]=gbid()
 return v
try:
 if os.path.exists(LF):
  d=json.load(open(LF)); USERS={norm(v.get("display_name",k) or k):ensure(v,k) for k,v in d.items()}
except: pass
try:
 if os.path.exists(MF): MESSAGES=json.load(open(MF))
except: pass
def save():
 try: open(LF,"w").write(json.dumps(USERS))
 except: pass
def tick():
 if time.time()-ECO["tick"]>5:
  ECO["tick"]=time.time(); ECO["gold"]=max(0,ECO["gold"]+random.randint(-80000,120000)); ECO["hist"].append(ECO["gold"]); ECO["hist"]=ECO["hist"][-80:]
def notify(n,t,typ="info",ex=None):
 if norm(n) in USERS:
  x={"text":t,"time":str(datetime.datetime.now()),"type":typ}
  if ex: x.update(ex)
  USERS[norm(n)]["notifs"].append(x); save()
def getp(n): return USERS.get(norm(n))
@app.route("/")
def home(): tick(); return HOME
@app.route("/api/player")
def gp():
 n=norm(request.args.get("name","")); pw=request.args.get("password","")
 if n in USERS:
  v=USERS[n]
  if pw and v.get("password") and str(v.get("password"))!=str(pw): return jsonify({"found":True,"password_ok":False,"player_id":v["player_id"]})
  return jsonify({"found":True,"password_ok":True,"name":v["display_name"],"wins":v["wins"],"losses":v["losses"],"gold":v["gold"],"gems":v["gems"],"bank_gold":v.get("bank_gold",0),"bank_gems":v.get("bank_gems",0),"player_id":v["player_id"],"bank_id":v.get("bank_id",""),"rank":rank(v["wins"]),"classified":v["wins"]>=3200,"friends":v["friends"],"notifs":v.get("notifs",[]),"seen":v.get("seen",[]),"items":v.get("items",[]),"cars":v.get("cars",[]),"loans":v.get("loans",[]),"glevel":v.get("glevel",1),"gkills":v.get("gkills",0)})
 return jsonify({"found":False})
@app.route("/api/leaderboard")
def lb():
 m=request.args.get("mode","pvp"); ps=[]
 for v in USERS.values(): ps.append({"name":v["display_name"],"wins":v["wins"],"losses":v["losses"],"gold":v.get("gold",0),"gems":v.get("gems",0),"player_id":v.get("player_id",""),"rank":rank(v["wins"])})
 if m=="gold": ps=sorted(ps,key=lambda x:x["gold"],reverse=True)
 elif m=="gems": ps=sorted(ps,key=lambda x:x["gems"],reverse=True)
 elif m=="rank": ps=sorted(ps,key=lambda x:x["wins"],reverse=True)
 else: ps=sorted(ps,key=lambda x:x["wins"]-x["losses"],reverse=True)
 return jsonify({"players":ps})
@app.route("/api/score",methods=["POST"])
def sc():
 d=request.get_json() or {}; n=norm(d.get("name"))
 if not n: return jsonify({"error":"no name"}),400
 if n not in USERS: USERS[n]=ensure({"display_name":d.get("name"),"password":d.get("password","")},d.get("name"))
 v=USERS[n]
 if d.get("password"): v["password"]=d.get("password")
 v["wins"]=max(v["wins"],d.get("wins",v["wins"])); v["losses"]=d.get("losses",v["losses"])
 for k in ("gold","gems"):
  if k in d: v[k]=max(v[k],d[k])
 for k in ("seen","items","cars"):
  if k in d:
   for x in d[k]:
    if x not in v.get(k,[]): v[k].append(x)
 if "glevel" in d: v["glevel"]=max(v.get("glevel",1),d["glevel"])
 if "gkills" in d: v["gkills"]=max(v.get("gkills",0),d["gkills"])
 save(); return jsonify({"ok":True})
def chk(v,pin):
 if str(v.get("password"))!=str(pin): notify(v["display_name"],"Warning! Pin is wrong.","warn"); return False
 return True
@app.route("/api/transfer",methods=["POST"])
def tr():
 d=request.get_json() or {}; s=getp(d.get("sender")); amt=int(d.get("amount",0))
 if not s or not chk(s,d.get("pin","")): return jsonify({"error":"Wrong PIN / Not found"}),403
 rid="INF-"+cid(d.get("receiver_id","")); r=None
 for v in USERS.values():
  if v.get("player_id")==rid: r=v
 if not r: return jsonify({"error":"Receiver not found"}),404
 if s.get("gold",0)<amt: return jsonify({"error":"Not enough Gold"}),400
 fee=int(amt*0.05); s["gold"]-=amt; r["gold"]=r.get("gold",0)+(amt-fee); ECO["gold"]+=fee; ECO["fees"]+=fee; tick()
 notify(s["display_name"],"You sent "+str(amt)+" Gold.","send"); notify(r["display_name"],"You received "+str(amt)+" Gold.","receive"); save(); return jsonify({"ok":True,"sender_gold":s["gold"]})
@app.route("/api/bank_action",methods=["POST"])
def ba():
 d=request.get_json() or {}; v=getp(d.get("name")); amt=int(d.get("amount",0)); act=d.get("action","deposit"); cur=d.get("currency","Gold")
 if not v or not chk(v,d.get("pin","")): return jsonify({"error":"Wrong PIN"}),403
 if act=="deposit":
  if cur=="Gems":
   if v.get("gems",0)<amt: return jsonify({"error":"Not enough Gems"}),400
   v["gems"]-=amt; v["bank_gems"]=v.get("bank_gems",0)+amt
  else:
   if v.get("gold",0)<amt: return jsonify({"error":"Not enough Gold"}),400
   v["gold"]-=amt; v["bank_gold"]=v.get("bank_gold",0)+amt; ECO["gold"]+=amt; ECO["bank"]+=amt
 else:
  if cur=="Gems":
   if v.get("bank_gems",0)<amt: return jsonify({"error":"Not enough in Bank"}),400
   v["bank_gems"]-=amt; v["gems"]=v.get("gems",0)+amt
  else:
   if v.get("bank_gold",0)<amt: return jsonify({"error":"Not enough in Bank"}),400
   v["bank_gold"]-=amt; v["gold"]=v.get("gold",0)+amt
 save(); return jsonify({"ok":True,"gold":v["gold"],"gems":v["gems"],"bank_gold":v.get("bank_gold",0),"bank_gems":v.get("bank_gems",0)})
@app.route("/api/exchange",methods=["POST"])
def ex():
 d=request.get_json() or {}; v=getp(d.get("name")); amt=int(d.get("amount",0)); dr=d.get("direction","gold_to_gem")
 if not v or not chk(v,d.get("pin","")): return jsonify({"error":"Wrong PIN"}),403
 if dr=="gold_to_gem":
  g=amt//100
  if g<1 or v.get("gold",0)<g*100: return jsonify({"error":"Need 100 Gold = 1 Germ"}),400
  v["gold"]-=g*100; v["gems"]=v.get("gems",0)+g
 else:
  if v.get("gems",0)<amt: return jsonify({"error":"Not enough Gems"}),400
  v["gems"]-=amt; v["gold"]=v.get("gold",0)+amt*100
 save(); return jsonify({"ok":True,"gold":v["gold"],"gems":v["gems"]})
@app.route("/api/loan_apply",methods=["POST"])
def la():
 d=request.get_json() or {}; v=getp(d.get("name")); amt=int(d.get("amount",0))
 if not v or not chk(v,d.get("pin","")): return jsonify({"error":"Wrong PIN"}),403
 lid="LN-"+str(random.randint(10000000,99999999)); loan={"id":lid,"from":v["display_name"],"from_id":v.get("player_id"),"amount":amt,"currency":d.get("currency","Gold"),"repay_date":d.get("repay_date",""),"status":"pending_dominic","new_date":""}
 LOANS.append(loan); notify("dominic","LOAN: "+v["display_name"]+" wants "+str(amt)+" "+loan["currency"]+" repay "+loan["repay_date"]+" - Approve?","loan_request",{"loan_id":lid,"amount":amt,"currency":loan["currency"],"repay_date":loan["repay_date"],"from":v["display_name"]}); return jsonify({"ok":True})
@app.route("/api/loan_dominic",methods=["POST"])
def ld():
 d=request.get_json() or {}
 if norm(d.get("admin"))!="dominic" or str(d.get("pin"))!="2164": return jsonify({"error":"Only Dominic"}),403
 for l in LOANS:
  if l["id"]==d.get("loan_id"):
   if not d.get("approve"): l["status"]="declined"; notify(l["from"],"Loan DECLINED by Dominic.","loan_declined"); return jsonify({"ok":True})
   l["new_date"]=d.get("new_date") or l["repay_date"]; l["status"]="waiting_player"
   notify(l["from"],"Loan APPROVED but date changed to "+l["new_date"]+" - Approve? NO = refunded.","loan_date_change",{"loan_id":l["id"],"amount":l["amount"],"currency":l["currency"],"new_date":l["new_date"]}); return jsonify({"ok":True})
 return jsonify({"error":"Not found"}),404
@app.route("/api/loan_confirm",methods=["POST"])
def lc():
 d=request.get_json() or {}; v=getp(d.get("name"))
 if not v: return jsonify({"error":"Not found"}),404
 for l in LOANS:
  if l["id"]==d.get("loan_id"):
   if not d.get("approve"): l["status"]="refunded"; notify(v["display_name"],"Loan refunded.","loan_refunded"); return jsonify({"ok":True})
   l["status"]="approved"; l["repay_date"]=l.get("new_date") or l["repay_date"]; amt=l["amount"]
   if l["currency"]=="Gold": v["gold"]=v.get("gold",0)+amt; ECO["gold"]-=amt
   else: v["gems"]=v.get("gems",0)+amt; ECO["gems"]-=amt
   v.setdefault("loans",[]).append(l); save(); notify(v["display_name"],"✅ LOAN CREDITED "+str(amt)+" "+l["currency"]+" Repay by "+l["repay_date"],"loan_approved"); return jsonify({"ok":True})
 return jsonify({"error":"Not found"}),404
@app.route("/api/buy_item",methods=["POST"])
def bi():
 d=request.get_json() or {}; v=getp(d.get("name")); price=int(d.get("price",0)); item=d.get("item","")
 if not v or not chk(v,d.get("pin","")): return jsonify({"error":"Wrong PIN"}),403
 if v.get("gold",0)<price: return jsonify({"error":"Not enough Gold"}),400
 if item in v.get("items",[]) or item in v.get("cars",[]): return jsonify({"error":"Already own!"}),400
 v["gold"]-=price
 if any(x in item for x in ["Toyota","BMW","Lamborghini","Ferrari","Tesla","Mercedes","Audi","Rover","Hilux","Nissan","Bugatti"]): v.setdefault("cars",[]).append(item)
 else: v.setdefault("items",[]).append(item)
 ECO["gold"]+=price; ECO["fees"]+=price; notify(v["display_name"],"Bought "+item,"shop"); save(); return jsonify({"ok":True,"gold":v["gold"]})
@app.route("/api/request_money",methods=["POST"])
def rm():
 d=request.get_json() or {}; v=getp(d.get("name")); amt=d.get("amount"); cur=d.get("currency","Gold")
 if not v: return jsonify({"error":"Not found"}),404
 rid="RQ-"+str(random.randint(10000000,99999999)); REQ.append({"id":rid,"from":v["display_name"],"from_id":v.get("player_id"),"amount":amt,"currency":cur,"message":str(d.get("message",""))[:200]}); notify("dominic","SECRET: "+v["display_name"]+" wants "+str(amt)+" "+cur,"request",{"request_id":rid,"from":v["display_name"],"amount":amt,"currency":cur}); return jsonify({"ok":True})
@app.route("/api/request_approve",methods=["POST"])
def ra():
 d=request.get_json() or {}
 if norm(d.get("admin"))!="dominic" or str(d.get("pin"))!="2164": return jsonify({"error":"Only Dominic"}),403
 amt=int(d.get("amount",0)); cur=d.get("currency","Gold")
 for r in list(REQ):
  if r["id"]==d.get("request_id"):
   REQ.remove(r)
   if cur=="Gold": ECO["gold"]-=amt
   else: ECO["gems"]-=amt
   for v in USERS.values():
    if v.get("player_id")==r["from_id"]:
     if cur=="Gold": v["gold"]=v.get("gold",0)+amt
     else: v["gems"]=v.get("gems",0)+amt
     notify(v["display_name"],"✅ SECRET APPROVED: +"+str(amt)+" "+cur,"request_ok")
   save(); return jsonify({"ok":True})
 return jsonify({"error":"Not found"}),404
@app.route("/api/lottery",methods=["POST"])
def lo():
 d=request.get_json() or {}; v=getp(d.get("name")); bet=int(d.get("bet",0)); cur=d.get("currency","Gold")
 if not v or not chk(v,d.get("pin","")): return jsonify({"error":"Wrong PIN"}),403
 if cur=="Gold":
  if v.get("gold",0)<bet: return jsonify({"error":"Not enough"}),400
  v["gold"]-=bet
 else:
  if v.get("gems",0)<bet: return jsonify({"error":"Not enough"}),400
  v["gems"]-=bet
 win=random.random()<0.5
 if win:
  if cur=="Gold": v["gold"]+=bet*2; ECO["gold"]-=bet
  else: v["gems"]+=bet*2; ECO["gems"]-=bet
  notify(v["display_name"],"LOTTERY WIN "+str(bet*2)+" "+cur,"lottery"); res={"win":True,"prize":bet*2}
 else:
  if cur=="Gold": ECO["gold"]+=bet
  else: ECO["gems"]+=bet
  notify(v["display_name"],"LOTTERY LOSE "+str(bet)+" "+cur,"lottery"); res={"win":False,"lost":bet}
 save(); return jsonify({"ok":True,"result":res,"gold":v["gold"],"gems":v["gems"]})
@app.route("/api/economy")
def ec():
 if norm(request.args.get("name"))!="dominic" or str(request.args.get("password"))!="2164": return jsonify({"error":"Admin only"}),403
 tick(); return jsonify({"economy":ECO,"requests":REQ,"loans":LOANS})
@app.route("/api/announce",methods=["POST"])
def an():
 d=request.get_json() or {}
 if norm(d.get("admin"))!="dominic" or str(d.get("pin"))!="2164": return jsonify({"error":"Only Dominic"}),403
 t=d.get("text","")[:500]; ANN.append({"text":t,"time":str(datetime.datetime.now())})
 for k in list(USERS.keys()): notify(USERS[k]["display_name"],"📢 ANNOUNCEMENT: "+t,"announcement")
 return jsonify({"ok":True})
@app.route("/api/announcements")
def ga(): return jsonify({"announcements":ANN[-5:]})
@app.route("/api/challenge_send",methods=["POST"])
def cs():
 d=request.get_json() or {}; s=getp(d.get("sender")); tid="INF-"+cid(d.get("target_id",""))
 if not s: return jsonify({"error":"Not found"}),404
 tgt=None
 for v in USERS.values():
  if v.get("player_id")==tid: tgt=v
 if not tgt: return jsonify({"error":"Not found"}),404
 cid2="CH-"+str(random.randint(10000000,99999999)); CH[cid2]={"host":s["display_name"],"guest":tgt["display_name"],"host_score":0,"guest_score":0,"q":0,"status":"pending"}
 notify(tgt["display_name"],"CHALLENGE from "+s["display_name"],"challenge",{"challenge_id":cid2}); return jsonify({"ok":True,"challenge_id":cid2})
@app.route("/api/challenge_respond",methods=["POST"])
def cr():
 d=request.get_json() or {}; c=CH.get(d.get("challenge_id"))
 if not c: return jsonify({"error":"Not found"}),404
 c["status"]="accepted" if d.get("accept") else "declined"; return jsonify({"ok":True})
@app.route("/api/review",methods=["POST"])
def rv():
 d=request.get_json() or {}
 try: open(os.path.join(BASE,"reviews.json"),"a").write(json.dumps(d)+"\n")
 except: pass
 return jsonify({"ok":True})
@app.route("/api/chat_send",methods=["POST"])
def chs():
 d=request.get_json() or {}; s=norm(d.get("sender")); t=norm(d.get("to"))
 if s not in USERS or t not in USERS: return jsonify({"error":"Not found"}),404
 k="|".join(sorted([s,t])); MESSAGES.setdefault(k,[]).append({"from":USERS[s]["display_name"],"text":d.get("text","")[:500],"kind":d.get("kind","text"),"time":str(datetime.datetime.now())}); notify(t,"Msg from "+USERS[s]["display_name"],"chat")
 try: open(MF,"w").write(json.dumps(MESSAGES))
 except: pass
 return jsonify({"ok":True})
@app.route("/api/chat_get")
def chg():
 a=norm(request.args.get("a","")); b=norm(request.args.get("b","")); return jsonify({"messages":MESSAGES.get("|".join(sorted([a,b])),[])})
@app.route("/api/friends")
def fr():
 n=norm(request.args.get("name",""))
 if n not in USERS: return jsonify({"friends":[]})
 out=[]
 for f in USERS[n].get("friends",[]):
  if norm(f) in USERS: out.append({"name":USERS[norm(f)]["display_name"],"player_id":USERS[norm(f)].get("player_id",""),"rank":rank(USERS[norm(f)]["wins"])})
 if not out:
  for k,v in USERS.items():
   if k!=n: out.append({"name":v["display_name"],"player_id":v.get("player_id",""),"rank":rank(v["wins"])})
 return jsonify({"friends":out})
@app.route("/api/add_friend",methods=["POST"])
def af():
 d=request.get_json() or {}; n=norm(d.get("name")); tid="INF-"+cid(d.get("target_id",""))
 if n not in USERS: return jsonify({"error":"Not found"}),404
 for v in USERS.values():
  if v.get("player_id")==tid:
   if v["display_name"] not in USERS[n]["friends"]: USERS[n]["friends"].append(v["display_name"])
   if USERS[n]["display_name"] not in v["friends"]: v["friends"].append(USERS[n]["display_name"])
   save(); return jsonify({"ok":True})
 return jsonify({"error":"Not found"}),404
@app.route("/api/consume",methods=["POST"])
def co():
 d=request.get_json() or {}; v=getp(d.get("name")); b=min(int(d.get("bonus",0)),100)
 if not v or not chk(v,d.get("pin","")): return jsonify({"error":"Wrong PIN"}),403
 if d.get("product") in v.get("items",[]): v["items"].remove(d.get("product"))
 v["wins"]+=b; save(); return jsonify({"ok":True,"wins":v["wins"]})
@app.route("/api/earning_status")
def es(): tick(); return jsonify({"economy":ECO})
@app.route("/webhook",methods=["GET","POST"])
def wh():
 if request.method=="GET":
  if request.args.get("hub.verify_token")=="infinity": return request.args.get("hub.challenge"),200
  return "Forbidden",403
 return jsonify({"ok":True})
HOME=r"""<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>INFINITY BOT v24</title><link href="https://fonts.googleapis.com/css2?family=Great+Vibes&family=Poppins:wght@400;700;900&display=swap" rel="stylesheet"><style>*{box-sizing:border-box}body{margin:0;font-family:Poppins,Arial;color:#fff;background:radial-gradient(circle at 50% 20%,#3a0a5e,#12002b 70%);min-height:100vh}.cursive{font-family:'Great Vibes',cursive}.center{min-height:82vh;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:20px}.enterBtn{margin-top:20px;padding:16px 70px;font-family:'Great Vibes',cursive;font-size:48px;border:none;border-radius:60px;background:linear-gradient(90deg,#ff006e,#ffd700,#00e5ff);color:#000;box-shadow:0 0 40px #ff006e;cursor:pointer}.card{background:rgba(255,255,255,.08);border:2px solid rgba(255,255,255,.35);border-radius:26px;padding:20px;margin:14px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.box{background:linear-gradient(160deg,rgba(255,255,255,.18),rgba(0,0,0,.4));border:2px solid #fff;border-radius:24px;padding:22px 10px;text-align:center;cursor:pointer}.box span{font-size:38px;display:block}.btn{width:100%;padding:14px;border:none;border-radius:25px;font-weight:900;background:#ffd700;margin:6px 0;cursor:pointer}.btn2{width:100%;padding:13px;border-radius:25px;border:2px solid #00e5ff;background:transparent;color:#00e5ff;font-weight:900;margin:6px 0;cursor:pointer}.opt{width:100%;padding:13px;margin:7px 0;border-radius:16px;border:2px solid #fff;background:rgba(0,0,0,.5);color:#fff;font-weight:700;cursor:pointer;text-align:left}input,select,textarea{width:100%;padding:14px;border-radius:14px;border:2px solid #ffd700;margin:8px 0;font-size:16px;background:#fff;color:#000}.hidden{display:none!important}.leadRow{display:flex;justify-content:space-between;padding:10px;background:rgba(0,0,0,.45);border-radius:14px;margin:6px 0;cursor:pointer}.toast{position:fixed;top:70px;left:50%;transform:translateX(-50%);background:#fff;color:#000;padding:12px 18px;border-radius:20px;font-weight:700;z-index:999;max-width:90%;text-align:center}.gameOverlay{position:fixed;inset:0;background:rgba(0,0,0,.75);display:flex;align-items:center;justify-content:center;padding:16px;z-index:500}.gamePopup{background:linear-gradient(160deg,#2b005e,#12002b);border:3px solid #ffd700;border-radius:28px;padding:22px 18px;max-width:420px;width:100%;text-align:center}.choiceRow{display:flex;gap:12px}.choiceBox{flex:1;padding:18px 8px;border-radius:20px;cursor:pointer;font-weight:900;border:3px solid #fff}.choiceNo{background:#ff2222;color:#fff}.choiceYes{background:#00cc44;color:#000}.bottomNav{position:fixed;bottom:0;left:0;right:0;background:rgba(0,0,0,.85);border-top:2px solid #ffd700;display:flex;justify-content:space-around;padding:10px 0 14px;z-index:100}.walletCard{background:linear-gradient(135deg,#ffd700,#ff006e);color:#000;border-radius:24px;padding:18px;text-align:center}.bigBankBox{padding:22px 10px;border-radius:24px;border:2px solid #fff;text-align:center;cursor:pointer;background:linear-gradient(160deg,rgba(255,255,255,.18),rgba(0,0,0,.4))}.idPrefix{display:flex;align-items:center;background:#fff;border-radius:14px;border:2px solid #ffd700;padding:0 10px}.idPrefix b{color:#000}.idPrefix input{border:none;flex:1;margin:0}.timerBar{height:14px;background:#333;border-radius:99px;overflow:hidden;margin:10px 0}.timerFill{height:100%;background:linear-gradient(90deg,#00ff88,#ffd700,#ff2222)}.fallArea{position:relative;height:400px;background:linear-gradient(#000428,#004e92);border:2px solid #00e5ff;border-radius:18px;overflow:hidden}.fallItem{position:absolute;font-size:34px;cursor:pointer}.dinoArea{height:200px;background:#fff;border-radius:18px;position:relative;overflow:hidden;border:3px solid #000}.dino{position:absolute;bottom:20px;left:40px;font-size:52px;transition:bottom .3s}.cactus{position:absolute;bottom:20px;font-size:36px}</style></head><body>
<div id="announceBar" class="hidden" style="position:fixed;top:0;left:0;right:0;background:#ffd700;color:#000;padding:10px;text-align:center;font-weight:900;z-index:1000"></div>
<div style="display:flex;justify-content:space-between;padding:8px 14px"><div><span id="catTime" style="font-size:12px;background:rgba(0,0,0,.55);border:1px solid #ffd700;padding:5px 9px;border-radius:20px">00:00:00 CAT</span><br><span id="catDate" style="font-size:10px">Central Africa</span><br><b>INFINITY BOT</b></div><div id="topRight" class="hidden" style="display:flex;gap:8px;align-items:center"><div onclick="openShop()" style="width:32px;height:32px;border-radius:50%;background:rgba(0,0,0,.55);border:1px solid #ffd700;display:flex;align-items:center;justify-content:center;cursor:pointer">🛍️</div><div onclick="openMyProfile()" style="width:46px;height:46px;border-radius:50%;background:linear-gradient(135deg,#ff006e,#ffd700);display:flex;align-items:center;justify-content:center;cursor:pointer">👤</div><div id="menuBtn" style="width:32px;height:32px;border-radius:50%;background:rgba(0,0,0,.55);border:1px solid #ffd700;display:flex;align-items:center;justify-content:center;cursor:pointer">⋮</div></div></div>
<script>function p2(n){return(n<10?"0":"")+n}function ct(){try{var n=new Date();var c=new Date(n.getTime()+n.getTimezoneOffset()*60000+7200000);var d=["Sun","Mon","Tue","Wed","Thu","Fri","Sat"],m=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];document.getElementById("catTime").textContent=p2(c.getHours())+":"+p2(c.getMinutes())+":"+p2(c.getSeconds())+" CAT";document.getElementById("catDate").textContent=d[c.getDay()]+", "+p2(c.getDate())+" "+m[c.getMonth()]+" "+c.getFullYear()+" - Central Africa"}catch(e){}}ct();setInterval(ct,1000)</script>
<div id="menuDrop" class="hidden" style="position:absolute;top:130px;right:10px;background:#1a1a2e;border:2px solid #ffd700;border-radius:16px;padding:8px;z-index:500;min-width:220px"></div><div id="toast" class="toast hidden"></div>
<div id="pinOverlay" class="gameOverlay hidden" style="display:none;z-index:900"><div class="gamePopup"><div style="font-size:50px">🔐</div><h2>Enter PIN</h2><p id="pinDesc">Enter PIN</p><input id="pinInput" placeholder="...." maxlength="4" inputmode="numeric" type="password" style="font-size:28px;text-align:center;letter-spacing:12px"><div class="choiceRow"><div class="choiceBox choiceNo" onclick="closePin()">❌ Cancel</div><div class="choiceBox choiceYes" onclick="confirmPin()">✅ Confirm</div></div></div></div>
<div id="annOverlay" class="gameOverlay hidden" style="display:none;z-index:960"><div class="gamePopup"><h2>📢 Enter Announcement</h2><textarea id="annText" style="height:100px"></textarea><button class="btn" onclick="sendAnn()">📢 Announce</button><button class="btn2" onclick="closeAnn()">Cancel</button></div></div>
<div id="secretOverlay" class="gameOverlay hidden" style="display:none;z-index:920"><div class="gamePopup"><h2>🔒 Secret Request</h2><input id="reqMsg" type="password" placeholder="Secret message"><input id="reqAmt" type="password" placeholder="Amount"><select id="reqCur"><option>Gold</option><option>Gems</option></select><div class="choiceRow"><div class="choiceBox choiceNo" onclick="closeSecret()">❌</div><div class="choiceBox choiceYes" onclick="sendMoneyRequest()">📩 Send</div></div></div></div>
<div id="loanOverlay" class="gameOverlay hidden" style="display:none;z-index:920"><div class="gamePopup"><h2>🏦 Loan</h2><input id="loanAmt" type="number" placeholder="Amount"><select id="loanCur"><option>Gold</option><option>Gems</option></select><input id="loanDate" type="date"><div class="choiceRow"><div class="choiceBox choiceNo" onclick="closeLoan()">❌</div><div class="choiceBox choiceYes" onclick="submitLoan()">📩 Apply</div></div></div></div>
<div id="idOverlay" class="gameOverlay hidden" style="display:none;z-index:900"><div class="gamePopup"><h2 id="idTitle">Enter ID</h2><div class="idPrefix"><b>INF-</b><input id="idInput" placeholder="12345678" inputmode="numeric" maxlength="8"></div><div class="choiceRow"><div class="choiceBox choiceNo" onclick="closeIdPopup()">❌</div><div class="choiceBox choiceYes" onclick="confirmIdPopup()">✅</div></div></div></div>
<div id="page-welcome" class="gameOverlay hidden" style="display:none;z-index:950"><div class="gamePopup"><div style="font-size:56px">👑</div><h2>Do you already have an account?</h2><div class="choiceRow"><div class="choiceBox choiceNo" onclick="welcomeChoice('no')">❌ No</div><div class="choiceBox choiceYes" onclick="welcomeChoice('yes')">✅ Yes</div></div></div></div>
<div id="page-home" class="center"><div style="font-size:26px">✨ 💖 ⭐ 🌟 💫</div><div style="font-size:90px">👑</div><h1 class="cursive" style="font-size:68px;margin:5px">Infinity Bot</h1><p style="letter-spacing:3px;font-weight:900">DOMINIC MASTIRIA</p><p>Riddles • Bible Fight • Sci-Fi • WhatsApp</p><button class="enterBtn" onclick="enterClicked()">Enter</button></div>
<div id="page-register" class="hidden" style="max-width:520px;margin:0 auto;padding:20px 14px"><div class="card" style="text-align:center"><h1 class="cursive" style="font-size:48px">Register</h1><div id="registerForm"><input id="regName" placeholder="Your Name"><input id="regPass" placeholder="...." maxlength="4" type="password"><p style="font-size:12px;color:#ffd700">⚠️ Do NOT use 1234 or 0000</p><button class="btn" onclick="doRegister()">📝 REGISTER</button><p>Have account? <b style="color:#ffd700;cursor:pointer" onclick="showLogin()">Login</b></p></div><div id="loginForm" class="hidden"><input id="loginName" placeholder="Your Name"><input id="loginPass" placeholder="...." maxlength="4" type="password"><button class="btn" onclick="doLogin()">🔓 LOGIN</button><p>New? <b style="color:#ffd700;cursor:pointer" onclick="showRegister()">Register</b></p></div></div></div>
<div id="page-dash" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div style="text-align:center"><h2 class="cursive" style="font-size:44px" id="welcomeText">Welcome 👑</h2><span style="padding:5px 10px;border:1px solid #ffd700;border-radius:20px;font-size:12px">⭐ <b id="myRank">#-</b></span> <span style="padding:5px 10px;border:1px solid #ffd700;border-radius:20px;font-size:12px">🚗 Cars: <b id="myCarsCount">0</b> +<span id="myExtra">0</span>s</span></div><div class="grid"><div class="box" onclick="pickRiddleCat()"><span>🧩</span><b>RIDDLES</b><br><small>10 Qs • Timer • 3 Options</small></div><div class="box" onclick="pickBible()"><span>📖</span><b>BIBLE FIGHT</b><br><small>Old / New</small></div><div class="box" onclick="openSciFi()"><span>🚀</span><b>SCI-FI</b><br><small>25 Dec 2026</small></div><div class="box" onclick="openMessages()"><span>💚</span><b>WHATSAPP</b></div></div><div class="card"><h3 style="text-align:center">🏆 TOP 5 🏆</h3><div id="leaderList">Loading...</div><button class="btn2" onclick="openFullLeader()">👀 Full Leaderboard</button></div></div>
<div id="page-leader" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h3 style="text-align:center">🏆 LEADERBOARD</h3><div style="display:flex;gap:8px"><div class="btn2" onclick="setLeaderMode('gold')">🪙 Gold</div><div class="btn2" onclick="setLeaderMode('gems')">💎 Germ</div><div class="btn2" onclick="setLeaderMode('pvp')">⚔️ PvP</div></div><div id="fullLeaderList"></div></div></div>
<div id="page-game" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 id="gameTitle" style="text-align:center">Game</h2><div id="gameBody"></div></div></div>
<div id="page-bank" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">💰 BANK</h2><div class="walletCard"><div id="bankIDShow">Bank INF-</div><div>🪙 Bank: <b id="bankGold">0</b> | 💎 <b id="bankGems">0</b></div><div>Wallet 🪙 <span id="walletGold">0</span> | 💎 <span id="walletGems">0</span></div></div><div style="display:flex;gap:12px;margin-top:14px"><div style="flex:1"><div class="bigBankBox" onclick="openSendPage()">💸<br><b>Send</b></div><div class="bigBankBox" style="margin-top:10px" onclick="openWithdrawPage()">🏧<br><b>Withdraw</b></div><div class="bigBankBox" style="margin-top:10px" onclick="openDepositPage()">💰<br><b>Deposit</b></div><div class="bigBankBox" style="margin-top:10px" onclick="openExchangePage()">🔄<br><b>Exchange LEFT</b></div></div><div style="flex:1"><div class="bigBankBox" style="background:linear-gradient(160deg,#ff006e,#ffd700);color:#000" onclick="openLoan()">🏦<br><b>LOAN RIGHT</b></div><div class="bigBankBox" style="margin-top:10px" onclick="openMyProfile()">👤<br><b>Profile</b></div><div id="myLoansBox" style="font-size:12px;margin-top:10px"></div></div></div></div></div>
<div id="page-send" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">💸 SEND</h2><div class="walletCard">🪙 <b id="sendPageGold">0</b> | 💎 <b id="sendPageGems">0</b><br><b id="sendPageMyID">INF-</b></div><div class="idPrefix"><b>INF-</b><input id="sendDigits" placeholder="12345678" maxlength="8"></div><input id="sendAmt" type="number" placeholder="Amount"><button class="btn" onclick="doSend()">➤ SEND</button></div></div>
<div id="page-withdraw" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">🏧 WITHDRAW</h2><input id="withdrawAmt" type="number" placeholder="Amount"><select id="withdrawCur"><option>Gold</option><option>Gems</option></select><button class="btn" onclick="doWithdraw()">🏧 WITHDRAW</button></div></div>
<div id="page-deposit" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">💰 DEPOSIT</h2><input id="depositAmt" type="number" placeholder="Amount"><select id="depositCur"><option>Gold</option><option>Gems</option></select><button class="btn" onclick="doDeposit()">💰 DEPOSIT</button></div></div>
<div id="page-exchange" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">🔄 EXCHANGE</h2><div class="bigBankBox" onclick="openExchange('gold_to_gem')">Gold >>>> Germ<br><small>100=1</small></div><div class="bigBankBox" style="margin-top:10px" onclick="openExchange('gem_to_gold')">Germ >>>> Gold<br><small>1=100</small></div><div id="exchangeForm"></div></div></div>
<div id="page-profile" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card" style="text-align:center"><div style="font-size:70px">👤</div><h2 id="profName">Player</h2><p id="profIDShow">ID:</p><p id="profBankID">Bank:</p><p>⭐ <b id="profRank">#-</b> | 🏆 <b id="profWins">0</b> | ❌ <b id="profLoss">0</b></p><p>🪙 <b id="profGold">0</b> | 💎 <b id="profGems">0</b></p><p>🚗 <b id="profCars">None</b></p><p>🌌 Galaxy Lvl <b id="profGalaxy">1</b> Kills <b id="profGalaxyKills">0</b></p><button class="btn2" onclick="openSecret()">🔒 Secret</button></div><div class="card"><h3>🎒 INVENTORY</h3><div id="profInventory"></div><div id="consumeBox"></div></div></div>
<div id="page-other" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card" style="text-align:center"><h2 id="otherName">Player</h2><div id="otherClassified" class="hidden"><h3>⚠️ Warning</h3><p>Cannot view profile 😉 Level up</p></div><div id="otherNormal"><p>⭐ <b id="otherRank">#-</b></p><p><b id="otherWins">0</b> Win | <b id="otherLoss">0</b> Lose</p><div id="otherActions"></div></div></div></div>
<div id="page-notifs" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">✉️ NOTIFICATIONS</h2><div id="notifList"></div></div></div>
<div id="page-economy" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2>💰 SERVER ECONOMY - LIVE 24/7</h2><p style="font-size:12px">Ticks every 5s - Up 📈 Down 📉</p><div class="grid"><div class="walletCard">Gold<br><b id="ecoGold">0</b></div><div class="walletCard">Germ<br><b id="ecoGems">0</b></div><div class="bigBankBox">Banks<br><b id="ecoBank">0</b></div><div class="bigBankBox">Fees<br><b id="ecoFees">0</b></div></div><h3>📈 CRYPTO LIVE</h3><canvas id="ecoChart" width="480" height="160" style="width:100%;background:#000;border:2px solid #00ffaa"></canvas><h3>💰 SECRET REQUESTS (Approved=Hidden)</h3><div id="ecoRequests"></div><h3>🏦 LOANS</h3><div id="ecoLoans"></div></div></div>
<div id="page-lottery" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">🎰 LOTTERY</h2><input id="lotBet" type="number" placeholder="1000"><select id="lotCur"><option>Gold</option><option>Gems</option></select><button class="btn" onclick="playLottery()">🎰 SPIN</button><div id="lotResult"></div></div></div>
<div id="page-challenge" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">🎮 CHALLENGE</h2><p id="challengeDashText"></p><div id="duelBox"></div><button class="btn2" onclick="goDash()">⬅ Back</button></div></div>
<div id="page-messages" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h1 style="text-align:center">💚 WhatsApp</h1><div style="display:flex;gap:8px"><div class="idPrefix" style="flex:1"><b>INF-</b><input id="addFriendDigits" placeholder="Add ID" maxlength="8"></div><button class="btn" style="width:auto" onclick="addFriendById()">➕ Add</button></div><div id="chatFriendList"></div></div></div>
<div id="page-chat" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">💬 <span id="chatWith">Friend</span></h2><div id="chatBox" style="background:#1a1a2e;border-radius:20px;padding:12px;min-height:260px;max-height:360px;overflow-y:auto"></div><div style="display:flex;gap:8px;margin-top:10px"><input id="msgInput" placeholder="Message..." style="flex:1"><button class="btn" style="width:70px" onclick="sendMsg()">➤</button></div></div></div>
<div id="page-scifi" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 style="text-align:center">🚀 SCI-FI</h2><div id="scifiList"></div></div></div>
<div id="page-review" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 90px"><div class="card"><h2 id="reviewTitle">⭐ Review</h2><textarea id="reviewText" style="height:140px"></textarea><button class="btn" onclick="submitReview()">📩 SEND</button></div></div>
<div id="backFab" style="position:fixed;left:16px;bottom:16px;width:58px;height:58px;border-radius:50%;background:#1a1a2e;display:none;align-items:center;justify-content:center;font-size:28px;color:#ffd700;border:3px solid #ffd700;cursor:pointer;z-index:60">←</div>
<div id="msgFab" style="position:fixed;right:16px;bottom:16px;width:62px;height:62px;border-radius:50%;background:linear-gradient(135deg,#ff006e,#ffd700,#00e5ff);display:none;align-items:center;justify-content:center;font-size:30px;border:3px solid #fff;cursor:pointer;z-index:60">💬</div>
<div id="bottomNav" class="bottomNav hidden"><div onclick="goDash()">🏡<small>Home</small></div><div onclick="openFullLeader()">🏆<small>Leader</small></div><div onclick="openBank()">💰<small>Bank</small></div><div onclick="openNotifs()">✉️<small>Notify</small></div></div>
<audio id="pinSound" preload="auto" src="https://cdn.pixabay.com/audio/2025/07/09/audio_121db7b43f.mp3"></audio>
<script>
function playPin(){try{var a=document.getElementById("pinSound");a.currentTime=0;a.play().catch(function(){})}catch(e){}}
var user=null;try{user=JSON.parse(localStorage.getItem("inf_user")||"null")}catch(e){}
var wins=0,losses=0,myGold=0,myGems=0,myCars=[];try{wins=parseInt(localStorage.getItem("inf_wins")||"0")||0;losses=parseInt(localStorage.getItem("inf_loss")||"0")||0;myGold=parseInt(localStorage.getItem("inf_gold")||"0")||0;myGems=parseInt(localStorage.getItem("inf_gems")||"0")||0;myCars=JSON.parse(localStorage.getItem("inf_cars")||"[]")}catch(e){}
var loggedIn=false,currentPage="page-home",seen=[];try{seen=JSON.parse(localStorage.getItem("inf_seen")||"[]")}catch(e){}
var hasEntered=false,pinCb=null,idCb=null,leaderMode="pvp",chatWith="",shopCat="All",quizRound=[],quizIdx=0,quizScore=0,quizMode="",quizT=null,quizLeft=0,gKills=0,gLevel=1,dinoJumps=0,dinoInt=null,fallInt=null;
function extraTime(){var t=0;myCars.forEach(function(c){if(/Lamborghini|Ferrari|Bugatti/.test(c))t+=15;else if(/Tesla|Mercedes|BMW/.test(c))t+=10;else if(/Audi|Rover/.test(c))t+=7;else t+=2});return Math.min(t,30)}
function isDom(){return user&&user.name&&user.name.toLowerCase()==="dominic"&&user.password==="2164"}
function toast(m){var t=document.getElementById("toast");t.innerText=m;t.classList.remove("hidden");setTimeout(function(){t.classList.add("hidden")},4500)}
function showPage(id){currentPage=id;["page-home","page-register","page-dash","page-leader","page-game","page-bank","page-send","page-withdraw","page-deposit","page-exchange","page-profile","page-other","page-notifs","page-economy","page-lottery","page-challenge","page-messages","page-chat","page-scifi","page-review"].forEach(function(p){var e=document.getElementById(p);if(e){e.classList.add("hidden");e.style.display="none"}});var tg=document.getElementById(id);if(tg){tg.classList.remove("hidden");tg.style.display="block"}window.scrollTo(0,0);var r=document.getElementById("topRight"),nv=document.getElementById("bottomNav"),b=document.getElementById("backFab"),mf=document.getElementById("msgFab");var isEnter=(id==="page-home"||id==="page-register");if(isEnter){if(r)r.style.display="none";if(nv)nv.classList.add("hidden");if(b)b.style.display="none";if(mf)mf.style.display="none"}else if(loggedIn&&id==="page-dash"){if(r)r.style.display="flex";if(nv)nv.classList.remove("hidden");if(b)b.style.display="none";if(mf)mf.style.display="flex"}else if(loggedIn){if(r)r.style.display="none";if(nv)nv.classList.add("hidden");if(b)b.style.display="flex";if(mf)mf.style.display="flex"}else{if(r)r.style.display="none";if(nv)nv.classList.add("hidden");if(b)b.style.display="none";if(mf)mf.style.display="none"}}
function goDash(){if(!loggedIn){showPage("page-register");return}showPage("page-dash");loadLeader()}
function goBack(){if(currentPage==="page-register")showPage("page-home");else if(currentPage==="page-chat")showPage("page-messages");else goDash()}
function enterClicked(){hasEntered=true;showPage("page-register");showRegister();setTimeout(function(){var o=document.getElementById("page-welcome");o.classList.remove("hidden");o.style.display="flex"},100)}
function welcomeChoice(c){var o=document.getElementById("page-welcome");o.classList.add("hidden");o.style.display="none";if(c==="yes")showLogin();else showRegister()}
function showRegister(){document.getElementById("registerForm").classList.remove("hidden");document.getElementById("loginForm").classList.add("hidden")}
function showLogin(){document.getElementById("registerForm").classList.add("hidden");document.getElementById("loginForm").classList.remove("hidden")}
function saveLocal(){try{localStorage.setItem("inf_user",JSON.stringify(user));localStorage.setItem("inf_wins",wins);localStorage.setItem("inf_loss",losses);localStorage.setItem("inf_gold",myGold);localStorage.setItem("inf_gems",myGems);localStorage.setItem("inf_seen",JSON.stringify(seen));localStorage.setItem("inf_cars",JSON.stringify(myCars))}catch(e){}}
function doLogout(){try{localStorage.clear()}catch(e){}user=null;loggedIn=false;hasEntered=false;wins=0;losses=0;myGold=0;myGems=0;myCars=[];showPage("page-home");toast("👋 Logged out")}
function special(n,pw){var x=(n||"").toLowerCase().trim();if(x==="britney"||x==="kayula")return"Welcome MY Fiance 💖";if(x==="blessing")return"Welcome Avatar ✨";if(x==="lubuto")return"Welcome Desk Bender 🛠️";if(x==="dominic"&&pw==="2164")return"Welcome Infinity Emperor ♾";return"Welcome, "+n+" 👑"}
function doRegister(){var n=document.getElementById("regName").value.trim();var pw=document.getElementById("regPass").value.trim();if(!n){toast("Enter name");return}if(!pw||pw.length!==4||isNaN(pw)){toast("Password 4 digits");return}if(pw==="1234"||pw==="0000"){toast("Too easy");return}fetch("/api/player?name="+encodeURIComponent(n)).then(function(r){return r.json()}).then(function(d){if(d&&d.found){showLogin();document.getElementById("loginName").value=n;toast("Account found! Login");return}user={name:n,password:pw};wins=0;losses=0;myGold=0;myGems=0;seen=[];myCars=[];saveLocal();syncScore();enterDash(special(n,pw))})}
function doLogin(){var n=document.getElementById("loginName").value.trim();var pw=document.getElementById("loginPass").value.trim();fetch("/api/player?name="+encodeURIComponent(n)+"&password="+encodeURIComponent(pw)).then(function(r){return r.json()}).then(function(d){if(d&&d.found&&d.password_ok!==false){user={name:n,password:pw};wins=d.wins||0;losses=d.losses||0;myGold=d.gold||0;myGems=d.gems||0;seen=d.seen||[];myCars=d.cars||[];gLevel=d.glevel||1;gKills=d.gkills||0;saveLocal();enterDash(special(n,pw))}else toast("Wrong / Not found")})}
function enterDash(m){loggedIn=true;hasEntered=true;toast(m);playPin();showPage("page-dash");document.getElementById("welcomeText").innerText=m;loadLeader();loadMe();checkAnn()}
function syncScore(){if(!user)return;fetch("/api/score",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,password:user.password,wins:wins,losses:losses,gold:myGold,gems:myGems,seen:seen,cars:myCars,glevel:gLevel,gkills:gKills})}).catch(function(){})}
function loadMe(){if(!user)return;fetch("/api/player?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){if(!d||!d.found)return;myGold=d.gold;myGems=d.gems;myCars=d.cars||myCars;document.getElementById("myRank").innerText="#-";document.getElementById("myCarsCount").innerText=myCars.length;document.getElementById("myExtra").innerText=extraTime();document.getElementById("bankGold").innerText=d.bank_gold||0;document.getElementById("bankGems").innerText=d.bank_gems||0;document.getElementById("bankIDShow").innerText=d.bank_id;document.getElementById("walletGold").innerText=d.gold;document.getElementById("walletGems").innerText=d.gems})}
function loadLeader(){fetch("/api/leaderboard?mode=pvp").then(function(r){return r.json()}).then(function(d){var h="";(d.players||[]).slice(0,5).forEach(function(p,i){h+="<div class='leadRow' onclick=\"viewOther('"+p.name+"')\"><span>"+(i+1)+". "+p.name+"</span><span>🏆 "+p.wins+"W</span></div>"});document.getElementById("leaderList").innerHTML=h||"No players"})}
function setLeaderMode(m){leaderMode=m;openFullLeader()}
function openFullLeader(){showPage("page-leader");fetch("/api/leaderboard?mode="+leaderMode).then(function(r){return r.json()}).then(function(d){var h="";(d.players||[]).forEach(function(p,i){h+="<div class='leadRow' onclick=\"viewOther('"+p.name+"')\"><span>"+(i+1)+". "+p.name+"<br><small>"+p.player_id+"</small></span><span>"+(leaderMode==="gold"?"🪙 "+p.gold:leaderMode==="gems"?"💎 "+p.gems:"🏆 "+p.wins+"W")+"</span></div>"});document.getElementById("fullLeaderList").innerHTML=h||"No players"})}
function viewOther(name){fetch("/api/player?name="+encodeURIComponent(name)).then(function(r){return r.json()}).then(function(d){showPage("page-other");document.getElementById("otherName").innerText=d.name;if(d.classified){document.getElementById("otherClassified").classList.remove("hidden");document.getElementById("otherNormal").classList.add("hidden")}else{document.getElementById("otherClassified").classList.add("hidden");document.getElementById("otherNormal").classList.remove("hidden");document.getElementById("otherRank").innerText=d.rank;document.getElementById("otherWins").innerText=d.wins;document.getElementById("otherLoss").innerText=d.losses;document.getElementById("otherActions").innerHTML="<button class='btn' onclick=\"openBankSendTo('"+d.player_id+"')\">💸 Send Gold</button>"}})}
function openMyProfile(){showPage("page-profile");fetch("/api/player?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){document.getElementById("profName").innerText=special(d.name,user.password);document.getElementById("profIDShow").innerText="ID:"+d.player_id;document.getElementById("profBankID").innerText=d.bank_id;document.getElementById("profRank").innerText="#-";document.getElementById("profWins").innerText=d.wins;document.getElementById("profLoss").innerText=d.losses;document.getElementById("profGold").innerText=d.gold;document.getElementById("profGems").innerText=d.gems;document.getElementById("profCars").innerText=(d.cars||[]).join(", ")||"None";document.getElementById("profGalaxy").innerText=d.glevel||1;document.getElementById("profGalaxyKills").innerText=d.gkills||0;var inv=d.items||[];var h="";inv.forEach(function(it){h+="<div style='padding:10px;background:rgba(0,0,0,.4);border-radius:12px;margin:6px 0'>🎒 "+it+"</div>"});document.getElementById("profInventory").innerHTML=h||"No items";var cb=document.getElementById("consumeBox");var drink=inv.find(function(x){return /Cola|Juice|Drink/.test(x)});var food=inv.find(function(x){return /Burger|Pizza|Donut/.test(x)});var h2="";if(drink)h2+="<button class='btn' onclick=\"consumeP('"+drink+"')\">🥤 Drink "+drink+"</button>";if(food)h2+="<button class='btn2' onclick=\"consumeP('"+food+"')\">🍔 Eat "+food+"</button>";cb.innerHTML=h2})}
function consumeP(p){openPin("PIN to consume "+p,function(pin){var b=[20,50,100][Math.floor(Math.random()*3)];fetch("/api/consume",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,product:p,bonus:b})}).then(function(r){return r.json()}).then(function(d){wins=d.wins;saveLocal();syncScore();toast("😋 +"+b+" Wins");openMyProfile()})})}
function openSecret(){var o=document.getElementById("secretOverlay");o.classList.remove("hidden");o.style.display="flex";playPin()}
function closeSecret(){var o=document.getElementById("secretOverlay");o.classList.add("hidden");o.style.display="none"}
function sendMoneyRequest(){var m=document.getElementById("reqMsg").value;var a=document.getElementById("reqAmt").value;var c=document.getElementById("reqCur").value;closeSecret();fetch("/api/request_money",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,amount:a||"",currency:c,message:m})}).then(function(){toast("🔒 Secret sent");playPin()})}
function openBank(){showPage("page-bank");loadMe();fetch("/api/player?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){var h="";(d.loans||[]).forEach(function(l){h+="<div style='padding:8px;background:rgba(0,0,0,.4);border-radius:10px;margin:4px 0'>🏦 "+l.amount+" "+l.currency+" - "+l.status+"</div>"});document.getElementById("myLoansBox").innerHTML=h||"<small>No loans</small>"})}
function openLoan(){var o=document.getElementById("loanOverlay");o.classList.remove("hidden");o.style.display="flex";playPin()}
function closeLoan(){var o=document.getElementById("loanOverlay");o.classList.add("hidden");o.style.display="none"}
function submitLoan(){var a=document.getElementById("loanAmt").value;var c=document.getElementById("loanCur").value;var dt=document.getElementById("loanDate").value;if(!a||!dt){toast("Amount + date");return}closeLoan();openPin("PIN for Loan "+a+" "+c,function(pin){fetch("/api/loan_apply",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,amount:a,currency:c,repay_date:dt})}).then(function(){toast("🏦 Loan sent to Dominic");playPin()})})}
function openBankSendTo(id){openSendPage();document.getElementById("sendDigits").value=id.replace("INF-","")}
function openSendPage(){showPage("page-send");fetch("/api/player?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){document.getElementById("sendPageGold").innerText=d.gold;document.getElementById("sendPageGems").innerText=d.gems;document.getElementById("sendPageMyID").innerText=d.player_id})}
function openWithdrawPage(){showPage("page-withdraw")}
function openDepositPage(){showPage("page-deposit")}
function openExchangePage(){showPage("page-exchange");document.getElementById("exchangeForm").innerHTML=""}
function openExchange(dir){document.getElementById("exchangeForm").innerHTML="<input id='exAmt' type='number' placeholder='Amount'><button class='btn' onclick=\"doExchange('"+dir+"')\">Confirm</button>"}
function doSend(){var dg=document.getElementById("sendDigits").value.replace(/[^0-9]/g,"");var amt=parseInt(document.getElementById("sendAmt").value||"0");if(dg.length<8||!amt){toast("ID + Amount");return}openPin("PIN to send "+amt,function(pin){fetch("/api/transfer",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({sender:user.name,pin:pin,receiver_id:"INF-"+dg,amount:amt})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.sender_gold;saveLocal();toast("✅ Sent");playPin();openNotifs()})})}
function doWithdraw(){var amt=parseInt(document.getElementById("withdrawAmt").value||"0");var cur=document.getElementById("withdrawCur").value;openPin("PIN withdraw "+amt,function(pin){fetch("/api/bank_action",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,amount:amt,action:"withdraw",currency:cur})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.gold;myGems=d.gems;saveLocal();toast("✅ Withdrawn")})})}
function doDeposit(){var amt=parseInt(document.getElementById("depositAmt").value||"0");var cur=document.getElementById("depositCur").value;openPin("PIN deposit "+amt,function(pin){fetch("/api/bank_action",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,amount:amt,action:"deposit",currency:cur})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.gold;myGems=d.gems;saveLocal();toast("✅ Deposited")})})}
function doExchange(dir){var amt=parseInt(document.getElementById("exAmt").value||"0");openPin("PIN Exchange",function(pin){fetch("/api/exchange",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,amount:amt,direction:dir})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.gold;myGems=d.gems;saveLocal();toast("✅ Exchange done")})})}
function openNotifs(){showPage("page-notifs");fetch("/api/player?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){var h="";(d.notifs||[]).slice().reverse().forEach(function(n){h+="<div style='padding:12px;background:rgba(0,0,0,.4);border-radius:14px;margin:8px 0'>"+n.text+"<br><small>"+(n.time||"")+"</small></div>"});document.getElementById("notifList").innerHTML=h||"No notifications";if(h)playPin()})}
function openEconomy(){if(!isDom()){toast("🔒 Dominic only");return}showPage("page-economy");fetch("/api/economy?name=Dominic&password=2164").then(function(r){return r.json()}).then(function(d){var e=d.economy||{};document.getElementById("ecoGold").innerText=e.gold||0;document.getElementById("ecoGems").innerText=e.gems||0;document.getElementById("ecoBank").innerText=e.bank||0;document.getElementById("ecoFees").innerText=e.fees||0;var h="";(d.requests||[]).forEach(function(rq){h+="<div style='padding:12px;background:rgba(0,0,0,.4);border-radius:14px;margin:8px 0'>"+rq.from+" wants "+rq.amount+" "+rq.currency+" <button class='btn' onclick=\"approveReq('"+rq.id+"',"+rq.amount+",'"+rq.currency+"')\">✅ Approve</button></div>"});document.getElementById("ecoRequests").innerHTML=h||"No requests";var h2="";(d.loans||[]).forEach(function(l){h2+="<div style='padding:12px;background:rgba(0,0,0,.4);border-radius:14px;margin:8px 0'>"+l.from+" Loan "+l.amount+" "+l.currency+" Repay "+l.repay_date+" ["+l.status+"] <button class='btn' onclick=\"domLoan('"+l.id+"',true)\">✅ Approve</button><button class='btn2' onclick=\"domLoan('"+l.id+"',false)\">❌ Decline</button></div>"});document.getElementById("ecoLoans").innerHTML=h2||"No loans";var cv=document.getElementById("ecoChart");if(cv){var ctx=cv.getContext("2d");ctx.clearRect(0,0,480,160);ctx.strokeStyle="#00ffaa";ctx.lineWidth=3;ctx.beginPath();var hist=e.hist||[0];hist.forEach(function(v,i){var x=i/(Math.max(1,hist.length-1))*460+10;var y=150-(v/(Math.max(1,Math.max.apply(null,hist)))*120);if(i===0)ctx.moveTo(x,y);else ctx.lineTo(x,y)});ctx.stroke()}})}
function approveReq(id,amt,cur){openPin("PIN approve "+amt,function(pin){fetch("/api/request_approve",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({admin:"dominic",pin:pin,request_id:id,amount:amt,currency:cur})}).then(function(){toast("✅ Approved - Hidden");openEconomy()})})}
function domLoan(id,ap){if(!ap){openPin("PIN decline loan",function(pin){fetch("/api/loan_dominic",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({admin:"dominic",pin:pin,loan_id:id,approve:false})}).then(function(){toast("Loan declined");openEconomy()})});return}var nd=prompt("New repay date? Leave blank = same","");openPin("PIN approve loan",function(pin){fetch("/api/loan_dominic",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({admin:"dominic",pin:pin,loan_id:id,approve:true,new_date:nd})}).then(function(){toast("Loan sent to player for confirm");openEconomy()})})}
function openLottery(){showPage("page-lottery")}
function playLottery(){var bet=parseInt(document.getElementById("lotBet").value||"0");var cur=document.getElementById("lotCur").value;openPin("PIN Lottery "+bet,function(pin){fetch("/api/lottery",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,bet:bet,currency:cur})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.gold;myGems=d.gems;saveLocal();document.getElementById("lotResult").innerHTML=d.result.win?"<h2 style='color:#00ff88'>🎉 WON "+d.result.prize+"</h2>":"<h2 style='color:#ff5555'>😢 Lost "+d.result.lost+"</h2>"})})}
function openAnn(){if(!isDom()){toast("🔒 Dominic only");return}var o=document.getElementById("annOverlay");o.classList.remove("hidden");o.style.display="flex"}
function closeAnn(){var o=document.getElementById("annOverlay");o.classList.add("hidden");o.style.display="none"}
function sendAnn(){var t=document.getElementById("annText").value.trim();if(!t){toast("Type announcement");return}closeAnn();openPin("PIN 2164 to Announce",function(pin){fetch("/api/announce",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({admin:"dominic",pin:pin,text:t})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}toast("📢 Announced to ALL");playPin()})})}
function checkAnn(){fetch("/api/announcements").then(function(r){return r.json()}).then(function(d){var a=(d.announcements||[]).slice(-1)[0];if(a){var bar=document.getElementById("announceBar");bar.innerText="📢 "+a.text;bar.classList.remove("hidden");playPin();setTimeout(function(){bar.classList.add("hidden")},1000)}})}
// QUESTIONS - 100 HARD - format Q|A|W1|W2|CAT
var QB=["vanity of vanities book?|Ecclesiastes - Solomon|Genesis - Moses|Psalms - David|OLD","Woman judge under palm tree?|Deborah - Palm tree|Esther - Palace|Ruth - Field|OLD","Methuselah lived how long?|969 years|930 years|950 years|OLD","3 men in fiery furnace?|Shadrach, Meshach, Abednego|Daniel, Shadrach, Meshach|Peter, James, John|OLD","High priest tore robes?|Caiaphas|Annas|Pilate|NEW","24 elders represent?|12 tribes + 12 apostles|24 prophets|24 angels|NEW","Sheol vs Gehenna?|Sheol=grave, Gehenna=hell punishment|Same thing|Both heaven|OLD","King and priest?|Melchizedek|David|Solomon|OLD","Goliath spearhead weight?|600 shekels ~15lbs|100 shekels|1000 shekels|OLD","5 books Torah Hebrew?|Bereshit, Shemot, Vayikra, Bamidbar, Devarim|Genesis, Exodus...|Torah 1-5|OLD","Father of Caleb?|Jephunneh|Jesse|Jacob|OLD","Moses father-in-law?|Jethro / Reuel|Aaron|Joshua|OLD","First Gentile church?|Antioch|Rome|Corinth|NEW","Ebenezer means?|Stone of Help - Samuel|Stone of God - Moses|Holy Stone - David|OLD","Fear not how many times?|365 - one per day|100|50|OLD","Only apostle natural death?|John|Peter|Paul|NEW","Demon called Legion?|Legion - we are many|Beelzebub|Lucifer|NEW","Longest chapter?|Psalm 119 - Word of God|Psalm 23|Genesis 1|OLD","Shortest chapter?|Psalm 117 - 2 verses|Psalm 23|John 11|OLD","Struck blind touching Ark?|Uzzah|David|Saul|OLD"];
var QR=["Always hungry, finger red?|Fire|Water|Wind|FUNNY","Man photo - father's son?|His son|His brother|His father|SMART","3 boxes labels wrong, pick 1?|Pick from 'both' box|Pick apples box|Pick oranges box|SMART","Plane crashes border, bury survivors?|Nowhere - alive|USA|Canada|FUNNY","Rooster lays egg on roof?|Roosters don't lay eggs|Left side|Right side|FUNNY","Overtake 2nd place?|2nd place|1st place|3rd place|SMART","3/7 chicken, 2/3 cat, 1/2 goat?|Chicago|Chicatgo|Catgo|SMART","Cowboy Friday 3 days leaves Friday?|Horse named Friday|Time travel|Magic|FUNNY","Once in minute, twice moment?|Letter M|Letter O|Letter N|SMART","Man pushes car to hotel bankrupt?|Playing Monopoly|Real bankrupt|Lost|FUNNY","Maker doesn't need, buyer doesn't use?|A coffin|A car|A house|SMART","Hold in right not left?|Your left hand|Your right foot|Pen|SMART","Cities no houses, forests no trees?|A map|A book|A photo|SMART","1,11,21,1211,111221 next?|312211|1112211|121211|SMART","12 coins 3 weighs fake?|Divide 4-4-4 then 1-1|Guess|Weigh all|SMART","2 doors 1 lies 1 truth 1 Q?|Ask what other would say, pick opposite|Ask truth|Ask lie|SMART","Fragile saying name breaks?|Silence|Glass|Egg|SMART","Beginning eternity, end time?|Letter E|Letter A|Letter T|SMART","Dies old age on 25th birthday?|Born Feb 29 leap year|Magic|Time|FUNNY","Head tail brown no legs?|A penny|A dog|A snake|FUNNY","Not seen but felt, king kneel?|Love|Money|Power|LOVE","Grows when give away?|Love|Money|Gold|LOVE","Prison no bars, chain no iron?|Being in love|Jail|Home|LOVE","Broken without touch, mended without fix?|A heart|A glass|A bone|LOVE","Written no pen, spoken no voice?|Love|Dream|Song|LOVE","War both win surrender?|Love|Peace|War|LOVE","Time stop and fly?|Love|Sleep|Dream|LOVE","Question and answer in 3 words?|I love you|Who are you|Yes I do|LOVE","Blind but sees everything?|Love|God|Faith|LOVE","Beginning and forever?|True love|Life|Time|LOVE","Stranger feel home?|Love|Money|Home|LOVE","Felt heart measured tears?|Love|Pain|Joy|LOVE","Cure and disease?|Love|Medicine|Virus|LOVE","Light darkness and darkness light?|Love|Sun|Moon|LOVE","Lose yourself find yourself?|Love|Travel|Dream|LOVE","100 prisoners 100 boxes 50 open?|Loop strategy - follow chain|Random|Guess|SMART","Bat+ball $1.10 bat $1 more?|5 cents|10 cents|50 cents|PROGRAMMERS","3 numbers add 12 multiply 48?|2,4,6|3,4,5|1,5,6|SMART","Half of 2+2?|3|2|4|SMART","17 sheep all but 9 die?|9|8|17|SMART","Months have 28 days?|All 12|February only|1|SMART","3-gal and 5-gal measure 4?|Fill 5 pour 3 leave 2 etc|Impossible|Fill 3|SMART","2 fathers 2 sons 3 people?|Grandfather father son|Twins|Brothers|SMART","5 machines 5 parts 5 min, 100 machines?|5 minutes|100 min|20 min|SMART","Boat sinks no one dies?|Everyone married - no single|Boat empty|Swim|FUNNY","3 consecutive double letters?|Bookkeeper|Mississippi|Letter|PROGRAMMERS","Same forwards backwards race?|Racecar|Level|Madam|SMART","Number letters = value?|Four - 4 letters|Three|Five|SMART","Man 3x son, in 15y 2x, son age?|15 years|10 years|20 years|SMART","O T T F F S S E next?|N - Nine|T|E|SMART","Subtract 10 from 100 how many?|Once - then 90|10 times|9 times|SMART","4 letters sometimes 9 never 5?|What - word play|Yes|No|SMART","OCT 31 == DEC 25?|Octal 31 = Decimal 25|Halloween|Christmas|PROGRAMMERS","10 types people binary?|10 binary = 2|10 people|2 types|PROGRAMMERS","[] + [] in JS?|Empty string|0|NaN|PROGRAMMERS","0.1+0.2?|0.30000000000000004|0.3|0.4|PROGRAMMERS","Programmer dies shower?|Lather Rinse Repeat loop|Drowned|Slipped|PROGRAMMERS","What is deadlock?|Two waiting each other forever|Bug|Crash|PROGRAMMERS","Bug vs feature?|Documentation|Code|Test|PROGRAMMERS","null vs undefined?|Null intentional, Undefined never assigned|Same|Opposite|PROGRAMMERS","!false = ?|true|false|0|PROGRAMMERS","NaN !== NaN why?|IEEE 754 spec|Bug|Error|PROGRAMMERS","What is recursion?|To understand recursion must understand recursion|Loop|Function|PROGRAMMERS","Hardest CS problem?|Naming, cache, off-by-one|Coding|Debugging|PROGRAMMERS","1 + '1' in JS?|'11' string|2|11 number|PROGRAMMERS","Developer broke?|Used up all cache|No money|Lost job|PROGRAMMERS","DELETE vs TRUNCATE?|DELETE rollback+WHERE, TRUNCATE drops all|Same|No diff|PROGRAMMERS","Scarecrow award?|Outstanding in field|Funny|Tall|FUNNY","Fish without eyes?|A fsh|Blind fish|Nemo|FUNNY","Coffee police report?|Got mugged - depresso|Stolen|Cold|FUNNY","Cheese not yours?|Nacho cheese|Cheddar|Mozzarella|FUNNY","Bicycle fall over?|Two-tired|Flat|Broken|FUNNY","Can opener not work?|A can't opener|Broken|Rusty|FUNNY","Math book sad?|Too many problems|Hard|Boring|FUNNY","Bear no teeth?|A gummy bear|Old bear|Baby|FUNNY","Golfer two pants?|Hole in one|Cold|Fashion|FUNNY","Hardest riddle?|One you still thinking|Last one|First one|FUNNY"];
function parseQ(s){var p=s.split("|");var opts=[p[1],p[2],p[3]];for(var i=opts.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1));var t=opts[i];opts[i]=opts[j];opts[j]=t}return {q:p[0],correct:p[1],opts:opts,cat:p[4]}}
function pickRiddleCat(){showPage("page-game");document.getElementById("gameTitle").innerText="🧩 PICK RIDDLE TYPE";document.getElementById("gameBody").innerHTML="<p>Pick one - 10 Questions, Timer, 3 Options</p><button class='btn2' onclick=\"startQuiz('RIDDLE','LIVE')\">🎤 Live</button><button class='btn2' onclick=\"startQuiz('RIDDLE','SMART')\">🧠 Smart / Logic</button><button class='btn2' onclick=\"startQuiz('RIDDLE','FUNNY')\">😂 Funny</button><button class='btn2' onclick=\"startQuiz('RIDDLE','PROGRAMMERS')\">💻 Programmers</button><button class='btn2' onclick=\"startQuiz('RIDDLE','LOVE')\">💖 Love</button><button class='btn2' onclick='goDash()'>⬅ Back</button>"}
function pickBible(){showPage("page-game");document.getElementById("gameTitle").innerText="📖 PICK TESTAMENT";document.getElementById("gameBody").innerHTML="<p>Pick - Only Bible questions from that Testament</p><button class='btn2' onclick=\"startQuiz('BIBLE','OLD')\">📜 Old Testament</button><button class='btn2' onclick=\"startQuiz('BIBLE','NEW')\">✝️ New Testament</button><button class='btn2' onclick='goDash()'>⬅ Back</button>"}
function startQuiz(mode,cat){quizMode=mode;var pool=(mode==="BIBLE"?QB:QR);var filtered=pool.filter(function(s){var c=s.split("|")[4];if(cat==="LIVE")return true;return c===cat});var avail=filtered.filter(function(s){return seen.indexOf(s)<0});if(avail.length<10){seen=[];avail=filtered}avail.sort(function(){return Math.random()-0.5});quizRound=avail.slice(0,10).map(parseQ);quizIdx=0;quizScore=0;showQuizQ()}
function showQuizQ(){if(quizIdx>=10){finishQuiz();return}var q=quizRound[quizIdx];showPage("page-game");document.getElementById("gameTitle").innerText=(quizMode==="BIBLE"?"📖 BIBLE FIGHT":"🧩 RIDDLES")+" - Q "+(quizIdx+1)+"/10";var total=15+extraTime();quizLeft=total;var hint="";if(myCars.length>0)hint="<p style='font-size:12px;color:#ffd700'>🚗 Car Bonus +"+extraTime()+"s = "+total+"s total</p>";document.getElementById("gameBody").innerHTML="<div style='font-size:28px;font-weight:900' id='timerTxt'>⏱️ "+quizLeft+"s</div><div class='timerBar'><div class='timerFill' id='timerFill' style='width:100%'></div></div>"+hint+"<p style='font-size:18px;font-weight:700'>"+q.q+"</p><p>🏆 Wins: "+wins+" | 🪙 "+myGold+" | Score: "+quizScore+"/10</p><div id='hintBox'></div>"+q.opts.map(function(o,i){return "<button class='opt' onclick=\"answerQuiz("+i+")\">"+o+"</button>"}).join("")+"<button class='btn2' onclick='goDash()'>⬅ Quit</button>";if(quizT)clearInterval(quizT);quizT=setInterval(function(){quizLeft--;var t=document.getElementById("timerTxt");if(t)t.innerText="⏱️ "+quizLeft+"s";var f=document.getElementById("timerFill");if(f)f.style.width=(quizLeft/total*100)+"%";if(quizLeft===5&&myCars.length>0){var hb=document.getElementById("hintBox");if(hb)hb.innerHTML="<p style='color:#ffd700'>💡 HINT (Expensive Car): Answer starts with '"+q.correct.charAt(0)+"' - "+q.correct.length+" letters</p>"}if(quizLeft<=0){clearInterval(quizT);losses++;saveLocal();syncScore();toast("⏰ Time up! Correct: "+q.correct);quizIdx++;setTimeout(showQuizQ,900)}},1000)}
function answerQuiz(i){if(quizT)clearInterval(quizT);var q=quizRound[quizIdx];var chosen=q.opts[i];var ok=(chosen===q.correct);if(ok){quizScore++;wins++;myGold+=50;toast("✅ Correct +1 Win +50 Gold")}else{losses++;toast("❌ Wrong! Correct: "+q.correct)}seen.push(q.q+"|"+q.correct);saveLocal();syncScore();quizIdx++;setTimeout(showQuizQ,900)}
function finishQuiz(){showPage("page-game");document.getElementById("gameTitle").innerText="🏁 ROUND DONE";document.getElementById("gameBody").innerHTML="<h2>Score: "+quizScore+"/10</h2><p>Wins: "+wins+" | Gold: "+myGold+"</p><button class='btn' onclick=\"pickRiddleCat()\">🧩 Play Riddles Again</button><button class='btn2' onclick=\"pickBible()\">📖 Bible Again</button><button class='btn2' onclick='goDash()'>⬅ Dashboard</button>"}
function openSciFi(){var now=new Date();var openDate=new Date(2026,11,25);if(now<openDate){showPage("page-game");document.getElementById("gameTitle").innerText="🚀 SCI-FI LOCKED";document.getElementById("gameBody").innerHTML="<p>Opens 25 Dec 2026 automatically</p><button class='btn2' onclick='goDash()'>⬅ Back</button>";return}showPage("page-scifi");var games=[["🌌 Galaxy Shooter","openGalaxy()"],["🦖 Dino Jump - 10 jumps = reward","openDino()"],["🍬 Royal Match - Match 3","openMatch()"],["🧩 Puzzle Rush","openMatch()"],["🏎️ Space Racing","openMatch()"],["🎯 Target Shooter","openGalaxy()"],["💎 Gem Blast","openMatch()"],["🃏 Card Battle","openMatch()"],["🏃 Runner","openDino()"],["🚀 Rocket Jump","openDino()"]];var h="";games.forEach(function(g){h+="<button class='btn2' onclick=\""+g[1]+"\">"+g[0]+"</button>"});document.getElementById("scifiList").innerHTML=h}
function openGalaxy(){showPage("page-game");document.getElementById("gameTitle").innerText="🌌 GALAXY SHOOTER - PLAN";document.getElementById("gameBody").innerHTML="<p>Plan: Things fall from sky - TAP to kill!</p><p>Level "+gLevel+" - Need "+(gLevel===1?100:gLevel*500)+" kills to level up (x5)</p><p>Kills this level: "+gKills+"</p><button class='btn' onclick='startGalaxy()'>🚀 START GALAXY</button><button class='btn2' onclick='openSciFi()'>⬅ Sci-Fi</button>"}
function startGalaxy(){showPage("page-game");document.getElementById("gameTitle").innerText="🌌 GALAXY - Level "+gLevel;document.getElementById("gameBody").innerHTML="<p>Kills: <b id='gKillTxt'>"+gKills+"</b> | Need: "+(gLevel===1?100:gLevel*500)+" | Level: "+gLevel+"</p><div class='fallArea' id='fallArea'></div><button class='btn2' onclick='stopGalaxy();openSciFi()'>⬅ Stop</button>";var area=document.getElementById("fallArea");var speed=Math.max(600,1800-(gLevel*200));if(fallInt)clearInterval(fallInt);fallInt=setInterval(function(){var el=document.createElement("div");el.className="fallItem";el.innerText=["👾","🛸","☄️","👽","🛰️"][Math.floor(Math.random()*5)];el.style.left=Math.random()*85+"%";el.style.top="0px";area.appendChild(el);var top=0;var iv=setInterval(function(){top+=8+gLevel*3;el.style.top=top+"px";if(top>380){clearInterval(iv);if(el.parentNode)el.parentNode.removeChild(el)}},50);el.onclick=function(){gKills++;wins+=0;var t=document.getElementById("gKillTxt");if(t)t.innerText=gKills;if(el.parentNode)el.parentNode.removeChild(el);clearInterval(iv);var need=(gLevel===1?100:gLevel*500);if(gKills>=need){stopGalaxy();gLevel++;gKills=0;wins+=50;var rew=Math.floor(Math.random()*106)+45;if(Math.random()<0.5){myGold+=rew;toast("🌌 LEVEL UP! Level "+gLevel+" +50 Wins +"+rew+" Gold")}else{myGems+=rew;toast("🌌 LEVEL UP! +50 Wins +"+rew+" Germ")}saveLocal();syncScore();openGalaxy()}}},speed)}
function stopGalaxy(){if(fallInt)clearInterval(fallInt)}
function openDino(){showPage("page-game");document.getElementById("gameTitle").innerText="🦖 DINO JUMP - Tap Dino";document.getElementById("gameBody").innerHTML="<p>Jumps: <b id='dinoTxt'>"+dinoJumps+"</b> | Every 10 jumps = 45-150 Gold/Germ OR 10 Wins</p><div class='dinoArea' id='dinoArea'><div class='dino' id='dinoEl'>🦖</div><div class='cactus' id='cactusEl'>🌵</div></div><button class='btn' onclick='jumpDino()'>🦖 TAP TO JUMP</button><p>Tap dino to play - like screenshot</p><button class='btn2' onclick='stopDino();openSciFi()'>⬅ Sci-Fi</button>";var cx=400;if(dinoInt)clearInterval(dinoInt);dinoInt=setInterval(function(){cx-=6;if(cx<-30)cx=400;var c=document.getElementById("cactusEl");if(c)c.style.left=cx+"px"},50)}
function stopDino(){if(dinoInt)clearInterval(dinoInt)}
function jumpDino(){var d=document.getElementById("dinoEl");if(!d)return;d.style.bottom="90px";setTimeout(function(){d.style.bottom="20px"},350);dinoJumps++;var t=document.getElementById("dinoTxt");if(t)t.innerText=dinoJumps;if(dinoJumps%10===0){var r=Math.floor(Math.random()*106)+45;var type=Math.random();if(type<0.4){myGold+=r;toast("🦖 10 Jumps! +"+r+" Gold")}else if(type<0.8){myGems+=r;toast("🦖 10 Jumps! +"+r+" Germ")}else{wins+=10;toast("🦖 10 Jumps! +10 Wins")}saveLocal();syncScore()}}
function openMatch(){showPage("page-game");document.getElementById("gameTitle").innerText="🍬 ROYAL MATCH - Easy start, harder every level";var level=1;var emojis=["🍬","🍭","🍓","🍇","💎","⭐"];var board="";for(var i=0;i<9;i++){board+="<div style='display:inline-block;font-size:36px;padding:8px;cursor:pointer;background:rgba(255,255,255,.15);border-radius:12px;margin:4px' onclick=\"matchTap(this)\">"+emojis[Math.floor(Math.random()*emojis.length)]+"</div>"}document.getElementById("gameBody").innerHTML="<p>Tap 3 same candies to match! Level "+level+" - Gets harder every level</p><div style='text-align:center'>"+board+"</div><p>Score: <b id='matchScore'>0</b></p><button class='btn' onclick='openMatch()'>🔄 Next Level (Harder)</button><button class='btn2' onclick='openSciFi()'>⬅ Sci-Fi</button>"}
var matchScore=0;function matchTap(el){matchScore+=10;var s=document.getElementById("matchScore");if(s)s.innerText=matchScore;el.innerText=["🍬","🍭","🍓","🍇","💎","⭐"][Math.floor(Math.random()*6)];if(matchScore%30===0){myGold+=50;wins+=1;toast("🍬 Match! +50 Gold +1 Win");saveLocal();syncScore()}}
function openShop(){showPage("page-game");document.getElementById("gameTitle").innerText="🛍️ SHOP - No Repeats";renderShop()}
var SHOP=[["Toyota Corolla",34000],["Toyota Hilux",76000],["BMW M4",142000],["Lamborghini Huracan",400000],["Ferrari 488",500000],["Tesla Model 3",80000],["Mercedes C-Class",90000],["Audi A4",84000],["Range Rover",220000],["Nissan GTR",220000],["Bugatti Chiron",6000000],["Burger 1",200],["Pizza 1",300],["Cola 1",100],["Mango Juice 1",150],["Energy Drink 1",250],["Phone 1",5000],["Laptop 1",12000],["PS5 1",8000],["Jacket 1",800],["Dog 1",2000],["Cat 1",1500],["Football 1",400],["Perfume 1",900]];
function renderShop(){var h="<p>🪙 Gold: "+myGold+" | Cars = x2 Real Price | Car = +Time</p><input id='shopSearch' placeholder='🔍 Search...' oninput='renderShopList()' style='margin-bottom:10px'><div id='shopList'></div><button class='btn2' onclick='goDash()'>⬅ Back</button>";document.getElementById("gameBody").innerHTML=h;renderShopList()}
function renderShopList(){var q=(document.getElementById("shopSearch")?document.getElementById("shopSearch").value.toLowerCase():"");var h="";SHOP.forEach(function(it){if(q&&it[0].toLowerCase().indexOf(q)<0)return;var owned=myCars.indexOf(it[0])>=0;h+="<div style='padding:12px;background:rgba(255,255,255,.12);border-radius:14px;margin:6px 0;display:flex;justify-content:space-between'><span>"+it[0]+"<br><small>"+(owned?"✅ OWNED":"🪙 "+it[1]+" Gold")+"</small></span><button class='btn' style='width:auto;padding:8px 14px' onclick=\"buyItem('"+it[0].replace(/'/g,"")+"',"+it[1]+")\">"+(owned?"Owned":"Buy")+"</button></div>"});document.getElementById("shopList").innerHTML=h}
function buyItem(name,price){openPin("PIN buy "+name,function(pin){fetch("/api/buy_item",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,item:name,price:price})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.gold;if(/Toyota|BMW|Lamborghini|Ferrari|Tesla|Mercedes|Audi|Rover|Hilux|Nissan|Bugatti/.test(name)){if(myCars.indexOf(name)<0)myCars.push(name)}saveLocal();toast("✅ Bought "+name);renderShop()})})}
function openMessages(){showPage("page-messages");fetch("/api/friends?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){var h="";(d.friends||[]).forEach(function(f){h+="<div class='leadRow' onclick=\"openChat('"+f.name+"')\"><span>💚 "+f.name+"<br><small>"+f.player_id+"</small></span><span>💬</span></div>"});document.getElementById("chatFriendList").innerHTML=h||"No friends - Add by ID"})}
function addFriendById(){var dg=document.getElementById("addFriendDigits").value.replace(/[^0-9]/g,"");if(dg.length!==8){toast("8 digits");return}fetch("/api/add_friend",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,target_id:"INF-"+dg})}).then(function(){toast("✅ Friend added");openMessages()})}
function openChat(name){chatWith=name;showPage("page-chat");document.getElementById("chatWith").innerText=name;loadChat()}
function loadChat(){fetch("/api/chat_get?a="+encodeURIComponent(user.name)+"&b="+encodeURIComponent(chatWith)).then(function(r){return r.json()}).then(function(d){var h="";(d.messages||[]).forEach(function(m){h+="<div style='padding:10px;background:rgba(255,255,255,.2);border-radius:14px;margin:6px 0'>"+m.text+"</div>"});var b=document.getElementById("chatBox");b.innerHTML=h||"No messages";b.scrollTop=b.scrollHeight})}
function sendMsg(){var t=document.getElementById("msgInput").value.trim();if(!t)return;fetch("/api/chat_send",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({sender:user.name,to:chatWith,text:t})}).then(function(){document.getElementById("msgInput").value="";loadChat();playPin()})}
function openPin(desc,cb){pinCb=cb;document.getElementById("pinDesc").innerText=desc;document.getElementById("pinInput").value="";var o=document.getElementById("pinOverlay");o.classList.remove("hidden");o.style.display="flex";playPin();setTimeout(function(){document.getElementById("pinInput").focus()},100)}
function closePin(){var o=document.getElementById("pinOverlay");o.classList.add("hidden");o.style.display="none";pinCb=null}
function confirmPin(){var v=document.getElementById("pinInput").value.trim();if(!v||v.length!==4){toast("4 digits");return}var cb=pinCb;closePin();if(cb)cb(v)}
function openIdPopup(title,cb){idCb=cb;document.getElementById("idTitle").innerText=title;document.getElementById("idInput").value="";var o=document.getElementById("idOverlay");o.classList.remove("hidden");o.style.display="flex"}
function closeIdPopup(){var o=document.getElementById("idOverlay");o.classList.add("hidden");o.style.display="none";idCb=null}
function confirmIdPopup(){var v=document.getElementById("idInput").value.replace(/[^0-9]/g,"");if(v.length!==8){toast("8 digits");return}var cb=idCb;closeIdPopup();if(cb)cb("INF-"+v)}
function openReviewRequest(t){document.getElementById("reviewTitle").innerText=t==="request"?"📩 Request":"⭐ Review";showPage("page-review")}
function submitReview(){var txt=document.getElementById("reviewText").value.trim();if(!txt){toast("Type something");return}fetch("/api/review",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user?user.name:"Guest",text:txt})}).then(function(){toast("✅ Sent");document.getElementById("reviewText").value="";goDash()})}
function toggleMenu(){var m=document.getElementById("menuDrop");if(!m.classList.contains("hidden")){m.classList.add("hidden");return}var it="";it+="<div style='padding:10px;cursor:pointer;border-bottom:1px solid #333' onclick=\"openMyProfile();toggleMenu()\">👤 My Profile</div>";it+="<div style='padding:10px;cursor:pointer;border-bottom:1px solid #333' onclick=\"openBank();toggleMenu()\">💰 Bank</div>";it+="<div style='padding:10px;cursor:pointer;border-bottom:1px solid #333' onclick=\"openShop();toggleMenu()\">🛍️ Shop</div>";it+="<div style='padding:10px;cursor:pointer;border-bottom:1px solid #333' onclick=\"openLottery();toggleMenu()\">🎰 Lottery</div>";it+="<div style='padding:10px;cursor:pointer;border-bottom:1px solid #333' onclick=\"openEconomy();toggleMenu()\">💰 Economy (Dominic)</div>";it+="<div style='padding:10px;cursor:pointer;border-bottom:1px solid #333' onclick=\"openAnn();toggleMenu()\">📢 Announcement (Dominic)</div>";it+="<div style='padding:10px;cursor:pointer;border-bottom:1px solid #333' onclick=\"openReviewRequest('review');toggleMenu()\">⭐ Review</div>";it+="<div style='padding:10px;cursor:pointer' onclick=\"doLogout();toggleMenu()\">🚪 Logout</div>";m.innerHTML=it;m.classList.remove("hidden")}
document.addEventListener("click",function(e){var m=document.getElementById("menuDrop");var b=document.getElementById("menuBtn");if(m&&!m.classList.contains("hidden")&&b&&!b.contains(e.target)&&!m.contains(e.target))m.classList.add("hidden")});
document.addEventListener("DOMContentLoaded",function(){var mb=document.getElementById("menuBtn");if(mb)mb.onclick=function(e){e.stopPropagation();toggleMenu()};var bf=document.getElementById("backFab");if(bf)bf.onclick=function(){goBack()};var mf=document.getElementById("msgFab");if(mf)mf.onclick=function(){openMessages()};document.addEventListener("keydown",function(e){if(e.key==="Enter"&&currentPage==="page-home")enterClicked()});user=null;loggedIn=false;hasEntered=false;showPage("page-home");setInterval(function(){if(loggedIn)fetch("/api/player?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){if(!d||!d.notifs)return;var n=d.notifs.slice().reverse()[0];if(n&&n.type==="loan_date_change"){var lid=n.loan_id;if(confirm("Loan date changed to "+n.new_date+" - Approve? NO = refunded")){fetch("/api/loan_confirm",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,loan_id:lid,approve:true})})}else{fetch("/api/loan_confirm",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,loan_id:lid,approve:false})})}}if(n&&n.type==="loan_request"&&isDom()){toast("🏦 NEW LOAN! Check Economy")}}) },15000)});
</script></body></html>"""
if __name__=="__main__":
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port) 
