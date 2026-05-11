#!/usr/bin/env python3
from pathlib import Path
import re
import html
import shutil

ROOT = Path(".")
COMPETITION = "Midnight Sun CTF 2026 Quals"
COMP_SLUG = "midnight-sun-ctf-2026-quals"

SRC_DIRS = [
    ROOT / "Midnight Sun CTF 2026 Quals",
    ROOT / "writeups",
]

SRC = None
for d in SRC_DIRS:
    if d.exists():
        SRC = d
        break

if SRC is None:
    raise SystemExit("No writeups folder found. Expected: writeups/ or Midnight Sun CTF 2026 Quals/")

OUT = ROOT / "c" / COMP_SLUG
PUBLIC = ROOT / "public"
PUBLIC.mkdir(exist_ok=True)

def slugify(s):
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "unknown"

def read_field(text, name):
    m = re.search(rf"^{re.escape(name)}:\s*(.*)$", text, re.M)
    return m.group(1).strip() if m else "N/A"

def section(text, title):
    pattern = rf"^## {re.escape(title)}\s*\n(.*?)(?=^## |\Z)"
    m = re.search(pattern, text, re.S | re.M)
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

def page(title, body, current=""):
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
          <img class="brand-avatar" src="/public/mylogo.gif" alt="saad avatar">
          <div class="brand-text">
            <div class="brand-name">saad</div>
            <div class="brand-subtitle">CTF Writeups</div>
          <div class="brand-socials">
            <a href="https://x.com/_z68d" target="_blank" rel="noreferrer">X: @_z68d</a>
            <span>Discord: z68d</span>
          </div>
          </div>
        </a>
        <div class="nav-links">
          <a href="/">main</a>
          <a href="/c/{COMP_SLUG}/">Midnight Sun CTF 2026 Quals</a>
          <a href="/c/{COMP_SLUG}/">Challenges</a>
          <a href="https://w4llz.me/" target="_blank" rel="noreferrer">our team</a>
        </div>
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

writeups = []

for f in sorted(SRC.glob("*.md")):
    text = f.read_text(encoding="utf-8", errors="replace")
    challenge = read_field(text, "Name")
    author = read_field(text, "Author")
    category = read_field(text, "Category")
    desc = read_field(text, "Description")
    objective = read_field(text, "Objective")
    flag_format = read_field(text, "Flag format")

    if challenge == "N/A":
        m = re.search(r"^#\s+(.+)$", text, re.M)
        challenge = m.group(1).strip() if m else f.stem

    writeups.append({
        "file": f,
        "text": text,
        "challenge": challenge,
        "challenge_slug": slugify(challenge),
        "category": category if category != "N/A" else "misc",
        "category_slug": slugify(category if category != "N/A" else "misc"),
        "author": author,
        "description": desc,
        "objective": objective,
        "flag_format": flag_format,
    })

