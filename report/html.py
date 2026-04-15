"""
report/html.py
--------------
Builds the self-contained HTML report from structured scan data.
No external dependencies — pure Python string building.
"""

import platform
import sys


def _esc(s: str) -> str:
    """Escape HTML special characters."""
    return str(s).replace("&", "&amp;").replace("<", "&lt;") \
                 .replace(">", "&gt;").replace('"', "&quot;")


# Badge HTML + row CSS class for each status type
BADGES = {
    "ok":        ('<span class="badge ok">OK</span>',       "row-ok"),
    "warn":      ('<span class="badge warn">WARN</span>',   "row-warn"),
    "miss":      ('<span class="badge miss">MISS</span>',   "row-miss"),
    "info":      ('<span class="badge info">INFO</span>',   "row-info"),
    "risk_high": ('<span class="badge rhigh">HIGH</span>',  "row-rhigh"),
    "risk_med":  ('<span class="badge rmed">MED</span>',    "row-rmed"),
    "risk_low":  ('<span class="badge rlow">LOW</span>',    "row-rlow"),
    "risk_info": ('<span class="badge rinfo">INFO</span>',  "row-rinfo"),
}


def _render_item(item: dict, depth: int = 0) -> str:
    """Render one item (and its children) as HTML rows."""
    status   = item.get("status", "info")
    badge, row_cls = BADGES.get(status, BADGES["info"])
    label    = _esc(item.get("label", ""))
    detail   = _esc(item.get("detail", ""))
    children = item.get("children", [])
    padding  = 16 + depth * 20

    html = f'<div class="row {row_cls}" style="padding-left:{padding}px">'
    html += f'{badge} <span class="rl">{label}</span>'
    if detail:
        html += f' <span class="rd">{detail}</span>'
    html += '</div>'

    for child in children:
        html += _render_item(child, depth + 1)

    return html


def _render_scan_card(result: dict) -> tuple[str, str]:
    """
    Render one scan section as an HTML card.
    Returns (nav_link_html, card_html).
    """
    title  = result["title"]
    anchor = title.lower().replace(" ", "_").replace("/", "_") \
                          .replace("(", "").replace(")", "")
    items  = result.get("items", [])

    ok_n   = sum(1 for i in items if i["status"] == "ok")
    warn_n = sum(1 for i in items if i["status"] == "warn")
    miss_n = sum(1 for i in items if i["status"] == "miss")

    nav = f'<a href="#{anchor}" class="nl">{_esc(title)}</a>\n'

    body = "".join(_render_item(i) for i in items)

    card = f'''
<div class="card" id="{anchor}">
  <div class="ch">
    <h2 class="ct">{_esc(title)}</h2>
    <div class="cs">
      <span class="st so">{ok_n} found</span>
      <span class="st sw">{warn_n} warn</span>
      <span class="st sm">{miss_n} missing</span>
    </div>
  </div>
  <div class="cb">{body}</div>
</div>'''

    return nav, card


def _render_permissions_card(permissions: dict) -> tuple[str, str]:
    """Render the permissions audit as an HTML card."""
    nav = '<a href="#permissions_audit" class="nl">Permissions Audit</a>\n'

    body = ""
    for section in permissions.get("sections", []):
        body += f'<div class="subt">{_esc(section.get("subtitle", ""))}</div>'
        for item in section.get("items", []):
            body += _render_item(item)

    card = f'''
<div class="card" id="permissions_audit">
  <div class="ch">
    <h2 class="ct">Permissions Audit</h2>
    <div class="rl2">
      <span class="badge rhigh">HIGH</span> serious &nbsp;
      <span class="badge rmed">MED</span> moderate &nbsp;
      <span class="badge rlow">LOW</span> low risk &nbsp;
      <span class="badge rinfo">INFO</span>
    </div>
  </div>
  <div class="cb">{body}</div>
</div>'''

    return nav, card


CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --bg:#f4f4f2; --surf:#fff; --bdr:rgba(0,0,0,.08);
  --txt:#18181a; --muted:#6b6b68;
  --ok:#16753e;  --okb:#e4f2eb;
  --wn:#8a5700;  --wnb:#fef2c7;
  --ms:#b91c1c;  --msb:#fde8e8;
  --inf:#1a5fa8; --infb:#e7f0fb;
  --hi:#b91c1c;  --hib:#fde8e8;
  --md:#8a5700;  --mdb:#fef2c7;
  --lo:#16753e;  --lob:#e4f2eb;
  --r:10px;
  --f:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  --mono:"SF Mono","Fira Code",monospace;
}
body { font-family:var(--f); background:var(--bg); color:var(--txt);
       font-size:14px; line-height:1.6; }
