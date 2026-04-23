from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

from router import route

DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class Question(BaseModel):
    question: str
    history: list[dict] | None = None


@app.post("/ask")
def ask(q: Question):
    return route(q.question, q.history)


@app.get("/pdf/{region}/{filename}")
def serve_pdf(region: str, filename: str):
    pdf_path = DATA_DIR / "pdf" / region.upper() / Path(filename).name
    if not pdf_path.exists() or pdf_path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(str(pdf_path), media_type="application/pdf")


@app.get("/", response_class=HTMLResponse)
def index():
    return HTML


HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>License Intelligence</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
  *, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

  :root {
    --bg: #f9f9f8;
    --surface: #ffffff;
    --border: #e8e8e5;
    --text: #1a1a18;
    --muted: #8a8a85;
    --accent: #1a1a18;
    --accent-muted: #f0f0ee;
  }

  body {
    font-family: 'Inter', system-ui, sans-serif;
    background: var(--bg);
    height: 100vh;
    display: grid;
    grid-template-columns: 220px 1fr;
    grid-template-rows: 1fr;
    overflow: hidden;
  }

  /* ── Sidebar ── */
  aside {
    background: var(--surface);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    padding: 24px 0;
    overflow: hidden;
  }

  .brand {
    padding: 0 20px 24px;
    border-bottom: 1px solid var(--border);
  }

  .brand-name {
    font-size: 13px;
    font-weight: 600;
    color: var(--text);
    letter-spacing: -0.01em;
  }

  .brand-sub {
    font-size: 11px;
    color: var(--muted);
    margin-top: 3px;
  }

  .sidebar-section {
    padding: 20px 20px 0;
  }

  .sidebar-label {
    font-size: 10px;
    font-weight: 600;
    color: var(--muted);
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-bottom: 10px;
  }

  .sug {
    display: block;
    width: 100%;
    text-align: left;
    background: none;
    border: none;
    font-family: inherit;
    font-size: 12px;
    color: var(--text);
    padding: 7px 10px;
    border-radius: 6px;
    cursor: pointer;
    line-height: 1.4;
    margin-bottom: 2px;
    transition: background 0.1s;
  }

  .sug:hover { background: var(--accent-muted); }

  /* ── Main ── */
  main {
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  #chat {
    flex: 1;
    overflow-y: auto;
    padding: 40px 48px;
    display: flex;
    flex-direction: column;
    gap: 32px;
    scroll-behavior: smooth;
  }

  #chat::-webkit-scrollbar { width: 4px; }
  #chat::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }

  /* ── Messages ── */
  .msg-user {
    display: flex;
    justify-content: flex-end;
  }

  .msg-user-text {
    max-width: 560px;
    font-size: 14px;
    color: var(--text);
    background: var(--accent-muted);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 10px 14px;
    line-height: 1.6;
    white-space: pre-wrap;
  }

  .msg-bot {
    display: flex;
    flex-direction: column;
    gap: 12px;
    max-width: 680px;
  }

  .bot-header {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .bot-avatar {
    width: 22px;
    height: 22px;
    background: var(--text);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .bot-avatar svg { display: block; }

  .bot-name {
    font-size: 12px;
    font-weight: 600;
    color: var(--text);
  }

  .bot-tag {
    font-size: 10px;
    font-weight: 500;
    color: var(--muted);
    background: var(--accent-muted);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 1px 6px;
    letter-spacing: 0.02em;
  }

  .conf-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    flex-shrink: 0;
    margin-left: auto;
  }
  .conf-dot.high { background: #22c55e; }
  .conf-dot.mid  { background: #f59e0b; }
  .conf-dot.low  { background: #ef4444; }

  .conf-pct {
    font-size: 10px;
    color: var(--muted);
  }

  .bot-body {
    font-size: 14px;
    color: var(--text);
    line-height: 1.75;
    padding-left: 30px;
  }

  .bot-body p { margin-bottom: 8px; }
  .bot-body p:last-child { margin-bottom: 0; }
  .bot-body strong { font-weight: 600; }
  .bot-body em { font-style: italic; }
  .bot-body ul, .bot-body ol { padding-left: 18px; margin-bottom: 8px; }
  .bot-body li { margin-bottom: 3px; }
  .bot-body code { font-family: 'SF Mono', 'Menlo', monospace; font-size: 12px; background: var(--accent-muted); border-radius: 3px; padding: 1px 5px; }
  .bot-body pre { background: var(--accent-muted); border-radius: 6px; padding: 10px 12px; overflow-x: auto; margin-bottom: 8px; }
  .bot-body pre code { background: none; padding: 0; }
  .bot-body table { border-collapse: collapse; width: 100%; margin-bottom: 8px; font-size: 13px; }
  .bot-body th, .bot-body td { border: 1px solid var(--border); padding: 6px 10px; text-align: left; }
  .bot-body th { background: var(--accent-muted); font-weight: 600; }
  .bot-body h1, .bot-body h2, .bot-body h3 { font-weight: 600; margin-bottom: 6px; }

  .bot-footer {
    padding-left: 30px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .pdf-links {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .pdf-link {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 11px;
    font-weight: 500;
    color: var(--text);
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 5px;
    padding: 3px 8px;
    text-decoration: none;
    transition: border-color 0.1s;
  }

  .pdf-link:hover { border-color: var(--text); }

  .pdf-link::before {
    content: '';
    display: inline-block;
    width: 8px;
    height: 8px;
    background: #ef4444;
    border-radius: 1px;
    flex-shrink: 0;
  }

  .raw-toggle {
    background: none;
    border: none;
    font-family: inherit;
    font-size: 11px;
    color: var(--muted);
    cursor: pointer;
    padding: 0;
    display: flex;
    align-items: center;
    gap: 4px;
    width: fit-content;
    transition: color 0.1s;
  }

  .raw-toggle:hover { color: var(--text); }

  .raw-toggle svg { transition: transform 0.15s; }
  .raw-toggle.open svg { transform: rotate(90deg); }

  .raw-panel {
    display: none;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: #fafaf9;
    overflow: hidden;
  }

  .raw-panel.open { display: block; }

  .raw-conf {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 14px;
    border-bottom: 1px solid var(--border);
    font-size: 11px;
    color: var(--muted);
  }

  .raw-body {
    padding: 12px 14px;
    font-size: 11.5px;
    font-family: 'SF Mono', 'Menlo', monospace;
    color: #4a4a45;
    white-space: pre-wrap;
    word-break: break-word;
    max-height: 280px;
    overflow-y: auto;
    line-height: 1.6;
  }

  .raw-body::-webkit-scrollbar { width: 4px; }
  .raw-body::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }

  /* ── Typing ── */
  .typing-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding-left: 30px;
  }

  .typing-dot {
    width: 5px;
    height: 5px;
    background: var(--muted);
    border-radius: 50%;
    animation: pulse 1.2s ease-in-out infinite;
  }

  .typing-dot:nth-child(2) { animation-delay: 0.2s; }
  .typing-dot:nth-child(3) { animation-delay: 0.4s; }

  @keyframes pulse {
    0%, 60%, 100% { opacity: 0.3; transform: scale(1); }
    30% { opacity: 1; transform: scale(1.2); }
  }

  /* ── Input ── */
  #footer {
    border-top: 1px solid var(--border);
    background: var(--surface);
    padding: 16px 48px;
    display: flex;
    align-items: center;
    gap: 10px;
  }

  #input {
    flex: 1;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 13.5px;
    font-family: inherit;
    color: var(--text);
    outline: none;
    transition: border-color 0.15s;
  }

  #input::placeholder { color: var(--muted); }
  #input:focus { border-color: #aaa; }

  #send {
    background: var(--text);
    color: #fff;
    border: none;
    border-radius: 8px;
    padding: 10px 18px;
    font-size: 13px;
    font-family: inherit;
    font-weight: 500;
    cursor: pointer;
    transition: opacity 0.15s;
    flex-shrink: 0;
  }

  #send:hover { opacity: 0.82; }
  #send:disabled { opacity: 0.3; cursor: not-allowed; }
</style>
</head>
<body>

<aside>
  <div class="brand">
    <div class="brand-name">LME (License Management Environment) - Chatbot</div>
    <div class="brand-sub"></div>
  </div>

  <div class="sidebar-section">
    <div class="sidebar-label">Suggestions</div>
    <button class="sug" onclick="ask(this.innerText)">Contact of EU-A-A1-000003</button>
    <button class="sug" onclick="ask(this.innerText)">Expired licenses in EU</button>
    <button class="sug" onclick="ask(this.innerText)">Active Gold SLA — IT dept</button>
    <button class="sug" onclick="ask(this.innerText)">High Risk + overdue payment</button>
    <button class="sug" onclick="ask(this.innerText)">Termination clauses EU-A-A1-000003</button>
    <button class="sug" onclick="ask(this.innerText)">Engineering licenses expiring 2025</button>
    <button class="sug" onclick="ask(this.innerText)">What does Risk Rating mean?</button>
  </div>
</aside>

<main>
  <div id="chat"></div>

  <div id="footer">
    <input id="input" type="text" placeholder="Ask anything about licenses…" onkeydown="if(event.key==='Enter') send()"/>
    <button id="send" onclick="send()">Send</button>
  </div>
</main>

<script>
const chat = document.getElementById('chat');
const input = document.getElementById('input');
const btn   = document.getElementById('send');

marked.setOptions({ breaks: true, gfm: true });

const history = [];  // [{role, content}, ...]

function addUser(text) {
  const row = document.createElement('div');
  row.className = 'msg-user';
  const bubble = document.createElement('div');
  bubble.className = 'msg-user-text';
  bubble.textContent = text;
  row.appendChild(bubble);
  chat.appendChild(row);
  chat.scrollTop = chat.scrollHeight;
}

function addBot(answer, category, pdfLinks, rawContext, confidence) {
  const wrap = document.createElement('div');
  wrap.className = 'msg-bot';

  // header row
  const header = document.createElement('div');
  header.className = 'bot-header';
  header.innerHTML = `
    <div class="bot-avatar">
      <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
        <circle cx="6" cy="6" r="5" stroke="white" stroke-width="1.5"/>
        <path d="M4 6h4M6 4v4" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
      </svg>
    </div>
    <span class="bot-name">MatheusBot</span>
  `;

  wrap.appendChild(header);

  // answer text
  const body = document.createElement('div');
  body.className = 'bot-body';
  body.innerHTML = marked.parse(answer);
  wrap.appendChild(body);

  // footer: pdf links + raw toggle
  const footer = document.createElement('div');
  footer.className = 'bot-footer';

  if (pdfLinks && pdfLinks.length > 0) {
    const links = document.createElement('div');
    links.className = 'pdf-links';
    pdfLinks.forEach(link => {
      const a = document.createElement('a');
      a.href = link.url;
      a.target = '_blank';
      a.rel = 'noopener noreferrer';
      a.className = 'pdf-link';
      a.title = link.company || link.license_id;
      a.textContent = link.license_id;
      links.appendChild(a);
    });
    footer.appendChild(links);
  }

  if (rawContext && rawContext.trim()) {
    const id = 'raw-' + Date.now();
    const toggle = document.createElement('button');
    toggle.className = 'raw-toggle';
    toggle.innerHTML = `<svg width="10" height="10" viewBox="0 0 10 10" fill="none"><path d="M3 2l4 3-4 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>Details`;
    toggle.onclick = () => {
      const panel = document.getElementById(id);
      const open = panel.classList.toggle('open');
      toggle.classList.toggle('open', open);
    };
    footer.appendChild(toggle);

    const panel = document.createElement('div');
    panel.className = 'raw-panel';
    panel.id = id;

    if (category || confidence != null) {
      const confRow = document.createElement('div');
      confRow.className = 'raw-conf';
      let inner = '';
      if (category) inner += `<span class="bot-tag">${category}</span>`;
      if (confidence != null) {
        const cls = confidence >= 75 ? 'high' : confidence >= 40 ? 'mid' : 'low';
        const label = confidence >= 75 ? 'High confidence' : confidence >= 40 ? 'Moderate confidence' : 'Low confidence';
        inner += `<span class="conf-dot ${cls}"></span><span>${label} &mdash; ${confidence}%</span>`;
      }
      confRow.innerHTML = inner;
      panel.appendChild(confRow);
    }

    const rawBody = document.createElement('div');
    rawBody.className = 'raw-body';
    rawBody.textContent = rawContext;
    panel.appendChild(rawBody);
    footer.appendChild(panel);
  }

  wrap.appendChild(footer);
  chat.appendChild(wrap);
  chat.scrollTop = chat.scrollHeight;
}

function addTyping() {
  const wrap = document.createElement('div');
  wrap.className = 'msg-bot';
  wrap.id = 'typing';

  const header = document.createElement('div');
  header.className = 'bot-header';
  header.innerHTML = `
    <div class="bot-avatar">
      <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
        <circle cx="6" cy="6" r="5" stroke="white" stroke-width="1.5"/>
        <path d="M4 6h4M6 4v4" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
      </svg>
    </div>
    <span class="bot-name">MatheusBot</span>
  `;
  wrap.appendChild(header);

  const row = document.createElement('div');
  row.className = 'typing-row';
  row.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
  wrap.appendChild(row);

  chat.appendChild(wrap);
  chat.scrollTop = chat.scrollHeight;
}

function ask(text) { input.value = text; send(); }

async function send() {
  const q = input.value.trim();
  if (!q) return;
  input.value = '';
  btn.disabled = true;
  addUser(q);
  addTyping();
  try {
    const res  = await fetch('/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q, history })
    });
    const data = await res.json();
    document.getElementById('typing')?.remove();
    addBot(data.answer, data.category, data.pdf_links || [], data.context || '', data.confidence);
    history.push({ role: 'user', content: q });
    history.push({ role: 'assistant', content: data.answer });
    if (history.length > 12) history.splice(0, 2);  // garde 6 échanges max
  } catch {
    document.getElementById('typing')?.remove();
    addBot('Connection error.', null, [], '');
  }
  btn.disabled = false;
  input.focus();
}
</script>
</body>
</html>"""
