"""Sıralama başarım metrikleri: Recall@k, MRR@k, NDCG@k."""

import math


def recall_at_k(ranked_ids: list, relevant_ids: set, k: int) -> float:
    if not relevant_ids:
        return 0.0
    hits = len(set(ranked_ids[:k]) & relevant_ids)
    return hits / len(relevant_ids)


def mrr_at_k(ranked_ids: list, relevant_ids: set, k: int) -> float:
    for rank, item in enumerate(ranked_ids[:k], start=1):
        if item in relevant_ids:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(ranked_ids: list, relevance: dict, k: int) -> float:
    dcg = sum(
        relevance.get(item, 0) / math.log2(rank + 1)
        for rank, item in enumerate(ranked_ids[:k], start=1)
    )
    ideal = sorted(relevance.values(), reverse=True)[:k]
    idcg = sum(rel / math.log2(rank + 1) for rank, rel in enumerate(ideal, start=1))
    return dcg / idcg if idcg > 0 else 0.0
