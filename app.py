import os,json,random,shutil,sqlite3,time
from datetime import datetime,timedelta
from flask import Flask,request,jsonify,make_response
app=Flask(__name__)
DB="infinity.db";B1="infinity_backup1.db";B2="infinity_backup2.db";ALL=[DB,B1,B2]
DE={"gold":100000000,"gems":100000,"bank_gold":50000000,"bank_gems":50000000,"lottery":0,"crypto":{"BTC":85000,"ETH":4200,"DOGE":2}}
DATA={"players":{},"loans":[],"requests":[],"announcements":[],"reviews":[],"chats":{},"game_on":True,"friend_requests":[],"economy":dict(DE)}
def dc(p):
 c=sqlite3.connect(p);c.execute("CREATE TABLE IF NOT EXISTS kv(k TEXT PRIMARY KEY,v TEXT)");return c
def dr(p):
 try:
  if not os.path.exists(p):return None
  c=dc(p);r=c.execute("SELECT v FROM kv WHERE k='DATA'").fetchone();c.close();return json.loads(r[0]) if r else None
 except Exception:return None
def dw():
 try:
  c=dc(DB);c.execute("INSERT OR REPLACE INTO kv VALUES('DATA',?)",(json.dumps(DATA),));c.commit();c.close()
  for b in [B1,B2]:
   try:shutil.copyfile(DB,b)
   except Exception:pass
 except Exception:pass
def load():
 global DATA
 f=[d for d in [dr(p) for p in ALL] if d]
 if not f:dw();return
 f.sort(key=lambda x:len(x.get("players",{})),reverse=True)
 for k in DATA:
  if k in f[0]:DATA[k]=f[0][k]
 for v in DATA["players"].values():v.setdefault("crypto",{"BTC":0,"ETH":0,"DOGE":0});v.setdefault("losses",0)
 dw()
load()
def norm(s):return str(s or "").strip().lower()
def getp(n):
 if not n:return None
 for k,v in DATA["players"].items():
  if norm(k)==norm(n):return v
 return None
def newp(n,pw):
 pid="INF-"+str(random.randint(10000000,99999999));bid="BANK INF-"+str(random.randint(10000000,99999999))
 p={"name":n,"display_name":n,"password":str(pw),"player_id":pid,"bank_id":bid,"wins":0,"losses":0,"gold":0,"gems":0,"bank_gold":0,"bank_gems":0,"cars":[],"items":[],"seen_qs":[],"crypto":{"BTC":0,"ETH":0,"DOGE":0},"notifs":[],"friends":[],"active_loan":None,"last_interest":"","saved_at":int(time.time())}
 DATA["players"][n]=p;dw();return p
def cpin(v,pin):return str(pin)=="2164" if norm(v.get("name"))=="dominic" else str(pin)==str(v.get("password"))
def notify(n,t,typ="info",ex=None):
 v=getp(n)
 if not v:
  if norm(n)=="dominic":v=newp("dominic","2164")
  else:return
 x={"text":t,"type":typ,"time":datetime.now().strftime("%H:%M %d %b")}
 if ex:x.update(ex)
 v.setdefault("notifs",[]).append(x);dw()
def byid(pid):
 pid=str(pid).upper().replace("BANK ","")
 if not pid.startswith("INF-"):pid="INF-"+pid
 for v in DATA["players"].values():
  if v.get("player_id")==pid or v.get("bank_id")==pid:return v
 return None
def alo(v):
 if not v:return None
 for l in DATA["loans"]:
  if norm(l.get("from"))==norm(v["name"]) and l.get("status") in ["active","waiting_player_confirm","extended"]:return l
 return v.get("active_loan")
@app.route("/")
def home():return make_response(HOME,200,{"Content-Type":"text/html"})
@app.route("/api/switch_status")
def sws():return jsonify({"game_on":DATA.get("game_on",True)})
@app.route("/api/switch_toggle",methods=["POST"])
def swt():
 d=request.get_json() or {}
 if norm(d.get("admin"))!="dominic" or str(d.get("pin"))!="2164":return jsonify({"error":"Only Dominic"}),403
 DATA["game_on"]=bool(d.get("on",True));dw();return jsonify({"ok":True,"game_on":DATA["game_on"]})
@app.route("/api/player")
def apl():
 v=getp(request.args.get("name",""))
 if not v:return jsonify({"found":False})
 if request.args.get("password") and str(request.args.get("password"))!=str(v.get("password")):return jsonify({"found":True,"password_ok":False})
 return jsonify({"found":True,"password_ok":True,"name":v["name"],"player_id":v.get("player_id"),"bank_id":v.get("bank_id"),"wins":v.get("wins",0),"losses":v.get("losses",0),"gold":v.get("gold",0),"gems":v.get("gems",0),"bank_gold":v.get("bank_gold",0),"bank_gems":v.get("bank_gems",0),"cars":v.get("cars",[]),"items":v.get("items",[]),"seen_qs":v.get("seen_qs",[]),"crypto":v.get("crypto",{"BTC":0,"ETH":0,"DOGE":0}),"notifs":v.get("notifs",[])[-30:],"friends":v.get("friends",[]),"friend_requests":[r for r in DATA.get("friend_requests",[]) if norm(r.get("to"))==norm(v["name"]) and r.get("status")=="pending"],"active_loan":alo(v)})
@app.route("/api/restore",methods=["POST"])
def ar():
 d=request.get_json() or {};n=d.get("name","");pw=str(d.get("password",""));v=getp(n)
 if v:return jsonify({"found":True,"player":v}) if str(v.get("password"))==pw else (jsonify({"error":"Wrong password"}),403)
 v=newp(n,pw);v["wins"]=int(d.get("wins",0) or 0);v["losses"]=int(d.get("losses",0) or 0);v["gold"]=int(d.get("gold",0) or 0);v["gems"]=int(d.get("gems",0) or 0);v["cars"]=d.get("cars",[]);v["items"]=d.get("items",[])
 if d.get("player_id"):v["player_id"]=d.get("player_id")
 if d.get("bank_id"):v["bank_id"]=d.get("bank_id")
 dw();return jsonify({"found":True,"player":v})
@app.route("/api/score",methods=["POST"])
def asc():
 d=request.get_json() or {};v=getp(d.get("name"))
 if not v:v=newp(d.get("name","Player"),d.get("password","0000"))
 v["wins"]=max(v.get("wins",0),int(d.get("wins",0)));v["losses"]=max(v.get("losses",0),int(d.get("losses",0)));v["gold"]=max(v.get("gold",0),int(d.get("gold",0)));v["gems"]=max(v.get("gems",0),int(d.get("gems",0)))
 if d.get("cars") and len(d.get("cars",[]))>len(v.get("cars",[])):v["cars"]=d.get("cars")
 if d.get("seen_qs"):v["seen_qs"]=list(set(v.get("seen_qs",[]))|set(d.get("seen_qs",[])))
 dw();return jsonify({"ok":True})
@app.route("/api/leaderboard")
def alb():
 m=request.args.get("mode","pvp");ps=list(DATA["players"].values())
 if m=="gold":ps.sort(key=lambda x:x.get("gold",0),reverse=True)
 elif m=="gems":ps.sort(key=lambda x:x.get("gems",0),reverse=True)
 else:ps.sort(key=lambda x:(x.get("wins",0)-x.get("losses",0)),reverse=True)
 return jsonify({"players":[{"name":p["name"],"player_id":p.get("player_id"),"wins":p.get("wins",0),"losses":p.get("losses",0),"gold":p.get("gold",0),"gems":p.get("gems",0),"rank":i+1,"active_loan":bool(alo(p))} for i,p in enumerate(ps[:50])]})
@app.route("/api/transfer",methods=["POST"])
def atr():
 d=request.get_json() or {};v=getp(d.get("sender"))
 if not v or not cpin(v,d.get("pin","")):return jsonify({"error":"Wrong PIN"}),403
 r=byid(d.get("receiver_id",""));amt=int(d.get("amount",0))
 if not r:return jsonify({"error":"Receiver not found"}),404
 if amt<=0 or v.get("gold",0)<amt:return jsonify({"error":"Not enough Gold"}),400
 v["gold"]-=amt;r["gold"]=r.get("gold",0)+amt;notify(r["name"],"💸 "+v["name"]+" sent you "+str(amt)+" Gold");dw();return jsonify({"ok":True,"sender_gold":v["gold"]})
@app.route("/api/bank_action",methods=["POST"])
def aba():
 d=request.get_json() or {};v=getp(d.get("name"))
 if not v or not cpin(v,d.get("pin","")):return jsonify({"error":"Wrong PIN"}),403
 amt=int(d.get("amount",0));cur=d.get("currency","Gold");g=(cur=="Gold")
 if d.get("action")=="deposit":
  if g:
   if v.get("gold",0)<amt:return jsonify({"error":"Not enough"}),400
   v["gold"]-=amt;v["bank_gold"]=v.get("bank_gold",0)+amt
  else:
   if v.get("gems",0)<amt:return jsonify({"error":"Not enough"}),400
   v["gems"]-=amt;v["bank_gems"]=v.get("bank_gems",0)+amt
 else:
  if g:
   if v.get("bank_gold",0)<amt:return jsonify({"error":"Not enough in Bank"}),400
   v["bank_gold"]-=amt;v["gold"]=v.get("gold",0)+amt
  else:
   if v.get("bank_gems",0)<amt:return jsonify({"error":"Not enough in Bank"}),400
   v["bank_gems"]-=amt;v["gems"]=v.get("gems",0)+amt
 dw();return jsonify({"ok":True,"gold":v["gold"],"gems":v["gems"],"bank_gold":v.get("bank_gold",0),"bank_gems":v.get("bank_gems",0)})
@app.route("/api/bank_interest",methods=["POST"])
def abi():
 d=request.get_json() or {};v=getp(d.get("name"))
 if not v or not cpin(v,d.get("pin","")):return jsonify({"error":"Wrong PIN"}),403
 mo=datetime.now().strftime("%Y-%m")
 if v.get("last_interest")==mo:return jsonify({"error":"Already claimed this month"}),400
 bg=int(v.get("bank_gold",0)*0.10);bm=int(v.get("bank_gems",0)*0.10);v["bank_gold"]=v.get("bank_gold",0)+bg;v["bank_gems"]=v.get("bank_gems",0)+bm;v["last_interest"]=mo;notify(v["name"],"🎁 Interest +10%: +"+str(bg)+" Gold, +"+str(bm)+" Gems");dw();return jsonify({"ok":True})
@app.route("/api/exchange",methods=["POST"])
def aex():
 d=request.get_json() or {};v=getp(d.get("name"));amt=int(d.get("amount",0));dr=d.get("direction","gold_to_gem")
 if not v or not cpin(v,d.get("pin","")):return jsonify({"error":"Wrong PIN"}),403
 if dr=="gold_to_gem":
  g=amt//100
  if g<1 or v.get("gold",0)<g*100:return jsonify({"error":"Need 100 Gold = 1 Gem"}),400
  v["gold"]-=g*100;v["gems"]=v.get("gems",0)+g
 else:
  if v.get("gems",0)<amt:return jsonify({"error":"Not enough Gems"}),400
  v["gems"]-=amt;v["gold"]=v.get("gold",0)+amt*100
 dw();return jsonify({"ok":True,"gold":v["gold"],"gems":v["gems"]})
@app.route("/api/crypto",methods=["GET"])
def acg():
 e=DATA["economy"].get("crypto",{"BTC":85000,"ETH":4200,"DOGE":2})
 for k in e:e[k]=max(1,round(e[k]*(1+random.uniform(-0.03,0.03)),2))
 dw();v=getp(request.args.get("name",""));return jsonify({"prices":e,"holdings":v.get("crypto",{"BTC":0,"ETH":0,"DOGE":0}) if v else {"BTC":0,"ETH":0,"DOGE":0},"gold":v.get("gold",0) if v else 0})
@app.route("/api/crypto_trade",methods=["POST"])
def act():
 d=request.get_json() or {};v=getp(d.get("name"))
 if not v or not cpin(v,d.get("pin","")):return jsonify({"error":"Wrong PIN"}),403
 coin=d.get("coin","BTC");amt=float(d.get("amount",0));a2=d.get("action","buy");pr=float(DATA["economy"].get("crypto",{"BTC":85000,"ETH":4200,"DOGE":2}).get(coin,0))
 if pr<=0 or amt<=0:return jsonify({"error":"Bad amount"}),400
 v.setdefault("crypto",{"BTC":0,"ETH":0,"DOGE":0})
 if a2=="buy":
  cost=amt*pr
  if v.get("gold",0)<cost:return jsonify({"error":"Not enough Gold. Need "+str(int(cost))}),400
  v["gold"]-=int(cost);v["crypto"][coin]=round(float(v["crypto"].get(coin,0))+amt,6)
 else:
  if float(v["crypto"].get(coin,0))<amt:return jsonify({"error":"Not enough "+coin}),400
  v["crypto"][coin]=round(float(v["crypto"].get(coin,0))-amt,6);v["gold"]+=int(amt*pr)
 dw();return jsonify({"ok":True,"gold":v["gold"],"holdings":v["crypto"]})
