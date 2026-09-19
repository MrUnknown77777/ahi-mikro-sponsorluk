# -*- coding: utf-8 -*-
"""AHİ — Sentetik korpus üreticisi.

Canlı demoda jüri herhangi bir sektör söyleyebileceği için korpus 30 nişe ve
900 profile genişletilmiştir. Her nişin gönderi metinleri o alanın kendi
diliyle yazılmıştır; anlamsal eşleştirmenin ayırt ediciliği buna bağlıdır.

Korpusun yaklaşık %10'una bilinçli olarak anormal etkileşim örüntüsü
yerleştirilir; bu profiller kitle kalitesi bileşeninin sınanması içindir ve
arayüzde işaretlenmez.

Çalıştırma:
    python data/synthetic/generate_corpus.py
"""
from __future__ import annotations

import json
import random
from pathlib import Path

RANDOM_SEED = 2026
random.seed(RANDOM_SEED)

OUT_DIR = Path("data/generated")
PER_NICHE = 100
ANOMALY_RATIO = 0.10

CITIES = ["İstanbul", "Ankara", "İzmir", "Bursa", "Antalya", "Konya", "Gaziantep",
          "Trabzon", "Eskişehir", "Denizli", "Samsun", "Muğla", "Kayseri", "Adana"]

from niches import NICHES  # 30 niş × 20 özgün cümle

NICHE_LIST = list(NICHES.keys())
HANDLE_A = ["atolye", "gunluk", "sade", "elisi", "minik", "kuzey", "mavi", "ceviz",
            "lodos", "pusula", "kirmizi", "yesil", "deniz", "ruzgar", "toprak",
            "meltem", "yildiz", "kum", "bahar", "gece"]
HANDLE_B = ["defteri", "notlari", "gunlugu", "isleri", "dukkani", "kosesi",
            "hikayesi", "denemeleri", "arsivi", "studyo", "atolyesi", "sayfasi"]
RISK_FLAGS = ["aşırı politik söylem", "doğrulanmamış sağlık iddiası", "agresif dil"]

# Nişten bağımsız genel cümleler. Gerçek üreticiler yalnızca kendi konularını
# paylaşmaz; bu cümleler profil metinlerine doğal gürültü katar ve niş içi
# profillerin birbirinin kopyası olmasını engeller.
GENEL_CUMLELER = [
 "Bu hafta gelen sorulara tek tek cevap vermeye çalıştım, hepsi için teşekkürler.",
 "Sabah erken başlamak günün geri kalanını tamamen değiştiriyor.",
 "Yorumlarda gelen öneriyi denedim ve gerçekten işe yaradı.",
 "Uzun bir aradan sonra tekrar düzenli paylaşmaya başlıyorum.",
 "Bugün planladığım işlerin yarısını bitirebildim, kalanı yarına.",
 "Yeni bir şey denemek her zaman ilk adımda zor geliyor.",
 "Bu ay önceki aya göre çok daha verimli geçti.",
 "Takip eden herkese ayrı ayrı teşekkür ederim, geri bildirimleriniz yol gösteriyor.",
 "Küçük düzenlemeler uzun vadede büyük fark yaratıyor.",
 "Hafta sonu için planım sadece dinlenmek.",
 "Bu konuda sizin deneyimlerinizi de merak ediyorum.",
 "Gün içinde ara vermek aslında işi hızlandırıyor.",
]

# Komşu niş eşlemesi: bir üretici zaman zaman yakın bir alandan da paylaşır
KOMSU = {
 "el yapımı takı": ["moda ve stil", "el sanatları"],
 "ev dekorasyonu": ["ev tekstili", "sade yaşam", "bitki ve bahçe"],
 "sade yaşam": ["ev düzeni ve organizasyon", "sağlıklı beslenme"],
 "butik kahve": ["yemek ve tarif", "sağlıklı beslenme"],
 "oyun ekipmanları": ["teknoloji ve gadget"],
 "ahşap işçiliği": ["ev dekorasyonu", "el sanatları"],
 "seramik": ["el sanatları", "ev dekorasyonu"],
 "moda ve stil": ["kozmetik ve cilt bakımı", "el yapımı takı"],
 "outdoor ve balıkçılık": ["seyahat ve kamp"],
 "yemek ve tarif": ["sağlıklı beslenme", "butik kahve"],
 "dijital eğitim": ["kitap ve okuma", "tasarım ve illüstrasyon"],
 "kitap ve okuma": ["kırtasiye ve hobi", "dijital eğitim"],
 "bebek ve çocuk ürünleri": ["ev düzeni ve organizasyon"],
 "evcil hayvan": ["bitki ve bahçe"],
 "spor ve fitness": ["sağlıklı beslenme", "bisiklet ve scooter"],
 "kozmetik ve cilt bakımı": ["moda ve stil"],
 "bitki ve bahçe": ["ev dekorasyonu", "tarım ve yerel üretim"],
 "fotoğrafçılık": ["seyahat ve kamp", "tasarım ve illüstrasyon"],
 "müzik ve enstrüman": ["teknoloji ve gadget"],
 "oto aksesuar": ["teknoloji ve gadget"],
 "ev tekstili": ["ev dekorasyonu", "ev düzeni ve organizasyon"],
 "kırtasiye ve hobi": ["tasarım ve illüstrasyon", "el sanatları"],
 "teknoloji ve gadget": ["oyun ekipmanları", "fotoğrafçılık"],
 "seyahat ve kamp": ["outdoor ve balıkçılık", "fotoğrafçılık"],
 "el sanatları": ["kırtasiye ve hobi", "seramik"],
 "sağlıklı beslenme": ["yemek ve tarif", "spor ve fitness"],
 "tasarım ve illüstrasyon": ["kırtasiye ve hobi", "fotoğrafçılık"],
 "ev düzeni ve organizasyon": ["sade yaşam", "ev tekstili"],
 "bisiklet ve scooter": ["spor ve fitness", "seyahat ve kamp"],
 "tarım ve yerel üretim": ["sağlıklı beslenme", "bitki ve bahçe"],
}


