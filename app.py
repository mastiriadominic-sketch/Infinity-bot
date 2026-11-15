from flask import Flask, request
import os, requests, random
app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "infinity")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
PHONE_ID = os.environ.get("PHONE_NUMBER_ID", "")

players = {}
QUESTIONS = [
    {"q":"What is the capital of Zambia?","opts":["A) Lusaka","B) Kitwe","C) Ndola"],"ans":"A"},
    {"q":"Which planet is called the Red Planet?","opts":["A) Venus","B) Mars","C) Jupiter"],"ans":"B"},
    {"q":"What is 2 + 6 + 12?","opts":["A) 18","B) 20","C) 22"],"ans":"B"},
    {"q":"I speak without a mouth, I hear without ears. What am I?","opts":["A) Echo","B) Phone","C) Wind"],"ans":"A"},
    {"q":"Who is the creator of INFINITY BOT?","opts":["A) Dominic Mastiria","B) Elon","C) Messi"],"ans":"A"},
]

def send_whatsapp(to, text):
    if not WHATSAPP_TOKEN or not PHONE_ID:
        print(f"TO {to}: {text}")
        return
    url = f"https://graph.facebook.com/v21.0/{PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    data = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text}}
    try:
        requests.post(url, headers=headers, json=data, timeout=10)
    except Exception as e:
        print(e)

def handle_command(sender, text):
    low = text.strip().lower()
    if low.startswith("/help") or low == "help":
        return "👑 INFINITY AND BEYOND\n\n/register <name> - Join\nPLAY - Play game\nSTART - Start 10 questions\nPUZZLE - Charming puzzle\nCREATE - Create your own game\nLEADER - Leaderboard"
    if low.startswith("/register") or low.startswith("register"):
        name = text[9:].strip() if len(text)>9 else "Player"
        players[sender] = {"name": name, "score": 0, "q": 0}
        return f"Welcome {name} 👑 to INFINITY BOT! Send PLAY to start!"
    if low == "play":
        players[sender] = {"name": players.get(sender,{}).get("name","Player"), "score":0, "q":0}
        return "👑 INFINITY GAME START!\n\nSend START to get your first question!\n\n💖 Puzzles | 🚀 Create Game | 💚 Play on Website"
    if low == "start":
        if sender not in players:
            players[sender] = {"name":"Player","score":0,"q":0}
        players[sender]["q"]=0
        players[sender]["score"]=0
        q = QUESTIONS[0]
        return f"🚀 Q1: {q['q']}\n" + "\n".join(q['opts']) + "\n\nReply A, B or C"
    if low == "puzzle":
        return "💖 CHARMING PUZZLE:\nWhat can you hold in your right hand, but never in your left?\nReply your answer!"
    if low == "create":
        return "🚀 CREATE YOUR GAME!\nSend like this:\nCREATE | Your Question | A) ... | B) ... | C) ...\nExample:\nCREATE | Capital of Zambia? | A) Lusaka | B) Kitwe | C) Ndola"
    if low == "leader" or low == "leaderboard":
        return "🏆 LEADERBOARD 🏆\n1. 👑 CHAMPION_ZM - 10/10\n2. 💖 LUCY_LUSAKA - 9/10\n3. 🚀 MASTERK - 9/10\n\nPlay to climb!"
    if low in ["a","b","c"]:
        if sender not in players:
            return "Send PLAY first 👑"
        p = players[sender]
        idx = p.get("q",0)
        if idx >= len(QUESTIONS):
            return "Game over! Send PLAY to play again 👑"
        q = QUESTIONS[idx]
        correct = (low.upper() == q["ans"])
        if correct:
            p["score"]+=1
        p["q"]+=1
        msg = "✅ Correct! 💖" if correct else f"❌ Wrong! Answer was {q['ans']}"
        if p["q"] >= len(QUESTIONS):
            return f"{msg}\n\n🏁 GAME OVER!\nYou got {p['score']}/{len(QUESTIONS)} 👑\n\nSend PLAY to play again! Check website for leaderboard!"
        nq = QUESTIONS[p["q"]]
        return f"{msg}\n\n🚀 Q{p['q']+1}: {nq['q']}\n" + "\n".join(nq['opts']) + "\n\nReply A, B or C"
    if low.startswith("create |"):
        return "🚀 Your game is created! 👑 Share it with friends! Send PLAY to play the main game."
    return "👑 INFINITY BOT IS ONLINE!\n\nSend:\nPLAY - Play game\nSTART - Start questions\nPUZZLE - Charming puzzle\nCREATE - Create your game\nLEADER - Leaderboard\n\nOr visit our website!"

