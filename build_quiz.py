#!/usr/bin/env python3
"""data/{student}.json + config.json + template.html → docs/{slug}/index.html（GitHub Pages用）"""
import json, secrets, datetime, pathlib, html

ROOT = pathlib.Path(__file__).parent
MIN_ITEMS = 4  # 4択が成立する最低語数


def build():
    cfg_path = ROOT / "config.json"
    cfg = json.load(open(cfg_path))
    tpl = open(ROOT / "template.html").read()
    build_stamp = datetime.date.today().strftime("%Y-%m-%d")
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    # 一覧ページは作らない（生徒間でURLを推測されないようslug直リンクのみ）
    (docs / "index.html").write_text("<!doctype html><title>quiz</title>")
    (docs / ".nojekyll").write_text("")

    rows, skipped = [], []
    for name, s in cfg["students"].items():
        data_path = ROOT / "data" / f"{name}.json"
        if not data_path.exists():
            skipped.append((name, "データなし"))
            continue
        data = json.load(open(data_path))
        items = [x for x in data["items"] if x.get("ja") and x.get("en")]
        if len(items) < MIN_ITEMS:
            skipped.append((name, f"語数不足({len(items)}語)"))
            continue
        if not s["slug"]:  # 初回のみ採番して永続化（URL固定のため）
            s["slug"] = f"{name}-{secrets.token_hex(2)}"
        student = data["student"]
        payload = {"student": student, "items": items}
        out = (tpl
               .replace("__TITLE__", f"{student}'s Vocabulary Quiz")
               .replace("__STUDENT__", html.escape(student))
               .replace("__FLAG__", s["flag"])
               .replace("__BUILD__", build_stamp)
               .replace("__DATA__", json.dumps(payload, ensure_ascii=False)))
        d = docs / s["slug"]
        d.mkdir(exist_ok=True)
        (d / "index.html").write_text(out)
        url = f"{cfg['base_url'].rstrip('/')}/{s['slug']}/" if cfg["base_url"] else f"docs/{s['slug']}/"
        rows.append((student, len(items), url))

    json.dump(cfg, open(cfg_path, "w"), ensure_ascii=False, indent=2)

    print(f"built {len(rows)} quiz pages ({build_stamp})")
    for st, n, url in rows:
        print(f"  {st:10s} {n:3d} words  {url}")
    for name, why in skipped:
        print(f"  -- skip {name}: {why}")


if __name__ == "__main__":
    build()
