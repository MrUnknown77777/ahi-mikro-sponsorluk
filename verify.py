# -*- coding: utf-8 -*-
"""Çekirdek doğrulama çıktısı."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from src.matching.embeddings import get_backend
from src.matching.matcher import Matcher
sys.path.insert(0, str(Path(__file__).parent / "data" / "synthetic"))
from generate_corpus import NICHES

creators = json.load(open("data/generated/creators.json", encoding="utf-8"))
briefs = json.load(open("data/generated/briefs.json", encoding="utf-8"))
niche_index = {k: v["price_index"] for k, v in NICHES.items()}

backend = get_backend("tfidf")
m = Matcher(backend, creators, niche_index)

brief = briefs[0]   # el yapımı gümüş takı, barter
print("=" * 78)
print("BRİF:", brief["raw_text"][:95], "...")
print("Kampanya tipi:", brief["campaign_type"], "| Bütçe:", brief["budget_range"])
print("=" * 78)

res = m.rank(brief, weight_set="shipped", top_n=5)
for i, r in enumerate(res, 1):
    c = r["creator"]
    tag = "  [BELİRSİZ]" if r["uncertain"] else ""
    print(f"\n{i}. @{c['handle']}  —  TOPLAM {r['total']}{tag}")
    print(f"   niş: {c['niche']} | {c['followers']} takipçi | {c['city']}"
          f" | etkileşim %{c['engagement_rate']*100:.1f}")
    comp = "  ".join(f"{k}: {v}" for k, v in r["components"].items())
    print(f"   {comp}")
    print(f"   önerilen karşılık: {r['price_range'][0]}–{r['price_range'][1]} TL")
    print(f"   son gönderi: \"{c['posts'][0][:72]}...\"")

print("\n" + "=" * 78)
print("ANOMALİ TESPİTİ KONTROLÜ")
import numpy as np
sc = m._aud_scores
anom = np.array([c["_is_anomalous"] for c in creators])
print(f"  anormal profillerin ortalama kitle kalitesi : {sc[anom].mean():.1f}")
print(f"  normal  profillerin ortalama kitle kalitesi : {sc[~anom].mean():.1f}")
thr = np.percentile(sc, 15)
caught = (sc[anom] <= thr).sum()
print(f"  en düşük %15 eşiğinde yakalanan anormal     : {caught}/{anom.sum()}"
      f"  (yakalama oranı {caught/anom.sum():.0%})")
