"""Test the chatbot with questions whose answers are known from the workbook.

Offline (no key, no quota):  python backend/eval_questions.py
Against a running service:   python backend/eval_questions.py --url https://YOUR-SERVICE.onrender.com

The offline run checks retrieval and calculated facts. The --url run makes one
Gemini request per question, spaced out to respect the free-tier limit, and
checks the answer text, so run it sparingly.
"""
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

# (question, values that must appear, values that must not appear)
QUESTIONS = [
    ('How many registered births were there in 2025?', ['356838|356,838'], []),
    ('How many babies were born in 2025?', ['356838|356,838'], []),
    ('What was the birth count in 2019?', ['313398|313,398'], []),
    ('How many people died in 2025?', ['39355|39,355'], []),
    ('How many registered deaths were there in 2024?', ['36021|36,021'], []),
    ('How many marriages were registered in 2025?', ['50256|50,256'], []),
    ('How many couples married in 2023?', ['57880|57,880'], []),
    ('How did registered deaths change between 2019 and 2025?', ['15564|15,564'], []),
    ('How did deaths change since 2019?', ['15564|15,564'], []),
    ('Compare births and deaths in 2025', ['356838|356,838', '39355|39,355'], []),
    ('What is the gap between birth and death registration completeness in 2025?', ['42.4'], []),
    ('What do we know about adolescent mothers?', ['8.5'], []),
    ('What are the leading causes of death?', ['perinatal', 'cardiac'], []),
    ('Which province has the most registered divorces?', ['1199|1,199|1185|1,185'], ['1820', '1,820']),
    ('How many divorces were registered in 2025?', ['4479|4,479'], []),
]
# The service must not answer these from outside knowledge.
OFF_TOPIC = [
    ('What is the capital of France?', ['Paris']),
    ('Who won the 2022 football World Cup?', ['Argentina']),
]


def has(text, alternatives):
    return any(option in text for option in alternatives.split('|'))


def offline_evidence(question):
    import rag_server
    facts = rag_server.numeric_evidence(question)
    return json.dumps(facts) + ' ' + ' '.join(d['text'] for d in rag_server.retrieve(question))


def offline_fact_values(text):
    # Calculated facts are floats such as 356838.0; retrieval text is unchanged.
    return text.replace('.0,', ',').replace('.0}', '}')


def ask_service(url, question):
    request = urllib.request.Request(
        url.rstrip('/') + '/api/ask', data=json.dumps({'question': question}).encode(),
        headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.load(response)


def run_offline():
    os.environ.pop('GEMINI_API_KEY', None)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    failures = 0
    for question, required, forbidden in QUESTIONS:
        text = offline_fact_values(offline_evidence(question))
        missing = [r for r in required if not has(text, r)]
        banned = [f for f in forbidden if f in text]
        if missing or banned:
            failures += 1
            print(f'FAIL  {question}\n      missing {missing}; forbidden {banned}')
        else:
            print(f'ok    {question}')
    import rag_server
    fallback = rag_server.answer('How many registered births were there in 2025?')
    if fallback['mode'] != 'csv_retrieval_only' or not fallback['sources']:
        failures += 1
        print('FAIL  fallback without a key should return cited CSV rows, got', fallback['mode'])
    else:
        print('ok    fallback without a key returns cited CSV rows')
    return failures


def run_service(url):
    failures = 0
    checks = [(q, req, forb) for q, req, forb in QUESTIONS] + [(q, [], forb) for q, forb in OFF_TOPIC]
    for question, required, forbidden in checks:
        try:
            result = ask_service(url, question)
        except OSError as exc:
            failures += 1
            print(f'FAIL  {question}\n      request failed: {exc}')
            continue
        text = result.get('answer', '')
        missing = [r for r in required if not has(text, r)]
        banned = [f for f in forbidden if f in text]
        mode = result.get('mode')
        failed = missing or banned or (required and mode != 'gemini_csv_rag')
        failures += bool(failed)
        print(f"{'FAIL' if failed else 'ok  '}  [{mode}] {question}")
        print('      ' + ' '.join(text.split())[:260])
        if missing or banned:
            print(f'      missing {missing}; forbidden {banned}')
        time.sleep(7)
    return failures


if __name__ == '__main__':
    failed = run_service(sys.argv[2]) if sys.argv[1:2] == ['--url'] else run_offline()
    print(f'{failed} failed')
    sys.exit(1 if failed else 0)
