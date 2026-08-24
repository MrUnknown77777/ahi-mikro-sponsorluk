"""İki aşamalı eşleştirme motoru.

Aşama 1: Bi-encoder ile aday getirme (hızlı, geniş havuz).
Aşama 2: Cross-encoder ile yeniden sıralama (isabetli, dar havuz).

Gerekçe: Bi-encoder çift etkileşimini modelleyemez; cross-encoder ise
havuzun tamamına uygulanamayacak kadar maliyetlidir.
"""

DEFAULT_WEIGHTS = {
    "semantic": 0.40,
    "audience_quality": 0.25,
    "brand_safety": 0.15,
    "budget_fit": 0.15,
    "geo": 0.05,
}

CANDIDATE_POOL_SIZE = 50


def retrieve_candidates(brief_vector, index, k: int = CANDIDATE_POOL_SIZE):
    """Aşama 1: Vektör indeksinden en yakın k adayı getirir."""
    raise NotImplementedError("Geliştirme aşamasında")


def rerank(brief_text: str, candidates: list):
    """Aşama 2: Cross-encoder ile adayları yeniden sıralar."""
    raise NotImplementedError("Geliştirme aşamasında")


def combined_score(components: dict, weights: dict = None) -> float:
    """Bileşen skorlarını ağırlıklı olarak birleştirir.

    Ağırlıklar kampanya tipine göre değişir; kargoyla satış yapan bir
    marka için coğrafi bileşen sıfırlanır.
    """
    weights = weights or DEFAULT_WEIGHTS
    return sum(components.get(k, 0.0) * w for k, w in weights.items())
