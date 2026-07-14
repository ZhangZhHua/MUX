import { buildMarkdownNodes } from './buildMarkdownNodes.js';
import {
  PDF_COLORS,
  PDF_CONTENT_WIDTH,
  PDF_FONT_FAMILY,
  PDF_IMAGE_MAX_HEIGHT,
  PDF_PAGE_MARGIN,
  PDF_STYLES
} from './pdfStyles.js';
import { isPdfImageAttachment } from './imageTypes.js';

const STATUS_COLORS = {
  running: '#059669',
  completed: '#4f46e5',
  paused: '#d97706',
  stopped: '#dc2626',
  archived: '#6b7280'
};

function asText(value, fallback = '') {
  if (value === null || value === undefined || value === '') return fallback;
  return String(value);
}

function formatDate(value) {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return asText(value);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function formatTime(value) {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return asText(value);
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hour = String(date.getHours()).padStart(2, '0');
  const minute = String(date.getMinutes()).padStart(2, '0');
  return `${month}-${day} ${hour}:${minute}`;
}

function truncateFilename(filename, maxLength = 72) {
  const value = asText(filename);
  if (value.length <= maxLength) return value;
  const extensionIndex = value.lastIndexOf('.');
  if (extensionIndex <= 0) return `${value.slice(0, maxLength - 3)}...`;
  const extension = value.slice(extensionIndex);
  const baseLength = Math.max(1, maxLength - extension.length - 3);
  return `${value.slice(0, baseLength)}...${extension}`;
}

function buildAbsoluteAttachmentUrl(apiBaseUrl, filename) {
  const origin = globalThis.location?.origin || 'http://localhost';
  const base = new URL(apiBaseUrl || '/api', origin);
  const normalizedBase = base.href.endsWith('/') ? base.href : `${base.href}/`;
  return new URL(`experiments/attachments/${encodeURIComponent(filename)}`, normalizedBase).href;
}

function buildSectionTitle(title) {
  return {
    stack: [
      { text: title, style: 'sectionTitle' },
      {
        canvas: [
          { type: 'line', x1: 0, y1: 0, x2: PDF_CONTENT_WIDTH, y2: 0, lineWidth: 0.6, lineColor: PDF_COLORS.border }
        ],
        margin: [0, -4, 0, 6]
      }
    ]
  };
}

function buildHeader(experiment, generatedDate) {
  const status = asText(experiment.status, 'unknown');
  const statusColor = STATUS_COLORS[status] || PDF_COLORS.muted;
  const tags = (experiment.tags || []).map((tag) => asText(tag?.name)).filter(Boolean).join(', ') || '-';

  return [
    {
      columns: [
        { text: asText(experiment.title, 'Untitled Experiment'), style: 'title', width: '*' },
        {
          text: status,
          color: '#ffffff',
          bold: true,
          fontSize: 8.5,
          alignment: 'center',
          background: statusColor,
          margin: [8, 4, 8, 4],
          width: 'auto'
        }
      ],
      columnGap: 10
    },
    {
      text: `Tags: ${tags}    Exported: ${generatedDate}`,
      style: 'documentMeta',
      margin: [0, 4, 0, 8]
    },
    {
      canvas: [
        { type: 'line', x1: 0, y1: 0, x2: PDF_CONTENT_WIDTH, y2: 0, lineWidth: 1.5, lineColor: PDF_COLORS.primary }
      ],
      margin: [0, 0, 0, 6]
    }
  ];
}

function buildBulletins(bulletins) {
  if (!bulletins.length) return [{ text: 'No bulletins.', style: 'empty' }];
  return bulletins.map((bulletin) => ({
    table: {
      widths: ['*'],
      body: [[{
        stack: [
          {
            text: `${formatTime(bulletin.created_at)}  ${asText(bulletin.author)}`.trim(),
            fontSize: 7.8,
            color: PDF_COLORS.warning
          },
          {
            text: asText(bulletin.text),
            fontSize: 9,
            color: '#78350f',
            lineHeight: 1.35,
            margin: [0, 2, 0, 0]
          }
        ],
        fillColor: PDF_COLORS.warningSoft
      }]]
    },
    layout: {
      hLineWidth: () => 0,
      vLineWidth: (index) => (index === 0 ? 2 : 0),
      vLineColor: () => '#d97706',
      paddingLeft: () => 8,
      paddingRight: () => 8,
      paddingTop: () => 6,
      paddingBottom: () => 6
    },
    margin: [0, 0, 0, 5]
  }));
}

function buildPersonnel(experiment, contributorStats) {
  const members = experiment.members || [];
  const nodes = [
    members.length
      ? { text: members.map((member) => `${asText(member.first_name)} ${asText(member.last_name)}`.trim()).join(', '), style: 'paragraph' }
      : { text: 'No personnel assigned.', style: 'empty' }
  ];

  if (contributorStats.length) {
    const body = [
      [
        { text: '#', style: 'tableHeader' },
        { text: 'Name', style: 'tableHeader' },
        { text: 'Logs', style: 'tableHeader', alignment: 'center' },
        { text: 'Attachments', style: 'tableHeader', alignment: 'center' },
        { text: 'Total', style: 'tableHeader', alignment: 'center' }
      ],
      ...contributorStats.map((item, index) => [
        { text: String(index + 1), style: 'tableCell' },
        { text: `${asText(item.user?.first_name)} ${asText(item.user?.last_name)}`.trim(), style: 'tableCell' },
        { text: String(item.logCount || 0), style: 'tableCell', alignment: 'center' },
        { text: String(item.attachmentCount || 0), style: 'tableCell', alignment: 'center' },
        { text: String(item.total || 0), style: 'tableCell', bold: true, alignment: 'center' }
      ])
    ];

    nodes.push({
      table: {
        headerRows: 1,
        widths: [22, '*', 62, 68, 44],
        body
      },
      layout: {
        fillColor: (rowIndex) => (rowIndex === 0 ? '#f3f4f6' : null),
        hLineColor: () => PDF_COLORS.border,
        vLineColor: () => PDF_COLORS.border,
        hLineWidth: () => 0.5,
        vLineWidth: () => 0.5,
        paddingLeft: () => 5,
        paddingRight: () => 5,
        paddingTop: () => 4,
        paddingBottom: () => 4
      },
      margin: [0, 5, 0, 0]
    });
  }

  return nodes;
}

function buildSteps(steps) {
  if (!steps.length) return [{ text: 'No operation steps.', style: 'empty' }];
  return steps.map((step) => ({
    text: `${step.is_completed ? '✓' : '□'} ${asText(step.title)}`,
    style: 'list',
    margin: [0, 1, 0, 1]
  }));
}

function buildAllAttachments(allAttachments, apiBaseUrl) {
  if (!allAttachments.length) return [{ text: 'No attachments.', style: 'empty' }];
  return allAttachments.map((item) => {
    const filename = asText(item.file);
    return {
      text: [
        { text: `${truncateFilename(filename)}  `, color: PDF_COLORS.text },
        {
          text: formatDate(item.log?.shift_date || item.log?.created_at),
          color: PDF_COLORS.faint
        }
      ],
      link: buildAbsoluteAttachmentUrl(apiBaseUrl, filename),
      style: 'attachment',
      decoration: 'underline',
      decorationColor: PDF_COLORS.faint
    };
  });
}

function buildImageNode(filename, imageAssets) {
  const asset = imageAssets.get(filename);
  if (!asset || asset.error || !asset.imageKey) {
    return {
      text: `${truncateFilename(filename)} (attachment unavailable; name retained)`,
      style: 'imageError'
    };
  }

  return {
    stack: [
      { text: truncateFilename(filename), style: 'imageCaption' },
      {
        image: asset.imageKey,
        fit: [PDF_CONTENT_WIDTH - 20, PDF_IMAGE_MAX_HEIGHT],
        alignment: 'center'
      }
    ],
    unbreakable: true,
    margin: [0, 6, 0, 7]
  };
}

function buildLogNode(log, imageAssets, apiBaseUrl) {
  const author = log.author
    ? `${asText(log.author.first_name)} ${asText(log.author.last_name)}`.trim()
    : 'Unknown';
  const participants = asText(log.participants);
  const attachments = log.attachments || [];
  const attachmentNodes = attachments.map((filename) => {
    if (isPdfImageAttachment(filename)) return buildImageNode(filename, imageAssets);
    return {
      text: truncateFilename(filename),
      link: buildAbsoluteAttachmentUrl(apiBaseUrl, filename),
      style: 'attachment',
      decoration: 'underline',
      decorationColor: PDF_COLORS.faint
    };
  });

  return {
    stack: [
      {
        canvas: [
          { type: 'line', x1: 0, y1: 0, x2: PDF_CONTENT_WIDTH, y2: 0, lineWidth: 0.5, lineColor: PDF_COLORS.border }
        ],
        margin: [0, 2, 0, 5]
      },
      {
        columns: [
          {
            text: `${author}${participants ? `  |  Operators: ${participants}` : ''}`,
            style: 'logMeta',
            width: '*'
          },
          {
            text: formatTime(log.shift_date || log.created_at),
            style: 'logMeta',
            alignment: 'right',
            width: 'auto'
          }
        ],
        columnGap: 8
      },
      { text: asText(log.content), style: 'logBody' },
      ...attachmentNodes
    ],
    margin: [0, 0, 0, 9]
  };
}

function buildLogs(groupedLogColumns, imageAssets, apiBaseUrl) {
  if (!groupedLogColumns.length) {
    return [{ text: 'No log entries.', style: 'empty' }];
  }

  return groupedLogColumns.flatMap((column) => {
    const logs = column.logs || [];
    return [
      {
        text: `${asText(column.date)}  |  ${logs.length} ${logs.length === 1 ? 'entry' : 'entries'}`,
        style: 'dateHeader',
        headlineLevel: 1
      },
      ...logs.map((log) => buildLogNode(log, imageAssets, apiBaseUrl))
    ];
  });
}

function buildImagesDictionary(imageAssets) {
  const images = {};
  imageAssets.forEach((asset) => {
    if (!asset.error && asset.imageKey && asset.dataUrl) {
      images[asset.imageKey] = asset.dataUrl;
    }
  });
  return images;
}

export function buildExperimentPdf({
  experiment,
  descriptionText = '',
  descriptionFormat = 'markdown',
  bulletins = [],
  steps = [],
  groupedLogColumns = [],
  contributorStats = [],
  allAttachments = [],
  imageAssets = new Map(),
  apiBaseUrl = ''
}) {
  const generatedDate = formatDate(new Date().toISOString());
  const content = [
    ...buildHeader(experiment, generatedDate),
    buildSectionTitle('Experiment Description'),
    ...buildMarkdownNodes(descriptionText, descriptionFormat),
    buildSectionTitle('Current Task'),
    {
      table: {
        widths: ['*'],
        body: [[{
          text: asText(experiment.current_task, '-'),
          fontSize: 9.5,
          color: PDF_COLORS.success,
          fillColor: PDF_COLORS.successSoft,
          margin: [7, 5, 7, 5]
        }]]
      },
      layout: 'noBorders'
    },
    buildSectionTitle('Bulletins'),
    ...buildBulletins(bulletins),
    buildSectionTitle('Personnel and Contributions'),
    ...buildPersonnel(experiment, contributorStats),
    buildSectionTitle('Operation Steps'),
    ...buildSteps(steps),
    buildSectionTitle('All Attachments'),
    ...buildAllAttachments(allAttachments, apiBaseUrl),
    buildSectionTitle('Log Entries (Newest First)'),
    ...buildLogs(groupedLogColumns, imageAssets, apiBaseUrl)
  ];

  return {
    pageSize: 'A4',
    pageOrientation: 'portrait',
    pageMargins: [PDF_PAGE_MARGIN, 46, PDF_PAGE_MARGIN, 46],
    defaultStyle: {
      font: PDF_FONT_FAMILY,
      fontSize: 9.5,
      color: PDF_COLORS.text,
      lineHeight: 1.35
    },
    styles: PDF_STYLES,
    images: buildImagesDictionary(imageAssets),
    info: {
      title: asText(experiment.title, 'Experiment Export'),
      subject: 'MUX experiment record export',
      author: 'MUX Physics Lab Log',
      creator: 'MUX Physics Lab Log',
      producer: 'pdfmake'
    },
    header: (currentPage) => ({
      text: currentPage > 1 ? asText(experiment.title, 'Experiment Export') : '',
      font: PDF_FONT_FAMILY,
      fontSize: 7.5,
      color: PDF_COLORS.faint,
      margin: [PDF_PAGE_MARGIN, 20, PDF_PAGE_MARGIN, 0]
    }),
    footer: (currentPage, pageCount) => ({
      columns: [
        { text: `Generated by MUX - ${generatedDate}`, alignment: 'left' },
        { text: `${currentPage} / ${pageCount}`, alignment: 'right' }
      ],
      font: PDF_FONT_FAMILY,
      fontSize: 7.5,
      color: PDF_COLORS.faint,
      margin: [PDF_PAGE_MARGIN, 0, PDF_PAGE_MARGIN, 18]
    }),
    pageBreakBefore: (currentNode, nodeContainer) => (
      currentNode.style === 'dateHeader'
      && typeof nodeContainer?.getFollowingNodesOnPage === 'function'
      && nodeContainer.getFollowingNodesOnPage().length === 0
    ),
    content
  };
}
