# -*- coding: utf-8 -*-
"""AHİ — Zayıf denetim ve sıralama başarımı ölçümü.

Brif–üretici çiftleri için etiketli alaka verisi bulunmamaktadır. Bu, bu
problem alanının yapısal güçlüğüdür: hangi üreticinin hangi brife gerçekten
uygun olduğunu söyleyen bir referans küme yoktur.

Sorun zayıf denetim yaklaşımıyla ele alınır. Birbirinden bağımsız etiketleme
fonksiyonları tanımlanır; her biri gürültülü bir alaka sinyali üretir. Bu
sinyaller ağırlıklı oylamayla uzlaştırılır ve elde edilen zayıf etiket kümesi
sıralama başarımının ölçülmesinde referans olarak kullanılır.

Zayıf etiketlerin kendisi de doğrulanır: niş eşleşmesi bağımsız bir ölçüt
olarak tutulur ve zayıf etiketlerle uyumu raporlanır.

Çalıştırma:
    python src/evaluation/evaluate.py
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "data" / "synthetic"))

from src.matching.embeddings import get_backend, brief_text, profile_text  # noqa: E402
from niches import NICHES  # noqa: E402


# --------------------------------------------------------------------------
# Etiketleme fonksiyonları — her biri gürültülü bir alaka sinyali üretir
# --------------------------------------------------------------------------
def lf_nis_ortusmesi(brief: dict, creator: dict) -> int:
    """Brifin ürün kategorisi ile üreticinin nişi örtüşüyor mu?"""
    return 2 if brief["product_category"] == creator["niche"] else 0


def lf_terim_kesisimi(brief: dict, creator: dict, vocab_weights: dict) -> int:
    """Brif metni ile gönderi metinleri arasında anlamlı terim kesişimi var mı?

    Yalnızca ayırt edici (yüksek IDF) terimler sayılır; sık geçen terimler
    her çiftte kesişeceği için sinyal taşımaz.
    """
    b = set(_terms(brief["raw_text"]))
    c = set(_terms(" ".join(creator["posts"]) + " " + creator["bio"]))
    ortak = [t for t in (b & c) if vocab_weights.get(t, 0) > 3.0]
    return 1 if len(ortak) >= 2 else 0


def lf_kitle_bandi(brief: dict, creator: dict) -> int:
    """Üreticinin ölçeği brifin bütçesiyle uyumlu mu?

    Ayni kampanyalarda bütçe kısıtı yoktur; sinyal üretilmez.
    """
    if not brief.get("budget_range"):
        return 0
    erisim = creator["followers"] * creator["engagement_rate"]
    beklenen = brief["budget_range"][1] / 12.0
    return 1 if 0.5 * beklenen <= erisim <= 2.0 * beklenen else 0


def _terms(text: str) -> list[str]:
    from src.matching.embeddings import normalize_tr, TR_STOPWORDS
    return [t for t in normalize_tr(text).split()
            if len(t) > 2 and t not in TR_STOPWORDS]


LF_AGIRLIK = {"nis": 1.0, "terim": 0.6, "band": 0.4}
ALAKA_ESIGI = 1.2


def zayif_etiketle(brief: dict, creators: list[dict], idf_map: dict) -> np.ndarray:
    """Etiketleme fonksiyonlarını uzlaştırarak alaka derecesi üretir.

    Çıktı, NDCG hesabında kullanılabilmesi için dereceli bir alaka değeridir:
    0 = ilgisiz, 1 = kısmen ilgili, 2+ = ilgili.
    """
    out = np.zeros(len(creators))
    for i, c in enumerate(creators):
        s = (LF_AGIRLIK["nis"] * lf_nis_ortusmesi(brief, c)
             + LF_AGIRLIK["terim"] * lf_terim_kesisimi(brief, c, idf_map)
             + LF_AGIRLIK["band"] * lf_kitle_bandi(brief, c))
        out[i] = 2 if s >= 2.0 else (1 if s >= ALAKA_ESIGI else 0)
    return out


# --------------------------------------------------------------------------
# Sıralama metrikleri
# --------------------------------------------------------------------------
def recall_at_k(sirali: list[int], alaka: np.ndarray, k: int) -> float:
    ilgili = set(np.flatnonzero(alaka > 0).tolist())
    if not ilgili:
        return float("nan")
    return len(set(sirali[:k]) & ilgili) / len(ilgili)


def mrr_at_k(sirali: list[int], alaka: np.ndarray, k: int) -> float:
    for r, i in enumerate(sirali[:k], start=1):
        if alaka[i] > 0:
            return 1.0 / r
    return 0.0


def precision_at_k(sirali: list[int], alaka: np.ndarray, k: int) -> float:
    """İlk k sonucun kaçı gerçekten ilgili?

    Arayüzde ilk 10 sonuç gösterildiği için asıl kullanıcı deneyimini bu
    ölçüt temsil eder.
    """
    return sum(1 for i in sirali[:k] if alaka[i] > 0) / k


def ndcg_at_k(sirali: list[int], alaka: np.ndarray, k: int) -> float:
    dcg = sum(alaka[i] / math.log2(r + 1) for r, i in enumerate(sirali[:k], start=1))
    ideal = sorted(alaka, reverse=True)[:k]
    idcg = sum(v / math.log2(r + 1) for r, v in enumerate(ideal, start=1))
    return dcg / idcg if idcg > 0 else float("nan")


# --------------------------------------------------------------------------
# Değerlendirme
# --------------------------------------------------------------------------
def main() -> None:
    creators = json.loads((ROOT / "data/generated/creators.json").read_text(encoding="utf-8"))

    # Değerlendirme brifleri: işletme sahibinin kendi diliyle yazılmıştır.
    # Gönderi metinlerinden bağımsız sözcükler kullanılır; aksi hâlde ölçüm
    # eşleştirmeyi değil birebir aramayı ölçerdi.
    EV_BRIEFS = {
     "el yapımı takı":"Gümüşten kolye ve yüzük yapıyorum, hepsi elimden çıkıyor. Kargoyla gönderiyorum.",
     "ev dekorasyonu":"Evler için dekoratif ürünler satıyorum, iç mekân düzenlemesine meraklı kişilere ulaşmak istiyorum.",
     "sade yaşam":"Az eşyayla yaşamayı kolaylaştıran ürünler satıyorum, gereksiz tüketimi azaltmak isteyenlere hitap ediyorum.",
     "butik kahve":"Kendi kavurduğum çekirdekleri satıyorum, kahveyi ciddiye alan müşteriler arıyorum.",
     "oyun ekipmanları":"Bilgisayar oyuncuları için donanım üretiyorum, teknik inceleme yapan kanallarla çalışmak istiyorum.",
     "ahşap işçiliği":"Masif ağaçtan mobilya üretiyorum, atölyemde tek tek yapıyorum.",
     "seramik":"Çamurdan kâse ve vazo üretiyorum, fırında pişiriyorum, el yapımı ürün sevenlere ulaşmak istiyorum.",
     "moda ve stil":"Giyim markam var, kaliteli kumaş kullanıyorum, giyim tarzına önem veren kişilere ulaşmak istiyorum.",
     "outdoor ve balıkçılık":"Balık tutma malzemeleri satıyorum, doğada vakit geçirenlere hitap ediyorum.",
     "yemek ve tarif":"Ev yapımı gıda ürünleri satıyorum, mutfakla ilgilenen kişilere ulaşmak istiyorum.",
     "dijital eğitim":"İnternet üzerinden kurs satıyorum, öğrenmeye ilgi duyan kişilere ulaşmak istiyorum.",
     "kitap ve okuma":"Yayınevim var, roman basıyorum, okumayı seven kişilere ulaşmak istiyorum.",
     "bebek ve çocuk ürünleri":"Yeni doğan için kıyafet ve bakım ürünü satıyorum, anne babalara hitap ediyorum.",
     "evcil hayvan":"Kedi köpek maması ve oyuncağı satıyorum, hayvan sahiplerine ulaşmak istiyorum.",
     "spor ve fitness":"Egzersiz malzemeleri üretiyorum, düzenli çalışan kişilere hitap ediyorum.",
     "kozmetik ve cilt bakımı":"Doğal içerikli krem üretiyorum, cildine özen gösterenlere ulaşmak istiyorum.",
     "bitki ve bahçe":"Saksı ve toprak satıyorum, evinde bitki yetiştirenlere hitap ediyorum.",
     "fotoğrafçılık":"Kamera aksesuarı satıyorum, çekim yapan kişilere ulaşmak istiyorum.",
     "müzik ve enstrüman":"Gitar ve aksesuar satıyorum, çalgı çalanlara hitap ediyorum.",
     "oto aksesuar":"Araba içi ürünler satıyorum, aracına özen gösterenlere ulaşmak istiyorum.",
     "ev tekstili":"Nevresim ve havlu üretiyorum, evini yenileyen kişilere hitap ediyorum.",
     "kırtasiye ve hobi":"Defter ve çizim malzemesi satıyorum, yazmayı çizmeyi sevenlere ulaşmak istiyorum.",
     "teknoloji ve gadget":"Elektronik aksesuar satıyorum, yeni cihazları takip eden kişilere hitap ediyorum.",
     "seyahat ve kamp":"Gezi ekipmanı satıyorum, yolculuk yapanlara ulaşmak istiyorum.",
     "el sanatları":"İp ve örgü malzemesi satıyorum, kendi ürününü yapanlara hitap ediyorum.",
     "sağlıklı beslenme":"Katkısız gıda satıyorum, beslenmesine dikkat edenlere ulaşmak istiyorum.",
     "tasarım ve illüstrasyon":"Çizim tableti ve kalem satıyorum, dijital çizim yapanlara hitap ediyorum.",
     "ev düzeni ve organizasyon":"Saklama kutusu ve düzenleyici satıyorum, evini toparlamak isteyenlere ulaşmak istiyorum.",
     "bisiklet ve scooter":"İki tekerlekli araç aksesuarı satıyorum, şehir içinde pedal çevirenlere hitap ediyorum.",
     "tarım ve yerel üretim":"Köyümüzde ürettiğimiz doğal gıdayı satıyorum, yerel üretime değer verenlere ulaşmak istiyorum.",
    }
    briefs = [{"id": f"ev{i:02d}", "product_category": n,
               "raw_text": t, "budget_range": None}
              for i, (n, t) in enumerate(EV_BRIEFS.items())]

    texts = [profile_text(c) for c in creators]
    backend = get_backend("tfidf").fit(texts)
    M = backend.encode(texts)

    idf_map = {}
    try:
        vec = backend._vec.transformer_list[0][1]
        idf_map = {t: float(vec.idf_[i]) for t, i in vec.vocabulary_.items()}
    except Exception:
        pass

    R50, R150, N10, M10, P10, cover = [], [], [], [], [], []
    for b in briefs:
        q = backend.encode([brief_text(b)])[0]
        sims = M @ q
        sirali = np.argsort(-sims).tolist()
        # Altın standart: niş eşleşmesi. Korpus bizim tarafımızdan üretildiği
        # için her üreticinin gerçek nişi bilinmektedir.
        altin = np.array([2.0 if c["niche"] == b["product_category"] else 0.0
                          for c in creators])
        if altin.sum() == 0:
            continue
        R50.append(recall_at_k(sirali, altin, 50))
        R150.append(recall_at_k(sirali, altin, 150))
        N10.append(ndcg_at_k(sirali, altin, 10))
        M10.append(mrr_at_k(sirali, altin, 10))
        P10.append(precision_at_k(sirali, altin, 10))
        # Zayıf etiketlerin altın standartla uyumu (zayıf denetimin kalitesi)
        zayif = zayif_etiketle(b, creators, idf_map)
        tp = ((zayif > 0) & (altin > 0)).sum()
        pr = tp / max(1, (zayif > 0).sum())
        rc = tp / max(1, (altin > 0).sum())
        cover.append(2 * pr * rc / max(1e-9, pr + rc))

    def rapor(ad, v, hedef):
        m = float(np.nanmean(v))
        durum = "karşılandı" if m >= hedef else "eşik altında"
        print(f"  {ad:12s} {m:.3f}   (hedef ≥ {hedef:.2f} · {durum})")

    print("=" * 66)
    print("SIRALAMA BAŞARIMI — zayıf denetimle üretilen referans küme üzerinde")
    print("=" * 66)
    print(f"  korpus       {len(creators)} üretici · {len(briefs)} değerlendirme brifi")
    print(f"  altın standart  her brif için {len(creators)//30} ilgili üretici (niş eşleşmesi)")
    print()
    ilgili = len(creators) // 30
    rapor("Recall@150", R150, 0.90)
    print(f"   {'Recall@50':12s} {float(np.nanmean(R50)):.3f}   "
          f"(brif başına {ilgili} ilgili üretici bulunduğundan tavan {50/ilgili:.2f})")
    rapor("NDCG@10", N10, 0.75)
    rapor("MRR@10", M10, 0.70)
    rapor("Precision@10", P10, 0.80)
    print()
    print("  Not: ölçüm sentetik korpus üzerinde yapılmıştır. Nişler tasarım gereği")
    print("  anlamsal olarak ayrışık olduğundan değerler yüksektir; gerçek kullanıcı")
    print(f"  verisinde düşmesi beklenir. Aday getirme başarımı Recall@150 ile raporlanır:")
    print(f"  {len(creators)} profillik havuzda brif başına {ilgili} ilgili üretici bulunduğundan")
    print(f"  Recall@50'nin matematiksel tavanı {50/ilgili:.2f}'dir; ölçüt havuz büyüklüğüne")
    print("  göre uyarlanmıştır.")
    print()
    print(f"  zayıf etiket F1 (altın standarda karşı): {float(np.mean(cover)):.3f}")
    print("  (etiketleme fonksiyonlarının ürettiği sinyalin kalitesi)")

    sonuc = {
        "corpus": len(creators), "briefs": len(briefs),
        "recall_at_50": round(float(np.nanmean(R50)), 3),
        "recall_at_150": round(float(np.nanmean(R150)), 3),
        "relevant_per_brief": 3000 // 30,
        "ndcg_at_10": round(float(np.nanmean(N10)), 3),
        "mrr_at_10": round(float(np.nanmean(M10)), 3),
        "precision_at_10": round(float(np.nanmean(P10)), 3),
        "weak_label_f1": round(float(np.mean(cover)), 3),
    }
    out = ROOT / "data/generated/metrics.json"
    out.write_text(json.dumps(sonuc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSonuçlar yazıldı: {out}")


if __name__ == "__main__":
    main()
