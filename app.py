import os,json,random,shutil,sqlite3,time
from datetime import datetime,timedelta
from flask import Flask,request,jsonify,make_response
app=Flask(__name__)
DB_FILE="infinity.db";DB_B1="infinity_backup1.db";DB_B2="infinity_backup2.db";ALL_DB=[DB_FILE,DB_B1,DB_B2]
DE={"gold":100000000,"gems":100000,"bank_gold":50000000,"bank_gems":50000000,"bank_total":100000000,"fees":0,"lottery":0,"backup":100000000,"history":[100000000,100000000],"crypto":{"BTC":85000,"ETH":4200,"DOGE":2}}
DATA={"players":{},"loans":[],"requests":[],"announcements":[],"reviews":[],"chats":{},"game_on":True,"friend_requests":[],"economy":dict(DE)}
def dc(p):
 c=sqlite3.connect(p);c.execute("CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT)");return c
def dr(p):
 try:
  if not os.path.exists(p):return None
  c=dc(p);r=c.execute("SELECT v FROM kv WHERE k='DATA'").fetchone();c.close();return json.loads(r[0]) if r else None
 except Exception:return None
def dw():
 try:
  c=dc(DB_FILE);c.execute("INSERT OR REPLACE INTO kv VALUES ('DATA',?)",(json.dumps(DATA),));c.commit();c.close()
  for b in [DB_B1,DB_B2]:
   try:shutil.copyfile(DB_FILE,b)
   except Exception:pass
 except Exception:pass
def save():dw()
def ss():
 o=[]
 for p in ALL_DB:
  d=dr(p);o.append({"file":p,"exists":os.path.exists(p),"players":len(d.get("players",{})) if d else 0})
 return o
def load():
 global DATA
 f=[d for d in [dr(p) for p in ALL_DB] if d]
 if not f:DATA["economy"]=dict(DE);dw();return
 f.sort(key=lambda x:len(x.get("players",{})),reverse=True)
 for k in DATA:
  if k in f[0]:DATA[k]=f[0][k]
 m={}
 for d in f:
  for n,p in d.get("players",{}).items():
   if n not in m:m[n]=p
   elif (p.get("wins",0)+p.get("gold",0))>(m[n].get("wins",0)+m[n].get("gold",0)):m[n]=p
 DATA["players"]=m;e=DATA.get("economy",{})
 if e.get("gold",0)==0 and len(m)==0:DATA["economy"]=dict(DE)
 else:e.setdefault("bank_gold",50000000);e.setdefault("bank_gems",50000000);e.setdefault("gems",100000);e.setdefault("crypto",{"BTC":85000,"ETH":4200,"DOGE":2})
 for v in DATA["players"].values():v.setdefault("crypto",{"BTC":0,"ETH":0,"DOGE":0});v.setdefault("losses",0);v.setdefault("galaxy_level",1);v.setdefault("galaxy_kills",0)
 dw()
load()
def norm(s):return str(s or "").strip().lower()
def getp(n):
 if not n:return None
 for k,v in DATA["players"].items():
  if norm(k)==norm(n):return v
 return None
def newp(name,pw):
 pid="INF-"+str(random.randint(10000000,99999999));bid="BANK INF-"+str(random.randint(10000000,99999999))
 p={"name":name,"display_name":name,"password":str(pw),"player_id":pid,"bank_id":bid,"wins":0,"losses":0,"gold":0,"gems":0,"bank_gold":0,"bank_gems":0,"cars":[],"items":[],"seen_qs":[],"crypto":{"BTC":0,"ETH":0,"DOGE":0},"galaxy_level":1,"galaxy_kills":0,"notifs":[],"friends":[],"active_loan":None,"loan_history":[],"rank":0,"last_interest":"","saved_at":int(time.time())}
 DATA["players"][name]=p;save();return p
def cpin(v,pin):
 if not v:return False
 return str(pin)=="2164" if norm(v.get("name"))=="dominic" else str(pin)==str(v.get("password"))
def notify(name,text,typ="info",extra=None):
 v=getp(name)
 if not v:
  if norm(name)=="dominic":v=newp("dominic","2164")
  else:return
 n={"text":text,"type":typ,"time":datetime.now().strftime("%H:%M %d %b")}
 if extra:n.update(extra)
 v.setdefault("notifs",[]).append(n);save()
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
def home():return make_response(HOME,200,{"Content-Type":"text/html; charset=utf-8"})
@app.route("/api/switch_status")
def sws():return jsonify({"game_on":DATA.get("game_on",True)})
@app.route("/api/switch_toggle",methods=["POST"])
def swt():
 d=request.get_json() or {}
 if norm(d.get("admin"))!="dominic" or str(d.get("pin"))!="2164":return jsonify({"error":"Only Dominic"}),403
 DATA["game_on"]=bool(d.get("on",True));save();return jsonify({"ok":True,"game_on":DATA["game_on"]})
@app.route("/api/player")
def apl():
 v=getp(request.args.get("name",""))
 if not v:return jsonify({"found":False})
 if request.args.get("password") and str(request.args.get("password"))!=str(v.get("password")):return jsonify({"found":True,"password_ok":False})
 return jsonify({"found":True,"password_ok":True,"name":v["name"],"player_id":v.get("player_id"),"bank_id":v.get("bank_id"),"wins":v.get("wins",0),"losses":v.get("losses",0),"gold":v.get("gold",0),"gems":v.get("gems",0),"bank_gold":v.get("bank_gold",0),"bank_gems":v.get("bank_gems",0),"cars":v.get("cars",[]),"items":v.get("items",[]),"seen_qs":v.get("seen_qs",[]),"crypto":v.get("crypto",{"BTC":0,"ETH":0,"DOGE":0}),"galaxy_level":v.get("galaxy_level",1),"galaxy_kills":v.get("galaxy_kills",0),"notifs":v.get("notifs",[])[-30:],"friends":v.get("friends",[]),"friend_requests":[r for r in DATA.get("friend_requests",[]) if norm(r.get("to"))==norm(v["name"]) and r.get("status")=="pending"],"active_loan":alo(v),"loans":[x for x in DATA["loans"] if norm(x.get("from"))==norm(v["name"])],"rank":v.get("rank",0)})
@app.route("/api/restore",methods=["POST"])
def ar():
 d=request.get_json() or {};n=d.get("name","");pw=str(d.get("password",""));v=getp(n)
 if v:return jsonify({"restored":False,"found":True,"player":v}) if str(v.get("password"))==pw else (jsonify({"error":"Wrong password"}),403)
 v=newp(n,pw);v["wins"]=int(d.get("wins",0) or 0);v["losses"]=int(d.get("losses",0) or 0);v["gold"]=int(d.get("gold",0) or 0);v["gems"]=int(d.get("gems",0) or 0);v["cars"]=d.get("cars",[]);v["items"]=d.get("items",[])
 if d.get("player_id"):v["player_id"]=d.get("player_id")
 if d.get("bank_id"):v["bank_id"]=d.get("bank_id")
 save();return jsonify({"restored":True,"found":True,"player":v})
@app.route("/api/score",methods=["POST"])
def asc():
 d=request.get_json() or {};v=getp(d.get("name"))
 if not v:v=newp(d.get("name","Player"),d.get("password","0000"))
 v["wins"]=max(v.get("wins",0),int(d.get("wins",0)));v["losses"]=max(v.get("losses",0),int(d.get("losses",0)));v["gold"]=max(v.get("gold",0),int(d.get("gold",0)));v["gems"]=max(v.get("gems",0),int(d.get("gems",0)))
 if d.get("cars") and len(d.get("cars",[]))>len(v.get("cars",[])):v["cars"]=d.get("cars")
 if d.get("seen_qs"):v["seen_qs"]=list(set(v.get("seen_qs",[]))|set(d.get("seen_qs",[])))
 v["saved_at"]=int(time.time());save();return jsonify({"ok":True})
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
 v["gold"]-=amt;r["gold"]=r.get("gold",0)+amt;notify(r["name"],v["name"]+" sent you "+str(amt)+" Gold");save();return jsonify({"ok":True,"sender_gold":v["gold"]})
@app.route("/api/bank_action",methods=["POST"])
def aba():
 d=request.get_json() or {};v=getp(d.get("name"))
 if not v or not cpin(v,d.get("pin","")):return jsonify({"error":"Wrong PIN"}),403
 amt=int(d.get("amount",0));cur=d.get("currency","Gold");g=(cur=="Gold")
 if d.get("action")=="deposit":
  if g:
   if v.get("gold",0)<amt:return jsonify({"error":"Not enough"}),400
   v["gold"]-=amt;v["bank_gold"]=v.get("bank_gold",0)+amt;DATA["economy"]["bank_gold"]=DATA["economy"].get("bank_gold",0)+amt
  else:
   if v.get("gems",0)<amt:return jsonify({"error":"Not enough"}),400
   v["gems"]-=amt;v["bank_gems"]=v.get("bank_gems",0)+amt;DATA["economy"]["bank_gems"]=DATA["economy"].get("bank_gems",0)+amt
 else:
  if g:
   if v.get("bank_gold",0)<amt:return jsonify({"error":"Not enough in Bank"}),400
   v["bank_gold"]-=amt;v["gold"]=v.get("gold",0)+amt
  else:
   if v.get("bank_gems",0)<amt:return jsonify({"error":"Not enough in Bank"}),400
   v["bank_gems"]-=amt;v["gems"]=v.get("gems",0)+amt
 save();return jsonify({"ok":True,"gold":v["gold"],"gems":v["gems"],"bank_gold":v.get("bank_gold",0),"bank_gems":v.get("bank_gems",0)})
@app.route("/api/bank_interest",methods=["POST"])
def abi():
 d=request.get_json() or {};v=getp(d.get("name"))
 if not v or not cpin(v,d.get("pin","")):return jsonify({"error":"Wrong PIN"}),403
 mo=datetime.now().strftime("%Y-%m")
 if v.get("last_interest")==mo:return jsonify({"error":"Already claimed this month"}),400
 bg=int(v.get("bank_gold",0)*0.10);bm=int(v.get("bank_gems",0)*0.10);v["bank_gold"]=v.get("bank_gold",0)+bg;v["bank_gems"]=v.get("bank_gems",0)+bm;v["last_interest"]=mo;save();return jsonify({"ok":True,"bonus_gold":bg,"bonus_gems":bm})
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
 save();return jsonify({"ok":True,"gold":v["gold"],"gems":v["gems"]})
@app.route("/api/crypto",methods=["GET"])
def acg():
 e=DATA["economy"].get("crypto",{"BTC":85000,"ETH":4200,"DOGE":2})
 for k in e:e[k]=max(1,round(e[k]*(1+random.uniform(-0.03,0.03)),2))
 save();v=getp(request.args.get("name",""));return jsonify({"prices":e,"holdings":v.get("crypto",{"BTC":0,"ETH":0,"DOGE":0}) if v else {"BTC":0,"ETH":0,"DOGE":0},"gold":v.get("gold",0) if v else 0})
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
 save();return jsonify({"ok":True,"gold":v["gold"],"holdings":v["crypto"]})
@app.route("/api/loan_apply",methods=["POST"])
def ala():
 d=request.get_json() or {};v=getp(d.get("name"));amt=int(d.get("amount",0))
 if not v or not cpin(v,d.get("pin","")):return jsonify({"error":"Wrong PIN"}),403
 if alo(v):return jsonify({"error":"You already have ACTIVE loan. Pay it first!"}),400
 lid="LN-"+str(random.randint(10000000,99999999));loan={"id":lid,"from":v["display_name"],"amount":amt,"currency":d.get("currency","Gold"),"repay_date":d.get("repay_date",""),"status":"pending_dominic","dominic_new_date":"","extended":False}
 DATA["loans"].append(loan);notify("dominic","LOAN: "+v["display_name"]+" wants "+str(amt)+" "+loan["currency"],"loan_request",{"loan_id":lid,"amount":amt,"currency":loan["currency"],"repay_date":loan["repay_date"],"from":v["display_name"]});save();return jsonify({"ok":True})
