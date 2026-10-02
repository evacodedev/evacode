// Nginx на проде принимает тело запроса до 1 МБ: фото оплаты ужимаем в браузере.
export const PROOF_UPLOAD_LIMIT = 950 * 1024
const MAX_SIDE = 1800

function loadImage(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file)
    const img = new Image()
    img.onload = () => {
      URL.revokeObjectURL(url)
      resolve(img)
    }
    img.onerror = () => {
      URL.revokeObjectURL(url)
      reject(new Error('decode'))
    }
    img.src = url
  })
}

function canvasBlob(canvas, quality) {
  return new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', quality))
}

function jpegName(name) {
  const base = String(name || 'payment').replace(/\.[^.]+$/, '')
  return `${base || 'payment'}.jpg`
}

/** Возвращает File не больше PROOF_UPLOAD_LIMIT или бросает Error с текстом для консультанта. */
export async function prepareProofFile(file) {
  if (!file) {
    throw new Error('Приложите фото подтверждения оплаты')
  }
  const type = String(file.type || '').toLowerCase()
  if (type === 'application/pdf') {
    if (file.size > PROOF_UPLOAD_LIMIT) {
      throw new Error('PDF больше 950 КБ. Приложите скриншот оплаты вместо PDF.')
    }
    return file
  }
  if (!type.startsWith('image/')) {
    throw new Error('Нужна картинка (JPG, PNG, WEBP) или PDF')
  }
  let img
  try {
    img = await loadImage(file)
  } catch {
    if (file.size <= PROOF_UPLOAD_LIMIT) {
      return file
    }
    throw new Error('Не удалось прочитать фото. Сделайте скриншот и приложите его.')
  }
  if (file.size <= PROOF_UPLOAD_LIMIT && type !== 'image/heic' && type !== 'image/heif') {
    return file
  }
  let side = MAX_SIDE
  for (let attempt = 0; attempt < 6; attempt += 1) {
    const scale = Math.min(1, side / Math.max(img.naturalWidth, img.naturalHeight))
    const canvas = document.createElement('canvas')
    canvas.width = Math.max(1, Math.round(img.naturalWidth * scale))
    canvas.height = Math.max(1, Math.round(img.naturalHeight * scale))
    const ctx = canvas.getContext('2d')
    ctx.fillStyle = '#fff'
    ctx.fillRect(0, 0, canvas.width, canvas.height)
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
    const blob = await canvasBlob(canvas, attempt < 3 ? 0.82 : 0.7)
    if (blob && blob.size <= PROOF_UPLOAD_LIMIT) {
      return new File([blob], jpegName(file.name), { type: 'image/jpeg' })
    }
    side = Math.round(side * 0.75)
  }
  throw new Error('Фото слишком большое даже после сжатия. Приложите скриншот.')
}
