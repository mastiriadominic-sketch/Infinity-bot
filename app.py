from flask import Flask, request, jsonify
import os, random

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Infinity Bot</title>
<style>
body{margin:0;font-family:Arial;background:#0b0b1a;color:white;text-align:center}
.top{padding:12px;background:#111133;display:flex;justify-content:space-between}
button{background:#ffcc00;color:black;border:0;padding:12px 20px;border-radius:10px;font-weight:bold;margin:6px;font-size:16px}
input{padding:12px;width:85%;margin:6px;border-radius:10px;border:0;font-size:16px}
.card{background:#1a1a3a;margin:12px;padding:16px;border-radius:14px}
.page{display:none;padding:10px}
.gamebox{background:#222244;padding:14px;margin:10px;border-radius:12px}
</style>
</head>
<body>
<div class="top"><div>♾️ INFINITY</div><div id="catClock">Loading CAT...</div></div>

<div id="page-welcome" class="page" style="display:block">
<div class="card"><h1>♾️ Welcome to Infinity</h1><p>Play • Win • Rank Up</p><button id="enterBtn">Enter ➡️</button></div>
<div class="card"><p>🕐 CAT Time is live above</p></div>
</div>

<div id="page-register" class="page">
<div class="card"><h2>Register</h2><input id="regName" placeholder="Username"><input id="regPhone" placeholder="Phone"><button onclick="doRegister()">Create Account</button><br><button onclick="showPage('page-login')">Have Account? Login</button><br><button onclick="showPage('page-welcome')">Back</button></div>
</div>

<div id="page-login" class="page">
<div class="card"><h2>Login</h2><input id="logName" placeholder="Username"><button onclick="doLogin()">Login</button><br><button onclick="showPage('page-register')">No Account? Register</button></div>
</div>

<div id="page-home" class="page">
<div class="card"><h2 id="welcomeUser">Hello Player 👋</h2><p>Balance: <b id="balance">1000</b> Coins</p><p>Rank: <b id="rankLabel">Bronze</b></p></div>
<div class="card"><h3>🎮 Games</h3><button onclick="showPage('page-dice')">🎲 Dice</button><button onclick="showPage('page-coin')">🪙 Coin Flip</button><button onclick="showPage('page-number')">🔢 Number Guess</button><button onclick="showPage('page-slot')">🎰 Slots</button><button onclick="showPage('page-rps')">✂️ Rock Paper</button><button onclick="showPage('page-highlow')">⬆️ High / Low</button></div>
<div class="card"><button onclick="showPage('page-rank')">🏆 Rank Board</button><button onclick="doLogout()">Logout</button></div>
</div>

<div id="page-dice" class="page"><div class="card"><h2>🎲 Dice</h2><p id="diceRes">Tap Roll</p><button onclick="playDice()">Roll Dice</button><br><button onclick="showPage('page-home')">Back</button></div></div>
<div id="page-coin" class="page"><div class="card"><h2>🪙 Coin Flip</h2><p id="coinRes">Heads or Tails?</p><button onclick="playCoin('Heads')">Heads</button><button onclick="playCoin('Tails')">Tails</button><br><button onclick="showPage('page-home')">Back</button></div></div>
<div id="page-number" class="page"><div class="card"><h2>🔢 Guess 1-10</h2><input id="guessNum" type="number" placeholder="1 to 10"><p id="numRes"></p><button onclick="playNumber()">Guess</button><br><button onclick="showPage('page-home')">Back</button></div></div>
<div id="page-slot" class="page"><div class="card"><h2>🎰 Slots</h2><p id="slotRes">🍒 🍒 🍒</p><button onclick="playSlot()">Spin</button><br><button onclick="showPage('page-home')">Back</button></div></div>
<div id="page-rps" class="page"><div class="card"><h2>✂️ Rock Paper Scissors</h2><p id="rpsRes"></p><button onclick="playRps('Rock')">Rock</button><button onclick="playRps('Paper')">Paper</button><button onclick="playRps('Scissors')">Scissors</button><br><button onclick="showPage('page-home')">Back</button></div></div>
<div id="page-highlow" class="page"><div class="card"><h2>⬆️ High / Low</h2><p id="hlRes">Next card higher or lower than 5?</p><button onclick="playHL('high')">Higher</button><button onclick="playHL('low')">Lower</button><br><button onclick="showPage('page-home')">Back</button></div></div>
<div id="page-rank" class="page"><div class="card"><h2>🏆 Rank Board</h2><div id="rankList"></div><br><button onclick="showPage('page-home')">Back</button></div></div>

<script>
var balance = 1000;
var myName = "Player";
function showPage(id){
  var pages = document.querySelectorAll('.page');
  for(var i=0;i<pages.length;i++){ pages[i].style.display='none'; }
  var p = document.getElementById(id);
  if(p){ p.style.display='block'; }
  if(id==='page-rank'){ loadRank(); }
  window.scrollTo(0,0);
}
function catNow(){ return new Date(); }
function updateCatTime(){
  try{
    var el = document.getElementById('catClock');
    if(el){
      var d = catNow();
      el.innerText = d.toLocaleTimeString('en-GB') + ' CAT';
    }
  }catch(e){}
}
function goRegister(){ showPage('page-register'); }
function doRegister(){
  var n = document.getElementById('regName').value;
  if(!n){ alert('Enter username'); return; }
  myName = n;
  document.getElementById('welcomeUser').innerText = 'Hello ' + myName + ' 👋';
  showPage('page-home');
}
function doLogin(){
  var n = document.getElementById('logName').value;
  if(!n){ alert('Enter username'); return; }
  myName = n;
  document.getElementById('welcomeUser').innerText = 'Hello ' + myName + ' 👋';
  showPage('page-home');
}
function doLogout(){ showPage('page-welcome'); }
function updateBalance(){
  document.getElementById('balance').innerText = balance;
  var r = 'Bronze';
  if(balance>=5000){ r='Diamond'; } else if(balance>=3000){ r='Gold'; } else if(balance>=1500){ r='Silver'; }
  document.getElementById('rankLabel').innerText = r;
}
function playDice(){
  var v = Math.floor(Math.random()*6)+1;
  var win = (v>=4);
  if(win){ balance+=100; } else { balance-=50; }
  document.getElementById('diceRes').innerText = 'You rolled ' + v + (win?' - YOU WIN +100':' - LOSE -50');
  updateBalance();
}
function playCoin(choice){
  var c = Math.random()>0.5 ? 'Heads':'Tails';
  var win = (c===choice);
  if(win){ balance+=100; } else { balance-=50; }
  document.getElementById('coinRes').innerText = 'It was ' + c + (win?' - WIN +100':' - LOSE -50');
  updateBalance();
}
function playNumber(){
  var g = parseInt(document.getElementById('guessNum').value);
  var target = Math.floor(Math.random()*10)+1;
  var win = (g===target);
  if(win){ balance+=500; } else { balance-=50; }
  document.getElementById('numRes').innerText = 'Number was ' + target + (win?' - JACKPOT +500':' - LOSE -50');
  updateBalance();
}
function playSlot(){
  var em = ['🍒','🍋','⭐','💎','7️⃣'];
  var a = em[Math.floor(Math.random()*em.length)];
  var b = em[Math.floor(Math.random()*em.length)];
  var c = em[Math.floor(Math.random()*em.length)];
  var win = (a===b && b===c);
  if(win){ balance+=300; } else { balance-=50; }
  document.getElementById('slotRes').innerText = a+' '+b+' '+c+(win?' - JACKPOT +300':' - LOSE -50');
  updateBalance();
}
function playRps(choice){
  var opts = ['Rock','Paper','Scissors'];
  var comp = opts[Math.floor(Math.random()*3)];
  var win = (choice==='Rock'&&comp==='Scissors')||(choice==='Paper'&&comp==='Rock')||(choice==='Scissors'&&comp==='Paper');
  var draw = (choice===comp);
  if(!draw && win){ balance+=100; } else if(!draw){ balance-=50; }
  document.getElementById('rpsRes').innerText = 'Computer: '+comp+(draw?' - DRAW':(win?' - WIN +100':' - LOSE -50'));
  updateBalance();
}
function playHL(choice){
  var card = Math.floor(Math.random()*10)+1;
  var win = (choice==='high' && card>5) || (choice==='low' && card<5);
  if(win){ balance+=100; } else { balance-=50; }
  document.getElementById('hlRes').innerText = 'Card was '+card+(win?' - WIN +100':' - LOSE -50');
  updateBalance();
}
function loadRank(){
  var list = document.getElementById('rankList');
  list.innerHTML = '1. '+myName+' - '+balance+' coins<br>2. Champion - 4800<br>3. Star - 3200<br>4. Pro - 2100<br>5. Newbie - 900';
}
try{
  var eb = document.getElementById('enterBtn');
  if(eb){ eb.onclick = function(){ goRegister(); }; }
}catch(e){}
setInterval(updateCatTime,1000);
updateCatTime();
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return HTML

@app.route('/health')
def health():
    return jsonify({"status":"ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
