# -*- coding: utf-8 -*-
"""AHİ — Reklam mevzuatı uyum katmanı.

Ticari Reklam ve Haksız Ticari Uygulamalar Yönetmeliği m. 23/A
(RG 01.07.2026, Sayı 33297 — yürürlük 01.08.2026) kurallarını uygular.

Bilinçli olarak kural tabanlıdır: mevzuat uygunluğu belirlenimci olmak
zorundadır; olasılıksal bir model burada öngörülemez risk üretir.
Kurallar uygulama kodundan ayrı tutulur, mevzuat değiştiğinde yalnızca
bu tanımlar güncellenir.
"""
from __future__ import annotations

# 23/A ile kaldırılan serbest ifadeler
KALDIRILAN_IFADELER = {
    "işbirliği", "isbirligi", "sponsor", "sponsorlu", "hediyem",
    "teşekkürler", "tesekkurler", "ad", "collab", "iş birliği",
}

# Etiketleme zorunluluğu doğuran kampanya tipleri.
# Ayni menfaat de reklam sayılır; barter kampanyalarda da etiket zorunludur.
ETIKET_ZORUNLU = {"cash", "barter", "event", "discount"}


def etiket_uret(marka_adi: str, kampanya_tipi: str) -> str:
    """Mevzuata uygun tanıtım etiketini üretir."""
    if kampanya_tipi not in ETIKET_ZORUNLU:
        raise ValueError(f"Bilinmeyen kampanya tipi: {kampanya_tipi}")
    if not marka_adi.strip():
        raise ValueError("Marka adı zorunludur")
    return f"Reklam — {marka_adi.strip()} tarafından sağlanmıştır"


def denetle(etiket: str, marka_adi: str) -> dict:
    """Yayın öncesi uyum denetimi.

    Döndürülen sözlük, arayüzde madde madde gösterilir; kullanıcı hangi
    kuralın karşılanmadığını doğrudan görür.
    """
    e = etiket.lower().strip()
    marka_var = marka_adi.lower().strip() in e
    serbest = any(k in e for k in KALDIRILAN_IFADELER)
    return {
        "marka_adi_var": marka_var,
        "serbest_ifade": serbest,
        "uygun": marka_var and not serbest,
        "onerilen": etiket_uret(marka_adi, "barter"),
        "dayanak": "Ticari Reklam ve Haksız Ticari Uygulamalar Yönetmeliği m. 23/A",
    }
