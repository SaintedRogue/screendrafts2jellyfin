# ScreenDrafts → Jellyfin Playlist

Create ranked Jellyfin playlists from ScreenDrafts Fandom episode pages.

## Quickstart
```bash
pip install -e .
export JELLYFIN_URL="http://10.0.0.248:8096"
export JF_KEY="your_api_key"
screendraft2jellyfin --user "SaintedRogue" --list "Kidventure" --dry-run
```


### Overwrite an existing playlist

If a playlist with the same name already exists, pass `--overwrite` to replace its items:

```bash
screendraft2jellyfin --user "SaintedRogue" --list "Kidventure" --overwrite
```
