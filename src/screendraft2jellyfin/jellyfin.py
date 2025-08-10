import string, requests
from difflib import SequenceMatcher
from typing import Optional, Tuple, List

GUID_CHARS = set(string.hexdigits.lower() + '-')

class JellyfinClient:

    def find_playlist_by_name(self, name: str, user_id: str=None):
        """Return (playlist_id, name) for an exact name match owned/visible to the user, else None."""
        uid = user_id or self.user_id
        params = {
            "IncludeItemTypes": "Playlist",
            "Recursive": "true",
            "SearchTerm": name,
            "Limit": 50
        }
        data = self._get(f"/Users/{uid}/Items", **params)
        for it in data.get("Items", []):
            if it.get("Name","").strip().lower() == name.strip().lower():
                return it.get("Id"), it.get("Name","")
        return None

    def get_playlist_items(self, playlist_id: str, user_id: str=None):
        """Return list of {'PlaylistItemId':..., 'ItemId':..., 'Name':...} for a playlist."""
        uid = user_id or self.user_id
        params = {"UserId": uid, "Fields": "BasicSyncInfo,CanDelete"}
        data = self._get(f"/Playlists/{playlist_id}/Items", **params)
        items = []
        for it in data.get("Items", []):
            pid = it.get("PlaylistItemId") or it.get("Id")
            items.append({
                "PlaylistItemId": pid,
                "ItemId": it.get("Id"),
                "Name": it.get("Name","")
            })
        return items

    def clear_playlist(self, playlist_id: str, user_id: str=None):
        """Remove all entries from a playlist by deleting each PlaylistItemId."""
        items = self.get_playlist_items(playlist_id, user_id=user_id)
        if not items:
            return
        entry_ids = ",".join([i["PlaylistItemId"] for i in items if i.get("PlaylistItemId")])
        # Some servers accept DELETE with query; others exposed via SDK removeItemFromPlaylist
        import requests
        url = f"{self.base}/Playlists/{playlist_id}/Items"
        r = requests.delete(url, headers=self.headers, params={"EntryIds": entry_ids}, timeout=30)
        if not r.ok and r.status_code != 204:
            raise SystemExit(f"DELETE /Playlists/{playlist_id}/Items -> HTTP {r.status_code}: {r.text}")
    def __init__(self, base_url: str, api_key: str, user_hint: str):
        self.base = base_url.rstrip("/")
        self.user_id = user_hint
        self.headers = {
            "X-Emby-Token": api_key,
            "X-Emby-Authorization": 'MediaBrowser Client="SD-Playlist", Device="script", DeviceId="sd-playlist-1", Version="1.0.0", Token="%s"' % api_key,
            "Content-Type": "application/json"
        }

    def _get(self, path: str, **params):
        r = requests.get(f"{self.base}{path}", headers=self.headers, params=params, timeout=30)
        if not r.ok: raise SystemExit(f"GET {path} -> HTTP {r.status_code}: {r.text}")
        return r.json()

    def _post_json(self, path: str, **params):
        r = requests.post(f"{self.base}{path}", headers=self.headers, params=params, timeout=30)
        if not r.ok: raise SystemExit(f"POST {path} -> HTTP {r.status_code}: {r.text}")
        return r.json() if r.content else {}

    def _post(self, path: str, **params):
        r = requests.post(f"{self.base}{path}", headers=self.headers, params=params, timeout=30)
        if not r.ok: raise SystemExit(f"POST {path} -> HTTP {r.status_code}: {r.text}")
        return True

    def resolve_user_id(self, hint: str) -> str:
        h = hint.strip()
        if 32 <= len(h) <= 36 and set(h.lower()) <= GUID_CHARS and '-' in h:
            return h
        try:
            for u in self._get("/Users"):
                if u.get("Name","").strip().lower() == h.lower():
                    return u["Id"]
        except Exception:
            pass
        try:
            me = self._get("/Users/Me")
            if me.get("Name","").strip().lower() == h.lower():
                return me["Id"]
        except Exception:
            pass
        raise SystemExit(f"Could not resolve user '{hint}' to an Id.")

    def find_library_id(self, name_substring: Optional[str]) -> Optional[str]:
        if not name_substring:
            return None
        views = self._get(f"/Users/{self.user_id}/Views").get("Items", [])
        target = name_substring.lower()
        for v in views:
            if target in v.get("Name","").lower():
                return v["Id"]
        return None

    def search_items(self, title: str, parent_id: Optional[str], limit=25):
        params = {"IncludeItemTypes":"Movie","Recursive":"true","SearchTerm":title,"Limit":limit}
        if parent_id: params["ParentId"] = parent_id
        data = self._get(f"/Users/{self.user_id}/Items", **params)
        return data.get("Items", [])

    def score(self, a: str, b: str) -> float:
        return SequenceMatcher(None, a, b).ratio()

    def search_movie_best(self, title: str, parent_id: Optional[str], threshold: float) -> Optional[Tuple[str,str,float,int]]:
        items = self.search_items(title, parent_id, limit=25)
        if not items:
            return None
        for it in items:
            if it.get("Name","").strip().lower() == title.strip().lower():
                return it["Id"], it.get("Name",""), 1.0, it.get("ProductionYear") or 0
        def sc(it): return self.score(it.get("Name",""), title)
        best = max(items, key=sc); s = sc(best)
        return (best["Id"], best.get("Name",""), s, best.get("ProductionYear") or 0) if s >= threshold else None

    def suggestions(self, title: str, parent_id: Optional[str], limit=8):
        items = self.search_items(title, parent_id, limit=30)
        def sc(it): return self.score(it.get("Name",""), title)
        ranked = sorted(items, key=sc, reverse=True)[:limit]
        out = []
        for it in ranked:
            out.append({
                "id": it["Id"],
                "name": it.get("Name",""),
                "year": it.get("ProductionYear"),
                "score": round(sc(it), 3)
            })
        return out

    def create_playlist(self, name: str) -> str:
        return self._post_json("/Playlists", name=name, userId=self.user_id)["Id"]

    def add_items(self, playlist_id: str, item_ids: List[str]):
        if not item_ids: return
        self._post(f"/Playlists/{playlist_id}/Items", Ids=",".join(item_ids), UserId=self.user_id)
