import re, requests
from typing import List, Dict, Tuple, Optional
from urllib.parse import urlparse, parse_qs, unquote_plus

API_FANDOM = "https://screendrafts.fandom.com/api.php"
MARKER = "The following films were drafted:"

def resolve_episode_arg(arg: str) -> str:
    val = arg.strip()
    if val.lower().startswith("http"):
        q = parse_qs(urlparse(val).query)
        page = (q.get("page") or [None])[0]
        if not page: raise SystemExit("URL lacks 'page=' parameter.")
        val = page
    return unquote_plus(val).replace("_", " ")

def fetch_wikitext_for_title(title: str) -> Tuple[str, str]:
    def _fetch(section: Optional[int]):
        params = {"action":"parse","format":"json","formatversion":2,"prop":"wikitext","page":title}
        if section is not None: params["section"] = section
        r = requests.get(API_FANDOM, params=params, timeout=30); r.raise_for_status()
        data = r.json()
        return data["parse"]["wikitext"], data["parse"]["title"]
    w0, api_title = _fetch(section=0)
    if extract_ranked_films(w0): return w0, api_title
    wfull, api_title = _fetch(section=None)
    return wfull, api_title

def extract_episode_title(wikitext: str, fallback: str) -> str:
    m = re.search(r"'''\"([^\"]+)\"'''", wikitext)
    return m.group(1).strip() if m else fallback

def first_wikilink_outside_strike(line: str):
    struck_spans = [(m.start(), m.end()) for m in re.finditer(r"<s>.*?</s>", line)]
    def in_struck(i: int) -> bool: return any(a <= i < b for a,b in struck_spans)
    for m in re.finditer(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", line):
        if not in_struck(m.start()):
            page, display = m.group(1), m.group(2)
            return (display or page).strip()
    return None

def extract_ranked_films(wikitext: str) -> List[Dict]:
    i = wikitext.find(MARKER)
    if i == -1: return []
    films: List[Dict] = []
    for raw in wikitext[i+len(MARKER):].splitlines():
        line = raw.strip()
        mnum = re.match(r"^(\d+)\.\s", line)
        if not mnum: continue
        film = first_wikilink_outside_strike(line)
        if not film: continue
        films.append({"rank": int(mnum.group(1)), "title": film})
    return films
