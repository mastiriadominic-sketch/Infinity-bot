from flask import Flask, request, jsonify
import os, requests, time, datetime
app = Flask(__name__)
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN","infinity")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN","")
PHONE_ID = os.environ.get("PHONE_NUMBER_ID","")
USERS={}
def get_capacity():
    try:
        now=datetime.datetime.now()
        upgrade=datetime.datetime(2026,12,25,0,0,0)
        return 10000 if now>=upgrade else 1000
    except: return 1000
def send_whatsapp(to,text):
    if not WHATSAPP_TOKEN or not PHONE_ID: return
    try: requests.post(f"https://graph.facebook.com/v21.0/{PHONE_ID}/messages",headers={"Authorization":f"Bearer {WHATSAPP_TOKEN}","Content-Type":"application/json"},json={"messaging_product":"whatsapp","to":to,"type":"text","text":{"body":text}},timeout=10)
    except: pass
HOME=r"""<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>INFINITY BOT</title>
<link href="https://fonts.googleapis.com/css2?family=Great+Vibes&family=Poppins:wght@400;700;900&display=swap" rel="stylesheet">
<style>*{box-sizing:border-box}body{margin:0;font-family:Poppins,Arial;color:white;background:radial-gradient(circle at 50% 20%,#3a0a5e,#12002b 70%);min-height:100vh}.cursive{font-family:'Great Vibes',cursive}.topbar{display:flex;justify-content:space-between;align-items:center;padding:8px 14px}.profile{width:46px;height:46px;border-radius:50%;background:linear-gradient(135deg,#ff006e,#ffd700);display:flex;align-items:center;justify-content:center;font-size:20px;border:2px solid #fff;cursor:pointer;position:relative;box-shadow:0 0 20px #ff006e}.notif{position:absolute;top:-6px;right:-6px;background:red;color:white;font-size:11px;width:20px;height:20px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:900}.center{min-height:82vh;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:20px}.crownBig{font-size:90px;filter:drop-shadow(0 0 30px gold)}.enterBtn{margin-top:20px;padding:16px 70px;font-family:'Great Vibes',cursive;font-size:48px;border:none;border-radius:60px;background:linear-gradient(90deg,#ff006e,#ffd700,#00e5ff);color:#000;box-shadow:0 0 40px #ff006e;cursor:pointer}.card{background:rgba(255,255,255,.08);border:2px solid rgba(255,255,255,.35);border-radius:26px;padding:20px;margin:14px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.box{background:linear-gradient(160deg,rgba(255,255,255,.18),rgba(0,0,0,.4));border:2px solid #fff;border-radius:24px;padding:22px 10px;text-align:center;cursor:pointer}.box span{font-size:38px;display:block}.btn{width:100%;padding:14px;border:none;border-radius:25px;font-weight:900;background:#ffd700;margin:6px 0;cursor:pointer}.btn2{width:100%;padding:13px;border-radius:25px;border:2px solid #00e5ff;background:transparent;color:#00e5ff;font-weight:900;margin:6px 0;cursor:pointer}.opt{width:100%;padding:13px;margin:7px 0;border-radius:16px;border:2px solid #fff;background:rgba(0,0,0,.5);color:white;font-weight:700;cursor:pointer;text-align:left}input{width:100%;padding:14px;border-radius:14px;border:2px solid #ffd700;margin:8px 0;font-size:16px;background:#fff;color:#000}.hidden{display:none}.leadRow{display:flex;justify-content:space-between;align-items:center;padding:10px 12px;background:rgba(0,0,0,.45);border-radius:14px;margin:6px 0;cursor:pointer}.dot{width:12px;height:12px;border-radius:50%;display:inline-block}.green{background:#00ff00;box-shadow:0 0 10px #00ff00}.red{background:#ff2222;box-shadow:0 0 10px #ff2222}.badge{display:inline-block;padding:5px 10px;border-radius:20px;background:rgba(0,0,0,.5);border:1px solid #ffd700;font-size:12px;margin:3px}.count{font-size:60px;font-weight:900;color:#ffd700}.toast{position:fixed;top:70px;left:50%;transform:translateX(-50%);background:#fff;color:#000;padding:12px 18px;border-radius:20px;font-weight:700;z-index:99;max-width:90%;text-align:center}.regInput{font-size:18px;text-align:center;letter-spacing:2px}
.msgFab{position:fixed;right:16px;bottom:16px;width:62px;height:62px;border-radius:50%;background:linear-gradient(135deg,#ff006e,#ffd700,#00e5ff);display:flex;align-items:center;justify-content:center;font-size:30px;border:3px solid #fff;box-shadow:0 0 25px #ff006e;cursor:pointer;z-index:50}
.chatRow{display:flex;justify-content:space-between;align-items:center;padding:12px;background:rgba(0,0,0,.45);border-radius:16px;margin:8px 0}.chatBtn{width:36px;height:36px;border-radius:50%;border:2px solid #fff;background:linear-gradient(135deg,#00e5ff,#ff006e);display:inline-flex;align-items:center;justify-content:center;font-size:18px;cursor:pointer;margin-left:6px}.chatBox{background:#1a1a2e;border-radius:20px;padding:12px;min-height:320px;max-height:380px;overflow-y:auto}.bubble{max-width:80%;padding:10px 14px;border-radius:18px;margin:6px 0;font-size:14px}.mine{background:#ffd700;color:#000;margin-left:auto}.theirs{background:rgba(255,255,255,.2);color:#fff}
.msgBarWrap{display:flex;align-items:center;gap:8px;margin-top:12px}.msgBar{flex:1;display:flex;align-items:center;gap:10px;background:#2b2b33;border-radius:999px;padding:10px 12px}.msgBar .emojiBtn{font-size:22px;background:none;border:none;cursor:pointer}.msgBar input{flex:1;background:transparent;border:none;outline:none;color:#fff;font-size:16px;padding:0;margin:0}.msgBar input::placeholder{color:#aaa}.msgBar .attachBtn{font-size:20px;background:none;border:none;cursor:pointer}.micBtn{width:52px;height:52px;min-width:52px;border-radius:50%;border:none;background:linear-gradient(135deg,#c39bff,#9a6bff);display:flex;align-items:center;justify-content:center;font-size:24px;cursor:pointer}.sendBtnSmall{width:44px;height:44px;border-radius:50%;border:none;background:#ffd700;font-size:20px;cursor:pointer;display:none}.catTimeTop{font-size:11px;background:rgba(0,0,0,.55);border:1px solid #ffd700;padding:4px 8px;border-radius:20px;display:inline-block}.timer{position:absolute;top:10px;right:12px;background:#ff2222;color:#fff;padding:6px 12px;border-radius:20px;font-weight:900;font-size:18px}.topRight{display:flex;align-items:center;gap:6px}.soundSmall{width:32px;height:32px;border-radius:50%;background:rgba(0,0,0,.55);border:1px solid #ffd700;display:flex;align-items:center;justify-content:center;font-size:16px;cursor:pointer}
</style></head><body>
<div class="topbar"><div><span class="catTimeTop" id="catTime">🕐 Loading CAT...</span><br><div style="font-weight:900;margin-top:4px">👑 INFINITY BOT</div></div><div class="topRight"><div class="soundSmall" id="soundBtn">🔊</div><div class="profile" id="profileBtn">👤<span id="notifBadge" class="notif hidden">1</span></div></div></div>
<div id="toast" class="toast hidden"></div>
<div id="page-home" class="center"><div style="font-size:26px">✨ 💖 ⭐ 🌟 💫</div><div class="crownBig">👑</div><h1 class="cursive" style="font-size:68px;margin:5px">Infinity Bot</h1><p style="letter-spacing:3px;font-weight:900">DOMINIC MASTIRIA</p><p>Riddles • Bible Fight • Sci-Fi • WhatsApp</p><button class="enterBtn" id="enterBtn">Enter</button><div style="margin-top:16px;font-size:26px">✨ 💖 👑 💖 ✨</div><p style="font-size:12px;opacity:.7">Press ENTER to Register / Login</p><p style="font-size:12px;opacity:.7">🎹 Tap ENTER to start Yeshua Instrumental</p></div>
<div id="page-register" class="hidden" style="max-width:520px;margin:0 auto;padding:20px 14px"><button class="btn2" onclick="showPage('page-home')">← Back</button>
<div class="card" style="text-align:center"><div style="font-size:60px">👑</div><h1 class="cursive" style="font-size:48px;margin:5px">Register</h1><p id="regSub">Create your Infinity account 👑</p>
<div id="registerForm"><label style="text-align:left;display:block">Your Name:</label><input id="regName" placeholder="e.g. Chikondi" maxlength="20"><label style="text-align:left;display:block">4-Digit Password:</label><input id="regPass" placeholder="e.g. 5678 - NOT 1234 or 0000" maxlength="4" inputmode="numeric" type="password" class="regInput"><p style="font-size:12px;color:#ffd700">⚠️ Do NOT use 1234 or 0000 - Too easy!</p><button class="btn" onclick="doRegister()">📝 REGISTER</button><p style="font-size:13px;opacity:.8">Already have an account? <b style="color:#ffd700;cursor:pointer" onclick="showLogin()">Click here to Login</b></p></div>
<div id="loginForm" class="hidden"><label style="text-align:left;display:block">Your Name:</label><input id="loginName" placeholder="Your registered name"><label style="text-align:left;display:block">4-Digit Password:</label><input id="loginPass" placeholder="****" maxlength="4" inputmode="numeric" type="password" class="regInput"><button class="btn" onclick="doLogin()">🔓 LOGIN</button><p style="font-size:13px;opacity:.8">New here? <b style="color:#ffd700;cursor:pointer" onclick="showRegister()">Click here to Register</b></p></div>
<p style="font-size:12px;opacity:.7">Chikondi = My Princess 👸<br>Chimwemwe = Her Majesty 👑</p></div></div>
<div id="page-dash" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 20px"><div style="text-align:center"><h2 class="cursive" style="font-size:44px;margin:10px 0" id="welcomeText">Welcome, Player 👑</h2><span class="badge">⭐ Rank: <b id="myRank">#-</b></span><span class="badge">🎯 <b id="myStage">Beginner</b></span><br><span style="font-size:11px;opacity:.7">🎹 Yeshua Playing • Tap 👤 for Wins / Losses / Friends</span></div>
<div class="grid"><div class="box" onclick="openRiddles()"><span>🧩</span><b>RIDDLES</b><br><small>5 Types • 10 Qs</small></div><div class="box" onclick="openBible()"><span>📖</span><b>BIBLE FIGHT</b><br><small>4 Types • 10 Qs</small></div><div class="box" onclick="openComing('SCI-FI')"><span>🚀</span><b>SCI-FI</b><br><small>Coming Soon</small></div><div class="box" onclick="openComing('WHATSAPP')"><span>💚</span><b>WHATSAPP</b><br><small>Coming Soon</small></div></div>
<div class="card"><h3 style="text-align:center;margin:0">🏆 LEADERBOARD 🏆</h3><div id="leaderList">Loading...</div><button class="btn2" onclick="loadLeader()">🔄 Refresh</button></div></div>
<div id="page-game" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 20px"><button class="btn2" onclick="goDash()">← Back to Dashboard</button><div class="card" style="position:relative"><h2 id="gameTitle" style="text-align:center">🧩 RIDDLES</h2><div id="gameBody"></div></div></div>
<div id="page-coming" class="hidden" style="max-width:520px;margin:0 auto;padding:40px 20px;text-align:center"><div style="font-size:80px">🚀</div><h1 class="cursive" style="font-size:54px">Coming Soon</h1><h2 id="comingName">SCI-FI</h2><p>Launching on<br><b>25th December 2026</b></p><p>Returning in:</p><div class="count" id="countDown">5</div></div>
<div id="page-profile" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 20px"><button class="btn2" onclick="goDash()">← Back</button><div class="card" style="text-align:center"><div style="font-size:70px">👤</div><h2 id="profName">Player</h2><p><span id="profDot" class="dot green"></span> <span id="profStatus">Online</span></p><p>⭐ Rank: <b id="profRank">#-</b></p><p>🏆 Wins: <b id="profWins">0</b> | ❌ Losses: <b id="profLoss">0</b></p><p id="profFriends"></p><p>🎯 Stage: <b id="profStage">Beginner</b></p></div>
<div class="card"><h3>📩 Friend Requests</h3><div id="reqList"><p>No requests</p></div></div>
<div class="card"><h3>👥 My Friends</h3><div id="friendList"></div></div></div>
<div id="page-other" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 20px"><button class="btn2" onclick="goDash()">← Back</button><div class="card" style="text-align:center"><div style="font-size:70px">👤</div><h2 id="otherName">Player</h2><p><span id="otherDot" class="dot green"></span> <span id="otherStatus">Online</span></p><p>⭐ Rank: <b id="otherRank">#-</b></p><p><b id="otherWins">0</b> Win | <b id="otherLoss">0</b> Lose</p><div id="otherActions"></div></div></div>
<div id="page-messages" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 20px"><button class="btn2" onclick="goDash()">← Back to Dashboard</button><div class="card"><h1 style="text-align:center;margin:0;font-size:34px">Message</h1><p style="text-align:center;margin:2px 0 12px;opacity:.8;font-size:14px">chats</p><div id="chatFriendList"></div></div></div>
<div id="page-chat" class="hidden" style="max-width:520px;margin:0 auto;padding:0 14px 20px"><button class="btn2" onclick="showPage('page-messages');loadChatList()">← Back to Chats</button><div class="card"><h2 style="text-align:center;margin:0">💬 <span id="chatWith">Friend</span></h2><p style="text-align:center;font-size:12px;opacity:.8">Africa Central Time • <span id="chatCatTime"></span></p><div class="chatBox" id="chatBox"></div>
<div class="msgBarWrap"><div class="msgBar"><button class="emojiBtn" onclick="addEmoji()">😊</button><input id="msgInput" placeholder="Message" oninput="toggleSend()"><button class="attachBtn" onclick="blockedFeature('Picture')">📎</button><button class="attachBtn" onclick="blockedFeature('Picture')">📷</button></div><button class="micBtn" id="micBtn" onclick="blockedFeature('Voice Note')">🎤</button><button class="sendBtnSmall" id="sendBtnSmall" onclick="sendMsg()">➤</button></div>
<p style="text-align:center;font-size:11px;opacity:.7">📎 Picture • 🎤 Voice • 📞 Call unlock 24 Jan 2027 12:00 CAT</p></div></div>
<div class="msgFab" id="msgFab">💬</div>
<script>
try{ if(!localStorage.getItem('inf_version')){ localStorage.setItem('inf_version','v6-final'); } }catch(e){}
var user=null; try{ user=JSON.parse(localStorage.getItem('inf_user')||'null'); }catch(e){ user=null; }
var wins=parseInt(localStorage.getItem('inf_wins')||'0')||0, losses=parseInt(localStorage.getItem('inf_loss')||'0')||0;
var stageIdx=parseInt(localStorage.getItem('inf_stage')||'0')||0;
var loggedIn=false;
var STAGES=['Beginner','Intermediate','Advanced','Expert','Professional'];
function stageName(){ return STAGES[Math.min(stageIdx, STAGES.length-1)] + (stageIdx>=5 ? ' +' : ''); }
function getDiff(){ return (Math.pow(1.3, stageIdx)).toFixed(2); }
var currentMode='',currentCat='',qIndex=0,qList=[],score=0,roundWins=0,roundLoss=0,prevRank=999, lastNotif='', chatFriend='';
function isBannedPassword(pw){ return pw==='1234' || pw==='0000'; }
function getAskedMap(){ try{ return JSON.parse(localStorage.getItem('inf_asked_qs')||'{}'); }catch(e){ return {}; } }
function saveAskedMap(m){ try{ localStorage.setItem('inf_asked_qs', JSON.stringify(m)); }catch(e){} }
function markAsked(qText){ var m=getAskedMap(); m[qText]=Date.now(); saveAskedMap(m); }
function isFresh(qText){ var m=getAskedMap(); var last=m[qText]; if(!last) return true; var days=(Date.now()-last)/(1000*60*60*24); return days>=6; }
function gamblePick(list, count){
  var fresh=list.filter(function(q){ return isFresh(q.q); });
  var pool=fresh.length>=count?fresh.slice():list.slice().sort(function(a,b){ return (getAskedMap()[a.q]||0)-(getAskedMap()[b.q]||0); });
  for(var k=0;k<3;k++){ for(var i=pool.length-1;i>0;i--){ var j=Math.floor(Math.random()*(i+1)); var t=pool[i]; pool[i]=pool[j]; pool[j]=t; } }
  var picked=pool.slice(0,count);
  picked.forEach(function(q){ markAsked(q.q); });
  return picked;
}
function catNow(){ try{ return new Date(new Date().toLocaleString('en-US',{timeZone:'Africa/Lusaka'})); }catch(e){ return new Date(); } }
function updateCatTime(){ try{ var d=catNow(); var timeStr=d.toLocaleTimeString('en-GB',{hour:'2-digit',minute:'2-digit',second:'2-digit'}); var dateStr=('0'+d.getDate()).slice(-2)+'/'+('0'+(d.getMonth()+1)).slice(-2)+'/'+d.getFullYear(); var el=document.getElementById('catTime'); if(el) el.innerText='🕐 '+timeStr+' • '+dateStr+' CAT'; var c2=document.getElementById('chatCatTime'); if(c2) c2.innerText=timeStr+' • '+dateStr; }catch(e){} }
try{ setInterval(updateCatTime,1000); updateCatTime(); }catch(e){}
function isLocked(){ var now=catNow(); var unlock=new Date(2027,0,24,12,0,0); return now < unlock; }
function blockedFeature(name){ if(isLocked()){ alert('🔒 '+name+' is locked!\nAvailable on 24 January 2027 at 12:00hrs CAT'); } else { alert('✅ '+name+' is now unlocked!'); } }
function addEmoji(){ var inp=document.getElementById('msgInput'); inp.value+='😊'; inp.focus(); toggleSend(); }
function toggleSend(){ var v=document.getElementById('msgInput').value.trim(); document.getElementById('micBtn').style.display=v?'none':'flex'; document.getElementById('sendBtnSmall').style.display=v?'block':'none'; }
var audioCtx=null, soundOn=true, soundNodes=[], soundStarted=false;
function unlockAudio(){
  try{
    if(!audioCtx) audioCtx=new (window.AudioContext||window.webkitAudioContext)();
    if(audioCtx.state==='suspended'){ audioCtx.resume(); }
    var o=audioCtx.createOscillator(), g=audioCtx.createGain();
    g.gain.value=0.0001; o.connect(g); g.connect(audioCtx.destination); o.start(); o.stop(audioCtx.currentTime+0.05);
  }catch(e){}
}
function playTick(){ try{ unlockAudio(); var o=audioCtx.createOscillator(), g=audioCtx.createGain(); o.type='sine'; o.frequency.value=1200; g.gain.value=0.08; o.connect(g); g.connect(audioCtx.destination); o.start(); o.stop(audioCtx.currentTime+0.08); }catch(e){} }
function startDashboardSound(){
  if(!soundOn) return;
  try{
    unlockAudio();
    stopDashboardSound();
    var master=audioCtx.createGain(); master.gain.value=0.18; master.connect(audioCtx.destination); soundNodes.push(master);
    var len=audioCtx.sampleRate*2; var buf=audioCtx.createBuffer(1,len,audioCtx.sampleRate); var d=buf.getChannelData(0); for(var i=0;i<len;i++) d[i]=Math.random()*2-1;
    var noise=audioCtx.createBufferSource(); noise.buffer=buf; noise.loop=true;
    var filt=audioCtx.createBiquadFilter(); filt.type='lowpass'; filt.frequency.value=700;
    var ng=audioCtx.createGain(); ng.gain.value=0.22;
    noise.connect(filt); filt.connect(ng); ng.connect(master); noise.start(); soundNodes.push(noise);
    var dropTimer=setInterval(function(){ if(!soundOn) return; try{ var o=audioCtx.createOscillator(), g=audioCtx.createGain(); o.type='sine'; o.frequency.setValueAtTime(800+Math.random()*600, audioCtx.currentTime); o.frequency.exponentialRampToValueAtTime(200, audioCtx.currentTime+0.4); g.gain.setValueAtTime(0.10, audioCtx.currentTime); g.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime+0.4); o.connect(g); g.connect(master); o.start(); o.stop(audioCtx.currentTime+0.45); }catch(e){} }, 1100); soundNodes.push({isTimer:true, id:dropTimer});
    var yeshua=[523.25, 659.25, 783.99, 659.25, 587.33, 659.25, 523.25, 0, 440, 523.25, 587.33, 659.25, 783.99, 659.25, 587.33, 523.25, 0, 392, 440, 523.25, 659.25, 587.33, 440, 523.25];
    var ni=0;
    var pianoTimer=setInterval(function(){ if(!soundOn) return; var f=yeshua[ni % yeshua.length]; ni++; if(f===0) return; try{
      var o=audioCtx.createOscillator(), g=audioCtx.createGain(); o.type='triangle'; o.frequency.value=f; g.gain.setValueAtTime(0.35, audioCtx.currentTime); g.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime+2.0); o.connect(g); g.connect(master); o.start(); o.stop(audioCtx.currentTime+2.0);
      var o2=audioCtx.createOscillator(), g2=audioCtx.createGain(); o2.type='sine'; o2.frequency.value=f/2; g2.gain.setValueAtTime(0.15, audioCtx.currentTime); g2.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime+2.0); o2.connect(g2); g2.connect(master); o2.start(); o2.stop(audioCtx.currentTime+2.0);
    }catch(e){} }, 1200); soundNodes.push({isTimer:true, id:pianoTimer});
    soundStarted=true;
    var b=document.getElementById('soundBtn'); if(b) b.innerText='🔊';
  }catch(e){}
}
function stopDashboardSound(){ try{ soundNodes.forEach(function(n){ try{ if(n.isTimer) clearInterval(n.id); else if(n.stop) n.stop(); else if(n.disconnect) n.disconnect(); }catch(e){} }); soundNodes=[]; soundStarted=false; if(audioCtx && audioCtx.state==='running'){ audioCtx.suspend(); } }catch(e){} }
function toggleSound(){ unlockAudio(); soundOn=!soundOn; var b=document.getElementById('soundBtn'); if(b) b.innerText=soundOn?'🔊':'🔇'; if(soundOn){ startDashboardSound(); toast('🎹 Yeshua Instrumental ON'); } else { stopDashboardSound(); toast('🔇 Sound OFF'); } }
document.addEventListener('touchstart', function(){ unlockAudio(); if(soundOn && loggedIn && !soundStarted){ startDashboardSound(); } }, {passive:true});
document.addEventListener('click', function(){ unlockAudio(); if(soundOn && loggedIn && !soundStarted){ startDashboardSound(); } }, true);
function autoLogout(){
  stopDashboardSound();
  loggedIn=false;
  if(!user) return;
  try{
    var data=JSON.stringify({name:user.name});
    if(navigator.sendBeacon){ navigator.sendBeacon('/api/logout', new Blob([data], {type:'application/json'})); }
    else { fetch('/api/logout',{method:'POST',headers:{'Content-Type':'application/json'},body:data,keepalive:true}).catch(function(){}); }
  }catch(e){}
  try{ localStorage.setItem('inf_needs_login','yes'); localStorage.setItem('inf_page','page-home'); }catch(e){}
}
try{
document.addEventListener('visibilitychange', function(){ if(document.hidden){ autoLogout(); } });
window.addEventListener('pagehide', function(){ autoLogout(); });
window.addEventListener('beforeunload', function(){ autoLogout(); });
}catch(e){}
function toast(m){ var t=document.getElementById('toast'); t.innerText=m; t.classList.remove('hidden'); setTimeout(function(){ t.classList.add('hidden'); },4500); }
function showPage(id){
  ['page-home','page-register','page-dash','page-game','page-coming','page-profile','page-other','page-messages','page-chat'].forEach(function(p){ document.getElementById(p).classList.add('hidden'); });
  document.getElementById(id).classList.remove('hidden'); window.scrollTo(0,0);
  try{ if(loggedIn && id!=='page-home'){ localStorage.setItem('inf_page', id); } }catch(e){}
}
function requireLogin(){ if(!loggedIn){ alert('Please LOGIN first!'); showPage('page-register'); showLogin(); return false; } return true; }
function welcomeName(){ if(!user) return 'Player'; var n=user.name.trim().toLowerCase(); if(n.indexOf('chikondi')===0) return 'My Princess 👸'; if(n.indexOf('chimwemwe')===0) return 'Her Majesty 👑'; return user.name; }
function save(){ try{ localStorage.setItem('inf_user',JSON.stringify(user)); localStorage.setItem('inf_wins',wins); localStorage.setItem('inf_loss',losses); localStorage.setItem('inf_stage',stageIdx); }catch(e){} sync(); }
// *** FIX: Login MUST push you to leaderboard! ***
function forceSync(){
  if(!user || !loggedIn) return;
  fetch('/api/score',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:user.name,password:user.password,wins:wins,losses:losses,stage:stageIdx})}).then(function(){ return fetch('/api/online',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:user.name})}); }).then(function(){ loadLeader(); }).catch(function(){ loadLeader(); });
}
function sync(){ if(!user || !loggedIn) return; fetch('/api/score',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:user.name,password:user.password,wins:wins,losses:losses,stage:stageIdx})}).then(function(){ loadLeader(); }).catch(function(){}); }
function heartbeat(){ if(!user || !loggedIn) return; fetch('/api/online',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:user.name})}).catch(function(){}); }
setInterval(function(){ heartbeat(); checkNotif(); },5000);
function goRegister(){ unlockAudio(); if(user){ showPage('page-register'); showLogin(); document.getElementById('loginName').value=user.name; document.getElementById('regSub').innerText='Welcome back '+user.name+' 👑 Enter password to Login'; } else { showPage('page-register'); showRegister(); } }
function showRegister(){ document.getElementById('registerForm').classList.remove('hidden'); document.getElementById('loginForm').classList.add('hidden'); document.getElementById('regSub').innerText='Create your Infinity account 👑'; }
function showLogin(){ document.getElementById('registerForm').classList.add('hidden'); document.getElementById('loginForm').classList.remove('hidden'); document.getElementById('regSub').innerText='Login to your account 👑'; }
function doRegister(){ unlockAudio(); var n=document.getElementById('regName').value.trim(); var pw=document.getElementById('regPass').value.trim(); if(!n){ alert('Please enter your name!'); return; } if(!pw || pw.length!==4 || isNaN(pw)){ alert('Password must be exactly 4 digits! e.g. 5678'); return; } if(isBannedPassword(pw)){ alert('❌ Password '+pw+' is too easy!\nPlease enter ANY password EXCEPT 1234 or 0000!\nExample: 5678, 2468, 1357'); return; } user={name:n,password:pw}; wins=0; losses=0; stageIdx=0; loggedIn=true; try{ localStorage.setItem('inf_needs_login','no'); }catch(e){} save(); toast('Welcome '+welcomeName()+'! Registered 👑'); updateMe(); showPage('page-dash'); loadLeader(); heartbeat(); startDashboardSound(); }
function doLogin(){ unlockAudio(); var n=document.getElementById('loginName').value.trim(); var pw=document.getElementById('loginPass').value.trim(); if(!n || !pw){ alert('Enter name + password!'); return; } if(user && n===user.name && pw===user.password){ loggedIn=true; try{ localStorage.setItem('inf_needs_login','no'); }catch(e){} toast('Welcome back '+welcomeName()+' 👑 - Nothing reset!'); updateMe(); showPage('page-dash'); forceSync(); heartbeat(); startDashboardSound(); } else if(user && n===user.name){ alert('Wrong password! Try again'); } else { if(pw.length!==4 || isNaN(pw)){ alert('Password must be exactly 4 digits!'); return; } if(isBannedPassword(pw)){ alert('❌ Password '+pw+' is too easy!\nPlease enter ANY password EXCEPT 1234 or 0000!'); return; } user={name:n,password:pw}; wins=0; losses=0; stageIdx=0; loggedIn=true; try{ localStorage.setItem('inf_needs_login','no'); }catch(e){} save(); toast('Welcome '+welcomeName()+'! Registered 👑'); updateMe(); showPage('page-dash'); loadLeader(); heartbeat(); startDashboardSound(); } }
function updateMe(){ if(!user) return; document.getElementById('welcomeText').innerText='Welcome '+welcomeName(); document.getElementById('myStage').innerText=stageName(); }
function goDash(){ if(!requireLogin()) return; showPage('page-dash'); updateMe(); loadLeader(); }
function loadLeader(){ fetch('/api/leaderboard').then(function(r){ return r.json(); }).then(function(d){
 var sorted=(d.players||d).sort(function(a,b){ return (b.wins-b.losses)-(a.wins-a.losses); });
 var idx=-1; for(var i=0;i<sorted.length;i++){ if(user && loggedIn && sorted[i].name===user.name) idx=i; }
 document.getElementById('myRank').innerText=idx>=0?'#'+(idx+1):'#-'; prevRank=idx>=0?idx+1:999;
 var html=''; if(sorted.length===0) html='<p style="text-align:center">No players yet</p>';
 sorted.forEach(function(p,i){ var dot=p.online?'<span class="dot green"></span>':'<span class="dot red"></span>'; html+='<div class="leadRow" onclick="openOther(\''+p.name+'\')"><span>'+dot+' '+(i+1)+'. '+p.name+' '+(i==0?'👑':'')+'</span><span><b>'+p.wins+'</b> Win | <b>'+p.losses+'</b> Lose</span></div>'; });
 document.getElementById('leaderList').innerHTML=html;
 }).catch(function(){}); }
function checkNotif(){ if(!user || !loggedIn) return; fetch('/api/notif?name='+encodeURIComponent(user.name)).then(function(r){ return r.json(); }).then(function(d){
 if(d.requests && d.requests.length>0){ document.getElementById('notifBadge').innerText=d.requests.length; document.getElementById('notifBadge').classList.remove('hidden'); if(lastNotif!==d.requests.join(',')){ toast('📩 You have a friend request from '+d.requests[0]+'!'); lastNotif=d.requests.join(','); } } else { document.getElementById('notifBadge').classList.add('hidden'); }
 if(d.newOnline && d.newOnline!==user.name && lastNotif!==('online'+d.newOnline)){ toast('🟢 '+d.newOnline+' is now Online!'); lastNotif='online'+d.newOnline; }
 }).catch(function(){}); }
function openMyProfile(){ if(!requireLogin()) return; showPage('page-profile'); document.getElementById('profName').innerText=user.name; document.getElementById('profDot').className='dot green'; document.getElementById('profStatus').innerText='Online'; document.getElementById('profWins').innerText=wins; document.getElementById('profLoss').innerText=losses; document.getElementById('profStage').innerText=stageName();
 fetch('/api/leaderboard').then(function(r){ return r.json(); }).then(function(d){ var arr=d.players||d; var s=arr.sort(function(a,b){ return (b.wins-b.losses)-(a.wins-a.losses); }); var ii=-1; for(var i=0;i<s.length;i++){ if(s[i].name===user.name) ii=i; } document.getElementById('profRank').innerText='#'+(ii+1); var me=null; for(var k=0;k<s.length;k++){ if(s[k].name===user.name) me=s[k]; } document.getElementById('profFriends').innerText='👥 Friends: '+(me?me.friends.length:0); document.getElementById('friendList').innerHTML=(me && me.friends.length)?me.friends.map(function(f){ return '<p>👤 '+f+'</p>'; }).join(''):'<p>No friends yet</p>'; }).catch(function(){});
 fetch('/api/notif?name='+encodeURIComponent(user.name)).then(function(r){ return r.json(); }).then(function(d){ if(d.requests.length===0) document.getElementById('reqList').innerHTML='<p>No requests</p>'; else document.getElementById('reqList').innerHTML=d.requests.map(function(req){ return '<div style="display:flex;justify-content:space-between;align-items:center;background:rgba(0,0,0,.4);padding:10px;border-radius:12px;margin:6px 0"><span>👤 '+req+'</span><span><button onclick="respondFriend(\''+req+'\',\'accept\')" style="background:#00cc00;color:white;border:none;padding:8px 12px;border-radius:50%;font-weight:900">✓</button> <button onclick="respondFriend(\''+req+'\',\'reject\')" style="background:#ff2222;color:white;border:none;padding:8px 12px;border-radius:50%;font-weight:900">✕</button></span></div>'; }).join(''); }).catch(function(){});
}
function openOther(name){ if(!requireLogin()) return; if(name===user.name){ openMyProfile(); return; } fetch('/api/leaderboard').then(function(r){ return r.json(); }).then(function(d){ var arr=d.players||d; var s=arr.sort(function(a,b){ return (b.wins-b.losses)-(a.wins-a.losses); }); var p=null; for(var i=0;i<s.length;i++){ if(s[i].name===name) p=s[i]; } if(!p) return; var idx=0; for(var j=0;j<s.length;j++){ if(s[j].name===name) idx=j; } document.getElementById('otherName').innerText=p.name; document.getElementById('otherDot').className=p.online?'dot green':'dot red'; document.getElementById('otherStatus').innerText=p.online?'Online':'Offline'; document.getElementById('otherRank').innerText='#'+(idx+1); document.getElementById('otherWins').innerText=p.wins; document.getElementById('otherLoss').innerText=p.losses; var me=null; for(var k=0;k<s.length;k++){ if(s[k].name===user.name) me=s[k]; } var isFriend=me && me.friends.indexOf(name)>=0; document.getElementById('otherActions').innerHTML=isFriend?'<p style="color:#00ff00">✅ Already Friends</p>':'<button class="btn" onclick="addFriend(\''+name+'\')">➕ Add Friend</button>'; showPage('page-other'); }).catch(function(){}); }
function addFriend(to){ if(!requireLogin()) return; fetch('/api/friend',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({from:user.name,to:to})}).then(function(){ toast('Friend request sent to '+to+'!'); }); }
function respondFriend(from,act){ fetch('/api/respond',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({me:user.name,from:from,action:act})}).then(function(){ toast(act==='accept'?'✅ You accepted '+from:'❌ You rejected '+from); openMyProfile(); }); }
function openMessages(){ if(!requireLogin()) return; showPage('page-messages'); loadChatList(); }
function loadChatList(){ fetch('/api/leaderboard').then(function(r){ return r.json(); }).then(function(d){ var arr=d.players||d; var me=null; for(var i=0;i<arr.length;i++){ if(arr[i].name===user.name) me=arr[i]; } var friends=me?me.friends:[]; if(!friends.length){ document.getElementById('chatFriendList').innerHTML='<p style="text-align:center">No friends yet.<br>Add friends from Leaderboard to chat!</p>'; return; } document.getElementById('chatFriendList').innerHTML=friends.map(function(f,i){ return '<div class="chatRow"><span><b>'+(i+1)+'. '+f+'</b></span><span><span class="chatBtn" onclick="openChat(\''+f+'\')">💬</span><span class="chatBtn" onclick="blockedFeature(\'Call\')">📞</span></span></div>'; }).join(''); }).catch(function(){}); }
function openChat(name){ if(!requireLogin()) return; chatFriend=name; document.getElementById('chatWith').innerText=name; showPage('page-chat'); renderChat(); toggleSend(); }
function chatKey(a,b){ return [a,b].sort().join('|'); }
function getMsgs(){ var k=chatKey(user.name, chatFriend); return JSON.parse(localStorage.getItem('msg_'+k)||'[]'); }
function renderChat(){ var msgs=getMsgs(); var box=document.getElementById('chatBox'); if(!msgs.length) box.innerHTML='<p style="text-align:center;opacity:.7">Say hi to '+chatFriend+' 👋</p>'; else box.innerHTML=msgs.map(function(m){ return '<div class="bubble '+(m.from===user.name?'mine':'theirs')+'"><b>'+(m.from===user.name?'You':m.from)+':</b> '+m.text+'<br><small style="opacity:.6">'+m.time+'</small></div>'; }).join(''); box.scrollTop=box.scrollHeight; }
function sendMsg(){ var inp=document.getElementById('msgInput'); var txt=inp.value.trim(); if(!txt) return; var msgs=getMsgs(); msgs.push({from:user.name,text:txt,time:catNow().toLocaleTimeString('en-GB',{hour:'2-digit',minute:'2-digit'})}); try{ localStorage.setItem('msg_'+chatKey(user.name,chatFriend), JSON.stringify(msgs)); }catch(e){} inp.value=''; toggleSend(); renderChat(); }
function openRiddles(){ if(!requireLogin()) return; showPage('page-game'); document.getElementById('gameTitle').innerText='🧩 RIDDLES'; document.getElementById('gameBody').innerHTML='<p style="text-align:center">What kind? • 🎯 '+stageName()+' • '+getDiff()+'x</p><button class="opt" onclick="startGame(\'riddle\',\'Brain Teasers\')">1. 🧠 Brain Teasers</button><button class="opt" onclick="startGame(\'riddle\',\'Love Riddles\')">2. 💖 Love Riddles</button><button class="opt" onclick="startGame(\'riddle\',\'Funny Riddles\')">3. 😂 Funny Riddles</button><button class="opt" onclick="startGame(\'riddle\',\'Smart Riddles\')">4. 🎓 Smart Riddles</button><button class="opt" onclick="startGame(\'riddle\',\'Programmers Riddles\')">5. 💻 Programmers Riddles</button>'; }
function openBible(){ if(!requireLogin()) return; showPage('page-game'); document.getElementById('gameTitle').innerText='📖 BIBLE FIGHT'; document.getElementById('gameBody').innerHTML='<p style="text-align:center">Choose • 🎯 '+stageName()+' • '+getDiff()+'x</p><button class="opt" onclick="startGame(\'bible\',\'Random Bible\')">1. 🎲 Random Bible Questions</button><button class="opt" onclick="startGame(\'bible\',\'Old Testament\')">2. 📜 Old Testament Story</button><button class="opt" onclick="startGame(\'bible\',\'New Testament\')">3. ✝️ New Testament Story</button><button class="opt" onclick="startGame(\'bible\',\'Name Questions\')">4. 🏷️ Name Questions</button>'; }
var RIDDLES={'Brain Teasers':[{q:'I speak without a mouth, hear without ears?',o:['Echo','Phone','Wind']},{q:'What has keys but cannot open lock?',o:['Piano','Door','Map']},{q:'What gets wetter the more it dries?',o:['Towel','Rain','Soap']},{q:'What has face & 2 hands but no arms?',o:['Clock','Mirror','Robot']},{q:'What can you catch but never throw?',o:['A Cold','Ball','Fish']},{q:'Many needles but never sews?',o:['Christmas Tree','Doctor','Porcupine']},{q:'Goes up but never comes down?',o:['Age','Balloon','Rocket']},{q:'One eye but cannot see?',o:['Needle','Camera','Cyclops']},{q:'Runs but never walks?',o:['Water','Cheetah','Car']},{q:'Head & tail but no body?',o:['Coin','Snake','Cat']}],'Love Riddles':[{q:'Full of love but never tired?',o:['Heart','Phone','Brain']},{q:'Grows when you share me?',o:['Love','Money','Food']},{q:'Give and still keep?',o:['A Smile','Car','House']},{q:'Red, beats fast when you see crush?',o:['Heart','Tomato','Rose']},{q:'Language of love?',o:['Kindness','English','French']},{q:'Lovers hold, never breaks?',o:['Hands','Glass','Promise']},{q:'Sweeter than honey in love?',o:['A Kiss','Sugar','Cake']},{q:'Flies without wings in love?',o:['Butterflies','Bird','Plane']},{q:'Best gift in love?',o:['Time','Gold','Car']},{q:'What did heart say to brain?',o:['I love you','Think','Sleep']}],'Funny Riddles':[{q:'Why chicken cross road?',o:['To get to other side','Dance','Sleep']},{q:'Fish without eyes?',o:['Fsh','Blind','Nemo']},{q:'Scarecrow won award why?',o:['Outstanding in field','Funny','Tall']},{q:'Orange & sounds like parrot?',o:['Carrot','Orange','Mango']},{q:'Math book sad why?',o:['Too many problems','No friends','Old']},{q:'Cheese that is not yours?',o:['Nacho Cheese','My Cheese','Stolen']},{q:'Cookie went to hospital why?',o:['Felt crumby','Fell','Hungry']},{q:'Wall said to other wall?',o:['Meet at corner','Hello','Bye']},{q:'Ghosts bad liars why?',o:['See through them','Scary','Whisper']},{q:'4 wheels & flies?',o:['Garbage Truck','Plane','Car']}],'Smart Riddles':[{q:'2,6,12,20,30,?',o:['42','36','40']},{q:'3 apples, take 2, how many you have?',o:['2','1','3']},{q:'15+15-10?',o:['20','15','30']},{q:'Heavier: 1kg steel or 1kg feathers?',o:['Same','Steel','Feathers']},{q:'How many months have 28 days?',o:['All','1','2']},{q:'Once in minute, twice in moment, never in 1000 years?',o:['M','O','Time']},{q:'Odd number, take letter become even?',o:['Seven','Nine','Five']},{q:'Half of 2+2?',o:['3','2','4']},{q:'Plane crashes Zambia-Zimbabwe border, bury survivors where?',o:['Nowhere, alive','Zambia','Zimbabwe']},{q:'Hexagon sides?',o:['6','5','8']}],'Programmers Riddles':[{q:'HTML stands for?',o:['HyperText Markup Language','High Text','Hyper Tool']},{q:'Style websites?',o:['CSS','Python','Java']},{q:'Brain of computer?',o:['CPU','RAM','Keyboard']},{q:'WWW?',o:['World Wide Web','World Web Wide','Wide World']},{q:'Python comment?',o:['#','//','/*']},{q:'Bug in coding?',o:['Error','Insect','Feature']},{q:'Link tag?',o:['<a>','<p>','<link>']},{q:'AI?',o:['Artificial Intelligence','Amazing Internet','Automatic']},{q:'File that runs website?',o:['index.html','photo.jpg','music.mp3']},{q:'Python is?',o:['Programming Language','Snake','Game']}]};
var BIBLE={'Random Bible':[{q:'Who built Ark?',o:['Noah','Moses','David']},{q:'God created world in?',o:['6 days','7 days','10 days']},{q:'Swallowed by big fish?',o:['Jonah','Peter','Paul']},{q:'First book?',o:['Genesis','Exodus','Matthew']},{q:'Killed Goliath?',o:['David','Saul','Samson']},{q:'Mother of Jesus?',o:['Mary','Ruth','Esther']},{q:'Disciples?',o:['12','10','7']},{q:'Moses parted?',o:['Red Sea','Jordan','Lake']},{q:'Wrote Psalms?',o:['David','Solomon','Abraham']},{q:'Birth of Jesus in?',o:['Matthew','Genesis','Revelation']}],'Old Testament':[{q:'Led Israel out of Egypt?',o:['Moses','Aaron','Joshua']},{q:'God gave Moses?',o:['10 Commandments','Ark','Crown']},{q:'Lions den?',o:['Daniel','Joseph','Jacob']},{q:'Coat of many colours?',o:['Joseph','Benjamin','Reuben']},{q:'First man?',o:['Adam','Noah','Abraham']},{q:'First woman?',o:['Eve','Sarah','Rebekah']},{q:'Samson fought?',o:['Philistines','Egyptians','Romans']},{q:'David killed Goliath with?',o:['Stone & Sling','Sword','Spear']},{q:'Chariot of fire?',o:['Elijah','Elisha','Enoch']},{q:'Tower of Babel?',o:['People of Babel','Noah','Abraham']}],'New Testament':[{q:'Jesus born where?',o:['Bethlehem','Nazareth','Jerusalem']},{q:'Baptized Jesus?',o:['John the Baptist','Peter','Paul']},{q:'Loaves to feed 5000?',o:['5','7','12']},{q:'Denied Jesus 3 times?',o:['Peter','Judas','Thomas']},{q:'Betrayed Jesus?',o:['Judas','Peter','John']},{q:'Jesus rose on?',o:['Sunday','Friday','Saturday']},{q:'First to see risen Jesus?',o:['Mary Magdalene','Peter','John']},{q:'Wrote Revelation?',o:['John','Paul','Luke']},{q:'Last book?',o:['Revelation','Jude','Acts']},{q:'Saul became?',o:['Paul','Peter','Stephen']}],'Name Questions':[{q:'Emmanuel means?',o:['God with us','God great','Peace']},{q:'Jesus means?',o:['Saviour','King','Teacher']},{q:'Father of Faith?',o:['Abraham','Moses','Jacob']},{q:'Beloved Disciple?',o:['John','Peter','James']},{q:'David means?',o:['Beloved','Strong','King']},{q:'Called Israel?',o:['Jacob','Joseph','Esau']},{q:'Moses means?',o:['Drawn out of water','Leader','Prince']},{q:'Weeping Prophet?',o:['Jeremiah','Isaiah','Ezekiel']},{q:'Gabriel means?',o:['God is my strength','Messenger','Angel']},{q:'Called Rock?',o:['Peter','Paul','Andrew']}]};
var HARD={'riddle':[{q:'[ADVANCED] I have cities but no houses, forests but no trees, water but no fish. What am I?',o:['Map','Earth','Book']},{q:'[ADVANCED] What comes after 1, 1, 2, 3, 5, 8, 13?',o:['21','18','20']},{q:'[EXPERT] If 5 machines make 5 parts in 5 mins, 100 machines make 100 parts in?',o:['5 mins','100 mins','20 mins']},{q:'[EXPERT] What is 7 x 8 + (12 / 3) - 5?',o:['55','60','51']},{q:'[PROFESSIONAL] I am taken from a mine and shut in a wooden case, never released, used by all. What am I?',o:['Pencil lead','Gold','Coal']}],'bible':[{q:'[ADVANCED] Who was the father of John the Baptist?',o:['Zechariah','Joseph','Simeon']},{q:'[ADVANCED] How many books in Old Testament?',o:['39','27','66']},{q:'[EXPERT] Who was first king of Israel?',o:['Saul','David','Solomon']},{q:'[EXPERT] In which city was Paul born?',o:['Tarsus','Jerusalem','Antioch']},{q:'[PROFESSIONAL] What is shortest verse?',o:['Jesus wept','God is love','Pray always']}]};
function shuffleArray(a){ for(var i=a.length-1;i>0;i--){ var j=Math.floor(Math.random()*(i+1)); var t=a[i]; a[i]=a[j]; a[j]=t; } return a; }
function prepareQuestions(list, mode){
  var picked=gamblePick(list, 10);
  var base = picked.map(function(q){ var opts=q.o.slice(); var correct=opts[0]; shuffleArray(opts); return {q:q.q, o:opts, a:opts.indexOf(correct)}; });
  if(stageIdx>=1){
    var hardPool = HARD[mode] || [];
    var hardQs = gamblePick(hardPool, Math.min(2+stageIdx*2,5)).map(function(q){ var opts=q.o.slice(); var correct=opts[0]; shuffleArray(opts); return {q:q.q, o:opts, a:opts.indexOf(correct)}; });
    shuffleArray(base); shuffleArray(hardQs);
    var rc = Math.min(2 + stageIdx*2, 5);
    base = hardQs.slice(0,rc).concat(base.slice(0,10-rc));
  }
  return shuffleArray(base);
}
var qTimer=null, qTimeLeft=21;
function startGame(mode,cat){ if(!requireLogin()) return; currentMode=mode; currentCat=cat; qIndex=0; score=0; roundWins=0; roundLoss=0; var raw=mode=='riddle'?RIDDLES[cat]:BIBLE[cat]; qList=prepareQuestions(raw, mode); showQuestion(); }
function continueHarder(){ stageIdx++; save(); updateMe(); toast('🔥 Harder now! Stage: '+stageName()+' • '+getDiff()+'x'); startGame(currentMode,currentCat); }
function clearQTimer(){ if(qTimer) clearInterval(qTimer); qTimer=null; }
function showQuestion(){ clearQTimer(); if(qIndex>=10){ finishRound(); return; } var q=qList[qIndex]; qTimeLeft=21;
 document.getElementById('gameBody').innerHTML='<div style="display:flex;justify-content:space-between;align-items:center"><span><b>Q '+(qIndex+1)+'/10</b> • '+currentCat+'</span><span class="timer" id="qTimer">⏰ '+qTimeLeft+'</span></div><p>🎯 '+stageName()+' • '+getDiff()+'x Harder</p><p style="font-size:18px"><b>'+q.q+'</b></p>'+q.o.map(function(o,i){ return '<button class="opt" onclick="answerQ('+i+')">'+['A','B','C'][i]+') '+o+'</button>'; }).join('')+'<p>✅ '+roundWins+' • ❌ '+roundLoss+'</p>';
 qTimer=setInterval(function(){ qTimeLeft--; var el=document.getElementById('qTimer'); if(el) el.innerText='⏰ '+qTimeLeft; if(qTimeLeft<=5 && qTimeLeft>0) playTick(); if(qTimeLeft<=0){ clearQTimer(); losses++; roundLoss++; save(); updateMe(); alert('⏰ TIME UP! Question VOID - Moving to next!'); qIndex++; showQuestion(); } },1000);
}
function answerQ(i){ clearQTimer(); var q=qList[qIndex]; if(i===q.a){ wins++; roundWins++; score++; alert('✅ CORRECT! +1 WIN 👑'); } else { losses++; roundLoss++; alert('❌ WRONG! Correct: '+q.o[q.a]); } save(); updateMe(); qIndex++; showQuestion(); }
function finishRound(){ clearQTimer(); document.getElementById('gameBody').innerHTML='<h3 style="text-align:center">⏳ Calculating...</h3><p style="text-align:center">Bot calculating...<br>Press CONTINUE to go HARDER!</p><div class="count" style="text-align:center"><span id="coolT">5</span></div><p style="text-align:center">Score: '+score+'/10 • Wins +'+roundWins+' • Losses +'+roundLoss+'<br>Current Stage: '+stageName()+'</p>'; var t=5; var iv=setInterval(function(){ t--; document.getElementById('coolT').innerText=t; if(t<=0){ clearInterval(iv); showResult(); } },1000); }
function showResult(){ fetch('/api/leaderboard').then(function(r){ return r.json(); }).then(function(d){ var arr=d.players||d; var s=arr.sort(function(a,b){ return (b.wins-b.losses)-(a.wins-a.losses); }); var nr=0; for(var i=0;i<s.length;i++){ if(user && s[i].name===user.name) nr=i+1; } var move=nr<prevRank?'📈 MOVED UP! 👑':nr>prevRank?'📉 Moved DOWN':'➡️ Same rank'; var nextStage=STAGES[Math.min(stageIdx+1, STAGES.length-1)]; document.getElementById('gameBody').innerHTML='<h2 style="text-align:center">🏁 DONE!</h2><p style="text-align:center;font-size:22px">Marks: <b>'+score+'/10</b></p><p style="text-align:center">Rank: #'+nr+'<br>'+move+'<br>Now: '+stageName()+' → Next if you Continue: <b>'+nextStage+'</b> 🔥</p><button class="btn" onclick="continueHarder()">🔁 CONTINUE - HARDER! ('+nextStage+')</button><button class="btn2" onclick="openRiddles()">Change Riddle Type</button><button class="btn2" onclick="openBible()">Change Bible Type</button><button class="btn2" onclick="goDash()">🏠 Dashboard</button>'; prevRank=nr; }); }
function openComing(name){ showPage('page-coming'); document.getElementById('comingName').innerText=name+' - COMING SOON'; var t=5; document.getElementById('countDown').innerText=t; var iv=setInterval(function(){ t--; document.getElementById('countDown').innerText=t; if(t<=0){ clearInterval(iv); goDash(); } },1000); }
try{
document.getElementById('enterBtn').addEventListener('click', function(){ unlockAudio(); goRegister(); });
document.getElementById('profileBtn').addEventListener('click', function(){ openMyProfile(); });
document.getElementById('soundBtn').addEventListener('click', function(){ toggleSound(); });
document.getElementById('msgFab').addEventListener('click', function(){ openMessages(); });
}catch(e){}
showPage('page-home');
try{ loadLeader(); }catch(e){}
</script></body></html>"""
@app.route("/")
def home(): return HOME
@app.route("/api/leaderboard")
def lb():
    now=time.time(); arr=[]
    for n,v in USERS.items():
        online = v.get("logged_out", False)==False and (now - v.get("last_seen",0)) < 15
        arr.append({"name":n,"wins":v["wins"],"losses":v["losses"],"online":online,"friends":v.get("friends",[]),"stage":v.get("stage",0)})
    cap=get_capacity()
    return jsonify({"capacity":cap,"players":arr[:cap]})
