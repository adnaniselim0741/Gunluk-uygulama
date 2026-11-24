import os
import json
import datetime
from google import genai

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

with open("data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

today_str = datetime.date.today().strftime("%Y-%m-%d")
is_sunday = datetime.date.today().weekday() == 6

# 1. İNGİLİZCE AKADEMİK & TEKNİK KELİMELER
eng_prompt = f"""
Bugün {today_str}. {data['english']['current_level']} seviyesinden daha önce öğrenilmemiş 10 yeni akademik İngilizce kelime ve Elektrik-Elektronik, Kontrol-Otomasyon ve Mühendislik alanlarından karışık 3 teknik terim üret.
Daha önce öğrenilenler: {', '.join(data['english']['learned_words'][-50:])}
Çıktıyı SADECE aşağıdaki JSON formatında ver, başka hiçbir açıklama yazma:
{{
  "day": {data['english']['day_count'] + 1},
  "date": "{today_str}",
  "academic": [{{"word": "...", "pronunciation": "...", "meaning": "..."}}],
  "technical": [{{"word": "...", "pronunciation": "...", "meaning": "..."}}],
  "examples": ["..."],
  "reading_text": "...",
  "quote": {{"text": "...", "author": "..."}}
}}
"""

res_eng = client.models.generate_content(model="gemini-2.5-flash", contents=eng_prompt)
clean_eng = res_eng.text.replace("```json", "").replace("```", "").strip()
eng_entry = json.loads(clean_eng)

data["english"]["day_count"] += 1
for item in eng_entry["academic"] + eng_entry["technical"]:
    data["english"]["learned_words"].append(item["word"])
data["english"]["daily_entries"].insert(0, eng_entry)

# 2. TARİHTE BUGÜN
history_prompt = f"""
Bugünün tarihi: {today_str}. Türk tarihi ve dünya tarihi açısından bugünün en önemli 3 olayını akademik, tarafsız ve kaynak temelli bir dille özetle.
Çıktıyı SADECE aşağıdaki JSON formatında ver:
{{
  "date": "{today_str}",
  "events": [{{"year": "...", "title": "...", "detail": "..."}}]
}}
"""
res_hist = client.models.generate_content(model="gemini-2.5-flash", contents=history_prompt)
clean_hist = res_hist.text.replace("```json", "").replace("```", "").strip()
data["tarihte_bugun"].insert(0, json.loads(clean_hist))

# 3. İMET (Günlük Akış)
imet_prompt = f"""
Bugünün tarihi: {today_str}. İMet modülü için bugünün teknik/analitik veya güncel değerlendirme özetini hazırla.
Çıktıyı SADECE aşağıdaki JSON formatında ver:
{{
  "date": "{today_str}",
  "title": "Günlük İMet Özeti",
  "content": "..."
}}
"""
res_imet = client.models.generate_content(model="gemini-2.5-flash", contents=imet_prompt)
clean_imet = res_imet.text.replace("```json", "").replace("```", "").strip()
data["imet"].insert(0, json.loads(clean_imet))

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