@app.route("/api/loan_apply",methods=["POST"])
def ala():
 d=request.get_json() or {};v=getp(d.get("name"));amt=int(d.get("amount",0))
 if not v or not cpin(v,d.get("pin","")):return jsonify({"error":"Wrong PIN"}),403
 if alo(v):return jsonify({"error":"You already have ACTIVE loan. Pay it first!"}),400
 lid="LN-"+str(random.randint(10000000,99999999));loan={"id":lid,"from":v["display_name"],"amount":amt,"currency":d.get("currency","Gold"),"repay_date":d.get("repay_date",""),"status":"pending_dominic","new_date":"","dominic_new_date":"","extended":False}
 DATA["loans"].append(loan);notify("dominic","LOAN: "+v["display_name"]+" wants "+str(amt)+" "+loan["currency"],"loan_request",{"loan_id":lid,"amount":amt,"currency":loan["currency"],"repay_date":loan["repay_date"],"from":v["display_name"]});dw();return jsonify({"ok":True})
@app.route("/api/loan_dominic",methods=["POST"])
def ald():
 d=request.get_json() or {}
 if norm(d.get("admin"))!="dominic" or str(d.get("pin"))!="2164":return jsonify({"error":"Only Dominic"}),403
 for l in list(DATA["loans"]):
  if l["id"]==d.get("loan_id"):
   dom=getp("dominic")
   if not d.get("approve"):
    if dom:dom["notifs"]=[n for n in dom.get("notifs",[]) if not (n.get("type")=="loan_request" and n.get("loan_id")==l["id"])]
    notify(l["from"],"Loan DECLINED by Dominic");DATA["loans"]=[x for x in DATA["loans"] if x["id"]!=l["id"]];dw();return jsonify({"ok":True})
   if dom:dom["notifs"]=[n for n in dom.get("notifs",[]) if not (n.get("type")=="loan_request" and n.get("loan_id")==l["id"])]
   l["new_date"]=d.get("new_date") or l["repay_date"];l["dominic_new_date"]=l["new_date"];l["status"]="waiting_player_confirm";notify(l["from"],"Dominic APPROVED your loan! Date: "+l["new_date"],"loan_date_change",{"loan_id":l["id"],"new_date":l["new_date"]});dw();return jsonify({"ok":True})
 return jsonify({"error":"Not found"}),404
@app.route("/api/loan_player_confirm",methods=["POST"])
def alp():
 d=request.get_json() or {};v=getp(d.get("name"))
 if not v:return jsonify({"error":"No player"}),404
 for l in list(DATA["loans"]):
  if l["id"]==d.get("loan_id"):
   if d.get("approve"):
    l["status"]="active";l["repay_date"]=l.get("dominic_new_date") or l["repay_date"];v["active_loan"]=l
    if l["currency"]=="Gold":v["gold"]=v.get("gold",0)+l["amount"]
    else:v["gems"]=v.get("gems",0)+l["amount"]
    v["notifs"]=[n for n in v.get("notifs",[]) if not (n.get("type")=="loan_date_change" and n.get("loan_id")==l["id"])];notify("dominic",v["name"]+" received Loan "+str(l["amount"]))
   else:
    v["notifs"]=[n for n in v.get("notifs",[]) if not (n.get("type")=="loan_date_change" and n.get("loan_id")==l["id"])];DATA["loans"]=[x for x in DATA["loans"] if x["id"]!=l["id"]];notify("dominic",v["name"]+" declined Loan")
   dw();return jsonify({"ok":True})
 return jsonify({"error":"Not found"}),404
@app.route("/api/loan_repay",methods=["POST"])
def alr():
 d=request.get_json() or {};v=getp(d.get("name"))
 if not v or not cpin(v,d.get("pin","")):return jsonify({"error":"Wrong PIN"}),403
 loan=None
 for l in DATA["loans"]:
  if l["id"]==d.get("loan_id") and norm(l.get("from"))==norm(v["name"]):loan=l;break
 if not loan or loan.get("status") not in ["active","extended"]:return jsonify({"error":"No active loan"}),404
 amt=loan["amount"];cur=loan["currency"]
 if cur=="Gold":
  if v.get("gold",0)<amt:return jsonify({"error":"Not enough Gold"}),400
  v["gold"]-=amt
 else:
  if v.get("gems",0)<amt:return jsonify({"error":"Not enough Gems"}),400
  v["gems"]-=amt
 DATA["loans"]=[x for x in DATA["loans"] if x["id"]!=loan["id"]];v["active_loan"]=None;notify(v["name"],"✅ Loan PAID: "+str(amt)+" "+cur);dw();return jsonify({"ok":True})
@app.route("/api/loan_due",methods=["POST"])
def aldu():
 d=request.get_json() or {};v=getp(d.get("name"))
 if not v:return jsonify({"error":"No player"}),404
 loan=None
 for l in DATA["loans"]:
  if l["id"]==d.get("loan_id") and norm(l.get("from"))==norm(v["name"]):loan=l;break
 if not loan:return jsonify({"error":"No loan"}),404
 if d.get("action","extend")=="extend" and not loan.get("extended"):
  try:old=datetime.strptime(loan["repay_date"],"%Y-%m-%d");loan["repay_date"]=(old+timedelta(days=7)).strftime("%Y-%m-%d")
  except Exception:pass
  loan["extended"]=True;loan["status"]="extended";v["active_loan"]=loan;dw();return jsonify({"ok":True,"new_date":loan["repay_date"]})
 amt=loan["amount"];cur=loan["currency"];wt=0
 if cur=="Gold":
  h=v.get("gold",0)
  if h>=amt:v["gold"]-=amt
  else:v["gold"]=0;wt=((amt-h)+999)//1000;v["wins"]=max(0,v.get("wins",0)-wt)
 else:
  h=v.get("gems",0)
  if h>=amt:v["gems"]-=amt
  else:v["gems"]=0;wt=((amt-h)+9)//10;v["wins"]=max(0,v.get("wins",0)-wt)
 DATA["loans"]=[x for x in DATA["loans"] if x["id"]!=loan["id"]];v["active_loan"]=None;dw();return jsonify({"ok":True,"wins_taken":wt})
@app.route("/api/request_money",methods=["POST"])
def arq():
 d=request.get_json() or {};v=getp(d.get("name"))
 if not v:return jsonify({"error":"No player"}),404
 rid="RQ-"+str(random.randint(10000000,99999999));amt=int(d.get("amount") or 0);r={"id":rid,"from":v["display_name"],"amount":amt,"currency":d.get("currency","Gold"),"message":d.get("message","")};DATA["requests"].append(r);notify("dominic","🔒 SECRET: "+v["display_name"]+" wants "+str(amt)+" "+r["currency"],"request",{"request_id":rid,"amount":amt,"currency":r["currency"]});dw();return jsonify({"ok":True})
@app.route("/api/request_approve",methods=["POST"])
def arqa():
 d=request.get_json() or {}
 if norm(d.get("admin"))!="dominic" or str(d.get("pin"))!="2164":return jsonify({"error":"Only Dominic"}),403
 for r in DATA["requests"]:
  if r["id"]==d.get("request_id"):
   v=getp(r["from"])
   if v:
    if d.get("currency","Gold")=="Gold":v["gold"]=v.get("gold",0)+int(d.get("amount",0))
    else:v["gems"]=v.get("gems",0)+int(d.get("amount",0))
    notify(v["name"],"🔒 Secret Approved: +"+str(d.get("amount",0))+" "+d.get("currency","Gold"));dom=getp("dominic")
    if dom:dom["notifs"]=[n for n in dom.get("notifs",[]) if not (n.get("type")=="request" and n.get("request_id")==r["id"])]
   DATA["requests"]=[x for x in DATA["requests"] if x["id"]!=r["id"]];dw();return jsonify({"ok":True})
 return jsonify({"error":"Not found"}),404
@app.route("/api/buy_item",methods=["POST"])
def aby():
 d=request.get_json() or {};v=getp(d.get("name"))
 if not v or not cpin(v,d.get("pin","")):return jsonify({"error":"Wrong PIN"}),403
 it=d.get("item","");pr=int(d.get("price",0))
 if v.get("gold",0)<pr:return jsonify({"error":"Not enough Gold"}),400
 if it in v.get("cars",[]) or it in v.get("items",[]):return jsonify({"error":"Already owned"}),400
 v["gold"]-=pr
 if any(x in it for x in ["Toyota","BMW","Lamborghini","Ferrari","Tesla","Mercedes","Audi","Rover","Hilux","Nissan","Bugatti"]):v.setdefault("cars",[]).append(it)
 else:v.setdefault("items",[]).append(it)
 dw();return jsonify({"ok":True,"gold":v["gold"]})
@app.route("/api/consume",methods=["POST"])
def aco():
 d=request.get_json() or {};v=getp(d.get("name"))
 if not v or not cpin(v,d.get("pin","")):return jsonify({"error":"Wrong PIN"}),403
 p=d.get("product","")
 if p in v.get("items",[]):v["items"].remove(p)
 v["wins"]=v.get("wins",0)+int(d.get("bonus",20));dw();return jsonify({"ok":True,"wins":v["wins"]})
@app.route("/api/lottery",methods=["POST"])
def alo2():
 d=request.get_json() or {};v=getp(d.get("name"))
 if not v or not cpin(v,d.get("pin","")):return jsonify({"error":"Wrong PIN"}),403
 bet=int(d.get("bet",0));cur=d.get("currency","Gold")
 if bet<=0:return jsonify({"error":"Bet > 0"}),400
 if cur=="Gold":
  if v.get("gold",0)<bet:return jsonify({"error":"Not enough Gold"}),400
  v["gold"]-=bet
 else:
  if v.get("gems",0)<bet:return jsonify({"error":"Not enough Gems"}),400
  v["gems"]-=bet
 win=random.random()<0.35
 if win:
  pr=bet*2
  if cur=="Gold":v["gold"]+=pr
  else:v["gems"]+=pr
  res={"win":True,"prize":pr}
 else:res={"win":False,"prize":0};DATA["economy"]["lottery"]=DATA["economy"].get("lottery",0)+bet
 dw();return jsonify({"ok":True,"gold":v["gold"],"gems":v["gems"],"result":res})
@app.route("/api/announce",methods=["POST"])
def aan():
 d=request.get_json() or {}
 if norm(d.get("admin"))!="dominic" or str(d.get("pin"))!="2164":return jsonify({"error":"Only Dominic"}),403
 DATA["announcements"].append({"text":d.get("text",""),"time":datetime.now().strftime("%H:%M")})
 for v in DATA["players"].values():v.setdefault("notifs",[]).append({"text":"📢 "+d.get("text",""),"type":"announce","time":datetime.now().strftime("%H:%M")})
 dw();return jsonify({"ok":True})
@app.route("/api/economy")
def aeco():
 if norm(request.args.get("name"))!="dominic" or str(request.args.get("password"))!="2164":return jsonify({"error":"Only Dominic"}),403
 return jsonify({"economy":DATA["economy"],"requests":DATA["requests"],"loans":[x for x in DATA["loans"] if x.get("status")=="pending_dominic"],"is_negative":DATA["economy"].get("gold",0)<0})
@app.route("/api/emergency",methods=["POST"])
def aem():
 d=request.get_json() or {}
 if norm(d.get("name"))!="dominic" or str(d.get("pin"))!="2164":return jsonify({"error":"Only Dominic"}),403
 if DATA["economy"].get("gold",0)>=0:return jsonify({"error":"Not negative - Locked"}),400
 DATA["economy"].update({"gold":100000000,"gems":100000});v=getp("dominic") or newp("dominic","2164");v["gold"]=v.get("gold",0)+500000000000;dw();return jsonify({"ok":True})
@app.route("/api/review",methods=["POST"])
def arv():
 d=request.get_json() or {};DATA["reviews"].append({"name":d.get("name"),"type":d.get("type"),"text":d.get("text")});dw();return jsonify({"ok":True})
@app.route("/api/friends")
def afr():
 v=getp(request.args.get("name",""))
 if not v:return jsonify({"friends":[],"requests":[]})
 return jsonify({"friends":[{"name":getp(fn)["name"],"player_id":getp(fn).get("player_id")} for fn in v.get("friends",[]) if getp(fn)],"requests":[r for r in DATA.get("friend_requests",[]) if norm(r.get("to"))==norm(v["name"]) and r.get("status")=="pending"]})
@app.route("/api/friend_request",methods=["POST"])
def afrq():
 d=request.get_json() or {};v=getp(d.get("name"));t=byid(d.get("target_id",""))
 if not v or not t:return jsonify({"error":"Not found"}),404
 if norm(t["name"])==norm(v["name"]):return jsonify({"error":"Cannot add yourself"}),400
 if t["name"] in v.get("friends",[]):return jsonify({"error":"Already friends"}),400
 DATA.setdefault("friend_requests",[]).append({"id":"FR-"+str(random.randint(10000000,99999999)),"from":v["display_name"],"to":t["display_name"],"status":"pending"});notify(t["name"],"👥 Friend Request from "+v["display_name"],"friend_request");dw();return jsonify({"ok":True})