@app.route("/api/score", methods=["POST"])
def score():
    d=request.get_json() or {}; n=d.get("name","Player")
    cap=get_capacity()
    if n not in USERS and len(USERS)>=cap:
        return jsonify({"ok":False,"error":f"Capacity full: {cap} players. Upgrades to 10000 on 25 Dec!"}),403
    if n not in USERS: USERS[n]={"password":d.get("password",""),"wins":0,"losses":0,"last_seen":time.time(),"friends":[],"requests":[],"stage":0,"logged_out":False}
    USERS[n]["wins"]=int(d.get("wins",0)); USERS[n]["losses"]=int(d.get("losses",0)); USERS[n]["last_seen"]=time.time(); USERS[n]["stage"]=int(d.get("stage",0)); USERS[n]["logged_out"]=False
    if d.get("password"): USERS[n]["password"]=d.get("password")
    return jsonify({"ok":True,"capacity":cap})
@app.route("/api/logout", methods=["POST"])
def logout():
    d=request.get_json(silent=True) or {}
    if not d:
        try: d=request.get_json(force=True, silent=True) or {}
        except: d={}
    n=d.get("name")
    if n in USERS: USERS[n]["logged_out"]=True; USERS[n]["last_seen"]=0
    return jsonify({"ok":True})
@app.route("/api/online", methods=["POST"])
def online():
    d=request.get_json() or {}; n=d.get("name")
    if n in USERS: USERS[n]["last_seen"]=time.time(); USERS[n]["logged_out"]=False
    return jsonify({"ok":True})
