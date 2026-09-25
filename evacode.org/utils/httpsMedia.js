/** Force https for same-origin media URLs built by Django behind a plain proxy. */
export function httpsMedia(url) {
  if (!url) {
    return ''
  }
  return String(url).replace(/^http:\/\/(www\.)?evacode\.org/i, 'https://www.evacode.org')
}
