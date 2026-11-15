from flask import Flask, request, jsonify
import os, requests, random, time
app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "infinity")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
PHONE_ID = os.environ.get("PHONE_NUMBER_ID", "")
players = {}
leaderboard = {}  # name -> {wins, losses, games}

def send_whatsapp(to, text):
    if not WHATSAPP_TOKEN or not PHONE_ID:
        print(f"TO {to}: {text}"); return
    url = f"https://graph.facebook.com/v21.0/{PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    data = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text}}
    try: requests.post(url, headers=headers, json=data, timeout=10)
    except Exception as e: print(e)

def handle_command(sender, text):
    low = text.strip().lower()
    if low in ["play","start","hi","hello","enter"]:
        return "👑 INFINITY BOT IS ONLINE!\n\nPlay on our WEBSITE for Riddles & Bible Fight!\nSend PLAY to start here too!\n\nRiddles | Bible Fight | Sci-Fi (25 Dec 2026)"
    if low.startswith("/register") or low.startswith("register"):
        name = text[9:].strip() if len(text)>9 else "Player"
        players[sender]={"name":name,"score":0,"q":0}
        return f"Welcome {name} 👑 Registered! Send PLAY"
    return "👑 INFINITY BOT 👑\nSend PLAY\nOr visit our website - Press ENTER to register!"