@app.route("/api/friend_respond",methods=["POST"])
def afrp():
 d=request.get_json() or {};v=getp(d.get("name"))
 if not v:return jsonify({"error":"No player"}),404
 for r in DATA.get("friend_requests",[]):
  if r["id"]==d.get("request_id") and norm(r.get("to"))==norm(v["name"]):
   if d.get("accept"):
    r["status"]="accepted";f=getp(r["from"])
    if f and f["name"] not in v.get("friends",[]):v.setdefault("friends",[]).append(f["name"])
    if f and v["name"] not in f.get("friends",[]):f.setdefault("friends",[]).append(v["name"])
    notify(r["from"],"✅ "+v["display_name"]+" ACCEPTED your Friend Request!")
   else:r["status"]="declined";notify(r["from"],"❌ "+v["display_name"]+" declined Friend Request")
   dw();return jsonify({"ok":True})
 return jsonify({"error":"Not found"}),404
@app.route("/api/chat_send",methods=["POST"])
def acs():
 d=request.get_json() or {};k="|".join(sorted([norm(d.get("sender","")),norm(d.get("to",""))]));DATA["chats"].setdefault(k,[]).append({"from":d.get("sender",""),"text":d.get("text","")});dw();return jsonify({"ok":True})
@app.route("/api/chat_get")
def acg2():
 k="|".join(sorted([norm(request.args.get("a","")),norm(request.args.get("b",""))]));return jsonify({"messages":DATA["chats"].get(k,[])})

