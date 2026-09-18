# -*- coding: utf-8 -*-
"""AHİ — Prototip uçtan uca test paketi.

Kullanıcı yolculuğunun tamamını masaüstü ve mobil görünümde doğrular.

Çalıştırma:
    python tests/test_prototip.py
"""
from __future__ import annotations
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
URL = (ROOT / "web/AHI_prototip.html").as_uri()
basarisiz: list[str] = []


def kontrol(etiket: str, kosul: bool) -> None:
    print(f"  {'✓' if kosul else '✗'} {etiket}")
    if not kosul:
        basarisiz.append(etiket)


def giris(pg, rol="brand"):
    pg.click("#goAhi"); pg.wait_for_timeout(200)
    pg.click("#rBrand" if rol == "brand" else "#rCreator"); pg.wait_for_timeout(150)
    pg.click("#gNext"); pg.wait_for_timeout(200)
    if rol == "creator":
        pg.fill("#eFol", "4200"); pg.fill("#eEng", "3.8")
    pg.fill("#eAge", "14"); pg.wait_for_timeout(250)
    pg.click("#gNext2"); pg.wait_for_timeout(200)
    for i, d in enumerate("123456"):
        pg.fill(f"#c{i}", d)
    pg.click("#gVerify"); pg.wait_for_timeout(350)


def iki_tarafli_surec(b, hatalar):
    """Revizyon döngüsünün iki taraftan da izlenebildiğini doğrular."""
    pg = b.new_page(viewport={"width": 1440, "height": 950})
    pg.on("pageerror", lambda e: hatalar.append(str(e)))
    pg.goto(URL); pg.wait_for_timeout(900)
    pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(900)
    print("\nİKİ TARAFLI SÜREÇ")
    pg.keyboard.press("d"); pg.wait_for_timeout(400)
    pg.fill("#bt", "Kendi kavurduğum kahve çekirdeği satıyorum.")
    pg.fill("#notes", "Gün ışığında çekin.")
    pg.click("#detect"); pg.wait_for_timeout(400)
    pg.click("#run"); pg.wait_for_timeout(600)
    pg.click('[data-i="0"]'); pg.wait_for_timeout(400)
    pg.click("#offer"); pg.wait_for_timeout(400)
    kontrol("üretici menüsünde İşlerim", pg.query_selector('[data-nav="cwork"]') is not None)
    pg.click("#openOffer"); pg.wait_for_timeout(300)
    pg.click("#acc"); pg.wait_for_timeout(300)
    pg.fill("#lb", "#işbirliği"); pg.click("#chk"); pg.wait_for_timeout(350)
    pg.click("#pub"); pg.wait_for_timeout(450)
    pg.fill("#onayNot", "Ürün görseli yakından çekilsin.")
    pg.click("#revizyon"); pg.wait_for_timeout(450)
    kontrol("marka revizyon isteyebiliyor", "Revizyon istendi" in pg.content())
    pg.click("#swap"); pg.wait_for_timeout(350)
    pg.click('[data-nav="cwork"]'); pg.wait_for_timeout(450)
    kontrol("üretici revizyon talebini görüyor", pg.query_selector(".panel.belir") is not None)
    kontrol("revizyon notu iletildi", "yakından çekilsin" in pg.content())
    pg.click("[data-yenile]"); pg.wait_for_timeout(500)
    kontrol("üretici içeriği yeniden gönderebiliyor",
            pg.evaluate("S.campaigns.filter(c=>c.status==='revizyon istendi').length") == 0)
    pg.click("[data-is]"); pg.wait_for_timeout(400)
    kontrol("iş ayrıntısı açılıyor", pg.query_selector("#isKapat") is not None)
    kontrol("üretici hesabı nötr", "Doğrulanmış" in pg.content())
    pg.close()


