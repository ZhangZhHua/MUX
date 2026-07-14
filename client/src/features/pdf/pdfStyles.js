export const PDF_FONT_FAMILY = 'NotoSansHans';
export const PDF_PAGE_WIDTH = 595.28;
export const PDF_PAGE_MARGIN = 42;
export const PDF_CONTENT_WIDTH = PDF_PAGE_WIDTH - (PDF_PAGE_MARGIN * 2);
export const PDF_IMAGE_MAX_HEIGHT = 500;

export const PDF_COLORS = {
  primary: '#4f46e5',
  primarySoft: '#eef2ff',
  text: '#1f2937',
  muted: '#6b7280',
  faint: '#9ca3af',
  border: '#e5e7eb',
  panel: '#f9fafb',
  warning: '#92400e',
  warningSoft: '#fef3c7',
  success: '#047857',
  successSoft: '#ecfdf5'
};

export const PDF_STYLES = {
  title: {
    fontSize: 20,
    bold: true,
    color: '#111827',
    lineHeight: 1.15
  },
  documentMeta: {
    fontSize: 8.5,
    color: PDF_COLORS.muted
  },
  sectionTitle: {
    fontSize: 13,
    bold: true,
    color: PDF_COLORS.text,
    margin: [0, 14, 0, 7]
  },
  heading2: {
    fontSize: 12,
    bold: true,
    color: PDF_COLORS.text,
    margin: [0, 8, 0, 4]
  },
  heading3: {
    fontSize: 10.5,
    bold: true,
    color: PDF_COLORS.text,
    margin: [0, 6, 0, 3]
  },
  paragraph: {
    fontSize: 9.5,
    color: PDF_COLORS.text,
    lineHeight: 1.4,
    margin: [0, 0, 0, 4]
  },
  quote: {
    fontSize: 9,
    color: PDF_COLORS.warning,
    lineHeight: 1.35,
    margin: [10, 4, 8, 6]
  },
  list: {
    fontSize: 9.5,
    color: PDF_COLORS.text,
    lineHeight: 1.35,
    margin: [10, 0, 0, 4]
  },
  tableHeader: {
    fontSize: 8.5,
    bold: true,
    color: '#374151'
  },
  tableCell: {
    fontSize: 8.5,
    color: PDF_COLORS.text
  },
  dateHeader: {
    fontSize: 11.5,
    bold: true,
    color: PDF_COLORS.primary,
    margin: [0, 10, 0, 5]
  },
  logMeta: {
    fontSize: 8.2,
    color: PDF_COLORS.muted
  },
  logBody: {
    fontSize: 9.5,
    color: PDF_COLORS.text,
    lineHeight: 1.4,
    margin: [0, 4, 0, 0]
  },
  attachment: {
    fontSize: 8.2,
    color: PDF_COLORS.muted,
    margin: [0, 4, 0, 0]
  },
  imageCaption: {
    fontSize: 8,
    color: PDF_COLORS.muted,
    alignment: 'center',
    margin: [0, 0, 0, 3]
  },
  imageError: {
    fontSize: 8,
    color: '#b91c1c',
    margin: [0, 3, 0, 0]
  },
  empty: {
    fontSize: 9,
    color: PDF_COLORS.faint,
    italics: true
  }
};
