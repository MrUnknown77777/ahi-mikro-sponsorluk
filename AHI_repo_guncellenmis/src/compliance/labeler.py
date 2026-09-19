# -*- coding: utf-8 -*-
"""Reklam mevzuatı uyum katmanı.

Ticari Reklam ve Haksız Ticari Uygulamalar Yönetmeliği m. 23/A
(RG 01.07.2026, Sayı 33297 — yürürlük 01.08.2026) kurallarını uygular.

Bilinçli olarak kural tabanlıdır: mevzuat uygunluğu belirlenimci olmak
zorundadır, olasılıksal bir model burada öngörülemez risk üretir.

Denetim üç koşulu birlikte arar:
  1. Etiket, içeriğin ticari nitelikte olduğunu açıkça beyan etmelidir.
  2. Etiket, markanın adını içermelidir.
  3. Yönetmelikle kaldırılan serbest ifadeler kullanılmamalıdır.

Eşleşme kelime sınırında yapılır. Alt dizgi taraması Türkçede yanlış sonuç
üretir: "Akademi", "Sade", "Kadıköy" gibi adlar "ad" hecesini taşıdığından,
alt dizgi kullanan bir denetim sistemin kendi ürettiği uyumlu etiketi
reddedebilir. Yasaklı ifade taraması ayrıca marka adı etiketten çıkarıldıktan
sonra yapılır; aksi hâlde "Hediyelik Eşya Atölyesi" gibi bir işletmenin
uyumlu etiketi, adındaki kelime nedeniyle reddedilirdi.
"""
from __future__ import annotations
import re

# Ayni menfaat de reklam sayılır; barter kampanyalarda da etiket zorunludur.
CAMPAIGN_TYPES_REQUIRING_LABEL = {"cash", "barter", "event", "discount"}

# Yönetmelik değişikliğiyle kaldırılan ya da tek başına yeterli olmayan ifadeler.
KALDIRILAN = (
    "işbirliği", "isbirligi", "sponsor", "sponsorlu", "sponsorluğunda",
    "hediye", "hediyelik", "teşekkür", "collab", "collaboration",
    "reklam değildir",
)

# Ticari niteliği açıkça beyan eden ifadeler.
BEYAN = ("reklam", "tanıtım", "tanitim", "ticari ileti", "reklamdır", "reklamdir")

_TR_KUCUK = str.maketrans("IİĞÜŞÖÇ", "ıiğüşöç")


def normalize(metin: str) -> str:
    """Türkçeye duyarlı küçük harfe çevirme ve boşluk sadeleştirme."""
    return re.sub(r"\s+", " ", metin.translate(_TR_KUCUK).lower()).strip()


def _kelime_gecer(metin: str, kalip: str) -> bool:
    """Kalıbı kelime sınırında arar; Türkçe ekler nedeniyle sonek serbesttir."""
    temiz = " " + re.sub(r"[^\w\s]", " ", normalize(metin)) + " "
    temiz = re.sub(r"\s+", " ", temiz)
    k = normalize(kalip)
    return (" " + k + " ") in temiz or (" " + k) in temiz


def build_label(brand_name: str, campaign_type: str) -> str:
    """Mevzuata uygun tanıtım etiketini üretir.

    Etiket marka adını içermeli, arka fondan ayırt edilebilir olmalı ve
    kaydırma gerekmeden ilk anda görülebilecek konumda bulunmalıdır.
    """
    if campaign_type not in CAMPAIGN_TYPES_REQUIRING_LABEL:
        raise ValueError(f"Bilinmeyen kampanya tipi: {campaign_type}")
    return f"Reklam — {brand_name} tarafından sağlanmıştır"


def validate(label: str, brand_name: str) -> dict:
    """Yayın öncesi uyum denetimi yapar.

    Returns:
        dict: beyan_var, marka_var, serbest_ifade, uygun ve gerekçe alanları.
              'uygun' yalnızca üç koşulun birlikte sağlanmasıyla True olur.
    """
    ham = (label or "").strip()
    n = normalize(ham)
    marka = normalize(brand_name or "")

    marka_var = len(marka) > 2 and marka in n
    if not marka_var:
        parcalar = [p for p in marka.split(" ") if p]
        if len(parcalar) >= 2:
            marka_var = " ".join(parcalar[:2]) in n

    kalan = n.replace(marka, " ") if marka else n
    serbest = [k for k in KALDIRILAN if _kelime_gecer(kalan, k)]
    beyan_var = any(_kelime_gecer(ham, k) for k in BEYAN)

    gerekce = []
    if not ham:
        gerekce.append("Etiket boş.")
    if not beyan_var:
        gerekce.append("Etiket, içeriğin ticari nitelikte olduğunu beyan etmiyor.")
    if not marka_var:
        gerekce.append("Etiket marka adını içermiyor.")
    if serbest:
        gerekce.append("Kaldırılan ifade kullanılmış: " + ", ".join(serbest) + ".")

    return {
        "beyan_var": beyan_var,
        "marka_var": marka_var,
        "serbest_ifade": serbest,
        "uygun": bool(ham) and beyan_var and marka_var and not serbest,
        "gerekce": gerekce or ["Etiket 23/A gerekliliklerini karşılıyor."],
    }
