import regularFontUrl from '@pdf-font-regular';
import boldFontUrl from '@pdf-font-bold';
import { PDF_FONT_FAMILY } from './pdfStyles.js';

let registeredPdfMake = null;
let fontDataPromise = null;

const FONT_FILES = {
  regular: 'NotoSansHans-Regular.otf',
  bold: 'NotoSansHans-Bold.otf'
};

function assertFontResponse(response, label) {
  if (!response.ok) {
    throw new Error(`${label} PDF font failed to load (${response.status}).`);
  }
}

function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result || '');
      const separatorIndex = result.indexOf(',');
      if (separatorIndex < 0) {
        reject(new Error('PDF font could not be encoded.'));
        return;
      }
      resolve(result.slice(separatorIndex + 1));
    };
    reader.onerror = () => reject(reader.error || new Error('PDF font could not be read.'));
    reader.readAsDataURL(blob);
  });
}

async function fetchFontAsBase64(url, label) {
  const response = await fetch(url);
  assertFontResponse(response, label);
  const blob = await response.blob();
  if (!blob.size) throw new Error(`${label} PDF font is empty.`);
  return blobToBase64(blob);
}

export async function registerPdfFonts(pdfMake) {
  if (registeredPdfMake === pdfMake) return;

  if (!fontDataPromise) {
    fontDataPromise = Promise.all([
      fetchFontAsBase64(regularFontUrl, 'Regular'),
      fetchFontAsBase64(boldFontUrl, 'Bold')
    ]).catch((error) => {
      fontDataPromise = null;
      throw error;
    });
  }

  const [regularFontData, boldFontData] = await fontDataPromise;
  pdfMake.addVirtualFileSystem({
    [FONT_FILES.regular]: { data: regularFontData, encoding: 'base64' },
    [FONT_FILES.bold]: { data: boldFontData, encoding: 'base64' }
  });
  pdfMake.addFonts({
    [PDF_FONT_FAMILY]: {
      normal: FONT_FILES.regular,
      bold: FONT_FILES.bold,
      italics: FONT_FILES.regular,
      bolditalics: FONT_FILES.bold
    }
  });
  registeredPdfMake = pdfMake;
  fontDataPromise = null;
}
