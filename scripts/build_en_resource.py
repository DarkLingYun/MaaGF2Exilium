# -*- coding: utf-8 -*-
"""
Generate English-client OCR overrides into resource_en from the glossary.

Reads:
  - assets/resource_en_glossary.json   (the "ocr" map: zh expected string -> English)
  - assets/resource/base/pipeline/**   (the base nodes to override)

Writes:
  - assets/resource/resource_en/pipeline/_auto_en_ocr.json
      A single file of {node: {"expected": <English>}} overrides, regenerated
      every run. MaaFramework merges resources FIELD-LEVEL across resource paths,
      so overriding only `expected` is enough; the rest comes from base.

Rules:
  - Only nodes whose OCR `expected` (string or list) has at least one entry
    translated in the glossary are emitted.
  - For a list, translated Chinese entries are replaced; untranslated Chinese
    entries are DROPPED (they can't match the EN client); non-Chinese entries
    (numbers, already-English, etc.) are kept as-is.
  - Any node already defined in a *manual* resource_en file is SKIPPED — manual
    overrides win, and a node must not be defined twice within one resource.
    (So to hand-tune a generated node, move it into a manual file; the generator
    will then leave it alone.)

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
EN = ROOT / "assets" / "resource" / "resource_en"
GLOSSARY = ROOT / "assets" / "resource_en_glossary.json"
AUTO_FILE = EN / "pipeline" / "_auto_en_ocr.json"
CJK = re.compile(r"[一-鿿]")


def manual_node_names():
    """Node names already defined in hand-authored resource_en pipeline files."""
    names = set()
    for f in glob.glob(str(EN / "pipeline" / "**" / "*.json"), recursive=True):
        if Path(f).resolve() == AUTO_FILE.resolve():
            continue
        try:
            d = load_jsonc(f)
        except Exception:
            continue
        names.update(k for k in d if isinstance(d.get(k), dict))
    return names


def translate_expected(exp, ocr):
    """Return (new_expected, fully_translated:bool) or (None, _) if nothing usable."""
    items = [exp] if isinstance(exp, str) else exp
    out, had_zh, missed = [], False, False
    for x in items:
        if not isinstance(x, str):
            out.append(x)
            continue
        if CJK.search(x):
            had_zh = True
            en = ocr.get(x, "")
            if en:
                out.append(en)
            else:
                missed = True
        else:
            out.append(x)  # numbers / already-English: keep
    if not had_zh or not out or all(not (isinstance(o, str) and o) for o in out):
        return None, False
    new = out[0] if (isinstance(exp, str) and len(out) == 1) else out
    return new, (not missed)


def translate_focus(foc, fmap_keys, fmap):
    """Translate the string values of a `focus` dict via substring replacement.

    MaaFramework replaces the whole `focus` field on override, so we return the
    COMPLETE dict (every sub-key), translating any CJK phrase found in the map
    and leaving markup (e.g. <span>) and untranslated text intact.
    Returns (new_focus, changed, still_zh) where still_zh lists values that
    still contain CJK after translation (missing glossary entries).
    """
    out, changed, still_zh = {}, False, []
    for k, val in foc.items():
        if isinstance(val, str) and CJK.search(val):
            newval = val
            for zh in fmap_keys:  # longest-first: avoids partial-key clobber
                if zh in newval:
                    newval = newval.replace(zh, fmap[zh])
            if newval != val:
                changed = True
            if CJK.search(newval):
                still_zh.append(newval)
            out[k] = newval
        else:
            out[k] = val
    return out, changed, still_zh


def main():
    glossary = json.loads(GLOSSARY.read_text(encoding="utf-8"))
    ocr = {k: v for k, v in glossary.get("ocr", {}).items() if v}  # filled only
    focus_map = {k: v for k, v in glossary.get("focus", {}).items() if v}
    focus_keys = sorted(focus_map, key=len, reverse=True)
    manual = manual_node_names()

    generated = {}
    partials = []          # nodes emitted but with some entries still untranslated
    needs = {}             # file -> [nodes that have zh OCR but no/partial fills]
    focus_missing = set()  # focus values still containing CJK (missing glossary)
    focus_count = 0        # nodes given a focus override
    covered_files = set()

    for f in sorted(glob.glob(str(BASE / "pipeline" / "**" / "*.json"), recursive=True)):
        rel = os.path.relpath(f, BASE).replace("\\", "/")
        try:
            d = load_jsonc(f)
        except Exception:
            continue
        for node, v in d.items():
            if not isinstance(v, dict):
                continue
            if node in manual or node in generated:
                continue
            override = {}

            exp = v.get("expected")
            if exp is not None:
                has_zh = any(isinstance(x, str) and CJK.search(x)
                             for x in ([exp] if isinstance(exp, str) else exp))
                if has_zh:
                    new, full = translate_expected(exp, ocr)
                    if new is None:
                        needs.setdefault(rel, []).append(node)
                    else:
                        override["expected"] = new
                        if not full:
                            partials.append(f"{rel}::{node}")

            foc = v.get("focus")
            if isinstance(foc, dict):
                new_foc, changed, still_zh = translate_focus(foc, focus_keys, focus_map)
                if changed:
                    override["focus"] = new_foc
                    focus_count += 1
                focus_missing.update(still_zh)

            if override:
                generated[node] = override
                covered_files.add(rel)

    # NOTE: every top-level key here must be a pipeline node (object) — MaaFramework
    # will choke on a stray string, so we do NOT embed a _README key. This file is
    # AUTO-GENERATED; to customize a node, move it into a manual resource_en file
    # (the generator then skips it).
    AUTO_FILE.parent.mkdir(parents=True, exist_ok=True)
    AUTO_FILE.write_text(
        json.dumps(generated, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8",
    )

    total_need = sum(len(v) for v in needs.values())
    print(f"Generated {len(generated)} override node(s) -> {AUTO_FILE.relative_to(ROOT)}")
    print(f"  (manual nodes skipped: {len(manual)})")
    print(f"  focus/log overrides: {focus_count} node(s)")
    if partials:
        print(f"  partial (some list entries still untranslated): {len(partials)}")
    print(f"  nodes still needing OCR glossary fills: {total_need} across {len(needs)} files")
    if focus_missing:
        print(f"  focus values still containing zh (missing focus fills): {len(focus_missing)}")
    print(f"  glossary filled: {len(ocr)} ocr, {len(focus_map)} focus")


if __name__ == "__main__":
    main()
