#!/usr/bin/env python3
"""KDP Niche Scout Bot - Telegram MVP"""
import os, re, json, random, logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request, urllib.parse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
PORT = int(os.environ.get("PORT", "8080"))

# Mock data for MVP (real scraper needs proxy rotation)
NICHE_DB = {
    "word search": {"demand": 85, "competition": 72, "profit": 65, "bsr_avg": 45000, "keywords": ["word search adults large print", "brain games seniors", "relaxing puzzles"]},
    "sudoku": {"demand": 90, "competition": 80, "profit": 70, "bsr_avg": 38000, "keywords": ["sudoku easy medium hard", "large print sudoku", "puzzle book gift"]},
    "crossword": {"demand": 75, "competition": 65, "profit": 60, "bsr_avg": 52000, "keywords": ["crossword puzzle adults", "vocabulary builder", "themed crosswords"]},
    "coloring book": {"demand": 95, "competition": 88, "profit": 75, "bsr_avg": 28000, "keywords": ["coloring book seniors", "bold easy coloring", "stress relief art"]},
    "trivia": {"demand": 70, "competition": 55, "profit": 58, "bsr_avg": 65000, "keywords": ["trivia quiz book", "fun facts adults", "knowledge challenge"]},
    "activity book": {"demand": 88, "competition": 70, "profit": 72, "bsr_avg": 41000, "keywords": ["activity book seniors dementia", "brain training mixed", "large print games"]},
}

def analyze_niche(query):
    q = query.lower().strip()
    best_match = None
    for key in NICHE_DB:
        if key in q:
            best_match = key
            break
    
    if not best_match:
        return f"Niche '{query}' not found. Try: word search, sudoku, crossword, coloring book, trivia, activity book"
    
    d = NICHE_DB[best_match]
    score = int((d["demand"] * 0.4 + (100 - d["competition"]) * 0.35 + d["profit"] * 0.25))
    
    keywords_str = chr(10).join('• ' + k for k in d['keywords'])
    tip = 'High demand but saturated — niche down!' if d['competition'] > 75 else 'Good opportunity — start with 3-5 books.' if score >= 65 else 'Low competition but weak demand — test small.'
    
    return f"*Niche Analysis: {best_match.title()}*

Score: {score}/100 {'✅ Good' if score >= 65 else '⚠️ Medium' if score >= 50 else '❌ Low'}
Demand: {d['demand']}/100
Competition: {d['competition']}/100
Profit Potential: {d['profit']}/100
Avg BSR: {d['bsr_avg']:,}

Top Keywords:
{keywords_str}

Tip: {tip}"

def handle_command(text):
    text = text.strip()
    if text.startswith("/start"):
        return "*KDP Niche Scout Bot*

Find profitable Amazon KDP niches instantly!

*Commands:*
/niche <topic> — Analyze niche
/keywords <topic> — Get backend keywords
/score <topic> — Quick profitability score

*Examples:*
/niche sudoku adults
/keywords coloring book seniors
/score trivia quiz

Free: 5 commands/day | Pro: $4.99/mo unlimited"
    
    elif text.startswith("/niche "):
        return analyze_niche(text[7:])
    
    elif text.startswith("/keywords "):
        q = text[10:].lower()
        for key, val in NICHE_DB.items():
            if key in q:
                kw_list = "
".join(f"{i+1}. {k}" for i, k in enumerate(val["keywords"]))
                return f"*Keywords for {key.title()}:*

{kw_list}

Copy-paste to KDP backend (7 slots)"
        return "Niche not found. Try: word search, sudoku, crossword, coloring book, trivia, activity book"
    
    elif text.startswith("/score "):
        q = text[7:]
        for key, val in NICHE_DB.items():
            if key in q.lower():
                score = int((val["demand"] * 0.4 + (100 - val["competition"]) * 0.35 + val["profit"] * 0.25))
                emoji = "🟢" if score >= 65 else "🟡" if score >= 50 else "🔴"
                return f"{emoji} *{key.title()}*: {score}/100"
        return "Not found."
    
    else:
        return "Send /start to see available commands."

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        try:
            update = json.loads(body)
            msg = update.get("message", {})
            text = msg.get("text", "")
            chat_id = msg.get("chat", {}).get("id")
            
            if chat_id and text:
                reply = handle_command(text)
                payload = json.dumps({"chat_id": chat_id, "text": reply, "parse_mode": "Markdown"}).encode()
                req = urllib.request.Request(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    data=payload, headers={"Content-Type": "application/json"}
                )
                urllib.request.urlopen(req, timeout=10)
        except Exception as e:
            logger.error(f"Error: {e}")
        
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"KDP Scout Bot running")

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), WebhookHandler)
    logger.info(f"Bot listening on port {PORT}")
    server.serve_forever()
