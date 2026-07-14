import api from '../../services/api.js';
import { isPdfImageAttachment } from './imageTypes.js';

const MAX_IMAGE_WIDTH = 1600;
const MAX_IMAGE_HEIGHT = 1800;
const JPEG_QUALITY = 0.9;
const IMAGE_CONCURRENCY = 3;

export function collectPdfImageFilenames(groupedLogColumns = []) {
  const filenames = new Set();
  groupedLogColumns.forEach((column) => {
    (column.logs || []).forEach((log) => {
      (log.attachments || []).forEach((filename) => {
        if (isPdfImageAttachment(filename)) filenames.add(filename);
      });
    });
  });
  return [...filenames];
}

function loadHtmlImage(blob) {
  return new Promise((resolve, reject) => {
    const objectUrl = URL.createObjectURL(blob);
    const image = new Image();

    image.onload = () => resolve({ image, objectUrl });
    image.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      reject(new Error('The browser could not decode this image.'));
    };
    image.src = objectUrl;
  });
}

function calculateOutputSize(width, height) {
  const scale = Math.min(
    1,
    MAX_IMAGE_WIDTH / width,
    MAX_IMAGE_HEIGHT / height
  );
  return {
    width: Math.max(1, Math.round(width * scale)),
    height: Math.max(1, Math.round(height * scale))
  };
}

async function convertBlobToPdfImage(blob, filename) {
  const { image, objectUrl } = await loadHtmlImage(blob);
  try {
    const output = calculateOutputSize(image.naturalWidth, image.naturalHeight);
    const canvas = document.createElement('canvas');
    canvas.width = output.width;
    canvas.height = output.height;

    const context = canvas.getContext('2d', { alpha: true });
    if (!context) throw new Error('Canvas is unavailable for image conversion.');
    context.imageSmoothingEnabled = true;
    context.imageSmoothingQuality = 'high';

    const shouldUseJpeg = /\.jpe?g$/i.test(filename) || blob.type === 'image/jpeg';
    if (shouldUseJpeg) {
      context.fillStyle = '#ffffff';
      context.fillRect(0, 0, output.width, output.height);
    }
    context.drawImage(image, 0, 0, output.width, output.height);

    return {
      dataUrl: canvas.toDataURL(shouldUseJpeg ? 'image/jpeg' : 'image/png', JPEG_QUALITY),
      pixelWidth: output.width,
      pixelHeight: output.height
    };
  } finally {
    URL.revokeObjectURL(objectUrl);
  }
}

async function loadOnePdfImage(filename, index) {
  try {
    const response = await api.get(
      `/experiments/attachments/${encodeURIComponent(filename)}?preview=true`,
      { responseType: 'blob' }
    );
    const converted = await convertBlobToPdfImage(response.data, filename);
    return {
      filename,
      imageKey: `log-image-${index}`,
      ...converted,
      error: null
    };
  } catch (error) {
    return {
      filename,
      imageKey: null,
      dataUrl: null,
      pixelWidth: 0,
      pixelHeight: 0,
      error: error?.message || 'Image loading failed.'
    };
  }
}

export async function loadPdfImages(groupedLogColumns = [], onProgress = () => {}) {
  const filenames = collectPdfImageFilenames(groupedLogColumns);
  const results = new Array(filenames.length);
  let nextIndex = 0;
  let completed = 0;

  onProgress({ completed, total: filenames.length });

  async function worker() {
    while (nextIndex < filenames.length) {
      const index = nextIndex;
      nextIndex += 1;
      results[index] = await loadOnePdfImage(filenames[index], index);
      completed += 1;
      onProgress({ completed, total: filenames.length });
    }
  }

  const workerCount = Math.min(IMAGE_CONCURRENCY, filenames.length);
  await Promise.all(Array.from({ length: workerCount }, () => worker()));

  return new Map(results.map((result) => [result.filename, result]));
}
