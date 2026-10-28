"""Export existing, source-traceable Python analytics CSVs for the static React site.

Standard-library only. Run after analyze_crvs.py when source workbooks change.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / 'data' / 'processed'
DEST = ROOT / 'dynamic' / 'src' / 'analytics-data.json'

def rows(filename):
    with (PROCESSED / filename).open(encoding='utf-8-sig', newline='') as handle:
        result = list(csv.DictReader(handle))
    if [int(x['year']) for x in result] != list(range(2019, 2026)):
        raise ValueError(f'Expected consecutive years 2019–2025 in {filename}')
    return result

def numbers(data, column, cast=float):
    return [cast(record[column]) for record in data]

def main():
    birth = rows('birth_trends_2019_2025.csv')
    death = rows('death_trends_2019_2025.csv')
    marriage = rows('marriage_trends_2019_2025.csv')
    registration = rows('registration_trends_2019_2025.csv')
    payload = {
        'years': numbers(birth, 'year', int),
        'births': {'counts': numbers(birth, 'registered_live_births', int), 'rates': numbers(birth, 'adjusted_crude_birth_rate_per_1000')},
        'deaths': {'counts': numbers(death, 'registered_deaths', int), 'rates': numbers(death, 'adjusted_crude_death_rate_per_1000')},
        'marriages': {'counts': numbers(marriage, 'registered_marriages', int), 'rates': numbers(marriage, 'crude_marriage_rate_per_1000')},
        'registration': {'birthCompleteness': numbers(registration, 'birth_completeness_pct'), 'deathCompleteness': numbers(registration, 'death_completeness_pct')},
        'provenance': {'origin': 'NISR CRVS workbooks; precomputed by analytics/analyze_crvs.py', 'marriage_count_note': '2025 workbook time series: 50,256; factsheet headline: 50,236'}
    }
    extra = {}
    with (PROCESSED / 'dashboard_supplemental_source.csv').open(encoding='utf-8', newline='') as fh:
        for r in csv.DictReader(fh):
            x = extra.setdefault(r['chart'], {'labels': [], 'values': [], 'unit': r['unit'], 'source': r['provenance'], 'verification_status': r['verification_status']})
            x['labels'].append(r['category'])
            x['values'].append(float(r['value']))
    payload['supplemental'] = extra
    indicators = {}
    with (PROCESSED / 'factsheet_indicators_2025.csv').open(encoding='utf-8',newline='') as fh:
        indicators = {r['indicator']: float(r['value']) for r in csv.DictReader(fh)}
    payload['factsheet_indicators'] = indicators
    payload['display'] = {}
    payload['display_provenance'] = {}
    with (PROCESSED / 'dashboard_display_source.csv').open(encoding='utf-8', newline='') as fh:
        for r in csv.DictReader(fh):
            number = float(r['value'])
            number_string = f'{int(number):,}' if ',' in r['display'] else r['value']
            payload['display'][r['display']] = number_string + r['suffix']
            payload['display_provenance'][r['display']] = r['source']
    keymap = {'Registered live births': '356,838', 'Registered deaths': '39,355', 'Registered marriages': '50,236',
              'Registered divorces': '4,479', 'Divorces granted and registered in 2025': '2,629',
              'Live births in health facilities': '97.8%', 'Births to adolescent mothers aged 10–19': '8.5%',
              'Total fertility rate': '3.5', 'Registered community deaths': '55.9%',
              'Usable cause of death in facilities': '82.3%', 'Usable cause of death in community': '83.9%',
              'Community of property marriages': '97.0%'}
    for indicator,label in keymap.items():
        if indicator in indicators:
            n=indicators[indicator]
            payload['display'][label] = (f'{int(n):,}' if ',' in label else str(n)) + ('%' if label.endswith('%') else '')
            payload['display_provenance'][label] = 'data/processed/factsheet_indicators_2025.csv: ' + indicator
    payload['data_quality_warning'] = 'Supplemental legacy-transcribed chart series are not independently source-verified; see CSV verification_status.'
    DEST.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'Wrote {DEST.relative_to(ROOT)} from four precomputed CSV files')

if __name__ == '__main__':
    main()
