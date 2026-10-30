"""Check the figures published on the dashboard against the NISR workbook rows.

Run: python analytics/verify_dashboard.py
Standard-library only. Exits with status 1 if any figure disagrees with its source.
"""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / 'data' / 'processed'
DATA = json.loads((ROOT / 'dynamic' / 'src' / 'analytics-data.json').read_text(encoding='utf-8'))
APP = (ROOT / 'dynamic' / 'src' / 'App.jsx').read_text(encoding='utf-8')

with (PROCESSED / 'nisr_workbook_rows.csv').open(encoding='utf-8', newline='') as handle:
    ROWS = [r for r in csv.DictReader(handle) if r['publication_year'] == '2025']

errors = []


def w(sheet, label):
    """Numbers after `label` in the first row that has it in one of its first two cells."""
    for row in ROWS:
        if row['sheet'] != sheet:
            continue
        cells = [c.strip() for c in json.loads(row['values_json'])]
        for i in (0, 1):
            if i < len(cells) and cells[i] == label:
                try:
                    return [None if c == '-' else float(c) for c in cells[i + 1:] if c]
                except ValueError:  # a header row repeating the label
                    break
    raise KeyError(f'{sheet}: {label}')


def check_display(shown, expected):
    """`shown` is the text on the page; `expected` comes straight from workbook cells."""
    actual = DATA['display'].get(shown)
    if actual != shown:
        errors.append(f'display value for {shown} is {actual}')
    body = shown.rstrip('%')
    if ',' in body:
        rounded = f'{int(expected):,}'
    else:
        rounded = f'{expected:.{len(body.split(".")[1]) if "." in body else 0}f}'
    if rounded != body:
        errors.append(f'dashboard shows {shown}; workbook gives {rounded}')


def check_series(chart, labels, expected):
    series = DATA['supplemental'].get(chart)
    if not series:
        errors.append(f'missing chart series {chart}')
        return
    if series['labels'] != labels:
        errors.append(f'{chart} labels are {series["labels"]}')
    for label, shown, value in zip(labels, series['values'], expected):
        if abs(shown - value) > 0.05:
            errors.append(f'{chart} {label} shows {shown}; workbook gives {value:.2f}')


AGES = ['15-19', '20-24', '25-29', '30-34', '35-39', '40-44', '45-49']
DURATIONS = ['0-4', '5-9', '10-14', '15-19', '20-24', '25-29', '30-34', '35-39', '40-44', '45-49', '50+']
dash = lambda labels: [x.replace('-', '–') for x in labels]

births = w('10.3', 'Registered live births (number)')
birth_rate = w('10.3', 'Adjusted Crude birth rate (per 1,000 population)')
deaths = w('10.5', 'Registered deaths (number)')
death_rate = w('10.5', 'Crude death rate per 1,000 (Adjusted)')
birth_complete = w('Figure7', 'Birth registration completeness rate')
death_complete = w('Figure7', 'Death registration completeness rate')
marriages = {int(float(y)): w('Table18', y) for y in map(str, range(2019, 2026))}
divorces = w('Figure32', 'Grand Total')[0]
facility_deaths = w('Table 15', '2025')[0]
causes = {
    'Non-communicable': w('Figure25', 'Noncommunicable diseases'),
    'Communicable etc.': w('Figure25', 'Communicable, maternal, perinatal and nutritional conditions'),
    'Injuries': w('Figure25', 'Injuries'),
}
usable = w('Figure24', 'Usable')
under_15 = w('Figure 12', '<15')[1]
teen = w('Figure 12', '15-19')[1]

for shown, expected in {
    '356,838': births[-1], '39,355': deaths[-1], '50,256': marriages[2025][0], '4,479': divorces,
    '2,629': w('Table28', 'Number of divorces granted and registered in 2025')[0],
    '92.9%': birth_complete[-1], '50.5%': death_complete[-1], '87.0%': birth_complete[0], '31.4%': death_complete[0],
    '42.4': birth_complete[-1] - death_complete[-1], '5.9': birth_complete[-1] - birth_complete[0],
    '19.1': death_complete[-1] - death_complete[0], '4.4': death_complete[-1] - death_complete[-2],
    '99.1%': w('Figure6', 'Proportion of birth registered timely')[-1],
    '89.9%': w('Figure6', 'Proportion of death registered timely')[-1],
    '43,440': births[-1] - births[0], '13.9%': 100 * (births[-1] / births[0] - 1),
    '29.1': birth_rate[0], '27.2': birth_rate[-1], '1.9': birth_rate[0] - birth_rate[-1],
    '5.5': death_rate[-1], '23,791': deaths[0], '3.9': marriages[2019][2], '3.6': marriages[2025][2],
    '97.8%': w('Table4', 'All')[4], '8.5%': under_15 + teen, '3.5': w('Table9', 'TFR')[6],
    '8.1%': w('Table9', 'Low birth weight (%)')[6], '102.7': w('Table9', 'Sex ratio at Birth')[6],
    '24,393': w('Table5', 'Gasabo')[2], '8,229': w('Table5', 'Nyaruguru')[2],
    '166.3': w('Figure15', '25-29')[0], '14,997': w('Table 15', '2025')[1],
    '18,921': w('Table 16', 'VA for deaths that occurred in the reporting year')[3],
    '55.9%': 100 * (deaths[-1] - facility_deaths) / deaths[-1],
    '82.3%': usable[6], '83.9%': usable[9], '49.5%': 100 * causes['Non-communicable'][1],
    '58.8%': 100 * causes['Non-communicable'][3], '97.0%': w('Table20', 'Community of property regime')[1],
    '24%': 100 * w('Table27', '5-9')[2] / divorces,
}.items():
    check_display(shown, expected)
