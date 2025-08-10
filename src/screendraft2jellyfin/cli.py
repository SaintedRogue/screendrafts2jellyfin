import os, argparse
from .fandom import resolve_episode_arg, fetch_wikitext_for_title, extract_episode_title, extract_ranked_films
from .jellyfin import JellyfinClient
from .title_utils import generate_query_variants

def main():
    ap = argparse.ArgumentParser(description="Create a ranked Jellyfin playlist from a ScreenDrafts episode.")
    ap.add_argument("--user", "--user-id", dest="user", required=True, help="Jellyfin username or GUID.")
    ap.add_argument("--list", required=True, help="Episode title or full Fandom API URL.")
    ap.add_argument("--library", default="movies", help='Substring of Movies library name (default: "movies").')
    ap.add_argument("--threshold", type=float, default=0.66, help="Fuzzy title threshold 0–1 (default 0.66).")
    ap.add_argument("--prefix", default="ScreenDrafts - ", help="Playlist name prefix.")
    ap.add_argument("--reverse", action="store_true", help="Add items lowest→highest rank.")
    ap.add_argument("--dry-run", action="store_true", help="Resolve & print without creating playlist.")
    ap.add_argument("--interactive", action="store_true", help="Prompt to resolve unmatched titles (pick/skip/custom).")
    ap.add_argument("--overwrite", action="store_true", help="If a playlist with the same name exists, replace its items.")
    args = ap.parse_args()

    base_url = os.environ.get("JELLYFIN_URL")
    api_key  = os.environ.get("JF_KEY")
    if not base_url or not api_key:
        raise SystemExit("Missing env vars. Please set JELLYFIN_URL and JF_KEY.")

    page_title = resolve_episode_arg(args.list)
    wikitext, api_title = fetch_wikitext_for_title(page_title)
    episode_title = extract_episode_title(wikitext, api_title)
    films = extract_ranked_films(wikitext)
    if not films:
        raise SystemExit(f"No ranked films found on '{episode_title}'.")

    films_sorted = sorted(films, key=lambda x: int(x["rank"]), reverse=args.reverse)

    jf = JellyfinClient(base_url, api_key, args.user)
    jf.user_id = jf.resolve_user_id(args.user)
    parent_id = jf.find_library_id(args.library)
    if args.library and not parent_id:
        print(f'NOTE: Could not find a library containing "{args.library}". Searching all movies.')

    print(f"[{episode_title}] threshold={args.threshold} library='{args.library}' reverse={args.reverse}")

    resolved, unresolved = [], []

    for f in films_sorted:
        title = f["title"]
        best = jf.search_movie_best(title, parent_id, threshold=args.threshold)
        if not best:
            for q in generate_query_variants(title):
                best = jf.search_movie_best(q, parent_id, threshold=args.threshold) or                        jf.search_movie_best(q, None, threshold=args.threshold)
                if best: break

        if not best and args.interactive:
            print(f"\nUnresolved: #{f['rank']} {title}")
            cands = jf.suggestions(title, parent_id, limit=8)
            if not cands and parent_id:
                cands = jf.suggestions(title, None, limit=8)
            if cands:
                for i, c in enumerate(cands, 1):
                    yr = f" ({c['year']})" if c['year'] else ""
                    print(f"  {i}. {c['name']}{yr}  [score={c['score']}, id={c['id']}]")
            else:
                print("  (no suggestions)")

            while True:
                choice = input("Pick #, 'c' to type a custom search, 's' to skip: ").strip().lower()
                if choice == "s":
                    break
                if choice == "c":
                    term = input("Custom search term: ").strip()
                    cands = jf.suggestions(term, parent_id, limit=8) or jf.suggestions(term, None, limit=8)
                    for i, c in enumerate(cands, 1):
                        yr = f" ({c['year']})" if c['year'] else ""
                        print(f"  {i}. {c['name']}{yr}  [score={c['score']}, id={c['id']}]")
                    continue
                if choice.isdigit():
                    idx = int(choice)
                    if 1 <= idx <= len(cands):
                        sel = cands[idx-1]
                        best = (sel["id"], sel["name"], sel["score"], sel["year"] or 0)
                        break
                    else:
                        print("Invalid number.")
                else:
                    print("Invalid input.")

        if best:
            item_id, item_name, score, year = best
            resolved.append({"rank": f["rank"], "title": title, "matched": item_name,
                             "score": round(score, 3), "year": year, "id": item_id})
        else:
            unresolved.append({"rank": f["rank"], "title": title})

    print(f"Resolved {len(resolved)} / {len(films_sorted)}")
    if args.dry_run:
        if resolved:
            print("Matches:")
            for r in resolved:
                yr = f" ({r['year']})" if r["year"] else ""
                print(f"  #{r['rank']:>2} {r['title']}  →  {r['matched']}{yr}  (score={r['score']}, id={r['id']})")
        if unresolved:
            print("Unresolved:")
            for u in unresolved:
                print(f"  #{u['rank']:>2} {u['title']}")
        return

    
    playlist_name = f"{args.prefix}{episode_title}"
    # Overwrite logic
    existing = jf.find_playlist_by_name(playlist_name)
    if existing:
        if args.overwrite:
            pid, _ = existing
            print(f"Overwriting existing playlist: {playlist_name} (id={pid})")
            jf.clear_playlist(pid)
            jf.add_items(pid, [r["id"] for r in resolved])
            print(f"Updated playlist: {playlist_name} (id={pid}) with {len(resolved)} items.")
            if unresolved:
                print("Unresolved (not added):")
                for u in unresolved:
                    print(f"  #{u['rank']:>2} {u['title']}")
            return
        else:
            print(f"A playlist named '{playlist_name}' already exists. Use --overwrite to replace its contents.")
            return

    # overwrite logic inserted
    playlist_name = f"{args.prefix}{episode_title}"
    playlist_id = jf.create_playlist(playlist_name)
    jf.add_items(playlist_id, [r["id"] for r in resolved])
    print(f"Created playlist: {playlist_name} (id={playlist_id}) with {len(resolved)} items.")
    if unresolved:
        print("Unresolved (not added):")
        for u in unresolved:
            print(f"  #{u['rank']:>2} {u['title']}")
