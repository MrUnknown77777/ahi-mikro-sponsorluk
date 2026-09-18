# -*- coding: utf-8 -*-
"""AHİ — BERTurk cümle gömme vektörlerini üretir.

Bu betik SENİN bilgisayarında çalıştırılır. Türkçe cümle gömme modelini
indirir, korpustaki 3.000 üretici profilinin ve değerlendirme briflerinin
vektörlerini hesaplayıp tek bir dosyaya yazar.

Kurulum:
    pip install sentence-transformers

Çalıştırma (proje kök dizininde):
    python tools/berturk_vektor.py

Çıktı:
    data/generated/berturk_vectors.npz
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

MODEL = "emrecan/bert-base-turkish-cased-mean-nli-stsb-tr"
OUT = ROOT / "data/generated/berturk_vectors.npz"


def main() -> None:
    try:
        import numpy as np
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        print("\n[HATA] Gerekli kütüphane bulunamadı:", e)
        print("Kurulum:  pip install sentence-transformers")
        print("\nKurulum başarısız olursa sorun değil: sistem mevcut Türkçeye")
        print("duyarlı gömme katmanıyla çalışmaya devam eder.")
        sys.exit(1)

    from src.matching.embeddings import profile_text

    creators_path = ROOT / "data/generated/creators.json"
    if not creators_path.exists():
        print("[HATA] Önce korpusu üretin:  python data/synthetic/generate_corpus.py")
        sys.exit(1)

    creators = json.loads(creators_path.read_text(encoding="utf-8"))
    print(f"{len(creators)} profil okundu.")

    print(f"\nModel indiriliyor: {MODEL}")
    print("(ilk çalıştırmada yaklaşık 450 MB iner, birkaç dakika sürebilir)")
    t0 = time.time()
    model = SentenceTransformer(MODEL)
    print(f"Model hazır ({time.time()-t0:.1f} sn)")

    texts = [profile_text(c) for c in creators]
    print(f"\n{len(texts)} profil vektörleştiriliyor...")
    t0 = time.time()
    vecs = model.encode(texts, batch_size=32, normalize_embeddings=True,
                        show_progress_bar=True)
    print(f"Tamamlandı ({time.time()-t0:.1f} sn) · boyut: {vecs.shape}")

    ids = np.array([c["id"] for c in creators])
    np.savez_compressed(OUT, ids=ids, vectors=vecs.astype("float32"),
                        model=np.array([MODEL]))
    boyut = OUT.stat().st_size / 1024 / 1024
    print(f"\nYazıldı: {OUT}  ({boyut:.1f} MB)")
    print("\nBu dosyayı sohbete yükleyin; paket BERTurk vektörleriyle yeniden kurulacak.")


if __name__ == "__main__":
    main()