if death_rate[0] != 5.9:
    errors.append('the 2019 crude death rate no longer shares the display value 5.9')

# Both trend charts come straight from these workbook series.
for name, shown, expected in [
    ('birth counts', DATA['births']['counts'], births), ('birth rates', DATA['births']['rates'], birth_rate),
    ('death counts', DATA['deaths']['counts'], deaths), ('death rates', DATA['deaths']['rates'], death_rate),
    ('marriage counts', DATA['marriages']['counts'], [marriages[y][0] for y in range(2019, 2026)]),
    ('marriage rates', DATA['marriages']['rates'], [marriages[y][2] for y in range(2019, 2026)]),
    ('birth completeness', DATA['registration']['birthCompleteness'], birth_complete),
    ('death completeness', DATA['registration']['deathCompleteness'], death_complete),
]:
    if list(shown) != list(expected):
        errors.append(f'{name} are {shown}; workbook gives {expected}')

fig12_labels = ['<15'] + AGES + ['50+']
check_series('maternal_age', ['<15'] + dash(AGES) + ['50+'], [w('Figure 12', x)[1] for x in fig12_labels])
check_series('age_specific_fertility', dash(AGES), [w('Figure15', x)[0] for x in AGES])
check_series('divorce_duration', dash(DURATIONS), [w('Table27', x)[2] for x in DURATIONS])
check_series('cause_facility', list(causes), [100 * v[1] for v in causes.values()])
check_series('cause_community', list(causes), [100 * v[3] for v in causes.values()])

PLACES = ['Eastern Province', 'Kigali City', 'Northern Province', 'Southern Province', 'Western Province', 'Abroad']
SHOWN = {'Kigali City': 'Kigali City', 'Eastern Province': 'Eastern', 'Southern Province': 'Southern',
         'Western Province': 'Western', 'Northern Province': 'Northern', 'Abroad': 'Abroad'}
husband = dict(zip(PLACES, w('Table24', 'Grand Total')))
wife = {place: w('Table24', place)[-1] for place in PLACES}
order = list(SHOWN)
check_series('divorce_province_wife', [SHOWN[p] for p in order], [wife[p] for p in order])
check_series('divorce_province_husband', [SHOWN[p] for p in order], [husband[p] for p in order])

for chart in ('divorce_duration', 'divorce_province_wife', 'divorce_province_husband'):
    total = sum(DATA['supplemental'].get(chart, {}).get('values', []))
    if total != divorces:
        errors.append(f'{chart} adds up to {total}, not {divorces:.0f}')

districts = {}
for row in ROWS:
    if row['sheet'] == 'Table5':
        cells = json.loads(row['values_json'])
        if len(cells) > 3 and cells[3].replace('.', '').isdigit() and cells[0] not in ('Grand Total', 'Abroad'):
            districts[cells[0]] = float(cells[3])
if max(districts, key=districts.get) != 'Gasabo' or min(districts, key=districts.get) != 'Nyaruguru':
    errors.append('Gasabo and Nyaruguru are no longer the highest and lowest districts')
if len(districts) != 30:
    errors.append(f'expected 30 districts in Table5, found {len(districts)}')

for key in re.findall(r'metric\("([^"]+)"\)', APP):
    if key not in DATA['display']:
        errors.append(f'App.jsx uses metric("{key}"), which has no source value')

if errors:
    print('FAILED: dashboard figures disagree with the workbook')
    for error in errors:
        print(' -', error)
    sys.exit(1)
shown_count = len(set(re.findall(r'metric\("([^"]+)"\)', APP)))
print(f'PASS: {shown_count} displayed figures and all chart series match the workbook rows')
