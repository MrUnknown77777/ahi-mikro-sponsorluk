# -*- coding: utf-8 -*-
"""AHİ — Anlamsal temsil katmanı.

Gömme arka ucu takılabilir biçimde tasarlanmıştır:

  TfidfBackend    : Türkçeye duyarlı ön işleme + karakter/kelime n-gram TF-IDF.
                    Bağımlılığı hafiftir, her ortamda çalışır.
  SbertBackend    : BERTurk tabanlı cümle gömme modeli (sentence-transformers).
                    Model indirme gerektirir; vektörler önceden hesaplanıp
                    dosyadan da yüklenebilir.

Arka uç değişimi uygulama kodunu etkilemez; matcher yalnızca encode() çağırır.
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import numpy as np

# --------------------------------------------------------------------------
# Türkçeye duyarlı ön işleme
# --------------------------------------------------------------------------
_URL = re.compile(r"https?://\S+")
_MENTION = re.compile(r"@\w+")
_HASHTAG = re.compile(r"#(\w+)")
_NONWORD = re.compile(r"[^\wçğıöşüÇĞİÖŞÜ\s]", re.UNICODE)

# Türkçede standart lower() "I" -> "i" hatası yapar; dile duyarlı eşleme:
_TR_LOWER = str.maketrans({"I": "ı", "İ": "i", "Ş": "ş", "Ğ": "ğ",
                          "Ü": "ü", "Ö": "ö", "Ç": "ç"})

# Etkisiz sözcükler (kısa liste; anlam taşımayan yüksek frekanslılar)
TR_STOPWORDS = {
    "ve", "ile", "bir", "bu", "da", "de", "için", "ama", "çok", "daha",
    "en", "gibi", "kadar", "sonra", "önce", "her", "ne", "ki", "mi", "mı",
    "ise", "olarak", "olan", "var", "yok", "ben", "sen", "o", "biz", "siz",
    "şu", "hem", "ya", "veya", "tek", "iki", "üç", "çünkü", "ancak", "diye",
}


def normalize_tr(text: str) -> str:
    """Türkçe metni normalize eder.

    Bağlantılar, etiketler ve kullanıcı adları tamamen silinmez; ayrı
    belirteçlere dönüştürülür, çünkü yoğunlukları içerik türü hakkında
    bilgi taşır.
    """
    text = unicodedata.normalize("NFC", text)
    text = _URL.sub(" _url_ ", text)
    text = _MENTION.sub(" _mention_ ", text)
    text = _HASHTAG.sub(r" \1 ", text)
    text = text.translate(_TR_LOWER).lower()
    text = _NONWORD.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def profile_text(creator: dict, recency_weight: bool = True) -> str:
    """Üretici profilini tek bir temsil metnine indirger.

    Güncel gönderiler daha yüksek katsayı alır; üreticinin içerik odağı
    zamanla değişebileceğinden son gönderiler daha belirleyicidir.
    """
    parts = [creator.get("niche", ""), creator.get("bio", "")]
    posts = creator.get("posts", [])
    if recency_weight:
        # en yeni gönderi 3 kez, ortadaki 2 kez, en eski 1 kez tekrarlanır
        for w, p in zip((3, 2, 1), posts):
            parts.extend([p] * w)
    else:
        parts.extend(posts)
    return normalize_tr(" ".join(parts))


def brief_text(brief: dict) -> str:
    parts = [brief.get("product_category", ""), brief.get("raw_text", "")]
    return normalize_tr(" ".join(parts))


# --------------------------------------------------------------------------
# Arka uçlar
# --------------------------------------------------------------------------
class TfidfBackend:
    """Kelime + karakter n-gram TF-IDF.

    Türkçe eklemeli bir dil olduğundan yalnızca kelime tabanlı temsil
    ek çeşitliliğini yakalayamaz; karakter n-gram bileşeni bu kaybı telafi eder.
    """

    name = "tfidf-tr"

    def __init__(self) -> None:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.pipeline import FeatureUnion
        self._vec = FeatureUnion([
            ("word", TfidfVectorizer(
                analyzer="word", ngram_range=(1, 2),
                stop_words=list(TR_STOPWORDS), min_df=1, sublinear_tf=True)),
            ("char", TfidfVectorizer(
                analyzer="char_wb", ngram_range=(3, 5),
                min_df=2, sublinear_tf=True)),
        ])
        self._fitted = False

    def fit(self, corpus: list[str]) -> "TfidfBackend":
        self._vec.fit(corpus)
        self._fitted = True
        return self

    def encode(self, texts: list[str]) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("Önce fit() çağrılmalı")
        m = self._vec.transform(texts)
        v = np.asarray(m.todense(), dtype=np.float32)
        norms = np.linalg.norm(v, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return v / norms


class SbertBackend:
    """BERTurk tabanlı cümle gömme modeli.

    Model indirme gerektirir. İnternet erişimi olmayan ortamlarda
    önceden hesaplanmış vektörler `vectors_path` üzerinden yüklenir.
    """

    name = "berturk-sbert"

    def __init__(self, model_name: str = "emrecan/bert-base-turkish-cased-mean-nli-stsb-tr",
                 vectors_path: str | Path | None = None) -> None:
        self.model_name = model_name
        self._cache: dict[str, np.ndarray] = {}
        self._model = None
        if vectors_path and Path(vectors_path).exists():
            data = np.load(vectors_path, allow_pickle=True)
            self._cache = {k: data[k] for k in data.files}

    def _lazy_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def fit(self, corpus: list[str]) -> "SbertBackend":
        return self  # önceden eğitilmiş model; uyarlama gerekmez

    def encode(self, texts: list[str]) -> np.ndarray:
        missing = [t for t in texts if t not in self._cache]
        if missing:
            vecs = self._lazy_model().encode(
                missing, normalize_embeddings=True, show_progress_bar=False)
            for t, v in zip(missing, vecs):
                self._cache[t] = np.asarray(v, dtype=np.float32)
        return np.vstack([self._cache[t] for t in texts])


def get_backend(kind: str = "tfidf", **kw):
    """Arka uç seçici. Uygulama kodu yalnızca bu fonksiyonu bilir."""
    if kind == "tfidf":
        return TfidfBackend()
    if kind == "sbert":
        return SbertBackend(**kw)
    raise ValueError(f"Bilinmeyen arka uç: {kind}")
