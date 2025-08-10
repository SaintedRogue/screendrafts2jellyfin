# ScreenDrafts → Jellyfin Playlist

Create ranked **Jellyfin** playlists straight from **Screen Drafts** episode pages on Fandom.  
It preserves ranking (top → bottom by default, or bottom → top with `--reverse`), ignores vetoed/overridden picks, supports **interactive matching** for tricky titles, and scopes searches to your Movies library.

---

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation (Option A: virtualenv + editable install)](#installation-option-a-virtualenv--editable-install)
- [Environment Variables](#environment-variables)
- [Usage](#usage)
  - [Basic commands](#basic-commands)
  - [Reverse order](#reverse-order)
  - [Interactive matching](#interactive-matching)
  - [Overwrite existing playlist](#overwrite-existing-playlist)
  - [Scope to a library](#scope-to-a-library)
  - [Adjust fuzzy threshold](#adjust-fuzzy-threshold)
  - [Passing a full Fandom URL](#passing-a-full-fandom-url)
- [CLI Reference](#cli-reference)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Tips & Title Quirks](#tips--title-quirks)
- [Publish to GitHub (quick guide)](#publish-to-github-quick-guide)
- [Development](#development)
- [Docker](#docker)
- [License](#license)

---

## Features

- Parses Screen Drafts **Fandom wikitext** and extracts the **final drafted list** (ignores vetoed/overridden entries)
- **Preserves rank order** (1 → N by default; `--reverse` flips to N → 1)
- Reads your **Jellyfin URL** and **API key** from env vars
- Accepts **username or GUID** for the Jellyfin user (auto-resolves username to Id)
- **Fuzzy matching** for titles (default threshold `0.66`)
- **Smart title variants**: normalizes punctuation, tries `&` ⇄ `and`, `:` ⇄ `-`, removes odd quotes/accents, etc.
- **Interactive mode**: choose from suggestions, custom search, or skip for unresolved titles
- **Overwrite** mode: replace contents of an existing playlist (same name) instead of creating a new one
- Works with **single-section** and **multi-section** episode pages

---

## Requirements

- **Python 3.9+**
- A **Jellyfin API key** that can read your libraries and create playlists

---

## Installation (Option A: virtualenv + editable install)

```bash
# 1) Clone and enter the repo
git clone https://github.com/<YOUR_USER>/screendraft2jellyfin.git
cd screendraft2jellyfin

# 2) Create & activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate     # Windows PowerShell: .venv\Scripts\Activate.ps1

# 3) Install the CLI in editable mode
python3 -m pip install --upgrade pip
pip install -e .
```

> After this, the `screendraft2jellyfin` command should be on your PATH **inside** the venv.

---

## Environment Variables

Set these before running the CLI:

```bash
export JELLYFIN_URL="http://<server>:8096"
export JF_KEY="<your_api_key>"
```

Windows PowerShell:
```powershell
$env:JELLYFIN_URL = "http://<server>:8096"
$env:JF_KEY = "<your_api_key>"
```

> Tip: copy `.env.example` to `.env` and `source .env` to load them from a file.

---

## Usage

### Basic commands

Help:
```bash
screendraft2jellyfin --help
```

Dry-run (no playlist created), highest → lowest:
```bash
screendraft2jellyfin --user "YourJellyfinUsername" --list "Kidventure" --dry-run
```

Create the playlist:
```bash
screendraft2jellyfin --user "YourJellyfinUsername" --list "Kidventure"
```

### Reverse order
Play bottom → top:
```bash
screendraft2jellyfin --user "YourJellyfinUsername" --list "'90s_Action_Mega_Draft" --reverse
```

### Interactive matching
Prompt to resolve tricky titles:
```bash
screendraft2jellyfin --user "YourJellyfinUsername" --list "Steven Soderbergh" --interactive
```

### Overwrite existing playlist
If a playlist with the same name already exists, replace its items:
```bash
screendraft2jellyfin --user "YourJellyfinUsername" --list "Kidventure" --overwrite
```

### Scope to a library
(Defaults to `"movies"`; substring match against your Jellyfin libraries.)
```bash
screendraft2jellyfin --user "YourJellyfinUsername" --list "Disney Animation Studios Mega Draft" --library "4k movies"
```

### Adjust fuzzy threshold
(Default is `0.66`; higher = stricter)
```bash
screendraft2jellyfin --user "YourJellyfinUsername" --list "Kidventure" --threshold 0.72
```

### Passing a full Fandom URL
You can pass an **episode title** OR the **Fandom API URL**:
```bash
screendraft2jellyfin --user "YourJellyfinUsername"   --list "https://screendrafts.fandom.com/api.php?action=parse&format=json&formatversion=2&prop=wikitext&page=%2790s_Action_Mega_Draft"
```

---

## CLI Reference

```
screendraft2jellyfin --user USER_OR_GUID --list TITLE_OR_URL [options]

Required:
  --user, --user-id     Jellyfin username or GUID (username auto-resolves to Id)
  --list                Screen Drafts episode title OR full Fandom API URL

Options:
  --library TEXT        Substring of your Movies library name (default: "movies")
  --threshold FLOAT     Fuzzy match threshold 0–1 (default: 0.66)
  --prefix TEXT         Playlist name prefix (default: "ScreenDrafts - ")
  --reverse             Add items lowest→highest rank (default: highest→lowest)
  --dry-run             Resolve & print matches/unresolved without creating a playlist
  --interactive         Prompt to resolve unmatched titles (pick/custom/skip)
  --overwrite           If a playlist with the same name exists, replace its contents
```

---

## Examples

Create a playlist from the **Kidventure** episode:
```bash
screendraft2jellyfin --user "SaintedRogue" --list "Kidventure"
```

Parse the **’90s Action Mega Draft** (URL form) and interactively confirm any misses:
```bash
screendraft2jellyfin --user "SaintedRogue"   --list "https://screendrafts.fandom.com/api.php?action=parse&format=json&formatversion=2&prop=wikitext&page=%2790s_Action_Mega_Draft"   --interactive
```

Reverse order (bottom → top) with overwrite:
```bash
screendraft2jellyfin --user "SaintedRogue" --list "Disney Animation Studios Mega Draft" --reverse --overwrite
```

---

## Troubleshooting

**“command not found: screendraft2jellyfin”**  
Make sure your virtualenv is activated (`source .venv/bin/activate`) and you ran `pip install -e .`.  
Alternatively run as a module:
```bash
PYTHONPATH=src python3 -m screendraft2jellyfin --help
```

**“Missing env vars. Please set JELLYFIN_URL and JF_KEY.”**  
Check the env vars are exported:
```bash
echo "$JELLYFIN_URL" ; echo "$JF_KEY"
```
(PowerShell: `echo $env:JELLYFIN_URL; echo $env:JF_KEY`)

**User not found / 400 on `/Users/{id}/Views`**  
Pass your **username**; the tool resolves it to your GUID. If resolution fails, fetch your GUID:
```bash
curl -s -H "X-Emby-Token: $JF_KEY" "${JELLYFIN_URL%/}/Users/Me" | jq -r '{Name,Id}'
```
Then use that `Id` with `--user`.

**Playlist already exists**  
Use `--overwrite` to replace its items; without it the tool won’t modify an existing playlist.

**A title won’t match**  
- Try `--interactive` to pick from suggestions or enter a custom search term.  
- You can also tweak `--threshold` or adjust `--library` to broaden/narrow the search scope.

---

## Tips & Title Quirks

- Some titles vary by punctuation or subtitles (e.g., `"Die Hard with a Vengeance"` vs `"Die Hard: With a Vengeance"`).  
  The tool automatically tries reasonable variants: normalizes quotes, tries `&/and`, swaps `:` and `-`, and removes odd punctuation.
- If a title still won’t match, `--interactive` will list likely candidates (with scores and years) so you can pick or skip.

---

## Publish to GitHub (quick guide)

Using GitHub’s website:

```bash
cd screendraft2jellyfin

git init
git add -A
git commit -m "Initial commit: ScreenDrafts → Jellyfin playlist tool"
git branch -M main

# Replace with your repo URL (HTTPS shown here)
git remote add origin https://github.com/<YOUR_USER>/screendraft2jellyfin.git
git push -u origin main
```

Using GitHub CLI (if installed):

```bash
cd screendraft2jellyfin
git init
git add -A
git commit -m "Initial commit: ScreenDrafts → Jellyfin playlist tool"
git branch -M main
gh auth login
gh repo create <YOUR_USER>/screendraft2jellyfin --public -s . --push
```

---

## Development

Run tests:
```bash
pytest -q
```

---

## Docker

Build:
```bash
docker build -t screendraft2jellyfin .
```

Run:
```bash
docker run --rm -it   -e JELLYFIN_URL="http://<server>:8096"   -e JF_KEY="<your_api_key>"   screendraft2jellyfin   screendraft2jellyfin --user "YourJellyfinUsername" --list "Kidventure" --dry-run
```

---

## License

MIT
