import React, {useMemo} from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

// Sources point to individual lines of the publicly published *processed* CSV.
const SOURCE_BASE = 'https://github.com/chuloezi/Ctrl-Freaks-Infographic-Dashboard/blob/main/data/processed/';
const CITATION = /\[(CSV\d+)\]/g;

function sourceUrl(source) {
  const name = String(source?.file || '');
  const line = Number(source?.csv_line);
  if (!/^[\w.-]+\.csv$/.test(name) || !Number.isSafeInteger(line) || line < 1) return null;
  return `${SOURCE_BASE}${encodeURIComponent(name)}#L${line}`;
}

export default function RagAnswer({answer, sources=[], mode=''}) {
  const validSources = useMemo(() => {
    const citedIds = new Set(Array.from(String(answer || '').matchAll(/\[(CSV\d+)\]/g), m => m[1]));
    return (Array.isArray(sources) ? sources : [])
      .filter(s => citedIds.has(s?.id) && /^CSV\d+$/.test(String(s?.id)) && sourceUrl(s));
  }, [answer, sources]);
  const byId = useMemo(() => new Map(validSources.map(s => [s.id, s])), [validSources]);
  const text = useMemo(() => String(answer || '').replace(CITATION, (original, id) => {
    const source = byId.get(id);
    // Missing/invalid metadata stays visibly uncoupled, not linked to a guess.
    return source ? `[${id}](${sourceUrl(source)})` : original;
  }), [answer, byId]);
  const isSourceLink = url => typeof url === 'string' && url.startsWith(SOURCE_BASE)
    && /^https:\/\/github\.com\/chuloezi\/Ctrl-Freaks-Infographic-Dashboard\/blob\/main\/data\/processed\/[\w.%-]+\.csv#L\d+$/.test(url);
  const modeLabel = mode === 'gemini_csv_rag' ? 'Gemini answer · CSV source IDs checked'
    : mode === 'citation_validation_fallback' ? 'Verified CSV fallback · citation check'
    : mode === 'csv_retrieval_only' ? 'CSV fallback · Gemini unavailable'
    : mode === 'insufficient_data' ? 'Insufficient CSV evidence'
    : mode === 'loading' ? 'Retrieving evidence'
    : mode === 'error' ? 'Connection unavailable' : '';

  return <div className="rag-output">
    <div className="rag-response">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={{
        a: ({href, children}) => isSourceLink(href)
          ? <a className="rag-inline-cite" href={href} target="_blank" rel="noopener noreferrer"
              aria-label={`Open source ${String(children).replace(/[\[\]]/g, '')} in GitHub`}>{children}</a>
          : <span>{children}</span>,
      }}>{text}</ReactMarkdown>
    </div>
    {validSources.length > 0 && <details className="rag-source-panel">
      <summary>View CSV sources ({validSources.length})</summary>
      <ul>
        {validSources.map(source => <li key={`${source.id}-${source.csv_line}`}>
          <a href={sourceUrl(source)} target="_blank" rel="noopener noreferrer">
            <span className="rag-source-id">{source.id}</span> {source.file}, line {source.csv_line}
          </a>
        </li>)}
      </ul>
    </details>}
    {modeLabel && <div className="rag-mode">{modeLabel}</div>}
  </div>;
}
