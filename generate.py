import os
import json
import time
import datetime
from google import genai

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# Hesabında açık olan geçerli metin üretim modellerini otomatik bul
available_models = ["gemini-3.8-flash"]
try:
    for m in client.models.list():
        name = m.name.replace("models/", "")
        if "gemini" in name and "embedding" not in name and "imagen" not in name and "veo" not in name:
            if name not in available_models:
                available_models.append(name)
except Exception as e:
    print("Model listesi alinamadi:", e)

print("Kullanilabilir modeller:", available_models)

def ask_gemini(prompt):
    # Önce birincil modeli (gemini-3.8-flash) yoğunluğa karşı 4 kez dene, olmazsa diğer aktif modellere geç
    for model_name in available_models:
        retries = 4 if model_name == "gemini-3.8-flash" else 2
        for attempt in range(retries):
            try:
                print(f"Model deneniyor: {model_name} (Deneme {attempt + 1})")
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                return response.text.replace("```json", "").replace("```", "").strip()
            except Exception as e:
                print(f"{model_name} hata verdi: {e}")
                if "404" in str(e) or "NOT_FOUND" in str(e) or "429" in str(e):
                    break
                time.sleep(15)
    raise RuntimeError("Hicbir modelden yanit alinamadi.")

with open("data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

today_str = datetime.date.today().strftime("%Y-%m-%d")

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

eng_entry = json.loads(ask_gemini(eng_prompt))
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
data["tarihte_bugun"].insert(0, json.loads(ask_gemini(history_prompt)))

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
data["imet"].insert(0, json.loads(ask_gemini(imet_prompt)))

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
