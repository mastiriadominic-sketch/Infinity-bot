
import os, json, random
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, make_response

app = Flask(__name__)
DATA_FILE = "data.json"
DATA = {"players": {}, "loans": [], "requests": [], "announcements": [], "reviews": [], "chats": {}, "economy": {"gold": 0, "gems": 0, "bank_total": 0, "fees": 0, "lottery": 0, "backup": 0, "history": [100, 120, 110, 130]}}

def load():
    global DATA
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                d = json.load(f)
                for k in DATA:
                    if k in d:
                        DATA[k] = d[k]
    except Exception:
        pass

def save():
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(DATA, f)
    except Exception:
        pass

load()

def norm(s):
    return str(s or "").strip().lower()

def getp(name):
    if not name:
        return None
    for k, v in DATA["players"].items():
        if norm(k) == norm(name):
            return v
    return None

def new_player(name, pw):
    pid = "INF-" + str(random.randint(10000000, 99999999))
    bid = "BANK INF-" + str(random.randint(10000000, 99999999))
    p = {"name": name, "display_name": name, "password": str(pw), "player_id": pid, "bank_id": bid, "wins": 0, "losses": 0, "gold": 0, "gems": 0, "bank_gold": 0, "bank_gems": 0, "cars": [], "items": [], "seen_qs": [], "galaxy_level": 1, "galaxy_kills": 0, "notifs": [], "friends": [], "loans": [], "rank": 0, "classified": False}
    DATA["players"][name] = p
    save()
    return p

def check_pin(v, pin):
    if not v:
        return False
    if norm(v.get("name")) == "dominic":
        return str(pin) == "2164"
    return str(pin) == str(v.get("password"))

def notify(name, text, typ="info", extra=None):
    v = getp(name)
    if not v:
        if norm(name) == "dominic" and "dominic" not in DATA["players"]:
            new_player("dominic", "2164")
            v = getp("dominic")
        else:
            return
    n = {"text": text, "type": typ, "time": datetime.now().strftime("%H:%M %d %b")}
    if extra:
        n.update(extra)
    v.setdefault("notifs", []).append(n)
    save()

def find_by_id(pid):
    pid = str(pid).upper().replace("BANK ", "")
    if not pid.startswith("INF-"):
        pid = "INF-" + pid
    for v in DATA["players"].values():
        if v.get("player_id") == pid or v.get("bank_id") == pid:
            return v
    return None

@app.route("/")
def home():
    return make_response(HOME, 200, {"Content-Type": "text/html"})

@app.route("/api/player")
def api_player():
    name = request.args.get("name", "")
    pw = request.args.get("password", "")
    v = getp(name)
    if not v:
        return jsonify({"found": False})
    if pw and str(pw) != str(v.get("password")):
        return jsonify({"found": True, "password_ok": False})
    return jsonify({"found": True, "password_ok": True, "name": v["name"], "player_id": v.get("player_id"), "bank_id": v.get("bank_id"), "wins": v.get("wins", 0), "losses": v.get("losses", 0), "gold": v.get("gold", 0), "gems": v.get("gems", 0), "bank_gold": v.get("bank_gold", 0), "bank_gems": v.get("bank_gems", 0), "cars": v.get("cars", []), "items": v.get("items", []), "seen_qs": v.get("seen_qs", []), "galaxy_level": v.get("galaxy_level", 1), "galaxy_kills": v.get("galaxy_kills", 0), "notifs": v.get("notifs", [])[-30:], "loans": [x for x in DATA["loans"] if norm(x.get("from")) == norm(name)], "rank": v.get("rank", 0), "classified": False})

@app.route("/api/score", methods=["POST"])
def api_score():
    d = request.get_json() or {}
    v = getp(d.get("name"))
    if not v:
        v = new_player(d.get("name", "Player"), d.get("password", "0000"))
    if str(d.get("password", "")) != str(v.get("password")) and norm(d.get("name")) != "dominic":
        pass
    v["wins"] = int(d.get("wins", v.get("wins", 0)))
    v["losses"] = int(d.get("losses", v.get("losses", 0)))
    v["gold"] = int(d.get("gold", v.get("gold", 0)))
    v["gems"] = int(d.get("gems", v.get("gems", 0)))
    if d.get("seen_qs") is not None:
        v["seen_qs"] = d.get("seen_qs")
    if d.get("cars") is not None:
        v["cars"] = d.get("cars")
    if d.get("galaxy_level") is not None:
        v["galaxy_level"] = d.get("galaxy_level")
    if d.get("galaxy_kills") is not None:
        v["galaxy_kills"] = d.get("galaxy_kills")
    save()
    return jsonify({"ok": True})

@app.route("/api/leaderboard")
def api_leader():
    mode = request.args.get("mode", "pvp")
    ps = list(DATA["players"].values())
    if mode == "gold":
        ps.sort(key=lambda x: x.get("gold", 0), reverse=True)
    elif mode == "gems":
        ps.sort(key=lambda x: x.get("gems", 0), reverse=True)
    elif mode == "rank":
        ps.sort(key=lambda x: x.get("wins", 0), reverse=True)
    else:
        ps.sort(key=lambda x: x.get("wins", 0), reverse=True)
    out = []
    for i, p in enumerate(ps[:50]):
        out.append({"name": p["name"], "player_id": p.get("player_id"), "wins": p.get("wins", 0), "losses": p.get("losses", 0), "gold": p.get("gold", 0), "gems": p.get("gems", 0), "rank": i + 1})
    return jsonify({"players": out})

@app.route("/api/transfer", methods=["POST"])
def api_transfer():
    d = request.get_json() or {}
    v = getp(d.get("sender"))
    if not v or not check_pin(v, d.get("pin", "")):
        return jsonify({"error": "Wrong PIN"}), 403
    r = find_by_id(d.get("receiver_id", ""))
    amt = int(d.get("amount", 0))
    if not r:
        return jsonify({"error": "Receiver not found"}), 404
    if amt <= 0 or v.get("gold", 0) < amt:
        return jsonify({"error": "Not enough Gold"}), 400
    v["gold"] -= amt
    r["gold"] = r.get("gold", 0) + amt
    notify(r["name"], "💸 " + v["name"] + " sent you " + str(amt) + " Gold")
    save()
    return jsonify({"ok": True, "sender_gold": v["gold"]})

@app.route("/api/bank_action", methods=["POST"])
def api_bank():
    d = request.get_json() or {}
    v = getp(d.get("name"))
    if not v or not check_pin(v, d.get("pin", "")):
        return jsonify({"error": "Wrong PIN"}), 403
    amt = int(d.get("amount", 0))
    cur = d.get("currency", "Gold")
    is_gold = (cur == "Gold")
    if d.get("action") == "deposit":
        if is_gold:
            if v.get("gold", 0) < amt:
                return jsonify({"error": "Not enough"}), 400
            v["gold"] -= amt
            v["bank_gold"] = v.get("bank_gold", 0) + amt
        else:
            if v.get("gems", 0) < amt:
                return jsonify({"error": "Not enough"}), 400
            v["gems"] -= amt
            v["bank_gems"] = v.get("bank_gems", 0) + amt
    else:
        if is_gold:
            if v.get("bank_gold", 0) < amt:
                return jsonify({"error": "Not enough in Bank"}), 400
            v["bank_gold"] -= amt
            v["gold"] = v.get("gold", 0) + amt
        else:
            if v.get("bank_gems", 0) < amt:
                return jsonify({"error": "Not enough in Bank"}), 400
            v["bank_gems"] -= amt
            v["gems"] = v.get("gems", 0) + amt
    save()
    return jsonify({"ok": True, "gold": v["gold"], "gems": v["gems"]})

@app.route("/api/exchange", methods=["POST"])
def api_exchange():
    d = request.get_json() or {}
    v = getp(d.get("name"))
    amt = int(d.get("amount", 0))
    direction = d.get("direction", "gold_to_gem")
    if not v or not check_pin(v, d.get("pin", "")):
        return jsonify({"error": "Wrong PIN"}), 403
    if direction == "gold_to_gem":
        gems = amt // 100
        if gems < 1 or v.get("gold", 0) < gems * 100:
            return jsonify({"error": "Need at least 100 Gold = 1 Germ"}), 400
        v["gold"] -= gems * 100
        v["gems"] = v.get("gems", 0) + gems
    else:
        if v.get("gems", 0) < amt:
            return jsonify({"error": "Not enough Gems"}), 400
        v["gems"] -= amt
        v["gold"] = v.get("gold", 0) + amt * 100
    save()
    return jsonify({"ok": True, "gold": v["gold"], "gems": v["gems"]})

@app.route("/api/loan_apply", methods=["POST"])
def loan_apply():
    d = request.get_json() or {}
    v = getp(d.get("name"))
    amt = int(d.get("amount", 0))
    if not v or not check_pin(v, d.get("pin", "")):
        return jsonify({"error": "Wrong PIN"}), 403
    lid = "LN-" + str(random.randint(10000000, 99999999))
    loan = {"id": lid, "from": v["display_name"], "from_id": v.get("player_id"), "amount": amt, "currency": d.get("currency", "Gold"), "repay_date": d.get("repay_date", ""), "original_date": d.get("repay_date", ""), "status": "pending_dominic", "new_date": "", "dominic_new_date": ""}
    DATA["loans"].append(loan)
    notify("dominic", "LOAN: " + v["display_name"] + " wants " + str(amt) + " " + loan["currency"] + " repay " + loan["repay_date"], "loan_request", {"loan_id": lid, "amount": amt, "currency": loan["currency"], "repay_date": loan["repay_date"], "from": v["display_name"]})
    save()
    return jsonify({"ok": True})

@app.route("/api/loan_dominic", methods=["POST"])
def loan_dom():
    d = request.get_json() or {}
    if norm(d.get("admin")) != "dominic" or str(d.get("pin")) != "2164":
        return jsonify({"error": "Only Dominic"}), 403
    for l in DATA["loans"]:
        if l["id"] == d.get("loan_id"):
            if not d.get("approve"):
                l["status"] = "declined"
                notify(l["from"], "Loan DECLINED by Dominic")
                save()
                return jsonify({"ok": True})
            l["new_date"] = d.get("new_date") or l["repay_date"]
            l["dominic_new_date"] = l["new_date"]
            l["status"] = "waiting_player_confirm"
            notify(l["from"], "Dominic changed Loan date to " + l["new_date"] + " - Approve?", "loan_date_change", {"loan_id": l["id"], "new_date": l["new_date"]})
            save()
            return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404

@app.route("/api/loan_player_confirm", methods=["POST"])
def loan_player_confirm():
    d = request.get_json() or {}
    v = getp(d.get("name"))
    if not v:
        return jsonify({"error": "No player"}), 404
    for l in DATA["loans"]:
        if l["id"] == d.get("loan_id"):
            if d.get("approve"):
                l["status"] = "approved"
                l["repay_date"] = l.get("dominic_new_date") or l["repay_date"]
                if l["currency"] == "Gold":
                    v["gold"] = v.get("gold", 0) + l["amount"]
                else:
                    v["gems"] = v.get("gems", 0) + l["amount"]
                notify("dominic", v["name"] + " accepted Loan date " + l["repay_date"])
            else:
                l["status"] = "refunded"
                notify("dominic", v["name"] + " declined Loan date - Refunded")
            save()
            return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404

@app.route("/api/request_money", methods=["POST"])
def api_req():
    d = request.get_json() or {}
    v = getp(d.get("name"))
    if not v:
        return jsonify({"error": "No player"}), 404
    rid = "RQ-" + str(random.randint(10000000, 99999999))
    try:
        amt = int(d.get("amount") or 0)
    except Exception:
        amt = 0
    r = {"id": rid, "from": v["display_name"], "amount": amt, "currency": d.get("currency", "Gold"), "message": d.get("message", "")}
    DATA["requests"].append(r)
    notify("dominic", "🔒 SECRET: " + v["display_name"] + " wants " + str(amt) + " " + r["currency"], "request", {"request_id": rid, "amount": amt, "currency": r["currency"]})
    save()
    return jsonify({"ok": True})

