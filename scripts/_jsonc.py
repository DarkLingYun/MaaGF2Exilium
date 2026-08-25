# -*- coding: utf-8 -*-
"""Tolerant JSON loader for MaaFramework pipeline files.

MaaFramework accepts JSONC: `//` line comments, `/* */` block comments, and
trailing commas. Plain json.loads chokes on these, so use load_jsonc() when
reading pipeline JSON or those files get silently skipped.
"""
import json


def strip_jsonc(text):
    out = []
    i, n = 0, len(text)
    in_str = False
    esc = False
    while i < n:
        c = text[i]
        if in_str:
            out.append(c)
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
            out.append(c)
            i += 1
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "/":
            i += 2
            while i < n and text[i] not in "\r\n":
                i += 1
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "*":
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
            continue
        out.append(c)
        i += 1
    s = "".join(out)
    # remove trailing commas:  , }  /  , ]
    import re
    s = re.sub(r",(\s*[}\]])", r"\1", s)
    return s


def load_jsonc(path):
    text = open(path, encoding="utf-8-sig").read()
    return json.loads(strip_jsonc(text))
