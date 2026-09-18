# AHİ — Mikro-Sponsorluk Eşleştirme ve Reklam Uyum Platformu

NSosyal platformunda mikro ölçekli girişimciler ile içerik üreticilerini Türkçe
anlamsal eşleştirme ve kitle kalitesi göstergesi üzerinden buluşturan, nakit ve
ayni kampanyaları destekleyen, Ticari Reklam Yönetmeliği m. 23/A'ya uygun tanıtım
etiketini otomatik üreten iki taraflı mikro-sponsorluk altyapısı.

**TEKNOFEST 2026 NSosyal İnovasyon Yarışması — İçerik Ekonomisi**
Takım: İstikbalin Cezerileri · Takım ID: 838684 · Başvuru ID: 5394543

---

## Hızlı başlangıç

Prototip kurulum gerektirmez:

    web/AHI_prototip.html   →  tarayıcıda açın

Python çekirdeğini doğrulamak için:

    pip install -r requirements.txt
    python demo_calistir.py

Bu komut korpusu üretir, modelleri eğitir, metrikleri ölçer ve örnek bir brif
çalıştırır. Yaklaşık 20 saniye sürer.

---

## Mimari

    Veri üretimi          Hesaplama (Python)              Arayüz (tarayıcı)
    ─────────────         ──────────────────              ─────────────────
    generate_corpus.py →  embeddings.py                →  AHI_prototip.html
    niches.py             matcher.py  (IsolationForest)
                          labeler.py  (23/A kural motoru)
                          export_web_bundle.py (GBM regresyon)

Model uyarlama, vektörleştirme, anomali tespiti ve karşılık tahmini Python
tarafında yapılır; sonuçlar `web/ahi_data.json` paketine yazılır. Arayüz bu
paketi okur ve yeni bir brif girildiğinde vektörleştirme ile sıralamayı aynı
sözlük ve IDF ağırlıklarıyla istemcide gerçekleştirir.

### Yapay zekâ bileşenleri

| Katman | Yöntem | Dosya |
|---|---|---|
| Brif motoru | Anlamsal alan tespiti, Türkçe kök bulma | `embeddings.py` |
| Eşleştirme | İki aşamalı getirme, TF-IDF / BERTurk (takılabilir) | `embeddings.py`, `matcher.py` |
| Güven katmanı | Isolation Forest, denetimsiz anomali tespiti | `matcher.py` |
| Karşılık önerisi | Gradyan artırmalı regresyon | `export_web_bundle.py` |
| Uyum katmanı | Kural motoru (belirlenimci, model içermez) | `labeler.py` |

---

## Ölçüm sonuçları

3.000 profillik sentetik korpus, 30 içerik alanı, 30 değerlendirme brifi:

| Metrik | Ölçülen | Hedef |
|---|---|---|
| Recall@150 | 1.000 | ≥ 0.90 |
| NDCG@10 | 0.995 | ≥ 0.75 |
| MRR@10 | 1.000 | ≥ 0.70 |
| Precision@10 | 0.993 | ≥ 0.80 |
| Kitle kalitesi yakalama | 300/300 | ≥ 0.85 |
| Karşılık modeli MAPE | %13.6 | ≤ %25 |

Doğrulamak için:

    python tools/rapor_denetimi.py

> Aday havuzu korpusla orantılı ölçeklenir. 3.000 profilde brif başına 100
> ilgili üretici bulunduğundan Recall@50 matematiksel olarak 0.50 ile sınırlıdır;
> bu nedenle Recall@150 raporlanır.

---

## Dizin yapısı

    data/synthetic/     korpus üretimi (30 niş × 20 özgün cümle)
    src/matching/       gömme katmanı, eşleştirme, güven katmanı
    src/compliance/     23/A kural motoru
    src/evaluation/     zayıf denetim ve sıralama metrikleri
    tools/              paketleme, ölçüm, ekran görüntüsü, BERTurk betiği
    tests/              uçtan uca test paketi (56 kontrol)
    web/                tarayıcı prototipi

---

## Test

    python tests/test_prototip.py

Masaüstü ve mobil görünümde marka akışı, üretici akışı, uygunluk eşikleri,
kapsam dışı sektör, coğrafi kural, iki taraflı revizyon döngüsü ve Türkçe
etiket denetimi doğrulanır.

---

## Gömme arka ucu

Varsayılan arka uç bağımlılığı hafif, Türkçeye duyarlı TF-IDF'tir. BERTurk
tabanlı cümle gömme modeline geçiş uygulama kodunu etkilemez:

    from src.matching.embeddings import get_backend
    backend = get_backend("sbert")     # yerine "tfidf"

Vektörleri yerel olarak üretmek için: `python tools/berturk_vektor.py`

---

## Veri ve mahremiyet

Prototip denetimli üretilmiş sentetik korpus üzerinde çalışır; kişisel veri
işlenmez. Gerçek veriye geçişte üretici kendi hesabını açık rıza ile bağlar ve
yalnızca kendi verisi işlenir. Veri kaynağı katmanı bu geçiş için soyutlanmıştır.
