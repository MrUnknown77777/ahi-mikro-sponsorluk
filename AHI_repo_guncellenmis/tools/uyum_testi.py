# -*- coding: utf-8 -*-
"""Uyum katmanı doğrulama betiği.

Kurulum gerektirmez; jüri incelemesi için tek komutla çalıştırılabilir:

    python tools/uyum_testi.py

23/A denetiminin iki yönünü birlikte sınar: sistemin ürettiği uyumlu
etiketlerin kabul edilmesi ve uygunsuz etiketlerin reddedilmesi.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.compliance.labeler import build_label, validate

UYGUN_MARKALAR = [
    "Kare Akademi", "Sade Yaşam", "Kadıköy Seramik", "Adana Bal",
    "Hediyelik Eşya Atölyesi", "Zeytin Atölye", "Kuzey Kavurma",
]

UYGUNSUZ = [
    ("#işbirliği", "Zeytin Atölye", "serbest ifade, beyan yok"),
    ("Sponsorlu içerik Zeytin Atölye", "Zeytin Atölye", "kaldırılan ifade"),
    ("zeytinyağı tarifi", "Zeytin Atölye", "ticari nitelik beyan edilmemiş"),
    ("Zeytin Atölye", "Zeytin Atölye", "yalnız marka adı yeterli değil"),
    ("Reklam", "Zeytin Atölye", "marka adı yok"),
    ("", "Zeytin Atölye", "boş etiket"),
]


def main() -> int:
    hata = 0
    print("Sistemin ürettiği etiketler (kabul edilmeli)")
    for marka in UYGUN_MARKALAR:
        etiket = build_label(marka, "barter")
        r = validate(etiket, marka)
        if not r["uygun"]:
            hata += 1
        print(f"  {'✓' if r['uygun'] else '✗'} {marka}")

    print("\nUygunsuz etiketler (reddedilmeli)")
    for etiket, marka, aciklama in UYGUNSUZ:
        r = validate(etiket, marka)
        if r["uygun"]:
            hata += 1
        print(f"  {'✓' if not r['uygun'] else '✗'} {etiket!r:42s} {aciklama}")
        print(f"      → {r['gerekce'][0]}")

    toplam = len(UYGUN_MARKALAR) + len(UYGUNSUZ)
    print(f"\n{toplam - hata}/{toplam} kontrol geçti.")
    return 1 if hata else 0


if __name__ == "__main__":
    raise SystemExit(main())
