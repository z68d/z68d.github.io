#!/usr/bin/env python3
from pathlib import Path
import json
import re
import html
import shutil

ROOT = Path(".")
PUBLIC = ROOT / "public"
PUBLIC.mkdir(exist_ok=True)
COMPETITIONS_FILE = ROOT / "competitions.json"
DEFAULT_COMPETITION = {
    "name": "Midnight Sun CTF 2026 Quals",
    "slug": "midnight-sun-ctf-2026-quals",
    "dir": "Midnight Sun CTF 2026 Quals",
}

CSS_CONTENT = '\n:root {\n  --background: 210 20% 4%;\n  --foreground: 193 50% 65%;\n  --card: 210 20% 7%;\n  --card-foreground: 193 50% 65%;\n  --primary: 193 66% 36%;\n  --muted-foreground: 210 10% 50%;\n  --accent: 200 70% 55%;\n  --border: 193 30% 15%;\n  --terminal-bg: 210 25% 6%;\n  --terminal-border: 193 40% 20%;\n  --gold: 45 100% 55%;\n  --radius: .5rem;\n}\n\n* { box-sizing: border-box; }\nhtml { font-size: 14px; scroll-behavior: smooth; }\n\nbody {\n  margin: 0;\n  min-height: 100vh;\n  background-color: hsl(var(--background));\n  font-family: "Space Grotesk", sans-serif;\n  color: hsl(var(--foreground));\n  line-height: 1.5;\n  overflow-x: hidden;\n}\n\nbody:before {\n  content: "";\n  position: fixed;\n  inset: 0;\n  pointer-events: none;\n  z-index: 0;\n  background:\n    radial-gradient(ellipse at top, hsl(var(--primary) / .12) 0%, transparent 58%),\n    radial-gradient(ellipse at bottom right, hsl(var(--accent) / .075) 0%, transparent 52%),\n    radial-gradient(ellipse at bottom left, hsl(var(--gold) / .035) 0%, transparent 48%);\n}\n\nbody:after {\n  content: "";\n  position: fixed;\n  inset: 0;\n  pointer-events: none;\n  z-index: 1;\n  background-image:\n    linear-gradient(hsl(var(--primary) / .035) 1px, transparent 1px),\n    linear-gradient(90deg, hsl(var(--primary) / .035) 1px, transparent 1px);\n  background-size: 42px 42px;\n  mask-image: linear-gradient(to bottom, black 0%, transparent 92%);\n}\n\na { color: inherit; text-decoration: none; }\n\n.scanlines {\n  position: fixed;\n  inset: 0;\n  pointer-events: none;\n  z-index: 2;\n  opacity: .20;\n  background: linear-gradient(rgba(18,16,16,0) 50%, rgba(0,0,0,.28) 50%);\n  background-size: 100% 4px;\n}\n\n.glow-orb {\n  position: fixed;\n  width: 420px;\n  height: 420px;\n  border-radius: 999px;\n  pointer-events: none;\n  z-index: 0;\n  filter: blur(28px);\n  opacity: .22;\n}\n\n.glow-orb.one {\n  top: -160px;\n  left: -130px;\n  background: hsl(var(--primary) / .55);\n}\n\n.glow-orb.two {\n  right: -140px;\n  bottom: 10%;\n  background: hsl(var(--accent) / .42);\n}\n\n.site-shell { position: relative; z-index: 3; }\n\n.site-nav {\n  position: sticky;\n  top: 0;\n  z-index: 50;\n  background: hsl(var(--background) / .90);\n  border-bottom: 1px solid hsl(var(--border) / .65);\n  backdrop-filter: blur(18px);\n}\n\n.nav-inner {\n  width: min(1200px, calc(100% - 38px));\n  min-height: 74px;\n  margin: 0 auto;\n  display: flex;\n  align-items: center;\n  justify-content: space-between;\n  gap: 1.5rem;\n}\n\n.brand {\n  display: flex;\n  align-items: center;\n  gap: .85rem;\n}\n\n.brand-mark {\n  width: 54px;\n  height: 54px;\n  display: grid;\n  place-items: center;\n  border-radius: .85rem;\n  color: hsl(var(--foreground));\n  font-weight: 900;\n  font-size: 1.5rem;\n  background: hsl(var(--primary) / .14);\n  border: 1px solid hsl(var(--primary) / .35);\n  box-shadow: 0 0 24px hsl(var(--accent) / .18);\n}\n\n.brand-name {\n  color: hsl(var(--foreground));\n  font-size: 1.45rem;\n  font-weight: 900;\n  letter-spacing: -.055em;\n}\n\n.brand-subtitle {\n  margin-top: .35rem;\n  color: hsl(var(--muted-foreground));\n  font-family: "JetBrains Mono", monospace;\n  font-size: .72rem;\n  letter-spacing: .12em;\n  text-transform: uppercase;\n}\n\n.nav-links {\n  display: flex;\n  align-items: center;\n  gap: .55rem;\n  color: hsl(var(--muted-foreground));\n  font-family: "JetBrains Mono", monospace;\n  font-size: .78rem;\n}\n\n.nav-links a {\n  padding: .58rem .82rem;\n  border: 1px solid transparent;\n  border-radius: var(--radius);\n  transition: .16s ease;\n}\n\n.nav-links a:hover {\n  color: hsl(var(--foreground));\n  background: hsl(var(--card) / .8);\n  border-color: hsl(var(--primary) / .35);\n  box-shadow: 0 0 24px hsl(var(--primary) / .13);\n}\n\n.container {\n  width: min(1200px, calc(100% - 38px));\n  margin: 0 auto;\n  padding: 2.1rem 0 5rem;\n}\n\n.hero {\n  position: relative;\n  overflow: hidden;\n  min-height: 360px;\n  display: grid;\n  align-items: center;\n  margin-bottom: 2.2rem;\n  padding: clamp(1.5rem, 4vw, 3rem);\n  border: 1px solid hsl(var(--primary) / .2);\n  border-radius: .9rem;\n  background:\n    linear-gradient(135deg, hsl(var(--terminal-bg) / .96), hsl(var(--card) / .88)),\n    radial-gradient(ellipse at top right, hsl(var(--primary) / .16), transparent 36rem);\n  box-shadow: 0 28px 80px rgb(0 0 0 / .48), inset 0 1px 0 hsl(var(--foreground) / .06);\n}\n\n.hero.compact { min-height: 230px; }\n\n.hero-grid {\n  position: absolute;\n  inset: 0;\n  background-image:\n    linear-gradient(hsl(var(--primary) / .06) 1px, transparent 1px),\n    linear-gradient(90deg, hsl(var(--primary) / .06) 1px, transparent 1px);\n  background-size: 34px 34px;\n  mask-image: radial-gradient(circle at center, black 0%, transparent 76%);\n}\n\n.hero-content {\n  position: relative;\n  z-index: 2;\n  max-width: 860px;\n}\n\n.eyebrow {\n  display: inline-flex;\n  align-items: center;\n  gap: .55rem;\n  margin-bottom: .9rem;\n  padding: .45rem .72rem;\n  color: hsl(var(--accent));\n  background: hsl(var(--primary) / .08);\n  border: 1px solid hsl(var(--primary) / .3);\n  border-radius: 999px;\n  font-family: "JetBrains Mono", monospace;\n  font-size: .72rem;\n  font-weight: 800;\n  letter-spacing: .1em;\n  text-transform: uppercase;\n}\n\n.pulse-dot {\n  width: .46rem;\n  height: .46rem;\n  border-radius: 999px;\n  background: hsl(var(--accent));\n  box-shadow: 0 0 14px hsl(var(--accent));\n}\n\n.hero h1 {\n  margin: 0;\n  color: hsl(var(--foreground));\n  font-size: clamp(3rem, 8vw, 6.5rem);\n  line-height: .88;\n  font-weight: 900;\n  letter-spacing: -.085em;\n}\n\n.hero.compact h1 {\n  font-size: clamp(2.3rem, 5vw, 4.8rem);\n}\n\n.hero h1 span {\n  color: hsl(var(--accent));\n  text-shadow: 0 0 34px hsl(var(--accent) / .24);\n}\n\n.hero p {\n  max-width: 760px;\n  margin: 1rem 0 0;\n  color: hsl(var(--muted-foreground));\n  font-size: 1.04rem;\n}\n\n.terminal-line {\n  width: fit-content;\n  max-width: 100%;\n  margin-top: 1.45rem;\n  padding: .82rem .95rem;\n  color: hsl(var(--foreground));\n  background: hsl(var(--background) / .78);\n  border: 1px solid hsl(var(--terminal-border));\n  border-radius: .65rem;\n  font-family: "JetBrains Mono", monospace;\n  font-size: .82rem;\n  overflow-wrap: anywhere;\n}\n\n.prompt {\n  color: hsl(var(--gold));\n  margin-right: .5rem;\n}\n\n.topbar { margin-bottom: 1.2rem; }\n\n.topbar a {\n  display: inline-flex;\n  align-items: center;\n  padding: .62rem .85rem;\n  color: hsl(var(--accent));\n  background: hsl(var(--card) / .72);\n  border: 1px solid hsl(var(--primary) / .28);\n  border-radius: .55rem;\n  font-family: "JetBrains Mono", monospace;\n  font-size: .82rem;\n  font-weight: 700;\n}\n\n.section-head {\n  display: flex;\n  align-items: end;\n  justify-content: space-between;\n  gap: 1rem;\n  margin: .45rem 0 1.2rem;\n}\n\n.section-head h2 {\n  margin: 0;\n  color: hsl(var(--foreground));\n  font-size: 1.8rem;\n  font-weight: 900;\n  letter-spacing: -.045em;\n}\n\n.terminal-chip {\n  padding: .55rem .7rem;\n  color: hsl(var(--accent));\n  background: hsl(var(--terminal-bg) / .82);\n  border: 1px solid hsl(var(--terminal-border));\n  border-radius: .55rem;\n  font-family: "JetBrains Mono", monospace;\n  font-size: .78rem;\n}\n\n.grid {\n  display: grid;\n  grid-template-columns: repeat(auto-fill, minmax(285px, 1fr));\n  gap: 1rem;\n}\n\n.card {\n  position: relative;\n  overflow: hidden;\n  display: block;\n  padding: 1.45rem;\n  color: hsl(var(--card-foreground));\n  background: linear-gradient(180deg, hsl(var(--card) / .94), hsl(var(--terminal-bg) / .84));\n  border: 1px solid hsl(var(--primary) / .16);\n  border-radius: .8rem;\n  box-shadow: 0 16px 48px rgb(0 0 0 / .25);\n  transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease;\n}\n\n.card:before {\n  content: "";\n  position: absolute;\n  inset: 0;\n  opacity: 0;\n  background:\n    radial-gradient(circle at top right, hsl(var(--accent) / .14), transparent 14rem),\n    radial-gradient(circle at bottom left, hsl(var(--gold) / .08), transparent 12rem);\n  transition: opacity .18s ease;\n}\n\n.card:hover {\n  transform: translateY(-4px);\n  border-color: hsl(var(--primary) / .42);\n  box-shadow: 0 22px 70px rgb(0 0 0 / .36), 0 0 34px hsl(var(--primary) / .13);\n}\n\n.card:hover:before { opacity: 1; }\n\n.card > * {\n  position: relative;\n  z-index: 1;\n}\n\n.card-kicker {\n  margin-bottom: .55rem;\n  color: hsl(var(--accent));\n  font-family: "JetBrains Mono", monospace;\n  font-size: .72rem;\n  font-weight: 800;\n  letter-spacing: .1em;\n  text-transform: uppercase;\n}\n\n.card-title {\n  margin-bottom: .55rem;\n  color: hsl(var(--foreground));\n  font-size: 1.22rem;\n  font-weight: 900;\n  line-height: 1.22;\n  letter-spacing: -.035em;\n}\n\n.card-meta {\n  color: hsl(var(--muted-foreground));\n  font-family: "JetBrains Mono", monospace;\n  font-size: .82rem;\n}\n\n.challenge-card { min-height: 170px; }\n\n.writeup-page {\n  display: grid;\n  gap: 1.15rem;\n}\n\n.writeup-card {\n  padding: 1.55rem;\n  color: hsl(var(--card-foreground));\n  background: linear-gradient(180deg, hsl(var(--card) / .94), hsl(var(--terminal-bg) / .84));\n  border: 1px solid hsl(var(--primary) / .2);\n  border-radius: .8rem;\n  box-shadow: 0 16px 48px rgb(0 0 0 / .25);\n}\n\n.overview-grid {\n  display: grid;\n  gap: .55rem;\n  padding: 1rem;\n  color: hsl(var(--foreground));\n  background: hsl(var(--background) / .88);\n  border: 1px solid hsl(var(--terminal-border));\n  border-radius: .75rem;\n  font-family: "JetBrains Mono", monospace;\n  font-size: .86rem;\n}\n\n.overview-grid span {\n  color: hsl(var(--accent));\n  font-weight: 900;\n}\n\n.prose {\n  color: hsl(var(--foreground));\n}\n\n.prose h1,\n.prose h2,\n.prose h3 {\n  color: hsl(var(--accent));\n  letter-spacing: -.035em;\n}\n\n.prose h1 { font-size: 2.2rem; }\n.prose h2 {\n  margin-top: 2rem;\n  padding-top: 1rem;\n  border-top: 1px solid hsl(var(--primary) / .20);\n}\n\n.prose p,\n.prose li {\n  color: hsl(var(--card-foreground));\n}\n\n.prose code {\n  color: hsl(var(--gold));\n  background: hsl(var(--background) / .88);\n  border: 1px solid hsl(var(--terminal-border));\n  border-radius: .35rem;\n  padding: .08rem .3rem;\n  font-family: "JetBrains Mono", monospace;\n}\n\npre {\n  white-space: pre-wrap;\n  word-break: break-word;\n  margin: 1rem 0;\n  padding: 1rem;\n  color: hsl(var(--foreground));\n  background: hsl(var(--background) / .88);\n  border: 1px solid hsl(var(--terminal-border));\n  border-radius: .75rem;\n  overflow-x: auto;\n  font-family: "JetBrains Mono", monospace;\n  font-size: .85rem;\n}\n\n@media (max-width: 720px) {\n  .nav-inner {\n    min-height: auto;\n    padding: 1rem 0;\n    align-items: flex-start;\n    flex-direction: column;\n  }\n\n  .nav-links { flex-wrap: wrap; }\n  .hero { min-height: auto; padding: 1.7rem; }\n  .section-head { align-items: flex-start; flex-direction: column; }\n  .grid { grid-template-columns: 1fr; }\n}\n'