def arayuz_butunlugu(b, hatalar):
    """İçerik türünün ve ek taleplerin tüm ekranlarda göründüğünü doğrular."""
    pg = b.new_page(viewport={"width": 1440, "height": 950})
    pg.on("pageerror", lambda e: hatalar.append(str(e)))
    pg.goto(URL); pg.wait_for_timeout(900)
    pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(900)
    print("\nARAYÜZ BÜTÜNLÜĞÜ")
    pg.keyboard.press("d"); pg.wait_for_timeout(400)

    bg = pg.eval_on_selector('[data-ct="gorsel"]', "e=>getComputedStyle(e).backgroundColor")
    kontrol("içerik türü butonu koyu temada", "239, 239, 239" not in bg)
    pg.click('[data-ct="kisa_video"]'); pg.wait_for_timeout(300)
    a = pg.eval_on_selector('[data-ct="kisa_video"]', "e=>getComputedStyle(e).borderColor")
    c = pg.eval_on_selector('[data-ct="gorsel"]', "e=>getComputedStyle(e).borderColor")
    kontrol("seçili tür görsel olarak ayrışıyor", a != c)

    pg.fill("#bt", "Kendi kavurduğum kahve çekirdeği satıyorum.")
    pg.fill("#notes", "Ürünü gün ışığında çekin.")
    pg.click("#detect"); pg.wait_for_timeout(400)
    pg.click("#run"); pg.wait_for_timeout(600)
    pg.click("summary"); pg.wait_for_timeout(300)
    kontrol("elenen üretici sayısı bildiriliyor", "listeden çıkarıldı" in pg.content())
    kontrol("listede içerik yetkinliği", "video" in pg.text_content(".list").lower())

    pg.click('[data-i="0"]'); pg.wait_for_timeout(400)
    kontrol("detayda içerik türü", "Kısa video" in pg.content())
    pg.click("#offer"); pg.wait_for_timeout(350)
    kontrol("üretici panelinde yetkinlik", "Üretebildiğim içerik" in pg.content())
    kontrol("teklif listesinde ek talep uyarısı", "Ek talep var" in pg.content())
    pg.click("#openOffer"); pg.wait_for_timeout(350)
    kontrol("teklifte içerik türü", "Kısa video" in pg.content())
    kontrol("teklifte ek talepler görünüyor", "gün ışığında" in pg.content())
    pg.close()


def sistem_kurallari(b, hatalar):
    """Anlamsal alt sınır ve içerik türü fiyatlandırmasını doğrular."""
    pg = b.new_page()
    pg.on("pageerror", lambda e: hatalar.append(str(e)))
    pg.goto(URL); pg.wait_for_timeout(900)
    print("\nSİSTEM KURALLARI")
    r = pg.evaluate("""(()=>{const d={text:'Kendi kavurduğum kahve çekirdeği satıyorum.',
      niche:'butik kahve',city:null,campaign:'barter',budget:null,contentType:'gorsel'};
      const x=pipeline(d);
      return {elenen:x.t.elenen, kalan:x.list.length,
              nisler:[...new Set(x.list.slice(0,10).map(r=>r.c.niche))],
              enDusuk:Math.min(...x.list.map(r=>r.comp.semantic))};})()""")
    kontrol(f"anlamsal alt sınır eledi ({r['elenen']} üretici)", r["elenen"] > 0)
    kontrol("ilk 10 tek nişten", len(r["nisler"]) == 1)
    kontrol("alt sınır altında sonuç yok", r["enDusuk"] >= 45)

    f = pg.evaluate("""(()=>{const c=D.creators.find(x=>x.contentTypes.length===4);
      return c.contentTypes.map(ct=>c.prices[ct][0]);})()""")
    kontrol("fiyat içerik karmaşıklığıyla artıyor",
            all(f[i] < f[i+1] for i in range(len(f)-1)))
    pg.close()


def uyum_motoru(b, hatalar):
    """Türkçe karakterli etiketlerin doğru denetlendiğini doğrular.

    #işbirliği gibi etiketlerde \\w Latin harfleriyle sınırlı olduğu için
    normalizasyon bir kez bozulmuştu; bu kontrol nüksetmesini engeller.
    """
    pg = b.new_page()
    pg.on("pageerror", lambda e: hatalar.append(str(e)))
    pg.goto(URL); pg.wait_for_timeout(600)
    print("\nUYUM MOTORU — Türkçe etiket denetimi")
    vakalar = [
        ("#işbirliği", False), ("#sponsorlu", False), ("işbirliği", False),
        ("#hediye", False), ("#ad", False),
        ("Reklam — İşletme Hesabım tarafından sağlanmıştır", True),
    ]
    for etiket, beklenen in vakalar:
        r = pg.evaluate(f"denetle({etiket!r},'İşletme Hesabım')")
        kontrol(f"{etiket[:44]:46s} → {'uygun' if beklenen else 'reddedilmeli'}",
                r["uygun"] == beklenen)
    pg.close()


