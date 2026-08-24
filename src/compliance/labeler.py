"""Reklam mevzuatı uyum katmanı.

Ticari Reklam ve Haksız Ticari Uygulamalar Yönetmeliği m. 23/A
(RG 01.07.2026, Sayı 33297 — yürürlük 01.08.2026) kurallarını uygular.

Bilinçli olarak kural tabanlıdır: mevzuat uygunluğu belirlenimci olmak
zorundadır, olasılıksal bir model burada öngörülemez risk üretir.
"""

# Ayni menfaat de reklam sayılır; barter kampanyalarda da etiket zorunludur.
CAMPAIGN_TYPES_REQUIRING_LABEL = {"cash", "barter", "event", "discount"}


def build_label(brand_name: str, campaign_type: str) -> str:
    """Mevzuata uygun tanıtım etiketini üretir.

    Etiket marka adını içermeli, arka fondan ayırt edilebilir olmalı ve
    kaydırma gerekmeden ilk anda görülebilecek konumda bulunmalıdır.
    """
    if campaign_type not in CAMPAIGN_TYPES_REQUIRING_LABEL:
        raise ValueError(f"Bilinmeyen kampanya tipi: {campaign_type}")
    return f"Reklam — {brand_name} tarafından sağlanmıştır"


def validate(content_text: str, label: str) -> dict:
    """Yayın öncesi uyum denetimi yapar."""
    raise NotImplementedError("Geliştirme aşamasında")