@app.route("/api/request_approve", methods=["POST"])
def api_req_ap():
    d = request.get_json() or {}
    if norm(d.get("admin")) != "dominic" or str(d.get("pin")) != "2164":
        return jsonify({"error": "Only Dominic"}), 403
    rid = d.get("request_id")
    amt = int(d.get("amount", 0))
    cur = d.get("currency", "Gold")
    for r in DATA["requests"]:
        if r["id"] == rid:
            v = getp(r["from"])
            if v:
                if cur == "Gold":
                    v["gold"] = v.get("gold", 0) + amt
                else:
                    v["gems"] = v.get("gems", 0) + amt
                notify(v["name"], "🔒 Secret Approved: +" + str(amt) + " " + cur)
            DATA["requests"] = [x for x in DATA["requests"] if x["id"] != rid]
            save()
            return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404

@app.route("/api/buy_item", methods=["POST"])
def api_buy():
    d = request.get_json() or {}
    v = getp(d.get("name"))
    if not v or not check_pin(v, d.get("pin", "")):
        return jsonify({"error": "Wrong PIN"}), 403
    item = d.get("item", "")
    price = int(d.get("price", 0))
    if v.get("gold", 0) < price:
        return jsonify({"error": "Not enough Gold"}), 400
    if item in v.get("cars", []):
        return jsonify({"error": "Already owned"}), 400
    v["gold"] -= price
    if any(x in item for x in ["Toyota", "BMW", "Lamborghini", "Ferrari", "Tesla", "Mercedes", "Audi", "Rover", "Hilux", "Nissan", "Bugatti"]):
        v.setdefault("cars", []).append(item)
    else:
        v.setdefault("items", []).append(item)
    save()
    return jsonify({"ok": True, "gold": v["gold"]})

@app.route("/api/consume", methods=["POST"])
def api_consume():
    d = request.get_json() or {}
    v = getp(d.get("name"))
    if not v or not check_pin(v, d.get("pin", "")):
        return jsonify({"error": "Wrong PIN"}), 403
    p = d.get("product", "")
    if p in v.get("items", []):
        v["items"].remove(p)
    v["wins"] = v.get("wins", 0) + int(d.get("bonus", 20))
    save()
    return jsonify({"ok": True, "wins": v["wins"]})

@app.route("/api/lottery", methods=["POST"])
def api_lot():
    d = request.get_json() or {}
    v = getp(d.get("name"))
    if not v or not check_pin(v, d.get("pin", "")):
        return jsonify({"error": "Wrong PIN"}), 403
    bet = int(d.get("bet", 0))
    cur = d.get("currency", "Gold")
    if bet <= 0:
        return jsonify({"error": "Bet > 0"}), 400
    if cur == "Gold":
        if v.get("gold", 0) < bet:
            return jsonify({"error": "Not enough Gold"}), 400
        v["gold"] -= bet
    else:
        if v.get("gems", 0) < bet:
            return jsonify({"error": "Not enough Gems"}), 400
        v["gems"] -= bet
    win = random.random() < 0.35
    if win:
        prize = bet * 2
        if cur == "Gold":
            v["gold"] += prize
        else:
            v["gems"] += prize
        res = {"win": True, "prize": prize, "lost": 0}
    else:
        res = {"win": False, "prize": 0, "lost": bet}
        DATA["economy"]["lottery"] = DATA["economy"].get("lottery", 0) + bet
    save()
    return jsonify({"ok": True, "gold": v["gold"], "gems": v["gems"], "result": res})

@app.route("/api/announce", methods=["POST"])
def api_ann():
    d = request.get_json() or {}
    if norm(d.get("admin")) != "dominic" or str(d.get("pin")) != "2164":
        return jsonify({"error": "Only Dominic"}), 403
    DATA["announcements"].append({"text": d.get("text", ""), "time": datetime.now().strftime("%H:%M")})
    for v in DATA["players"].values():
        v.setdefault("notifs", []).append({"text": "📢 " + d.get("text", ""), "type": "announce", "time": datetime.now().strftime("%H:%M")})
    save()
    return jsonify({"ok": True})

@app.route("/api/announcements")
def api_anns():
    return jsonify({"announcements": DATA["announcements"][-5:]})

@app.route("/api/economy")
def api_eco():
    if norm(request.args.get("name")) != "dominic" or str(request.args.get("password")) != "2164":
        return jsonify({"error": "Only Dominic"}), 403
    e = DATA["economy"]
    e["history"] = (e.get("history", []) + [random.randint(80, 180)])[-20:]
    e["gold"] = sum(p.get("gold", 0) for p in DATA["players"].values())
    e["gems"] = sum(p.get("gems", 0) for p in DATA["players"].values())
    e["bank_total"] = sum(p.get("bank_gold", 0) for p in DATA["players"].values())
    save()
    return jsonify({"economy": e, "requests": DATA["requests"], "loans": DATA["loans"]})

@app.route("/api/emergency", methods=["POST"])
def api_em():
    d = request.get_json() or {}
    if norm(d.get("name")) != "dominic" or str(d.get("pin")) != "2164":
        return jsonify({"error": "Only Dominic"}), 403
    v = getp("dominic")
    if not v:
        v = new_player("dominic", "2164")
    v["gold"] = v.get("gold", 0) + 500000000000
    save()
    return jsonify({"ok": True})

@app.route("/api/toggle_earning", methods=["POST"])
def api_tog():
    return jsonify({"ok": True, "earning_on": True})

@app.route("/api/server_info")
def api_srv():
    if norm(request.args.get("name")) != "dominic" or str(request.args.get("password")) != "2164":
        return jsonify({"error": "Only Dominic"}), 403
    return jsonify({"players": len(DATA["players"]), "earning_on": True, "reviews": DATA["reviews"][-20:]})

@app.route("/api/review", methods=["POST"])
def api_rev():
    d = request.get_json() or {}
    DATA["reviews"].append({"name": d.get("name"), "type": d.get("type"), "text": d.get("text")})
    save()
    return jsonify({"ok": True})

@app.route("/api/friends")
def api_friends():
    v = getp(request.args.get("name", ""))
    if not v:
        return jsonify({"friends": []})
    out = []
    for fn in v.get("friends", []):
        fv = getp(fn)
        if fv:
            out.append({"name": fv["name"], "player_id": fv.get("player_id")})
    return jsonify({"friends": out})

@app.route("/api/add_friend", methods=["POST"])
def api_addf():
    d = request.get_json() or {}
    v = getp(d.get("name"))
    t = find_by_id(d.get("target_id", ""))
    if not v or not t:
        return jsonify({"error": "Not found"}), 404
    if t["name"] not in v.get("friends", []):
        v.setdefault("friends", []).append(t["name"])
    if v["name"] not in t.get("friends", []):
        t.setdefault("friends", []).append(v["name"])
    save()
    return jsonify({"ok": True})

@app.route("/api/chat_send", methods=["POST"])
def api_chat_send():
    d = request.get_json() or {}
    a, b = d.get("sender", ""), d.get("to", "")
    key = "|".join(sorted([norm(a), norm(b)]))
    DATA["chats"].setdefault(key, []).append({"from": a, "text": d.get("text", "")})
    save()
    return jsonify({"ok": True})

@app.route("/api/chat_get")
def api_chat_get():
    a, b = request.args.get("a", ""), request.args.get("b", "")
    key = "|".join(sorted([norm(a), norm(b)]))
    return jsonify({"messages": DATA["chats"].get(key, [])})

