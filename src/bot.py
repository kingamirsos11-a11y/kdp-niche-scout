#!/usr/bin/env python3
"""KDP Niche Scout Bot - Telegram MVP (Polling Mode)"""
import os, json, time, logging, urllib.request, urllib.parse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

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
    
    keywords_str = "\n".join(f"• {k}" for k in d["keywords"])
    tip = "High demand but saturated — niche down!" if d["competition"] > 75 else "Good opportunity — start with 3-5 books." if score >= 65 else "Low competition but weak demand — test small."
    
    return f"*Niche Analysis: {best_match.title()}*\n\nScore: {score}/100 {'✅ Good' if score >= 65 else '⚠️ Medium' if score >= 50 else '❌ Low'}\nDemand: {d['demand']}/100\nCompetition: {d['competition']}/100\nProfit Potential: {d['profit']}/100\nAvg BSR: {d['bsr_avg']:,}\n\nTop Keywords:\n{keywords_str}\n\nTip: {tip}"

def handle_command(text):
    text = text.strip()
    if text.startswith("/start"):
        return "*KDP Niche Scout Bot* 🎯\n\nFind profitable Amazon KDP niches instantly!\n\n*Commands:*\n/niche <topic> — Analyze niche\n/keywords <topic> — Get backend keywords\n/score <topic> — Quick profitability score\n\n*Examples:*\n/niche sudoku adults\n/keywords coloring book seniors\n/score trivia quiz\n\nFree: 5 commands/day | Pro: $4.99/mo unlimited"
    
    elif text.startswith("/niche "):
        return analyze_niche(text[7:])
    
    elif text.startswith("/keywords "):
        q = text[10:].lower()
        for key, val in NICHE_DB.items():
            if key in q:
                kw_list = "\n".join(f"{i+1}. {k}" for i, k in enumerate(val["keywords"]))
                return f"*Keywords for {key.title()}:*\n\n{kw_list}\n\nCopy-paste to KDP backend (7 slots)"
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

def send_message(chat_id, text):
    try:
        payload = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}).encode()
        req = urllib.request.Request(
            f"{API_BASE}/sendMessage",
            data=payload, headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        logger.error(f"Send error: {e}")

def main():
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        return
    
    logger.info("Bot started in polling mode...")
    offset = None
    
    while True:
        try:
            url = f"{API_BASE}/getUpdates?timeout=30"
            if offset:
                url += f"&offset={offset}"
            
            req = urllib.request.Request(url)
            resp = urllib.request.urlopen(req, timeout=35)
            data = json.loads(resp.read())
            
            for update in data.get("result", []):
                offset = update["update_id"] + 1
                msg = update.get("message", {})
                text = msg.get("text", "")
                chat_id = msg.get("chat", {}).get("id")
                
                if chat_id and text:
                    reply = handle_command(text)
                    send_message(chat_id, reply)
                    
        except Exception as e:
            logger.error(f"Poll error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()

