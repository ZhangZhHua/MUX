import { readonly, shallowRef } from 'vue';
import { buildExperimentPdf } from '../features/pdf/buildExperimentPdf.js';
import { loadPdfImages } from '../features/pdf/loadPdfImages.js';
import { registerPdfFonts } from '../features/pdf/registerPdfFonts.js';

function formatDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function buildPdfFilename(title) {
  const safeTitle = String(title || 'experiment')
    .replace(/[\\/:*?"<>|]/g, '_')
    .substring(0, 80);
  return `${safeTitle}_${formatDate(new Date())}.pdf`;
}

export function usePdfExport() {
  const isExporting = shallowRef(false);
  const exportStatus = shallowRef('');

  const exportToPdf = async ({
    experiment,
    descriptionText = '',
    descriptionFormat = 'markdown',
    bulletins = [],
    steps = [],
    groupedLogColumns = [],
    contributorStats = [],
    allAttachments = [],
    apiBaseUrl = ''
  }) => {
    if (!experiment || isExporting.value) return;

    isExporting.value = true;
    exportStatus.value = 'Loading PDF engine...';

    try {
      const pdfMakeModule = await import('pdfmake/build/pdfmake');
      const pdfMake = pdfMakeModule.default || pdfMakeModule;

      exportStatus.value = 'Loading PDF fonts...';
      await registerPdfFonts(pdfMake);

      exportStatus.value = 'Preparing log images...';
      const imageAssets = await loadPdfImages(groupedLogColumns, ({ completed, total }) => {
        exportStatus.value = total > 0
          ? `Preparing log images ${completed}/${total}...`
          : 'Preparing PDF layout...';
      });

      exportStatus.value = 'Preparing PDF layout...';
      const docDefinition = buildExperimentPdf({
        experiment,
        descriptionText,
        descriptionFormat,
        bulletins,
        steps,
        groupedLogColumns,
        contributorStats,
        allAttachments,
        imageAssets,
        apiBaseUrl
      });

      exportStatus.value = 'Generating PDF...';
      await pdfMake.createPdf(docDefinition).download(buildPdfFilename(experiment.title));
    } catch (error) {
      console.error('[PDF Export] Failed:', error);
      throw error;
    } finally {
      exportStatus.value = '';
      isExporting.value = false;
    }
  };

  return {
    isExporting: readonly(isExporting),
    exportStatus: readonly(exportStatus),
    exportToPdf
  };
}
