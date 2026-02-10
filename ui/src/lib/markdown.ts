/**
 * Lightweight markdown-to-HTML renderer for LLM answers.
 * Handles: code blocks, inline code, headers, bold, italic, lists, citation links [n].
 */
export function renderMarkdown(text: string, citations: string[] = []): string {
  let html = escapeHtml(text);

  // Code blocks: ```lang\n...\n```
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_m, lang, code) => {
    const cls = lang ? ` class="language-${lang}"` : '';
    return `<pre class="code-block"><code${cls}>${code.trim()}</code></pre>`;
  });

  // Inline code: `...`
  html = html.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');

  // Headers
  html = html.replace(/^#### (.+)$/gm, '<h4 class="md-h4">$1</h4>');
  html = html.replace(/^### (.+)$/gm, '<h3 class="md-h3">$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2 class="md-h2">$1</h2>');

  // Bold and italic
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

  // Citation references: [n] -> clickable links
  html = html.replace(/\[(\d+)\]/g, (_m, num) => {
    const idx = parseInt(num, 10) - 1;
    if (idx >= 0 && idx < citations.length) {
      return `<a href="${escapeHtml(citations[idx])}" target="_blank" rel="noopener" class="citation-link">[${num}]</a>`;
    }
    return `<span class="citation-ref">[${num}]</span>`;
  });

  // Bullet lists
  html = html.replace(/^- (.+)$/gm, '<li class="md-li">$1</li>');
  html = html.replace(/(<li class="md-li">.*<\/li>\n?)+/g, (block) =>
    `<ul class="md-ul">${block}</ul>`
  );

  // Paragraphs
  html = html.replace(/\n\n/g, '</p><p class="md-p">');
  html = `<p class="md-p">${html}</p>`;
  html = html.replace(/(?<!\>)\n(?!\<)/g, '<br>');
  html = html.replace(/<p class="md-p"><\/p>/g, '');

  return html;
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
