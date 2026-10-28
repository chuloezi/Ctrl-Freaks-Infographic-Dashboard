"""Ctrl Freaks | reproducible Rwanda CRVS analytics.

Run: python analytics/analyze_crvs.py
Input: three original NISR final-tables XLSX workbooks in data/raw.
Output: transparent CSV source rows, analysis tables, chart, and validation report.

Uses artifact_tool to read XLSX (pip install artifact-tool), stdlib CSV and
matplotlib only for the optional plot. Never silently imputes missing values.
"""
from __future__ import annotations
import csv, json, re
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data'/'raw'
OUT=ROOT/'data'/'processed'
OUT.mkdir(parents=True,exist_ok=True)

SOURCE_FILES={
  2023:'Final Tables_CRVS_2023.xlsx',
  2024:'Final Tables_CRVS_2024_N.xlsx',
  2025:'Final Tables_CRVS_2025_0.xlsx',
}

def write_csv(path, columns, records):
    with path.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=columns)
        writer.writeheader()
        writer.writerows(records)

def clean(v):
    if v is None:return ''
    if isinstance(v,float):return f'{v:.12g}'
    return str(v).strip().replace('\n',' | ')

def read_workbooks():
    from artifact_tool import Blob, SpreadsheetFile
    records=[]; figures={}; sheet_index=[]
    for publication_year, name in SOURCE_FILES.items():
        path=RAW/name
        if not path.exists():raise FileNotFoundError('Missing original NISR source: '+str(path))
        wb=SpreadsheetFile.import_xlsx(Blob.load(str(path)))
        for sheet in wb.worksheets.items:
            used=sheet.get_used_range()
            match=re.search(r'\$?([A-Z]+)\$?(\d+)',used.address)
            if not match:raise ValueError('Cannot parse source range '+used.address)
            first_row=int(match.group(2))
            sheet_rows=[[clean(v) for v in row] for row in used.values]
            if publication_year==2025 and sheet.name.strip() in ('Figure6','Figure7','10.3','10.5','Table18'):
                figures[sheet.name.strip()]=sheet_rows
            count=0
            for offset, cells in enumerate(sheet_rows):
                if not any(cells):continue
                records.append({'publication_year':publication_year,'source_file':name,
                  'sheet':sheet.name.strip(),'excel_row':first_row+offset,
                  'source_range':used.address,'values_json':json.dumps(cells,ensure_ascii=False),
                  'row_text':' | '.join(x for x in cells if x)})
                count+=1
            sheet_index.append({'publication_year':publication_year,'source_file':name,
                'sheet':sheet.name.strip(),'used_range':used.address,'nonempty_rows':count})
        print(f'Loaded {publication_year}: {len(list(wb.worksheets.items))} sheets')
    return records,sheet_index,figures

def extract_series(figure,label):
    """Get series by matched original label, NOT by assumed hard-coded values."""
    years=next((row for row in figure if sum(x in [str(y) for y in range(2019,2026)] for x in row)>=6),None)
    if years is None:raise ValueError('Cannot find year columns')
    index={i:int(x) for i,x in enumerate(years) if x in [str(y) for y in range(2019,2026)]}
    row=next((r for r in figure if r and label.lower() in r[0].lower()),None)
    if row is None:raise ValueError(f'Not found: {label}')
    return {y:float(row[i]) for i,y in index.items() if i<len(row) and row[i]}