def masaustu(b, hatalar):
    pg = b.new_page(viewport={"width": 1440, "height": 950})
    pg.on("pageerror", lambda e: hatalar.append(str(e)))
    pg.goto(URL); pg.wait_for_timeout(500)
    pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(500)

    print("\nMASAÜSTÜ — marka akışı")
    giris(pg, "brand")
    kontrol("giriş yapıldı", pg.text_content("h1") == "Kampanyalarım")
    kontrol("kampanya listesi dolu", pg.query_selector("[data-camp]") is not None)
    pg.click("[data-camp]"); pg.wait_for_timeout(300)
    kontrol("kampanya ayrıntısı açıldı", pg.query_selector("#closeCamp") is not None)
    pg.click("#closeCamp"); pg.wait_for_timeout(200)

    pg.click('[data-nav="perf"]'); pg.wait_for_timeout(350)
    kontrol("sistem performansı metrikleri", "Recall@50" in pg.content())

    pg.click('[data-nav="new"]'); pg.wait_for_timeout(250)
    pg.fill("#bt", "Gümüşten kolye ve yüzük yapıyorum, kargoyla gönderiyorum.")
    pg.click("#detect"); pg.wait_for_timeout(400)
    kontrol("yapılandırılmış brif üretildi", "Oluşturulan brif" in pg.content())
    kontrol("doğru alan tespiti", "el yapımı takı" in pg.content())

    pg.click("#run"); pg.wait_for_timeout(500)
    kontrol("seçim kutucukları", len(pg.query_selector_all("[data-sel]")) > 0)
    pg.check('[data-sel="0"]'); pg.check('[data-sel="1"]'); pg.wait_for_timeout(250)
    kontrol("çoklu teklif butonu", pg.query_selector("#bulk") is not None)

    pg.click("#cmp"); pg.wait_for_timeout(400)
    kontrol("naif sıralama karşılaştırması", "Takipçi odaklı" in pg.content())
    pg.click("#cmp"); pg.wait_for_timeout(300)

    pg.click('[data-i="0"]'); pg.wait_for_timeout(400)
    kontrol("açıklanabilirlik bölümü", "neden önerildi" in pg.content().lower())
    pg.click("#offer"); pg.wait_for_timeout(350)
    kontrol("teklif doğru nişte", "takı" in pg.text_content(".offer.new").lower())
    pg.click("#openOffer"); pg.wait_for_timeout(250)
    pg.click("#acc"); pg.wait_for_timeout(250)
    pg.fill("#lb", "#işbirliği"); pg.click("#chk"); pg.wait_for_timeout(350)
    kontrol("uyumsuz etiket reddedildi", "23/A" in pg.content())
    pg.click("#pub"); pg.wait_for_timeout(450)
    kontrol("marka onay ekranı", "onayınızı bekliyor" in pg.content())
    pg.click("#onayla"); pg.wait_for_timeout(450)
    kontrol("kampanya raporu", "Kampanya raporu" in pg.content())
    pg.click("#re"); pg.wait_for_timeout(500)
    kontrol("geri besleme tablosu", "Önceki sıra" in pg.content())

    print("\nMASAÜSTÜ — kapsam dışı ve coğrafi kısıt")
    # onay adımı rolü markaya döndürür; ek geçiş gerekmez
    pg.click('[data-nav="new"]'); pg.wait_for_timeout(250)
    pg.fill("#bt", "Sigorta poliçesi satıyorum."); pg.click("#detect"); pg.wait_for_timeout(400)
    kontrol("kapsam dışı uyarısı", "Kapsam dışı" in pg.content())
    kontrol("devam kilitli", not pg.is_enabled("#run"))
    pg.click('[data-nav="new"]'); pg.wait_for_timeout(300)
    pg.fill("#bt", "Kendi kavurduğum kahve çekirdeği satıyorum.")
    pg.select_option("#cty", "Ankara")
    pg.select_option("#kati", "hard")          # katı kural: yalnızca seçilen şehir
    pg.click("#detect"); pg.wait_for_timeout(400)
    pg.click("#run"); pg.wait_for_timeout(500)
    sehirler = pg.eval_on_selector_all(".who2 .m", "e=>e.map(x=>x.textContent)")
    kontrol("katı coğrafi kural yalnızca o şehri getiriyor",
            len(sehirler) > 0 and all("Ankara" in s for s in sehirler))

    # Yumuşak kural: komşu iller de değerlendirilir, coğrafi skor kademelenir
    pg.click('[data-nav="new"]'); pg.wait_for_timeout(300)
    pg.select_option("#kati", "soft"); pg.click("#detect"); pg.wait_for_timeout(350)
    pg.click("#run"); pg.wait_for_timeout(500)
    skorlar = pg.evaluate("""(()=>{const x=pipeline(S.draft);
      return [...new Set(x.list.slice(0,8).map(r=>Math.round(r.comp.geo)))];})()""")
    kontrol("yumuşak kuralda coğrafi skor kademeli", len(skorlar) > 1)
    pg.reload(); pg.wait_for_timeout(700)
    kontrol("yenileme sonrası kurtarma", pg.query_selector(".item") is not None)
    pg.close()