@app.route("/api/notif")
def notif():
    n=request.args.get("name",""); reqs=[]
    if n in USERS: reqs=USERS[n].get("requests",[])
    now=time.time(); newOnline=""
    for k,v in USERS.items():
        if k!=n and v.get("logged_out",False)==False and (now-v.get("last_seen",0))<10: newOnline=k
    return jsonify({"requests":reqs,"newOnline":newOnline})
@app.route("/api/friend", methods=["POST"])
def friend():
    d=request.get_json() or {}; frm=d.get("from"); to=d.get("to")
    if to in USERS and frm not in USERS[to]["requests"] and frm not in USERS[to].get("friends",[]):
        USERS[to]["requests"].append(frm)
    return jsonify({"ok":True})
@app.route("/api/respond", methods=["POST"])
def respond():
    d=request.get_json() or {}; me=d.get("me"); frm=d.get("from"); act=d.get("action")
    if me in USERS and frm in USERS[me]["requests"]: USERS[me]["requests"].remove(frm)
    if act=="accept" and me in USERS and frm in USERS:
        if frm not in USERS[me]["friends"]: USERS[me]["friends"].append(frm)
        if me not in USERS[frm]["friends"]: USERS[frm]["friends"].append(me)
    return jsonify({"ok":True})
@app.route("/webhook", methods=["GET","POST"])
def webhook():
    if request.method=="GET":
        if request.args.get("hub.mode")=="subscribe" and request.args.get("hub.verify_token")==VERIFY_TOKEN: return request.args.get("hub.challenge"),200
        return "Forbidden",403
    data=request.get_json() or {}
    try:
        for m in data["entry"][0]["changes"][0]["value"].get("messages",[]):
            if m.get("from") and m.get("text",{}).get("body"): send_whatsapp(m["from"], handle_command(m["from"], m["text"]["body"]))
    except: pass
    return "OK",200
if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
