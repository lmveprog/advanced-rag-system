from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.retrieval.router import route

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class Question(BaseModel):
    question: str

@app.post("/ask")
def ask(q: Question):
    result = route(q.question)
    return result

@app.get("/", response_class=HTMLResponse)
def index():
    return HTML

HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Matheus - License Chatbot</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f7; height: 100vh; display: flex; flex-direction: column; }
  header { background: #1d1d1f; color: white; padding: 16px 24px; display: flex; align-items: center; gap: 12px; }
  header h1 { font-size: 18px; font-weight: 500; }
  header span { font-size: 12px; color: #86868b; }
  #chat { flex: 1; overflow-y: auto; padding: 24px; display: flex; flex-direction: column; gap: 16px; }
  .msg { max-width: 80%; display: flex; flex-direction: column; gap: 4px; }
  .msg.user { align-self: flex-end; }
  .msg.bot { align-self: flex-start; }
  .bubble { padding: 12px 16px; border-radius: 16px; font-size: 14px; line-height: 1.6; white-space: pre-wrap; }
  .user .bubble { background: #0071e3; color: white; border-bottom-right-radius: 4px; }
  .bot .bubble { background: white; color: #1d1d1f; border-bottom-left-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
  .meta { font-size: 11px; color: #86868b; padding: 0 4px; }
  .user .meta { text-align: right; }
  .tag { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 500; margin-right: 4px; }
  .tag.LOOKUP { background: #e8f5e9; color: #2e7d32; }
  .tag.SQL { background: #e3f2fd; color: #1565c0; }
  .tag.VECTOR { background: #fce4ec; color: #880e4f; }
  .tag.HYBRID { background: #fff3e0; color: #e65100; }
  #footer { background: white; border-top: 1px solid #e5e5e7; padding: 16px 24px; display: flex; gap: 12px; }
  #input { flex: 1; padding: 12px 16px; border: 1px solid #d2d2d7; border-radius: 24px; font-size: 14px; outline: none; font-family: inherit; }
  #input:focus { border-color: #0071e3; }
  #send { padding: 12px 24px; background: #0071e3; color: white; border: none; border-radius: 24px; font-size: 14px; cursor: pointer; font-weight: 500; }
  #send:hover { background: #0077ed; }
  #send:disabled { background: #d2d2d7; cursor: not-allowed; }
  .suggestions { display: flex; flex-wrap: wrap; gap: 8px; padding: 0 24px 16px; }
  .sug { padding: 6px 14px; background: white; border: 1px solid #d2d2d7; border-radius: 16px; font-size: 12px; cursor: pointer; color: #1d1d1f; }
  .sug:hover { background: #f5f5f7; }
  .typing { display: flex; gap: 4px; padding: 12px 16px; background: white; border-radius: 16px; border-bottom-left-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); width: fit-content; }
  .dot { width: 6px; height: 6px; background: #86868b; border-radius: 50%; animation: bounce 1.2s infinite; }
  .dot:nth-child(2) { animation-delay: 0.2s; }
  .dot:nth-child(3) { animation-delay: 0.4s; }
  @keyframes bounce { 0%,60%,100% { transform: translateY(0); } 30% { transform: translateY(-6px); } }
</style>
</head>
<body>
<header>
  <div>
    <h1>Matheus - License Chatbot</h1>
    <span>1994 licences · EU & US</span>
  </div>
</header>

<div class="suggestions">
  <div class="sug" onclick="ask(this.innerText)">Quel est le contact de EU-A-A1-000003 ?</div>
  <div class="sug" onclick="ask(this.innerText)">Combien de licences expirées en EU ?</div>
  <div class="sug" onclick="ask(this.innerText)">Active Gold SLA licenses for IT department</div>
  <div class="sug" onclick="ask(this.innerText)">Licences High Risk avec paiement en retard</div>
</div>

<div id="chat"></div>

<div id="footer">
  <input id="input" type="text" placeholder="Posez votre question sur les licences..." onkeydown="if(event.key==='Enter') send()"/>
  <button id="send" onclick="send()">Envoyer</button>
</div>

<script>
const chat = document.getElementById('chat');
const input = document.getElementById('input');
const btn = document.getElementById('send');

function addMsg(text, role, meta) {
  const div = document.createElement('div');
  div.className = `msg ${role}`;
  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.innerText = text;
  div.appendChild(bubble);
  if (meta) {
    const m = document.createElement('div');
    m.className = 'meta';
    m.innerHTML = meta;
    div.appendChild(m);
  }
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
  return div;
}

function addTyping() {
  const div = document.createElement('div');
  div.className = 'msg bot';
  div.id = 'typing';
  div.innerHTML = '<div class="typing"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>';
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

function ask(text) {
  input.value = text;
  send();
}

async function send() {
  const q = input.value.trim();
  if (!q) return;
  input.value = '';
  btn.disabled = true;

  addMsg(q, 'user');
  addTyping();

  try {
    const res = await fetch('/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q })
    });
    const data = await res.json();
    document.getElementById('typing')?.remove();
    const tag = `<span class="tag ${data.category}">${data.category}</span>`;
    addMsg(data.answer, 'bot', tag);
  } catch(e) {
    document.getElementById('typing')?.remove();
    addMsg('Erreur de connexion au serveur.', 'bot');
  }

  btn.disabled = false;
  input.focus();
}
</script>
</body>
</html>"""

