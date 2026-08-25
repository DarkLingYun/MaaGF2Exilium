# -*- coding: utf-8 -*-
"""
Extract the recognition surface of the BASE pipeline into a worksheet, so the
English-client (resource_en) adaptation can be driven by a glossary instead of
editing 78 files by hand.

Outputs assets/resource_en/_glossary.json:
{
  "ocr": {
      "<zh expected string>": "<English — FILL THIS from the EN client>",
      ...
  },
  "_template_nodes": {            # nodes that match by IMAGE (need EN screenshots)
      "<pipeline file>": ["<node>", ...]
  },
  "_ocr_locations": {             # where each zh string is used (context for filling)
      "<zh expected string>": ["<file>::<node>", ...]
  }
}

Workflow:
  1. Run this to (re)generate the worksheet (won't overwrite existing English
     you've already filled in the "ocr" map).
  2. Fill the English values in "ocr" by reading them off the EN client.
  3. Run scripts/build_en_resource.py (separate) to emit resource_en overrides.

Run with PYTHONUTF8=1.
"""
import json
import glob
import os
import re
from pathlib import Path

from _jsonc import load_jsonc

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "assets" / "resource" / "base"
# Worksheet lives OUTSIDE assets/resource (which install.py ships wholesale).
OUT = ROOT / "assets" / "resource_en_glossary.json"
CJK = re.compile(r"[一-鿿]")


def main():
    ocr_strings = {}          # zh -> "" (or kept English if already filled)
    locations = {}            # zh -> [file::node]
    template_nodes = {}       # file -> [nodes matched by template]

    existing = {}
    if OUT.exists():
        existing = json.loads(OUT.read_text(encoding="utf-8")).get("ocr", {})

    for f in sorted(glob.glob(str(BASE / "pipeline" / "**" / "*.json"), recursive=True)):
        rel = os.path.relpath(f, BASE).replace("\\", "/")
        try:
            d = load_jsonc(f)
        except Exception as e:
            print(f"  WARN could not parse {rel}: {e}")
            continue
        for node, v in d.items():
            if not isinstance(v, dict):
                continue
            recog = str(v.get("recognition", "")).upper()
            exp = v.get("expected")
            exps = [exp] if isinstance(exp, str) else (exp if isinstance(exp, list) else [])
            exps = [e for e in exps if isinstance(e, str) and CJK.search(e)]
            for e in exps:
                ocr_strings.setdefault(e, existing.get(e, ""))
                locations.setdefault(e, []).append(f"{rel}::{node}")
            if "Template" in recog or "template" in v:
                template_nodes.setdefault(rel, []).append(node)

    out = {
        "_README": "Fill the English value for each Chinese key in 'ocr' by reading "
                   "the EN client. Empty string = not yet done (falls back to base). "
                   "Then run scripts/build_en_resource.py.",
        "ocr": dict(sorted(ocr_strings.items())),
        "_template_nodes": dict(sorted(template_nodes.items())),
        "_ocr_locations": dict(sorted(locations.items())),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    filled = sum(1 for v in ocr_strings.values() if v)
    tmpl = sum(len(v) for v in template_nodes.values())
    print(f"Glossary written: {OUT.relative_to(ROOT)}")
    print(f"  OCR strings to translate: {len(ocr_strings)}  (already filled: {filled})")
    print(f"  Template-matched nodes (need EN screenshots): {tmpl} across {len(template_nodes)} files")


if __name__ == "__main__":
    main()
