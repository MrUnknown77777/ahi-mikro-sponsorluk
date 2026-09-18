# -*- coding: utf-8 -*-
"""AHİ — Canlı gösterim betiği.

Sunum sırasında terminalde çalıştırılır. Sistemin yalnızca bir arayüzden değil,
gerçekten çalışan bir Python çekirdeğinden oluştuğunu gösterir:

    1. Sentetik korpusu üretir
    2. Kitle kalitesi modelini (Isolation Forest) eğitir ve sınar
    3. Karşılık öneri modelini (gradyan artırmalı regresyon) eğitir
    4. Sıralama başarımını gerçek metriklerle ölçer
    5. Örnek bir brif çalıştırıp sonucu gösterir

Çalıştırma:
    python demo_calistir.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "data" / "synthetic"))

G = "\033[92m"; B = "\033[94m"; D = "\033[90m"; R = "\033[0m"; W = "\033[1m"


def baslik(n: int, metin: str) -> None:
    print(f"\n{B}{'─' * 74}{R}")
    print(f"{W}{n}. {metin}{R}")
    print(f"{B}{'─' * 74}{R}")


def satir(etiket: str, deger: str, iyi: bool | None = None) -> None:
    isaret = "" if iyi is None else (f"  {G}✓{R}" if iyi else "  ✕")
    print(f"   {etiket:<44} {W}{deger}{R}{isaret}")


def main() -> None:
    t0 = time.time()
    print(f"\n{W}AHİ — Mikro-Sponsorluk Eşleştirme ve Reklam Uyum Platformu{R}")
    print(f"{D}Çekirdek sistem doğrulaması · TEKNOFEST 2026 NSosyal İnovasyon Yarışması{R}")

    # ---------------------------------------------------------------- 1
    baslik(1, "Sentetik korpus üretiliyor")
    t = time.time()
    subprocess.run([sys.executable, "data/synthetic/generate_corpus.py"],
                   cwd=ROOT, check=True, capture_output=True)
    creators = json.loads((ROOT / "data/generated/creators.json").read_text(encoding="utf-8"))
    nisler = sorted({c["niche"] for c in creators})
    anormal = sum(1 for c in creators if c["_is_anomalous"])
    satir("Üretilen profil sayısı", str(len(creators)))
    satir("Farklı içerik alanı", str(len(nisler)))
    satir("Yerleştirilen anormal profil", f"{anormal}  ({anormal/len(creators):.0%})")
    satir("Süre", f"{time.time()-t:.2f} sn")

    # ---------------------------------------------------------------- 2
    baslik(2, "Kitle kalitesi modeli eğitiliyor (Isolation Forest)")
    t = time.time()
    import numpy as np
    from src.matching.matcher import AudienceQuality

    aq = AudienceQuality().fit(creators)
    skor = aq.score(creators)
    anom = np.array([c["_is_anomalous"] for c in creators])
    esik = float(np.percentile(skor, 15))
    yakalanan = int((skor[anom] <= esik).sum())

    satir("Öznitelik sayısı", "5 (etkileşim, sıçrama, yaş, çeşitlilik, bant)")
    satir("Anormal profillerin ortalama göstergesi", f"{skor[anom].mean():.1f}")
    satir("Normal profillerin ortalama göstergesi", f"{skor[~anom].mean():.1f}")
    satir("Yakalama oranı", f"{yakalanan}/{int(anom.sum())}  ({yakalanan/anom.sum():.0%})",
          yakalanan / anom.sum() >= 0.85)
    satir("Süre", f"{time.time()-t:.2f} sn")

    # ---------------------------------------------------------------- 3
    baslik(3, "Karşılık öneri modeli eğitiliyor (gradyan artırmalı regresyon)")
    t = time.time()
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.model_selection import KFold, cross_val_score
    from generate_corpus import NICHES

    ni = {k: v["price_index"] for k, v in NICHES.items()}
    rng = np.random.default_rng(2026)
    X, y = [], []
    for c in creators:
        reach = c["followers"] * c["engagement_rate"]
        idx = ni.get(c["niche"], 1.0)
        exp = 1.0 + min(c["past_campaigns"], 10) * 0.02
        X.append([c["followers"], c["engagement_rate"], reach, idx,
                  c["past_campaigns"], c["account_age_months"]])
        y.append(max(250.0, reach * 12.0 * idx * exp * rng.normal(1.0, 0.12)))
    X, y = np.asarray(X), np.asarray(y)
    gbr = GradientBoostingRegressor(n_estimators=220, max_depth=3, learning_rate=0.07,
                                    subsample=0.9, random_state=2026)
    mape = -cross_val_score(gbr, X, y, cv=KFold(5, shuffle=True, random_state=2026),
                            scoring="neg_mean_absolute_percentage_error").mean()
    satir("Eğitim örneği", str(len(X)))
    satir("Doğrulama", "5 katlı çapraz doğrulama")
    satir("Ortalama mutlak yüzde hata (MAPE)", f"%{mape*100:.1f}  (hedef ≤ %25)", mape <= 0.25)
    satir("Süre", f"{time.time()-t:.2f} sn")

    # ---------------------------------------------------------------- 4
    baslik(4, "Sıralama başarımı ölçülüyor")
    t = time.time()
    out = subprocess.run([sys.executable, "src/evaluation/evaluate.py"],
                         cwd=ROOT, check=True, capture_output=True, text=True)
    m = json.loads((ROOT / "data/generated/metrics.json").read_text(encoding="utf-8"))
    satir("Değerlendirme brifi", f"{m['briefs']} (işletme sahibi diliyle yazılmış)")
    satir("Recall@50", f"{m['recall_at_50']:.3f}  (hedef ≥ 0,90)", m["recall_at_50"] >= 0.90)
    satir("NDCG@10", f"{m['ndcg_at_10']:.3f}  (hedef ≥ 0,75)", m["ndcg_at_10"] >= 0.75)
    satir("MRR@10", f"{m['mrr_at_10']:.3f}  (hedef ≥ 0,70)", m["mrr_at_10"] >= 0.70)
    satir("Precision@10", f"{m['precision_at_10']:.3f}  (hedef ≥ 0,80)",
          m["precision_at_10"] >= 0.80)
    satir("Süre", f"{time.time()-t:.2f} sn")

    # ---------------------------------------------------------------- 5
    baslik(5, "Örnek brif çalıştırılıyor")
    t = time.time()
    from src.matching.embeddings import get_backend
    from src.matching.matcher import Matcher

    brief = {
        "raw_text": "Gümüşten kolye ve yüzük yapıyorum, hepsi elimden çıkıyor. "
                    "Kargoyla her yere gönderiyorum.",
        "product_category": "el yapımı takı",
        "budget_range": None, "geo_constraint": None,
    }
    print(f"   {D}Brif: “{brief['raw_text']}”{R}\n")
    m2 = Matcher(get_backend("tfidf"), creators, ni)
    sonuc = m2.rank(brief, weight_set="shipped", top_n=5)
    for i, r in enumerate(sonuc, 1):
        c = r["creator"]
        print(f"   {W}{i}. @{c['handle']:<26}{R} uyum {W}{r['total']:>5}{R}   "
              f"{D}{c['niche']} · {c['followers']} takipçi · "
              f"kitle kalitesi {r['components']['Kitle kalitesi']:.0f}{R}")
    satir("\n   Süre", f"{time.time()-t:.2f} sn")

    # ---------------------------------------------------------------- özet
    print(f"\n{B}{'─' * 74}{R}")
    print(f"{G}{W}Tüm bileşenler çalışıyor.{R}  Toplam süre: {W}{time.time()-t0:.1f} sn{R}")
    print(f"{D}Kaynak kod: github.com/MrUnknown77777/ahi-mikro-sponsorluk{R}")
    print(f"{B}{'─' * 74}{R}\n")


if __name__ == "__main__":
    main()