def _gonderi_sec(niche: str) -> list[str]:
    """Üreticinin gönderi karışımını oluşturur.

    Gerçek bir üretici yalnızca tek konuda paylaşmaz. Profillerin niş içinde
    birbirinin kopyası olmaması için karışım üç kaynaktan beslenir: kendi nişi,
    komşu bir niş ve nişten bağımsız genel cümleler.
    """
    kendi = random.sample(NICHES[niche]["posts"], k=2)
    r = random.random()
    if r < 0.35 and KOMSU.get(niche):
        ucuncu = random.choice(NICHES[random.choice(KOMSU[niche])]["posts"])
    elif r < 0.75:
        ucuncu = random.choice(GENEL_CUMLELER)
    else:
        ucuncu = random.choice([p for p in NICHES[niche]["posts"] if p not in kendi])
    gonderi = kendi + [ucuncu]
    random.shuffle(gonderi)
    return gonderi


# İçerik türleri: emek katsayısı, karşılık tahmininde çarpan olarak kullanılır
CONTENT_TYPES = {
    "gorsel":      {"ad": "Ürün görselli gönderi",   "emek": 1.00},
    "coklu_gorsel":{"ad": "Çoklu görsel / galeri",    "emek": 1.35},
    "kisa_video":  {"ad": "Kısa video (30–60 sn)",    "emek": 2.10},
    "inceleme":    {"ad": "Detaylı inceleme videosu", "emek": 3.20},
}


def _icerik_yetkinligi() -> list[str]:
    """Üreticinin üretebildiği içerik türleri.

    Her üretici her türü üretemez: video çekimi ayrı bir emek ve ekipman
    gerektirir. Gerçek dağılıma yakın olması için kademeli atanır.
    """
    r = random.random()
    if r < 0.30:
        return ["gorsel", "coklu_gorsel"]
    if r < 0.70:
        return ["gorsel", "coklu_gorsel", "kisa_video"]
    return ["gorsel", "coklu_gorsel", "kisa_video", "inceleme"]


def make_creator(idx: int, niche: str, anomalous: bool) -> dict:
    meta = NICHES[niche]
    followers = int(random.triangular(1000, 10000, 3200))
    if anomalous:
        engagement = round(random.uniform(0.22, 0.55), 4)
        spike = round(random.uniform(0.45, 0.85), 3)
        age_med = random.randint(1, 4)
        diversity = round(random.uniform(0.05, 0.25), 3)
    else:
        engagement = round(random.uniform(0.018, 0.085), 4)
        spike = round(random.uniform(0.02, 0.18), 3)
        age_med = random.randint(10, 60)
        diversity = round(random.uniform(0.55, 0.95), 3)

    return {
        "id": f"c{idx:04d}",
        "handle": f"{random.choice(HANDLE_A)}_{random.choice(HANDLE_B)}_{idx:03d}",
        "niche": niche,
        "bio": meta["bio"],
        "city": random.choice(CITIES),
        "followers": followers,
        "engagement_rate": engagement,
        "account_age_months": random.randint(6, 96),
        "follower_spike_ratio": spike,
        "engager_age_median_months": age_med,
        "engager_diversity": diversity,
        "posts": _gonderi_sec(niche),
        "risk_flags": [random.choice(RISK_FLAGS)] if random.random() < 0.07 else [],
        "past_campaigns": random.randint(0, 12),
        "content_types": _icerik_yetkinligi(),
        "_is_anomalous": anomalous,
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    creators, idx = [], 0
    for niche in NICHE_LIST:
        n_anom = max(1, int(PER_NICHE * ANOMALY_RATIO))
        flags = [True] * n_anom + [False] * (PER_NICHE - n_anom)
        random.shuffle(flags)
        for f in flags:
            creators.append(make_creator(idx, niche, f))
            idx += 1
    random.shuffle(creators)

    (OUT_DIR / "creators.json").write_text(
        json.dumps(creators, ensure_ascii=False, indent=2), encoding="utf-8")

    n_anom = sum(1 for c in creators if c["_is_anomalous"])
    print(f"{len(creators)} üretici profili üretildi · {len(NICHE_LIST)} niş · "
          f"{n_anom} anormal profil")


if __name__ == "__main__":
    main()