@app.route("/api/loan_dominic",methods=["POST"])
def ald():
 d=request.get_json() or {}
 if norm(d.get("admin"))!="dominic" or str(d.get("pin"))!="2164":return jsonify({"error":"Only Dominic"}),403
 for l in list(DATA["loans"]):
  if l["id"]==d.get("loan_id"):
   dom=getp("dominic")
   if dom:dom["notifs"]=[n for n in dom.get("notifs",[]) if not (n.get("type")=="loan_request" and n.get("loan_id")==l["id"])]
   if not d.get("approve"):
    notify(l["from"],"Loan DECLINED by Dominic");DATA["loans"]=[x for x in DATA["loans"] if x["id"]!=l["id"]];save();return jsonify({"ok":True})
   l["dominic_new_date"]=d.get("new_date") or l["repay_date"];l["status"]="waiting_player_confirm";notify(l["from"],"Dominic APPROVED your loan! Date: "+l["dominic_new_date"],"loan_date_change",{"loan_id":l["id"],"new_date":l["dominic_new_date"]});save();return jsonify({"ok":True})
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
   save();return jsonify({"ok":True})
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
 DATA["loans"]=[x for x in DATA["loans"] if x["id"]!=loan["id"]];v["active_loan"]=None;v.setdefault("loan_history",[]).append({"id":loan["id"],"amount":amt,"currency":cur,"paid":True});notify(v["name"],"Loan PAID: "+str(amt)+" "+cur);save();return jsonify({"ok":True})
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
  loan["extended"]=True;loan["status"]="extended";v["active_loan"]=loan;save();return jsonify({"ok":True,"new_date":loan["repay_date"]})
 amt=loan["amount"];cur=loan["currency"];wt=0
 if cur=="Gold":
  h=v.get("gold",0)
  if h>=amt:v["gold"]-=amt;DATA["economy"]["gold"]+=amt
  else:v["gold"]=0;wt=((amt-h)+999)//1000;v["wins"]=max(0,v.get("wins",0)-wt);DATA["economy"]["gold"]+=h
 else:
  h=v.get("gems",0)
  if h>=amt:v["gems"]-=amt;DATA["economy"]["gems"]+=amt
  else:v["gems"]=0;wt=((amt-h)+9)//10;v["wins"]=max(0,v.get("wins",0)-wt);DATA["economy"]["gems"]+=h
 DATA["loans"]=[x for x in DATA["loans"] if x["id"]!=loan["id"]];v["active_loan"]=None;notify(v["name"],"Collected Loan: -"+str(wt)+" Wins");save();return jsonify({"ok":True,"wins_taken":wt,"wins":v["wins"]})
@app.route("/api/request_money",methods=["POST"])
def arq():
 d=request.get_json() or {};v=getp(d.get("name"))
 if not v:return jsonify({"error":"No player"}),404
 rid="RQ-"+str(random.randint(10000000,99999999));amt=int(d.get("amount") or 0);r={"id":rid,"from":v["display_name"],"amount":amt,"currency":d.get("currency","Gold"),"message":d.get("message","")};DATA["requests"].append(r);notify("dominic","SECRET: "+v["display_name"]+" wants "+str(amt)+" "+r["currency"],"request",{"request_id":rid,"amount":amt,"currency":r["currency"]});save();return jsonify({"ok":True})
@app.route("/api/request_approve",methods=["POST"])
def arqa():
 d=request.get_json() or {}
 if norm(d.get("admin"))!="dominic" or str(d.get("pin"))!="2164":return jsonify({"error":"Only Dominic"}),403
 for r in DATA["requests"]:
  if r["id"]==d.get("request_id"):
   v=getp(r["from"])
   if v:
    if d.get("currency","Gold")=="Gold":v["gold"]=v.get("gold",0)+int(d.get("amount",0));DATA["economy"]["gold"]-=int(d.get("amount",0))
    else:v["gems"]=v.get("gems",0)+int(d.get("amount",0));DATA["economy"]["gems"]-=int(d.get("amount",0))
    notify(v["name"],"Secret Approved: +"+str(d.get("amount",0))+" "+d.get("currency","Gold"));dom=getp("dominic")
    if dom:dom["notifs"]=[n for n in dom.get("notifs",[]) if not (n.get("type")=="request" and n.get("request_id")==r["id"])]
   DATA["requests"]=[x for x in DATA["requests"] if x["id"]!=r["id"]];save();return jsonify({"ok":True})
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
 save();return jsonify({"ok":True,"gold":v["gold"]})
@app.route("/api/consume",methods=["POST"])
def aco():
 d=request.get_json() or {};v=getp(d.get("name"))
 if not v or not cpin(v,d.get("pin","")):return jsonify({"error":"Wrong PIN"}),403
 p=d.get("product","")
 if p in v.get("items",[]):v["items"].remove(p)
 v["wins"]=v.get("wins",0)+int(d.get("bonus",20));save();return jsonify({"ok":True,"wins":v["wins"]})
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
 save();return jsonify({"ok":True,"gold":v["gold"],"gems":v["gems"],"result":res})
@app.route("/api/announce",methods=["POST"])
def aan():
 d=request.get_json() or {}
 if norm(d.get("admin"))!="dominic" or str(d.get("pin"))!="2164":return jsonify({"error":"Only Dominic"}),403
 DATA["announcements"].append({"text":d.get("text",""),"time":datetime.now().strftime("%H:%M")})
 for v in DATA["players"].values():v.setdefault("notifs",[]).append({"text":"ANNOUNCE: "+d.get("text",""),"type":"announce","time":datetime.now().strftime("%H:%M")})
 save();return jsonify({"ok":True})
@app.route("/api/announcements")
def aann():return jsonify({"announcements":DATA["announcements"][-5:]})
@app.route("/api/economy")
def aeco():
 if norm(request.args.get("name"))!="dominic" or str(request.args.get("password"))!="2164":return jsonify({"error":"Only Dominic"}),403
 return jsonify({"economy":DATA["economy"],"requests":DATA["requests"],"loans":[x for x in DATA["loans"] if x.get("status")=="pending_dominic"],"backups":ss(),"is_negative":DATA["economy"].get("gold",0)<0})
@app.route("/api/emergency",methods=["POST"])
def aem():
 d=request.get_json() or {}
 if norm(d.get("name"))!="dominic" or str(d.get("pin"))!="2164":return jsonify({"error":"Only Dominic"}),403
 if DATA["economy"].get("gold",0)>=0:return jsonify({"error":"Not negative - Locked"}),400
 v=getp("dominic") or newp("dominic","2164");DATA["economy"].update({"gold":100000000,"gems":100000,"bank_gold":50000000,"bank_gems":50000000});v["gold"]=v.get("gold",0)+500000000000;save();return jsonify({"ok":True})
@app.route("/api/server_info")
def asv():
 if norm(request.args.get("name"))!="dominic" or str(request.args.get("password"))!="2164":return jsonify({"error":"Only Dominic"}),403
 return jsonify({"players":len(DATA["players"]),"earning_on":True,"reviews":DATA["reviews"][-20:],"backups":ss()})
@app.route("/api/storage_status")
def ast():
 if norm(request.args.get("name"))!="dominic" or str(request.args.get("password"))!="2164":return jsonify({"error":"Only Dominic"}),403
 return jsonify({"db":"SQLite infinity.db + 2 backups","backups":ss(),"ram_players":len(DATA["players"])})
@app.route("/api/review",methods=["POST"])
def arv():
 d=request.get_json() or {};DATA["reviews"].append({"name":d.get("name"),"type":d.get("type"),"text":d.get("text")});save();return jsonify({"ok":True})
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
 for r in DATA.get("friend_requests",[]):
  if norm(r.get("from"))==norm(v["name"]) and norm(r.get("to"))==norm(t["name"]) and r.get("status")=="pending":return jsonify({"error":"Request already sent"}),400
 DATA.setdefault("friend_requests",[]).append({"id":"FR-"+str(random.randint(10000000,99999999)),"from":v["display_name"],"to":t["display_name"],"status":"pending"});notify(t["name"],"Friend Request from "+v["display_name"],"friend_request");save();return jsonify({"ok":True})
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
    notify(r["from"],v["display_name"]+" ACCEPTED your Friend Request!")
   else:r["status"]="declined";notify(r["from"],v["display_name"]+" declined Friend Request")
   save();return jsonify({"ok":True})
 return jsonify({"error":"Not found"}),404
@app.route("/api/chat_send",methods=["POST"])
def acs():
 d=request.get_json() or {};k="|".join(sorted([norm(d.get("sender","")),norm(d.get("to",""))]));DATA["chats"].setdefault(k,[]).append({"from":d.get("sender",""),"text":d.get("text","")});save();return jsonify({"ok":True})
@app.route("/api/chat_get")
def acg2():
 k="|".join(sorted([norm(request.args.get("a","")),norm(request.args.get("b",""))]));return jsonify({"messages":DATA["chats"].get(k,[])})