def main():
    records,index,figures=read_workbooks()
    write_csv(OUT/'nisr_workbook_rows.csv',list(records[0]),records)
    write_csv(OUT/'sheet_inventory.csv',list(index[0]),index)
    fig7=figures['Figure7'];fig6=figures['Figure6']
    birth=extract_series(fig7,'Birth registration completeness')
    death=extract_series(fig7,'Death registration completeness')
    timely_birth=extract_series(fig6,'birth registered timely')
    timely_death=extract_series(fig6,'death registered timely')
    trends=[]
    for year in sorted(set(birth)&set(death)&set(timely_birth)&set(timely_death)):
        trends.append({'year':year,'birth_completeness_pct':birth[year],
             'death_completeness_pct':death[year],
             'completeness_gap_pp':round(birth[year]-death[year],3),
             'birth_timely_pct':round(timely_birth[year],3),
             'death_timely_pct':round(timely_death[year],3),
             'source_file':SOURCE_FILES[2025], 'completeness_sheet':'Figure7',
             'timeliness_sheet':'Figure6'})
    write_csv(OUT/'registration_trends_2019_2025.csv',list(trends[0]),trends)
    summary=figures['10.3']
    header=next(r for r in summary if r and r[0]=='Indicator')
    yearcols={i:int(v) for i,v in enumerate(header) if v.isdigit() and 2019<=int(v)<=2025}
    def get_summary(name):
        row=next((r for r in summary if r and r[0].strip()==name),None)
        if row is None:raise ValueError('Missing 10.3 indicator: '+name)
        return {year:float(row[i]) for i,year in yearcols.items()}
    registered=get_summary('Registered live births (number)')
    adjusted_rate=get_summary('Adjusted Crude birth rate (per 1,000 population)')
    birth_trend=[]
    previous=None
    for year in sorted(yearcols.values()):
        count=int(registered[year]);rate=adjusted_rate[year]
        birth_trend.append({'year':year,'registered_live_births':count,
            'adjusted_crude_birth_rate_per_1000':rate,
            'registered_births_yoy_change': '' if previous is None else count-previous,
            'registered_births_yoy_pct':'' if previous is None else round((count/previous-1)*100,2),
            'source_file':SOURCE_FILES[2025],'source_sheet':'10.3',
            'count_indicator':'Registered live births (number)',
            'rate_indicator':'Adjusted Crude birth rate (per 1,000 population)'})
        previous=count
    assert birth_trend[0]['registered_live_births']==313398
    assert birth_trend[-1]['registered_live_births']==356838
    assert birth_trend[0]['adjusted_crude_birth_rate_per_1000']==29.1
    assert birth_trend[-1]['adjusted_crude_birth_rate_per_1000']==27.2
    write_csv(OUT/'birth_trends_2019_2025.csv',list(birth_trend[0]),birth_trend)
    mortality=figures['10.5']
    mh=next(r for r in mortality if r and r[0]=='Indicator')
    myears={i:int(v) for i,v in enumerate(mh) if v.isdigit() and 2019<=int(v)<=2025}
    def mortality_series(label):
        row=next((r for r in mortality if r and r[0].strip()==label),None)
        if row is None:raise ValueError('Missing mortality measure: '+label)
        return {year:float(row[i]) for i,year in myears.items()}
    death_counts=mortality_series('Registered deaths (number)')
    death_rates=mortality_series('Crude death rate per 1,000 (Adjusted)')
    death_rows=[];prev=None
    for year in sorted(myears.values()):
        count=int(death_counts[year])
        death_rows.append({'year':year,'registered_deaths':count,'adjusted_crude_death_rate_per_1000':death_rates[year],
          'registered_deaths_yoy_change':'' if prev is None else count-prev,
          'registered_deaths_yoy_pct':'' if prev is None else round((count/prev-1)*100,2),
          'source_file':SOURCE_FILES[2025],'source_sheet':'10.5'})
        prev=count
    assert death_rows[0]['registered_deaths']==23791 and death_rows[-1]['registered_deaths']==39355
    write_csv(OUT/'death_trends_2019_2025.csv',list(death_rows[0]),death_rows)
    marriage_sheet=figures['Table18']
    marriage_rows=[];prev=None
    for r in marriage_sheet:
        if not r or not r[0].isdigit() or not (2019<=int(r[0])<=2025):continue
        year=int(r[0]);count=int(float(r[1]));rate=float(r[3])
        marriage_rows.append({'year':year,'registered_marriages':count,'crude_marriage_rate_per_1000':rate,
          'registered_marriages_yoy_change':'' if prev is None else count-prev,
          'registered_marriages_yoy_pct':'' if prev is None else round((count/prev-1)*100,2),
          'source_file':SOURCE_FILES[2025],'source_sheet':'Table18',
          'source_discrepancy':'2025 factsheet has 50,236' if year==2025 else ''})
        prev=count
    assert len(marriage_rows)==7 and marriage_rows[-1]['registered_marriages']==50256
    write_csv(OUT/'marriage_trends_2019_2025.csv',list(marriage_rows[0]),marriage_rows)


    catalog=[
      ('Registered live births',356838,'events','Birth Statistics Factsheet 2025','p. 1','Births occurring in 2025 registered in CRVS'),
      ('Registered deaths',39355,'events','Death & Cause of Death Statistics Factsheet 2025','p. 1','Deaths occurring and registered in 2025'),
      ('Registered marriages',50236,'events','Marriage & Divorce Statistics Factsheet 2025','p. 1','Marriages registered in CRVS'),
      ('Registered divorces',4479,'events','Marriage & Divorce Statistics Factsheet 2025','p. 1','Divorces recorded in CRVS; not a divorce rate'),
      ('Divorces granted and registered in 2025',2629,'events','Marriage & Divorce Statistics Factsheet 2025','p. 1','Subset of legally granted and registered divorces'),
      ('Live births in health facilities',97.8,'percent','Birth Statistics Factsheet 2025','p. 1','Of registered live births'),
      ('Births to adolescent mothers aged 10–19',8.5,'percent','Birth Statistics Factsheet 2025','p. 1','Of registered live births'),
      ('Total fertility rate',3.5,'births per woman','Birth Statistics Factsheet 2025','p. 1','Period total fertility rate'),
      ('Registered community deaths',55.9,'percent','Death & Cause of Death Statistics Factsheet 2025','p. 1','Of registered deaths'),
      ('Usable cause of death in facilities',82.3,'percent','Death & Cause of Death Statistics Factsheet 2025','p. 1','Of relevant certified facility deaths'),
      ('Usable cause of death in community',83.9,'percent','Death & Cause of Death Statistics Factsheet 2025','p. 1','Of relevant community causes'),
      ('Community of property marriages',97.0,'percent','Marriage & Divorce Statistics Factsheet 2025','p. 2','Of registered marriages'),
    ]
    indicators=[{'year':2025,'indicator':a,'value':b,'unit':c,'source_document':d,'page':e,'definition':f} for a,b,c,d,e,f in catalog]
    write_csv(OUT/'factsheet_indicators_2025.csv',list(indicators[0]),indicators)
    a=trends[-1]; prev=trends[-2]; base=trends[0]
    findings=[
      {'finding':'Birth registration completeness, 2025','value':a['birth_completeness_pct'],'unit':'percent','calculation':'2025 source series','source':'2025 workbook, Figure7'},
      {'finding':'Death registration completeness, 2025','value':a['death_completeness_pct'],'unit':'percent','calculation':'2025 source series','source':'2025 workbook, Figure7'},
      {'finding':'Completeness gap, 2025','value':a['completeness_gap_pp'],'unit':'percentage points','calculation':'birth completeness minus death completeness','source':'2025 workbook, Figure7'},
      {'finding':'Birth completeness change since 2019','value':round(a['birth_completeness_pct']-base['birth_completeness_pct'],2),'unit':'percentage points','calculation':'2025 minus 2019','source':'2025 workbook, Figure7'},
      {'finding':'Death completeness change since 2019','value':round(a['death_completeness_pct']-base['death_completeness_pct'],2),'unit':'percentage points','calculation':'2025 minus 2019','source':'2025 workbook, Figure7'},
      {'finding':'Birth completeness change from 2024','value':round(a['birth_completeness_pct']-prev['birth_completeness_pct'],2),'unit':'percentage points','calculation':'2025 minus 2024','source':'2025 workbook, Figure7'},
      {'finding':'Death completeness change from 2024','value':round(a['death_completeness_pct']-prev['death_completeness_pct'],2),'unit':'percentage points','calculation':'2025 minus 2024','source':'2025 workbook, Figure7'},
    ]
    write_csv(OUT/'dashboard_findings.csv',list(findings[0]),findings)
    assert len(trends)==7 and a['birth_completeness_pct']==92.9 and a['death_completeness_pct']==50.5
    assert a['completeness_gap_pp']==42.4
    report={'raw_rows':len(records),'source_sheets':len(index),'time_series_years':len(trends),
            'validation':'PASS','checks':['7 calendar years present','2025 births 92.9%','2025 deaths 50.5%','2025 gap 42.4 percentage points'],
            'limitations':['Some source sheets include formatted/empty ranges and mixed units; raw rows must be interpreted with sheet context',
               'Factsheet indicator catalog is transcribed, not independently derived from sheet cells',
               'Cross-year comparability depends on NISR definitions and revisions; latest 2025 workbook is used for historical trends', '2025 marriage count discrepancy: 50,256 in workbook Table18 versus 50,236 in 2025 marriage factsheet; chart preserves Table18']}
    (OUT/'validation_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig,ax=plt.subplots(figsize=(9,4.8))
        ax.plot([r['year'] for r in trends],[r['birth_completeness_pct'] for r in trends],marker='o',label='Birth registration')
        ax.plot([r['year'] for r in trends],[r['death_completeness_pct'] for r in trends],marker='o',label='Death registration')
        ax.set(ylabel='Registration completeness (%)',xlabel='Year',ylim=(0,100),title='Rwanda: registration completeness, 2019–2025')
        ax.legend(frameon=False);ax.spines[['top','right']].set_visible(False);fig.tight_layout()
        fig.savefig(OUT/'completeness_trend.png',dpi=180);plt.close(fig)
    except ImportError:
        print('matplotlib not installed; chart skipped')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
