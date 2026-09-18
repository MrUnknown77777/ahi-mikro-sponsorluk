# -*- coding: utf-8 -*-
"""AHİ — Tarayıcı prototipi için veri paketi üretir.

Ağır hesap (TF-IDF sözlüğü, üretici vektörleri, Isolation Forest kitle kalitesi
skorları) burada yapılır ve tek bir JSON dosyasına yazılır. Tarayıcı tarafı
yalnızca bu paketi okur; yeni bir brif girildiğinde vektörleştirme ve sıralama
istemcide, aynı sözlük ve IDF ağırlıklarıyla gerçekleştirilir.

Çalıştırma:
    python tools/export_web_bundle.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "data" / "synthetic"))

from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402

from src.matching.embeddings import TR_STOPWORDS, normalize_tr, profile_text  # noqa: E402
from src.matching.matcher import (AudienceQuality, PriceSuggester,  # noqa: E402
                                  brand_safety_score)
from niches import NICHES  # noqa: E402
from generate_corpus import CONTENT_TYPES  # noqa: E402

OUT = ROOT / "web" / "ahi_data.json"
MAX_TERMS = 2600


def main() -> None:
    creators = json.loads((ROOT / "data/generated/creators.json").read_text(encoding="utf-8"))
    briefs = json.loads((ROOT / "data/generated/briefs.json").read_text(encoding="utf-8"))
    niche_index = {k: v["price_index"] for k, v in NICHES.items()}

    # ---------------- sözlük ve üretici vektörleri ----------------
    texts = [profile_text(c) for c in creators]
    vec = TfidfVectorizer(analyzer="word", ngram_range=(1, 1),
                          stop_words=list(TR_STOPWORDS),
                          max_features=MAX_TERMS, sublinear_tf=True)
    M = vec.fit_transform(texts)
    vocab = {t: int(i) for t, i in vec.vocabulary_.items()}
    idf = [round(float(x), 5) for x in vec.idf_]

    M = M.tocsr()
    sparse_vectors = []
    for r in range(M.shape[0]):
        s, e = M.indptr[r], M.indptr[r + 1]
        idxs = M.indices[s:e]
        vals = M.data[s:e]
        norm = float(np.linalg.norm(vals)) or 1.0
        pairs = sorted(zip(idxs.tolist(), (vals / norm).round(4).tolist()),
                       key=lambda p: -p[1])[:60]
        sparse_vectors.append({str(i): v for i, v in pairs})

    # ---------------- kitle kalitesi ----------------
    aq = AudienceQuality().fit(creators)
    aud = aq.score(creators)

    # ---------------- karşılık önerisi: gerçek regresyon ----------------
    # Etiketli fiyat verisi bulunmadığından, piyasa pratiğini yansıtan bir
    # referans fonksiyondan türetilen sentetik kampanya kayıtları üzerinde
    # gradyan artırmalı regresyon eğitilir. Model, referans fonksiyonu
    # öznitelikler üzerinden yeniden öğrenir ve hata payı raporlanır.
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.model_selection import cross_val_score, KFold
    rng = np.random.default_rng(2026)

    # Her üretici için farklı içerik türlerinde örnek kayıt üretilir; model
    # emek katsayısını bağımsız bir öznitelik olarak öğrenir.
    X, y = [], []
    for c in creators:
        reach = c["followers"] * c["engagement_rate"]
        idx_n = niche_index.get(c["niche"], 1.0)
        exp = 1.0 + min(c["past_campaigns"], 10) * 0.02
        for ct in c["content_types"]:
            emek = CONTENT_TYPES[ct]["emek"]
            gercek = reach * 12.0 * idx_n * exp * emek
            X.append([c["followers"], c["engagement_rate"], reach, idx_n,
                      c["past_campaigns"], c["account_age_months"], emek])
            y.append(max(250.0, gercek * rng.normal(1.0, 0.12)))
    X = np.asarray(X); y = np.asarray(y)

    gbr = GradientBoostingRegressor(n_estimators=220, max_depth=3,
                                    learning_rate=0.07, subsample=0.9,
                                    random_state=2026)
    kf = KFold(n_splits=5, shuffle=True, random_state=2026)
    mape = -cross_val_score(gbr, X, y, cv=kf,
                            scoring="neg_mean_absolute_percentage_error").mean()
    gbr.fit(X, y)
    tahmin = gbr.predict(X)
    print(f"  karşılık modeli MAPE (5-katlı çapraz doğrulama): {mape*100:.1f}%")

    pricer = PriceSuggester(niche_index)

    payload_creators = []
    for k, (c, sv, a) in enumerate(zip(creators, sparse_vectors, aud)):
        # Her içerik türü için ayrı fiyat aralığı
        fiyatlar = {}
        for ct in c["content_types"]:
            emek = CONTENT_TYPES[ct]["emek"]
            ozn = np.array([[c["followers"], c["engagement_rate"],
                             c["followers"]*c["engagement_rate"],
                             niche_index.get(c["niche"], 1.0),
                             c["past_campaigns"], c["account_age_months"], emek]])
            pv = float(gbr.predict(ozn)[0])
            fiyatlar[ct] = [max(int(round(pv*0.85, -1)), 250),
                            max(int(round(pv*1.20, -1)), 400)]
        lo, hi = fiyatlar[c["content_types"][0]]
        rationale = (f"Tahmini erişim {int(c['followers']*c['engagement_rate'])} · "
                     f"niş katsayısı {niche_index.get(c['niche'],1.0):.2f} · "
                     f"{c['past_campaigns']} geçmiş kampanya")
        payload_creators.append({
            "id": c["id"],
            "handle": c["handle"],
            "niche": c["niche"],
            "bio": c["bio"],
            "city": c["city"],
            "followers": c["followers"],
            "engagement": round(c["engagement_rate"], 4),
            "accountAge": c["account_age_months"],
            "pastCampaigns": c["past_campaigns"],
            "posts": c["posts"],
            "riskFlags": c["risk_flags"],
            "audience": round(float(a), 1),
            "safety": round(brand_safety_score(c), 1),
            "priceLo": lo, "priceHi": hi, "priceWhy": rationale,
            "uncertain": AudienceQuality.is_uncertain(c),
            "contentTypes": c["content_types"],
            "prices": fiyatlar,
            "engagerAgeMedian": c["engager_age_median_months"],
            "engagerDiversity": c["engager_diversity"],
            "spike": c["follower_spike_ratio"],
            "vec": sv,
        })

    # ---------------- doğrulama metrikleri ----------------
    anom = np.array([c.get("_is_anomalous", False) for c in creators])
    thr = float(np.percentile(aud, 15))
    caught = int((aud[anom] <= thr).sum())
    try:
        rank_metrics = json.loads((ROOT/"data/generated/metrics.json").read_text(encoding="utf-8"))
    except Exception:
        rank_metrics = {}

    metrics = {
        "priceMape": round(float(mape), 3),
        **rank_metrics,
        "anomalyTotal": int(anom.sum()),
        "anomalyCaught": caught,
        "anomalyRecall": round(caught / max(1, int(anom.sum())), 3),
        "meanAnomalous": round(float(aud[anom].mean()), 1),
        "meanNormal": round(float(aud[~anom].mean()), 1),
        "corpusSize": len(creators),
        "briefCount": len(briefs),
        "vocabSize": len(vocab),
    }

    scenarios = [
        {"id":"taki","brand":"Zeytin Atölye","sector":"El yapımı gümüş takı",
         "city":"İstanbul","campaign":"barter","barterItem":"bir kolye",
         "barterValue":2400,"budget":None,
         "text":"El yapımı gümüş takı üretiyorum. Her parçayı kendim yapıyorum, "
                "ürünlerimi kargoyla her yere gönderiyorum. Sade tasarım ve el emeği "
                "ürünlere değer veren kişilere ulaşmak istiyorum.",
         "niche":"el yapımı takı"},
        {"id":"kahve","brand":"Kuzey Kavurma","sector":"Butik kahve",
         "city":"İzmir","campaign":"cash","barterItem":None,"barterValue":None,
         "budget":[2000,4000],
         "text":"Kendi kavurduğum tek kaynak kahve çekirdeği satıyorum. Demleme "
                "yöntemleriyle ilgilenen, kahveyi ciddiye alan bir kitleye ulaşmak istiyorum.",
         "niche":"butik kahve"},
        {"id":"mousepad","brand":"Vektör Ekipman","sector":"Oyun ekipmanı",
         "city":"Ankara","campaign":"cash","barterItem":None,"barterValue":None,
         "budget":[3000,6000],
         "text":"Oyuncular için kaymaz tabanlı mousepad üretiyorum. Ekipman inceleyen, "
                "test eden ve karşılaştıran kanallarla çalışmak istiyorum.",
         "niche":"oyun ekipmanları"},
        {"id":"kurs","brand":"Kare Akademi","sector":"Çevrim içi eğitim",
         "city":"Bursa","campaign":"cash","barterItem":None,"barterValue":None,
         "budget":[2500,5000],
         "text":"Çevrim içi fotoğrafçılık kursu satıyorum. Öğrenmeye ilgili, dijital "
                "eğitim içeriklerini takip eden kişilere ulaşmak istiyorum.",
         "niche":"dijital eğitim"},
    ]

    # Örnek kampanya geçmişi (Kampanyalarım ekranı için)
    rng2 = np.random.default_rng(7)
    ornek_kampanyalar = [
        {"id":"k001","brand":"Zeytin Atölye","creator":"@elisi_denemeleri_068",
         "niche":"el yapımı takı","type":"barter","status":"tamamlandı",
         "date":"02.09.2026","reach":4820,"engagement":530,"clicks":126,"compliant":True},
        {"id":"k002","brand":"Zeytin Atölye","creator":"@ruzgar_gunlugu_026",
         "niche":"el yapımı takı","type":"barter","status":"yayında",
         "date":"11.09.2026","reach":2140,"engagement":238,"clicks":51,"compliant":True},
        {"id":"k003","brand":"Zeytin Atölye","creator":"@ceviz_studyo_094",
         "niche":"el yapımı takı","type":"nakit","status":"teklif bekliyor",
         "date":"14.09.2026","reach":0,"engagement":0,"clicks":0,"compliant":None},
    ]

    payload = {
        "campaigns": ornek_kampanyalar,
        "scenarios": scenarios,
        "vocab": vocab,
        "idf": idf,
        "stopwords": sorted(TR_STOPWORDS),
        "creators": payload_creators,
        "briefs": briefs,
        "nicheIndex": niche_index,
        "contentTypes": CONTENT_TYPES,
        "niches": sorted(niche_index.keys()),
        "cities": sorted({c["city"] for c in creators}),
        "metrics": metrics,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
                   encoding="utf-8")
    size_kb = OUT.stat().st_size / 1024
    print(f"Paket yazıldı: {OUT}  ({size_kb:.0f} KB)")
    print(f"  sözlük: {len(vocab)} terim | üretici: {len(payload_creators)}")
    print(f"  anomali yakalama: {caught}/{int(anom.sum())} "
          f"(ortalama {metrics['meanAnomalous']} / {metrics['meanNormal']})")


if __name__ == "__main__":
    main()
