import json, html, pathlib, sys

D = pathlib.Path(__file__).parent
OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else D / "index.html"

items = []
for f in ["tokyo", "hokkaido", "kansai", "west", "extra"]:
    p = D / f"{f}.json"
    if p.exists():
        items += json.loads(p.read_text())

# route order; items are bucketed by the first key found in their "city"
ROUTE = [
    ("tokyo", "Tokyo", "東京", 35.681, 139.767),
    ("sapporo", "Sapporo", "札幌", 43.062, 141.354),
    ("biei", "Biei", "美瑛", 43.588, 142.467),
    ("osaka", "Osaka", "大阪", 34.702, 135.495),
    ("kyoto", "Kyoto", "京都", 35.011, 135.768),
    ("hiroshima", "Hiroshima", "広島", 34.397, 132.475),
    ("nagasaki", "Nagasaki", "長崎", 32.750, 129.878),
    ("okinawa", "Okinawa", "沖縄", 26.212, 127.681),
]
ALIAS = {"kobe": "osaka", "himeji": "osaka", "kameoka": "kyoto", "arima": "osaka", "hakone": "tokyo", "jozankei": "sapporo",
         "miyajima": "hiroshima", "unzen": "nagasaki", "ureshino": "nagasaki",
         "hokkaido": "sapporo", "asahidake": "biei", "daisetsuzan": "biei", "naha": "okinawa"}
CAT = {"onsen": ("Onsen", "温泉"), "anime": ("Anime & manga", "アニメ・マンガ"),
       "food": ("Food", "食べ物"), "couple": ("For two", "ふたりで"),
       "nature": ("Nature", "自然"), "horror": ("Horror", "ホラー"),
       "season": ("Late October", "10月下旬"), "culture": ("Culture", "文化")}


def bucket(city):
    c = city.lower()
    for key, *_ in ROUTE:
        if key in c:
            return key
    for a, key in ALIAS.items():
        if a in c:
            return key
    return "tokyo"


e = lambda s: html.escape(s or "")


def bi(en, ja, tag="span"):
    return f'<{tag} class="en">{e(en)}</{tag}><{tag} class="ja" lang="ja">{e(ja)}</{tag}>'


def gmaps(it):
    from urllib.parse import quote
    return "https://www.google.com/maps/search/?api=1&query=" + quote(it.get("maps_query") or it["name_en"])


def card(it, n):
    cat_en, cat_ja = CAT.get(it.get("category"), (it.get("category", ""), ""))
    ph = it.get("photo") or {}
    ex = f'<span class="ex">{bi("Example dish, not this shop", "料理のイメージ写真（この店ではありません）")}</span>' if ph.get("example") else ""
    img = (f'<div class="ph"><img loading="lazy" src="{e(ph["url"])}" alt="{e(it["name_en"])}">'
           f'{ex}</div>') if ph.get("url") else ""
    tip = f'<p class="tip">{bi(it.get("tip_en"), it.get("tip_ja"))}</p>' if it.get("tip_en") else ""
    maplink = f'<a class="maplink" href="{e(gmaps(it))}" target="_blank" rel="noopener">{bi("Map", "地図")}</a>'
    official = f'<a href="{e(it["official_url"])}" target="_blank" rel="noopener">{bi("Official site", "公式サイト")}</a>' if it.get("official_url") else ""
    return f'''<details class="card c-{e(it.get("category"))}" data-n="{n}">
<summary><span class="num inline">{n}</span><span class="head"><span class="cat">{bi(cat_en, cat_ja)}</span>
<span class="name">{e(it["name_en"].split(" (")[0])}</span><small>{e(("(" + it["name_en"].split(" (",1)[1]) if " (" in it["name_en"] else "")}</small><small lang="ja">{e(it.get("name_ja"))}</small></span>{maplink}<span class="chev" aria-hidden="true"></span></summary>
{img}<div class="body"><p class="why">{bi(it.get("why_en"), it.get("why_ja"))}</p>{tip}
<div class="links">{official}</div></div></details>'''


