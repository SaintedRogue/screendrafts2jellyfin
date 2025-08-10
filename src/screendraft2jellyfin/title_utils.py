import re, unicodedata
from typing import List, Optional

def strip_accents(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))

def normalize_punct(s: str) -> str:
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = s.replace("–", "-").replace("—", "-")
    return s

def insert_colon_before_subtitle(s: str) -> Optional[str]:
    if ":" in s: return None
    m = re.match(r"^(.+?)\s+(with|without|and|the|part|chapter|versus|vs\.?|episode)\b(.*)$", s, re.I)
    if not m: return None
    return f"{m.group(1).strip()}: {m.group(2).capitalize()}{m.group(3)}".strip()

def collapse_ws(s: str) -> str:
    return " ".join(s.split())

def generate_query_variants(title: str) -> List[str]:
    t = normalize_punct(strip_accents(title)).strip()
    variants = {t}
    variants.add(re.sub(r"\band\b", "&", t, flags=re.I))
    variants.add(re.sub(r"&", "and", t))
    variants.add(t.replace(" - ", ": "))
    if ":" in t:
        variants.add(t.replace(":", " - "))
    else:
        v = insert_colon_before_subtitle(t)
        if v: variants.add(v)
    variants.add(re.sub(r"[!?,:;‘’“”'\"()\[\]-]", " ", t))
    variants = {collapse_ws(v) for v in variants}
    return [v for v in variants if v and v != title]