def uretici(b, hatalar):
    pg = b.new_page(viewport={"width": 1440, "height": 950})
    pg.on("pageerror", lambda e: hatalar.append(str(e)))
    pg.goto(URL); pg.wait_for_timeout(500)
    pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(500)

    print("\nMASAÜSTÜ — üretici akışı ve uygunluk eşiği")
    pg.click("#goAhi"); pg.wait_for_timeout(200)
    pg.click("#rCreator"); pg.wait_for_timeout(150)
    pg.click("#gNext"); pg.wait_for_timeout(200)
    pg.fill("#eFol", "500"); pg.fill("#eAge", "14"); pg.fill("#eEng", "3.8")
    pg.wait_for_timeout(300)
    kontrol("eşik altı engellendi", not pg.is_enabled("#gNext2"))
    pg.fill("#eFol", "4200"); pg.wait_for_timeout(300)
    kontrol("eşik üstü geçti", pg.is_enabled("#gNext2"))
    pg.click("#gNext2"); pg.wait_for_timeout(200)
    pg.click("#gVerify"); pg.wait_for_timeout(250)
    kontrol("boş kod reddedildi", pg.query_selector(".tferr") is not None)
    for i, d in enumerate("123456"):
        pg.fill(f"#c{i}", d)
    pg.click("#gVerify"); pg.wait_for_timeout(350)
    kontrol("üretici paneli", pg.text_content("h1") == "Panelim")
    pg.click('[data-nav="coffers"]'); pg.wait_for_timeout(300)
    kontrol("gelen teklifler", "Gelen teklifler" in pg.content())
    pg.close()


def mobil(b, hatalar):
    pg = b.new_page(viewport={"width": 390, "height": 844})
    pg.on("pageerror", lambda e: hatalar.append(str(e)))
    pg.goto(URL); pg.wait_for_timeout(600)
    pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(600)

    print("\nMOBİL — 390×844")
    pg.click("#goAhi2"); pg.wait_for_timeout(250)
    giris_mobil = pg.query_selector("#rBrand") is not None
    kontrol("giriş ekranı mobilde açıldı", giris_mobil)
    pg.click("#rBrand"); pg.wait_for_timeout(200)
    pg.click("#gNext"); pg.wait_for_timeout(200)
    pg.fill("#eAge", "14"); pg.wait_for_timeout(250)
    pg.click("#gNext2"); pg.wait_for_timeout(200)
    for i, d in enumerate("123456"):
        pg.fill(f"#c{i}", d)
    pg.click("#gVerify"); pg.wait_for_timeout(400)
    tasma = pg.evaluate(
        "document.documentElement.scrollWidth>document.documentElement.clientWidth")
    kontrol("yatay taşma yok", not tasma)
    rail_top = pg.eval_on_selector(".rail", "e=>e.getBoundingClientRect().top")
    kontrol("menü alt çubuğa dönüştü", rail_top > 600)
    pg.click('[data-nav="new"]'); pg.wait_for_timeout(300)
    pg.fill("#bt", "Kedi maması ve oyuncağı satıyorum.")
    pg.click("#detect"); pg.wait_for_timeout(400)
    pg.click("#run"); pg.wait_for_timeout(500)
    kontrol("mobilde sonuç listesi", pg.query_selector(".item") is not None)
    kontrol("mobilde taşma yok", not pg.evaluate(
        "document.documentElement.scrollWidth>document.documentElement.clientWidth"))
    pg.close()


def main() -> None:
    hatalar: list[str] = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        masaustu(b, hatalar)
        uyum_motoru(b, hatalar)
        sistem_kurallari(b, hatalar)
        arayuz_butunlugu(b, hatalar)
        iki_tarafli_surec(b, hatalar)
        uretici(b, hatalar)
        mobil(b, hatalar)
        b.close()

    print("\n" + "─" * 60)
    if hatalar:
        print("JAVASCRIPT HATALARI:")
        for h in set(hatalar):
            print("  ", h)
    else:
        print("JavaScript hatası yok.")
    if basarisiz:
        print(f"BAŞARISIZ: {len(basarisiz)}")
        for x in basarisiz:
            print("  ", x)
        sys.exit(1)
    print("Tüm kontroller geçti.")


if __name__ == "__main__":
    main()