sections, markers, credits = [], [], []
for key, en, ja, lat, lng in ROUTE:
    its = [i for i in items if bucket(i.get("city", "")) == key]
    if not its:
        continue
    pts = []
    cards = []
    for n, it in enumerate(its, 1):
        cards.append(card(it, n))
        if it.get("lat") and it.get("lng"):
            pts.append([it["lat"], it["lng"], n, it["name_en"]])
        ph = it.get("photo") or {}
        if ph.get("url"):
            credits.append(f'<li>{e(it["name_en"])}: <a href="{e(ph.get("commons_page"))}" target="_blank" rel="noopener">{e(ph.get("credit") or "Wikimedia Commons")}</a></li>')
    extra = ""
    sections.append(f'''<section class="city" id="{key}">
<header><p class="step">{ROUTE.index((key, en, ja, lat, lng)) + 1:02d}</p><h2>{en} <span class="sub" lang="ja">{ja}</span></h2></header>
<div class="citymap" data-pts='{e(json.dumps(pts))}'></div>
<div class="grid">{"".join(cards)}</div>{extra}</section>''')
    markers.append([lat, lng, en, key])

exec((D / 'extras.py').read_text())
route_pts = json.dumps([[m[0], m[1], m[2], m[3]] for m in markers])

page = f'''<!DOCTYPE html>
<html lang="en" data-lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="noindex">
<title>Kelsi &amp; Max in Japan</title>
<link rel="icon" href="data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='22' fill='%23C8102E'/><circle cx='50' cy='50' r='22' fill='white'/></svg>">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=Inter:wght@400;500;600&family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet">
<style>
:root{{--bg:#FAF7F2;--card:#fff;--ink:#1d1d1f;--sub:#6b6b70;--line:#e7e2d9;--red:#C8102E;--moss:#3F6B4E}}
*{{box-sizing:border-box;margin:0;padding:0}}
html{{background:var(--bg)}}
body{{font:16px/1.65 Inter,"Noto Sans JP",system-ui,sans-serif;color:var(--ink);background:var(--bg)}}
html[data-lang=en] .ja{{display:none}} html[data-lang=ja] .en{{display:none}}
a{{color:inherit}}
.wrap{{max-width:1080px;margin:0 auto;padding:0 16px}}
.hero{{position:relative;min-height:78vh;display:flex;align-items:flex-end;color:#fff;overflow:hidden}}
.hero img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}
.hero::after{{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.05) 30%,rgba(0,0,0,.65))}}
.hero .wrap{{position:relative;z-index:1;padding-bottom:48px;width:100%}}
.hero h1{{font:700 clamp(40px,8vw,84px)/1.02 Fraunces,serif;letter-spacing:-.02em}}
.hero p{{font-size:clamp(16px,2.2vw,20px);margin-top:12px;max-width:34em;opacity:.95}}
.toggle{{position:fixed;top:14px;right:14px;z-index:1000;display:flex;background:#fff;border:1px solid var(--line);border-radius:999px;overflow:hidden;box-shadow:0 2px 10px rgba(0,0,0,.08)}}
.toggle button{{border:0;background:none;padding:8px 14px;font:600 13px Inter,"Noto Sans JP",sans-serif;cursor:pointer;color:var(--sub)}}
.toggle button[aria-pressed=true]{{background:var(--ink);color:#fff}}
.intro{{padding:56px 0 24px}}
.intro h2,.city h2{{font:700 clamp(28px,4.5vw,44px)/1.1 Fraunces,serif;letter-spacing:-.01em}}
.intro p{{max-width:40em;margin-top:12px;color:var(--sub)}}
.chips{{display:flex;flex-wrap:wrap;gap:8px;margin-top:20px}}
.chips>span{{background:#fff;border:1px solid var(--line);border-radius:999px;padding:6px 12px;font-size:14px}}
#route{{height:440px;border-radius:14px;margin:28px 0 8px;border:1px solid var(--line)}}
.legend{{font-size:13px;color:var(--sub)}}
.city{{padding:56px 0 8px;border-top:1px solid var(--line);margin-top:40px}}
.city header{{display:flex;align-items:baseline;gap:14px}}
.step{{font:700 15px Inter;color:var(--red);letter-spacing:.08em}}
.city h2 .sub{{font:500 .5em "Noto Sans JP";color:var(--sub);margin-left:6px}}
.citymap{{height:260px;border-radius:12px;margin:20px 0;border:1px solid var(--line)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:12px;align-items:start}}
.card{{background:var(--card);border-radius:14px;overflow:hidden;border:1px solid var(--line)}}
.card summary{{list-style:none;cursor:pointer;display:flex;align-items:center;gap:12px;padding:14px 16px}}
.card summary::-webkit-details-marker{{display:none}}
.card .head{{flex:1;min-width:0;display:flex;flex-direction:column}}
.card .name{{font:700 18px/1.25 Fraunces,serif}}
.card .head small{{font:500 12px "Noto Sans JP";color:var(--sub)}}
.card .head .cat{{font-size:11px}}
.maplink{{flex:none;font:600 13px Inter,"Noto Sans JP";color:var(--red);text-decoration:none;border:1px solid var(--line);border-radius:999px;padding:6px 12px}}
.chev{{flex:none;width:10px;height:10px;border-right:2px solid var(--sub);border-bottom:2px solid var(--sub);transform:rotate(45deg);margin:0 4px 4px}}
.card[open] .chev{{transform:rotate(-135deg);margin-bottom:-4px}}
.card[open]{{box-shadow:0 6px 20px rgba(0,0,0,.08)}}
.card.flash{{outline:2px solid var(--red)}}
.ph{{position:relative;aspect-ratio:3/2;background:#e9e4da}}
.ph img{{width:100%;height:100%;object-fit:cover;display:block}}
.num{{position:absolute;top:10px;left:10px;width:28px;height:28px;border-radius:50%;background:var(--red);color:#fff;font:700 14px/28px Inter;text-align:center}}
.num.inline{{position:static;display:inline-block;margin-right:8px;vertical-align:middle}}
.ex{{position:absolute;right:8px;bottom:8px;background:rgba(0,0,0,.6);color:#fff;font-size:11px;padding:2px 8px;border-radius:999px}}
.body{{padding:14px 18px 18px;display:flex;flex-direction:column;gap:8px;flex:1}}
.cat{{font:600 12px Inter,"Noto Sans JP";letter-spacing:.08em;text-transform:uppercase;color:var(--moss)}}
.c-couple .cat{{color:var(--red)}}
.why{{font-size:15px}}
.tip{{font-size:14px;color:var(--sub);border-left:3px solid var(--line);padding-left:10px}}
.links{{margin-top:auto;display:flex;gap:16px;padding-top:6px;font:600 14px Inter,"Noto Sans JP"}}
.links a{{color:var(--red);text-decoration:none}} .links a:hover{{text-decoration:underline}}
.tour{{margin-top:28px;background:var(--ink);color:#fff;border-radius:14px;padding:24px;display:flex;gap:20px;align-items:center;justify-content:space-between;flex-wrap:wrap}}
.tour .cat{{color:#f3b3bd}} .tour h3{{font:700 24px Fraunces,serif;margin:4px 0}} .tour p{{max-width:36em}}
.btn{{background:var(--red);color:#fff;text-decoration:none;padding:12px 20px;border-radius:999px;font-weight:600;white-space:nowrap}}
footer{{margin-top:64px;padding:40px 0 64px;border-top:1px solid var(--line);font-size:13px;color:var(--sub)}}
.credits{{margin-top:12px}} .credits summary{{cursor:pointer;font-weight:600;color:var(--ink)}}
footer ul{{list-style:none;margin-top:12px;columns:2;column-gap:24px}} footer li{{break-inside:avoid;margin-bottom:4px}}
@media(max-width:640px){{.grid{{grid-template-columns:1fr}} #route{{height:360px}} footer ul{{columns:1}}}}
EXTRA_CSS_HERE</style>
</head>
<body>
<div class="toggle" role="group" aria-label="Language"><button data-l="en" aria-pressed="true">EN</button><button data-l="ja" aria-pressed="false">日本語</button></div>
<header class="hero">
<img src="HERO_SRC" alt="">
<div class="wrap">
<h1>Kelsi &amp; Max<br>in Japan</h1>
<p>{bi("October 17–31 · Tokyo to Okinawa. Places picked for the two of you, with photos, maps and links.",
       "10月17日〜31日・東京から沖縄まで。おふたり向けに選んだ場所を、写真・地図・リンクつきでまとめました。")}</p>
</div></header>
<main class="wrap">
<section class="intro">
<h2>{bi("Your route", "ルート")}</h2>
<p>{bi("Congratulations on your wedding! I picked these with what you told me in our lessons in mind. Tap a number on the map to jump to that city.",
       "ご結婚おめでとうございます！レッスンで聞いた話をもとに選びました。地図の番号を押すと、その都市に移動します。")}</p>
<div class="chips">CHIPS</div>
NAV_HTML
<div id="route"></div>
<p class="legend">{bi("Dates for each city are yours to fill in. Everything here was open or scheduled for late October when I checked; please double-check before you go.",
                    "各都市の日付は未確定です。掲載情報は確認時点で10月下旬に営業・開催予定だったものです。行く前に念のため再確認してください。")}</p>
</section>
{"".join(sections)}
EXTRA_HTML
<footer>
<p>{bi("Made by Yuuki, your Japanese teacher.", "作成：ユウキ")}</p>
<details class="credits"><summary>{bi("Photo credits (Wikimedia Commons)", "写真クレジット（Wikimedia Commons）")}</summary>
<ul>{"".join(credits)}</ul></details>
</footer>
</main>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<script>
const tiles=()=>L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{{z}}/{{y}}/{{x}}',{{maxZoom:18,attribution:'Tiles &copy; Esri'}});
const pin=(n,c)=>L.divIcon({{className:'',html:`<div style="width:26px;height:26px;border-radius:50%;background:${{c||'#C8102E'}};color:#fff;font:700 13px/26px Inter,sans-serif;text-align:center;border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.3)">${{n}}</div>`,iconSize:[26,26],iconAnchor:[13,13]}});
const R={route_pts};
const rm=L.map('route',{{scrollWheelZoom:false}});tiles().addTo(rm);
const byK=Object.fromEntries(R.map(p=>[p[3],[p[0],p[1]]]));const line=['tokyo','sapporo','biei','tokyo','osaka','kyoto','hiroshima','nagasaki','okinawa','tokyo'].filter(k=>byK[k]).map(k=>byK[k]);
L.polyline(line,{{color:'#C8102E',weight:2,dashArray:'6 6'}}).addTo(rm);
R.forEach((p,i)=>L.marker([p[0],p[1]],{{icon:pin(i+1)}}).addTo(rm).bindTooltip(p[2]).on('click',()=>document.getElementById(p[3]).scrollIntoView({{behavior:'smooth'}})));
rm.fitBounds(line,{{padding:[20,20]}});
document.querySelectorAll('.citymap').forEach(el=>{{const P=JSON.parse(el.dataset.pts);if(!P.length){{el.remove();return}}
const m=L.map(el,{{scrollWheelZoom:false}});tiles().addTo(m);const sec=el.closest('.city');const mk={{}};P.forEach(p=>{{mk[p[2]]=L.marker([p[0],p[1]],{{icon:pin(p[2])}}).addTo(m).bindTooltip(p[3]).on('click',()=>{{const c=sec.querySelector(`.card[data-n="${{p[2]}}"]`);c.open=true;c.scrollIntoView({{behavior:'smooth',block:'center'}});c.classList.add('flash');setTimeout(()=>c.classList.remove('flash'),1200)}})}});sec.querySelectorAll('.card').forEach(c=>c.addEventListener('toggle',()=>{{const t=mk[c.dataset.n];if(c.open&&t){{t.openTooltip()}}}}));
P.length>1?m.fitBounds(P.map(p=>[p[0],p[1]]),{{padding:[30,30],maxZoom:14}}):m.setView([P[0][0],P[0][1]],13);}});
const setL=l=>{{document.documentElement.dataset.lang=l;document.querySelectorAll('.toggle button').forEach(b=>b.setAttribute('aria-pressed',b.dataset.l===l));try{{localStorage.setItem('lang',l)}}catch(e){{}}}};
document.querySelectorAll('.toggle button').forEach(b=>b.onclick=()=>setL(b.dataset.l));
try{{const s=localStorage.getItem('lang');if(s)setL(s)}}catch(e){{}}
</script>
</body></html>'''

CHIPS = [("Jujutsu Kaisen", "呪術廻戦"), ("Horror", "ホラー"), ("Soba", "そば"), ("Crab & scallops", "カニ・ホタテ"),
         ("Onsen", "温泉"), ("Hiking", "ハイキング"), ("Ice cream", "アイスクリーム")]
page = page.replace("CHIPS", "".join(f"<span>{bi(a, b)}</span>" for a, b in CHIPS))
hero = next((i["photo"]["url"] for i in items if i.get("hero") and i.get("photo")), None) \
    or next((i["photo"]["url"] for i in items if i.get("photo")), "")
page = page.replace("HERO_SRC", e(hero)).replace("EXTRA_HTML", EXTRA).replace("NAV_HTML", NAV).replace("EXTRA_CSS_HERE", EXTRA_CSS)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(page)
print(OUT, len(items), "items")