# CSS
(PUBLIC / "writeups.css").write_text(r'''
:root {
  --background: 210 20% 4%;
  --foreground: 193 50% 65%;
  --card: 210 20% 7%;
  --card-foreground: 193 50% 65%;
  --primary: 193 66% 36%;
  --muted-foreground: 210 10% 50%;
  --accent: 200 70% 55%;
  --border: 193 30% 15%;
  --terminal-bg: 210 25% 6%;
  --terminal-border: 193 40% 20%;
  --gold: 45 100% 55%;
  --radius: .5rem;
}

* { box-sizing: border-box; }
html { font-size: 14px; scroll-behavior: smooth; }

body {
  margin: 0;
  min-height: 100vh;
  background-color: hsl(var(--background));
  font-family: "Space Grotesk", sans-serif;
  color: hsl(var(--foreground));
  line-height: 1.5;
  overflow-x: hidden;
}

body:before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background:
    radial-gradient(ellipse at top, hsl(var(--primary) / .12) 0%, transparent 58%),
    radial-gradient(ellipse at bottom right, hsl(var(--accent) / .075) 0%, transparent 52%),
    radial-gradient(ellipse at bottom left, hsl(var(--gold) / .035) 0%, transparent 48%);
}

body:after {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 1;
  background-image:
    linear-gradient(hsl(var(--primary) / .035) 1px, transparent 1px),
    linear-gradient(90deg, hsl(var(--primary) / .035) 1px, transparent 1px);
  background-size: 42px 42px;
  mask-image: linear-gradient(to bottom, black 0%, transparent 92%);
}

a { color: inherit; text-decoration: none; }

.scanlines {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 2;
  opacity: .20;
  background: linear-gradient(rgba(18,16,16,0) 50%, rgba(0,0,0,.28) 50%);
  background-size: 100% 4px;
}

.glow-orb {
  position: fixed;
  width: 420px;
  height: 420px;
  border-radius: 999px;
  pointer-events: none;
  z-index: 0;
  filter: blur(28px);
  opacity: .22;
}

.glow-orb.one {
  top: -160px;
  left: -130px;
  background: hsl(var(--primary) / .55);
}

.glow-orb.two {
  right: -140px;
  bottom: 10%;
  background: hsl(var(--accent) / .42);
}

.site-shell { position: relative; z-index: 3; }

.site-nav {
  position: sticky;
  top: 0;
  z-index: 50;
  background: hsl(var(--background) / .90);
  border-bottom: 1px solid hsl(var(--border) / .65);
  backdrop-filter: blur(18px);
}

.nav-inner {
  width: min(1200px, calc(100% - 32px));
  min-height: 74px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
}

.brand {
  display: flex;
  align-items: center;
  gap: .85rem;
}

.brand-mark {
  width: 54px;
  height: 54px;
  display: grid;
  place-items: center;
  border-radius: .85rem;
  color: hsl(var(--foreground));
  font-weight: 900;
  font-size: 1.5rem;
  background: hsl(var(--primary) / .14);
  border: 1px solid hsl(var(--primary) / .35);
  box-shadow: 0 0 24px hsl(var(--accent) / .18);
}

.brand-name {
  color: hsl(var(--foreground));
  font-size: 1.45rem;
  font-weight: 900;
  letter-spacing: -.055em;
}

.brand-subtitle {
  margin-top: .35rem;
  color: hsl(var(--muted-foreground));
  font-family: "JetBrains Mono", monospace;
  font-size: .72rem;
  letter-spacing: .12em;
  text-transform: uppercase;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: .55rem;
  color: hsl(var(--muted-foreground));
  font-family: "JetBrains Mono", monospace;
  font-size: .78rem;
}

.nav-links a {
  padding: .58rem .82rem;
  border: 1px solid transparent;
  border-radius: var(--radius);
  transition: .16s ease;
}

.nav-links a:hover {
  color: hsl(var(--foreground));
  background: hsl(var(--card) / .8);
  border-color: hsl(var(--primary) / .35);
  box-shadow: 0 0 24px hsl(var(--primary) / .13);
}

.container {
  width: min(1200px, calc(100% - 32px));
  margin: 0 auto;
  padding: 2.1rem 0 5rem;
}

.hero {
  position: relative;
  overflow: hidden;
  min-height: 360px;
  display: grid;
  align-items: center;
  margin-bottom: 2.2rem;
  padding: clamp(1.5rem, 4vw, 3rem);
  border: 1px solid hsl(var(--primary) / .2);
  border-radius: .9rem;
  background:
    linear-gradient(135deg, hsl(var(--terminal-bg) / .96), hsl(var(--card) / .88)),
    radial-gradient(ellipse at top right, hsl(var(--primary) / .16), transparent 36rem);
  box-shadow: 0 28px 80px rgb(0 0 0 / .48), inset 0 1px 0 hsl(var(--foreground) / .06);
}

.hero.compact { min-height: 230px; }

.hero-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(hsl(var(--primary) / .06) 1px, transparent 1px),
    linear-gradient(90deg, hsl(var(--primary) / .06) 1px, transparent 1px);
  background-size: 34px 34px;
  mask-image: radial-gradient(circle at center, black 0%, transparent 76%);
}

.hero-content {
  position: relative;
  z-index: 2;
  max-width: 860px;
}

.eyebrow {
  display: inline-flex;
  align-items: center;
  gap: .55rem;
  margin-bottom: .9rem;
  padding: .45rem .72rem;
  color: hsl(var(--accent));
  background: hsl(var(--primary) / .08);
  border: 1px solid hsl(var(--primary) / .3);
  border-radius: 999px;
  font-family: "JetBrains Mono", monospace;
  font-size: .72rem;
  font-weight: 800;
  letter-spacing: .1em;
  text-transform: uppercase;
}

.pulse-dot {
  width: .46rem;
  height: .46rem;
  border-radius: 999px;
  background: hsl(var(--accent));
  box-shadow: 0 0 14px hsl(var(--accent));
}

.hero h1 {
  margin: 0;
  color: hsl(var(--foreground));
  font-size: clamp(3rem, 8vw, 6.5rem);
  line-height: .88;
  font-weight: 900;
  letter-spacing: -.085em;
}

.hero.compact h1 {
  font-size: clamp(2.3rem, 5vw, 4.8rem);
}

.hero h1 span {
  color: hsl(var(--accent));
  text-shadow: 0 0 34px hsl(var(--accent) / .24);
}

.hero p {
  max-width: 760px;
  margin: 1rem 0 0;
  color: hsl(var(--muted-foreground));
  font-size: 1.04rem;
}

.terminal-line {
  width: fit-content;
  max-width: 100%;
  margin-top: 1.45rem;
  padding: .82rem .95rem;
  color: hsl(var(--foreground));
  background: hsl(var(--background) / .78);
  border: 1px solid hsl(var(--terminal-border));
  border-radius: .65rem;
  font-family: "JetBrains Mono", monospace;
  font-size: .82rem;
  overflow-wrap: anywhere;
}

.prompt {
  color: hsl(var(--gold));
  margin-right: .5rem;
}

.topbar { margin-bottom: 1.2rem; }

.topbar a {
  display: inline-flex;
  align-items: center;
  padding: .62rem .85rem;
  color: hsl(var(--accent));
  background: hsl(var(--card) / .72);
  border: 1px solid hsl(var(--primary) / .28);
  border-radius: .55rem;
  font-family: "JetBrains Mono", monospace;
  font-size: .82rem;
  font-weight: 700;
}

.section-head {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 1rem;
  margin: .45rem 0 1.2rem;
}

.section-head h2 {
  margin: 0;
  color: hsl(var(--foreground));
  font-size: 1.8rem;
  font-weight: 900;
  letter-spacing: -.045em;
}

.terminal-chip {
  padding: .55rem .7rem;
  color: hsl(var(--accent));
  background: hsl(var(--terminal-bg) / .82);
  border: 1px solid hsl(var(--terminal-border));
  border-radius: .55rem;
  font-family: "JetBrains Mono", monospace;
  font-size: .78rem;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(285px, 1fr));
  gap: 1rem;
}

.card {
  position: relative;
  overflow: hidden;
  display: block;
  padding: 1.45rem;
  color: hsl(var(--card-foreground));
  background: linear-gradient(180deg, hsl(var(--card) / .94), hsl(var(--terminal-bg) / .84));
  border: 1px solid hsl(var(--primary) / .16);
  border-radius: .8rem;
  box-shadow: 0 16px 48px rgb(0 0 0 / .25);
  transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease;
}

.card:before {
  content: "";
  position: absolute;
  inset: 0;
  opacity: 0;
  background:
    radial-gradient(circle at top right, hsl(var(--accent) / .14), transparent 14rem),
    radial-gradient(circle at bottom left, hsl(var(--gold) / .08), transparent 12rem);
  transition: opacity .18s ease;
}

.card:hover {
  transform: translateY(-4px);
  border-color: hsl(var(--primary) / .42);
  box-shadow: 0 22px 70px rgb(0 0 0 / .36), 0 0 34px hsl(var(--primary) / .13);
}

.card:hover:before { opacity: 1; }

.card > * {
  position: relative;
  z-index: 1;
}

.card-kicker {
  margin-bottom: .55rem;
  color: hsl(var(--accent));
  font-family: "JetBrains Mono", monospace;
  font-size: .72rem;
  font-weight: 800;
  letter-spacing: .1em;
  text-transform: uppercase;
}

.card-title {
  margin-bottom: .55rem;
  color: hsl(var(--foreground));
  font-size: 1.22rem;
  font-weight: 900;
  line-height: 1.22;
  letter-spacing: -.035em;
}

.card-meta {
  color: hsl(var(--muted-foreground));
  font-family: "JetBrains Mono", monospace;
  font-size: .82rem;
}

.challenge-card { min-height: 170px; }

.writeup-page {
  display: grid;
  gap: 1.15rem;
}

.writeup-card {
  padding: 1.55rem;
  color: hsl(var(--card-foreground));
  background: linear-gradient(180deg, hsl(var(--card) / .94), hsl(var(--terminal-bg) / .84));
  border: 1px solid hsl(var(--primary) / .2);
  border-radius: .8rem;
  box-shadow: 0 16px 48px rgb(0 0 0 / .25);
}

.overview-grid {
  display: grid;
  gap: .55rem;
  padding: 1rem;
  color: hsl(var(--foreground));
  background: hsl(var(--background) / .88);
  border: 1px solid hsl(var(--terminal-border));
  border-radius: .75rem;
  font-family: "JetBrains Mono", monospace;
  font-size: .86rem;
}

.overview-grid span {
  color: hsl(var(--accent));
  font-weight: 900;
}

.prose {
  color: hsl(var(--foreground));
}

.prose h1,
.prose h2,
.prose h3 {
  color: hsl(var(--accent));
  letter-spacing: -.035em;
}

.prose h1 { font-size: 2.2rem; }
.prose h2 {
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid hsl(var(--primary) / .20);
}

.prose p,
.prose li {
  color: hsl(var(--card-foreground));
}

.prose code {
  color: hsl(var(--gold));
  background: hsl(var(--background) / .88);
  border: 1px solid hsl(var(--terminal-border));
  border-radius: .35rem;
  padding: .08rem .3rem;
  font-family: "JetBrains Mono", monospace;
}

pre {
  white-space: pre-wrap;
  word-break: break-word;
  margin: 1rem 0;
  padding: 1rem;
  color: hsl(var(--foreground));
  background: hsl(var(--background) / .88);
  border: 1px solid hsl(var(--terminal-border));
  border-radius: .75rem;
  overflow-x: auto;
  font-family: "JetBrains Mono", monospace;
  font-size: .85rem;
}

@media (max-width: 720px) {
  .nav-inner {
    min-height: auto;
    padding: 1rem 0;
    align-items: flex-start;
    flex-direction: column;
  }

  .nav-links { flex-wrap: wrap; }
  .hero { min-height: auto; padding: 1.7rem; }
  .section-head { align-items: flex-start; flex-direction: column; }
  .grid { grid-template-columns: 1fr; }
}
''', encoding="utf-8")