HOME=r"""<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>INFINITY BOT v44</title><style>*{box-sizing:border-box}html,body{margin:0;padding:0}body{font-family:Arial;color:#fff;background:radial-gradient(circle at 50% 0%,#5a1a9e 0%,#2a0a5e 35%,#12002b 70%,#0a0018 100%);min-height:100vh;background-attachment:fixed}.topbar{display:flex;justify-content:space-between;padding:8px 14px;position:relative;z-index:10}.center{min-height:82vh;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:20px;position:relative;z-index:5}.enterBtn{margin-top:18px;padding:16px 70px;font-size:34px;font-weight:900;border:none;border-radius:60px;background:linear-gradient(90deg,#ff006e,#ffd700,#00e5ff);color:#000;cursor:pointer;position:relative;z-index:999;box-shadow:0 10px 30px rgba(255,0,110,.5);pointer-events:auto!important}.card{background:rgba(255,255,255,.10);border:2px solid rgba(255,255,255,.35);border-radius:26px;padding:20px;margin:14px;backdrop-filter:blur(6px)}.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.box{background:linear-gradient(160deg,rgba(255,255,255,.22),rgba(0,0,0,.45));border:2px solid #fff;border-radius:24px;padding:22px 10px;text-align:center;cursor:pointer;position:relative;z-index:5}.box span{font-size:32px;display:block}button{cursor:pointer;position:relative;z-index:5}.btn{width:100%;padding:14px;border:none;border-radius:25px;font-weight:900;background:#ffd700;color:#000;margin:6px 0;position:relative;z-index:999;pointer-events:auto!important}.btn2{width:100%;padding:13px;border-radius:25px;border:2px solid #00e5ff;background:transparent;color:#00e5ff;font-weight:900;margin:6px 0;position:relative;z-index:999;pointer-events:auto!important}.opt{width:100%;padding:13px;margin:7px 0;border-radius:16px;border:2px solid #fff;background:rgba(0,0,0,.5);color:#fff;font-weight:700;cursor:pointer;text-align:left;position:relative;z-index:999}input,select,textarea{width:100%;padding:14px;border-radius:14px;border:2px solid #ffd700;margin:8px 0;font-size:16px;background:#fff;color:#000;position:relative;z-index:999}.hidden{display:none!important}.leadRow{display:flex;justify-content:space-between;align-items:center;padding:10px 12px;background:rgba(0,0,0,.45);border-radius:14px;margin:6px 0;cursor:pointer}.toast{position:fixed;top:70px;left:50%;transform:translateX(-50%);background:#fff;color:#000;padding:12px 18px;border-radius:20px;font-weight:700;z-index:9999;max-width:90%;text-align:center}.ov{position:fixed;inset:0;background:rgba(0,0,0,.78);display:flex;align-items:center;justify-content:center;padding:16px;z-index:500}.pop{background:linear-gradient(160deg,#2b005e,#12002b);border:3px solid #ffd700;border-radius:28px;padding:22px 18px;max-width:420px;width:100%;text-align:center;position:relative;z-index:501}.choiceRow{display:flex;gap:12px;margin-top:16px}.choiceBox{flex:1;padding:18px 8px;border-radius:20px;cursor:pointer;font-weight:900;border:3px solid #fff;position:relative;z-index:999;pointer-events:auto!important}.choiceNo{background:#ff2222;color:#fff}.choiceYes{background:#00cc44;color:#000}.walletCard{background:linear-gradient(135deg,#ffd700,#ff006e);color:#000;border-radius:24px;padding:18px;text-align:center}.bigBankBox{padding:22px 10px;border-radius:24px;border:2px solid #fff;text-align:center;cursor:pointer;background:linear-gradient(160deg,rgba(255,255,255,.18),rgba(0,0,0,.4))}.loanGreen{border:4px solid #00ff88!important;background:linear-gradient(160deg,#00cc44,#00ff88)!important;color:#000!important}.idPrefix{display:flex;align-items:center;background:#fff;border-radius:14px;border:2px solid #ffd700;padding:0 10px;margin:8px 0}.idPrefix b{color:#000}.idPrefix input{border:none;flex:1;margin:0}.timerBar{height:14px;background:#333;border-radius:99px;overflow:hidden}.timerFill{height:100%;background:linear-gradient(90deg,#00ff88,#ffd700,#ff2222);transition:width 1s linear}.tabBox{flex:1;padding:12px 4px;border-radius:16px;background:rgba(255,255,255,.15);border:2px solid #ffd700;text-align:center;cursor:pointer;font-weight:900;font-size:13px}.tabBox.active{background:#ffd700;color:#000}.catTab{padding:8px 4px;border-radius:12px;background:rgba(255,255,255,.12);border:1px solid #ffd700;text-align:center;cursor:pointer;font-size:11px;font-weight:900}.catTab.active{background:#ffd700;color:#000}#menuDrop{position:fixed!important;top:108px!important;right:8px!important;width:210px!important;background:#1a1a2e;border:2px solid #ffd700;border-radius:14px;padding:6px;z-index:900}#menuDrop div{padding:9px!important;font-size:13px!important;cursor:pointer}#page-welcome{z-index:2000!important}.shopGrid{display:grid;grid-template-columns:1fr 1fr;gap:10px}.shopBox{background:rgba(255,255,255,.12);border:2px solid rgba(255,255,255,.5);border-radius:18px;padding:12px;text-align:center}</style></head><body>
<div id="frozenOverlay" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.92);z-index:3000;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:20px"><h1>❄️ GAME PAUSED</h1><p style="color:#ffd700;font-weight:900">SWITCHED OFF BY DOMINIC</p><div id="frozenDominicBox" style="display:none;margin-top:20px;background:#1a1a2e;border:2px solid #ffd700;border-radius:20px;padding:16px;width:100%;max-width:320px"><p>👑 Dominic Only</p><input id="frozenPin" type="password" inputmode="numeric" maxlength="4" placeholder="2164"><button class="btn" type="button" onclick="dominicUnfreeze()">🔓 TURN GAME ON</button></div></div>
<div id="loanDatePopup" class="ov hidden" style="display:none;z-index:1200"><div class="pop"><h2>📅 Dominic Changed Date</h2><p id="loanDatePopupText"></p><input id="loanDateInput" type="date"><div class="choiceRow"><div class="choiceBox choiceNo" onclick="loanDateRespond(false)">❌ No - Refund</div><div class="choiceBox choiceYes" onclick="loanDateRespond(true)">✅ Yes - Receive Loan</div></div></div></div>
<div id="loanDueOverlay" class="ov hidden" style="display:none;z-index:1100"><div class="pop"><h2>⏰ LOAN DUE!</h2><p id="loanDueText"></p><div class="choiceRow"><div class="choiceBox choiceNo" onclick="loanDueAction('extend')">⏳ Extension +7 Days</div><div class="choiceBox choiceYes" onclick="loanDueAction('collect')">💰 Pay / Collect Now</div></div></div></div>
<div id="menuDrop" class="hidden"></div><div id="toast" class="toast hidden"></div>
<div id="pinOverlay" class="ov hidden" style="display:none;z-index:900"><div class="pop"><h2>Enter PIN</h2><p id="pinDesc"></p><input id="pinInput" placeholder="...." maxlength="4" inputmode="numeric" type="password" style="font-size:28px;text-align:center;letter-spacing:12px"><div class="choiceRow"><div class="choiceBox choiceNo" onclick="closePin()">Cancel</div><div class="choiceBox choiceYes" onclick="confirmPin()">Confirm</div></div></div></div>
<div id="announceOverlay" class="ov hidden" style="display:none;z-index:960"><div class="pop"><h2>📢 Announcement</h2><textarea id="annText" style="height:100px"></textarea><button class="btn" type="button" onclick="sendAnnounce()">📢 Announce</button><button class="btn2" type="button" onclick="closeAnnounce()">Cancel</button></div></div>
<div id="secretOverlay" class="ov hidden" style="display:none;z-index:920"><div class="pop"><h2>🔒 Secret</h2><input id="reqMsg" type="password" placeholder="Secret message"><input id="reqAmt" type="password" inputmode="numeric" placeholder="Amount"><select id="reqCur"><option>Gold</option><option>Gems</option></select><div class="choiceRow"><div class="choiceBox choiceNo" onclick="closeSecret()">Cancel</div><div class="choiceBox choiceYes" onclick="sendMoneyRequest()">📩 Send</div></div></div></div>
<div id="loanOverlay" class="ov hidden" style="display:none;z-index:920"><div class="pop"><h2>🏦 Apply for Loan</h2><input id="loanAmt" type="number" placeholder="Amount"><select id="loanCur"><option>Gold</option><option>Gems</option></select><label>When to repay?</label><input id="loanDate" type="date"><div class="choiceRow"><div class="choiceBox choiceNo" onclick="closeLoan()">Cancel</div><div class="choiceBox choiceYes" onclick="submitLoan()">📩 Apply</div></div></div></div>
<div id="page-welcome" class="ov hidden" style="display:none;z-index:2000"><div class="pop"><h2>Do you already have an account?</h2><div class="choiceRow"><div class="choiceBox choiceNo" type="button" onclick="welcomeChoice('no')">❌ No</div><div class="choiceBox choiceYes" type="button" onclick="welcomeChoice('yes')">✅ Yes</div></div></div></div>
<div class="topbar"><div><span id="catTime" style="font-size:12px;background:rgba(0,0,0,.55);border:1px solid #ffd700;padding:5px 9px;border-radius:20px">Loading time...</span><br><span id="catDate" style="font-size:10px;background:rgba(0,0,0,.45);padding:3px 8px;border-radius:20px">Central Africa</span><br><div style="font-weight:900">INFINITY BOT</div></div><div id="topRight" style="display:none;flex-direction:column;align-items:flex-end;gap:4px"><div style="display:flex;gap:6px"><div onclick="toggleSound()" style="padding:6px 8px;border-radius:20px;background:rgba(0,0,0,.55);border:1px solid #ffd700;cursor:pointer;font-size:11px"><span id="soundBtn">🔊 SOUND ON</span></div><div onclick="openShop()" style="padding:6px 8px;border-radius:20px;background:rgba(0,0,0,.55);border:1px solid #ffd700;cursor:pointer;font-size:11px">🛍️ SHOP</div><div onclick="openMyProfile()" style="padding:6px 8px;border-radius:20px;background:linear-gradient(135deg,#ff006e,#ffd700);cursor:pointer;border:2px solid #fff;font-size:11px">👤 ME</div></div><div id="menuBtn" onclick="toggleMenu(event)" style="padding:6px 10px;border-radius:20px;background:rgba(0,0,0,.55);border:1px solid #ffd700;cursor:pointer;font-size:11px">⋮ MENU</div></div></div>
<div id="page-home" class="center"><div style="font-size:90px">👑</div><h1 style="font-size:58px;margin:5px">Infinity Bot</h1><p style="letter-spacing:3px;font-weight:900">DOMINIC MASTIRIA</p><p style="font-size:11px;color:#00ff88">DB Storage - Never Lose Account</p><button class="enterBtn" id="enterBtn" type="button" onclick="enterClicked()">Enter</button></div>
<div id="page-register" class="hidden" style="max-width:520px;margin:0 auto;padding:20px 14px;position:relative;z-index:10"><div class="card" style="text-align:center"><h1 style="font-size:48px">Register</h1><div id="registerForm"><input id="regName" placeholder="Your Name" maxlength="20"><input id="regPass" placeholder="...." maxlength="4" inputmode="numeric" type="password"><button class="btn" type="button" onclick="doRegister()">📝 REGISTER</button><p>Already? <b style="color:#ffd700;cursor:pointer" onclick="showLogin()">Login</b></p></div><div id="loginForm" class="hidden"><input id="loginName" placeholder="Your Name"><input id="loginPass" placeholder="...." maxlength="4" inputmode="numeric" type="password"><button class="btn" type="button" onclick="doLogin()">🔓 LOGIN</button><p>New? <b style="color:#ffd700;cursor:pointer" onclick="showRegister()">Register</b></p></div></div></div>
<div id="page-dash" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 40px"><div style="text-align:center"><h2 style="font-size:44px" id="welcomeText">Welcome 👑</h2><span style="padding:8px 18px;border-radius:20px;background:rgba(0,0,0,.6);border:2px solid #ffd700;font-size:14px;font-weight:900">⭐ RANK: <b id="myRank">#-</b></span><div id="dashLoanBox" style="margin-top:10px"></div></div><div class="grid"><div class="box" onclick="openRiddles()"><span>🧩</span><b>RIDDLES</b></div><div class="box" onclick="openBible()"><span>📖</span><b>BIBLE FIGHT</b></div><div class="box" onclick="openSciFi()"><span>🚀</span><b>SCI-FI</b></div><div class="box" onclick="openMessages()"><span>💚</span><b>WHATSAPP</b></div></div><div class="card"><h3 style="text-align:center;margin:0">🏆 TOP 5 🏆</h3><div id="leaderList">Loading...</div><button class="btn2" type="button" onclick="openFullLeader()">👀 Full Leaderboard</button></div><div class="card"><button class="btn" type="button" onclick="openBank()">💰 BANK</button><button class="btn" type="button" onclick="openShop()">🛍️ SHOP</button><button class="btn" type="button" onclick="openCrypto()">₿ CRYPTO</button><button class="btn" type="button" onclick="openNotifs()">✉️ NOTIFICATIONS</button><button class="btn" type="button" onclick="openLotteryPage()">🎰 LOTTERY</button><button class="btn2" type="button" onclick="openChallenge()">🎮 CHALLENGE</button></div></div>
<div id="page-leader" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 40px"><div class="card"><h3 style="text-align:center">🏆 LEADERBOARD</h3><div style="display:flex;gap:8px"><div class="tabBox" id="tabGold" onclick="setLeaderMode('gold')">🪙 Gold</div><div class="tabBox" id="tabGems" onclick="setLeaderMode('gems')">💎 Gem</div><div class="tabBox active" id="tabPvp" onclick="setLeaderMode('pvp')">⚔️ PvP (W-L)</div></div><div id="fullLeaderList" style="margin-top:10px">Loading...</div></div></div>
<div id="page-game" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 40px"><div class="card"><h2 id="gameTitle" style="text-align:center">Game</h2><div id="gameBody"></div></div></div>
<div id="page-coming" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 40px"><div class="card"><h2 style="text-align:center">🚀 SCI-FI - READY 25 DEC 2026</h2><p id="countDown" style="text-align:center;font-weight:900;color:#ffd700"></p><div id="scifiList"></div></div></div>
<div id="page-bank" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 40px"><div class="card"><h2 style="text-align:center">💰 BANK</h2><div class="walletCard"><div>🏦 BANK PROFILE</div><div id="bankIDShow">Bank INF-</div><div>🪙 Bank Gold: <b id="bankGold">0</b> | 💎 <b id="bankGems">0</b></div><div>Wallet — 🪙 <span id="walletGold">0</span> | 💎 <span id="walletGems">0</span></div><button class="btn" type="button" style="background:#00cc44" onclick="claimInterest()">🎁 Claim 10% Interest (Monthly)</button></div><div style="display:flex;gap:12px;margin-top:14px"><div style="flex:1"><div class="bigBankBox" onclick="openSendPage()">💸<br>Send</div><div class="bigBankBox" style="margin-top:10px" onclick="openExchangePage()">🔄<br>Exchange</div><div class="bigBankBox" style="margin-top:10px" onclick="openWithdrawPage()">🏧<br>Withdraw</div></div><div style="flex:1"><div class="bigBankBox" onclick="openDepositPage()">💰<br>Deposit</div><div class="bigBankBox loanGreen" style="margin-top:10px" onclick="openLoan()">🏦<br>LOAN</div><div class="bigBankBox" style="margin-top:10px" onclick="openCrypto()">₿<br>CRYPTO</div><div class="bigBankBox" style="margin-top:10px" onclick="openMyProfile()">👤<br>My Profile</div></div></div></div></div>
<div id="page-send" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 40px"><div class="card"><h2 style="text-align:center">💸 SEND GOLD</h2><div class="walletCard">🪙 <b id="sendPageGold">0</b> | 💎 <b id="sendPageGems">0</b><br>Your ID: <b id="sendPageMyID">INF-</b></div><div class="idPrefix"><b>INF-</b><input id="sendDigits" placeholder="12345678" inputmode="numeric" maxlength="8"></div><input id="sendAmt" type="number" placeholder="Amount"><button class="btn" type="button" onclick="doSend()">➤ SEND NOW</button></div></div>
<div id="page-withdraw" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 40px"><div class="card"><h2 style="text-align:center">🏧 WITHDRAW</h2><input id="withdrawAmt" type="number" placeholder="Amount"><select id="withdrawCur"><option>Gold</option><option>Gems</option></select><button class="btn" type="button" onclick="doWithdraw()">🏧 WITHDRAW</button></div></div>
<div id="page-deposit" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 40px"><div class="card"><h2 style="text-align:center">💰 DEPOSIT</h2><input id="depositAmt" type="number" placeholder="Amount"><select id="depositCur"><option>Gold</option><option>Gems</option></select><button class="btn" type="button" onclick="doDeposit()">💰 DEPOSIT</button></div></div>
<div id="page-exchange" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 40px"><div class="card"><h2 style="text-align:center">🔄 EXCHANGE</h2><div class="bigBankBox" onclick="openExchange('gold_to_gem')"><b>Gold &gt;&gt;&gt;&gt; Gem</b><br><small>100 Gold = 1 Gem</small></div><div class="bigBankBox" style="margin-top:10px" onclick="openExchange('gem_to_gold')"><b>Gem &gt;&gt;&gt;&gt; Gold</b></div><div id="exchangeForm"></div></div></div>
<div id="page-crypto" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 40px"><div class="card"><h2 style="text-align:center">₿ CRYPTO TRADE</h2><p style="text-align:center">🪙 Your Gold: <b id="cryptoGold">0</b></p><p style="text-align:center;font-size:12px">Prices move every refresh. Buy low, sell high. Holdings saved in DB.</p><div id="cryptoList">Loading prices...</div></div></div>
<div id="page-profile" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 40px"><div class="card" style="text-align:center"><div style="font-size:60px">👤</div><h2 id="profName">Player</h2><p id="profIDShow">ID:INF-</p><p id="profBankID">Bank INF-</p><p>⭐ Rank: <b id="profRank">#-</b></p><p>🏆 <b id="profWins">0</b> W | ❌ <b id="profLoss">0</b> L</p><p>🪙 Gold: <b id="profGold">0</b> | 💎 Gem: <b id="profGems">0</b></p><p>₿ Crypto: <b id="profCrypto">None</b></p><p>🚗 Cars: <b id="profCars">None</b></p><p>🌌 Galaxy: <b id="profGalaxy">1</b> | Kills: <b id="profGalaxyKills">0</b></p><div id="profLoanBox" style="background:#00ff88;color:#000;padding:12px;border-radius:14px;display:none"></div><button class="btn2" type="button" onclick="openSecret()">🔒 Secret</button></div><div class="card"><h3>👥 FRIENDS</h3><div id="profFriends">No friends yet</div><h3>📩 FRIEND REQUESTS</h3><div id="profFriendReqs">No requests</div></div><div class="card"><h3>🎒 INVENTORY</h3><div id="profInventory">No items</div><div id="consumeBox"></div></div></div>
<div id="page-other" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 40px"><div class="card" style="text-align:center"><h2 id="otherName">Player</h2><p>⭐ <b id="otherRank">#-</b></p><p>🏆 <b id="otherWins">0</b> W | ❌ <b id="otherLoss">0</b> L</p><div id="otherActions"></div></div></div>
<div id="page-notifs" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 40px"><div class="card"><h2 style="text-align:center">✉️ NOTIFICATIONS</h2><div id="notifList">No notifications</div></div></div>
<div id="page-economy" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 40px"><div class="card"><h2>💰 SERVER ECONOMY</h2><button id="emergencyBtn" class="btn" type="button" style="width:auto;background:#666" disabled onclick="doEmergency()">🚨 Emergency (Locked)</button><p id="ecoStatus" style="font-size:12px;color:#ffd700"></p><div class="grid"><div class="walletCard">Server Gold<br><b id="ecoGold">0</b></div><div class="walletCard">Server Gem<br><b id="ecoGems">0</b></div><div class="bigBankBox">🏦 Bank Gold<br><b id="ecoBankGold">0</b></div><div class="bigBankBox">🏦 Bank Gem<br><b id="ecoBankGems">0</b></div><div class="bigBankBox">🎰 Lottery<br><b id="ecoLottery">0</b></div><div class="bigBankBox">🛟 Backup<br><b id="ecoBackup">0</b></div></div><h3>₿ CRYPTO</h3><div id="ecoCryptoBox"></div><button class="btn" type="button" onclick="openCrypto()">₿ Open Crypto Trade</button><div id="ecoBackups"></div><h3>💰 SECRET REQUESTS</h3><div id="ecoRequests">No requests</div><h3>🏦 LOANS - PENDING ONLY</h3><div id="ecoLoans">No loans</div></div></div>
<div id="page-lottery" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 40px"><div class="card"><h2 style="text-align:center">🎰 LOTTERY</h2><input id="lotBet" type="number" placeholder="1000"><select id="lotCur"><option>Gold</option><option>Gems</option></select><button class="btn" type="button" onclick="playLottery()">🎰 SPIN</button><div id="lotResult" style="text-align:center"></div></div></div>
<div id="page-update" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 40px"><div class="card"><h2 style="text-align:center">🔄 UPDATE - DOMINIC ONLY</h2><button class="btn" type="button" onclick="doServerUpdate()">🚀 APPLY UPDATE</button><button class="btn" type="button" onclick="toggleGameSwitch()">🔌 SWITCH ON / OFF</button><button class="btn" type="button" onclick="openAnnounce()">📢 Announce</button></div></div>
<div id="page-server-info" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 40px"><div class="card"><h2 style="text-align:center">🖥️ SERVER INFO</h2><p>PLAYERS: <b id="serverPlayers">0</b></p><div id="serverBackups"></div><h3>📜 Reviews</h3><div id="serverReviewsList"></div></div></div>
<div id="page-review" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 40px"><div class="card"><h2 id="reviewTitle">⭐ Review</h2><textarea id="reviewText" style="height:140px"></textarea><button class="btn" type="button" onclick="submitReview()">📩 SEND</button></div></div>
<div id="page-challenge" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 40px"><div class="card"><h2 style="text-align:center">🎮 CHALLENGE</h2><div class="grid"><div class="box" onclick="hostPickMode('Bible Fight')"><span>📖</span><b>Bible</b></div><div class="box" onclick="hostPickMode('Riddles')"><span>🧩</span><b>Riddles</b></div><div class="box" onclick="hostPickMode('Galaxy Shooter')"><span>🌌</span><b>Galaxy</b></div><div class="box" onclick="hostPickMode('Decoding')"><span>💻</span><b>Decoding</b></div></div><button class="btn2" type="button" onclick="goDash()">❌ Decline</button></div></div>
<div id="page-messages" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 40px"><div class="card"><h1 style="text-align:center">💚 WhatsApp</h1><div style="display:flex;gap:8px"><div class="idPrefix" style="flex:1"><b>INF-</b><input id="addFriendDigits" placeholder="Add friend ID" inputmode="numeric" maxlength="8"></div><button class="btn" type="button" style="width:auto" onclick="sendFriendRequest()">➕ Send Request</button></div><div id="chatFriendList"></div></div></div>
<div id="page-chat" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 40px"><div class="card"><h2 style="text-align:center">💬 Chat - <span id="chatWith">Friend</span></h2><div id="chatBox" style="background:#1a1a2e;border-radius:20px;padding:12px;min-height:260px;max-height:360px;overflow-y:auto"></div><div style="display:flex;gap:8px;margin-top:10px"><input id="msgInput" placeholder="Message..." style="flex:1"><button class="btn" type="button" style="width:70px" onclick="sendMsg()">➤ Send</button></div></div></div>
<div id="page-shop" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 40px"><div class="card"><h2 style="text-align:center">🛍️ SHOP</h2><div style="display:flex;gap:6px"><div class="catTab" onclick="setShopCat('All')">All</div><div class="catTab" onclick="setShopCat('Cars')">Cars</div><div class="catTab" onclick="setShopCat('Food')">Food</div><div class="catTab" onclick="setShopCat('Tech')">Tech</div><div class="catTab" onclick="setShopCat('Pets')">Pets</div></div><div id="shopGrid" class="shopGrid" style="margin-top:12px"></div></div></div>
<div id="backFab" onclick="goBack()" style="position:fixed;left:16px;bottom:20px;width:58px;height:58px;border-radius:50%;background:#1a1a2e;display:none;align-items:center;justify-content:center;font-size:16px;color:#ffd700;border:3px solid #ffd700;cursor:pointer;z-index:150">← BACK</div>
<div id="announceBar" class="hidden" style="background:#ffd700;color:#000;padding:10px;text-align:center;font-weight:900;position:fixed;top:0;left:0;right:0;z-index:9999"></div>
<script>
// === CAT TIME - RUNS FIRST, NEVER BLOCKS ===
function pad2(v){return v<10?"0"+v:""+v}
function updateCatTime(){
  try{
    var n=new Date();
    try{
      var f=new Intl.DateTimeFormat("en-GB",{timeZone:"Africa/Lusaka",hour:"2-digit",minute:"2-digit",second:"2-digit",hour12:false});
      var d=new Intl.DateTimeFormat("en-GB",{timeZone:"Africa/Lusaka",weekday:"short",day:"2-digit",month:"short",year:"numeric"});
      var t=document.getElementById("catTime");if(t)t.textContent=f.format(n)+" CAT";
      var e=document.getElementById("catDate");if(e)e.textContent=d.format(n)+" - Central Africa";
      return;
    }catch(e2){}
    var h=n.getUTCHours()+2;if(h>=24)h-=24;if(h<0)h+=24;
    var t2=document.getElementById("catTime");if(t2)t2.textContent=pad2(h)+":"+pad2(n.getUTCMinutes())+":"+pad2(n.getUTCSeconds())+" CAT";
    var e2=document.getElementById("catDate");if(e2)e2.textContent="Central Africa - CAT (UTC+2)";
  }catch(e){}
}
updateCatTime();setInterval(updateCatTime,1000);
var _ac=null,soundOn=true;
function playPin(){try{if(!_ac)_ac=new (window.AudioContext||window.webkitAudioContext)();if(_ac.state==="suspended")_ac.resume();var o=_ac.createOscillator(),g=_ac.createGain();o.type="sine";o.frequency.value=880;g.gain.value=0.15;o.connect(g);g.connect(_ac.destination);o.start();o.stop(_ac.currentTime+0.15)}catch(e){}}
function hideMenu(){var d=document.getElementById("menuDrop");if(d){d.classList.add("hidden");d.style.display="none"}}
function showRegister(){var rf=document.getElementById("registerForm"),lf=document.getElementById("loginForm");if(rf){rf.classList.remove("hidden");rf.style.display="block"}if(lf){lf.classList.add("hidden");lf.style.display="none"}}
function showLogin(){var rf=document.getElementById("registerForm"),lf=document.getElementById("loginForm");if(rf){rf.classList.add("hidden");rf.style.display="none"}if(lf){lf.classList.remove("hidden");lf.style.display="block"}}
function welcomeChoice(c){try{playPin()}catch(e){}var o=document.getElementById("page-welcome");if(o){o.classList.add("hidden");o.style.display="none"}var reg=document.getElementById("page-register");if(reg){reg.classList.remove("hidden");reg.style.display="block"}var home=document.getElementById("page-home");if(home){home.classList.add("hidden");home.style.display="none"}if(c==="yes")showLogin();else showRegister()}
function enterClicked(){try{playPin()}catch(e){}hideMenu();var h=document.getElementById("page-home");if(h){h.classList.add("hidden");h.style.display="none"}var r=document.getElementById("page-register");if(r){r.classList.remove("hidden");r.style.display="block"}showRegister();var w=document.getElementById("page-welcome");if(w){w.classList.remove("hidden");w.style.display="flex"}}
document.addEventListener("click",function(e){var d=document.getElementById("menuDrop");var b=document.getElementById("menuBtn");if(d&&b&&!d.contains(e.target)&&e.target!==b){d.classList.add("hidden");d.style.display="none"}},true);
var user=null;try{user=JSON.parse(localStorage.getItem("inf_user")||"null")}catch(e){}
var wins=0,losses=0,myGold=0,myGems=0,myPlayerID="",myBankID="",myCars=[];try{var b2=JSON.parse(localStorage.getItem("inf_backup")||"{}");wins=parseInt(localStorage.getItem("inf_wins")||b2.wins||"0")||0;losses=parseInt(localStorage.getItem("inf_losses")||b2.losses||"0")||0;myGold=parseInt(localStorage.getItem("inf_gold")||b2.gold||"0")||0;myGems=parseInt(localStorage.getItem("inf_gems")||b2.gems||"0")||0;myPlayerID=localStorage.getItem("inf_player_id")||b2.player_id||"";myBankID=localStorage.getItem("inf_bank_id")||b2.bank_id||"";myCars=JSON.parse(localStorage.getItem("inf_cars")||JSON.stringify(b2.cars||[]))}catch(e){}
var loggedIn=false,currentPage="page-home",seenQs=[];try{seenQs=JSON.parse(localStorage.getItem("inf_seen")||"[]")}catch(e){}
var pinCb=null,leaderMode="pvp",chatWithName="",quizT=null,quizLeft=30,quizRound=[],quizIdx=0,quizScore=0,quizLoss=0,quizMode="",quizCat="",gameOn=true,shopCat="All",currentLoan=null,pendingLoanForDate=null,reviewType="review",cryptoPrices={BTC:85000,ETH:4200,DOGE:2},cryptoHold={BTC:0,ETH:0,DOGE:0};
var RB="BIBLE|In which book is vanity of vanities?|Ecclesiastes - Solomon|Genesis - Moses|Psalms - David;BIBLE|Only woman judge in Judges?|Deborah - Palm tree|Ruth - Oak tree|Esther - Cedar tree;BIBLE|How many years did Methuselah live?|969 years|777 years|856 years;BIBLE|3 men in fiery furnace?|Shadrach Meshach Abednego|Daniel Hananiah Mishael|Peter James John;BIBLE|High priest tore robes?|Caiaphas|Annas|Pilate;BIBLE|How many elders around throne?|24 elders|12 elders|7 elders;BIBLE|Only person both king and priest?|Melchizedek|David|Solomon;BIBLE|Weight of Goliath spearhead?|600 shekels - 15 lbs|100 shekels|300 shekels;BIBLE|Father of Caleb?|Jephunneh|Nun|Aaron;BIBLE|Moses father-in-law?|Jethro|Aaron|Hobab only;BIBLE|City first Gentile church?|Antioch|Jerusalem|Rome;BIBLE|What does Ebenezer mean?|Stone of Help - Samuel|Rock of Ages - David|House of God - Jacob;BIBLE|How many times Fear not?|365 times|100 times|50 times;BIBLE|Only apostle died natural death?|John|Peter|Paul;BIBLE|Demon called Legion?|Legion - we are many|Beelzebub|Lucifer;BIBLE|Longest chapter?|Psalm 119|Psalm 23|Genesis 1;BIBLE|Shortest chapter?|Psalm 117|Psalm 23|John 11;BIBLE|Man struck blind for Ark?|Uzzah|Aaron|Saul;BIBLE|Who built ark?|Noah|Moses|Abraham;BIBLE|Who defeated Goliath?|David|Samson|Saul;HARD|Always hungry must be fed, finger lick turns red|Fire|Water|Shadow;HARD|Brothers sisters I have none, that mans father is my fathers son, who in photo?|His son|His brother|His father;HARD|3 boxes labels all WRONG, pick 1 fruit, how fix?|Pick from box labeled both|Pick from apples box|Pick from oranges box;HARD|Plane crashes US-Canada border, bury survivors where?|Nowhere - survivors alive|Canada|USA;HARD|Rooster lays egg on roof, which side rolls?|Roosters dont lay eggs|Left side|Right side;HARD|Overtake person in 2nd place, what place?|2nd place|1st place|3rd place;HARD|What is 3/7 chicken, 2/3 cat, 1/2 goat?|Chicago|Chicatgo|London;HARD|Cowboy rides town Friday, stays 3 days, leaves Friday, how?|His horse named Friday|Time travels|Friday twice;HARD|Comes once in minute, twice in moment, never in thousand years?|Letter M|Letter O|Letter T;HARD|Man pushes car to hotel, tells owner bankrupt, why?|Playing Monopoly|Homeless|Car broke;HARD|Maker doesnt need, buyer doesnt use, user doesnt know?|A coffin|A gift|A car;HARD|Hold in right hand never left?|Your left hand|Your right hand|A pen;HARD|Cities no houses, forests no trees, water no fish?|A map|A dream|A book;HARD|Next: 1,11,21,1211,111221?|312211|121221|1112221;HARD|12 coins one fake, 3 weighs?|Divide 4-4-4 then 1-1 logic|Weigh all|Guess;HARD|Prisoner 2 doors, one lies one truth, one question?|Ask what would other say, pick opposite|Ask which is freedom|Ask your name;HARD|So fragile saying name breaks it?|Silence|Glass|Egg;HARD|Beginning of eternity, end of time, beginning of every end?|Letter E|Letter A|Letter T;HARD|Man dies old age on 25th birthday, how?|Born Feb 29|He lied|Sick;HARD|Head tail brown no legs?|A penny|A snake|A dog;LOVE|Not seen but felt, king kneel slave rise, given never taken?|Love|Money|Power;LOVE|Grows give away, dies hold tight, lives set free?|Love|Money|Fear;LOVE|Prison no bars, chain no iron, fire no flame, want stay?|Being in love|Jail|Hate;LOVE|Broken without touched, mended without fixed?|A heart|A glass|A bone;LOVE|Written without pen, spoken without voice, seen without eyes?|Love|Dream|Song;LOVE|Only war both win when surrender?|Love|Chess|Peace;LOVE|Make time stop and fly?|Love|Sleep|Work;LOVE|Both question and answer in 3 words?|I love you|How are you|I miss you;LOVE|Blind but sees everything?|Love|Justice|Night;LOVE|Both beginning and forever?|True love|Time|Death;LOVE|Make stranger feel home, home stranger when gone?|Love|Money|Fear;LOVE|Felt in heart measured in tears?|Love|Pain|Joy;LOVE|Both cure and disease?|Love|Medicine|Poison;LOVE|Light in darkness and darkness in light?|Love|Fire|Moon;LOVE|Make you lose yourself to find yourself?|Love|Travel|Sleep;LOGIC|100 prisoners 100 boxes, open 50, strategy >30%?|Loop strategy - own number follow chain|Open random|Open first 50;LOGIC|Bat and ball $1.10, bat $1 more, ball?|5 cents|10 cents|15 cents;LOGIC|3 numbers add 12 multiply 48?|2, 4, 6|1, 5, 6|3, 3, 6;LOGIC|What is half of 2+2?|3|2|4;LOGIC|Farmer 17 sheep, all but 9 die, left?|9|8|17;LOGIC|How many months have 28 days?|All 12|1 - February|2;LOGIC|3-gallon and 5-gallon measure 4?|Fill 5 pour into 3 leave 2, etc leaves 4|Fill both|Impossible;LOGIC|2 fathers 2 sons in car but only 3 people?|Grandfather father son|Twins|Two cars;LOGIC|5 machines 5 parts 5 min, 100 machines 100 parts?|5 minutes|100 minutes|20 minutes;LOGIC|Boat filled people sinks, no one dies, how?|Everyone married - no one single|Boat not real|They swam;LOGIC|Only word 3 consecutive double letters?|Bookkeeper|Mississippi|Balloon;LOGIC|Spelled same forwards backwards means race?|Racecar|Level|Madam;LOGIC|Number same letters as value?|Four - 4 letters|Three|Five;LOGIC|Man 3x son age, in 15 years twice, son now?|15 years old|10 years|20 years;LOGIC|Next letter O T T F F S S E ?|N - Nine|T - Ten|E - Eleven;LOGIC|How many times subtract 10 from 100?|Once - then 90|10 times|9 times;LOGIC|Has 4 letters, sometimes 9, never 5?|What - word play|Love|Time;LOGIC|Pass person in 2nd, what place?|2nd|1st|3rd;LOGIC|What runs but never walks?|Water|Man|Car;LOGIC|I speak without mouth?|Echo|Parrot|Radio;PROG|Why programmers mix Halloween and Christmas?|OCT 31 == DEC 25|Both holidays|They forget;PROG|10 types people understand binary and dont?|10 binary = 2|10 = ten|Joke;PROG|Output [] + [] in JS?|Empty string|0|NaN;PROG|What is 0.1+0.2?|0.30000000000000004|0.3|0.4;PROG|Why programmer died in shower?|Shampoo Lather Rinse Repeat loop|Water hot|Slipped;PROG|What is deadlock?|Two processes waiting each other forever|Computer crash|Bug;PROG|Difference bug vs feature?|Documentation|Nothing|Code;PROG|Null vs undefined JS?|Null intentionally empty, Undefined never assigned|Same|Opposite;PROG|What does !false equal?|true|false|0;PROG|Why NaN !== NaN?|NaN not equal itself IEEE 754|Bug|It is equal;PROG|What is recursion?|To understand recursion must first understand recursion|Loop|Function;PROG|Hardest problem in CS?|Naming cache off-by-one|Sorting|Memory;PROG|Output 1+1 in JS?|11 - string concatenation|2|1;PROG|Why developer go broke?|Used up all cache|Spent money|No job;PROG|DELETE vs TRUNCATE?|DELETE rollback WHERE, TRUNCATE drops all|Same|TRUNCATE slower;FUNNY|Why scarecrow win award?|Outstanding in his field|Tall|Scares birds;FUNNY|What call fish without eyes?|A fsh|A fish|Blind fish;FUNNY|Why coffee file police report?|It got mugged|Stolen|Cold;FUNNY|What call cheese not yours?|Nacho cheese|Cheddar|Mozzarella;FUNNY|Why bicycle fall over?|Two-tired|No wheels|Wind;FUNNY|What call can opener not work?|A cant opener|Broken opener|Tin opener;FUNNY|Why math book sad?|Too many problems|Heavy|No pages;FUNNY|What call bear no teeth?|A gummy bear|Brown bear|Polar bear;FUNNY|Why golfer bring two pants?|Hole in one|Cold|Fashion;FUNNY|Hardest riddle?|One you still thinking about|Number 1|Number 100";
var NEW100="NEW|I go in dry and come out wet, longer in stronger I get|A tea bag|A sponge|A towel;NEW|More you have of me less you see|Darkness|Light|Air;NEW|Head like cat feet like cat but not cat|A kitten|A puppy|A tiger;NEW|Can be cracked never break, told never speak|A code|A joke|An egg;NEW|Fly without wings cry without eyes|A cloud|A bird|A kite;NEW|Always with you never see in mirror|Your thoughts|Your shadow|Your back;NEW|What has 4 eyes but cant see|Mississippi - 4 Is|Potato|Spider;NEW|Start with T end with T full of T|A teapot|A tent|A tablet;NEW|What has 2 banks but no money|A river|A bank|A road;NEW|Tall young short old smaller as give light|A candle|A pencil|A tree;NEW|What put in bucket to make lighter|A hole|Air|Water;NEW|No wings fly no eyes cry no mouth whisper|Wind|Ghost|Cloud;NEW|Only thing goes up when comes down|An umbrella|A balloon|A rocket;NEW|Taken from mine locked in wood used by all|Pencil lead|Gold|Coal;NEW|Has tongue never tastes|A shoe|A bell|A spoon;NEW|Only thing go through door without opening it|Light|Keyhole|Air;NEW|Face never smiles but tells everything|A clock|A mirror|A book;NEW|Full of keys cant open door, space no room|A keyboard|A piano|A map;NEW|Always in middle of sea|The letter E|Water|Fish;NEW|Not alive but can die, no lungs need air|Fire|A flame|A car;NEW|Has neck no head wears cap|A bottle|A guitar|A shirt;NEW|Both place and thing you wear|A cap|A coat|A ring;NEW|Has heart beats but no blood|A drum|A heart|A clock;NEW|Always coming never arrive always leaving never go|Tomorrow|Time|Yesterday;NEW|Only thing both hot and cold|Water|Weather|Fire;NEW|Has body no soul head no brain|A doll|A robot|A statue;NEW|Both in past and future|A dream|A memory|A hope;NEW|Both question and statement|Why|What|How;NEW|Mouth never eats river never flows|A map|A jar|A book;NEW|Both color and fruit|Orange|Apple|Banana;NEW|Tail wags but no dog|A kite|A fish|A cat;NEW|Both weapon and tool|A knife|A hammer|A gun;NEW|Bed never sleeps mouth never talks|A river|A truck|A bed;NEW|Both star and fish|A starfish|A shark|A dolphin;NEW|Ring never fits finger|A tree ring|A phone ring|A bell;NEW|Both bird and fruit|A kiwi|A mango|A peach;NEW|Foot never walks head never thinks|A bed|A chair|A table;NEW|Both bank and river|A river bank|A bank|A stream;NEW|Face never frowns changes every day|A calendar|A clock|A mirror;NEW|Both game and animal|A bat|A ball|A cat;NEW|Back never bends face never smiles|A book|A chair|A wall;NEW|Both drink and color|Orange juice|Teal|Coffee;NEW|Tongue never talks tooth never bites|A zipper|A comb|A saw;NEW|Both vegetable and car|A beet|A carrot|A lemon;NEW|Nose never smells body never moves|A teapot|A doll|A statue;NEW|Both door and window|A glass door|A gate|A curtain;NEW|Hand never waves face never looks|A glove|A clock|A hand;NEW|Both light and heavy|A feather|A weight|A stone;NEW|Top never spins bottom never falls|A bottle cap|A lid|A hat;NEW|Both cat and dog|A hot dog|A catdog|A puppy;NEW|Key never opens lock never closes|A piano key|A keyboard|A door;NEW|Both snake and computer|Python|A cobra|A laptop;NEW|Head never hurts tail never wags|A hammer|A coin|A nail;NEW|Both flower and girl name|Rose|A lily|A daisy;NEW|Wing never flies beak never eats|A paper plane|A bird|A kite;NEW|Both day and night|Twilight|Dawn|Noon;NEW|Mouth never speaks ear never hears|A jug|A cup|A bottle;NEW|Both mountain and mole|A hill|A rock|A valley;NEW|Leg never runs arm never lifts|A chair|A table|A bed;NEW|Both sea and saw|A seasaw|A boat|A wave;NEW|Stomach never hungry mouth never eats|A bag|A box|A jar;NEW|Both ball and bell|A jingle bell|A basketball|A balloon;NEW|Tooth never hurts brush never paints|A comb|A toothbrush|A rake;NEW|Both pen and pig|A pigpen|A pen|A farm;NEW|Eye never blinks needle never sews|A storm|A potato|A needle;NEW|Both bear and bare|A bear|A bare|An animal;NEW|Horn never honks hoof never walks|A unicorn|A goat|A horse;NEW|Both rock and roll|Rock and roll|A stone|A music;NEW|Bark never bites leaf never falls|A tree|A dog|A book;NEW|Both lion and line|A lion|A line|A tiger;NEW|Shell never cracks yolk never cooks|A turtle|A snail|A nut;NEW|Both king and queen|A chess piece|A card|A crown;NEW|Root never grows branch never breaks|A family tree|A tree|A plant;NEW|Both cloud and crowd|A crowd|A cloud|A group;NEW|Wave never crashes hand never shakes|A goodbye wave|A wave|A hand;NEW|Both fire and fighter|A firefighter|A flame|A soldier;NEW|Cap never fits pen never writes|A mushroom|A hat|A pen;NEW|Both star and start|A star|A start|A sun;NEW|Bed never sleeps blanket never warms|A riverbed|A bed|A blanket;NEW|Both sun and son|Sun|A son|A moon;NEW|Nail never hurts hammer never hits|A fingernail|A nail|A toe;NEW|Both moon and spoon|Moon|A spoon|A star;NEW|Foot never steps yard never grows|A ruler|A yardstick|A foot;NEW|Both table and stable|A table|A stable|A chair;NEW|Heart never loves beat never stops|A metronome|A drum|A clock;NEW|Both cat and cap|Cat|A cap|A hat;NEW|Tail never wags head never thinks|A comet|A dog|A fish;NEW|Both rain and reign|Rain|A reign|A storm;NEW|Leg never walks foot never kicks|A table leg|A chair|A bed;NEW|Both well and wheel|Well|A wheel|A water;NEW|Smile never fades frown never appears|A photo|A Cheshire cat|A painting;NEW|Both ship and sheep|Ship|A sheep|A boat;NEW|Ear never hears corn never eats|An ear of corn|A corn|A ear;NEW|Both bat and ball|Bat|A ball|A game;NEW|Hole never leaks donut never eats|A donut hole|A donut|A hole;NEW|Both park and spark|Park|A spark|A car;NEW|Wing never flaps plane never flies|A building wing|A plane|A bird;NEW|Both rose and rise|Rose|A rise|A flower;NEW|Key never locks door never opens|A keyboard key|A key|A lock;NEW|Beginning of end end of time space essential to creation surround every place|The letter E|A circle|Time";
RB=RB+";"+NEW100;
function parseRB(){var o=[];RB.split(";").forEach(function(s){var p=s.split("|");if(p.length>=5)o.push({cat:p[0],q:p[1],a:p[2],w1:p[3],w2:p[4],id:p[0]+"|"+p[1]})});return o}
function isDom(){return user&&user.name&&user.name.toLowerCase()==="dominic"&&user.password==="2164"}
function toast(m){var t=document.getElementById("toast");if(!t)return;t.innerText=m;t.classList.remove("hidden");setTimeout(function(){t.classList.add("hidden")},4500)}
function showPage(id){hideMenu();if(quizT){clearInterval(quizT);quizT=null}currentPage=id;["page-home","page-register","page-dash","page-leader","page-game","page-coming","page-bank","page-send","page-withdraw","page-deposit","page-exchange","page-profile","page-other","page-notifs","page-economy","page-lottery","page-update","page-server-info","page-review","page-challenge","page-messages","page-chat","page-scifi","page-shop","page-crypto"].forEach(function(p){var e=document.getElementById(p);if(e){e.classList.add("hidden");e.style.display="none"}});var tg=document.getElementById(id);if(tg){tg.classList.remove("hidden");tg.style.display="block"}window.scrollTo(0,0);updateVisibility()}
function updateVisibility(){var r=document.getElementById("topRight"),b=document.getElementById("backFab");var isEnter=(currentPage==="page-home"||currentPage==="page-register");if(isEnter){if(r)r.style.display="none";if(b)b.style.display="none"}else if(loggedIn&&currentPage==="page-dash"){if(r)r.style.display="flex";if(b)b.style.display="none"}else if(loggedIn){if(r)r.style.display="none";if(b)b.style.display="flex"}else{if(r)r.style.display="none";if(b)b.style.display="none"}checkSwitch();checkLoanDue()}
function checkSwitch(){fetch("/api/switch_status").then(function(r){return r.json()}).then(function(d){gameOn=d.game_on!==false;var o=document.getElementById("frozenOverlay");if(!o)return;if(!gameOn){o.style.display="flex";document.getElementById("frozenDominicBox").style.display=isDom()?"block":"none"}else o.style.display="none"}).catch(function(){})}
function dominicUnfreeze(){var pin=document.getElementById("frozenPin").value.trim();if(pin!=="2164"){toast("Wrong PIN");return}fetch("/api/switch_toggle",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({admin:"dominic",pin:"2164",on:true})}).then(function(){gameOn=true;document.getElementById("frozenOverlay").style.display="none";toast("GAME ON")})}
function toggleGameSwitch(){if(!isDom()){toast("Dominic only");return}var wantOff=gameOn;if(!confirm(wantOff?"Turn OFF?":"Turn ON?"))return;openPin("PIN 2164 SWITCH "+(wantOff?"OFF":"ON"),function(pin){fetch("/api/switch_toggle",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({admin:"dominic",pin:pin,on:!wantOff})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}gameOn=d.game_on;toast(gameOn?"ON":"OFF");checkSwitch()})})}
function toggleSound(){soundOn=!soundOn;var b=document.getElementById("soundBtn");if(b)b.innerText=soundOn?"🔊 SOUND ON":"🔇 SOUND OFF";if(soundOn)playPin();toast(soundOn?"SOUND ON":"SOUND OFF")}
function goDash(){if(!loggedIn){showPage("page-register");return}showPage("page-dash");loadLeader()}
function goBack(){if(currentPage==="page-register")showPage("page-home");else if(currentPage==="page-chat")showPage("page-messages");else goDash()}
function saveLocal(){try{var bk={name:user?user.name:"",password:user?user.password:"",wins:wins,losses:losses,gold:myGold,gems:myGems,player_id:myPlayerID,bank_id:myBankID,cars:myCars,seen:seenQs};localStorage.setItem("inf_user",JSON.stringify(user));localStorage.setItem("inf_backup",JSON.stringify(bk));localStorage.setItem("inf_wins",wins);localStorage.setItem("inf_losses",losses);localStorage.setItem("inf_gold",myGold);localStorage.setItem("inf_gems",myGems);localStorage.setItem("inf_player_id",myPlayerID);localStorage.setItem("inf_bank_id",myBankID);localStorage.setItem("inf_seen",JSON.stringify(seenQs));localStorage.setItem("inf_cars",JSON.stringify(myCars))}catch(e){}}
function doLogout(){loggedIn=false;showPage("page-home");toast("Logged out - Data SAFE in DB.")}
function special(n,pw){var x=(n||"").toLowerCase().trim();if(x==="britney"||x==="kayula")return"Welcome MY Fiance 💖";if(x==="blessing")return"Welcome Avatar ✨";if(x==="lubuto")return"Welcome Desk Bender 🛠️";if(x==="dominic"&&pw==="2164")return"Welcome Infinity Emperor ♾";return"Welcome, "+n+" 👑"}
function doRegister(){var n=document.getElementById("regName").value.trim();var pw=document.getElementById("regPass").value.trim();if(!n||!pw||pw.length!==4||isNaN(pw)){toast("Name + 4-digit PIN");return}if(pw==="1234"||pw==="0000"){toast("Too easy");return}playPin();fetch("/api/player?name="+encodeURIComponent(n)).then(function(r){return r.json()}).then(function(d){if(d&&d.found){showLogin();document.getElementById("loginName").value=n;toast("Already exists! Just Login");return}user={name:n,password:pw};wins=0;losses=0;myGold=0;myGems=0;seenQs=[];myCars=[];saveLocal();syncScore();enterDash(special(n,pw))})}
function doLogin(){var n=document.getElementById("loginName").value.trim();var pw=document.getElementById("loginPass").value.trim();if(!n||!pw){toast("Name + Password");return}playPin();fetch("/api/player?name="+encodeURIComponent(n)+"&password="+encodeURIComponent(pw)).then(function(r){return r.json()}).then(function(d){if(d&&d.found&&d.password_ok!==false){user={name:n,password:pw};wins=d.wins||0;losses=d.losses||0;myGold=d.gold||0;myGems=d.gems||0;myPlayerID=d.player_id||"";myBankID=d.bank_id||"";seenQs=d.seen_qs||[];myCars=d.cars||[];saveLocal();enterDash(special(n,pw)+" - Restored ✅")}else if(d&&d.found===false){var b={};try{b=JSON.parse(localStorage.getItem("inf_backup")||"{}")}catch(e){}if(b.name&&b.name.toLowerCase()===n.toLowerCase()){toast("Restoring from phone backup...");fetch("/api/restore",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:n,password:pw,wins:b.wins||wins,losses:b.losses||losses,gold:b.gold||myGold,gems:b.gems||myGems,cars:b.cars||myCars,player_id:b.player_id||myPlayerID,bank_id:b.bank_id||myBankID})}).then(function(r){return r.json()}).then(function(rd){if(rd.found){user={name:n,password:pw};wins=rd.player.wins||0;losses=rd.player.losses||0;myGold=rd.player.gold||0;myGems=rd.player.gems||0;myPlayerID=rd.player.player_id||"";saveLocal();enterDash(special(n,pw)+" - RESTORED ✅")}else toast("Not found - Register")})}else toast("Wrong / Not found")}else toast("Wrong / Not found")})}
function enterDash(m){loggedIn=true;toast(m);playPin();showPage("page-dash");document.getElementById("welcomeText").innerText=m;loadLeader();loadMe();checkAnn()}
function syncScore(){if(!user)return;fetch("/api/score",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,password:user.password,wins:wins,losses:losses,gold:myGold,gems:myGems,seen_qs:seenQs,cars:myCars})}).catch(function(){})}
function loadMe(){if(!user)return;fetch("/api/player?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){if(!d||!d.found)return;myGold=d.gold;myGems=d.gems;myCars=d.cars||myCars;wins=d.wins;losses=d.losses;if(d.crypto)cryptoHold=d.crypto;saveLocal();var e=function(id,v){var x=document.getElementById(id);if(x)x.innerText=v};e("bankGold",d.bank_gold||0);e("bankGems",d.bank_gems||0);e("bankIDShow",d.bank_id||myBankID);e("walletGold",d.gold);e("walletGems",d.gems);var lb=document.getElementById("dashLoanBox");if(d.active_loan){lb.innerHTML="<div style='background:#00ff88;color:#000;padding:10px;border-radius:14px;font-size:12px;font-weight:900'>🏦 ACTIVE LOAN: "+d.active_loan.amount+" "+d.active_loan.currency+" - Repay by "+d.active_loan.repay_date+"<br><button class='btn' type='button' style='background:#000;color:#fff;padding:8px' onclick=\"payLoanNow('"+d.active_loan.id+"')\">💰 Pay Loan Now</button></div>"}else lb.innerHTML="";checkLoanDueWith(d.active_loan)});fetch("/api/leaderboard?mode=pvp").then(function(r){return r.json()}).then(function(d){var me=(d.players||[]).find(function(p){return p.name===user.name});if(me){var el=document.getElementById("myRank");if(el)el.innerText="#"+me.rank;var pr=document.getElementById("profRank");if(pr)pr.innerText="#"+me.rank}}})}
function loadLeader(){fetch("/api/leaderboard?mode=pvp").then(function(r){return r.json()}).then(function(d){var h="";(d.players||[]).slice(0,5).forEach(function(p,i){h+="<div class='leadRow' onclick=\"viewOther('"+p.name+"')\"><span>"+(i+1)+". "+p.name+(p.active_loan?" 🏦":"")+"</span><span>🏆 "+p.wins+"W | "+p.losses+"L</span></div>"});document.getElementById("leaderList").innerHTML=h||"No players"})}
function setLeaderMode(m){leaderMode=m;["gold","gems","pvp"].forEach(function(x){var el=document.getElementById("tab"+x.charAt(0).toUpperCase()+x.slice(1));if(el)el.classList.remove("active")});var a=document.getElementById("tab"+m.charAt(0).toUpperCase()+m.slice(1));if(a)a.classList.add("active");openFullLeader()}
function openFullLeader(){showPage("page-leader");fetch("/api/leaderboard?mode="+leaderMode).then(function(r){return r.json()}).then(function(d){var h="";(d.players||[]).forEach(function(p,i){h+="<div class='leadRow' onclick=\"viewOther('"+p.name+"')\"><span>"+(i+1)+". "+p.name+"<br><small>"+p.player_id+(p.active_loan?" | 🏦 Has Loan":"")+"</small></span><span>"+(leaderMode==="gold"?"🪙 "+p.gold+"<br><small>"+p.wins+"W | "+p.losses+"L</small>":leaderMode==="gems"?"💎 "+p.gems+"<br><small>"+p.wins+"W | "+p.losses+"L</small>":"🏆 "+p.wins+"W | "+p.losses+"L")+"</span></div>"});document.getElementById("fullLeaderList").innerHTML=h||"No players"})}
function viewOther(name){fetch("/api/player?name="+encodeURIComponent(name)).then(function(r){return r.json()}).then(function(d){showPage("page-other");document.getElementById("otherName").innerText=d.name;fetch("/api/leaderboard?mode=pvp").then(function(rr){return rr.json()}).then(function(dd){var me=(dd.players||[]).find(function(p){return p.name===name});if(me)document.getElementById("otherRank").innerText="#"+me.rank});document.getElementById("otherWins").innerText=d.wins;document.getElementById("otherLoss").innerText=d.losses;document.getElementById("otherActions").innerHTML="<button class='btn' type='button' onclick=\"openBankSendTo('"+d.player_id+"')\">💸 Send Gold</button><button class='btn2' type='button' onclick=\"sendFriendTo('"+d.player_id+"')\">👥 Send Friend Request</button>"})}
function openMyProfile(){if(!user)return;showPage("page-profile");fetch("/api/player?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){document.getElementById("profName").innerText=special(d.name,user.password);document.getElementById("profIDShow").innerText="ID:"+d.player_id;document.getElementById("profBankID").innerText=d.bank_id;document.getElementById("profWins").innerText=d.wins;document.getElementById("profLoss").innerText=d.losses;document.getElementById("profGold").innerText=d.gold;document.getElementById("profGems").innerText=d.gems;var cr="";if(d.crypto){for(var k in d.crypto){if(d.crypto[k]>0)cr+=k+": "+d.crypto[k]+" "}}document.getElementById("profCrypto").innerText=cr||"None";document.getElementById("profCars").innerText=(d.cars||[]).join(", ")||"None";document.getElementById("profGalaxy").innerText=d.galaxy_level||1;document.getElementById("profGalaxyKills").innerText=d.galaxy_kills||0;var lb=document.getElementById("profLoanBox");if(d.active_loan){lb.style.display="block";lb.innerHTML="🏦 ACTIVE LOAN<br>"+d.active_loan.amount+" "+d.active_loan.currency+"<br>Repay by: "+d.active_loan.repay_date+"<br><button class='btn' type='button' onclick=\"payLoanNow('"+d.active_loan.id+"')\">💰 Pay Now</button>"}else lb.style.display="none";var fh="";(d.friends||[]).forEach(function(f){fh+="<div style='padding:10px;background:rgba(0,0,0,.4);border-radius:12px;margin:6px 0;display:flex;justify-content:space-between'><span>👥 "+f+"</span><button class='btn' type='button' style='width:auto;padding:6px 10px' onclick=\"openChatWith('"+f+"')\">💬 Chat</button></div>"});document.getElementById("profFriends").innerHTML=fh||"No friends yet";var rh="";(d.friend_requests||[]).forEach(function(rq){rh+="<div style='padding:10px;background:rgba(255,215,0,.2);border-radius:12px;margin:6px 0'>👥 "+rq.from+"<br><button class='btn' type='button' onclick=\"respondFriend('"+rq.id+"',true)\">✅ Accept</button><button class='btn2' type='button' onclick=\"respondFriend('"+rq.id+"',false)\">❌ Decline</button></div>"});document.getElementById("profFriendReqs").innerHTML=rh||"No pending requests";var inv=d.items||[];var h="";inv.forEach(function(it){h+="<div style='padding:10px;background:rgba(0,0,0,.4);border-radius:12px;margin:6px 0'>🎒 "+it+"</div>"});document.getElementById("profInventory").innerHTML=h||"No items";var cb=document.getElementById("consumeBox");var drink=inv.find(function(x){return /Cola|Juice|Drink/.test(x)});var food=inv.find(function(x){return /Burger|Pizza|Donut/.test(x)});var h2="";if(drink)h2+="<button class='btn' type='button' onclick=\"consumeP('"+drink+"')\">🥤 Drink "+drink+"</button>";if(food)h2+="<button class='btn2' type='button' onclick=\"consumeP('"+food+"')\">🍔 Eat "+food+"</button>";cb.innerHTML=h2})}
function respondFriend(id,ok){fetch("/api/friend_respond",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,request_id:id,accept:ok})}).then(function(){toast(ok?"✅ Friend Accepted":"❌ Declined");openMyProfile()})}
function sendFriendTo(pid){fetch("/api/friend_request",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,target_id:pid})}).then(function(r){return r.json()}).then(function(d){toast(d.error||"✅ Friend Request Sent")})}
function sendFriendRequest(){var dg=document.getElementById("addFriendDigits").value.replace(/[^0-9]/g,"");if(dg.length!==8){toast("8 digits");return}sendFriendTo("INF-"+dg)}
function consumeP(p){openPin("PIN consume "+p,function(pin){var b=[20,50,100][Math.floor(Math.random()*3)];fetch("/api/consume",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,product:p,bonus:b})}).then(function(r){return r.json()}).then(function(d){wins=d.wins;saveLocal();syncScore();toast("😋 +"+b+" Wins");openMyProfile()})})}
function openSecret(){var o=document.getElementById("secretOverlay");o.classList.remove("hidden");o.style.display="flex"}
function closeSecret(){var o=document.getElementById("secretOverlay");o.classList.add("hidden");o.style.display="none"}
function sendMoneyRequest(){var m=document.getElementById("reqMsg").value;var a=document.getElementById("reqAmt").value;var c=document.getElementById("reqCur").value;closeSecret();fetch("/api/request_money",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,amount:a||"",currency:c,message:m})}).then(function(){toast("🔒 Secret sent")})}
function openBank(){showPage("page-bank");loadMe()}
function claimInterest(){openPin("PIN Claim 10% Interest",function(pin){fetch("/api/bank_interest",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}toast("🎁 +10%: +"+d.bonus_gold+" Gold, +"+d.bonus_gems+" Gems");loadMe()})})}
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
function openEconomy(){if(!isDom()){toast("Dominic only");return}showPage("page-economy");fetch("/api/economy?name=dominic&password=2164").then(function(r){return r.json()}).then(function(d){var e=d.economy;document.getElementById("ecoGold").innerText=e.gold;document.getElementById("ecoGems").innerText=e.gems;document.getElementById("ecoBankGold").innerText=e.bank_gold;document.getElementById("ecoBankGems").innerText=e.bank_gems;document.getElementById("ecoLottery").innerText=e.lottery||0;document.getElementById("ecoBackup").innerText=e.backup||0;document.getElementById("ecoStatus").innerText=e.gold<0?"⚠️ NEGATIVE - Emergency unlocked":"✅ Economy Healthy";document.getElementById("emergencyBtn").disabled=e.gold>=0;document.getElementById("emergencyBtn").style.background=e.gold<0?"#ff2222":"#666";var cb="";if(e.crypto){for(var k in e.crypto)cb+=k+": "+e.crypto[k]+" Gold "}document.getElementById("ecoCryptoBox").innerText=cb;var h="";(d.backups||[]).forEach(function(b){h+="<div>"+b.file+" - Players: "+b.players+" - Exists: "+b.exists+"</div>"});document.getElementById("ecoBackups").innerHTML=h;var rh="";(d.requests||[]).forEach(function(rq){rh+="<div style='padding:10px;background:rgba(0,0,0,.4);border-radius:12px;margin:6px 0'>🔒 "+rq.from+" wants "+rq.amount+" "+rq.currency+"</div>"});document.getElementById("ecoRequests").innerHTML=rh||"No requests";var lh="";(d.loans||[]).forEach(function(l){lh+="<div style='padding:10px;background:rgba(0,0,0,.4);border-radius:12px;margin:6px 0'>🏦 "+l.from+" - "+l.amount+" "+l.currency+" repay "+l.repay_date+"<br><input type='date' id='ecoDate_"+l.id+"' value='"+l.repay_date+"'><button class='btn' type='button' onclick=\"dominicLoanEco('"+l.id+"',true)\">Approve</button></div>"});document.getElementById("ecoLoans").innerHTML=lh||"No loans"})}
function dominicLoanEco(id,ok){var dt=document.getElementById("ecoDate_"+id).value;openPin("PIN Dominic",function(pin){fetch("/api/loan_dominic",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({admin:"dominic",pin:pin,loan_id:id,approve:ok,new_date:dt})}).then(function(r){return r.json()}).then(function(d){toast(d.error||"✅ Done");openEconomy()})})}
function doEmergency(){openPin("PIN Emergency",function(pin){fetch("/api/emergency",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:"dominic",pin:pin})}).then(function(r){return r.json()}).then(function(d){toast(d.error||"🚨 Emergency Reset Done");openEconomy()})})}
function openAnnounce(){if(!isDom()){toast("Dominic only");return}hideMenu();var o=document.getElementById("announceOverlay");o.classList.remove("hidden");o.style.display="flex"}
function closeAnnounce(){var o=document.getElementById("announceOverlay");o.classList.add("hidden");o.style.display="none"}
function sendAnnounce(){var t=document.getElementById("annText").value.trim();if(!t){toast("Write announcement");return}closeAnnounce();fetch("/api/announce",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({admin:"dominic",pin:"2164",text:t})}).then(function(){toast("📢 Announced");document.getElementById("annText").value=""})}
function checkAnn(){fetch("/api/announcements").then(function(r){return r.json()}).then(function(d){var a=(d.announcements||[]).slice(-1)[0];if(a){var b=document.getElementById("announceBar");b.innerText="📢 "+a.text;b.classList.remove("hidden");setTimeout(function(){b.classList.add("hidden")},6000)}}).catch(function(){})}
function openUpdate(){if(!isDom()){toast("Dominic only");return}showPage("page-update")}
function doServerUpdate(){toast("🚀 Already on v44 - Latest");checkSwitch()}
function openServerInfo(){if(!isDom()){toast("Dominic only");return}showPage("page-server-info");fetch("/api/server_info?name=dominic&password=2164").then(function(r){return r.json()}).then(function(d){document.getElementById("serverPlayers").innerText=d.players;var h="";(d.backups||[]).forEach(function(b){h+="<div>"+b.file+" - "+b.players+" players</div>"});document.getElementById("serverBackups").innerHTML=h;var rh="";(d.reviews||[]).forEach(function(rv){rh+="<div style='padding:8px;background:rgba(0,0,0,.4);border-radius:10px;margin:5px 0'>"+(rv.name||"")+" - "+(rv.text||"")+"</div>"});document.getElementById("serverReviewsList").innerHTML=rh||"No reviews"})}
function openReview(t){reviewType=t||"review";document.getElementById("reviewTitle").innerText="⭐ Review";showPage("page-review")}
function submitReview(){var t=document.getElementById("reviewText").value.trim();if(!t){toast("Write something");return}fetch("/api/review",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user?user.name:"Guest",type:reviewType,text:t})}).then(function(){document.getElementById("reviewText").value="";toast("✅ Review Sent");goDash()})}
function openChallenge(){showPage("page-challenge")}
function hostPickMode(m){if(m==="Bible Fight")openBible();else if(m==="Riddles")openRiddles();else if(m==="Galaxy Shooter")openSciFi();else{toast("💻 Decoding - Coming Soon");goDash()}}
function openRiddles(){showPage("page-game");document.getElementById("gameTitle").innerText="🧩 Choose Riddle Type";document.getElementById("gameBody").innerHTML="<button class='btn' type='button' onclick=\"startQuiz('Riddles','NEW')\">✨ NEW 100 Riddles</button><button class='btn' type='button' onclick=\"startQuiz('Riddles','HARD')\">🧠 Hard Riddles</button><button class='btn' type='button' onclick=\"startQuiz('Riddles','LOVE')\">💖 Love```js
Riddles</button><button class='btn' type='button' onclick="startQuiz('Riddles','LOGIC')">🧮 Logic / Smart</button><button class='btn' type='button' onclick="startQuiz('Riddles','PROG')">💻 Programmers</button><button class='btn' type='button' onclick="startQuiz('Riddles','FUNNY')">😂 Funny</button><button class='btn2' type='button' onclick='goDash()'>Back</button>"}
function openBible(){startQuiz("Bible Fight","BIBLE")}
function startQuiz(mode,cat){quizMode=mode;quizCat=cat;quizScore=0;quizLoss=0;quizIdx=0;var all=parseRB().filter(function(x){return x.cat===cat});var fresh=all.filter(function(x){return seenQs.indexOf(x.id)===-1});if(fresh.length<10){seenQs=seenQs.filter(function(s){return s.indexOf(cat+"|")!==0});fresh=all.slice();toast("🔄 Category reset - fresh round")}fresh.sort(function(){return Math.random()-0.5});quizRound=fresh.slice(0,10);showPage("page-game");document.getElementById("gameTitle").innerText=(mode==="Bible Fight"?"📖 Bible Fight":"🧩 Riddles - "+cat)+" - Q 1 / 10";showQuizQ()}
function showQuizQ(){if(quizIdx>=quizRound.length){if(quizT){clearInterval(quizT);quizT=null}document.getElementById("gameBody").innerHTML="<h2 style='text-align:center'>🏁 Finished!</h2><p style='text-align:center'>✅ Correct: "+quizScore+"<br>❌ Wrong: "+quizLoss+"</p><button class='btn' type='button' onclick='goDash()'>🏠 Home</button><button class='btn2' type='button' onclick=\"openRiddles()\">🧩 Play Again</button>";wins+=quizScore;losses+=quizLoss;saveLocal();syncScore();return}var it=quizRound[quizIdx];document.getElementById("gameTitle").innerText=(quizMode==="Bible Fight"?"📖 Bible Fight":"🧩 Riddles - "+quizCat)+" - Q "+(quizIdx+1)+" / 10 - ✅ "+quizScore+" ❌ "+quizLoss;var opts=[it.a,it.w1,it.w2].sort(function(){return Math.random()-0.5});var h="<p style='font-size:18px;font-weight:900'>"+it.q+"</p><p>⏱️ <b id='quizTime'>30</b>s left</p><div class='timerBar'><div id='quizBar' class='timerFill' style='width:100%'></div></div>";opts.forEach(function(o){h+="<button class='opt' type='button' onclick=\"answerQuiz(this,'"+o.replace(/'/g,"\\'").replace(/\"/g,"&quot;")+"')\">"+o+"</button>"});document.getElementById("gameBody").innerHTML=h;quizLeft=30;if(quizT)clearInterval(quizT);quizT=setInterval(function(){quizLeft--;var t=document.getElementById("quizTime");if(t)t.innerText=quizLeft;var b=document.getElementById("quizBar");if(b)b.style.width=(quizLeft/30*100)+"%";if(quizLeft<=0){clearInterval(quizT);quizT=null;toast("⏰ Time up! -1 Loss");quizLoss++;seenQs.push(it.id);saveLocal();quizIdx++;showQuizQ()}},1000)}
function answerQuiz(btn,ans){if(quizT){clearInterval(quizT);quizT=null}var it=quizRound[quizIdx];seenQs.push(it.id);if(ans===it.a){quizScore++;toast("✅ Correct! +1 Win")}else{quizLoss++;toast("❌ Wrong! Answer: "+it.a)}saveLocal();quizIdx++;setTimeout(showQuizQ,800)}
function openSciFi(){showPage("page-coming");var target=new Date("2026-12-25T00:00:00");var now=new Date();var diff=target-now;var days=Math.floor(diff/86400000);document.getElementById("countDown").innerText=days>0?days+" days left":"🚀 Coming Soon";var sc=document.getElementById("scifiList");if(sc)sc.innerHTML="<button class='btn' type='button' onclick=\"openBible()\">📖 Bible Fight</button><button class='btn' type='button' onclick=\"openRiddles()\">🧩 Riddles</button>"}
function setShopCat(c){shopCat=c;renderShop()}
function openShop(){showPage("page-shop");renderShop()}
function renderShop(){var items=[["Toyota Corolla",5000,"Cars","🚗"],["BMW M4",20000,"Cars","🚗"],["Lamborghini",80000,"Cars","🏎️"],["Ferrari",90000,"Cars","🏎️"],["Tesla Model S",60000,"Cars","🚗"],["Mercedes G",70000,"Cars","🚗"],["Audi R8",75000,"Cars","🚗"],["Range Rover",65000,"Cars","🚗"],["Burger",500,"Food","🍔"],["Pizza",800,"Food","🍕"],["Donut",300,"Food","🍩"],["Cola Drink",200,"Food","🥤"],["Juice Drink",250,"Food","🧃"],["iPhone",15000,"Tech","📱"],["Laptop",25000,"Tech","💻"],["Headphones",5000,"Tech","🎧"],["Dog Pet",10000,"Pets","🐶"],["Cat Pet",8000,"Pets","🐱"]];var h="";items.forEach(function(it){if(shopCat!=="All"&&it[2]!==shopCat)return;var owned=(myCars.indexOf(it[0])!==-1);h+="<div class='shopBox'>"+it[3]+"<br><b>"+it[0]+"</b><br>🪙 "+it[1]+"<br><button class='btn' type='button' style='padding:8px' onclick=\"buyShopItem('"+it[0]+"',"+it[1]+")\">"+(owned?"✅ Owned":"🛒 Buy")+"</button></div>"});document.getElementById("shopGrid").innerHTML=h;document.querySelectorAll(".catTab").forEach(function(t){t.classList.toggle("active",t.innerText.trim()===shopCat)})}
function buyShopItem(name,price){if(myCars.indexOf(name)!==-1){toast("Already owned");return}openPin("PIN Buy "+name,function(pin){fetch("/api/buy_item",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,item:name,price:price})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.gold;myCars.push(name);saveLocal();toast("✅ Bought "+name);renderShop()})})}
function openMessages(){showPage("page-messages");fetch("/api/friends?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){var h="";(d.friends||[]).forEach(function(f){h+="<div style='padding:12px;background:rgba(0,0,0,.4);border-radius:12px;margin:6px 0;display:flex;justify-content:space-between'><span>👥 "+f.name+"</span><button class='btn' type='button' style='width:auto;padding:6px 12px' onclick=\"openChatWith('"+f.name+"')\">💬 Chat</button></div>"});document.getElementById("chatFriendList").innerHTML=h||"No friends yet - add by ID above"})}
function openChatWith(name){chatWithName=name;showPage("page-chat");document.getElementById("chatWith").innerText=name;loadChat()}
function loadChat(){if(!chatWithName)return;fetch("/api/chat_get?a="+encodeURIComponent(user.name)+"&b="+encodeURIComponent(chatWithName)).then(function(r){return r.json()}).then(function(d){var h="";(d.messages||[]).forEach(function(m){h+="<div style='padding:8px;margin:5px 0;border-radius:12px;background:"+(m.from===user.name?"#00cc44":"#333")+"'><b>"+m.from+":</b> "+m.text+"</div>"});document.getElementById("chatBox").innerHTML=h||"No messages yet";var cb=document.getElementById("chatBox");cb.scrollTop=cb.scrollHeight})}
function sendMsg(){var t=document.getElementById("msgInput").value.trim();if(!t||!chatWithName)return;document.getElementById("msgInput").value="";fetch("/api/chat_send",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({sender:user.name,to:chatWithName,text:t})}).then(function(){loadChat()})}
function openPin(desc,cb){pinCb=cb;document.getElementById("pinDesc").innerText=desc||"Enter PIN";document.getElementById("pinInput").value="";var o=document.getElementById("pinOverlay");o.classList.remove("hidden");o.style.display="flex"}
function closePin(){pinCb=null;var o=document.getElementById("pinOverlay");o.classList.add("hidden");o.style.display="none"}
function confirmPin(){var pin=document.getElementById("pinInput").value.trim();if(pin.length!==4){toast("4-digit PIN");return}var cb=pinCb;closePin();if(cb)cb(pin)}
function openCrypto(){showPage("page-crypto");fetch("/api/crypto?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){cryptoPrices=d.prices;cryptoHold=d.holdings;document.getElementById("cryptoGold").innerText=d.gold;var h="";for(var k in d.prices){h+="<div style='padding:12px;background:rgba(0,0,0,.4);border-radius:14px;margin:8px 0'><b>"+k+"</b> - "+d.prices[k]+" Gold<br>You hold: "+(d.holdings[k]||0)+" "+k+"<br><input type='number' id='cr_"+k+"' placeholder='Amount e.g. 0.01' step='any'><div style='display:flex;gap:8px'><button class='btn' type='button' onclick=\"cryptoTrade('"+k+"','buy')\">Buy</button><button class='btn2' type='button' onclick=\"cryptoTrade('"+k+"','sell')\">Sell</button></div></div>"}document.getElementById("cryptoList").innerHTML=h})}
function cryptoTrade(coin,action){var amt=parseFloat(document.getElementById("cr_"+coin).value||"0");if(!amt||amt<=0){toast("Enter amount");return}openPin("PIN Crypto "+action+" "+coin,function(pin){fetch("/api/crypto_trade",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,coin:coin,amount:amt,action:action})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.gold;saveLocal();toast("Crypto "+action+" done");openCrypto()})})}
function playLottery(){var bet=parseInt(document.getElementById("lotBet").value||"0");var cur=document.getElementById("lotCur").value;openPin("PIN Lottery "+bet,function(pin){fetch("/api/lottery",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,bet:bet,currency:cur})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.gold;myGems=d.gems;saveLocal();document.getElementById("lotResult").innerHTML=d.result.win?"WON +"+d.result.prize:"Lost"})})}
function setupMenu(){var b=document.getElementById("menuBtn");if(!b)return;b.onclick=function(e){e.stopPropagation();var d=document.getElementById("menuDrop");if(!d)return;if(!d.classList.contains("hidden")){hideMenu();return}var items="";if(isDom())items+="<div onclick=\"openEconomy()\">💰 Server Economy</div><div onclick=\"openServerInfo()\">🖥️ Server Info</div><div onclick=\"openUpdate()\">🔄 Update</div><div onclick=\"openAnnounce()\">📢 Announce</div>";items+="<div onclick=\"openMyProfile()\">👤 My Profile</div><div onclick=\"openBank()\">💰 Bank</div><div onclick=\"openCrypto()\">₿ Crypto Trade</div><div onclick=\"openShop()\">🛍️ Shop</div><div onclick=\"openRiddles()\">🧩 Riddles</div><div onclick=\"openBible()\">📖 Bible Fight</div><div onclick=\"openMessages()\">💚 WhatsApp</div><div onclick=\"playLotteryPage()\">🎰 Lottery</div><div onclick=\"openNotifs()\">✉️ Notifications</div><div onclick=\"openReview()\">⭐ Review</div><div onclick=\"doLogout()\">Logout</div>";d.innerHTML=items;d.classList.remove("hidden");d.style.display="block"}}
function playLotteryPage(){showPage("page-lottery")}
function toggleMenu(e){setupMenu();var b=document.getElementById("menuBtn");if(b&&b.onclick)b.onclick(e)}
setupMenu();
if(user&&user.name){loggedIn=false;showPage("page-home")}
</script>
</body></html>"""
if __name__=="__main__":
 import os
 port=int(os.environ.get("PORT",5000))
 app.run(host="0.0.0.0",port=port)
