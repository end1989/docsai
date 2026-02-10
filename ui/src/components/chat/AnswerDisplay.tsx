import { renderMarkdown } from '../../lib/markdown';

interface AnswerDisplayProps {
  answer: string;
  citations: string[];
}

export default function AnswerDisplay({ answer, citations }: AnswerDisplayProps) {
  const html = renderMarkdown(answer, citations);

  return (
    <div
      className="text-slate-300 leading-relaxed"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
