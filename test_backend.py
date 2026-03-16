import requests, json

BASE = "http://localhost:8000"

tests = [
    {"url": "/api/chat", "data": {"message": "Dis-moi un proverbe Bamileke", "mode": "proverb"}},
    {"url": "/api/chat", "data": {"message": "How do you say father in Ghomala?", "mode": "tutor"}},
    {"url": "/api/translate", "data": {"text": "je suis content", "source_lang": "fr", "target_lang": "bbj"}},
    {"url": "/api/chat", "data": {"message": "Apprends-moi a compter de 1 a 5 en Ghomala", "mode": "tutor"}},
]

for t in tests:
    r = requests.post(f"{BASE}{t['url']}", json=t["data"])
    q = t["data"].get("message", t["data"].get("text", ""))
    print(f"--- {t['url']} : {q}")
    d = r.json()
    print(d.get("response", d.get("translation", "ERROR")))
    print()
