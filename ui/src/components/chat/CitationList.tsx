interface CitationListProps {
  citations: string[];
}

export default function CitationList({ citations }: CitationListProps) {
  if (citations.length === 0) return null;

  return (
    <div className="mt-3 pt-3 border-t border-panel-border">
      <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Sources</p>
      <ul className="space-y-1">
        {citations.map((url, i) => (
          <li key={i} className="text-sm">
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent hover:underline"
            >
              [{i + 1}] {url}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