.topbar { position:sticky; top:0; z-index:100; background:var(--surf);
  border-bottom:1px solid var(--bdr); padding:0 20px;
  display:flex; align-items:center; gap:12px; height:50px;
  overflow-x:auto; white-space:nowrap; }
.tb-title { font-size:15px; font-weight:600; flex-shrink:0; margin-right:8px; }
.nl { color:var(--muted); text-decoration:none; font-size:13px;
  padding:3px 9px; border-radius:6px; flex-shrink:0; }
.nl:hover { background:var(--bg); color:var(--txt); }
.page { max-width:900px; margin:0 auto; padding:24px 16px 60px; }
.hero { background:var(--surf); border:1px solid var(--bdr);
  border-radius:var(--r); padding:20px 24px; margin-bottom:20px;
  display:flex; align-items:center; gap:14px; flex-wrap:wrap; }
.hero h1 { font-size:21px; font-weight:600; }
.hero-meta { font-size:13px; color:var(--muted); margin-top:2px; }
.card { background:var(--surf); border:1px solid var(--bdr);
  border-radius:var(--r); margin-bottom:18px; overflow:hidden; }
.ch { padding:14px 18px; border-bottom:1px solid var(--bdr);
  display:flex; align-items:center; justify-content:space-between;
  flex-wrap:wrap; gap:8px; }
.ct { font-size:15px; font-weight:600; }
.cs { display:flex; gap:7px; }
.st { font-size:12px; font-weight:500; padding:2px 8px; border-radius:20px; }
.so { background:var(--okb); color:var(--ok); }
.sw { background:var(--wnb); color:var(--wn); }
.sm { background:var(--msb); color:var(--ms); }
.cb { padding:6px 0; }
.row { display:flex; align-items:baseline; gap:10px; padding:6px 18px;
  border-bottom:1px solid var(--bdr); transition:background .1s; }
.row:last-child { border-bottom:none; }
.row:hover { background:var(--bg); }
.row-ok    { border-left:3px solid var(--ok);  }
.row-warn  { border-left:3px solid var(--wn);  }
.row-miss  { border-left:3px solid var(--ms);  }
.row-info  { border-left:3px solid var(--inf); }
.row-rhigh { border-left:3px solid var(--hi);  }
.row-rmed  { border-left:3px solid var(--md);  }
.row-rlow  { border-left:3px solid var(--lo);  }
.row-rinfo { border-left:3px solid var(--inf); }
.rl  { font-weight:500; flex-shrink:0; }
.rd  { color:var(--muted); font-size:13px; font-family:var(--mono);
       word-break:break-all; }
.badge { display:inline-block; font-size:11px; font-weight:700;
  padding:1px 6px; border-radius:4px; margin-right:4px; }
.ok    { background:var(--okb);  color:var(--ok);  }
.warn  { background:var(--wnb);  color:var(--wn);  }
.miss  { background:var(--msb);  color:var(--ms);  }
.info  { background:var(--infb); color:var(--inf); }
.rhigh { background:var(--hib);  color:var(--hi);  }
.rmed  { background:var(--mdb);  color:var(--md);  }
.rlow  { background:var(--lob);  color:var(--lo);  }
.rinfo { background:var(--infb); color:var(--inf); }
.subt  { font-size:12px; font-weight:600; text-transform:uppercase;
  letter-spacing:.06em; color:var(--muted); padding:12px 18px 4px; }
.rl2   { display:flex; align-items:center; gap:5px;
  font-size:12px; color:var(--muted); flex-wrap:wrap; }
"""


def build(results: list[dict], permissions: dict, scan_time: str) -> str:
    """
    Build the full HTML report string.

    Args:
        results:     List of dicts from each scan_* function
        permissions: Dict from scan_permissions()
        scan_time:   Human-readable timestamp string
    """
    all_nav   = ""
    all_cards = ""

    for result in results:
        nav, card = _render_scan_card(result)
        all_nav   += nav
        all_cards += card

    perm_nav, perm_card = _render_permissions_card(permissions)
    all_nav   += perm_nav
    all_cards += perm_card

    os_str = f"{platform.system()} {platform.release()}"
    py_str = sys.version.split()[0]

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Ecosystem Scan Report</title>
  <style>{CSS}</style>
</head>
<body>

<nav class="topbar">
  <span class="tb-title">AI Ecosystem Scan</span>
  {all_nav}
</nav>

<div class="page">
  <div class="hero">
    <div style="font-size:30px">&#x1F916;</div>
    <div>
      <h1>AI Ecosystem Scan Report</h1>
      <div class="hero-meta">
        {_esc(os_str)} &nbsp;&middot;&nbsp;
        Python {_esc(py_str)} &nbsp;&middot;&nbsp;
        {_esc(scan_time)}
      </div>
    </div>
  </div>

  {all_cards}
</div>

</body>
</html>"""