HOME=r"""<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>INFINITY BOT v40</title><link href="https://fonts.googleapis.com/css2?family=Great+Vibes&family=Poppins:wght@400;700;900&display=swap" rel="stylesheet"><style>*{box-sizing:border-box}body{margin:0;font-family:Poppins,Arial;color:#fff;background:radial-gradient(circle at 50% 20%,#3a0a5e,#12002b 70%);min-height:100vh}.cursive{font-family:'Great Vibes',cursive}.topbar{display:flex;justify-content:space-between;padding:8px 14px}.center{min-height:82vh;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:20px}.enterBtn{margin-top:18px;padding:16px 70px;font-family:'Great Vibes',cursive;font-size:48px;border:none;border-radius:60px;background:linear-gradient(90deg,#ff006e,#ffd700,#00e5ff);cursor:pointer}.card{background:rgba(255,255,255,.08);border:2px solid rgba(255,255,255,.35);border-radius:26px;padding:20px;margin:14px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.box{background:linear-gradient(160deg,rgba(255,255,255,.18),rgba(0,0,0,.4));border:2px solid #fff;border-radius:24px;padding:22px 10px;text-align:center;cursor:pointer}.box span{font-size:38px;display:block}button{cursor:pointer}.btn{width:100%;padding:14px;border:none;border-radius:25px;font-weight:900;background:#ffd700;margin:6px 0}.btn2{width:100%;padding:13px;border-radius:25px;border:2px solid #00e5ff;background:transparent;color:#00e5ff;font-weight:900;margin:6px 0}.opt{width:100%;padding:13px;margin:7px 0;border-radius:16px;border:2px solid #fff;background:rgba(0,0,0,.5);color:#fff;font-weight:700;cursor:pointer;text-align:left}input,select,textarea{width:100%;padding:14px;border-radius:14px;border:2px solid #ffd700;margin:8px 0;font-size:16px;background:#fff;color:#000}.hidden{display:none!important}.leadRow{display:flex;justify-content:space-between;padding:10px 12px;background:rgba(0,0,0,.45);border-radius:14px;margin:6px 0;cursor:pointer}.toast{position:fixed;top:70px;left:50%;transform:translateX(-50%);background:#fff;color:#000;padding:12px 18px;border-radius:20px;font-weight:700;z-index:999;max-width:90%;text-align:center}.ov{position:fixed;inset:0;background:rgba(0,0,0,.75);display:flex;align-items:center;justify-content:center;padding:16px;z-index:500}.pop{background:linear-gradient(160deg,#2b005e,#12002b);border:3px solid #ffd700;border-radius:28px;padding:22px 18px;max-width:420px;width:100%;text-align:center}.choiceRow{display:flex;gap:12px;margin-top:16px}.choiceBox{flex:1;padding:18px 8px;border-radius:20px;cursor:pointer;font-weight:900;border:3px solid #fff}.choiceNo{background:#ff2222;color:#fff}.choiceYes{background:#00cc44;color:#000}.bottomNav{position:fixed;bottom:0;left:0;right:0;background:rgba(0,0,0,.85);border-top:2px solid #ffd700;display:flex;justify-content:space-around;padding:10px 0 14px;z-index:200}.bottomNav div{font-size:28px;cursor:pointer;text-align:center}.bottomNav small{display:block;font-size:10px;color:#ffd700}.walletCard{background:linear-gradient(135deg,#ffd700,#ff006e);color:#000;border-radius:24px;padding:18px;text-align:center}.bigBankBox{padding:22px 10px;border-radius:24px;border:2px solid #fff;text-align:center;cursor:pointer;background:linear-gradient(160deg,rgba(255,255,255,.18),rgba(0,0,0,.4))}.loanGreen{border:4px solid #00ff88!important;background:linear-gradient(160deg,#00cc44,#00ff88)!important;color:#000!important}.idPrefix{display:flex;align-items:center;background:#fff;border-radius:14px;border:2px solid #ffd700;padding:0 10px;margin:8px 0}.idPrefix b{color:#000}.idPrefix input{border:none;flex:1;margin:0}.timerBar{height:14px;background:#333;border-radius:99px;overflow:hidden}.timerFill{height:100%;background:#00ff88;transition:width 1s linear}.tabBox{flex:1;padding:12px 4px;border-radius:16px;background:rgba(255,255,255,.15);border:2px solid #ffd700;text-align:center;cursor:pointer;font-weight:900;font-size:13px}.tabBox.active{background:#ffd700;color:#000}.catTab{padding:8px 4px;border-radius:12px;background:rgba(255,255,255,.12);border:1px solid #ffd700;text-align:center;cursor:pointer;font-size:11px;font-weight:900}.catTab.active{background:#ffd700;color:#000}#menuDrop{position:fixed!important;top:108px!important;right:8px!important;width:210px!important;background:#1a1a2e;border:2px solid #ffd700;border-radius:14px;padding:6px;z-index:900}#menuDrop div{padding:9px!important;font-size:13px!important;cursor:pointer}#page-welcome{z-index:2000!important}button,.btn,.btn2,.opt,.box,.leadRow,.tabBox,.catTab,.bigBankBox,.choiceBox{pointer-events:auto!important;cursor:pointer!important}</style></head><body>
<div id="frozenOverlay" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.92);z-index:3000;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:20px"><div style="font-size:80px">❄️</div><h1>GAME PAUSED</h1><p style="color:#ffd700;font-weight:900">SWITCHED OFF BY DOMINIC</p><div id="frozenDominicBox" style="display:none;margin-top:20px;background:#1a1a2e;border:2px solid #ffd700;border-radius:20px;padding:16px;width:100%;max-width:320px"><p>👑 Dominic Only</p><input id="frozenPin" type="password" inputmode="numeric" maxlength="4" placeholder="2164"><button class="btn" type="button" onclick="dominicUnfreeze()">🔓 TURN GAME ON</button></div></div>
<div id="loanDatePopup" class="ov hidden" style="display:none;z-index:1200"><div class="pop"><div style="font-size:50px">📅</div><h2>Dominic Changed Date</h2><p id="loanDatePopupText"></p><input id="loanDateInput" type="date"><div class="choiceRow"><div class="choiceBox choiceNo" onclick="loanDateRespond(false)">❌ No</div><div class="choiceBox choiceYes" onclick="loanDateRespond(true)">✅ Yes</div></div></div></div>
<div id="loanDueOverlay" class="ov hidden" style="display:none;z-index:1100"><div class="pop"><div style="font-size:50px">⏰</div><h2>LOAN DUE!</h2><p id="loanDueText"></p><div class="choiceRow"><div class="choiceBox choiceNo" onclick="loanDueAction('extend')">⏳ +7 Days</div><div class="choiceBox choiceYes" onclick="loanDueAction('collect')">💰 Pay Now</div></div></div></div>
<div id="menuDrop" class="hidden"></div><div id="toast" class="toast hidden"></div>
<div id="pinOverlay" class="ov hidden" style="display:none;z-index:900"><div class="pop"><h2>Enter PIN</h2><p id="pinDesc"></p><input id="pinInput" placeholder="...." maxlength="4" inputmode="numeric" type="password" style="font-size:28px;text-align:center;letter-spacing:12px"><div class="choiceRow"><div class="choiceBox choiceNo" onclick="closePin()">❌ Cancel</div><div class="choiceBox choiceYes" onclick="confirmPin()">✅ Confirm</div></div></div></div>
<div id="announceOverlay" class="ov hidden" style="display:none;z-index:960"><div class="pop"><h2>📢 Announcement</h2><textarea id="annText" style="height:100px"></textarea><button class="btn" type="button" onclick="sendAnnounce()">📢 Announce</button><button class="btn2" type="button" onclick="closeAnnounce()">Cancel</button></div></div>
<div id="secretOverlay" class="ov hidden" style="display:none;z-index:920"><div class="pop"><h2>🔒 Secret</h2><input id="reqMsg" type="password" placeholder="Secret message"><input id="reqAmt" type="password" inputmode="numeric" placeholder="Amount"><select id="reqCur"><option>Gold</option><option>Gems</option></select><div class="choiceRow"><div class="choiceBox choiceNo" onclick="closeSecret()">❌ Cancel</div><div class="choiceBox choiceYes" onclick="sendMoneyRequest()">📩 Send</div></div></div></div>
<div id="loanOverlay" class="ov hidden" style="display:none;z-index:920"><div class="pop"><h2>🏦 Apply for Loan</h2><input id="loanAmt" type="number" placeholder="Amount"><select id="loanCur"><option>Gold</option><option>Gems</option></select><label>When to repay?</label><input id="loanDate" type="date"><div class="choiceRow"><div class="choiceBox choiceNo" onclick="closeLoan()">❌ Cancel</div><div class="choiceBox choiceYes" onclick="submitLoan()">📩 Apply</div></div></div></div>
<div id="page-welcome" class="ov hidden" style="display:none;z-index:2000"><div class="pop"><h2>Do you already have an account?</h2><div class="choiceRow"><div class="choiceBox choiceNo" onclick="welcomeChoice('no')">❌ No</div><div class="choiceBox choiceYes" onclick="welcomeChoice('yes')">✅ Yes</div></div></div></div>
<div class="topbar"><div><span id="catTime" style="font-size:12px;background:rgba(0,0,0,.55);border:1px solid #ffd700;padding:5px 9px;border-radius:20px">Loading time...</span><br><span id="catDate" style="font-size:10px;background:rgba(0,0,0,.45);padding:3px 8px;border-radius:20px">Central Africa</span><br><div style="font-weight:900">INFINITY BOT</div></div><div id="topRight" style="display:none;flex-direction:column;align-items:flex-end;gap:4px"><div style="display:flex;gap:6px"><div onclick="toggleSound()" style="width:32px;height:32px;border-radius:50%;background:rgba(0,0,0,.55);border:1px solid #ffd700;display:flex;align-items:center;justify-content:center;cursor:pointer"><span id="soundBtn">🔊</span></div><div onclick="openShop()" style="width:32px;height:32px;border-radius:50%;background:rgba(0,0,0,.55);border:1px solid #ffd700;display:flex;align-items:center;justify-content:center;cursor:pointer">🛍️</div><div onclick="openMyProfile()" style="width:32px;height:32px;border-radius:50%;background:linear-gradient(135deg,#ff006e,#ffd700);display:flex;align-items:center;justify-content:center;cursor:pointer;border:2px solid #fff">👤</div></div><div id="menuBtn" onclick="toggleMenu(event)" style="width:32px;height:32px;border-radius:50%;background:rgba(0,0,0,.55);border:1px solid #ffd700;display:flex;align-items:center;justify-content:center;cursor:pointer">⋮</div></div></div>
<div id="page-home" class="center"><div style="font-size:26px">✨ 💖 ⭐ 🌟 💫</div><div style="font-size:90px">👑</div><h1 class="cursive" style="font-size:68px;margin:5px">Infinity Bot</h1><p style="letter-spacing:3px;font-weight:900">DOMINIC MASTIRIA</p><p style="font-size:11px;color:#00ff88">DB Storage - Never Lose Account</p><button class="enterBtn" id="enterBtn" type="button" onclick="enterClicked()">Enter</button></div>
<div id="page-register" class="hidden" style="max-width:520px;margin:0 auto;padding:20px 14px"><div class="card" style="text-align:center"><h1 class="cursive" style="font-size:48px">Register</h1><div id="registerForm"><input id="regName" placeholder="Your Name" maxlength="20"><input id="regPass" placeholder="...." maxlength="4" inputmode="numeric" type="password"><button class="btn" type="button" onclick="doRegister()">📝 REGISTER</button><p>Already? <b style="color:#ffd700;cursor:pointer" onclick="showLogin()">Login</b></p></div><div id="loginForm" class="hidden"><input id="loginName" placeholder="Your Name"><input id="loginPass" placeholder="...." maxlength="4" inputmode="numeric" type="password"><button class="btn" type="button" onclick="doLogin()">🔓 LOGIN</button><p>New? <b style="color:#ffd700;cursor:pointer" onclick="showRegister()">Register</b></p></div></div></div>
<div id="page-dash" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div style="text-align:center"><h2 class="cursive" style="font-size:44px" id="welcomeText">Welcome 👑</h2><span style="padding:5px 10px;border-radius:20px;background:rgba(0,0,0,.5);border:1px solid #ffd700;font-size:12px">⭐ Rank: <b id="myRank">#-</b></span> <span style="padding:5px 10px;border-radius:20px;background:rgba(0,0,0,.5);border:1px solid #ffd700;font-size:12px">🚗 Cars: <b id="myCarsCount">0</b></span><div id="dashLoanBox" style="margin-top:10px"></div></div><div class="grid"><div class="box" onclick="openRiddles()"><span>🧩</span><b>RIDDLES</b></div><div class="box" onclick="openBible()"><span>📖</span><b>BIBLE FIGHT</b></div><div class="box" onclick="openSciFi()"><span>🚀</span><b>SCI-FI</b></div><div class="box" onclick="openMessages()"><span>💚</span><b>WHATSAPP</b></div></div><div class="card"><h3 style="text-align:center;margin:0">🏆 TOP 5 🏆</h3><div id="leaderList">Loading...</div><button class="btn2" type="button" onclick="openFullLeader()">👀 Full Leaderboard</button></div></div>
<div id="page-leader" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h3 style="text-align:center">🏆 LEADERBOARD</h3><div style="display:flex;gap:8px"><div class="tabBox" id="tabGold" onclick="setLeaderMode('gold')">🪙 Gold</div><div class="tabBox" id="tabGems" onclick="setLeaderMode('gems')">💎 Gem</div><div class="tabBox active" id="tabPvp" onclick="setLeaderMode('pvp')">⚔️ PvP (W|L)</div></div><div id="fullLeaderList" style="margin-top:10px">Loading...</div></div></div>
<div id="page-game" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 id="gameTitle" style="text-align:center">Game</h2><div id="gameBody"></div></div></div>
<div id="page-bank" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">💰 BANK</h2><div class="walletCard"><div>🏦 BANK PROFILE</div><div id="bankIDShow">Bank INF-</div><div>🪙 Bank Gold: <b id="bankGold">0</b> | 💎 <b id="bankGems">0</b></div><div>Wallet — 🪙 <span id="walletGold">0</span> | 💎 <span id="walletGems">0</span></div><button class="btn" type="button" style="background:#00cc44" onclick="claimInterest()">🎁 Claim 10% Interest (Monthly)</button></div><div style="display:flex;gap:12px;margin-top:14px"><div style="flex:1"><div class="bigBankBox" onclick="openSendPage()">💸<br><b>Send</b></div><div class="bigBankBox" style="margin-top:10px" onclick="openExchangePage()">🔄<br><b>Exchange</b></div><div class="bigBankBox" style="margin-top:10px" onclick="openWithdrawPage()">🏧<br><b>Withdraw</b></div></div><div style="flex:1"><div class="bigBankBox" onclick="openDepositPage()">💰<br><b>Deposit</b></div><div class="bigBankBox loanGreen" style="margin-top:10px" onclick="openLoan()">🏦<br><b>LOAN</b></div><div class="bigBankBox" style="margin-top:10px" onclick="openCrypto()">₿<br><b>CRYPTO</b></div><div class="bigBankBox" style="margin-top:10px" onclick="openMyProfile()">👤<br><b>My Profile</b></div></div></div></div></div>
<div id="page-send" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">💸 SEND GOLD</h2><div class="walletCard">🪙 <b id="sendPageGold">0</b> | 💎 <b id="sendPageGems">0</b><br>Your ID: <b id="sendPageMyID">INF-</b></div><div class="idPrefix"><b>INF-</b><input id="sendDigits" placeholder="12345678" inputmode="numeric" maxlength="8"></div><input id="sendAmt" type="number" placeholder="Amount"><button class="btn" type="button" onclick="doSend()">➤ SEND NOW</button></div></div>
<div id="page-withdraw" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">🏧 WITHDRAW</h2><input id="withdrawAmt" type="number" placeholder="Amount"><select id="withdrawCur"><option>Gold</option><option>Gems</option></select><button class="btn" type="button" onclick="doWithdraw()">🏧 WITHDRAW</button></div></div>
<div id="page-deposit" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">💰 DEPOSIT</h2><input id="depositAmt" type="number" placeholder="Amount"><select id="depositCur"><option>Gold</option><option>Gems</option></select><button class="btn" type="button" onclick="doDeposit()">💰 DEPOSIT</button></div></div>
<div id="page-exchange" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">🔄 EXCHANGE</h2><div class="bigBankBox" onclick="openExchange('gold_to_gem')"><b>Gold >>>> Gem</b><br><small>100 Gold = 1 Gem</small></div><div class="bigBankBox" style="margin-top:10px" onclick="openExchange('gem_to_gold')"><b>Gem >>>> Gold</b></div><div id="exchangeForm"></div></div></div>
<div id="page-crypto" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">₿ CRYPTO TRADE</h2><p style="text-align:center">🪙 Your Gold: <b id="cryptoGold">0</b></p><div id="cryptoList">Loading prices...</div></div></div>
<div id="page-profile" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card" style="text-align:center"><div style="font-size:70px">👤</div><h2 id="profName">Player</h2><p id="profIDShow">ID:INF-</p><p id="profBankID">Bank INF-</p><p>⭐ Rank: <b id="profRank">#-</b></p><p>🏆 <b id="profWins">0</b> W | <b id="profLoss">0</b> L</p><p>🪙 Gold: <b id="profGold">0</b> | 💎 Gem: <b id="profGems">0</b></p><p>₿ Crypto: <b id="profCrypto">None</b></p><p>🚗 Cars: <b id="profCars">None</b></p><div id="profLoanBox" style="background:#00ff88;color:#000;padding:12px;border-radius:14px;display:none"></div><button class="btn2" type="button" onclick="openSecret()">🔒 Secret</button></div><div class="card"><h3>👥 FRIENDS</h3><div id="profFriends">No friends yet</div><h3>📩 FRIEND REQUESTS</h3><div id="profFriendReqs">No requests</div></div><div class="card"><h3>🎒 INVENTORY</h3><div id="profInventory">No items</div><div id="consumeBox"></div></div></div>
<div id="page-other" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card" style="text-align:center"><h2 id="otherName">Player</h2><p>⭐ <b id="otherRank">#-</b></p><p>🏆 <b id="otherWins">0</b> W | <b id="otherLoss">0</b> L</p><div id="otherActions"></div></div></div>
<div id="page-notifs" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">✉️ NOTIFICATIONS</h2><div id="notifList">No notifications</div></div></div>
<div id="page-menu" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">🎮 MENU</h2><div id="menuGamesList"></div></div></div>
<div id="page-economy" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><div style="display:flex;justify-content:space-between"><h2>💰 SERVER ECONOMY</h2><button id="emergencyBtn" class="btn" type="button" style="width:auto;background:#666" disabled onclick="doEmergency()">🚨 Emergency (Locked)</button></div><p id="ecoStatus" style="font-size:12px;color:#ffd700"></p><div class="grid"><div class="walletCard">Server Gold<br><b id="ecoGold">0</b></div><div class="walletCard">Server Gem<br><b id="ecoGems">0</b></div><div class="bigBankBox">🏦 Bank Gold<br><b id="ecoBankGold">0</b></div><div class="bigBankBox">🏦 Bank Gem<br><b id="ecoBankGems">0</b></div><div class="bigBankBox">🎰 Lottery<br><b id="ecoLottery">0</b></div></div><h3>₿ CRYPTO</h3><div id="ecoCryptoBox"></div><button class="btn" type="button" onclick="openCrypto()">₿ Open Crypto</button><h3>💰 SECRET REQUESTS</h3><div id="ecoRequests">No requests</div><h3>🏦 LOANS - PENDING ONLY</h3><div id="ecoLoans">No loans</div></div></div>
<div id="page-lottery" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">🎰 LOTTERY</h2><input id="lotBet" type="number" placeholder="1000"><select id="lotCur"><option>Gold</option><option>Gems</option></select><button class="btn" type="button" onclick="playLottery()">🎰 SPIN</button><div id="lotResult" style="text-align:center"></div></div></div>
<div id="page-update" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">🔄 UPDATE - DOMINIC ONLY</h2><button class="btn" type="button" onclick="toggleGameSwitch()">🔌 SWITCH ON / OFF</button><button class="btn" type="button" onclick="openAnnounce()">📢 Announce</button></div></div>
<div id="page-review" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 id="reviewTitle">⭐ Review</h2><textarea id="reviewText" style="height:140px"></textarea><button class="btn" type="button" onclick="submitReview()">📩 SEND</button></div></div>
<div id="page-challenge" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">🎮 CHALLENGE</h2><div class="grid"><div class="box" onclick="hostPickMode('Bible Fight')"><span>📖</span><b>Bible</b></div><div class="box" onclick="hostPickMode('Riddles')"><span>🧩</span><b>Riddles</b></div><div class="box" onclick="hostPickMode('Galaxy Shooter')"><span>🌌</span><b>Galaxy</b></div><div class="box" onclick="hostPickMode('Decoding')"><span>💻</span><b>Decoding</b></div></div><button class="btn2" type="button" onclick="goDash()">❌ Decline</button></div></div>
<div id="page-messages" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h1 style="text-align:center">💚 WhatsApp</h1><div style="display:flex;gap:8px"><div class="idPrefix" style="flex:1"><b>INF-</b><input id="addFriendDigits" placeholder="Add friend ID" inputmode="numeric" maxlength="8"></div><button class="btn" type="button" style="width:auto" onclick="sendFriendRequest()">➕ Send Request</button></div><div id="chatFriendList"></div></div></div>
<div id="page-chat" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">💬 <span id="chatWith">Friend</span></h2><div id="chatBox" style="background:#1a1a2e;border-radius:20px;padding:12px;min-height:260px;max-height:360px;overflow-y:auto"></div><div style="display:flex;gap:8px;margin-top:10px"><input id="msgInput" placeholder="Message..." style="flex:1"><button class="btn" type="button" style="width:70px" onclick="sendMsg()">➤</button></div></div></div>
<div id="page-scifi" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">🚀 SCI-FI - READY 25 DEC</h2><div id="scifiList"></div></div></div>
<div id="page-shop" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">🛍️ SHOP</h2><div style="display:flex;gap:6px"><div class="catTab" onclick="setShopCat('All')">All</div><div class="catTab" onclick="setShopCat('Cars')">Cars</div><div class="catTab" onclick="setShopCat('Food')">Food</div><div class="catTab" onclick="setShopCat('Tech')">Tech</div><div class="catTab" onclick="setShopCat('Pets')">Pets</div></div><div id="shopGrid" class="shopGrid" style="margin-top:12px;display:grid;grid-template-columns:1fr 1fr;gap:10px"></div></div></div>
<div id="backFab" onclick="goBack()" style="position:fixed;left:16px;bottom:88px;width:58px;height:58px;border-radius:50%;background:#1a1a2e;display:none;align-items:center;justify-content:center;font-size:28px;color:#ffd700;border:3px solid #ffd700;cursor:pointer;z-index:150">←</div>
<div id="msgFab" onclick="openMessages()" style="position:fixed;right:16px;bottom:88px;width:62px;height:62px;border-radius:50%;background:linear-gradient(135deg,#ff006e,#ffd700,#00e5ff);display:none;align-items:center;justify-content:center;font-size:30px;border:3px solid #fff;cursor:pointer;z-index:150">💬</div>
<div id="bottomNav" class="bottomNav hidden"><div onclick="goDash()">🏡<small>Home</small></div><div onclick="openFullLeader()">🏆<small>Leader</small></div><div onclick="openBank()">💰<small>Bank</small></div><div onclick="openNotifs()">✉️<small>Notify</small></div></div>
<script>
function updateCatTime(){try{var n=new Date();var f=new Intl.DateTimeFormat("en-GB",{timeZone:"Africa/Lusaka",hour:"2-digit",minute:"2-digit",second:"2-digit",hour12:false});var d=new Intl.DateTimeFormat("en-GB",{timeZone:"Africa/Lusaka",weekday:"short",day:"2-digit",month:"short",year:"numeric"});var t=document.getElementById("catTime");if(t)t.textContent=f.format(n)+" CAT";var e=document.getElementById("catDate");if(e)e.textContent=d.format(n)+" - Central Africa"}catch(err){var t2=document.getElementById("catTime");if(t2){var x=new Date();var h=x.getUTCHours()+2;if(h>=24)h-=24;var p=function(v){return v<10?"0"+v:""+v};t2.textContent=p(h)+":"+p(x.getUTCMinutes())+":"+p(x.getUTCSeconds())+" CAT"}}}
updateCatTime();setInterval(updateCatTime,1000);
var _ac=null,soundOn=true;
function playPin(){try{if(!_ac)_ac=new (window.AudioContext||window.webkitAudioContext)();if(_ac.state==="suspended")_ac.resume();var o=_ac.createOscillator(),g=_ac.createGain();o.type="sine";o.frequency.value=880;g.gain.value=0.15;o.connect(g);g.connect(_ac.destination);o.start();o.stop(_ac.currentTime+0.15)}catch(e){}}
function hideMenu(){var d=document.getElementById("menuDrop");if(d){d.classList.add("hidden");d.style.display="none"}}
function showRegister(){var rf=document.getElementById("registerForm"),lf=document.getElementById("loginForm");if(rf){rf.classList.remove("hidden");rf.style.display="block"}if(lf){lf.classList.add("hidden");lf.style.display="none"}}
function showLogin(){var rf=document.getElementById("registerForm"),lf=document.getElementById("loginForm");if(rf){rf.classList.add("hidden");rf.style.display="none"}if(lf){lf.classList.remove("hidden");lf.style.display="block"}}
function welcomeChoice(c){playPin();var o=document.getElementById("page-welcome");if(o){o.classList.add("hidden");o.style.display="none"}var reg=document.getElementById("page-register");if(reg){reg.classList.remove("hidden");reg.style.display="block"}var home=document.getElementById("page-home");if(home){home.classList.add("hidden");home.style.display="none"}if(c==="yes")showLogin();else showRegister()}
function enterClicked(){playPin();hideMenu();var h=document.getElementById("page-home");if(h){h.classList.add("hidden");h.style.display="none"}var r=document.getElementById("page-register");if(r){r.classList.remove("hidden");r.style.display="block"}showRegister();var w=document.getElementById("page-welcome");if(w){w.classList.remove("hidden");w.style.display="flex"}}
document.addEventListener("click",function(e){var d=document.getElementById("menuDrop");var b=document.getElementById("menuBtn");if(d&&b&&!d.contains(e.target)&&e.target!==b){d.classList.add("hidden");d.style.display="none"}},true);
var user=null;try{user=JSON.parse(localStorage.getItem("inf_user")||"null")}catch(e){}
var wins=0,losses=0,myGold=0,myGems=0,myPlayerID="",myBankID="",myCars=[];try{var b2=JSON.parse(localStorage.getItem("inf_backup")||"{}");wins=parseInt(localStorage.getItem("inf_wins")||b2.wins||"0")||0;losses=parseInt(localStorage.getItem("inf_losses")||b2.losses||"0")||0;myGold=parseInt(localStorage.getItem("inf_gold")||b2.gold||"0")||0;myGems=parseInt(localStorage.getItem("inf_gems")||b2.gems||"0")||0;myPlayerID=localStorage.getItem("inf_player_id")||b2.player_id||"";myBankID=localStorage.getItem("inf_bank_id")||b2.bank_id||"";myCars=JSON.parse(localStorage.getItem("inf_cars")||JSON.stringify(b2.cars||[]))}catch(e){}
var loggedIn=false,currentPage="page-home",seenQs=[];try{seenQs=JSON.parse(localStorage.getItem("inf_seen")||"[]")}catch(e){}
var pinCb=null,leaderMode="pvp",chatWithName="",quizT=null,quizLeft=30,quizRound=[],quizIdx=0,quizScore=0,quizLoss=0,quizMode="",quizCat="",gameOn=true,shopCat="All",currentLoan=null,pendingLoanForDate=null,reviewType="review",cryptoPrices={BTC:85000,ETH:4200,DOGE:2},cryptoHold={BTC:0,ETH:0,DOGE:0};
var RB="BIBLE|Who built ark?|Noah|Moses|Abraham;BIBLE|Who defeated Goliath?|David|Samson|Saul;BIBLE|Longest chapter?|Psalm 119|Psalm 23|Genesis 1;BIBLE|Shortest chapter?|Psalm 117|Psalm 23|John 11;BIBLE|Only woman judge?|Deborah|Ruth|Esther;BIBLE|How many years Methuselah?|969 years|777 years|856 years;BIBLE|3 men in furnace?|Shadrach Meshach Abednego|Daniel Hananiah Mishael|Peter James John;BIBLE|City first Gentile church?|Antioch|Jerusalem|Rome;BIBLE|Only apostle died natural?|John|Peter|Paul;BIBLE|What does Ebenezer mean?|Stone of Help|Rock of Ages|House of God;BIBLE|How many elders?|24 elders|12 elders|7 elders;BIBLE|Only king and priest?|Melchizedek|David|Solomon;BIBLE|Father of Caleb?|Jephunneh|Nun|Aaron;BIBLE|Moses father-in-law?|Jethro|Aaron|Hobab;BIBLE|In which book vanity?|Ecclesiastes|Genesis|Psalms;BIBLE|Demon called Legion?|Legion - we are many|Beelzebub|Lucifer;BIBLE|High priest tore robes?|Caiaphas|Annas|Pilate;BIBLE|Weight Goliath spearhead?|600 shekels|100 shekels|300 shekels;BIBLE|How many times Fear not?|365 times|100 times|50 times;BIBLE|Man struck for Ark?|Uzzah|Aaron|Saul";
var NEW100="NEW|I go in dry and come out wet, longer in stronger I get|A tea bag|A sponge|A towel;NEW|More you have of me less you see|Darkness|Light|Air;NEW|Head like cat feet like cat but not cat|A kitten|A puppy|A tiger;NEW|Can be cracked never break, told never speak|A code|A joke|An egg;NEW|Fly without wings cry without eyes|A cloud|A bird|A kite;NEW|Always with you never see in mirror|Your thoughts|Your shadow|Your back;NEW|What has 4 eyes but can't see|Mississippi - 4 Is|Potato|Spider;NEW|Start with T end with T full of T|A teapot|A tent|A tablet;NEW|What has 2 banks but no money|A river|A bank|A road;NEW|Tall young short old smaller as give light|A candle|A pencil|A tree;NEW|What put in bucket to make lighter|A hole|Air|Water;NEW|No wings fly no eyes cry no mouth whisper|Wind|Ghost|Cloud;NEW|Only thing goes up when comes down|An umbrella|A balloon|A rocket;NEW|Taken from mine locked in wood used by all|Pencil lead|Gold|Coal;NEW|Has tongue never tastes|A shoe|A bell|A spoon;NEW|Only thing go through door without opening it|Light|Keyhole|Air;NEW|Face never smiles but tells everything|A clock|A mirror|A book;NEW|Full of keys can't open door, space no room|A keyboard|A piano|A map;NEW|Always in middle of sea|The letter E|Water|Fish;NEW|Not alive but can die, no lungs need air|Fire|A flame|A car;NEW|Has neck no head wears cap|A bottle|A guitar|A shirt;NEW|Both place and thing you wear|A cap|A coat|A ring;NEW|Has heart beats but no blood|A drum|A heart|A clock;NEW|Always coming never arrive always leaving never go|Tomorrow|Time|Yesterday;NEW|Only thing both hot and cold|Water|Weather|Fire;NEW|Has body no soul head no brain|A doll|A robot|A statue;NEW|Both in past and future|A dream|A memory|A hope;NEW|Both question and statement|Why|What|How;NEW|Mouth never eats river never flows|A map|A jar|A book;NEW|Both color and fruit|Orange|Apple|Banana;NEW|Tail wags but no dog|A kite|A fish|A cat;NEW|Both weapon and tool|A knife|A hammer|A gun;NEW|Bed never sleeps mouth never talks|A river|A truck|A bed;NEW|Both star and fish|A starfish|A shark|A dolphin;NEW|Ring never fits finger|A tree ring|A phone ring|A bell;NEW|Both bird and fruit|A kiwi|A mango|A peach;NEW|Foot never walks head never thinks|A bed|A chair|A table;NEW|Both bank and river|A river bank|A bank|A stream;NEW|Face never frowns changes every day|A calendar|A clock|A mirror;NEW|Both game and animal|A bat|A ball|A cat;NEW|Back never bends face never smiles|A book|A chair|A wall;NEW|Both drink and color|Orange juice|Teal|Coffee;NEW|Tongue never talks tooth never bites|A zipper|A comb|A saw;NEW|Both vegetable and car|A beet|A carrot|A lemon;NEW|Nose never smells body never moves|A teapot|A doll|A statue;NEW|Both door and window|A glass door|A gate|A curtain;NEW|Hand never waves face never looks|A glove|A clock|A hand;NEW|Both light and heavy|A feather|A weight|A stone;NEW|Top never spins bottom never falls|A bottle cap|A lid|A hat;NEW|Both cat and dog|A hot dog|A catdog|A puppy;NEW|Key never opens lock never closes|A piano key|A keyboard|A door;NEW|Both snake and computer|Python|A cobra|A laptop;NEW|Head never hurts tail never wags|A hammer|A coin|A nail;NEW|Both flower and girl name|Rose|A lily|A daisy;NEW|Wing never flies beak never eats|A paper plane|A bird|A kite;NEW|Both day and night|Twilight|Dawn|Noon;NEW|Mouth never speaks ear never hears|A jug|A cup|A bottle;NEW|Both mountain and mole|A hill|A rock|A valley;NEW|Leg never runs arm never lifts|A chair|A table|A bed;NEW|Both sea and saw|A seasaw|A boat|A wave;NEW|Stomach never hungry mouth never eats|A bag|A box|A jar;NEW|Both ball and bell|A jingle bell|A basketball|A balloon;NEW|Tooth never hurts brush never paints|A comb|A toothbrush|A rake;NEW|Both pen and pig|A pigpen|A pen|A farm;NEW|Eye never blinks needle never sews|A storm|A potato|A needle;NEW|Both bear and bare|A bear|A bare|An animal;NEW|Horn never honks hoof never walks|A unicorn|A goat|A horse;NEW|Both rock and roll|Rock and roll|A stone|A music;NEW|Bark never bites leaf never falls|A tree|A dog|A book;NEW|Both lion and line|A lion|A line|A tiger;NEW|Shell never cracks yolk never cooks|A turtle|A snail|A nut;NEW|Both king and queen|A chess piece|A card|A crown;NEW|Root never grows branch never breaks|A family tree|A tree|A plant;NEW|Both cloud and crowd|A crowd|A cloud|A group;NEW|Wave never crashes hand never shakes|A goodbye wave|A wave|A hand;NEW|Both fire and fighter|A firefighter|A flame|A soldier;NEW|Cap never fits pen never writes|A mushroom|A hat|A pen;NEW|Both star and start|A star|A start|A sun;NEW|Bed never sleeps blanket never warms|A riverbed|A bed|A blanket;NEW|Both sun and son|Sun|A son|A moon;NEW|Nail never hurts hammer never hits|A fingernail|A nail|A toe;NEW|Both moon and spoon|Moon|A spoon|A star;NEW|Foot never steps yard never grows|A ruler|A yardstick|A foot;NEW|Both table and stable|A table|A stable|A chair;NEW|Heart never loves beat never stops|A metronome|A drum|A clock;NEW|Both cat and cap|Cat|A cap|A hat;NEW|Tail never wags head never thinks|A comet|A dog|A fish;NEW|Both rain and reign|Rain|A reign|A storm;NEW|Leg never walks foot never kicks|A table leg|A chair|A bed;NEW|Both well and wheel|Well|A wheel|A water;NEW|Smile never fades frown never appears|A photo|A Cheshire cat|A painting;NEW|Both ship and sheep|Ship|A sheep|A boat;NEW|Ear never hears corn never eats|An ear of corn|A corn|A ear;NEW|Both bat and ball|Bat|A ball|A game;NEW|Hole never leaks donut never eats|A donut hole|A donut|A hole;NEW|Both park and spark|Park|A spark|A car;NEW|Wing never flaps plane never flies|A building wing|A plane|A bird;NEW|Both rose and rise|Rose|A rise|A flower;NEW|Key never locks door never opens|A keyboard key|A key|A lock;NEW|Beginning of end end of time space essential to creation surround every place|The letter E|A circle|Time";
RB=RB+";"+NEW100;
function parseRB(){var o=[];RB.split(";").forEach(function(s){var p=s.split("|");if(p.length>=5)o.push({cat:p[0],q:p[1],a:p[2],w1:p[3],w2:p[4],id:p[0]+"|"+p[1]})});return o}
function isDom(){return user&&user.name&&user.name.toLowerCase()==="dominic"&&user.password==="2164"}
function toast(m){var t=document.getElementById("toast");if(!t)return;t.innerText=m;t.classList.remove("hidden");setTimeout(function(){t.classList.add("hidden")},4500)}
function showPage(id){hideMenu();if(quizT){clearInterval(quizT);quizT=null}currentPage=id;["page-home","page-register","page-dash","page-leader","page-game","page-bank","page-send","page-withdraw","page-deposit","page-exchange","page-profile","page-other","page-notifs","page-menu","page-update","page-review","page-challenge","page-messages","page-chat","page-economy","page-lottery","page-scifi","page-shop","page-crypto"].forEach(function(p){var e=document.getElementById(p);if(e){e.classList.add("hidden");e.style.display="none"}});var tg=document.getElementById(id);if(tg){tg.classList.remove("hidden");tg.style.display="block"}window.scrollTo(0,0);updateVisibility()}
function updateVisibility(){var r=document.getElementById("topRight"),nv=document.getElementById("bottomNav"),b=document.getElementById("backFab"),mf=document.getElementById("msgFab");var isEnter=(currentPage==="page-home"||currentPage==="page-register");if(isEnter){if(r)r.style.display="none";if(nv)nv.classList.add("hidden");if(b)b.style.display="none";if(mf)mf.style.display="none"}else if(loggedIn&&currentPage==="page-dash"){if(r)r.style.display="flex";if(nv)nv.classList.remove("hidden");if(b)b.style.display="none";if(mf)mf.style.display="flex"}else if(loggedIn){if(r)r.style.display="none";if(nv)nv.classList.add("hidden");if(b)b.style.display="flex";if(mf)mf.style.display="flex"}else{if(r)r.style.display="none";if(nv)nv.classList.add("hidden");if(b)b.style.display="none";if(mf)mf.style.display="none"}checkSwitch();checkLoanDue()}
function checkSwitch(){fetch("/api/switch_status").then(function(r){return r.json()}).then(function(d){gameOn=d.game_on!==false;var o=document.getElementById("frozenOverlay");if(!o)return;if(!gameOn){o.style.display="flex";document.getElementById("frozenDominicBox").style.display=isDom()?"block":"none"}else o.style.display="none"}).catch(function(){})}
function dominicUnfreeze(){var pin=document.getElementById("frozenPin").value.trim();if(pin!=="2164"){toast("Wrong PIN");return}fetch("/api/switch_toggle",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({admin:"dominic",pin:"2164",on:true})}).then(function(){gameOn=true;document.getElementById("frozenOverlay").style.display="none";toast("✅ GAME ON")})}
function toggleGameSwitch(){if(!isDom()){toast("🔒 Dominic only");return}var wantOff=gameOn;if(!confirm(wantOff?"Turn OFF?":"Turn ON?"))return;openPin("PIN 2164 SWITCH "+(wantOff?"OFF":"ON"),function(pin){fetch("/api/switch_toggle",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({admin:"dominic",pin:pin,on:!wantOff})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}gameOn=d.game_on;toast(gameOn?"✅ ON":"❄️ OFF");checkSwitch()})})}
function toggleSound(){soundOn=!soundOn;var b=document.getElementById("soundBtn");if(b)b.innerText=soundOn?"🔊":"🔇";if(soundOn)playPin();toast(soundOn?"🔊 ON":"🔇 OFF")}
function goDash(){if(!loggedIn){showPage("page-register");return}showPage("page-dash");loadLeader()}
function goBack(){if(currentPage==="page-register")showPage("page-home");else if(currentPage==="page-chat")showPage("page-messages");else goDash()}
function saveLocal(){try{var bk={name:user?user.name:"",password:user?user.password:"",wins:wins,losses:losses,gold:myGold,gems:myGems,player_id:myPlayerID,bank_id:myBankID,cars:myCars,seen:seenQs};localStorage.setItem("inf_user",JSON.stringify(user));localStorage.setItem("inf_backup",JSON.stringify(bk));localStorage.setItem("inf_wins",wins);localStorage.setItem("inf_losses",losses);localStorage.setItem("inf_gold",myGold);localStorage.setItem("inf_gems",myGems);localStorage.setItem("inf_player_id",myPlayerID);localStorage.setItem("inf_bank_id",myBankID);localStorage.setItem("inf_seen",JSON.stringify(seenQs));localStorage.setItem("inf_cars",JSON.stringify(myCars))}catch(e){}}
function doLogout(){loggedIn=false;showPage("page-home");toast("👋 Logged out - Data SAFE in DB.")}
function special(n,pw){var x=(n||"").toLowerCase().trim();if(x==="britney"||x==="kayula")return"Welcome MY Fiance 💖";if(x==="blessing")return"Welcome Avatar ✨";if(x==="lubuto")return"Welcome Desk Bender 🛠️";if(x==="dominic"&&pw==="2164")return"Welcome Infinity Emperor ♾";return"Welcome, "+n+" 👑"}
function doRegister(){var n=document.getElementById("regName").value.trim();var pw=document.getElementById("regPass").value.trim();if(!n||!pw||pw.length!==4||isNaN(pw)){toast("Name + 4-digit PIN");return}if(pw==="1234"||pw==="0000"){toast("Too easy");return}playPin();fetch("/api/player?name="+encodeURIComponent(n)).then(function(r){return r.json()}).then(function(d){if(d&&d.found){showLogin();document.getElementById("loginName").value=n;toast("Already exists! Just Login");return}user={name:n,password:pw};wins=0;losses=0;myGold=0;myGems=0;seenQs=[];myCars=[];saveLocal();syncScore();enterDash(special(n,pw))})}
function doLogin(){var n=document.getElementById("loginName").value.trim();var pw=document.getElementById("loginPass").value.trim();if(!n||!pw){toast("Name + Password");return}playPin();fetch("/api/player?name="+encodeURIComponent(n)+"&password="+encodeURIComponent(pw)).then(function(r){return r.json()}).then(function(d){if(d&&d.found&&d.password_ok!==false){user={name:n,password:pw};wins=d.wins||0;losses=d.losses||0;myGold=d.gold||0;myGems=d.gems||0;myPlayerID=d.player_id||"";myBankID=d.bank_id||"";seenQs=d.seen_qs||[];myCars=d.cars||[];saveLocal();enterDash(special(n,pw)+" - Restored ✅")}else if(d&&d.found===false){var b={};try{b=JSON.parse(localStorage.getItem("inf_backup")||"{}")}catch(e){}if(b.name&&b.name.toLowerCase()===n.toLowerCase()){toast("⚠️ Restoring from phone backup...");fetch("/api/restore",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:n,password:pw,wins:b.wins||wins,losses:b.losses||losses,gold:b.gold||myGold,gems:b.gems||myGems,cars:b.cars||myCars,player_id:b.player_id||myPlayerID,bank_id:b.bank_id||myBankID})}).then(function(r){return r.json()}).then(function(rd){if(rd.found){user={name:n,password:pw};wins=rd.player.wins||0;losses=rd.player.losses||0;myGold=rd.player.gold||0;myGems=rd.player.gems||0;myPlayerID=rd.player.player_id||"";saveLocal();enterDash(special(n,pw)+" - RESTORED ✅")}else toast("Not found - Register")})}else toast("Wrong / Not found")}else toast("Wrong / Not found")})}
function enterDash(m){loggedIn=true;toast(m);playPin();showPage("page-dash");document.getElementById("welcomeText").innerText=m;loadLeader();loadMe()}
function syncScore(){if(!user)return;fetch("/api/score",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,password:user.password,wins:wins,losses:losses,gold:myGold,gems:myGems,seen_qs:seenQs,cars:myCars})}).catch(function(){})}
function loadMe(){if(!user)return;fetch("/api/player?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){if(!d||!d.found)return;myGold=d.gold;myGems=d.gems;myCars=d.cars||myCars;wins=d.wins;losses=d.losses;if(d.crypto)cryptoHold=d.crypto;saveLocal();var e=function(id,v){var x=document.getElementById(id);if(x)x.innerText=v};e("bankGold",d.bank_gold||0);e("bankGems",d.bank_gems||0);e("bankIDShow",d.bank_id||myBankID);e("walletGold",d.gold);e("walletGems",d.gems);e("myCarsCount",myCars.length);var lb=document.getElementById("dashLoanBox");if(d.active_loan){lb.innerHTML="<div style='background:#00ff88;color:#000;padding:10px;border-radius:14px;font-size:12px;font-weight:900'>🏦 ACTIVE LOAN: "+d.active_loan.amount+" "+d.active_loan.currency+" - Repay by "+d.active_loan.repay_date+"<br><button class='btn' type='button' style='background:#000;color:#fff;padding:8px' onclick=\"payLoanNow('"+d.active_loan.id+"')\">💰 Pay Loan Now</button></div>"}else lb.innerHTML="";checkLoanDueWith(d.active_loan)})}
function loadLeader(){fetch("/api/leaderboard?mode=pvp").then(function(r){return r.json()}).then(function(d){var h="";(d.players||[]).slice(0,5).forEach(function(p,i){h+="<div class='leadRow' onclick=\"viewOther('"+p.name+"')\"><span>"+(i+1)+". "+p.name+(p.active_loan?" 🏦":"")+"</span><span>🏆 "+p.wins+"W | "+p.losses+"L</span></div>"});document.getElementById("leaderList").innerHTML=h||"No players"})}
function setLeaderMode(m){leaderMode=m;["gold","gems","pvp"].forEach(function(x){var el=document.getElementById("tab"+x.charAt(0).toUpperCase()+x.slice(1));if(el)el.classList.remove("active")});var a=document.getElementById("tab"+m.charAt(0).toUpperCase()+m.slice(1));if(a)a.classList.add("active");openFullLeader()}
function openFullLeader(){showPage("page-leader");fetch("/api/leaderboard?mode="+leaderMode).then(function(r){return r.json()}).then(function(d){var h="";(d.players||[]).forEach(function(p,i){h+="<div class='leadRow' onclick=\"viewOther('"+p.name+"')\"><span>"+(i+1)+". "+p.name+"<br><small>"+p.player_id+(p.active_loan?" | 🏦 Has Loan":"")+"</small></span><span>"+(leaderMode==="gold"?"🪙 "+p.gold+"<br><small>"+p.wins+"W | "+p.losses+"L</small>":leaderMode==="gems"?"💎 "+p.gems+"<br><small>"+p.wins+"W | "+p.losses+"L</small>":"🏆 "+p.wins+"W | "+p.losses+"L")+"</span></div>"});document.getElementById("fullLeaderList").innerHTML=h||"No players"})}
function viewOther(name){fetch("/api/player?name="+encodeURIComponent(name)).then(function(r){return r.json()}).then(function(d){showPage("page-other");document.getElementById("otherName").innerText=d.name;document.getElementById("otherRank").innerText=d.rank||"#-";document.getElementById("otherWins").innerText=d.wins;document.getElementById("otherLoss").innerText=d.losses;document.getElementById("otherActions").innerHTML="<button class='btn' type='button' onclick=\"openBankSendTo('"+d.player_id+"')\">💸 Send Gold</button><button class='btn2' type='button' onclick=\"sendFriendTo('"+d.player_id+"')\">👥 Send Friend Request</button>"})}
function openMyProfile(){if(!user)return;showPage("page-profile");fetch("/api/player?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){document.getElementById("profName").innerText=special(d.name,user.password);document.getElementById("profIDShow").innerText="ID:"+d.player_id;document.getElementById("profBankID").innerText=d.bank_id;document.getElementById("profWins").innerText=d.wins;document.getElementById("profLoss").innerText=d.losses;document.getElementById("profGold").innerText=d.gold;document.getElementById("profGems").innerText=d.gems;var cr="";if(d.crypto){for(var k in d.crypto){if(d.crypto[k]>0)cr+=k+": "+d.crypto[k]+" "}}document.getElementById("profCrypto").innerText=cr||"None";document.getElementById("profCars").innerText=(d.cars||[]).join(", ")||"None";var lb=document.getElementById("profLoanBox");if(d.active_loan){lb.style.display="block";lb.innerHTML="🏦 ACTIVE LOAN<br>"+d.active_loan.amount+" "+d.active_loan.currency+"<br>Repay by: "+d.active_loan.repay_date+"<br><button class='btn' type='button' onclick=\"payLoanNow('"+d.active_loan.id+"')\">💰 Pay Now</button>"}else lb.style.display="none";var fh="";(d.friends||[]).forEach(function(f){fh+="<div style='padding:10px;background:rgba(0,0,0,.4);border-radius:12px;margin:6px 0;display:flex;justify-content:space-between'><span>👥 "+f+"</span><button class='btn' type='button' style='width:auto;padding:6px 10px' onclick=\"openChatWith('"+f+"')\">💬 Chat</button></div>"});document.getElementById("profFriends").innerHTML=fh||"No friends yet";var rh="";(d.friend_requests||[]).forEach(function(rq){rh+="<div style='padding:10px;background:rgba(255,215,0,.2);border-radius:12px;margin:6px 0'>👥 "+rq.from+"<br><button class='btn' type='button' onclick=\"respondFriend('"+rq.id+"',true)\">✅ Accept</button><button class='btn2' type='button' onclick=\"respondFriend('"+rq.id+"',false)\">❌ Decline</button></div>"});document.getElementById("profFriendReqs").innerHTML=rh||"No requests";var inv="";(d.items||[]).forEach(function(it){inv+="<div style='padding:8px;background:rgba(0,0,0,.4);border-radius:10px;margin:4px 0'>🎒 "+it+" <button class='btn' type='button' style='width:auto;padding:4px 8px' onclick=\"consumeItem('"+it+"')\">Use (+20W)</button></div>"});(d.cars||[]).forEach(function(c){inv+="<div style='padding:8px;background:rgba(0,0,0,.4);border-radius:10px;margin:4px 0'>🚗 "+c+"</div>"});document.getElementById("profInventory").innerHTML=inv||"No items"})}
function consumeItem(it){openPin("PIN to Use "+it,function(pin){fetch("/api/consume",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,product:it,bonus:20})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}wins=d.wins;toast("✅ +20 Wins!");saveLocal();syncScore();openMyProfile()})})}
function openBank(){showPage("page-bank");loadMe()}
function openSendPage(){showPage("page-send");fetch("/api/player?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){document.getElementById("sendPageGold").innerText=d.gold;document.getElementById("sendPageGems").innerText=d.gems;document.getElementById("sendPageMyID").innerText=d.player_id})}
function openBankSendTo(pid){showPage("page-send");var dig=pid.replace("INF-","");document.getElementById("sendDigits").value=dig}
function doSend(){var amt=parseInt(document.getElementById("sendAmt").value||"0");var dig=document.getElementById("sendDigits").value.trim();if(!amt||!dig){toast("ID + Amount");return}openPin("PIN to Send "+amt+" Gold",function(pin){fetch("/api/transfer",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({sender:user.name,pin:pin,receiver_id:"INF-"+dig,amount:amt})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.sender_gold;toast("✅ Sent!");saveLocal();syncScore();goDash()})})}
function openWithdrawPage(){showPage("page-withdraw")}
function openDepositPage(){showPage("page-deposit")}
function doWithdraw(){var amt=parseInt(document.getElementById("withdrawAmt").value||"0");var cur=document.getElementById("withdrawCur").value;openPin("PIN Withdraw",function(pin){fetch("/api/bank_action",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,action:"withdraw",amount:amt,currency:cur})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.gold;myGems=d.gems;toast("✅ Withdrawn!");saveLocal();syncScore();openBank()})})}
function doDeposit(){var amt=parseInt(document.getElementById("depositAmt").value||"0");var cur=document.getElementById("depositCur").value;openPin("PIN Deposit",function(pin){fetch("/api/bank_action",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,action:"deposit",amount:amt,currency:cur})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.gold;myGems=d.gems;toast("✅ Deposited!");saveLocal();syncScore();openBank()})})}
function claimInterest(){openPin("PIN Claim Interest",function(pin){fetch("/api/bank_interest",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}toast("🎁 +10% Interest!");loadMe()})})}
function openExchangePage(){showPage("page-exchange")}
function openExchange(dir){var amt=prompt("Enter amount (Gold for Gem: 100 Gold = 1 Gem)");if(!amt)return;openPin("PIN Exchange",function(pin){fetch("/api/exchange",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,amount:parseInt(amt),direction:dir})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.gold;myGems=d.gems;toast("✅ Exchanged!");saveLocal();syncScore();openBank()})})}
function openCrypto(){showPage("page-crypto");fetch("/api/crypto?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){cryptoPrices=d.prices;cryptoHold=d.holdings;document.getElementById("cryptoGold").innerText=d.gold;var h="";for(var k in d.prices){h+="<div class='card' style='margin:6px 0'><b>"+k+"</b> — "+d.prices[k]+" Gold<br>Holding: "+(d.holdings[k]||0)+" "+k+"<br><input id='amt_"+k+"' type='number' step='any' placeholder='Amount'><button class='btn' type='button' onclick=\"cryptoTrade('"+k+"','buy')\">🟢 BUY</button><button class='btn2' type='button' onclick=\"cryptoTrade('"+k+"','sell')\">🔴 SELL</button></div>"}document.getElementById("cryptoList").innerHTML=h})}
function cryptoTrade(coin,act){var amt=parseFloat(document.getElementById("amt_"+coin).value||"0");if(!amt){toast("Enter amount");return}openPin("PIN Crypto "+act+" "+coin,function(pin){fetch("/api/crypto_trade",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,coin:coin,amount:amt,action:act})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.gold;cryptoHold=d.holdings;toast("✅ Crypto "+act+" done!");saveLocal();syncScore();openCrypto()})})}
function openLoan(){var o=document.getElementById("loanOverlay");o.classList.remove("hidden");o.style.display="flex"}
function closeLoan(){var o=document.getElementById("loanOverlay");o.classList.add("hidden");o.style.display="none"}
function submitLoan(){var amt=parseInt(document.getElementById("loanAmt").value||"0");var cur=document.getElementById("loanCur").value;var dt=document.getElementById("loanDate").value;if(!amt||!dt){toast("Amount + Date");return}closeLoan();openPin("PIN Apply Loan",function(pin){fetch("/api/loan_apply",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,amount:amt,currency:cur,repay_date:dt})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}toast("📩 Loan sent to Dominic!");loadMe()})})}
function payLoanNow(id){openPin("PIN Pay Loan",function(pin){fetch("/api/loan_repay",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,loan_id:id})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}toast("✅ Loan PAID!");loadMe();goDash()})})}
function checkLoanDue(){fetch("/api/player?name="+encodeURIComponent(user.name||"")).then(function(r){return r.json()}).then(function(d){if(d&&d.active_loan)checkLoanDueWith(d.active_loan)}).catch(function(){})}
function checkLoanDueWith(loan){if(!loan||!loan.repay_date)return;try{var today=new Date();today.setHours(0,0,0,0);var due=new Date(loan.repay_date+"T00:00:00");if(today<due)return;if(sessionStorage.getItem("loanDueShown_"+loan.id))return;sessionStorage.setItem("loanDueShown_"+loan.id,"1");currentLoan=loan;document.getElementById("loanDueText").innerText="Loan: "+loan.amount+" "+loan.currency+" - Due: "+loan.repay_date;var o=document.getElementById("loanDueOverlay");o.classList.remove("hidden");o.style.display="flex"}catch(e){}}
function loanDueAction(act){var o=document.getElementById("loanDueOverlay");o.classList.add("hidden");o.style.display="none";if(!currentLoan)return;fetch("/api/loan_due",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,loan_id:currentLoan.id,action:act})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}if(act==="extend")toast("⏳ Extended to "+d.new_date);else toast("💰 Collected! Wins taken: "+(d.wins_taken||0));loadMe()})}
function loanDateRespond(ok){var o=document.getElementById("loanDatePopup");o.classList.add("hidden");o.style.display="none";if(!pendingLoanForDate)return;fetch("/api/loan_player_confirm",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,loan_id:pendingLoanForDate,approve:ok})}).then(function(r){return r.json()}).then(function(d){toast(ok?"✅ Loan Received!":"❌ Loan Declined");loadMe()})}
function openSecret(){var o=document.getElementById("secretOverlay");o.classList.remove("hidden");o.style.display="flex"}
function closeSecret(){var o=document.getElementById("secretOverlay");o.classList.add("hidden");o.style.display="none"}
function sendMoneyRequest(){var msg=document.getElementById("reqMsg").value;var amt=document.getElementById("reqAmt").value;var cur=document.getElementById("reqCur").value;closeSecret();fetch("/api/request_money",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,message:msg,amount:amt,currency:cur})}).then(function(){toast("📩 Secret sent to Dominic!")})}
function openNotifs(){showPage("page-notifs");fetch("/api/player?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){var h="";(d.notifs||[]).slice().reverse().forEach(function(n){h+="<div style='padding:12px;background:rgba(0,0,0,.4);border-radius:12px;margin:6px 0'><b>"+n.type+"</b><br>"+n.text+"<br><small>"+n.time+"</small>";if(n.type==="loan_request"){h+="<br><button class='btn' type='button' onclick=\"dominicLoan('"+n.loan_id+"',true)\">✅ Approve</button><button class='btn2' type='button' onclick=\"dominicLoan('"+n.loan_id+"',false)\">❌ Decline</button>"}if(n.type==="loan_date_change"){h+="<br><button class='btn' type='button' onclick=\"showLoanDatePopup('"+n.loan_id+"','"+n.new_date+"')\">📅 View Date</button>"}if(n.type==="request"){h+="<br><button class='btn' type='button' onclick=\"dominicReq('"+n.request_id+"',"+n.amount+",'"+n.currency+"')\">✅ Approve Secret</button>"}h+="</div>"});document.getElementById("notifList").innerHTML=h||"No notifications"})}
function showLoanDatePopup(id,nd){pendingLoanForDate=id;document.getElementById("loanDatePopupText").innerText="Dominic set new date: "+nd;document.getElementById("loanDateInput").value=nd;var o=document.getElementById("loanDatePopup");o.classList.remove("hidden");o.style.display="flex"}
function dominicLoan(id,ok){var nd="";if(ok){nd=prompt("New repay date (YYYY-MM-DD) - leave blank to keep");}openPin("PIN Dominic Loan",function(pin){fetch("/api/loan_dominic",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({admin:"dominic",pin:pin,loan_id:id,approve:ok,new_date:nd})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}toast(ok?"✅ Loan Approved":"❌ Loan Declined");openNotifs()})})}
function dominicReq(id,amt,cur){openPin("PIN Approve Secret",function(pin){fetch("/api/request_approve",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({admin:"dominic",pin:pin,request_id:id,amount:amt,currency:cur})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}toast("✅ Secret Approved");openNotifs()})})}
function openEconomy(){if(!isDom()){toast("🔒 Dominic only");return}showPage("page-economy");fetch("/api/economy?name=dominic&password=2164").then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}var e=d.economy;document.getElementById("ecoGold").innerText=e.gold;document.getElementById("ecoGems").innerText=e.gems;document.getElementById("ecoBankGold").innerText=e.bank_gold||0;document.getElementById("ecoBankGems").innerText=e.bank_gems||0;document.getElementById("ecoLottery").innerText=e.lottery||0;document.getElementById("ecoStatus").innerText=e.gold<0?"⚠️ NEGATIVE - Emergency unlocked":"✅ Healthy";var eb=document.getElementById("emergencyBtn");eb.disabled=e.gold>=0;eb.style.background=e.gold<0?"#ff2222":"#666";document.getElementById("ecoCryptoBox").innerHTML="BTC: "+(e.crypto?e.crypto.BTC:"")+" | ETH: "+(e.crypto?e.crypto.ETH:"")+" | DOGE: "+(e.crypto?e.crypto.DOGE:"");var rh="";(d.requests||[]).forEach(function(rq){rh+="<div style='padding:10px;background:rgba(0,0,0,.4);border-radius:12px;margin:6px 0'>🔒 "+rq.from+" wants "+rq.amount+" "+rq.currency+"<br><button class='btn' type='button' onclick=\"dominicReq('"+rq.id+"',"+rq.amount+",'"+rq.currency+"')\">✅ Approve</button></div>"});document.getElementById("ecoRequests").innerHTML=rh||"No requests";var lh="";(d.loans||[]).forEach(function(l){lh+="<div style='padding:10px;background:rgba(0,0,0,.4);border-radius:12px;margin:6px 0'>🏦 "+l.from+" wants "+l.amount+" "+l.currency+" repay "+l.repay_date+"<br><button class='btn' type='button' onclick=\"dominicLoan('"+l.id+"',true)\">✅ Approve</button><button class='btn2' type='button' onclick=\"dominicLoan('"+l.id+"',false)\">❌ Decline</button></div>"});document.getElementById("ecoLoans").innerHTML=lh||"No loans"})}
function doEmergency(){openPin("PIN Emergency",function(pin){fetch("/api/emergency",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:"dominic",pin:pin})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}toast("🚨 Emergency DONE!");openEconomy()})})}
function openAnnounce(){if(!isDom()){toast("🔒 Dominic only");return}var o=document.getElementById("announceOverlay");o.classList.remove("hidden");o.style.display="flex"}
function closeAnnounce(){var o=document.getElementById("announceOverlay");o.classList.add("hidden");o.style.display="none"}
function sendAnnounce(){var t=document.getElementById("annText").value.trim();if(!t){toast("Write announcement");return}closeAnnounce();fetch("/api/announce",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({admin:"dominic",pin:"2164",text:t})}).then(function(){toast("📢 Announced!")})}
function openUpdate(){if(!isDom()){toast("🔒 Dominic only");return}showPage("page-update")}
function openReview(t){reviewType=t;showPage("page-review");document.getElementById("reviewTitle").innerText=(t==="bug"?"🐛 Report Bug":"⭐ Review")}
function submitReview(){var txt=document.getElementById("reviewText").value.trim();if(!txt){toast("Write something");return}fetch("/api/review",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,type:reviewType,text:txt})}).then(function(){toast("📩 Sent! Thank you");goDash()})}
function openChallenge(){showPage("page-challenge")}
function hostPickMode(mode){if(mode==="Bible Fight")openBible();else if(mode==="Riddles")openRiddles();else openSciFi()}
function openRiddles(){showPage("page-game");document.getElementById("gameTitle").innerText="🧩 Choose Riddle Type";document.getElementById("gameBody").innerHTML="<button class='btn' type='button' onclick=\"startQuiz('Riddles','NEW')\">✨ NEW 100 Riddles</button><button class='btn' type='button' onclick=\"startQuiz('Riddles','BIBLE')\">📖 Bible Riddles</button><button class='btn2' type='button' onclick='goDash()'>Back</button>"}
function openBible(){showPage("page-game");document.getElementById("gameTitle").innerText="📖 BIBLE FIGHT";document.getElementById("gameBody").innerHTML="<p>10 Questions • 3 Choices • 30s each • No repeats</p><button class='btn' type='button' onclick=\"startQuiz('Bible Fight','BIBLE')\">▶️ START BIBLE FIGHT</button><button class='btn2' type='button' onclick='goDash()'>Back</button>"}
function startQuiz(mode,cat){playPin();quizMode=mode;quizCat=cat;var all=parseRB().filter(function(q){return q.cat===cat});var fresh=all.filter(function(q){return seenQs.indexOf(q.id)===-1});if(fresh.length<10){seenQs=seenQs.filter(function(id){return id.indexOf(cat+"|")!==0});fresh=all;toast("🔄 All seen - restarting "+cat)}
for(var i=fresh.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1));var tmp=fresh[i];fresh[i]=fresh[j];fresh[j]=tmp}
quizRound=fresh.slice(0,10);quizIdx=0;quizScore=0;quizLoss=0;showQuizQ()}
function showQuizQ(){if(quizT){clearInterval(quizT);quizT=null}if(quizIdx>=quizRound.length){var q=quizRound.length;var res="<h2>🏁 FINISHED!</h2><p>✅ Correct: "+quizScore+" / "+q+"<br>❌ Wrong: "+quizLoss+"</p>";if(quizScore>=7){wins+=5;res+="<p>🎉 +5 WINS BONUS!</p>"}else if(quizScore>=5){wins+=2;res+="<p>🎉 +2 WINS!</p>"}else{losses+=1;res+="<p>💔 +1 LOSS - Try again!</p>"}res+="<button class='btn' type='button' onclick='goDash()'>🏠 Home</button><button class='btn2' type='button' onclick=\"startQuiz('"+quizMode+"','"+quizCat+"')\">🔄 Play Again</button>";document.getElementById("gameBody").innerHTML=res;saveLocal();syncScore();loadLeader();return}var cur=quizRound[quizIdx];if(seenQs.indexOf(cur.id)===-1)seenQs.push(cur.id);saveLocal();var opts=[cur.a,cur.w1,cur.w2];for(var i=opts.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1));var tmp=opts[i];opts[i]=opts[j];opts[j]=tmp}
var h="<p>Question "+(quizIdx+1)+" / "+quizRound.length+" • Score: "+quizScore+"W | "+quizLoss+"L</p><div class='timerBar'><div id='timerFill' class='timerFill' style='width:100%'></div></div><p id='timerText' style='text-align:center;font-weight:900'>30s</p><h3>"+cur.q+"</h3>";opts.forEach(function(o){h+="<button class='opt' type='button' onclick=\"answerQuiz('"+o.replace(/'/g,"\\'")+"')\">"+o+"</button>"});h+="<button class='btn2' type='button' onclick='goDash()'>❌ Quit</button>";document.getElementById("gameBody").innerHTML=h;quizLeft=30;quizT=setInterval(function(){quizLeft--;var f=document.getElementById("timerFill");if(f)f.style.width=(quizLeft/30*100)+"%";var tx=document.getElementById("timerText");if(tx)tx.innerText=quizLeft+"s";if(quizLeft<=0){clearInterval(quizT);quizT=null;quizLoss++;toast("⏰ Time up! Answer: "+quizRound[quizIdx].a);quizIdx++;setTimeout(showQuizQ,1200)}},1000)}
function answerQuiz(ans){if(quizT){clearInterval(quizT);quizT=null}var cur=quizRound[quizIdx];if(ans===cur.a){quizScore++;playPin();toast("✅ CORRECT!")}else{quizLoss++;toast("❌ Wrong! Answer: "+cur.a)}quizIdx++;setTimeout(showQuizQ,1000)}
function openSciFi(){showPage("page-scifi");document.getElementById("scifiList").innerHTML="<div class='box' onclick=\"startQuiz('SciFi','NEW')\">🧩 Riddles in SciFi</div><div class='box' onclick=\"startQuiz('SciFi','BIBLE')\">📖 Bible in SciFi</div><p style='text-align:center'>Full SciFi - 25 Dec 2026 🚀</p><button class='btn2' type='button' onclick='goDash()'>Back</button>"}
function setShopCat(c){shopCat=c;document.querySelectorAll(".catTab").forEach(function(t){t.classList.toggle("active",t.innerText.trim()===c||(c==="All"&&t.innerText.trim()==="All"))});renderShop()}
function openShop(){showPage("page-shop");renderShop()}
function renderShop(){var items=[{n:"Toyota Corolla",p:5000,c:"Cars"},{n:"BMW M4",p:25000,c:"Cars"},{n:"Lamborghini",p:120000,c:"Cars"},{n:"Ferrari",p:150000,c:"Cars"},{n:"Tesla Model 3",p:80000,c:"Cars"},{n:"Mercedes",p:90000,c:"Cars"},{n:"Audi R8",p:100000,c:"Cars"},{n:"Range Rover",p:70000,c:"Cars"},{n:"Hilux",p:40000,c:"Cars"},{n:"Nissan GTR",p:95000,c:"Cars"},{n:"Bugatti",p:500000,c:"Cars"},{n:"Pizza",p:500,c:"Food"},{n:"Burger",p:300,c:"Food"},{n:"Shawarma",p:400,c:"Food"},{n:"iPhone 16",p:15000,c:"Tech"},{n:"PS5",p:12000,c:"Tech"},{n:"Laptop",p:20000,c:"Tech"},{n:"Dog",p:8000,c:"Pets"},{n:"Cat",p:6000,c:"Pets"},{n:"Parrot",p:4000,c:"Pets"}];var h="";items.filter(function(it){return shopCat==="All"||it.c===shopCat}).forEach(function(it){var owned=myCars.indexOf(it.n)!==-1||false;h+="<div style='background:rgba(255,255,255,.12);border:2px solid rgba(255,255,255,.5);border-radius:18px;padding:12px;text-align:center'><b>"+it.n+"</b><br>🪙 "+it.p+" Gold<br><button class='btn' type='button' onclick=\"buyShopItem('"+it.n+"',"+it.p+")\">🛒 Buy</button></div>"});document.getElementById("shopGrid").innerHTML=h}
function buyShopItem(name,price){openPin("PIN Buy "+name,function(pin){fetch("/api/buy_item",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,item:name,price:price})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.gold;if(["Toyota","BMW","Lamborghini","Ferrari","Tesla","Mercedes","Audi","Rover","Hilux","Nissan","Bugatti"].some(function(x){return name.indexOf(x)!==-1}))myCars.push(name);toast("✅ Bought "+name+"!");saveLocal();syncScore();openShop()})})}
function openMessages(){showPage("page-messages");fetch("/api/friends?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){var h="";(d.friends||[]).forEach(function(f){h+="<div class='leadRow' onclick=\"openChatWith('"+f.name+"')\"><span>👥 "+f.name+"</span><span>💬 Chat →</span></div>"});document.getElementById("chatFriendList").innerHTML=h||"No friends yet - Add by ID above"})}
function sendFriendRequest(){var dig=document.getElementById("addFriendDigits").value.trim();if(!dig){toast("Enter ID");return}fetch("/api/friend_request",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,target_id:"INF-"+dig})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}toast("📩 Friend Request Sent!");openMessages()})}
function sendFriendTo(pid){fetch("/api/friend_request",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,target_id:pid})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}toast("📩 Friend Request Sent!")})}
function respondFriend(id,ok){fetch("/api/friend_respond",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,request_id:id,accept:ok})}).then(function(){toast(ok?"✅ Accepted!":"❌ Declined");openMyProfile()})}
function openChatWith(name){chatWithName=name;showPage("page-chat");document.getElementById("chatWith").innerText=name;loadChat()}
function loadChat(){if(!chatWithName)return;fetch("/api/chat_get?a="+encodeURIComponent(user.name)+"&b="+encodeURIComponent(chatWithName)).then(function(r){return r.json()}).then(function(d){var h="";(d.messages||[]).forEach(function(m){var me=m.from===user.name;h+="<div style='text-align:"+(me?"right":"left")+";margin:6px 0'><span style='display:inline-block;background:"+(me?"#ffd700;color:#000":"#fff;color:#000")+";padding:8px 12px;border-radius:14px;max-width:80%'><b>"+m.from+":</b> "+m.text+"</span></div>"});document.getElementById("chatBox").innerHTML=h||"No messages yet - Say Hi 👋";document.getElementById("chatBox").scrollTop=9999})}
function sendMsg(){var txt=document.getElementById("msgInput").value.trim();if(!txt||!chatWithName)return;document.getElementById("msgInput").value="";fetch("/api/chat_send",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({sender:user.name,to:chatWithName,text:txt})}).then(function(){loadChat()})}
function openPin(desc,cb){pinCb=cb;document.getElementById("pinDesc").innerText=desc;document.getElementById("pinInput").value="";var o=document.getElementById("pinOverlay");o.classList.remove("hidden");o.style.display="flex"}
function closePin(){var o=document.getElementById("pinOverlay");o.classList.add("hidden");o.style.display="none";pinCb=null}
function confirmPin(){var pin=document.getElementById("pinInput").value.trim();if(!pin||pin.length!==4){toast("Enter 4-digit PIN");return}var cb=pinCb;closePin();if(cb)cb(pin)}
function playLottery(){var bet=parseInt(document.getElementById("lotBet").value||"0");var cur=document.getElementById("lotCur").value;if(!bet){toast("Enter bet");return}openPin("PIN Lottery "+bet,function(pin){fetch("/api/lottery",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,bet:bet,currency:cur})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.gold;myGems=d.gems;document.getElementById("lotResult").innerHTML=d.result.win?"🎉 WON +"+d.result.prize:"💔 LOST - Try again";saveLocal();syncScore()})})}
function toggleMenu(e){if(e)e.stopPropagation();var d=document.getElementById("menuDrop");if(!d)return;if(!d.classList.contains("hidden")){d.classList.add("hidden");d.style.display="none";return}var dom=isDom();d.innerHTML="<div onclick=\"goDash()\">🏠 Home</div><div onclick=\"openFullLeader()\">🏆 Leaderboard</div><div onclick=\"openBank()\">💰 Bank</div><div onclick=\"openShop()\">🛍️ Shop</div><div onclick=\"openCrypto()\">₿ Crypto</div><div onclick=\"openMessages()\">💬 WhatsApp</div><div onclick=\"openMyProfile()\">👤 My Profile</div><div onclick=\"openNotifs()\">✉️ Notifications</div><div onclick=\"openLotteryPage()\">🎰 Lottery</div><div onclick=\"openChallenge()\">🎮 Challenge</div><div onclick=\"openReview('review')\">⭐ Review</div><div onclick=\"openReview('bug')\">🐛 Report Bug</div>"+(dom?"<div onclick=\"openEconomy()\">💰 Server Economy</div><div onclick=\"openUpdate()\">🔄 Update</div><div onclick=\"openAnnounce()\">📢 Announce</div>":"")+"<div onclick=\"doLogout()\">🚪 Logout</div>";d.classList.remove("hidden");d.style.display="block"}
function openLotteryPage(){showPage("page-lottery")}
function openMenuPage(){showPage("page-menu");document.getElementById("menuGamesList").innerHTML="<button class='btn' type='button' onclick='openRiddles()'>🧩 Riddles</button><button class='btn' type='button' onclick='openBible()'>📖 Bible Fight</button><button class='btn' type='button' onclick='openShop()'>🛍️ Shop</button><button class='btn' type='button' onclick='openCrypto()'>₿ Crypto</button><button class='btn' type='button' onclick='openLotteryPage()'>🎰 Lottery</button>"}
</script>
</body></html>"""
if __name__=="__main__":
 app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)))
