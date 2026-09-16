const MAX_IMAGE_BYTES = 5 * 1024 * 1024
const ALLOWED_IMAGE_TYPES = new Set(['image/jpeg', 'image/png', 'image/webp'])

export const IMAGE_ACCEPT = 'image/jpeg,image/png,image/webp'
export const RECEIPT_ACCEPT = `${IMAGE_ACCEPT},application/pdf`

export function readImageDataUrl(file: File): Promise<string> {
  if (!ALLOWED_IMAGE_TYPES.has(file.type)) {
    return Promise.reject(new Error('Use uma imagem PNG, JPEG ou WebP.'))
  }
  if (file.size > MAX_IMAGE_BYTES) {
    return Promise.reject(new Error('A imagem deve ter no máximo 5 MB.'))
  }

  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onerror = () => reject(new Error('Não foi possível ler a imagem selecionada.'))
    reader.onload = () => resolve(String(reader.result))
    reader.readAsDataURL(file)
  })
}

export function readReceiptDataUrl(file: File): Promise<string> {
  if (![...ALLOWED_IMAGE_TYPES, 'application/pdf'].includes(file.type)) {
    return Promise.reject(new Error('Use PDF, PNG, JPEG ou WebP.'))
  }
  if (file.size > MAX_IMAGE_BYTES) {
    return Promise.reject(new Error('O comprovante deve ter no máximo 5 MB.'))
  }
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onerror = () => reject(new Error('Não foi possível ler o comprovante.'))
    reader.onload = () => resolve(String(reader.result))
    reader.readAsDataURL(file)
  })
}
