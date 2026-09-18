# -*- coding: utf-8 -*-
"""AHİ — Skor motoru.

Bileşenler:
  1. Anlamsal uyum        : brif ile üretici temsili arasındaki yakınlık
  2. Kitle kalitesi       : denetimsiz anomali tespiti (Isolation Forest)
  3. Marka güvenliği      : içerik geçmişindeki risk işaretleri
  4. Karşılık uyumu       : önerilen bedelin brif bütçesiyle örtüşmesi
  5. Coğrafi yakınlık     : kampanya tipine göre ağırlığı sıfırlanabilir

Nihai skor, bileşenlerin ağırlıklı birleşimidir. Ağırlıklar koda gömülü
değildir; kampanya tipine göre tanımlı setlerden seçilir.
"""
from __future__ import annotations

import numpy as np

# --------------------------------------------------------------------------
# Ağırlık setleri — kampanya tipine göre değişir
# --------------------------------------------------------------------------
WEIGHTS = {
    # Kargoyla ulaştırılan ürün: coğrafya anlamsız, sıfırlanır
    "shipped": {
        "semantic": 0.42, "audience": 0.26, "safety": 0.16,
        "budget": 0.16, "geo": 0.00,
    },
    # Yerinde hizmet: coğrafya baskın
    "local": {
        "semantic": 0.32, "audience": 0.20, "safety": 0.13,
        "budget": 0.10, "geo": 0.25,
    },
    # Varsayılan denge
    "default": {
        "semantic": 0.40, "audience": 0.25, "safety": 0.15,
        "budget": 0.15, "geo": 0.05,
    },
}

CANDIDATE_POOL_SIZE = 150


# --------------------------------------------------------------------------
# 2. Kitle kalitesi — denetimsiz anomali tespiti
# --------------------------------------------------------------------------
class AudienceQuality:
    """Etkileşim örüntülerindeki sapmalara göre kitle kalitesi göstergesi.

    Bilinçli olarak denetimsizdir: sahte hesap tespiti için güvenilir
    doğruluk verisi bulunmadığından sınıflandırma kararı üretilmez.
    Çıktı bir karar değil, 0-100 arası bir göstergedir.

    Kitle büyüklüğüne göre gruplanarak normalize edilir; aksi hâlde küçük
    hesapların doğal olarak yüksek etkileşim oranı anomali sayılır.
    """

    FEATURES = ("engagement_rate", "follower_spike_ratio",
                "engager_age_median_months", "engager_diversity")
    NEW_ACCOUNT_MONTHS = 6

    def __init__(self, contamination: float = 0.10, seed: int = 2026) -> None:
        from sklearn.ensemble import IsolationForest
        from sklearn.preprocessing import StandardScaler
        self._model = IsolationForest(
            n_estimators=300, contamination=contamination, random_state=seed)
        self._scaler = StandardScaler()
        self._bands: dict[str, tuple] = {}
        self._fitted = False

    @staticmethod
    def _band(followers: int) -> str:
        if followers < 3000:
            return "small"
        if followers < 6000:
            return "mid"
        return "large"

    def _matrix(self, creators: list[dict]) -> np.ndarray:
        rows = []
        for c in creators:
            band = self._band(c["followers"])
            # banda göre normalize edilmiş etkileşim
            rows.append([
                c["engagement_rate"],
                c["follower_spike_ratio"],
                c["engager_age_median_months"],
                c["engager_diversity"],
                {"small": 0, "mid": 1, "large": 2}[band],
            ])
        return np.asarray(rows, dtype=np.float64)

    def fit(self, creators: list[dict]) -> "AudienceQuality":
        X = self._scaler.fit_transform(self._matrix(creators))
        self._model.fit(X)
        raw = self._model.score_samples(X)
        self._lo, self._hi = float(raw.min()), float(raw.max())
        self._fitted = True
        return self

    def score(self, creators: list[dict]) -> np.ndarray:
        """0-100 arası kitle kalitesi göstergesi döndürür."""
        if not self._fitted:
            raise RuntimeError("Önce fit() çağrılmalı")
        X = self._scaler.transform(self._matrix(creators))
        raw = self._model.score_samples(X)
        span = (self._hi - self._lo) or 1.0
        return np.clip((raw - self._lo) / span, 0, 1) * 100

    @classmethod
    def is_uncertain(cls, creator: dict) -> bool:
        """Geçmiş verisi yetersiz üretici 'belirsiz' işaretlenir.

        Bu üreticiler düşük puanlanmaz; sisteme sonradan katılanın kalıcı
        biçimde dezavantajlı duruma düşmemesi için ayrı ele alınır.
        """
        return (creator.get("account_age_months", 0) < cls.NEW_ACCOUNT_MONTHS
                or creator.get("past_campaigns", 0) == 0)


# --------------------------------------------------------------------------
# 3. Marka güvenliği
# --------------------------------------------------------------------------
def brand_safety_score(creator: dict) -> float:
    """Risk işareti başına ceza uygulanır; taban 100."""
    penalty = 28.0 * len(creator.get("risk_flags", []))
    return float(max(0.0, 100.0 - penalty))


