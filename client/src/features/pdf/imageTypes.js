const IMAGE_EXTENSION_PATTERN = /\.(png|jpe?g|gif|webp|bmp)$/i;

export function isPdfImageAttachment(filename = '') {
  return IMAGE_EXTENSION_PATTERN.test(String(filename));
}