# --- WEBSITE ---
HOME = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>INFINITY BOT | Dominic Mastiria</title><style>*{box-sizing:border-box}body{margin:0;font-family:Arial;color:white;background:linear-gradient(160deg,#ff006e,#7b00ff,#00e5ff,#12002b);background-size:400% 400%;animation:bg 12s ease infinite} @keyframes bg{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}.top{padding:30px 18px;text-align:center}.crown{font-size:80px;filter:drop-shadow(0 0 25px gold)}h1{font-size:34px;text-shadow:0 0 20px #fff,0 0 40px #ff006e}.btn{display:block;margin:14px auto;padding:16px;background:linear-gradient(90deg,#ff006e,#ffd700,#00e5ff);color:#000;font-weight:900;font-size:18px;border-radius:30px;text-decoration:none;width:88%;max-width:360px;text-align:center}.card{margin:16px;background:rgba(0,0,0,0.6);border:2px solid #fff;border-radius:24px;padding:20px;text-align:center}input,select{width:100%;padding:12px;margin:6px 0;border-radius:12px;border:none}button{padding:13px 20px;border:none;border-radius:25px;font-weight:bold;background:#ffd700;margin:6px}.puzzle{background:rgba(255,255,255,0.12);padding:14px;border-radius:15px;margin:10px 0;text-align:left}.codebox{background:#000;color:#00ff88;padding:14px;border-radius:12px;font-family:monospace;word-break:break-all;margin:10px 0;text-align:left}.terminal{background:#000;color:#00ff88;padding:14px;border-radius:12px;font-family:monospace;text-align:left}</style></head><body><div class="top"><div class="crown">👑</div><div>INFINITY BOT • DOMINIC MASTIRIA</div><h1>INFINITY BOT<br>IS ONLINE 👑</h1><p>Romantic 💖 Sci-Fi 🚀 Coder's Dream 💻</p><a class="btn" href="https://wa.me/260000000000?text=PLAY">▶ PLAY NOW ON WHATSAPP</a></div><div class="card"><h2>💖 A - PUZZLES & CHARMING 💖</h2><div class="puzzle"><b>Puzzle 1:</b> I speak without a mouth, I hear without ears. What am I?<br><button onclick="show('p1')">Reveal 💖</button><div id="p1" style="display:none">✨ Answer: Echo! Like love, it comes back to you 💖</div></div><div class="puzzle"><b>Puzzle 2:</b> 2, 6, 12, 20, 30, ?<br><button onclick="show('p2')">Reveal 💖</button><div id="p2" style="display:none">✨ Answer: 42!</div></div><div class="puzzle"><b>Puzzle 3:</b> What can you hold in right hand, never in left?<br><button onclick="show('p3')">Reveal 💖</button><div id="p3" style="display:none">✨ Answer: Your LEFT hand! 😍</div></div></div><div class="card"><h2>🚀 SCI-FI - CREATE YOUR GAME 🚀</h2><p>YOU are Game Master!</p><input id="q" placeholder="Your Question"><input id="a" placeholder="Option A"><input id="b" placeholder="Option B"><input id="c" placeholder="Option C"><select id="correct"><option value="A">Correct is A</option><option value="B">Correct is B</option><option value="C">Correct is C</option></select><button onclick="makeGame()" style="background:#00e5ff">✨ CREATE MY GAME 🚀</button><div id="gameOut" style="display:none"><div class="codebox" id="gameCode"></div><button onclick="copyGame()">📋 COPY GAME</button></div></div><div class="card"><h2>💚 C - LINK BOT TO WHATSAPP 💚</h2><input id="phone" placeholder="Your number e.g. 260977123456"><button onclick="makeLink()" style="background:#25D366;color:white">🔗 MAKE MY WHATSAPP LINK</button><div id="linkOut" style="display:none"><div class="codebox" id="linkCode"></div><button onclick="copyLink()" style="background:#25D366;color:white">📋 COPY LINK</button></div><p>Website → WhatsApp → Auto types PLAY → Bot replies!</p></div><div class="card"><h2>💻 CODER'S SCENIC ROOM 💻</h2><div class="terminal">> Dominic@infinity-bot:~$ npm run start<br>> ✓ Romantic: ON 💖<br>> ✓ Sci-Fi: ON 🚀<br>> ✓ Coder: ON 💻<br>> INFINITY BOT IS ONLINE 👑</div><p>Made with love in Lusaka, Zambia 🇿🇲</p></div><div class="card"><h2>🏆 LEADERBOARD 🏆</h2><p style="text-align:left">1. 👑 CHAMPION_ZM — 10/10<br>2. 💖 LUCY_LUSAKA — 9/10<br>3. 🚀 MASTERK — 9/10</p></div><script>function show(id){document.getElementById(id).style.display='block'}function makeGame(){let q=document.getElementById('q').value||'Capital of Zambia?';let a=document.getElementById('a').value||'Lusaka';let b=document.getElementById('b').value||'Kitwe';let c=document.getElementById('c').value||'Ndola';let cor=document.getElementById('correct').value;let txt='🚀 INFINITY GAME 👑\\n'+q+'\\nA) '+a+'\\nB) '+b+'\\nC) '+c+'\\nReply A,B or C! Correct: '+cor;document.getElementById('gameCode').innerText=txt;document.getElementById('gameOut').style.display='block';window.myGame=txt;}function copyGame(){navigator.clipboard.writeText(window.myGame||'');alert('Game copied!')}function makeLink(){let p=document.getElementById('phone').value.replace(/[^0-9]/g,'')||'260000000000';let link='https://wa.me/'+p+'?text=PLAY';document.getElementById('linkCode').innerText=link;document.getElementById('linkOut').style.display='block';window.myLink=link;}function copyLink(){navigator.clipboard.writeText(window.myLink||'');alert('Link copied!')}</script></body></html>"""

@app.route("/")
def home():
    return HOME

@app.route("/webhook", methods=["GET","POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        return "Forbidden", 403
    data = request.get_json() or {}
    try:
        entry = data["entry"][0]["changes"][0]["value"]
        messages = entry.get("messages", [])
        for m in messages:
            sender = m.get("from")
            text = m.get("text", {}).get("body", "")
            if sender and text:
                reply = handle_command(sender, text)
                send_whatsapp(sender, reply)
    except Exception as e:
        print(e)
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
