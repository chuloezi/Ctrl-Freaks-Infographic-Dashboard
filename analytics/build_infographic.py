"""Build the one-page static infographic from the processed NISR workbook rows.

Run: python analytics/build_infographic.py
Output: static/static_infographic.html and PDF, plus a copy of the PDF for the site.
Standard library only; printing the PDF needs Chrome or Edge (or set CHROME_PATH).
Every number is read from data/processed; none are typed into this file.
"""
import csv
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / 'data' / 'processed'
OUT_HTML = ROOT / 'static' / 'static_infographic.html'
OUT_PDF = ROOT / 'static' / 'static_infographic.pdf'
SITE_PDF = ROOT / 'dynamic' / 'public' / 'static_infographic.pdf'

TEAL, RUST, AMBER = '#18766c', '#b65c3e', '#b98a2f'
INK, SOFT, MUTED, GRID, SURFACE = '#172b2c', '#526461', '#6b7a77', '#e4e4da', '#fffefb'

with (PROCESSED / 'nisr_workbook_rows.csv').open(encoding='utf-8', newline='') as handle:
    ROWS = [r for r in csv.DictReader(handle) if r['publication_year'] == '2025']
with (PROCESSED / 'dashboard_supplemental_source.csv').open(encoding='utf-8', newline='') as handle:
    SERIES = list(csv.DictReader(handle))


def cells(sheet, excel_row, label):
    """Cells of one workbook row; fails if the row no longer holds the expected label."""
    for row in ROWS:
        if row['sheet'] == sheet and int(row['excel_row']) == excel_row:
            values = [c.strip() for c in json.loads(row['values_json'])]
            if label not in values:
                raise ValueError(f'{sheet} row {excel_row} has no {label}: {values}')
            return values
    raise KeyError(f'{sheet} row {excel_row}')


def nums(sheet, excel_row, label):
    values = cells(sheet, excel_row, label)
    return [float(c) for c in values[values.index(label) + 1:] if c and c != '-']


def chart(name):
    picked = [r for r in SERIES if r['chart'] == name]
    return [(r['category'], float(r['value'])) for r in picked]


def n(value):
    return f'{int(round(value)):,}'


def signed(value, digits=1):
    return f'{value:+.{digits}f}'


YEARS = list(range(2019, 2026))
births = nums('10.3', 4, 'Registered live births (number)')
expected_births = nums('10.3', 7, 'Expected live births (number)')
birth_complete = nums('Figure7', 5, 'Birth registration completeness rate')
birth_rate = nums('10.3', 14, 'Adjusted Crude birth rate (per 1,000 population)')
fertility = nums('10.3', 15, 'Total fertility rate (births per woman)')
deaths = nums('10.5', 3, 'Registered deaths (number)')
expected_deaths = nums('10.5', 6, 'Expected number of deaths')
death_complete = nums('Figure7', 6, 'Death registration completeness rate')
male_complete = nums('10.5', 10, 'Male')
female_complete = nums('10.5', 11, 'Female')
death_rate = nums('10.5', 12, 'Crude death rate per 1,000 (Adjusted)')
under_five = nums('10.5', 13, 'Under-5 mortality rate per 1,000 live births (Adjusted)')
timely_birth = nums('Figure6', 5, 'Proportion of birth registered timely')
timely_death = nums('Figure6', 6, 'Proportion of death registered timely')
marriages = [nums('Table18', 4 + i, str(y))[0] for i, y in enumerate(YEARS)]
marriage_rate = [nums('Table18', 4 + i, str(y))[2] for i, y in enumerate(YEARS)]
divorces = nums('Figure32', 7, 'Grand Total')[0]
divorces_granted = nums('Table28', 5, 'Number of divorces granted and registered in 2025')[0]
divorce_age_male = nums('Table28', 7, 'Average age at divorce for males')[0]
divorce_age_female = nums('Table28', 8, 'Average age at divorce for females')[0]
facility_share = nums('Table4', 5, 'All')[4]
low_weight = nums('Table9', 10, 'Low birth weight (%)')[6]
property_share = nums('Table20', 4, 'Community of property regime')[1]
facility_deaths, certified = nums('Table 15', 8, '2025')[:2]
verbal_autopsies = nums('Table 16', 4, 'VA for deaths that occurred in the reporting year')[3]
usable = nums('Figure24', 6, 'Usable')
adolescent = nums('Figure 12', 5, '<15')[1] + nums('Figure 12', 6, '15-19')[1]
community_share = 100 * (deaths[-1] - facility_deaths) / deaths[-1]
fertility_peak = max(chart('age_specific_fertility'), key=lambda x: x[1])
gaps = [b - d for b, d in zip(birth_complete, death_complete)]
widest = max(range(7), key=lambda i: gaps[i])
lowest_death = min(range(7), key=lambda i: death_complete[i])
peak_timely = max(range(7), key=lambda i: timely_death[i])
top_causes = [cells('Table 17', 4 + i, str(i + 1)) for i in range(5)]
wife = chart('divorce_province_wife')
husband = dict(chart('divorce_province_husband'))
duration = chart('divorce_duration')
largest_duration = max(duration, key=lambda x: x[1])
assert wife[0][0] == 'Kigali City' and wife[0][1] == max(v for _, v in wife)


