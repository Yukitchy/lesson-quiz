#!/usr/bin/env python3
"""板書レッスンmdから抽出した語彙を data/<student>.json へマージする補助CLI（夜間ルーチン用）

使い方:
  python3 merge_vocab.py --pending          未処理のレッスンmd一覧を表示（0件なら "PENDING: 0"）
  python3 merge_vocab.py --seed             現存する全レッスンmdを処理済み扱いで台帳に登録（初期化用）
  python3 merge_vocab.py --skip <ファイル名>  対象外レッスンとして台帳に記録
  python3 merge_vocab.py <payload.json>     語彙をマージして台帳に記録

payload.json の形式:
  {"key": "pedro", "student": "Pedro", "src": "2026-07-10-Pedro-テーマ.md",
   "items": [{"ja": "...", "yomi": "...|null", "en": "...", "d": "YYYY-MM-DD"}]}

- 重複は (ja, en) の組で判定して自動スキップ（同じレッスンを二重処理しても安全＝冪等）
- config.json に居ない新生徒は flag "🌍"・slug空 で自動追加（build_quiz.py が slug を採番）
- macOSのNFDファイル名対策で台帳キーは常にNFC正規化
"""
import json, sys, unicodedata, pathlib

ROOT = pathlib.Path(__file__).parent
LESSONS = pathlib.Path("/Users/yuki/Library/Mobile Documents/iCloud~md~obsidian/Documents/ClaudeVault/notes/lessons")
LEDGER = ROOT / "data" / "processed_lessons.json"


def nfc(s):
    return unicodedata.normalize("NFC", s) if isinstance(s, str) else s


def load_ledger():
    return json.load(open(LEDGER)) if LEDGER.exists() else {}


def save_ledger(led):
    json.dump(led, open(LEDGER, "w"), ensure_ascii=False, indent=1, sort_keys=True)


def lesson_files():
    return sorted(nfc(p.name) for p in LESSONS.glob("*.md") if not p.name.startswith("_"))


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    led = load_ledger()

    if args[0] == "--pending":
        pend = [f for f in lesson_files() if f not in led]
        print(f"PENDING: {len(pend)}")
        for f in pend:
            print(f)
        return

    if args[0] == "--seed":
        n = 0
        for f in lesson_files():
            if f not in led:
                led[f] = "seeded"
                n += 1
        save_ledger(led)
        print(f"seeded {n} files (total {len(led)})")
        return

    if args[0] == "--skip":
        led[nfc(args[1])] = "skipped"
        save_ledger(led)
        print(f"skipped: {args[1]}")
        return

    payload = json.load(open(args[0]))
    key, student, src = payload["key"], payload["student"], nfc(payload["src"])
    data_path = ROOT / "data" / f"{key}.json"
    data = json.load(open(data_path)) if data_path.exists() else {"student": student, "items": []}

    seen = {(nfc(x["ja"]), x["en"].strip().lower()) for x in data["items"]}
    added = 0
    for it in payload["items"]:
        if not it.get("ja") or not it.get("en"):
            continue
        pair = (nfc(it["ja"]), it["en"].strip().lower())
        if pair in seen:
            continue
        seen.add(pair)
        data["items"].append({"ja": nfc(it["ja"]), "yomi": nfc(it.get("yomi")),
                              "en": it["en"].strip(), "d": it.get("d"), "src": src})
        added += 1
    json.dump(data, open(data_path, "w"), ensure_ascii=False, indent=1)

    cfg_path = ROOT / "config.json"
    cfg = json.load(open(cfg_path))
    new_student = key not in cfg["students"]
    if new_student:
        cfg["students"][key] = {"flag": "🌍", "slug": ""}
        json.dump(cfg, open(cfg_path, "w"), ensure_ascii=False, indent=2)

    led[src] = f"merged:+{added}"
    save_ledger(led)
    print(f"{student}: +{added} words (total {len(data['items'])})"
          + (" [NEW STUDENT — config.jsonのflagを国旗に直してね]" if new_student else ""))


if __name__ == "__main__":
    main()
