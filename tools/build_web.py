# -*- coding: utf-8 -*-
"""Veri paketini HTML şablonuna gömerek tek dosyalık prototip üretir."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
tpl = (ROOT/"web/index_template.html").read_text(encoding="utf-8")
data = (ROOT/"web/ahi_data.json").read_text(encoding="utf-8")
out = ROOT/"web/AHI_prototip.html"
out.write_text(tpl.replace("__DATA__", data), encoding="utf-8")
print(f"{out}  ({out.stat().st_size/1024:.0f} KB)")
