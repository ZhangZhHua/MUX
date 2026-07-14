const INLINE_PATTERN = /(\*\*[^*]+\*\*|\*[^*]+\*)/g;

export function buildInlineText(value = '') {
  const text = String(value);
  const fragments = [];
  let cursor = 0;

  for (const match of text.matchAll(INLINE_PATTERN)) {
    if (match.index > cursor) {
      fragments.push({ text: text.slice(cursor, match.index) });
    }

    const token = match[0];
    if (token.startsWith('**')) {
      fragments.push({ text: token.slice(2, -2), bold: true });
    } else {
      fragments.push({ text: token.slice(1, -1), italics: true });
    }
    cursor = match.index + token.length;
  }

  if (cursor < text.length) {
    fragments.push({ text: text.slice(cursor) });
  }

  return fragments.length > 0 ? fragments : [{ text }];
}

function buildDivider() {
  return {
    canvas: [
      { type: 'line', x1: 0, y1: 2, x2: 511, y2: 2, lineWidth: 0.6, lineColor: '#d1d5db' }
    ],
    margin: [0, 5, 0, 7]
  };
}

export function buildMarkdownNodes(text = '', format = 'markdown') {
  if (!text) {
    return [{ text: 'No document description recorded.', style: 'empty' }];
  }

  if (format !== 'markdown') {
    return [{ text: String(text), style: 'paragraph', preserveLeadingSpaces: true }];
  }

  const nodes = [];
  const lines = String(text).split('\n');
  let listItems = [];

  const flushList = () => {
    if (listItems.length === 0) return;
    nodes.push({ ul: listItems, style: 'list' });
    listItems = [];
  };

  lines.forEach((line) => {
    const trimmed = line.trim();

    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      listItems.push({ text: buildInlineText(trimmed.slice(2)) });
      return;
    }

    flushList();

    if (!trimmed) {
      nodes.push({ text: ' ', fontSize: 3, margin: [0, 0, 0, 1] });
    } else if (trimmed === '---') {
      nodes.push(buildDivider());
    } else if (trimmed.startsWith('### ')) {
      nodes.push({ text: buildInlineText(trimmed.slice(4)), style: 'heading3' });
    } else if (trimmed.startsWith('## ')) {
      nodes.push({ text: buildInlineText(trimmed.slice(3)), style: 'heading2' });
    } else if (trimmed.startsWith('> ') || trimmed.startsWith('💡 ')) {
      nodes.push({
        table: {
          widths: ['*'],
          body: [[{
            text: buildInlineText(trimmed.replace(/^> |^💡 /, '')),
            style: 'quote',
            fillColor: '#fffdf5'
          }]]
        },
        layout: {
          hLineWidth: () => 0,
          vLineWidth: (index) => (index === 0 ? 2 : 0),
          vLineColor: () => '#d97706',
          paddingLeft: () => 8,
          paddingRight: () => 8,
          paddingTop: () => 2,
          paddingBottom: () => 2
        },
        margin: [0, 2, 0, 5]
      });
    } else {
      nodes.push({ text: buildInlineText(line), style: 'paragraph' });
    }
  });

  flushList();
  return nodes;
}