def waffle(value, color):
    """Ten-by-ten grid: one dot for each of 100 estimated events."""
    filled = int(value + 0.5)
    dots = []
    for i in range(100):
        x, y = 9 + (i % 10) * 19, 9 + (i // 10) * 19
        fill = color if i < filled else GRID
        dots.append(f'<circle cx="{x}" cy="{y}" r="7.5" fill="{fill}"/>')
    return f'<svg viewBox="0 0 189 189" class="waffle" role="img" aria-label="{filled} of 100 dots filled">{"".join(dots)}</svg>'


def completeness_chart():
    W, H, L, R, T, B = 700, 262, 36, 86, 16, 26
    x = lambda i: L + i * (W - L - R) / 6
    y = lambda v: T + (H - T - B) * (1 - v / 100)
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Birth and death registration completeness, 2019 to 2025">']
    for v in (0, 25, 50, 75, 100):
        s.append(f'<line x1="{L}" x2="{W-R}" y1="{y(v)}" y2="{y(v)}" stroke="{GRID}"/><text x="{L-8}" y="{y(v)+4}" text-anchor="end" class="axis">{v}</text>')
    for i, year in enumerate(YEARS):
        s.append(f'<text x="{x(i)}" y="{H-6}" text-anchor="middle" class="axis">{year}</text>')
    # The widest gap, drawn between the two lines.
    s.append(f'<line x1="{x(widest)}" x2="{x(widest)}" y1="{y(birth_complete[widest])+8}" y2="{y(death_complete[widest])-8}" stroke="{MUTED}" stroke-dasharray="3 3"/>')
    s.append(f'<text x="{x(widest)+7}" y="{y((birth_complete[widest]+death_complete[widest])/2)+4}" class="note">{gaps[widest]:.1f}-point gap, the widest</text>')
    for values, color, name in ((birth_complete, TEAL, 'Births'), (death_complete, RUST, 'Deaths')):
        s.append(f'<polyline fill="none" stroke="{color}" stroke-width="2.5" stroke-linejoin="round" points="{" ".join(f"{x(i)},{y(v)}" for i, v in enumerate(values))}"/>')
        for i, v in enumerate(values):
            s.append(f'<circle cx="{x(i)}" cy="{y(v)}" r="4.5" fill="{color}" stroke="{SURFACE}" stroke-width="2"/>')
        s.append(f'<text x="{x(0)}" y="{y(values[0])-11}" text-anchor="middle" class="val">{values[0]:.1f}</text>')
        s.append(f'<text x="{x(6)+11}" y="{y(values[-1])+1}" class="val">{values[-1]:.1f}%</text>')
        s.append(f'<text x="{x(6)+11}" y="{y(values[-1])+15}" class="note">{name}</text>')
    s.append(f'<text x="{x(lowest_death)}" y="{y(death_complete[lowest_death])+20}" text-anchor="middle" class="val">{death_complete[lowest_death]:.1f}</text>')
    return ''.join(s) + '</svg>'


def columns(items, color, highlight, width=330, height=138, fmt=None, max_value=None, label_every=1):
    """Vertical bars with a label on the highlighted bars only."""
    fmt = fmt or n
    top = max_value or max(v for _, v in items)
    T, B = 18, 20
    step = width / len(items)
    bar = step * 0.68
    s = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{", ".join(f"{k}: {fmt(v)}" for k, v in items)}">']
    base = height - B
    for i, (label, value) in enumerate(items):
        h = max((base - T) * value / top, 1.5)
        x = i * step + (step - bar) / 2
        strong = label in highlight
        r = min(3, bar / 2, h)
        s.append(f'<path d="M{x},{base} v{-(h-r)} q0,{-r} {r},{-r} h{bar-2*r} q{r},0 {r},{r} v{h-r} z" fill="{color}" opacity="{1 if strong else .5}"/>')
        if strong:
            s.append(f'<text x="{x+bar/2}" y="{base-h-5}" text-anchor="middle" class="val">{fmt(value)}</text>')
        if i % label_every == 0 or strong:
            s.append(f'<text x="{x+bar/2}" y="{height-6}" text-anchor="middle" class="axis small">{label}</text>')
    s.append(f'<line x1="0" x2="{width}" y1="{base}" y2="{base}" stroke="{MUTED}"/>')
    return ''.join(s) + '</svg>'


def rows_bars(items, color, width=330, label_width=78, value_width=44):
    top = max(v for _, v in items)
    usable_width = width - label_width - value_width
    s = [f'<svg viewBox="0 0 {width} {len(items)*19}" role="img" aria-label="{", ".join(f"{k}: {n(v)}" for k, v in items)}">']
    for i, (label, value) in enumerate(items):
        y = i * 19
        s.append(f'<text x="0" y="{y+12}" class="axis dark">{label}</text>')
        s.append(f'<rect x="{label_width}" y="{y+3}" width="{max(usable_width*value/top,2)}" height="11" rx="3" fill="{color}"/>')
        s.append(f'<text x="{width}" y="{y+13}" text-anchor="end" class="val">{n(value)}</text>')
    return ''.join(s) + '</svg>'


def stacked(label, parts):
    segments = ''.join(f'<i style="width:{v}%;background:{c};color:{"#fff" if c == RUST else INK}"><b>{v:.1f}</b></i>' for v, c in parts)
    return f'<div class="stack"><span>{label}</span><div>{segments}</div></div>'


def kpi(color, name, value, foot):
    return f'<div class="kpi"><i style="background:{color}"></i><span>{name}</span><strong>{value}</strong><small>{foot}</small></div>'


def stat(value, text):
    return f'<div class="stat"><strong>{value}</strong><span>{text}</span></div>'


causes = dict(chart('cause_facility')), dict(chart('cause_community'))
cause_colors = {'Non-communicable': RUST, 'Communicable etc.': '#d9a93a', 'Injuries': '#2a9d8f'}
cause_rows = ''.join(
    f'<tr><td>{c[0]}</td><td>{c[1]}</td><td class="num">{float(c[2]):.1f}%</td><td>{c[3]}</td><td class="num">{float(c[4]):.1f}%</td></tr>'
    for c in top_causes)

HTML = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Every Life, Counted | Ctrl Freaks</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Libre+Baskerville:wght@400;700&display=swap" rel="stylesheet">
<style>
@page{{size:297mm 420mm;margin:0}}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:297mm;height:420mm}}
body{{background:#f6f4ec;color:{INK};font:12.5px/1.42 'DM Sans',Arial,sans-serif;-webkit-print-color-adjust:exact;print-color-adjust:exact;overflow:hidden}}
.page{{height:420mm;padding:0 40px;display:flex;flex-direction:column;gap:13px;border-top:12px solid {TEAL}}}
header{{padding-top:24px;display:flex;justify-content:space-between;align-items:flex-end;gap:30px}}
.eyebrow{{font-size:10.5px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:{TEAL}}}
h1{{font:400 62px/1.05 'Libre Baskerville',Georgia,serif;letter-spacing:-.03em;margin:7px 0 0}}
.lede{{max-width:340px;font-size:14px;line-height:1.45;color:{SOFT}}}
.kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}}
.kpi,.panel{{background:{SURFACE};border:1px solid #e3e2d7;border-radius:4px}}
.kpi{{padding:0 15px 11px}}
.kpi i{{display:block;width:30px;height:3px;margin-bottom:10px}}
.kpi span{{display:block;font-size:11.5px;font-weight:600;color:{SOFT}}}
.kpi strong{{display:block;font:400 31px/1.2 'Libre Baskerville',Georgia,serif;letter-spacing:-.02em}}
.kpi small{{display:block;font-size:11px;line-height:1.3;color:{MUTED}}}
.story{{display:grid;grid-template-columns:1fr 262px;gap:10px}}
.panel{{padding:14px 16px}}
h2{{font:400 21px/1.2 'Libre Baskerville',Georgia,serif;letter-spacing:-.01em}}
h3{{font-size:12.5px;font-weight:700;line-height:1.25;margin-top:11px}}
.sub{{font-size:11px;color:{MUTED};margin-bottom:5px}}
.head2{{display:flex;justify-content:space-between;align-items:baseline;gap:20px;margin-bottom:6px}}
.gap{{background:{TEAL};color:#fff;border-radius:4px;padding:16px 18px;display:flex;flex-direction:column}}
.gap .eyebrow{{color:#cfe3dc}}
.gap strong{{font:400 62px/1.1 'Libre Baskerville',Georgia,serif;letter-spacing:-.03em;margin-top:6px}}
.gap span{{font-size:14px}}
.gap p{{margin-top:16px;font-size:13px;line-height:1.48;color:#e8f2ee}}
.count{{display:grid;grid-template-columns:150px 1fr 150px 1fr;gap:12px;align-items:center;margin-bottom:9px;padding-bottom:10px;border-bottom:1px solid {GRID}}}
.waffle{{width:150px;height:auto;display:block}}
.count b{{display:block;font:400 34px/1.1 'Libre Baskerville',Georgia,serif;letter-spacing:-.02em}}
.count p{{font-size:12px;color:{SOFT};margin-top:4px}}
svg{{display:block;width:100%;height:auto;font-family:'DM Sans',Arial,sans-serif}}
.axis{{font-size:11px;fill:{MUTED}}}.axis.small{{font-size:10px}}.axis.dark{{fill:{INK}}}
.val{{font-size:11px;font-weight:700;fill:{INK}}}
.note{{font-size:11px;fill:{SOFT}}}
.three{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;flex:1;min-height:0}}
.col{{border-top-width:3px;border-top-style:solid;display:flex;flex-direction:column}}
.stats{{display:grid;grid-template-columns:1fr 1fr;gap:9px 12px;margin-top:9px}}
.stat strong{{display:block;font:400 21px/1.15 'Libre Baskerville',Georgia,serif;letter-spacing:-.02em}}
.stat span{{display:block;font-size:11px;line-height:1.28;color:{SOFT};margin-top:2px}}
.callout{{margin-top:auto;font-size:11.5px;line-height:1.38;color:{SOFT};padding-top:8px;border-top:1px solid {GRID}}}
table{{width:100%;border-collapse:collapse;font-size:10.5px;line-height:1.2;margin-top:3px}}
th{{text-align:left;font-size:9.5px;font-weight:700;color:{MUTED};padding:2px 3px 3px 0;border-bottom:1px solid {GRID}}}
td{{padding:2.5px 3px 2.5px 0;vertical-align:top;border-bottom:1px solid #f0efe7}}
.num{{font-weight:700;text-align:right;white-space:nowrap;padding-right:6px}}
.stack{{display:grid;grid-template-columns:58px 1fr;align-items:center;gap:4px;margin-top:3px;font-size:10.5px}}
.stack>div{{display:flex;gap:2px}}
.stack i{{display:block;height:17px;font-style:normal;color:#fff;font-size:10px;line-height:17px;text-align:center}}
.stack i:first-child{{border-radius:3px 0 0 3px}}.stack i:last-child{{border-radius:0 3px 3px 0}}
.stack b{{font-weight:700}}
.legend{{display:flex;gap:10px;font-size:10.5px;color:{SOFT};margin-top:4px}}
.legend i{{display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:4px}}
.read{{display:grid;grid-template-columns:repeat(3,1fr);gap:22px;padding:2px 2px 0}}
.read b{{display:block;font-size:12.5px}}
.read p{{font-size:11.5px;line-height:1.38;color:{SOFT}}}
footer{{border-top:1px solid #d9d8cc;padding:8px 0 16px;display:flex;justify-content:space-between;gap:30px;font-size:9.5px;line-height:1.38;color:{MUTED}}}
footer b{{color:{TEAL};white-space:nowrap}}
</style></head><body><div class="page">
<header>
 <div><div class="eyebrow">Ctrl Freaks / Rwanda civil registration &amp; vital statistics / 2019&ndash;2025</div><h1>Every life, counted.</h1></div>
 <p class="lede">Rwanda registers more than nine in ten expected births, but only about half of expected deaths. Seven years of data show where that gap is closing.</p>
</header>

<section class="kpis">
 {kpi(TEAL,'Live births registered',n(births[-1]),f'{signed(100*(births[-1]/births[0]-1))}% since 2019')}
 {kpi(RUST,'Deaths registered',n(deaths[-1]),f'{signed(100*(deaths[-1]/deaths[0]-1))}% since 2019, as coverage widened')}
 {kpi(AMBER,'Marriages registered',n(marriages[-1]),f'{signed(100*(marriages[-1]/marriages[0]-1))}% since 2019')}
 {kpi(AMBER,'Divorces registered',n(divorces),f'{n(divorces_granted)} of them granted in 2025')}
</section>

<section class="story">
 <div class="panel">
  <div class="count">
   {waffle(birth_complete[-1],TEAL)}<div><b>{birth_complete[-1]:.1f}%</b><p>of estimated births were registered in 2025: {n(births[-1])} of about {n(expected_births[-1])}.</p></div>
   {waffle(death_complete[-1],RUST)}<div><b>{death_complete[-1]:.1f}%</b><p>of estimated deaths were registered in 2025: {n(deaths[-1])} of about {n(expected_deaths[-1])}.</p></div>
  </div>
  <div class="head2"><h2>The gap is closing, but only recently</h2><span class="sub">Registration completeness, % of estimated events</span></div>
  {completeness_chart()}
 </div>
 <aside class="gap">
  <div class="eyebrow">The coverage gap, 2025</div>
  <strong>{gaps[-1]:.1f}</strong><span>percentage points</span>
  <p>Births are recorded far more completely than deaths. The gap reached {gaps[widest]:.1f} points in {YEARS[widest]} and has narrowed every year since.</p>
  <p><b>Births have levelled off.</b> {birth_complete[-1]:.1f}% matches the {YEARS[3]} level, after dipping near 90%.</p>
  <p><b>Deaths are driving the change,</b> up from a low of {death_complete[lowest_death]:.1f}% in {YEARS[lowest_death]}.</p>
  <p><b>Speed has slipped.</b> Deaths registered on time fell from {timely_death[peak_timely]:.1f}% in {YEARS[peak_timely]} to {timely_death[-1]:.1f}%, while births held at {timely_birth[-1]:.1f}%.</p>
  <p><b>Women's deaths are counted less.</b> Completeness is {female_complete[-1]:.1f}% for women and {male_complete[-1]:.1f}% for men.</p>
 </aside>
</section>

<section class="three">
 <div class="panel col" style="border-top-color:{TEAL}">
  <h2>Births</h2><p class="sub">Where life begins</p>
  <div class="stats">
   {stat(f'{facility_share:.1f}%','of registered births took place in a health facility')}
   {stat(f'{fertility[0]:.1f} &rarr; {fertility[-1]:.1f}','births per woman, 2019 to 2025 (adjusted)')}
   {stat(f'{adolescent:.1f}%','of births were to mothers under 20')}
   {stat(f'{low_weight:.1f}%',f'low birth weight, up from {nums("Table9",10,"Low birth weight (%)")[0]:.1f}% in 2019')}
  </div>
  <h3>One in four births is to a mother aged 20&ndash;24</h3><p class="sub">Share of registered births by mother's age, %</p>
  {columns(chart('maternal_age'),TEAL,('20–24','25–29','15–19'),height=172,fmt=lambda v:f'{v:.1f}')}
  <h3>Fertility itself peaks later, at {fertility_peak[0]}</h3><p class="sub">Adjusted births per 1,000 women, by age</p>
  {columns(chart('age_specific_fertility'),TEAL,(fertility_peak[0],),height=150,fmt=lambda v:f'{v:.1f}')}
  <p class="callout">More births are registered, yet the adjusted birth rate fell from {birth_rate[0]:.1f} to {birth_rate[-1]:.1f} per 1,000 people. Counts and rates tell different stories.</p>
 </div>
 <div class="panel col" style="border-top-color:{RUST}">
  <h2>Deaths</h2><p class="sub">Seeing what we lose</p>
  <div class="stats">
   {stat(f'{community_share:.1f}%','of registered deaths happened in the community')}
   {stat(f'{under_five[0]:.1f} &rarr; {under_five[-1]:.1f}','under-5 deaths per 1,000 live births, 2019 to 2025 (adjusted)')}
   {stat(n(certified),f'of {n(facility_deaths)} facility deaths were medically certified')}
   {stat(n(verbal_autopsies),'verbal autopsies recorded causes for community deaths')}
  </div>
  <h3>Non-communicable disease leads in both settings</h3><p class="sub">Share of usable causes of death, %</p>
  {stacked('Facility',[(causes[0][k],cause_colors[k]) for k in cause_colors])}
  {stacked('Community',[(causes[1][k],cause_colors[k]) for k in cause_colors])}
  <div class="legend"><span><i style="background:{RUST}"></i>Non-communicable</span><span><i style="background:#d9a93a"></i>Communicable etc.</span><span><i style="background:#2a9d8f"></i>Injuries</span></div>
  <h3>The leading causes differ by setting</h3><p class="sub">Top five recorded causes, 2025</p>
  <table><tr><th>#</th><th>Health facility</th><th></th><th>Community</th><th></th></tr>{cause_rows}</table>
  <p class="callout">These shares describe recorded causes, not all deaths in Rwanda. Adjusted crude death rate: {death_rate[0]:.1f} to {death_rate[-1]:.1f} per 1,000. Usable causes: {usable[6]:.1f}% in facilities, {usable[9]:.1f}% in the community.</p>
 </div>
 <div class="panel col" style="border-top-color:{AMBER}">
  <h2>Marriage &amp; divorce</h2><p class="sub">Families form, families change</p>
  <div class="stats">
   {stat(f'{property_share:.1f}%','of marriages chose community of property')}
   {stat(f'{marriage_rate[-1]:.1f}',f'marriages per 1,000 people, from {marriage_rate[0]:.1f} in 2019')}
   {stat(f'{100*divorces_granted/divorces:.0f}%','of divorces registered in 2025 were also granted that year')}
   {stat(f'{divorce_age_female:.1f} / {divorce_age_male:.1f}','average age at divorce, women / men')}
  </div>
  <h3>Marriage registration has swung widely</h3><p class="sub">Registered marriages per year</p>
  {columns(list(zip(map(str,YEARS),marriages)),AMBER,('2019','2020','2023','2025'),height=104)}
  <h3>The largest group divorced after {largest_duration[0]} years</h3><p class="sub">Registered divorces by length of marriage, 2025</p>
  {columns(duration,AMBER,(largest_duration[0],),height=92,label_every=2)}
  <h3>Kigali City registers the most divorces</h3><p class="sub">By wife's residence, 2025. By husband's, Kigali has {n(husband['Kigali City'])}.</p>
  {rows_bars(wife,AMBER)}
 </div>
</section>

<section class="read">
 <div><b>Completeness is not timeliness.</b><p>Completeness compares recorded events with estimated events. Timeliness asks how many recorded events met the legal deadline.</p></div>
 <div><b>More recorded deaths is not more dying.</b><p>Registered deaths rose as coverage widened, while the adjusted death rate edged down.</p></div>
 <div><b>A count is not a risk.</b><p>Provinces differ in population, so divorce counts are not rates, and no count here is one person's probability.</p></div>
</section>

<footer>
 <div>Source: NISR, CRVS Final Tables 2025 (Figures 6, 7, 12, 15, 24, 25, 32; Tables 4, 9, 15, 16, 17, 18, 20, 24, 27, 28; 10.3, 10.5). Expected events and adjusted rates are NISR estimates. The published 2025 factsheet prints 50,236 marriages; the final tables give {n(marriages[-1])}.</div>
 <div style="text-align:right"><b>Independent student infographic by Ctrl Freaks</b><br>NISR Infographic Competition 2026. Not an official NISR product.</div>
</footer>
</div></body></html>
'''


def find_browser():
    candidates = [os.environ.get('CHROME_PATH'), shutil.which('chrome'), shutil.which('google-chrome'), shutil.which('msedge'),
                  r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                  r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe']
    return next((c for c in candidates if c and Path(c).exists()), None)


def main():
    OUT_HTML.write_text(HTML, encoding='utf-8')
    browser = find_browser()
    if not browser:
        raise SystemExit('Wrote the HTML, but found no Chrome or Edge. Set CHROME_PATH to print the PDF.')
    subprocess.run([browser, '--headless=new', '--disable-gpu', '--no-pdf-header-footer', '--virtual-time-budget=8000',
                    f'--print-to-pdf={OUT_PDF}', OUT_HTML.as_uri()], check=True, capture_output=True, timeout=120)
    shutil.copyfile(OUT_PDF, SITE_PDF)
    print(f'Wrote {OUT_PDF.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