# Home
home_cards = card(
    f"/c/{COMP_SLUG}/",
    "competition",
    COMPETITION,
    f"{len(writeups)} write-ups · generated static archive"
)

home = f"""
<section class="hero">
  <div class="hero-grid"></div>
  <div class="hero-content">
    <div class="eyebrow"><span class="pulse-dot"></span> published writeups</div>
    <h1><span>saad</span><br>Archive</h1>
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
(ROOT / "index.html").write_text(page("Home", home), encoding="utf-8")

# Competition
OUT.mkdir(parents=True, exist_ok=True)

cats = {}
for w in writeups:
    cats.setdefault(w["category_slug"], {"name": w["category"], "items": []})["items"].append(w)

cat_cards = "\n".join(
    card(
        f"/c/{COMP_SLUG}/cat/{cat_slug}/",
        "category",
        data["name"],
        f'{len(data["items"])} challenge(s) · {len(data["items"])} write-up(s)'
    )
    for cat_slug, data in sorted(cats.items(), key=lambda x: x[1]["name"].lower())
)

competition_page = f"""
<div class="topbar"><a href="/">← main</a></div>
<section class="hero compact">
  <div class="hero-grid"></div>
  <div class="hero-content">
    <div class="eyebrow"><span class="pulse-dot"></span> Midnight Sun CTF 2026 Quals</div>
    <h1>{html.escape(COMPETITION)}</h1>
    <p>{len(cats)} categories · {len(writeups)} write-ups</p>
  </div>
