# -*- coding: utf-8 -*-
"""AHİ — Rapor–kod denetimi.

Teknik tasarım raporunda beyan edilen her sayısal iddianın kodda gerçekten
hesaplandığını ve eşiği karşıladığını doğrular. Jüri "bu rakam nereden
geliyor" diye sorduğunda kaynak dosya bu tablodan gösterilir.

Çalıştırma:
    python tools/rapor_denetimi.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
G, R, W, D = "\033[92m", "\033[91m", "\033[1m", "\033[90m"
X = "\033[0m"


def main() -> None:
    m = json.loads((ROOT / "data/generated/metrics.json").read_text(encoding="utf-8"))
    d = json.loads((ROOT / "web/ahi_data.json").read_text(encoding="utf-8"))
    dm = d["metrics"]

    iddialar = [
        ("Aday getirme — Recall", m.get("recall_at_150"), 0.90, ">=",
         "src/evaluation/evaluate.py", "Aday havuzu korpusla orantılı (150)"),
        ("Yeniden sıralama — NDCG@10", m.get("ndcg_at_10"), 0.75, ">=",
         "src/evaluation/evaluate.py", ""),
        ("Yeniden sıralama — MRR@10", m.get("mrr_at_10"), 0.70, ">=",
         "src/evaluation/evaluate.py", ""),
        ("İlk 10 isabeti — Precision@10", m.get("precision_at_10"), 0.80, ">=",
         "src/evaluation/evaluate.py", ""),
        ("Kitle kalitesi — yakalama oranı",
         dm["anomalyCaught"] / dm["anomalyTotal"], 0.85, ">=",
         "src/matching/matcher.py", "Isolation Forest, denetimsiz"),
        ("Karşılık modeli — MAPE", dm["priceMape"], 0.25, "<=",
         "tools/export_web_bundle.py", "5 katlı çapraz doğrulama"),
        ("Zayıf denetim — etiket F1", m.get("weak_label_f1"), 0.70, ">=",
         "src/evaluation/evaluate.py", "3 etiketleme fonksiyonu"),
    ]

    print(f"\n{W}RAPOR–KOD DENETİMİ{X}")
    print(f"{D}Raporda beyan edilen her sayının kaynağı ve güncel ölçümü{X}\n")
    print(f"{'İddia':<34}{'Ölçülen':>9}  {'Eşik':>7}  {'Durum':<12}Kaynak")
    print("─" * 100)

    hata = 0
    for ad, deger, esik, yon, dosya, not_ in iddialar:
        if deger is None:
            print(f"{ad:<34}{'—':>9}  {esik:>7.2f}  {R}hesaplanmadı{X}  {dosya}")
            hata += 1
            continue
        ok = deger >= esik if yon == ">=" else deger <= esik
        durum = f"{G}karşılandı{X}" if ok else f"{R}eşik altında{X}"
        if not ok:
            hata += 1
        print(f"{ad:<34}{deger:>9.3f}  {esik:>7.2f}  {durum:<21}{dosya}")
        if not_:
            print(f"{D}{'':34}{not_}{X}")

    print("\n" + "─" * 100)
    print(f"Korpus: {W}{dm['corpusSize']}{X} profil · {W}{len(d['niches'])}{X} içerik alanı · "
          f"sözlük {W}{dm['vocabSize']}{X} terim")
    print(f"Anomali tespiti: {W}{dm['anomalyCaught']}/{dm['anomalyTotal']}{X} "
          f"(anormal ort. {dm['meanAnomalous']} · normal ort. {dm['meanNormal']})")

    if hata:
        print(f"\n{R}{hata} iddia karşılanmıyor.{X}")
        sys.exit(1)
    print(f"\n{G}{W}Raporda beyan edilen tüm değerler kodda hesaplanıyor ve eşikleri karşılıyor.{X}\n")


if __name__ == "__main__":
    main()
