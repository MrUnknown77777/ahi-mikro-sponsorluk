"""Sentetik korpus üreticisi.

Prototip, kişisel veri işlememek ve sistem davranışını bilinen doğru
cevaplar üzerinde ölçebilmek için sentetik korpus kullanır.

Hedef: ~300 içerik üretici profili, 25 girişimci brifi.
Kitle kalitesi bileşeninin sınanabilmesi için korpusa bilinçli olarak
anormal etkileşim örüntüsüne sahip profiller yerleştirilir.
"""

import json
import random
from pathlib import Path

NICHES = [
    "ev dekorasyonu", "ahşap işçiliği", "sade yaşam", "butik kahve",
    "el yapımı takı", "seramik", "yemek tarifleri", "kitap",
    "outdoor ve balıkçılık", "kişisel gelişim", "dijital eğitim",
]

CITIES = ["Ankara", "İstanbul", "İzmir", "Bursa", "Konya", "Gaziantep", "Trabzon"]

OUTPUT_DIR = Path("data/generated")
TARGET_PROFILES = 300
ANOMALY_RATIO = 0.10


def make_profile(idx: int, anomalous: bool = False) -> dict:
    followers = random.randint(1000, 10000)
    ratio = random.uniform(0.25, 0.60) if anomalous else random.uniform(0.02, 0.08)
    return {
        "id": f"creator_{idx:04d}",
        "niche": random.choice(NICHES),
        "city": random.choice(CITIES),
        "followers": followers,
        "engagement_rate": round(ratio, 4),
        "is_anomalous": anomalous,
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    n_anomalous = int(TARGET_PROFILES * ANOMALY_RATIO)
    profiles = [make_profile(i, i < n_anomalous) for i in range(TARGET_PROFILES)]
    random.shuffle(profiles)

    out = OUTPUT_DIR / "creator_profiles.json"
    out.write_text(json.dumps(profiles, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(profiles)} profil üretildi -> {out}")


if __name__ == "__main__":
    main()