def slugify(s):
    s = str(s).strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "unknown"


def load_competitions():
    if not COMPETITIONS_FILE.exists():
        COMPETITIONS_FILE.write_text(json.dumps([DEFAULT_COMPETITION], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    data = json.loads(COMPETITIONS_FILE.read_text(encoding="utf-8"))
    competitions = []
    seen = set()
    for item in data:
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        slug = slugify(item.get("slug") or name)
        directory = str(item.get("dir") or name).strip() or name
        if slug in seen:
            continue
        seen.add(slug)
        competitions.append({"name": name, "slug": slug, "dir": directory})

    if not competitions:
        competitions = [DEFAULT_COMPETITION]

    return competitions


def save_competitions(competitions):
    COMPETITIONS_FILE.write_text(json.dumps(competitions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_field(text, name):
    m = re.search(rf"^{re.escape(name)}:\s*(.*)$", text, re.M)
    return m.group(1).strip() if m else "N/A"


def md_to_html(md):
    lines = md.splitlines()
    out = []
    in_code = False
    code_lang = ""
    code_buf = []
    in_ul = False

    def close_ul():
        nonlocal in_ul
        if in_ul:
            out.append("</ul>")
            in_ul = False

    def close_code():
        nonlocal in_code, code_buf, code_lang
        code = html.escape("\n".join(code_buf))
        out.append(f'<pre><code class="language-{html.escape(code_lang)}">{code}</code></pre>')
        in_code = False
        code_lang = ""
        code_buf = []

    for line in lines:
        if line.startswith("```"):
            if in_code:
                close_code()
            else:
                close_ul()
                in_code = True
                code_lang = line.strip("`").strip()
                code_buf = []
            continue

        if in_code:
            code_buf.append(line)
            continue

        if line.startswith("# "):
            close_ul()
            out.append(f"<h1>{html.escape(line[2:].strip())}</h1>")
        elif line.startswith("## "):
            close_ul()
            out.append(f"<h2>{html.escape(line[3:].strip())}</h2>")
        elif line.startswith("### "):
            close_ul()
            out.append(f"<h3>{html.escape(line[4:].strip())}</h3>")
        elif re.match(r"^\s*[-*]\s+", line):
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            item = re.sub(r"^\s*[-*]\s+", "", line)
            out.append(f"<li>{html.escape(item)}</li>")
        elif line.strip() == "":
            close_ul()
        else:
            close_ul()
            safe = html.escape(line)
            safe = re.sub(r"`([^`]+)`", r"<code>\1</code>", safe)
            safe = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", safe)
            out.append(f"<p>{safe}</p>")

    close_ul()
    if in_code:
        close_code()
    return "\n".join(out)


def nav_html(current_comp=None):
    comp = current_comp or DEFAULT_COMPETITION
    comp_name = comp["name"]
    comp_slug = comp["slug"]
    return f"""
        <div class="nav-links">
          <a href="/">main</a>
          <a href="/{html.escape(comp_slug)}/">{html.escape(comp_name)}</a>
          <a href="/{html.escape(comp_slug)}/">Challenges</a>
          <a href="https://w4llz.me/" target="_blank" rel="noreferrer">our team</a>
        </div>"""


def page(title, body, current_comp=None):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(title)} | saad Writeups</title>
  <link rel="stylesheet" href="/public/writeups.css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700;900&family=Space+Grotesk:wght@400;700;900&display=swap" rel="stylesheet">
</head>
<body>
  <div class="scanlines"></div>
  <div class="glow-orb one"></div>
  <div class="glow-orb two"></div>

  <div class="site-shell">
    <nav class="site-nav">
      <div class="nav-inner">
        <a class="brand" href="/">
          <img class="brand-avatar" src="/public/mylogo.gif" alt="saad avatar" width="38" height="38" style="width:38px!important;height:38px!important;min-width:38px!important;max-width:38px!important;min-height:38px!important;max-height:38px!important;object-fit:cover!important;display:block!important;flex:0 0 38px!important;">
          <div class="brand-text">
            <div class="brand-name">saad</div>
            <div class="brand-subtitle">CTF Writeups</div>
          <div class="brand-socials" style="display:block!important;line-height:1.05!important;margin-top:4px!important;">
            <a class="social-link" style="display:block!important;width:max-content!important;white-space:nowrap!important;line-height:1.05!important;text-decoration:none!important;" href="https://x.com/_z68d" target="_blank" rel="noreferrer">x : @_z68d</a>
            <span class="social-link" style="display:block!important;width:max-content!important;white-space:nowrap!important;line-height:1.05!important;">discord : z68d</span>
          </div>
          </div>
        </a>
{nav_html(current_comp)}
      </div>
    </nav>

    <main class="container">
      {body}
    </main>
  </div>
</body>
</html>
"""


def card(href, kicker, title, meta="", image=None):
    img = f'<img class="challenge-image" src="{html.escape(image)}" alt="challenge image">' if image else ""
    return f"""<a class="card challenge-card" href="{html.escape(href)}">
  {img}
  <div class="card-kicker">{html.escape(kicker)}</div>
  <div class="card-title">{html.escape(title)}</div>
  <div class="card-meta">{html.escape(meta)}</div>
</a>"""


def collect_writeups(comp):
    src = ROOT / comp["dir"]
    src.mkdir(parents=True, exist_ok=True)
    writeups = []

    for f in sorted(src.glob("*.md")):
        text = f.read_text(encoding="utf-8", errors="replace")
        challenge = read_field(text, "Name")
        author = read_field(text, "Author")
        category = read_field(text, "Category")
        desc = read_field(text, "Description")
        objective = read_field(text, "Objective")
        flag_format = read_field(text, "Flag format")

        if challenge == "N/A":
            m = re.search(r"^#\s+(.+)$", text, re.M)
            challenge = m.group(1).strip() if m else f.stem.replace("_writeup", "")

        writeups.append({
            "file": f,
            "text": text,
            "challenge": challenge,
            "challenge_slug": slugify(challenge),
            "category": category if category != "N/A" else "misc",
            "author": author,
            "description": desc,
            "objective": objective,
            "flag_format": flag_format,
        })

    return writeups


def build_competition(comp, writeups):
    out = ROOT / comp["slug"]
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    challenge_cards = "\n".join(
        card(
            f"/{comp['slug']}/ch/{w['challenge_slug']}/index.html",
            "challenge",
            w["challenge"],
            w["description"] if w["description"] != "N/A" else f"Author: {w['author']}"
        )
        for w in sorted(writeups, key=lambda x: x["challenge"].lower())
    )

    competition_page = f"""
<div class="topbar"><a href="/">← main</a></div>
<section class="hero compact">
  <div class="hero-grid"></div>
  <div class="hero-content">
    <div class="eyebrow"><span class="pulse-dot"></span> {html.escape(comp['name'])}</div>
    <h1>{html.escape(comp['name'])}</h1>
    <p>{len(writeups)} write-ups</p>
  </div>
</section>

<div class="section-head">
  <div><h2>Challenges</h2></div>
  <div class="terminal-chip">ls challenges/</div>
</div>

<div class="grid">
  {challenge_cards}
</div>
"""
    (out / "index.html").write_text(page(comp["name"], competition_page, comp), encoding="utf-8")

    for w in writeups:
        ch_dir = out / "ch" / w["challenge_slug"]
        ch_dir.mkdir(parents=True, exist_ok=True)

        overview = f"""
<div class="overview-grid">
  <div><span>Name:</span> {html.escape(w["challenge"])}</div>
  <div><span>Author:</span> {html.escape(w["author"])}</div>
  <div><span>Flag format:</span> {html.escape(w["flag_format"])}</div>
  <div><span>Objective:</span> {html.escape(w["objective"])}</div>
</div>
"""

        clean_text = re.sub(r'^Category:\s*.*$', '', w["text"], flags=re.I | re.M)
        writeup_html = md_to_html(clean_text)

        ch_page = f"""
<div class="topbar"><a href="/{comp['slug']}/">← {html.escape(comp['name'])}</a></div>
<section class="hero compact">
  <div class="hero-grid"></div>
  <div class="hero-content">
    <div class="eyebrow"><span class="pulse-dot"></span> writeup</div>
    <h1>{html.escape(w["challenge"])}</h1>
    <p>{html.escape(w["description"])}</p>
  </div>
</section>

<div class="writeup-page">
  <div class="writeup-card">
    {overview}
  </div>

  <article class="writeup-card prose">
    {writeup_html}
  </article>
</div>
"""
        (ch_dir / "index.html").write_text(page(w["challenge"], ch_page, comp), encoding="utf-8")


def build_home(competitions, counts):
    home_cards = "\n".join(
        card(
            f"/{comp['slug']}/",
            "competition",
            comp["name"],
            f"{counts.get(comp['slug'], 0)} write-ups · generated static archive"
        )
        for comp in competitions
    )

    home = f"""
<section class="hero">
  <div class="hero-grid"></div>
  <div class="hero-content">
    <div class="eyebrow"><span class="pulse-dot"></span> published writeups</div>
    <h1><span>SAAD</span><br>Write-ups</h1>
    <p>Clean CTF writeups with competition, category, challenge, and full writeup pages.</p>
    <div class="terminal-line"><span class="prompt">$</span><span>cat published_writeups.txt</span></div>
  </div>
</section>

<div class="section-head">
  <div>
    <h2>Competitions</h2>
  </div>
  <div class="terminal-chip">./writeups --competitions</div>
</div>

<div class="grid">
  {home_cards}
</div>
"""
    (ROOT / "index.html").write_text(page("Home", home, competitions[0] if competitions else DEFAULT_COMPETITION), encoding="utf-8")


def main():
    competitions = load_competitions()
    (PUBLIC / "writeups.css").write_text(CSS_CONTENT, encoding="utf-8")

    counts = {}
    total = 0
    for comp in competitions:
        writeups = collect_writeups(comp)
        counts[comp["slug"]] = len(writeups)
        total += len(writeups)
        build_competition(comp, writeups)

    build_home(competitions, counts)
    print(f"[+] Built {total} writeups across {len(competitions)} competition(s)")
    print("[+] Home: index.html")
    for comp in competitions:
        print(f"[+] Competition: {comp['slug']}/index.html")


if __name__ == "__main__":
    main()