HOME = r"""<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>INFINITY BOT v29</title><link href="https://fonts.googleapis.com/css2?family=Great+Vibes&family=Poppins:wght@400;700;900&display=swap" rel="stylesheet"><style>*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}body{margin:0;font-family:Poppins,Arial;color:#fff;background:radial-gradient(circle at 50% 20%,#3a0a5e,#12002b 70%);min-height:100vh}.cursive{font-family:'Great Vibes',cursive}.topbar{display:flex;justify-content:space-between;align-items:flex-start;padding:8px 14px}.profile{width:46px;height:46px;border-radius:50%;background:linear-gradient(135deg,#ff006e,#ffd700);display:flex;align-items:center;justify-content:center;font-size:20px;border:2px solid #fff;cursor:pointer}.center{min-height:82vh;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:20px}.crownBig{font-size:90px;filter:drop-shadow(0 0 30px gold)}.enterBtn{margin-top:20px;padding:16px 70px;font-family:'Great Vibes',cursive;font-size:48px;border:none;border-radius:60px;background:linear-gradient(90deg,#ff006e,#ffd700,#00e5ff);color:#000;box-shadow:0 0 40px #ff006e;cursor:pointer}.card{background:rgba(255,255,255,.08);border:2px solid rgba(255,255,255,.35);border-radius:26px;padding:20px;margin:14px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.box{background:linear-gradient(160deg,rgba(255,255,255,.18),rgba(0,0,0,.4));border:2px solid #fff;border-radius:24px;padding:22px 10px;text-align:center;cursor:pointer}.box span{font-size:38px;display:block}button{cursor:pointer}.btn{width:100%;padding:14px;border:none;border-radius:25px;font-weight:900;background:#ffd700;margin:6px 0}.btn2{width:100%;padding:13px;border-radius:25px;border:2px solid #00e5ff;background:transparent;color:#00e5ff;font-weight:900;margin:6px 0}.opt{width:100%;padding:13px;margin:7px 0;border-radius:16px;border:2px solid #fff;background:rgba(0,0,0,.5);color:#fff;font-weight:700;cursor:pointer;text-align:left}input,select,textarea{width:100%;padding:14px;border-radius:14px;border:2px solid #ffd700;margin:8px 0;font-size:16px;background:#fff;color:#000}input,select{position:relative;z-index:2}.hidden{display:none!important}.leadRow{display:flex;justify-content:space-between;align-items:center;padding:10px 12px;background:rgba(0,0,0,.45);border-radius:14px;margin:6px 0;cursor:pointer}.toast{position:fixed;top:70px;left:50%;transform:translateX(-50%);background:#fff;color:#000;padding:12px 18px;border-radius:20px;font-weight:700;z-index:999;max-width:90%;text-align:center}.gameOverlay{position:fixed;inset:0;background:rgba(0,0,0,.75);display:flex;align-items:center;justify-content:center;padding:16px;z-index:500}.gamePopup{background:linear-gradient(160deg,#2b005e,#12002b);border:3px solid #ffd700;border-radius:28px;padding:22px 18px;max-width:420px;width:100%;text-align:center}.choiceRow{display:flex;gap:12px;margin-top:16px}.choiceBox{flex:1;padding:18px 8px;border-radius:20px;cursor:pointer;font-weight:900;font-size:18px;border:3px solid #fff}.choiceNo{background:linear-gradient(135deg,#ff2222,#ff6b6b);color:#fff}.choiceYes{background:linear-gradient(135deg,#00cc44,#00ff88);color:#000}.bottomNav{position:fixed;bottom:0;left:0;right:0;background:rgba(0,0,0,.85);border-top:2px solid #ffd700;display:flex;justify-content:space-around;padding:10px 0 14px;z-index:200}.bottomNav div{font-size:28px;cursor:pointer;text-align:center}.bottomNav small{display:block;font-size:10px;color:#ffd700}.walletCard{background:linear-gradient(135deg,#ffd700,#ff006e);color:#000;border-radius:24px;padding:18px;text-align:center}.bigBankBox{padding:22px 10px;border-radius:24px;border:2px solid #fff;text-align:center;cursor:pointer;background:linear-gradient(160deg,rgba(255,255,255,.18),rgba(0,0,0,.4))}.loanGreen{border:4px solid #00ff88!important;box-shadow:0 0 25px #00ff88;background:linear-gradient(160deg,#00cc44,#00ff88)!important;color:#000!important}.idPrefix{display:flex;align-items:center;background:#fff;border-radius:14px;border:2px solid #ffd700;padding:0 10px;margin:8px 0}.idPrefix b{color:#000}.idPrefix input{border:none;flex:1;margin:0}.timerBar{height:14px;background:#333;border-radius:99px;overflow:hidden;margin:10px 0}.timerFill{height:100%;background:linear-gradient(90deg,#00ff88,#ffd700,#ff2222);transition:width .9s linear}.fallArea{position:relative;height:420px;background:linear-gradient(#000428,#004e92);border:2px solid #00e5ff;border-radius:18px;overflow:hidden}.fallItem{position:absolute;font-size:34px;cursor:pointer}.dinoArea{height:220px;background:#fff;border-radius:18px;position:relative;overflow:hidden;border:3px solid #000}.dino{position:absolute;bottom:20px;left:40px;font-size:52px;transition:bottom .35s}.cactus{position:absolute;bottom:20px;font-size:36px}.tabRow{display:flex;gap:8px}.tabBox{flex:1;padding:12px 4px;border-radius:16px;background:rgba(255,255,255,.15);border:2px solid #ffd700;text-align:center;cursor:pointer;font-weight:900;font-size:13px}.tabBox.active{background:#ffd700;color:#000}.pinInput{font-size:28px;text-align:center;letter-spacing:12px}</style></head><body>
<div id="announceBar" class="hidden" style="position:fixed;top:0;left:0;right:0;background:#ffd700;color:#000;padding:10px;text-align:center;font-weight:900;z-index:1000">📢</div>
<div class="topbar"><div><span id="catTime" style="font-size:12px;background:rgba(0,0,0,.55);border:1px solid #ffd700;padding:5px 9px;border-radius:20px;display:inline-block">00:00:00 CAT</span><br><span id="catDate" style="font-size:10px;background:rgba(0,0,0,.45);border:1px solid rgba(255,215,0,.6);padding:3px 8px;border-radius:20px;display:inline-block;margin-top:4px">Central Africa</span><br><div style="font-weight:900;margin-top:4px">INFINITY BOT</div></div><div id="topRight" class="hidden" style="display:flex;flex-direction:column;align-items:flex-end;gap:2px"><div style="display:flex;gap:8px;align-items:center"><div id="soundBtn" style="width:32px;height:32px;border-radius:50%;background:rgba(0,0,0,.55);border:1px solid #ffd700;display:flex;align-items:center;justify-content:center;cursor:pointer">🔊</div><div onclick="openShop()" style="width:32px;height:32px;border-radius:50%;background:rgba(0,0,0,.55);border:1px solid #ffd700;display:flex;align-items:center;justify-content:center;cursor:pointer">🛍️</div><div class="profile" id="profileBtn">👤</div></div><div id="menuBtn" style="width:32px;height:32px;border-radius:50%;background:rgba(0,0,0,.55);border:1px solid #ffd700;display:flex;align-items:center;justify-content:center;font-size:20px;cursor:pointer;margin-right:7px">⋮</div></div></div>
<div id="menuDrop" class="hidden" style="position:absolute;top:130px;right:10px;background:#1a1a2e;border:2px solid #ffd700;border-radius:16px;padding:8px;z-index:600;min-width:240px"></div><div id="toast" class="toast hidden"></div>
<div id="pinOverlay" class="gameOverlay hidden" style="display:none;z-index:900"><div class="gamePopup"><div style="font-size:50px">🔐</div><h2>Enter PIN</h2><p id="pinDesc">Enter your 4-digit PIN</p><input id="pinInput" class="pinInput" placeholder="...." maxlength="4" inputmode="numeric" type="password"><div class="choiceRow"><div class="choiceBox choiceNo" onclick="closePin()">❌ Cancel</div><div class="choiceBox choiceYes" onclick="confirmPin()">✅ Confirm</div></div></div></div>
<div id="announceOverlay" class="gameOverlay hidden" style="display:none;z-index:960"><div class="gamePopup"><h2>📢 Enter Announcement</h2><textarea id="annText" style="height:100px" placeholder="Type announcement to ALL players..."></textarea><button class="btn" type="button" onclick="sendAnnounce()">📢 Announce</button><button class="btn2" type="button" onclick="closeAnnounce()">Cancel</button></div></div>
<div id="secretOverlay" class="gameOverlay hidden" style="display:none;z-index:920"><div class="gamePopup"><div style="font-size:50px">🔒</div><h2>Secret Request</h2><input id="reqMsg" type="password" placeholder="Secret message"><input id="reqAmt" type="password" inputmode="numeric" placeholder="Amount (optional)"><select id="reqCur"><option>Gold</option><option>Gems</option></select><div class="choiceRow"><div class="choiceBox choiceNo" onclick="closeSecret()">❌ Cancel</div><div class="choiceBox choiceYes" onclick="sendMoneyRequest()">📩 Send Secret</div></div></div></div>
<div id="loanOverlay" class="gameOverlay hidden" style="display:none;z-index:920"><div class="gamePopup"><h2>🏦 Apply for Loan</h2><input id="loanAmt" type="number" placeholder="Amount"><select id="loanCur"><option>Gold</option><option>Gems</option></select><label>When to repay?</label><input id="loanDate" type="date"><div class="choiceRow"><div class="choiceBox choiceNo" onclick="closeLoan()">❌ Cancel</div><div class="choiceBox choiceYes" onclick="submitLoan()">📩 Apply</div></div></div></div>
<div id="page-welcome" class="gameOverlay hidden" style="display:none;z-index:950"><div class="gamePopup"><div style="font-size:56px">👑</div><h2>Do you already have an account?</h2><div class="choiceRow"><div class="choiceBox choiceNo" onclick="welcomeChoice('no')">❌ No</div><div class="choiceBox choiceYes" onclick="welcomeChoice('yes')">✅ Yes</div></div></div></div>
<div id="page-home" class="center"><div style="font-size:26px">✨ 💖 ⭐ 🌟 💫</div><div class="crownBig">👑</div><h1 class="cursive" style="font-size:68px;margin:5px">Infinity Bot</h1><p style="letter-spacing:3px;font-weight:900">DOMINIC MASTIRIA</p><p>Riddles • Bible Fight • Sci-Fi • WhatsApp</p><button class="enterBtn" id="enterBtn" type="button">Enter</button></div>
<div id="page-register" class="hidden" style="max-width:520px;margin:0 auto;padding:20px 14px"><div class="card" style="text-align:center"><div style="font-size:60px">👑</div><h1 class="cursive" style="font-size:48px;margin:5px">Register</h1><div id="registerForm"><input id="regName" placeholder="Your Name" maxlength="20"><input id="regPass" placeholder="...." maxlength="4" inputmode="numeric" type="password"><p style="font-size:12px;color:#ffd700">⚠️ Do NOT use 1234 or 0000</p><button class="btn" type="button" onclick="doRegister()">📝 REGISTER</button><p>Already have account? <b style="color:#ffd700;cursor:pointer" onclick="showLogin()">Login</b></p></div><div id="loginForm" class="hidden"><input id="loginName" placeholder="Your Name"><input id="loginPass" placeholder="...." maxlength="4" inputmode="numeric" type="password"><button class="btn" type="button" onclick="doLogin()">🔓 LOGIN</button><p>New? <b style="color:#ffd700;cursor:pointer" onclick="showRegister()">Register</b></p></div></div></div>
<div id="page-dash" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div style="text-align:center"><h2 class="cursive" style="font-size:44px;margin:10px 0" id="welcomeText">Welcome 👑</h2><span style="padding:5px 10px;border-radius:20px;background:rgba(0,0,0,.5);border:1px solid #ffd700;font-size:12px">⭐ Rank: <b id="myRank">#-</b></span> <span style="padding:5px 10px;border-radius:20px;background:rgba(0,0,0,.5);border:1px solid #ffd700;font-size:12px">🚗 Cars: <b id="myCarsCount">0</b> = +<span id="myExtraTime">0</span>s</span></div><div class="grid"><div class="box" onclick="openRiddles()"><span>🧩</span><b>RIDDLES</b><br><small>10 Qs • 25s • 3 Options</small></div><div class="box" onclick="openBible()"><span>📖</span><b>BIBLE FIGHT</b><br><small>Old / New</small></div><div class="box" onclick="openSciFi()"><span>🚀</span><b>SCI-FI</b><br><small>25 Dec 2026</small></div><div class="box" onclick="openMessages()"><span>💚</span><b>WHATSAPP</b><br><small>Chat • Call</small></div></div><div class="card"><h3 style="text-align:center;margin:0">🏆 TOP 5 🏆</h3><div id="leaderList">Loading...</div><button class="btn2" type="button" onclick="openFullLeader()">👀 View Full Leaderboard</button></div></div>
<div id="page-leader" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h3 style="text-align:center">🏆 LEADERBOARD 🏆</h3><div class="tabRow" style="margin:12px 0"><div class="tabBox" id="tabGold" onclick="setLeaderMode('gold')">🪙<br>Gold</div><div class="tabBox" id="tabGems" onclick="setLeaderMode('gems')">💎<br>Germ</div><div class="tabBox" id="tabRank" onclick="setLeaderMode('rank')">⭐<br>Rank</div><div class="tabBox active" id="tabPvp" onclick="setLeaderMode('pvp')">⚔️<br>PvP</div></div><div id="fullLeaderList">Loading...</div></div></div>
<div id="page-game" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 id="gameTitle" style="text-align:center">Game</h2><div id="gameBody"></div></div></div>
<div id="page-coming" class="hidden" style="max-width:520px;margin:0 auto;padding:40px 20px 110px;text-align:center"><div style="font-size:80px">🚀</div><h1 class="cursive" style="font-size:54px">Coming Soon</h1><h2>SCI-FI</h2><p>Launching <b>25th December 2026</b></p><div style="font-size:60px;font-weight:900;color:#ffd700" id="countDown">LOCKED</div></div>
<div id="page-bank" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">💰 BANK</h2><div class="walletCard"><div>🏦 BANK PROFILE</div><div id="bankIDShow">Bank INF-</div><div>🪙 Bank Gold: <b id="bankGold">0</b> | 💎 <b id="bankGems">0</b></div><div>Wallet — 🪙 <span id="walletGold">0</span> | 💎 <span id="walletGems">0</span></div></div><div style="display:flex;gap:12px;margin-top:14px"><div style="flex:1"><div class="bigBankBox" onclick="openSendPage()">💸<br><b>Send</b></div><div class="bigBankBox" style="margin-top:10px" onclick="openExchangePage()">🔄<br><b>Exchange UP</b><br><small>100 Gold = 1 Germ</small></div><div class="bigBankBox" style="margin-top:10px" onclick="openWithdrawPage()">🏧<br><b>Withdraw</b></div></div><div style="flex:1"><div class="bigBankBox" onclick="openDepositPage()">💰<br><b>Deposit</b></div><div class="bigBankBox loanGreen" style="margin-top:10px" onclick="openLoan()">🏦<br><b>LOAN - GREEN</b><br><small>Apply for Loan</small></div><div class="bigBankBox" style="margin-top:10px" onclick="openMyProfile()">👤<br><b>My Profile</b></div><div id="myLoansBox" style="margin-top:10px;font-size:12px"></div></div></div></div></div>
<div id="page-send" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">💸 SEND GOLD</h2><div class="walletCard">🪙 <b id="sendPageGold">0</b> | 💎 <b id="sendPageGems">0</b><br>Your ID: <b id="sendPageMyID">INF-</b></div><div class="idPrefix"><b>INF-</b><input id="sendDigits" placeholder="12345678" inputmode="numeric" maxlength="8"></div><input id="sendAmt" type="number" placeholder="Amount"><button class="btn" type="button" onclick="doSend()">➤ SEND NOW</button></div></div>
<div id="page-withdraw" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">🏧 WITHDRAW</h2><div class="walletCard">Bank: 🪙 <b id="wdBankGold">0</b> | 💎 <b id="wdBankGems">0</b><br>Wallet: 🪙 <b id="wdWalletGold">0</b> | 💎 <b id="wdWalletGems">0</b><br><b id="wdBankID">Bank INF-</b></div><input id="withdrawAmt" type="number" placeholder="Amount"><select id="withdrawCur"><option>Gold</option><option>Gems</option></select><button class="btn" type="button" onclick="doWithdraw()">🏧 WITHDRAW</button></div></div>
<div id="page-deposit" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">💰 DEPOSIT</h2><div class="walletCard">Wallet: 🪙 <b id="depWalletGold">0</b> | 💎 <b id="depWalletGems">0</b><br>Bank: 🪙 <b id="depBankGold">0</b> | 💎 <b id="depBankGems">0</b></div><input id="depositAmt" type="number" placeholder="Amount"><select id="depositCur"><option>Gold</option><option>Gems</option></select><button class="btn" type="button" onclick="doDeposit()">💰 DEPOSIT</button></div></div>
<div id="page-exchange" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">🔄 EXCHANGE</h2><div class="walletCard">🪙 <b id="exWalletGold">0</b> | 💎 <b id="exWalletGems">0</b></div><div class="bigBankBox" onclick="openExchange('gold_to_gem')"><b>Gold >>>> Germ</b><br><small>100 Gold = 1 Germ</small></div><div class="bigBankBox" style="margin-top:10px" onclick="openExchange('gem_to_gold')"><b>Germ >>>> Gold</b><br><small>1 Germ = 100 Gold</small></div><div id="exchangeForm"></div></div></div>
<div id="page-profile" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card" style="text-align:center"><div style="font-size:70px">👤</div><h2 id="profName">Player</h2><p id="profIDShow">ID:INF-</p><p id="profBankID">Bank INF-</p><p>⭐ Rank: <b id="profRank">#-</b></p><p>🏆 Wins: <b id="profWins">0</b> | ❌ <b id="profLoss">0</b></p><p>🪙 Gold: <b id="profGold">0</b> | 💎 Germ: <b id="profGems">0</b></p><p>🚗 My Cars: <b id="profCars">None</b></p><p>🌌 Galaxy Level: <b id="profGalaxy">1</b> | Kills: <b id="profGalaxyKills">0</b></p><button class="btn2" type="button" onclick="openSecret()">🔒 Secret</button></div><div class="card"><h3>🎒 INVENTORY</h3><div id="profInventory">No items</div><div id="consumeBox"></div></div></div>
<div id="page-other" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card" style="text-align:center"><h2 id="otherName">Player</h2><div id="otherNormal"><p>⭐ <b id="otherRank">#-</b></p><p><b id="otherWins">0</b> Win | <b id="otherLoss">0</b> Lose</p><div id="otherActions"></div></div></div></div>
<div id="page-notifs" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">✉️ NOTIFICATIONS</h2><div id="notifList">No notifications</div></div></div>
<div id="page-menu" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">🎮 MENU</h2><div id="menuGamesList"></div></div></div>
<div id="page-economy" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><div style="display:flex;justify-content:space-between"><h2>💰 SERVER ECONOMY</h2><button class="btn" type="button" style="width:auto;background:#ff2222;color:#fff" onclick="doEmergency()">🚨 Emergency</button></div><div class="grid"><div class="walletCard">Server Gold<br><b id="ecoGold">0</b></div><div class="walletCard">Server Germ<br><b id="ecoGems">0</b></div><div class="bigBankBox">🏦 Banks<br><b id="ecoBank">0</b></div><div class="bigBankBox">💸 Fees<br><b id="ecoFees">0</b></div><div class="bigBankBox">🎰 Lottery<br><b id="ecoLottery">0</b></div><div class="bigBankBox">🛟 Backup<br><b id="ecoBackup">0</b></div></div><h3>📈 CRYPTO - LIVE</h3><canvas id="ecoChart" width="480" height="160" style="width:100%;background:#000;border:2px solid #00ffaa;border-radius:14px"></canvas><h3>💰 SECRET REQUESTS</h3><div id="ecoRequests">No requests</div><h3>🏦 LOANS</h3><div id="ecoLoans">No loans</div></div></div>
<div id="page-lottery" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">🎰 LOTTERY</h2><input id="lotBet" type="number" placeholder="e.g. 1000"><select id="lotCur"><option>Gold</option><option>Gems</option></select><button class="btn" type="button" onclick="playLottery()">🎰 SPIN</button><div id="lotResult" style="text-align:center"></div></div></div>
<div id="page-update" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">🔄 UPDATE - DOMINIC ONLY</h2><p>🚀 SPACEX UPDATE CONSOLE v29 - No Data Lost</p><button class="btn" type="button" onclick="doServerUpdate()">🚀 APPLY UPDATE</button></div></div>
<div id="page-server-info" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">🖥️ SERVER INFO - DOMINIC</h2><p>PLAYERS: <span id="serverPlayers">0</span> | EARNING: <span id="serverEarningText">ON</span></p><h3>📜 Reviews</h3><div id="serverReviewsList">Loading...</div></div></div>
<div id="page-review" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 id="reviewTitle" style="text-align:center">⭐ Review</h2><textarea id="reviewText" style="height:140px" placeholder="Type..."></textarea><button class="btn" type="button" onclick="submitReview()">📩 SEND</button></div></div>
<div id="page-challenge" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">🎮 CHALLENGE</h2><p id="challengeDashText" style="text-align:center"></p><div class="grid"><div class="box" onclick="hostPickMode('Bible Fight')"><span>📖</span><b>Bible</b></div><div class="box" onclick="hostPickMode('Riddles')"><span>🧩</span><b>Riddles</b></div><div class="box" onclick="hostPickMode('Galaxy Shooter')"><span>🌌</span><b>Galaxy</b></div><div class="box" onclick="hostPickMode('Decoding')"><span>💻</span><b>Decoding</b></div></div><div id="duelBox"></div><button class="btn2" type="button" onclick="goDash()">❌ Decline</button></div></div>
<div id="page-messages" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h1 style="text-align:center">💚 WhatsApp</h1><div style="display:flex;gap:8px"><div class="idPrefix" style="flex:1"><b>INF-</b><input id="addFriendDigits" placeholder="Add friend ID" inputmode="numeric" maxlength="8"></div><button class="btn" type="button" style="width:auto" onclick="addFriendById()">➕ Add</button></div><div id="chatFriendList"></div></div></div>
<div id="page-chat" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">💬 <span id="chatWith">Friend</span></h2><div style="display:flex;gap:8px;justify-content:center"><button class="btn2" type="button" style="width:auto" onclick="startVoiceCall()">📞 Voice Call</button><button class="btn2" type="button" style="width:auto" onclick="toggleVoiceNote()">🎙️ Voice Note</button></div><div id="callBanner" class="hidden" style="background:#00cc44;color:#000;padding:12px;border-radius:14px;text-align:center;font-weight:900">📞 Calling... <span id="callTimer">00:00</span> <button onclick="endVoiceCall()">End</button></div><div id="chatBox" style="background:#1a1a2e;border-radius:20px;padding:12px;min-height:260px;max-height:360px;overflow-y:auto"></div><div style="display:flex;gap:8px;margin-top:10px"><input id="msgInput" placeholder="Message..." style="flex:1"><button class="btn" type="button" style="width:70px" onclick="sendMsg()">➤</button></div></div></div>
<div id="page-scifi" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 110px"><div class="card"><h2 style="text-align:center">🚀 SCI-FI DASHBOARD</h2><p style="text-align:center;font-size:12px">Galaxy Shooter + 9 Games</p><div id="scifiList"></div></div></div>
<div id="backFab" style="position:fixed;left:16px;bottom:88px;width:58px;height:58px;border-radius:50%;background:#1a1a2e;display:none;align-items:center;justify-content:center;font-size:28px;color:#ffd700;border:3px solid #ffd700;cursor:pointer;z-index:150">←</div>
<div id="msgFab" style="position:fixed;right:16px;bottom:88px;width:62px;height:62px;border-radius:50%;background:linear-gradient(135deg,#ff006e,#ffd700,#00e5ff);display:none;align-items:center;justify-content:center;font-size:30px;border:3px solid #fff;cursor:pointer;z-index:150">💬</div>
<div id="bottomNav" class="bottomNav hidden"><div onclick="goDash()">🏡<small>Home</small></div><div onclick="openFullLeader()">🏆<small>Leader</small></div><div onclick="openBank()">💰<small>Bank</small></div><div onclick="openNotifs()">✉️<small>Notify</small></div></div>
<audio id="pinSound" preload="auto" src="https://cdn.pixabay.com/audio/2025/07/09/audio_121db7b43f.mp3"></audio><audio id="dashAudio" loop preload="auto" style="display:none"></audio>
<script>
var CUTE_SOUND="https://cdn.pixabay.com/audio/2025/06/12/audio_0ea789b238.mp3";
var soundOn=true,audioCtx=null,dashAudio=null;
function pad2(n){return(n<10?"0":"")+n}
function updateCatTime(){try{var now=new Date();var cat=new Date(now.getTime()+now.getTimezoneOffset()*60000+2*3600000);var days=["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];var months=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];document.getElementById("catTime").textContent=pad2(cat.getHours())+":"+pad2(cat.getMinutes())+":"+pad2(cat.getSeconds())+" CAT";document.getElementById("catDate").textContent=days[cat.getDay()]+", "+pad2(cat.getDate())+" "+months[cat.getMonth()]+" "+cat.getFullYear()+" - Central Africa"}catch(e){}}
updateCatTime();setInterval(updateCatTime,1000);
function playPin(){try{var a=document.getElementById("pinSound");if(a){a.currentTime=0;var p=a.play();if(p&&p.catch)p.catch(function(){})}}catch(e){}}
function startDashLoop(){try{if(!dashAudio)dashAudio=document.getElementById("dashAudio");if(!dashAudio)return;if(!dashAudio.src)dashAudio.src=CUTE_SOUND;dashAudio.loop=true;dashAudio.volume=0.6;if(soundOn){var p=dashAudio.play();if(p&&p.catch)p.catch(function(){})}}catch(e){}}
function stopDashLoop(){try{if(dashAudio)dashAudio.pause()}catch(e){}}
function toggleSound(){soundOn=!soundOn;var b=document.getElementById("soundBtn");if(b)b.innerText=soundOn?"🔊":"🔇";if(soundOn){startDashLoop();playPin()}else{stopDashLoop()}toast(soundOn?"🔊 Cute Sound ON":"🔇 Sound OFF")}
var user=null;try{user=JSON.parse(localStorage.getItem("inf_user")||"null")}catch(e){}
var wins=0,losses=0,myGold=0,myGems=0,myPlayerID="",myBankID="",myCars=[];try{wins=parseInt(localStorage.getItem("inf_wins")||"0")||0;losses=parseInt(localStorage.getItem("inf_loss")||"0")||0;myGold=parseInt(localStorage.getItem("inf_gold")||"0")||0;myGems=parseInt(localStorage.getItem("inf_gems")||"0")||0;myPlayerID=localStorage.getItem("inf_player_id")||"";myBankID=localStorage.getItem("inf_bank_id")||"";myCars=JSON.parse(localStorage.getItem("inf_cars")||"[]")}catch(e){}
var stageIdx=0,loggedIn=false,currentPage="page-home",seenQs=[];try{seenQs=JSON.parse(localStorage.getItem("inf_seen")||"[]")}catch(e){seenQs=[]}
var pinCb=null,leaderMode="pvp",chatWithName="",callInterval=null,callSecs=0,quizT=null,quizLeft=0,quizRound=[],quizIdx=0,quizScore=0,quizMode="",galaxyKills=0,galaxyLevel=1,dinoJumps=0,dinoInterval=null,fallInt=null,matchScore=0,reviewType="review";
function carExtraTime(){var t=0;myCars.forEach(function(c){if(c.indexOf("Lamborghini")>=0||c.indexOf("Ferrari")>=0||c.indexOf("Bugatti")>=0)t+=15;else if(c.indexOf("Tesla")>=0||c.indexOf("Mercedes")>=0||c.indexOf("BMW")>=0)t+=10;else if(c.indexOf("Audi")>=0||c.indexOf("Range Rover")>=0)t+=7;else t+=2});return Math.min(t,30)}
function isDom(){return user&&user.name&&user.name.toLowerCase()==="dominic"&&user.password==="2164"}
function toast(m){var t=document.getElementById("toast");if(!t)return;t.innerText=m;t.classList.remove("hidden");setTimeout(function(){t.classList.add("hidden")},4500)}
function showPage(id){currentPage=id;["page-home","page-register","page-dash","page-leader","page-game","page-coming","page-bank","page-send","page-withdraw","page-deposit","page-exchange","page-profile","page-other","page-notifs","page-menu","page-update","page-server-info","page-review","page-challenge","page-messages","page-chat","page-economy","page-lottery","page-scifi"].forEach(function(p){var e=document.getElementById(p);if(e){e.classList.add("hidden");e.style.display="none"}});var tg=document.getElementById(id);if(tg){tg.classList.remove("hidden");tg.style.display="block"}window.scrollTo(0,0);updateVisibility()}
function updateVisibility(){var r=document.getElementById("topRight"),nv=document.getElementById("bottomNav"),b=document.getElementById("backFab"),mf=document.getElementById("msgFab");var isEnter=(currentPage==="page-home"||currentPage==="page-register");if(isEnter){if(r)r.style.display="none";if(nv)nv.classList.add("hidden");if(b)b.style.display="none";if(mf)mf.style.display="none";stopDashLoop()}else if(loggedIn&&currentPage==="page-dash"){if(r)r.style.display="flex";if(nv)nv.classList.remove("hidden");if(b)b.style.display="none";if(mf)mf.style.display="flex";startDashLoop()}else if(loggedIn){if(r)r.style.display="none";if(nv)nv.classList.add("hidden");if(b)b.style.display="flex";if(mf)mf.style.display="flex";stopDashLoop()}else{if(r)r.style.display="none";if(nv)nv.classList.add("hidden");if(b)b.style.display="none";if(mf)mf.style.display="none";stopDashLoop()}}
function goDash(){if(!loggedIn){showPage("page-register");return}showPage("page-dash");loadLeader()}
function goBack(){if(currentPage==="page-register")showPage("page-home");else if(currentPage==="page-chat")showPage("page-messages");else goDash()}
function enterClicked(){try{playPin()}catch(e){}showPage("page-register");showRegister();setTimeout(function(){var o=document.getElementById("page-welcome");if(o){o.classList.remove("hidden");o.style.display="flex"}},100)}
function welcomeChoice(c){var o=document.getElementById("page-welcome");o.classList.add("hidden");o.style.display="none";if(c==="yes")showLogin();else showRegister()}
function showRegister(){document.getElementById("registerForm").classList.remove("hidden");document.getElementById("loginForm").classList.add("hidden")}
function showLogin(){document.getElementById("registerForm").classList.add("hidden");document.getElementById("loginForm").classList.remove("hidden")}
function saveLocal(){try{localStorage.setItem("inf_user",JSON.stringify(user));localStorage.setItem("inf_wins",wins);localStorage.setItem("inf_loss",losses);localStorage.setItem("inf_gold",myGold);localStorage.setItem("inf_gems",myGems);localStorage.setItem("inf_player_id",myPlayerID);localStorage.setItem("inf_bank_id",myBankID);localStorage.setItem("inf_seen",JSON.stringify(seenQs));localStorage.setItem("inf_cars",JSON.stringify(myCars))}catch(e){}}
function doLogout(){try{localStorage.clear()}catch(e){}user=null;loggedIn=false;wins=0;losses=0;myGold=0;myGems=0;myCars=[];stopDashLoop();showPage("page-home");toast("👋 Logged out")}
function special(n,pw){var x=(n||"").toLowerCase().trim();if(x==="britney"||x==="kayula")return"Welcome MY Fiance 💖";if(x==="blessing")return"Welcome Avatar ✨";if(x==="lubuto")return"Welcome Desk Bender 🛠️";if(x==="dominic"&&pw==="2164")return"Welcome Infinity Emperor ♾";return"Welcome, "+n+" 👑"}
function doRegister(){var n=document.getElementById("regName").value.trim();var pw=document.getElementById("regPass").value.trim();if(!n){toast("Enter name");return}if(!pw||pw.length!==4||isNaN(pw)){toast("Password 4 digits");return}if(pw==="1234"||pw==="0000"){toast("Too easy");return}fetch("/api/player?name="+encodeURIComponent(n)).then(function(r){return r.json()}).then(function(d){if(d&&d.found){showLogin();document.getElementById("loginName").value=n;toast("Account found! Login");return}user={name:n,password:pw};wins=0;losses=0;myGold=0;myGems=0;seenQs=[];myCars=[];saveLocal();syncScore();enterDash(special(n,pw))})}
function doLogin(){var n=document.getElementById("loginName").value.trim();var pw=document.getElementById("loginPass").value.trim();fetch("/api/player?name="+encodeURIComponent(n)+"&password="+encodeURIComponent(pw)).then(function(r){return r.json()}).then(function(d){if(d&&d.found&&d.password_ok!==false){user={name:n,password:pw};wins=d.wins||0;losses=d.losses||0;myGold=d.gold||0;myGems=d.gems||0;myPlayerID=d.player_id||"";myBankID=d.bank_id||"";seenQs=d.seen_qs||[];myCars=d.cars||[];galaxyLevel=d.galaxy_level||1;galaxyKills=d.galaxy_kills||0;saveLocal();enterDash(special(n,pw))}else toast("Wrong / Not found")})}
function enterDash(m){loggedIn=true;toast(m);playPin();startDashLoop();showPage("page-dash");document.getElementById("welcomeText").innerText=m;loadLeader();loadMe();checkAnn()}
function syncScore(){if(!user)return;fetch("/api/score",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,password:user.password,wins:wins,losses:losses,stage:stageIdx,gold:myGold,gems:myGems,seen_qs:seenQs,cars:myCars,galaxy_level:galaxyLevel,galaxy_kills:galaxyKills})}).catch(function(){})}
function loadMe(){if(!user)return;fetch("/api/player?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){if(!d||!d.found)return;myGold=d.gold;myGems=d.gems;myCars=d.cars||myCars;var e=function(id,v){var x=document.getElementById(id);if(x)x.innerText=v};e("bankGold",d.bank_gold||0);e("bankGems",d.bank_gems||0);e("bankIDShow",d.bank_id||myBankID);e("walletGold",d.gold);e("walletGems",d.gems);e("myCarsCount",myCars.length);e("myExtraTime",carExtraTime())})}
function loadLeader(){fetch("/api/leaderboard?mode=pvp").then(function(r){return r.json()}).then(function(d){var h="";(d.players||[]).slice(0,5).forEach(function(p,i){h+="<div class='leadRow' onclick=\"viewOther('"+p.name+"')\"><span>"+(i+1)+". "+p.name+"</span><span>🏆 "+p.wins+"W | "+p.losses+"L</span></div>"});document.getElementById("leaderList").innerHTML=h||"No players"})}
function setLeaderMode(m){leaderMode=m;["gold","gems","rank","pvp"].forEach(function(x){var el=document.getElementById("tab"+x.charAt(0).toUpperCase()+x.slice(1));if(el)el.classList.remove("active")});var a=document.getElementById("tab"+m.charAt(0).toUpperCase()+m.slice(1));if(a)a.classList.add("active");openFullLeader()}
function openFullLeader(){showPage("page-leader");fetch("/api/leaderboard?mode="+leaderMode).then(function(r){return r.json()}).then(function(d){var h="";(d.players||[]).forEach(function(p,i){h+="<div class='leadRow' onclick=\"viewOther('"+p.name+"')\"><span>"+(i+1)+". "+p.name+"<br><small>"+p.player_id+"</small></span><span>"+(leaderMode==="gold"?"🪙 "+p.gold:leaderMode==="gems"?"💎 "+p.gems:leaderMode==="rank"?"⭐ "+p.rank:"🏆 "+p.wins+"W | "+p.losses+"L")+"</span></div>"});document.getElementById("fullLeaderList").innerHTML=h||"No players"})}
function viewOther(name){fetch("/api/player?name="+encodeURIComponent(name)).then(function(r){return r.json()}).then(function(d){showPage("page-other");document.getElementById("otherName").innerText=d.name;document.getElementById("otherRank").innerText=d.rank;document.getElementById("otherWins").innerText=d.wins;document.getElementById("otherLoss").innerText=d.losses;document.getElementById("otherActions").innerHTML="<button class='btn' type='button' onclick=\"openBankSendTo('"+d.player_id+"')\">💸 Send Gold</button>"})}
function openMyProfile(){showPage("page-profile");fetch("/api/player?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){document.getElementById("profName").innerText=special(d.name,user.password);document.getElementById("profIDShow").innerText="ID:"+d.player_id;document.getElementById("profBankID").innerText=d.bank_id;document.getElementById("profRank").innerText="#-";document.getElementById("profWins").innerText=d.wins;document.getElementById("profLoss").innerText=d.losses;document.getElementById("profGold").innerText=d.gold;document.getElementById("profGems").innerText=d.gems;document.getElementById("profCars").innerText=(d.cars||[]).join(", ")||"None";document.getElementById("profGalaxy").innerText=d.galaxy_level||1;document.getElementById("profGalaxyKills").innerText=d.galaxy_kills||0;var inv=d.items||[];var h="";inv.forEach(function(it){h+="<div style='padding:10px;background:rgba(0,0,0,.4);border-radius:12px;margin:6px 0'>🎒 "+it+"</div>"});document.getElementById("profInventory").innerHTML=h||"No items";var cb=document.getElementById("consumeBox");var drink=inv.find(function(x){return /Cola|Juice|Drink/.test(x)});var food=inv.find(function(x){return /Burger|Pizza|Donut/.test(x)});var h2="";if(drink)h2+="<button class='btn' type='button' onclick=\"consumeP('"+drink+"')\">🥤 Drink "+drink+"</button>";if(food)h2+="<button class='btn2' type='button' onclick=\"consumeP('"+food+"')\">🍔 Eat "+food+"</button>";cb.innerHTML=h2})}
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
function openWithdrawPage(){showPage("page-withdraw");fetch("/api/player?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){document.getElementById("wdBankGold").innerText=d.bank_gold||0;document.getElementById("wdBankGems").innerText=d.bank_gems||0;document.getElementById("wdWalletGold").innerText=d.gold;document.getElementById("wdWalletGems").innerText=d.gems;document.getElementById("wdBankID").innerText=d.bank_id})}
function openDepositPage(){showPage("page-deposit");fetch("/api/player?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){document.getElementById("depWalletGold").innerText=d.gold;document.getElementById("depWalletGems").innerText=d.gems;document.getElementById("depBankGold").innerText=d.bank_gold||0;document.getElementById("depBankGems").innerText=d.bank_gems||0})}
function openExchangePage(){showPage("page-exchange");fetch("/api/player?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){document.getElementById("exWalletGold").innerText=d.gold;document.getElementById("exWalletGems").innerText=d.gems});document.getElementById("exchangeForm").innerHTML=""}
function openExchange(dir){document.getElementById("exchangeForm").innerHTML="<input id='exAmt' type='number' placeholder='Amount'><button class='btn' type='button' onclick=\"doExchange('"+dir+"')\">Confirm</button>"}
function doSend(){var dg=document.getElementById("sendDigits").value.replace(/[^0-9]/g,"");var amt=parseInt(document.getElementById("sendAmt").value||"0");if(dg.length<8||!amt){toast("ID + Amount");return}openPin("PIN to send "+amt,function(pin){fetch("/api/transfer",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({sender:user.name,pin:pin,receiver_id:"INF-"+dg,amount:amt})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.sender_gold;saveLocal();toast("✅ Sent");playPin();openNotifs()})})}
function doWithdraw(){var amt=parseInt(document.getElementById("withdrawAmt").value||"0");var cur=document.getElementById("withdrawCur").value;openPin("PIN withdraw "+amt,function(pin){fetch("/api/bank_action",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,amount:amt,action:"withdraw",currency:cur})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.gold;myGems=d.gems;saveLocal();toast("✅ Withdrawn")})})}
function doDeposit(){var amt=parseInt(document.getElementById("depositAmt").value||"0");var cur=document.getElementById("depositCur").value;openPin("PIN deposit "+amt,function(pin){fetch("/api/bank_action",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,amount:amt,action:"deposit",currency:cur})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.gold;myGems=d.gems;saveLocal();toast("✅ Deposited")})})}
function doExchange(dir){var amt=parseInt(document.getElementById("exAmt").value||"0");openPin("PIN Exchange",function(pin){fetch("/api/exchange",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,amount:amt,direction:dir})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.gold;myGems=d.gems;saveLocal();toast("✅ Exchange done")})})}
function openNotifs(){showPage("page-notifs");fetch("/api/player?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){var h="";(d.notifs||[]).slice().reverse().forEach(function(n){var extra="";if(n.type==="loan_request"){extra="<br><button class='btn' type='button' onclick=\"domLoan('"+n.loan_id+"',true)\">✅ Approve Loan</button><button class='btn2' type='button' onclick=\"domLoan('"+n.loan_id+"',false)\">❌ Decline</button>"}if(n.type==="loan_date_change"){extra="<br><button class='btn' type='button' onclick=\"playerLoanConfirm('"+n.loan_id+"',true)\">✅ Yes Approve Date "+n.new_date+"</button><button class='btn2' type='button' onclick=\"playerLoanConfirm('"+n.loan_id+"',false)\">❌ No - Refund</button>"}if(n.type==="request"){extra="<br><button class='btn' type='button' onclick=\"approveReq('"+n.request_id+"',"+n.amount+",'"+n.currency+"')\">✅ Approve Secret</button>"}h+="<div style='padding:12px;background:rgba(0,0,0,.4);border-radius:14px;margin:8px 0'>"+n.text+"<br><small>"+(n.time||"")+"</small>"+extra+"</div>"});document.getElementById("notifList").innerHTML=h||"No notifications";if(h)playPin()})}
function openEconomy(){if(!isDom()){toast("🔒 Dominic only");return}showPage("page-economy");fetch("/api/economy?name=Dominic&password=2164").then(function(r){return r.json()}).then(function(d){var e=d.economy||{};document.getElementById("ecoGold").innerText=e.gold||0;document.getElementById("ecoGems").innerText=e.gems||0;document.getElementById("ecoBank").innerText=e.bank_total||e.bank||0;document.getElementById("ecoFees").innerText=e.fees||0;document.getElementById("ecoLottery").innerText=e.lottery||0;document.getElementById("ecoBackup").innerText=e.backup||0;var h="";(d.requests||[]).forEach(function(rq){h+="<div style='padding:12px;background:rgba(0,0,0,.4);border-radius:14px;margin:8px 0'>"+rq.from+" wants "+rq.amount+" "+rq.currency+" <button class='btn' type='button' onclick=\"approveReq('"+rq.id+"',"+rq.amount+",'"+rq.currency+"')\">✅ Approve</button></div>"});document.getElementById("ecoRequests").innerHTML=h||"No requests";var h2="";(d.loans||[]).forEach(function(l){h2+="<div style='padding:12px;background:rgba(0,0,0,.4);border-radius:14px;margin:8px 0'>"+l.from+" Loan "+l.amount+" "+l.currency+" Repay "+l.repay_date+" ["+l.status+"] <button class='btn' type='button' onclick=\"domLoan('"+l.id+"',true)\">✅ Approve</button><button class='btn2' type='button' onclick=\"domLoan('"+l.id+"',false)\">❌ Decline</button></div>"});document.getElementById("ecoLoans").innerHTML=h2||"No loans";var cv=document.getElementById("ecoChart");if(cv){var ctx=cv.getContext("2d");ctx.clearRect(0,0,480,160);ctx.strokeStyle="#00ffaa";ctx.lineWidth=3;ctx.beginPath();var hist=e.history||[0];hist.forEach(function(v,i){var x=i/(Math.max(1,hist.length-1))*460+10;var y=150-(v/(Math.max(1,Math.max.apply(null,hist)))*120);if(i===0)ctx.moveTo(x,y);else ctx.lineTo(x,y)});ctx.stroke()}})}
function approveReq(id,amt,cur){openPin("PIN approve "+amt,function(pin){fetch("/api/request_approve",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({admin:"dominic",pin:pin,request_id:id,amount:amt,currency:cur})}).then(function(){toast("✅ Approved - Hidden");playPin();openEconomy()})})}
function domLoan(id,ap){if(!ap){openPin("PIN decline loan",function(pin){fetch("/api/loan_dominic",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({admin:"dominic",pin:pin,loan_id:id,approve:false})}).then(function(){toast("Loan declined");openEconomy()})});return}var nd=prompt("New repay date? Leave blank = same","");openPin("PIN approve loan",function(pin){fetch("/api/loan_dominic",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({admin:"dominic",pin:pin,loan_id:id,approve:true,new_date:nd})}).then(function(){toast("Loan sent to player for confirm");openEconomy()})})}
function playerLoanConfirm(id,ap){fetch("/api/loan_player_confirm",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,loan_id:id,approve:ap})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}toast(ap?"✅ Loan Credited":"↩️ Loan Refunded");playPin();loadMe();openNotifs()})}
function doEmergency(){openPin("PIN Emergency 2164",function(pin){fetch("/api/emergency",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:"dominic",pin:pin})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}toast("🚨 Emergency +500B");openEconomy()})})}
function openLottery(){showPage("page-lottery")}
function playLottery(){var bet=parseInt(document.getElementById("lotBet").value||"0");var cur=document.getElementById("lotCur").value;openPin("PIN Lottery "+bet,function(pin){fetch("/api/lottery",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,bet:bet,currency:cur})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.gold;myGems=d.gems;saveLocal();document.getElementById("lotResult").innerHTML=d.result.win?"<h2 style='color:#00ff88'>🎉 WON "+d.result.prize+"</h2>":"<h2 style='color:#ff5555'>😢 Lost "+d.result.lost+"</h2>"})})}
function openAnnounce(){if(!isDom()){toast("🔒 Dominic only");return}var o=document.getElementById("announceOverlay");o.classList.remove("hidden");o.style.display="flex";playPin()}
function closeAnnounce(){var o=document.getElementById("announceOverlay");o.classList.add("hidden");o.style.display="none"}
function sendAnnounce(){var t=document.getElementById("annText").value.trim();if(!t){toast("Type announcement");return}closeAnnounce();openPin("PIN 2164 to Announce",function(pin){fetch("/api/announce",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({admin:"dominic",pin:pin,text:t})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}toast("📢 Announced to ALL");playPin()})})}
function checkAnn(){fetch("/api/announcements").then(function(r){return r.json()}).then(function(d){var a=(d.announcements||[]).slice(-1)[0];if(a){var bar=document.getElementById("announceBar");bar.innerText="📢 "+a.text;bar.classList.remove("hidden");playPin();setTimeout(function(){bar.classList.add("hidden")},1000)}})}
function doServerUpdate(){toast("🚀 Update Applied - No Data Lost");playPin()}
function openServerInfo(){if(!isDom()){toast("🔒 Dominic only");return}showPage("page-server-info");fetch("/api/server_info?name=Dominic&password=2164").then(function(r){return r.json()}).then(function(d){document.getElementById("serverPlayers").innerText=d.players||0;document.getElementById("serverEarningText").innerText=d.earning_on?"ON":"OFF";var h="";(d.reviews||[]).forEach(function(rv){h+="<div style='padding:10px;background:rgba(0,0,0,.4);border-radius:12px;margin:6px 0'>"+rv.name+": "+rv.text+"</div>"});document.getElementById("serverReviewsList").innerHTML=h||"No reviews"})}
function openMenuPage(){showPage("page-menu");var g=[["🧩 Riddles","openRiddles()"],["📖 Bible Fight","openBible()"],["🚀 Sci-Fi","openSciFi()"],["💚 WhatsApp","openMessages()"],["💰 Bank","openBank()"],["🛍️ Shop","openShop()"],["🎰 Lottery","openLottery()"],["🏆 Leaderboard","openFullLeader()"],["🎮 Challenge","openChallengeDash()"],["📢 Announcement","openAnnounce()"]];var h="";g.forEach(function(x){h+="<button class='btn2' type='button' onclick=\""+x[1]+"\">"+x[0]+"</button>"});document.getElementById("menuGamesList").innerHTML=h}
function openChallengeDash(){showPage("page-challenge");document.getElementById("challengeDashText").innerText="Challenge Dashboard - Host picks mode"}
function hostPickMode(m){toast("Host picked "+m+" - 10 Qs");openRiddles()}
function openRiddles(){pickRiddleCat()}
function openBible(){pickBible()}
var QB=["vanity of vanities book?|Ecclesiastes - Solomon|Genesis - Moses|Psalms - David|OLD","Woman judge under palm tree?|Deborah - Palm tree|Esther - Palace|Ruth - Field|OLD","Methuselah lived how long?|969 years|930 years|950 years|OLD","3 men in fiery furnace?|Shadrach, Meshach, Abednego|Daniel, Shadrach, Meshach|Peter, James, John|OLD","High priest tore robes?|Caiaphas|Annas|Pilate|NEW","24 elders represent?|12 tribes + 12 apostles|24 prophets|24 angels|NEW","Father of Caleb?|Jephunneh|Jesse|Jacob|OLD","Moses father-in-law?|Jethro / Reuel|Aaron|Joshua|OLD","First Gentile church?|Antioch|Rome|Corinth|NEW","Ebenezer means?|Stone of Help - Samuel|Stone of God - Moses|Holy Stone - David|OLD","Fear not how many times?|365 - one per day|100|50|OLD","Only apostle natural death?|John|Peter|Paul|NEW","Longest chapter?|Psalm 119 - Word of God|Psalm 23|Genesis 1|OLD","Shortest chapter?|Psalm 117 - 2 verses|Psalm 23|John 11|OLD"];
var QR=["Always hungry, finger red?|Fire|Water|Wind|FUNNY","Man photo - father's son?|His son|His brother|His father|SMART","3 boxes labels wrong, pick 1?|Pick from 'both' box|Pick apples box|Pick oranges box|SMART","Plane crashes border, bury survivors?|Nowhere - alive|USA|Canada|FUNNY","Rooster lays egg on roof?|Roosters don't lay eggs|Left side|Right side|FUNNY","Overtake 2nd place?|2nd place|1st place|3rd place|SMART","Cowboy Friday 3 days leaves Friday?|Horse named Friday|Time travel|Magic|FUNNY","Once in minute, twice moment?|Letter M|Letter O|Letter N|SMART","Man pushes car to hotel bankrupt?|Playing Monopoly|Real bankrupt|Lost|FUNNY","Hold in right not left?|Your left hand|Your right foot|Pen|SMART","Cities no houses, forests no trees?|A map|A book|A photo|SMART","Fragile saying name breaks?|Silence|Glass|Egg|SMART","Beginning eternity, end time?|Letter E|Letter A|Letter T|SMART","Dies old age on 25th birthday?|Born Feb 29 leap year|Magic|Time|FUNNY","Head tail brown no legs?|A penny|A dog|A snake|FUNNY","Not seen but felt, king kneel?|Love|Money|Power|LOVE","Grows when give away?|Love|Money|Gold|LOVE","Broken without touch, mended without fix?|A heart|A glass|A bone|LOVE","Written no pen, spoken no voice?|Love|Dream|Song|LOVE","War both win surrender?|Love|Peace|War|LOVE","Question and answer in 3 words?|I love you|Who are you|Yes I do|LOVE","Bat+ball $1.10 bat $1 more?|5 cents|10 cents|50 cents|PROGRAMMERS","Half of 2+2?|3|2|4|SMART","Months have 28 days?|All 12|February only|1|SMART","Boat sinks no one dies?|Everyone married - no single|Boat empty|Swim|FUNNY","Scarecrow award?|Outstanding in field|Funny|Tall|FUNNY","Fish without eyes?|A fsh|Blind fish|Nemo|FUNNY","Coffee police report?|Got mugged - depresso|Stolen|Cold|FUNNY","Cheese not yours?|Nacho cheese|Cheddar|Mozzarella|FUNNY","Bicycle fall over?|Two-tired|Flat|Broken|FUNNY","Math book sad?|Too many problems|Hard|Boring|FUNNY","Bear no teeth?|A gummy bear|Old bear|Baby|FUNNY","Golfer two pants?|Hole in one|Cold|Fashion|FUNNY"];
function parseQ(s){var p=s.split("|");var opts=[p[1],p[2],p[3]];for(var i=opts.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1));var t=opts[i];opts[i]=opts[j];opts[j]=t}return {q:p[0],correct:p[1],opts:opts,cat:p[4]}}
function pickRiddleCat(){showPage("page-game");document.getElementById("gameTitle").innerText="🧩 PICK RIDDLE TYPE";document.getElementById("gameBody").innerHTML="<p>Pick one - 10 Questions, 25s Timer, 3 Options</p><button class='btn2' type='button' onclick=\"startQuiz('RIDDLE','LIVE')\">🎤 Live</button><button class='btn2' type='button' onclick=\"startQuiz('RIDDLE','SMART')\">🧠 Smart / Logic</button><button class='btn2' type='button' onclick=\"startQuiz('RIDDLE','FUNNY')\">😂 Funny</button><button class='btn2' type='button' onclick=\"startQuiz('RIDDLE','PROGRAMMERS')\">💻 Programmers</button><button class='btn2' type='button' onclick=\"startQuiz('RIDDLE','LOVE')\">💖 Love</button><button class='btn2' type='button' onclick='goDash()'>⬅ Back</button>"}
function pickBible(){showPage("page-game");document.getElementById("gameTitle").innerText="📖 PICK TESTAMENT";document.getElementById("gameBody").innerHTML="<p>Pick - Only Bible questions from that Testament</p><button class='btn2' type='button' onclick=\"startQuiz('BIBLE','OLD')\">📜 Old Testament</button><button class='btn2' type='button' onclick=\"startQuiz('BIBLE','NEW')\">✝️ New Testament</button><button class='btn2' type='button' onclick='goDash()'>⬅ Back</button>"}
function startQuiz(mode,cat){quizMode=mode;var pool=(mode==="BIBLE"?QB:QR);var filtered=pool.filter(function(s){var c=s.split("|")[4];if(cat==="LIVE")return true;return c===cat});var avail=filtered.filter(function(s){return seenQs.indexOf(s)<0});if(avail.length<10){seenQs=[];avail=filtered}avail.sort(function(){return Math.random()-0.5});quizRound=avail.slice(0,10).map(parseQ);quizIdx=0;quizScore=0;showQuizQ()}
function showQuizQ(){if(quizIdx>=10){finishQuiz();return}var q=quizRound[quizIdx];showPage("page-game");document.getElementById("gameTitle").innerText=(quizMode==="BIBLE"?"📖 BIBLE FIGHT":"🧩 RIDDLES")+" - Q "+(quizIdx+1)+"/10";var total=25+carExtraTime();quizLeft=total;document.getElementById("gameBody").innerHTML="<div style='font-size:28px;font-weight:900' id='timerTxt'>⏱️ "+quizLeft+"s</div><div class='timerBar'><div class='timerFill' id='timerFill' style='width:100%'></div></div><p style='font-size:12px;color:#ffd700'>⏱️ 25s Base + 🚗 Car +"+carExtraTime()+"s = "+total+"s</p><p style='font-size:18px;font-weight:700'>"+q.q+"</p><p>🏆 Wins: "+wins+" | 🪙 "+myGold+" | Score: "+quizScore+"/10</p><div id='hintBox'></div>"+q.opts.map(function(o,i){return "<button class='opt' type='button' onclick=\"answerQuiz("+i+")\">"+o+"</button>"}).join("")+"<button class='btn2' type='button' onclick='goDash()'>⬅ Quit</button>";if(quizT)clearInterval(quizT);quizT=setInterval(function(){quizLeft--;var t=document.getElementById("timerTxt");if(t)t.innerText="⏱️ "+quizLeft+"s";var f=document.getElementById("timerFill");if(f)f.style.width=(quizLeft/total*100)+"%";if(quizLeft===5&&myCars.length>0){var hb=document.getElementById("hintBox");if(hb)hb.innerHTML="<p style='color:#ffd700'>💡 HINT (Car): Starts with '"+q.correct.charAt(0)+"' - "+q.correct.length+" letters</p>"}if(quizLeft<=0){clearInterval(quizT);losses++;saveLocal();syncScore();toast("⏰ Time up! Correct: "+q.correct);quizIdx++;setTimeout(showQuizQ,900)}},1000)}
function answerQuiz(i){if(quizT)clearInterval(quizT);var q=quizRound[quizIdx];var chosen=q.opts[i];var ok=(chosen===q.correct);if(ok){quizScore++;wins++;myGold+=50;toast("✅ Correct +1 Win +50 Gold")}else{losses++;toast("❌ Wrong! Correct: "+q.correct)}seenQs.push(q.q+"|"+q.correct);saveLocal();syncScore();quizIdx++;setTimeout(showQuizQ,900)}
function finishQuiz(){showPage("page-game");document.getElementById("gameTitle").innerText="🏁 ROUND DONE";document.getElementById("gameBody").innerHTML="<h2>Score: "+quizScore+"/10</h2><p>Wins: "+wins+" | Gold: "+myGold+"</p><button class='btn' type='button' onclick=\"pickRiddleCat()\">🧩 Play Again</button><button class='btn2' type='button' onclick=\"pickBible()\">📖 Bible Again</button><button class='btn2' type='button' onclick='goDash()'>⬅ Dashboard</button>"}
function openSciFi(){var now=new Date();var openDate=new Date(2026,11,25);if(now<openDate){showPage("page-coming");return}showPage("page-scifi");var games=[["🌌 Galaxy Shooter","openGalaxy()"],["🦖 Dino Jump","openDino()"],["🍬 Royal Match","openMatch()"],["🧩 Puzzle Rush","openMatch()"],["🏎️ Space Racing","openMatch()"],["🎯 Target Shooter","openGalaxy()"],["💎 Gem Blast","openMatch()"],["🃏 Card Battle","openMatch()"],["🏃 Runner","openDino()"],["🚀 Rocket Jump","openDino()"]];var h="";games.forEach(function(g){h+="<button class='btn2' type='button' onclick=\""+g[1]+"\">"+g[0]+"</button>"});document.getElementById("scifiList").innerHTML=h}
function openGalaxy(){showPage("page-game");document.getElementById("gameTitle").innerText="🌌 GALAXY SHOOTER";document.getElementById("gameBody").innerHTML="<p>Level "+galaxyLevel+" - Need "+(galaxyLevel===1?100:galaxyLevel*500)+" kills</p><p>Kills: "+galaxyKills+"</p><button class='btn' type='button' onclick='startGalaxy()'>🚀 START GALAXY</button><button class='btn2' type='button' onclick='openSciFi()'>⬅ Sci-Fi</button>"}
function startGalaxy(){showPage("page-game");document.getElementById("gameTitle").innerText="🌌 GALAXY - Level "+galaxyLevel;document.getElementById("gameBody").innerHTML="<p>Kills: <b id='gKillTxt'>"+galaxyKills+"</b> | Need: "+(galaxyLevel===1?100:galaxyLevel*500)+"</p><div class='fallArea' id='fallArea'></div><button class='btn2' type='button' onclick='stopGalaxy();openSciFi()'>⬅ Stop</button>";var area=document.getElementById("fallArea");var speed=Math.max(600,1800-(galaxyLevel*200));if(fallInt)clearInterval(fallInt);fallInt=setInterval(function(){var el=document.createElement("div");el.className="fallItem";el.innerText=["👾","🛸","☄️","👽","🛰️"][Math.floor(Math.random()*5)];el.style.left=Math.random()*85+"%";el.style.top="0px";area.appendChild(el);var top=0;var iv=setInterval(function(){top+=8+galaxyLevel*3;el.style.top=top+"px";if(top>380){clearInterval(iv);if(el.parentNode)el.parentNode.removeChild(el)}},50);el.onclick=function(){galaxyKills++;var t=document.getElementById("gKillTxt");if(t)t.innerText=galaxyKills;if(el.parentNode)el.parentNode.removeChild(el);clearInterval(iv);var need=(galaxyLevel===1?100:galaxyLevel*500);if(galaxyKills>=need){stopGalaxy();galaxyLevel++;galaxyKills=0;wins+=50;var rew=Math.floor(Math.random()*106)+45;if(Math.random()<0.5){myGold+=rew;toast("🌌 LEVEL UP! +50 Wins +"+rew+" Gold")}else{myGems+=rew;toast("🌌 LEVEL UP! +50 Wins +"+rew+" Germ")}saveLocal();syncScore();openGalaxy()}}},speed)}
function stopGalaxy(){if(fallInt)clearInterval(fallInt)}
function openDino(){showPage("page-game");document.getElementById("gameTitle").innerText="🦖 DINO JUMP";document.getElementById("gameBody").innerHTML="<p>Jumps: <b id='dinoTxt'>"+dinoJumps+"</b> | Every 10 jumps = 45-150 Gold/Germ OR 10 Wins</p><div class='dinoArea' id='dinoArea'><div class='dino' id='dinoEl'>🦖</div><div class='cactus' id='cactusEl'>🌵</div></div><button class='btn' type='button' onclick='jumpDino()'>🦖 TAP TO JUMP</button><button class='btn2' type='button' onclick='stopDino();openSciFi()'>⬅ Sci-Fi</button>";var cx=400;if(dinoInterval)clearInterval(dinoInterval);dinoInterval=setInterval(function(){cx-=6;if(cx<-30)cx=400;var c=document.getElementById("cactusEl");if(c)c.style.left=cx+"px"},50)}
function stopDino(){if(dinoInterval)clearInterval(dinoInterval)}
function jumpDino(){var d=document.getElementById("dinoEl");if(!d)return;d.style.bottom="90px";setTimeout(function(){d.style.bottom="20px"},350);dinoJumps++;var t=document.getElementById("dinoTxt");if(t)t.innerText=dinoJumps;if(dinoJumps%10===0){var r=Math.floor(Math.random()*106)+45;var type=Math.random();if(type<0.4){myGold+=r;toast("🦖 10 Jumps! +"+r+" Gold")}else if(type<0.8){myGems+=r;toast("🦖 10 Jumps! +"+r+" Germ")}else{wins+=10;toast("🦖 10 Jumps! +10 Wins")}saveLocal();syncScore()}}
function openMatch(){showPage("page-game");document.getElementById("gameTitle").innerText="🍬 ROYAL MATCH";var emojis=["🍬","🍭","🍓","🍇","💎","⭐"];var board="";for(var i=0;i<9;i++){board+="<div style='display:inline-block;font-size:36px;padding:8px;cursor:pointer;background:rgba(255,255,255,.2);border-radius:12px;margin:4px' onclick=\"matchTap(this)\">"+emojis[Math.floor(Math.random()*emojis.length)]+"</div>"}document.getElementById("gameBody").innerHTML="<p>Tap 3 same candies! Gets harder every level</p><div style='text-align:center'>"+board+"</div><p>Score: <b id='matchScore'>0</b></p><button class='btn' type='button' onclick='openMatch()'>🔄 Next Level</button><button class='btn2' type='button' onclick='openSciFi()'>⬅ Sci-Fi</button>"}
function matchTap(el){matchScore+=10;var s=document.getElementById("matchScore");if(s)s.innerText=matchScore;el.innerText=["🍬","🍭","🍓","🍇","💎","⭐"][Math.floor(Math.random()*6)];if(matchScore%30===0){myGold+=50;wins+=1;toast("🍬 Match! +50 Gold +1 Win");saveLocal();syncScore()}}
function openShop(){showPage("page-game");document.getElementById("gameTitle").innerText="🛍️ SHOP - No Repeats";renderShop()}
var SHOP=[["Toyota Corolla",34000],["Toyota Hilux",76000],["BMW M4",142000],["Lamborghini Huracan",400000],["Ferrari 488",500000],["Tesla Model 3",80000],["Mercedes C-Class",90000],["Audi A4",84000],["Range Rover",220000],["Nissan GTR",220000],["Bugatti Chiron",6000000],["Infinity Burger",200],["Infinity Pizza",300],["Infinity Cola",100],["Mango Juice",150],["Energy Drink",250],["Infinity Phone",5000],["Infinity Laptop",12000],["Infinity PS5",8000],["Infinity Jacket",800],["Infinity Dog",2000],["Infinity Cat",1500],["Infinity Football",400],["Infinity Perfume",900]];
function renderShop(){var h="<p>🪙 Gold: "+myGold+" | Cars = x2 Real Price | Car = +Time</p><input id='shopSearch' placeholder='🔍 Search...' oninput='renderShopList()'><div id='shopList'></div><button class='btn2' type='button' onclick='goDash()'>⬅ Back</button>";document.getElementById("gameBody").innerHTML=h;renderShopList()}
function renderShopList(){var q=(document.getElementById("shopSearch")?document.getElementById("shopSearch").value.toLowerCase():"");var h="";SHOP.forEach(function(it){if(q&&it[0].toLowerCase().indexOf(q)<0)return;var owned=myCars.indexOf(it[0])>=0;h+="<div style='padding:12px;background:rgba(255,255,255,.12);border-radius:14px;margin:6px 0;display:flex;justify-content:space-between;align-items:center'><span>🛍️ "+it[0]+"<br><small>"+(owned?"✅ OWNED":"🪙 "+it[1]+" Gold")+"</small></span><button class='btn' type='button' style='width:auto;padding:8px 14px' onclick=\"buyItem('"+it[0].replace(/'/g,"")+"',"+it[1]+")\">"+(owned?"Owned":"Buy")+"</button></div>"});document.getElementById("shopList").innerHTML=h}
function buyItem(name,price){openPin("PIN buy "+name,function(pin){fetch("/api/buy_item",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,pin:pin,item:name,price:price})}).then(function(r){return r.json()}).then(function(d){if(d.error){toast(d.error);return}myGold=d.gold;if(/Toyota|BMW|Lamborghini|Ferrari|Tesla|Mercedes|Audi|Rover|Hilux|Nissan|Bugatti/.test(name)){if(myCars.indexOf(name)<0)myCars.push(name)}saveLocal();toast("✅ Bought "+name);playPin();renderShop()})})}
function openPin(desc,cb){pinCb=cb;document.getElementById("pinDesc").innerText=desc;document.getElementById("pinInput").value="";var o=document.getElementById("pinOverlay");o.classList.remove("hidden");o.style.display="flex";playPin();setTimeout(function(){document.getElementById("pinInput").focus()},100)}
function closePin(){var o=document.getElementById("pinOverlay");o.classList.add("hidden");o.style.display="none";pinCb=null}
function confirmPin(){var v=document.getElementById("pinInput").value.trim();if(!v||v.length!==4){toast("PIN 4 digits");return}var cb=pinCb;closePin();if(cb)cb(v)}
function openMessages(){showPage("page-messages");fetch("/api/friends?name="+encodeURIComponent(user.name)).then(function(r){return r.json()}).then(function(d){var h="";(d.friends||[]).forEach(function(f){h+="<div class='leadRow' onclick=\"openChatWith('"+f.name+"')\"><span>💚 "+f.name+"<br><small>"+f.player_id+"</small></span><span>💬 Chat</span></div>"});document.getElementById("chatFriendList").innerHTML=h||"No friends - add by ID"})}
function addFriendById(){var dg=document.getElementById("addFriendDigits").value.replace(/[^0-9]/g,"");if(dg.length!==8){toast("8 digits");return}fetch("/api/add_friend",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user.name,target_id:"INF-"+dg})}).then(function(){toast("✅ Friend added");openMessages()})}
function openChatWith(n){chatWithName=n;showPage("page-chat");document.getElementById("chatWith").innerText=n;loadChat()}
function loadChat(){fetch("/api/chat_get?a="+encodeURIComponent(user.name)+"&b="+encodeURIComponent(chatWithName)).then(function(r){return r.json()}).then(function(d){var h="";(d.messages||[]).forEach(function(m){var mine=(m.from===user.name);h+="<div style='max-width:80%;padding:10px 14px;border-radius:18px;margin:6px 0;font-size:14px;"+(mine?"background:#ffd700;color:#000;margin-left:auto":"background:rgba(255,255,255,.2)")+"'>"+m.text+"</div>"});var b=document.getElementById("chatBox");b.innerHTML=h||"No messages";b.scrollTop=b.scrollHeight})}
function sendMsg(){var t=document.getElementById("msgInput").value.trim();if(!t)return;fetch("/api/chat_send",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({sender:user.name,to:chatWithName,text:t})}).then(function(){document.getElementById("msgInput").value="";loadChat();playPin()})}
function startVoiceCall(){var b=document.getElementById("callBanner");b.classList.remove("hidden");callSecs=0;if(callInterval)clearInterval(callInterval);callInterval=setInterval(function(){callSecs++;var m=Math.floor(callSecs/60),s=callSecs%60;document.getElementById("callTimer").innerText=(m<10?"0":"")+m+":"+(s<10?"0":"")+s},1000)}
function endVoiceCall(){var b=document.getElementById("callBanner");b.classList.add("hidden");if(callInterval)clearInterval(callInterval)}
function toggleVoiceNote(){toast("🎙️ Voice Note - hold to record (demo)")}
function openReviewRequest(t){reviewType=t;document.getElementById("reviewTitle").innerText=t==="request"?"📩 Request":"⭐ Review";showPage("page-review")}
function submitReview(){var t=document.getElementById("reviewText").value.trim();if(!t){toast("Type something");return}fetch("/api/review",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:user?user.name:"Guest",type:reviewType,text:t})}).then(function(){toast("✅ Sent");document.getElementById("reviewText").value="";goDash()})}
function toggleMenu(){var m=document.getElementById("menuDrop");if(!m.classList.contains("hidden")){m.classList.add("hidden");return}var items="";items+="<div style='padding:12px;cursor:pointer;border-bottom:1px solid #333' onclick=\"openMyProfile();toggleMenu()\">👤 My Profile</div>";items+="<div style='padding:12px;cursor:pointer;border-bottom:1px solid #333' onclick=\"openBank();toggleMenu()\">💰 Bank</div>";items+="<div style='padding:12px;cursor:pointer;border-bottom:1px solid #333' onclick=\"openShop();toggleMenu()\">🛍️ Shop</div>";items+="<div style='padding:12px;cursor:pointer;border-bottom:1px solid #333' onclick=\"openEconomy();toggleMenu()\">💰 Economy (Dominic)</div>";items+="<div style='padding:12px;cursor:pointer;border-bottom:1px solid #333' onclick=\"openLottery();toggleMenu()\">🎰 Lottery</div>";items+="<div style='padding:12px;cursor:pointer;border-bottom:1px solid #333' onclick=\"openAnnounce();toggleMenu()\">📢 Announcement (Dominic)</div>";items+="<div style='padding:12px;cursor:pointer;border-bottom:1px solid #333' onclick=\"openMenuPage();toggleMenu()\">🎮 Menu</div>";items+="<div style='padding:12px;cursor:pointer;border-bottom:1px solid #333' onclick=\"openServerInfo();toggleMenu()\">🖥️ Server Info</div>";items+="<div style='padding:12px;cursor:pointer;border-bottom:1px solid #333' onclick=\"openUpdatePage();toggleMenu()\">🔄 Update</div>";items+="<div style='padding:12px;cursor:pointer;border-bottom:1px solid #333' onclick=\"toggleSound();toggleMenu()\">🔊 Sound ON / OFF</div>";items+="<div style='padding:12px;cursor:pointer;border-bottom:1px solid #333' onclick=\"openReviewRequest('review');toggleMenu()\">⭐ Review</div>";items+="<div style='padding:12px;cursor:pointer;border-bottom:1px solid #333' onclick=\"openReviewRequest('request');toggleMenu()\">📩 Request</div>";items+="<div style='padding:12px;cursor:pointer' onclick=\"doLogout();toggleMenu()\">🚪 Logout</div>";m.innerHTML=items;m.classList.remove("hidden")}
function openUpdatePage(){if(!isDom()){toast("🔒 Dominic only");return}showPage("page-update")}
document.addEventListener("click",function(e){var m=document.getElementById("menuDrop");var b=document.getElementById("menuBtn");if(m&&!m.classList.contains("hidden")&&b&&!b.contains(e.target)&&!m.contains(e.target))m.classList.add("hidden")});
document.addEventListener("DOMContentLoaded",function(){var mb=document.getElementById("menuBtn");if(mb)mb.onclick=function(e){e.stopPropagation();toggleMenu()};var pb=document.getElementById("profileBtn");if(pb)pb.onclick=function(){openMyProfile()};var sb=document.getElementById("soundBtn");if(sb)sb.onclick=function(){toggleSound()};var bf=document.getElementById("backFab");if(bf)bf.onclick=function(){goBack()};var mf=document.getElementById("msgFab");if(mf)mf.onclick=function(){openMessages()};var eb=document.getElementById("enterBtn");if(eb)eb.onclick=function(){enterClicked()};showPage("page-home");document.addEventListener("keydown",function(e){if(e.key==="Enter"&&currentPage==="page-home")enterClicked()});setInterval(function(){if(loggedIn)checkAnn()},15000)});
</script></body></html>
"""

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
