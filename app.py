from flask import Flask, request
import os, requests
app = Flask(__name__)
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "infinity123")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
PHONE_ID = os.environ.get("PHONE_NUMBER_ID", "")
players = {}
def send_whatsapp(to, text):
    if not WHATSAPP_TOKEN or not PHONE_ID:
        print(f"TO {to}: {text}")
        return
    url = f"https://graph.facebook.com/v21.0/{PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    data = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text}}
    try: requests.post(url, headers=headers, json=data, timeout=10)
    except Exception as e: print(e)
def handle_command(sender, text):
    low = text.strip().lower()
    if low.startswith("/help"):
        return "👑 INFINITY AND BEYOND\n\n/register <name>\n/stats\n/church list\n/church join Heavenly Infinity\n/pray\n/go bar\n/drink Heineken 2"
    if low.startswith("/register"):
        name = text[9:].strip() or "Player"
        players[sender] = {"name": name, "level": 1, "zeni": 1000000, "church": "None"}
        return f"🎉 Welcome {name}!\n💰 1,000,000 Zeni\n✨ Lv1\n⛪ Join: /church join Heavenly Infinity"
    if low.startswith("/stats"):
        p = players.get(sender)
        if not p: return "❌ First do /register <name>"
        return f"👤 {p['name']}\n⭐ Lv{p['level']}\n💰 {p['zeni']} Zeni\n⛪ Church: {p['church']}"
    if low.startswith("/church list"):
        return "⛪ CHURCHES:\n⛪ Heavenly Infinity | Purpose: EXP"
    if low.startswith("/church join"):
        p = players.get(sender)
        if not p: return "❌ First /register"
        p["church"] = "Heavenly Infinity"
        return "✅ You joined Heavenly Infinity\n🙏 Now do /pray"
    if low.startswith("/pray"):
        p = players.get(sender)
        if not p or p["church"] == "None": return "❌ Join a church first"
        p["zeni"] += 5000
        return f"🙏 You prayed!\n🎁 +5000 Zeni"
    if low.startswith("/go bar"):
        return "🍸 INFINITY BAR!\n🥤 Coca-Cola 10,000\n🍺 Heineken 25,000\n👉 Do: /drink Heineken 2"
    if low.startswith("/drink"):
        return f"🍸 You drank: {text[6:]}"
    return f"❌ No Such Command: {text}\nTry /help"
@app.route("/", methods=["GET"])
def home(): return "INFINITY BOT IS ONLINE 👑"
@app.route("/webhook", methods=["GET"])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "wrong token", 403
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json
        entry = data["entry"][0]["changes"][0]["value"]
        if "messages" in entry:
            msg = entry["messages"][0]
            send_whatsapp(msg["from"], handle_command(msg["from"], msg["text"]["body"]))
    except Exception as e: print(e)
    return "OK", 200
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