# --------------------------------------------------------------------------
# 4. Karşılık önerisi
# --------------------------------------------------------------------------
class PriceSuggester:
    """Kampanyanın makul bedel aralığını tahmin eder.

    Girdiler: tahmini erişim, etkileşim oranı, niş talep katsayısı,
    geçmiş kampanya sayısı. Çıktı bir aralıktır, tek bir sayı değil.
    """

    def __init__(self, niche_index: dict[str, float]) -> None:
        self.niche_index = niche_index

    def estimate(self, creator: dict) -> tuple[int, int, str]:
        reach = creator["followers"] * creator["engagement_rate"]
        idx = self.niche_index.get(creator["niche"], 1.0)
        experience = 1.0 + min(creator.get("past_campaigns", 0), 10) * 0.02
        base = reach * 12.0 * idx * experience
        lo = int(round(base * 0.85, -1))
        hi = int(round(base * 1.25, -1))
        rationale = (f"Tahmini erişim {int(reach)} · niş katsayısı {idx:.2f} · "
                     f"{creator.get('past_campaigns', 0)} geçmiş kampanya")
        return max(lo, 250), max(hi, 400), rationale


def budget_fit_score(lo: int, hi: int, budget: list | None) -> float:
    """Önerilen aralık ile brif bütçesinin örtüşme oranı."""
    if not budget:
        return 100.0          # ayni kampanya: bütçe kısıtı yok
    b_lo, b_hi = budget
    overlap = max(0, min(hi, b_hi) - max(lo, b_lo))
    span = max(1, hi - lo)
    return float(np.clip(overlap / span, 0, 1) * 100)


# --------------------------------------------------------------------------
# 5. Coğrafi yakınlık
# --------------------------------------------------------------------------
def geo_score(creator: dict, brief: dict) -> float:
    constraint = brief.get("geo_constraint")
    if not constraint:
        return 100.0
    return 100.0 if creator.get("city") == constraint else 0.0


# --------------------------------------------------------------------------
# Eşleştirme motoru
# --------------------------------------------------------------------------
class Matcher:
    """İki aşamalı eşleştirme.

    Aşama 1 — Aday getirme: tüm havuz üzerinde hızlı benzerlik, ilk K aday.
    Aşama 2 — Yeniden sıralama: yalnızca daraltılmış küme üzerinde
              çok bileşenli ağırlıklı skor.

    Gerekçe: birinci aşama hızlıdır ancak yalnızca metin benzerliğine bakar;
    ikinci aşama maliyetlidir ve havuzun tamamına uygulanamaz.
    """

    def __init__(self, backend, creators: list[dict], niche_index: dict[str, float]):
        from src.matching.embeddings import profile_text
        self.backend = backend
        self.creators = creators
        self._texts = [profile_text(c) for c in creators]
        self.backend.fit(self._texts)
        self._matrix = self.backend.encode(self._texts)
        self.audience = AudienceQuality().fit(creators)
        self._aud_scores = self.audience.score(creators)
        self.pricer = PriceSuggester(niche_index)

    # -------------------------------------------------- aşama 1
    def retrieve(self, brief: dict, k: int = CANDIDATE_POOL_SIZE) -> list[int]:
        from src.matching.embeddings import brief_text
        q = self.backend.encode([brief_text(brief)])[0]
        sims = self._matrix @ q
        k = min(k, len(self.creators))
        idx = np.argpartition(-sims, k - 1)[:k]
        return idx[np.argsort(-sims[idx])].tolist(), sims

    # -------------------------------------------------- aşama 2
    def rank(self, brief: dict, weight_set: str = "shipped",
             top_n: int = 10) -> list[dict]:
        cand, sims = self.retrieve(brief)
        w = WEIGHTS.get(weight_set, WEIGHTS["default"])
        smin, smax = float(sims[cand].min()), float(sims[cand].max())
        span = (smax - smin) or 1.0

        results = []
        for i in cand:
            c = self.creators[i]
            semantic = (sims[i] - smin) / span * 100
            audience = float(self._aud_scores[i])
            safety = brand_safety_score(c)
            lo, hi, rationale = self.pricer.estimate(c)
            budget = budget_fit_score(lo, hi, brief.get("budget_range"))
            geo = geo_score(c, brief)

            total = (w["semantic"] * semantic + w["audience"] * audience +
                     w["safety"] * safety + w["budget"] * budget + w["geo"] * geo)

            results.append({
                "creator": c,
                "total": round(float(total), 1),
                "components": {
                    "Anlamsal uyum": round(float(semantic), 1),
                    "Kitle kalitesi": round(float(audience), 1),
                    "Marka güvenliği": round(float(safety), 1),
                    "Bütçe uyumu": round(float(budget), 1),
                    "Coğrafi yakınlık": round(float(geo), 1),
                },
                "weights": w,
                "price_range": (lo, hi),
                "price_rationale": rationale,
                "uncertain": AudienceQuality.is_uncertain(c),
            })
        results.sort(key=lambda r: -r["total"])
        return results[:top_n]


# --------------------------------------------------------------------------
# Karşılaştırma: takipçi odaklı naif sıralama
# --------------------------------------------------------------------------
def naive_rank(creators: list[dict], brief: dict, top_n: int = 10) -> list[dict]:
    """Piyasadaki araçların yaptığı gibi yalnızca erişime göre sıralar.

    Yalnızca karşılaştırma amaçlıdır: takipçi sayısı ve etkileşim oranı
    çarpımı (tahmini erişim) esas alınır, kitle kalitesi dikkate alınmaz.
    """
    cat = brief.get("product_category")
    pool = [c for c in creators if c.get("niche") == cat] or creators
    ranked = sorted(pool, key=lambda c: -(c["followers"] * c["engagement_rate"]))
    return ranked[:top_n]