HOME = r"""<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>INFINITY BOT | Dominic Mastiria</title>
<link href="https://fonts.googleapis.com/css2?family=Great+Vibes&family=Poppins:wght@400;700;900&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box}body{margin:0;font-family:Poppins,Arial;color:white;background:radial-gradient(circle at 50% 20%,#3a0a5e,#12002b 70%);min-height:100vh;overflow-x:hidden}
.cursive{font-family:'Great Vibes',cursive}
.topbar{display:flex;justify-content:space-between;align-items:center;padding:14px 18px}
.logo{font-weight:900;letter-spacing:2px}.profile{width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,#ff006e,#ffd700);display:flex;align-items:center;justify-content:center;font-size:22px;border:2px solid #fff;cursor:pointer;box-shadow:0 0 20px #ff006e}
.center{min-height:82vh;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:20px;position:relative}
.stars{position:absolute;inset:0;pointer-events:none;font-size:22px;opacity:.9}
.crownBig{font-size:90px;filter:drop-shadow(0 0 30px gold);animation:float 2s infinite alternate}
@keyframes float{from{transform:translateY(0) rotate(-3deg)}to{transform:translateY(-12px) rotate(3deg)}}
h1{font-size:52px;margin:5px 0;line-height:1}.subtitle{opacity:.9;max-width:420px}
.enterBtn{margin-top:26px;padding:18px 70px;font-family:'Great Vibes',cursive;font-size:48px;border:none;border-radius:60px;background:linear-gradient(90deg,#ff006e,#ffd700,#00e5ff);color:#000;box-shadow:0 0 40px #ff006e,0 0 70px #ffd700;cursor:pointer;transition:.2s}
.enterBtn:active{transform:scale(.96)}
.decor{margin-top:18px;font-size:26px;letter-spacing:6px}
.small{font-size:12px;opacity:.7;margin-top:12px}
.card{background:rgba(255,255,255,.08);border:2px solid rgba(255,255,255,.35);border-radius:26px;padding:20px;margin:14px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.box{background:linear-gradient(160deg,rgba(255,255,255,.18),rgba(0,0,0,.4));border:2px solid #fff;border-radius:24px;padding:22px 10px;text-align:center;cursor:pointer}
.box b{font-size:17px}.box span{font-size:38px;display:block}
.btn{width:100%;padding:14px;border:none;border-radius:25px;font-weight:900;background:#ffd700;margin:6px 0;cursor:pointer}
.btn2{width:100%;padding:13px;border-radius:25px;border:2px solid #00e5ff;background:transparent;color:#00e5ff;font-weight:900;margin:6px 0;cursor:pointer}
.opt{width:100%;padding:13px;margin:7px 0;border-radius:16px;border:2px solid #fff;background:rgba(0,0,0,.5);color:white;font-weight:700;cursor:pointer;text-align:left}
.opt:hover{background:#ff006e}
input{width:100%;padding:13px;border-radius:14px;border:none;margin:8px 0}
.hidden{display:none}
.leadRow{display:flex;justify-content:space-between;padding:10px 12px;background:rgba(0,0,0,.45);border-radius:14px;margin:6px 0}
.badge{display:inline-block;padding:5px 10px;border-radius:20px;background:rgba(0,0,0,.5);border:1px solid #ffd700;font-size:12px;margin:3px}
.cool{font-size:38px;font-weight:900;color:#ffd700}
.count{font-size:60px;font-weight:900;color:#ffd700}
.footer{text-align:center;padding:16px;font-size:12px;opacity:.8}
</style></head><body>
<div class="topbar"><div class="logo">👑 INFINITY BOT</div><div class="profile" id="profileIcon" onclick="showProfile()">👤</div></div>

<!-- PAGE 1 HOME -->
<div id="page-home" class="center">
<div class="stars">✨ 💖 ⭐ 🌟 💫 ⭐ ✨ 💖 ⭐ 🌟</div>
<div class="crownBig">👑</div>
<h1 class="cursive" style="font-size:68px;">Infinity Bot</h1>
<p style="letter-spacing:3px;font-weight:900">DOMINIC MASTIRIA</p>
<p class="subtitle">Riddles • Bible Fight • Sci-Fi • WhatsApp<br>Your wins take you to the top 👑</p>
<button class="enterBtn" onclick="enterSite()">Enter</button>
<div class="decor">✨ 💖 👑 💖 ✨</div>
<div class="small">Press ENTER to register your account & enter Dashboard</div>
<div class="small">INFINITY BOT © 2026 • Lusaka, Zambia 🇿🇲</div>
</div>

<!-- PAGE 2 DASHBOARD -->
<div id="page-dash" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 20px">
<div style="text-align:center"><h2 class="cursive" style="font-size:44px;margin:10px 0">Welcome, <span id="userName">Player</span> 👑</h2><span class="badge">🏆 Wins: <b id="myWins">0</b></span><span class="badge">❌ Losses: <b id="myLoss">0</b></span><span class="badge">⭐ Rank: <b id="myRank">#-</b></span></div>
<div class="grid">
<div class="box" onclick="openRiddles()"><span>🧩</span><b>RIDDLES</b><br><small>5 Types • 10 Qs</small></div>
<div class="box" onclick="openBible()"><span>📖</span><b>BIBLE FIGHT</b><br><small>4 Types • 10 Qs</small></div>
<div class="box" onclick="openComing('SCI-FI')"><span>🚀</span><b>SCI-FI</b><br><small>Coming Soon</small></div>
<div class="box" onclick="openComing('WHATSAPP')"><span>💚</span><b>WHATSAPP</b><br><small>Coming Soon</small></div>
</div>

<div class="card"><h3 style="text-align:center;margin:0 0 8px">🏆 LEADERBOARD 🏆</h3><p style="text-align:center;font-size:12px;opacity:.8">Higher = More Wins, Fewer Losses</p><div id="leaderList">Loading...</div><button class="btn2" onclick="loadLeader()">🔄 Refresh Leaderboard</button></div>
<div class="footer">Press a box to play • Every answer counts!</div>
</div>

<!-- PAGE 3 RIDDLES / BIBLE -->
<div id="page-game" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 20px">
<button class="btn2" onclick="goDash()">← Back to Dashboard</button>
<div class="card"><h2 id="gameTitle" style="text-align:center">🧩 RIDDLES</h2><div id="gameBody"></div></div>
</div>

<!-- PAGE 4 COMING SOON -->
<div id="page-coming" class="hidden" style="max-width:520px;margin:0 auto;padding:40px 20px;text-align:center">
<div style="font-size:80px">🚀</div><h1 class="cursive" style="font-size:54px">Coming Soon</h1><h2 id="comingName">SCI-FI</h2><p>Launching on<br><b>25th December 2026</b></p><p>Returning to Dashboard in:</p><div class="count" id="countDown">10</div><p>✨ Please wait...</p>
</div>

<!-- PROFILE MODAL -->
<div id="profileBox" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px"><div class="card"><h3>👤 My Profile</h3><p>Name: <b id="pName"></b></p><p>Wins: <b id="pWins"></b> • Losses: <b id="pLoss"></b></p><p>Account registered on this device ✅</p><button class="btn" onclick="closeProfile()">Close</button></div></div>

<script>
let user = JSON.parse(localStorage.getItem('inf_user')||'null');
let wins = parseInt(localStorage.getItem('inf_wins')||'0');
let losses = parseInt(localStorage.getItem('inf_loss')||'0');
let currentMode='', currentCat='', qIndex=0, qList=[], score=0, roundWins=0, roundLoss=0, prevRank=0;

function save(){localStorage.setItem('inf_user',JSON.stringify(user));localStorage.setItem('inf_wins',wins);localStorage.setItem('inf_loss',losses); syncServer();}
function syncServer(){ if(!user) return; fetch('/api/score',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:user.name,wins:wins,losses:losses})}).then(()=>loadLeader()); }
function showPage(id){['page-home','page-dash','page-game','page-coming'].forEach(p=>document.getElementById(p).classList.add('hidden')); document.getElementById(id).classList.remove('hidden'); window.scrollTo(0,0);}
function updateMe(){ document.getElementById('userName').innerText=user?user.name:'Player'; document.getElementById('myWins').innerText=wins; document.getElementById('myLoss').innerText=losses; document.getElementById('pName').innerText=user?user.name:''; document.getElementById('pWins').innerText=wins; document.getElementById('pLoss').innerText=losses; }
function enterSite(){
 if(!user){
   let n = prompt('Enter your name to register 👑 (or Google Name):');
   if(!n) n='Player'+Math.floor(Math.random()*999);
   // Google-style register - just name for now, saved as account
   user={name:n, email:n.toLowerCase().replace(/ /g,'')+'@gmail.com'};
   wins=0; losses=0; save();
   alert('Welcome '+n+' 👑 Your account is registered! You are now on the Leaderboard!');
 }
 updateMe(); showPage('page-dash'); loadLeader();
}
function showProfile(){ if(!user){alert('Press ENTER first to register!');return;} updateMe(); document.getElementById('profileBox').classList.remove('hidden');}
function closeProfile(){document.getElementById('profileBox').classList.add('hidden');}
function goDash(){showPage('page-dash'); updateMe(); loadLeader();}
function loadLeader(){ fetch('/api/leaderboard').then(r=>r.json()).then(d=>{
  let sorted=d.sort((a,b)=>(b.wins-b.losses)-(a.wins-a.losses));
  let myIdx = sorted.findIndex(x=>user && x.name===user.name);
  document.getElementById('myRank').innerText = myIdx>=0 ? '#'+(myIdx+1) : '#-';
  prevRank = myIdx>=0?myIdx+1:999;
  let html='';
  if(sorted.length===0) html='<p style="text-align:center">No players yet - Be the first 👑</p>';
  sorted.slice(0,10).forEach((p,i)=>{ html+=`<div class="leadRow"><span>${i+1}. ${i==0?'👑':''} ${p.name}</span><span>✅ ${p.wins} Wins • ❌ ${p.losses} Loss</span></div>`; });
  document.getElementById('leaderList').innerHTML=html;
});}
function openRiddles(){ currentMode='riddle'; showPage('page-game'); document.getElementById('gameTitle').innerText='🧩 RIDDLES'; document.getElementById('gameBody').innerHTML=`<p style="text-align:center">What kind of riddles?</p>
<button class="opt" onclick="startGame('riddle','Brain Teasers')">1. 🧠 Brain Teasers</button>
<button class="opt" onclick="startGame('riddle','Love Riddles')">2. 💖 Love Riddles</button>
<button class="opt" onclick="startGame('riddle','Funny Riddles')">3. 😂 Funny Riddles</button>
<button class="opt" onclick="startGame('riddle','Smart Riddles')">4. 🎓 Smart Riddles</button>
<button class="opt" onclick="startGame('riddle','Programmers Riddles')">5. 💻 Programmers Riddles</button>`;}
function openBible(){ currentMode='bible'; showPage('page-game'); document.getElementById('gameTitle').innerText='📖 BIBLE FIGHT'; document.getElementById('gameBody').innerHTML=`<p style="text-align:center">Choose your fight:</p>
<button class="opt" onclick="startGame('bible','Random Bible')">1. 🎲 Random Bible Questions</button>
<button class="opt" onclick="startGame('bible','Old Testament')">2. 📜 Old Testament Story Questions</button>
<button class="opt" onclick="startGame('bible','New Testament')">3. ✝️ New Testament Story Questions</button>
<button class="opt" onclick="startGame('bible','Name Questions')">4. 🏷️ Name Questions</button>`;}

const RIDDLES={
 'Brain Teasers':[
  {q:'I speak without a mouth, hear without ears. What am I?',o:['Echo','Phone','Wind'],a:0},
  {q:'What has keys but cannot open a lock?',o:['Piano','Door','Map'],a:0},
  {q:'What gets wetter the more it dries?',o:['Towel','Rain','Soap'],a:0},
  {q:'What has a face and two hands but no arms or legs?',o:['Clock','Mirror','Robot'],a:0},
  {q:'What can you catch but never throw?',o:['A Cold','A Ball','A Fish'],a:0},
  {q:'What has many needles but never sews?',o:['Christmas Tree','Doctor','Porcupine'],a:0},
  {q:'What goes up but never comes down?',o:['Age','Balloon','Rocket'],a:0},
  {q:'What has one eye but cannot see?',o:['Needle','Camera','Cyclops'],a:0},
  {q:'What runs but never walks?',o:['Water','Cheetah','Car'],a:0},
  {q:'What has a head and tail but no body?',o:['Coin','Snake','Cat'],a:0}],
 'Love Riddles':[
  {q:'What is full of love but never gets tired?',o:['Heart','Phone','Brain'],a:0},
  {q:'I am always with you, I grow when you share me. What am I?',o:['Love','Money','Food'],a:0},
  {q:'What can you give and still keep?',o:['A Smile','A Car','A House'],a:0},
  {q:'What did the heart say to the brain?',o:['I love you','Think more','Sleep'],a:0},
  {q:'What is red, beats fast when you see your crush?',o:['Heart','Tomato','Rose'],a:0},
  {q:'What is the language of love?',o:['Kindness','English','French'],a:0},
  {q:'What do lovers hold that never breaks?',o:['Hands','Glass','Promise'],a:0},
  {q:'What is sweeter than honey in love?',o:['A Kiss','Sugar','Cake'],a:0},
  {q:'What flies without wings in love?',o:['Butterflies in stomach','Bird','Plane'],a:0},
  {q:'What is the best gift in love?',o:['Time','Gold','Car'],a:0}],
 'Funny Riddles':[
  {q:'Why did the chicken cross the road?',o:['To get to the other side','To dance','To sleep'],a:0},
  {q:'What do you call a fish without eyes?',o:['Fsh','Blind fish','Nemo'],a:0},
  {q:'Why did the scarecrow win an award?',o:['Outstanding in his field','He is funny','He is tall'],a:0},
  {q:'What is orange and sounds like a parrot?',o:['Carrot','Orange','Mango'],a:0},
  {q:'Why did the math book look sad?',o:['Too many problems','No friends','It is old'],a:0},
  {q:'What do you call cheese that is not yours?',o:['Nacho Cheese','My Cheese','Stolen Cheese'],a:0},
  {q:'Why did the cookie go to hospital?',o:['It felt crumby','It fell','It was hungry'],a:0},
  {q:'What did one wall say to the other?',o:['I will meet you at the corner','Hello','Bye'],a:0},
  {q:'Why are ghosts bad liars?',o:['You can see through them','They are scary','They whisper'],a:0},
  {q:'What has 4 wheels and flies?',o:['Garbage Truck','Plane','Car'],a:0}],
 'Smart Riddles':[
  {q:'2, 6, 12, 20, 30, ?',o:['42','36','40'],a:0},
  {q:'If you have 3 apples and take away 2, how many do you have?',o:['2','1','3'],a:0},
  {q:'What is 15 + 15 - 10?',o:['20','15','30'],a:0},
  {q:'Which is heavier: 1kg steel or 1kg feathers?',o:['Same','Steel','Feathers'],a:0},
  {q:'How many months have 28 days?',o:['All of them','1','2'],a:0},
  {q:'What comes once in a minute, twice in a moment, never in 1000 years?',o:['Letter M','Letter O','Time'],a:0},
  {q:'I am an odd number. Take away a letter and I become even. What am I?',o:['Seven','Nine','Five'],a:0},
  {q:'What is half of 2+2?',o:['3','2','4'],a:0},
  {q:'If a plane crashes on Zambia-Zimbabwe border, where bury survivors?',o:['Nowhere, survivors alive','Zambia','Zimbabwe'],a:0},
  {q:'How many sides does a hexagon have?',o:['6','5','8'],a:0}],
 'Programmers Riddles':[
  {q:'What does HTML stand for?',o:['HyperText Markup Language','High Text Machine Language','Hyper Tool Markup Language'],a:0},
  {q:'Which language is used to style websites?',o:['CSS','Python','Java'],a:0},
  {q:'What is the brain of a computer?',o:['CPU','RAM','Keyboard'],a:0},
  {q:'What does WWW stand for?',o:['World Wide Web','World Web Wide','Wide World Web'],a:0},
  {q:'Which symbol is used for comments in Python?',o:['#','//','/*'],a:0},
  {q:'What is a bug in coding?',o:['An error','An insect','A feature'],a:0},
  {q:'Which tag makes a link in HTML?',o:['<a>','<p>','<link>'],a:0},
  {q:'What does AI stand for?',o:['Artificial Intelligence','Amazing Internet','Automatic Info'],a:0},
  {q:'What do you call a file that runs a website?',o:['index.html','photo.jpg','music.mp3'],a:0},
  {q:'Python is a...',o:['Programming Language','Snake only','Game'],a:0}],
};
const BIBLE={
 'Random Bible':[
  {q:'Who built the Ark?',o:['Noah','Moses','David'],a:0},{q:'How many days did God create the world?',o:['6','7','10'],a:0},{q:'Who was swallowed by a big fish?',o:['Jonah','Peter','Paul'],a:0},{q:'What is the first book of the Bible?',o:['Genesis','Exodus','Matthew'],a:0},{q:'Who killed Goliath?',o:['David','Saul','Samson'],a:0},{q:'Who was the mother of Jesus?',o:['Mary','Ruth','Esther'],a:0},{q:'How many disciples did Jesus have?',o:['12','10','7'],a:0},{q:'What did Moses part?',o:['Red Sea','Jordan River','Lake'],a:0},{q:'Who wrote many Psalms?',o:['David','Solomon','Abraham'],a:0},{q:'What book tells of the birth of Jesus?',o:['Matthew','Genesis','Revelation'],a:0}],
 'Old Testament':[
  {q:'Who led Israel out of Egypt?',o:['Moses','Aaron','Joshua'],a:0},{q:'What did God give Moses on the mountain?',o:['10 Commandments','Ark','Crown'],a:0},{q:'Who was thrown into the lions den?',o:['Daniel','Joseph','Jacob'],a:0},{q:'Who had a coat of many colours?',o:['Joseph','Benjamin','Reuben'],a:0},{q:'Who built the Tower of Babel people?',o:['People of Babel','Noah','Abraham'],a:0},{q:'Who was the first man?',o:['Adam','Noah','Abraham'],a:0},{q:'Who was the first woman?',o:['Eve','Sarah','Rebekah'],a:0},{q:'Who fought Samson?',o:['Philistines','Egyptians','Romans'],a:0},{q:'What did David use to kill Goliath?',o:['Stone & Sling','Sword','Spear'],a:0},{q:'Who was taken up in a chariot of fire?',o:['Elijah','Elisha','Enoch'],a:0}],
 'New Testament':[
  {q:'Where was Jesus born?',o:['Bethlehem','Nazareth','Jerusalem'],a:0},{q:'Who baptized Jesus?',o:['John the Baptist','Peter','Paul'],a:0},{q:'How many loaves did Jesus use to feed 5000?',o:['5','7','12'],a:0},{q:'Who denied Jesus 3 times?',o:['Peter','Judas','Thomas'],a:0},{q:'Who betrayed Jesus?',o:['Judas','Peter','John'],a:0},{q:'On which day did Jesus rise?',o:['Sunday','Friday','Saturday'],a:0},{q:'Who was the first to see risen Jesus?',o:['Mary Magdalene','Peter','John'],a:0},{q:'Who wrote Revelation?',o:['John','Paul','Luke'],a:0},{q:'What is the last book of the Bible?',o:['Revelation','Jude','Acts'],a:0},{q:'Who was Saul who became Paul?',o:['Apostle Paul','Peter','Stephen'],a:0}],
 'Name Questions':[
  {q:'What does the name Emmanuel mean?',o:['God with us','God is great','Peace'],a:0},{q:'What does Jesus name mean?',o:['Saviour','King','Teacher'],a:0},{q:'Who was called the Father of Faith?',o:['Abraham','Moses','Jacob'],a:0},{q:'Who was called the Beloved Disciple?',o:['John','Peter','James'],a:0},{q:'What does the name David mean?',o:['Beloved','Strong','King'],a:0},{q:'Who was named Israel?',o:['Jacob','Joseph','Esau'],a:0},{q:'What does the name Moses mean?',o:['Drawn out of water','Leader','Prince'],a:0},{q:'Who was called the Weeping Prophet?',o:['Jeremiah','Isaiah','Ezekiel'],a:0},{q:'What does the name Gabriel mean?',o:['God is my strength','Messenger','Angel'],a:0},{q:'Who was called the Rock?',o:['Peter','Paul','Andrew'],a:0}],
};
function startGame(mode,cat){ currentMode=mode; currentCat=cat; qIndex=0; score=0; roundWins=0; roundLoss=0; qList = mode=='riddle'? [...RIDDLES[cat]] : [...BIBLE[cat]]; showQuestion(); }
function showQuestion(){
 if(qIndex>=10){ finishRound(); return; }
 let q=qList[qIndex];
 document.getElementById('gameBody').innerHTML=`<p><b>Question ${qIndex+1} / 10</b> • ${currentCat}</p><p style="font-size:18px"><b>${q.q}</b></p>`+q.o.map((opt,i)=>`<button class="opt" onclick="answerQ(${i})">${['A','B','C'][i]}) ${opt}</button>`).join('')+`<p>✅ Wins this round: ${roundWins} • ❌ Losses: ${roundLoss}</p>`;
}
function answerQ(i){
 let q=qList[qIndex];
 if(i===q.a){ wins++; roundWins++; score++; alert('✅ CORRECT! +1 WIN 👑'); } else { losses++; roundLoss++; alert('❌ WRONG! Correct was: '+q.o[q.a]); }
 save(); updateMe(); qIndex++; showQuestion();
}
function finishRound(){
 let isBible = currentMode=='bible';
 let cool = isBible?30:60;
 document.getElementById('gameBody').innerHTML=`<h3 style="text-align:center">⏳ Calculating...</h3><p style="text-align:center">Bot is calculating your correct & wrong answers<br>Preparing next questions...</p><div class="cool" style="text-align:center"><span id="coolT">${cool}</span> sec</div><p style="text-align:center">Score: ${score}/10<br>Wins: +${roundWins} • Losses: +${roundLoss}</p>`;
 let t=cool; let iv=setInterval(()=>{
   t--; document.getElementById('coolT').innerText=t;
   if(t<=0){ clearInterval(iv); showResult(); }
 },1000);
}
function showResult(){
 // reload leaderboard to see rank move
 fetch('/api/leaderboard').then(r=>r.json()).then(d=>{
   let sorted=d.sort((a,b)=>(b.wins-b.losses)-(a.wins-a.losses));
   let newRank = sorted.findIndex(x=>user && x.name===user.name)+1;
   let move = newRank < prevRank ? '📈 You MOVED UP! 👑' : newRank > prevRank ? '📉 You moved DOWN - Play again!' : '➡️ Same rank - Keep pushing!';
   document.getElementById('gameBody').innerHTML=`<h2 style="text-align:center">🏁 ROUND DONE!</h2><p style="text-align:center;font-size:22px">Your Marks: <b>${score}/10</b></p><p style="text-align:center">Wins: ${roundWins} • Losses: ${roundLoss}<br>Your Rank: <b>#${newRank}</b><br>${move}</p><button class="btn" onclick="startGame(currentMode,currentCat)">🔁 Continue with ${currentCat}</button><button class="btn2" onclick="openRiddles()">Change Riddle Type</button><button class="btn2" onclick="openBible()">Change Bible Type</button><button class="btn2" onclick="goDash()">🏠 Dashboard</button>`;
   prevRank=newRank;
 });
}
function openComing(name){
 showPage('page-coming'); document.getElementById('comingName').innerText=name+' - COMING SOON';
 let t=10; document.getElementById('countDown').innerText=t;
 let iv=setInterval(()=>{ t--; document.getElementById('countDown').innerText=t; if(t<=0){ clearInterval(iv); goDash(); } },1000);
}
if(user){ updateMe(); }
loadLeader();
</script></body></html>"""

@app.route("/")
def home():
    return HOME

@app.route("/api/leaderboard")
def api_leader():
    arr = [{"name":k,"wins":v["wins"],"losses":v["losses"]} for k,v in leaderboard.items()]
    return jsonify(arr)

@app.route("/api/score", methods=["POST"])
def api_score():
    d = request.get_json() or {}
    name = d.get("name","Player")
    leaderboard[name] = {"wins": int(d.get("wins",0)), "losses": int(d.get("losses",0))}
    return jsonify({"ok":True})

@app.route("/webhook", methods=["GET","POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode"); token = request.args.get("hub.verify_token"); challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        return "Forbidden", 403
    data = request.get_json() or {}
    try:
        entry = data["entry"][0]["changes"][0]["value"]
        for m in entry.get("messages", []):
            sender = m.get("from"); text = m.get("text", {}).get("body", "")
            if sender and text:
                send_whatsapp(sender, handle_command(sender, text))
    except Exception as e: print(e)
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
