# AHİ — Mikro-Sponsorluk Eşleştirme ve Reklam Uyum Platformu

NSosyal platformunda mikro ölçekli girişimciler ile içerik üreticilerini
Türkçe semantik eşleştirme ve kitle kalitesi skoru üzerinden buluşturan,
nakit ve ayni kampanyaları destekleyen, Ticari Reklam Yönetmeliği 23/A'ya
uygun tanıtım etiketini otomatik üreten iki taraflı mikro-sponsorluk altyapısı.

TEKNOFEST 2026 NSosyal İnovasyon Yarışması — İçerik Ekonomisi teması.

## Modüller

| Modül | Görevi |
|---|---|
| `brief_engine` | Serbest metni yapılandırılmış brife dönüştürür |
| `matching` | İki aşamalı anlamsal eşleştirme (bi-encoder + cross-encoder) |
| `trust` | Kitle kalitesi ve marka güvenliği göstergesi |
| `pricing` | Kampanya karşılığı öneri modeli |
| `compliance` | 23/A uyumlu etiket üretimi ve yayın öncesi denetim |
| `analytics` | Kampanya performansı ve geri besleme döngüsü |

## Kurulum

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Sentetik korpus üretimi

Prototip, kişisel veri işlememek için sentetik korpus üzerinde çalışır.

```bash
python data/synthetic/generate_corpus.py
```

## Durum

Geliştirme aşamasında. Teknik rapor teslimi: 24 Ağustos 2026.
