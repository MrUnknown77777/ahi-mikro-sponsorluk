# -*- coding: utf-8 -*-
"""Sunum için prototip ekran görüntülerini üretir."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
URL = (ROOT / "web/AHI_prototip.html").as_uri()
OUT = ROOT / "web/shots"; OUT.mkdir(exist_ok=True)

FLOW = [
    ("#fill", 150), ("#go", 300), ("#match", 600),
]

def shot(pg, name):
    pg.screenshot(path=str(OUT / f"{name}.png"), full_page=True)
    print("  ", name)

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1440, "height": 920}, device_scale_factor=2)
    pg.goto(URL); pg.wait_for_timeout(400)

    shot(pg, "01_brif_girisi")
    pg.click("#fill"); pg.wait_for_timeout(200); shot(pg, "02_brif_dolu")
    pg.click("#go");   pg.wait_for_timeout(350); shot(pg, "03_yapilandirilmis_brif")
    pg.click("#match");pg.wait_for_timeout(700); shot(pg, "04_eslesme_listesi")
    pg.click("#cmp");  pg.wait_for_timeout(600); shot(pg, "05_karsilastirma")
    pg.click("#cmp");  pg.wait_for_timeout(400)
    pg.click(".item"); pg.wait_for_timeout(500); shot(pg, "06_skor_kirilimi")
    pg.click("#offer");pg.wait_for_timeout(450); shot(pg, "07_uretici_teklif")
    pg.click("#acc");  pg.wait_for_timeout(450); shot(pg, "08_uyum_giris")
    pg.fill("#lb", "#işbirliği"); pg.click("#chk"); pg.wait_for_timeout(500)
    shot(pg, "09_uyum_ret")
    pg.click("#pub");  pg.wait_for_timeout(500); shot(pg, "10_kampanya_raporu")
    pg.click("#relearn"); pg.wait_for_timeout(600); shot(pg, "11_geri_besleme")
    b.close()
print("tamam")
