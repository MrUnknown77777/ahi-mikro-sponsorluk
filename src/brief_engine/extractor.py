"""Brif motoru: serbest metni yapılandırılmış brife dönüştürür."""

from dataclasses import dataclass, field


@dataclass
class Brief:
    """Girişimcinin serbest metninden çıkarılan yapılandırılmış brif."""
    product_category: str
    target_audience: str
    campaign_type: str          # "cash" | "barter"
    budget_range: tuple | None = None
    barter_offer: str | None = None
    key_messages: list = field(default_factory=list)
    excluded_terms: list = field(default_factory=list)
    geo_constraint: str | None = None


def extract_brief(free_text: str) -> Brief:
    """Serbest metinden brif alanlarını çıkarır.

    Girişimci ürününü kendi cümleleriyle anlatır; yapılandırma işini
    kullanıcı değil sistem üstlenir.
    """
    raise NotImplementedError("Geliştirme aşamasında")