</section>

<div class="section-head">
  <div><h2>Categories</h2></div>
  <div class="terminal-chip">ls categories/</div>
</div>

<div class="grid">
  {cat_cards}
</div>
"""
(OUT / "index.html").write_text(page(COMPETITION, competition_page), encoding="utf-8")


# Challenge pages without category layer
challenge_cards = "\n".join(
    card(
        f"/c/{COMP_SLUG}/ch/{w['challenge_slug']}/",
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
    <div class="eyebrow"><span class="pulse-dot"></span> Midnight Sun CTF 2026 Quals</div>
    <h1>{html.escape(COMPETITION)}</h1>
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
(OUT / "index.html").write_text(page(COMPETITION, competition_page), encoding="utf-8")

for w in writeups:
    ch_dir = OUT / "ch" / w["challenge_slug"]
    ch_dir.mkdir(parents=True, exist_ok=True)

    overview = f"""
<div class="overview-grid">
  <div><span>Name:</span> {html.escape(w["challenge"])}</div>
  <div><span>Author:</span> {html.escape(w["author"])}</div>
  <div><span>Flag format:</span> {html.escape(w["flag_format"])}</div>
  <div><span>Objective:</span> {html.escape(w["objective"])}</div>
</div>
"""

    clean_text = re.sub(
        r'^Category:\s*.*$',
        '',
        w["text"],
        flags=re.I | re.M
    )
    writeup_html = md_to_html(clean_text)

    ch_page = f"""
<div class="topbar"><a href="/c/{COMP_SLUG}/">← Midnight Sun CTF 2026 Quals</a></div>
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
    (ch_dir / "index.html").write_text(page(w["challenge"], ch_page), encoding="utf-8")

print(f"[+] Built {len(writeups)} writeups without category layer")
print("[+] Home: index.html")
print(f"[+] Competition: c/{COMP_SLUG}/index.html")
