export function useHandoff() {
  const open = useState('app-handoff-open', () => false)
  const title = useState('app-handoff-title', () => '')
  const note = useState('app-handoff-note', () => '')
  const variant = useState('app-handoff-variant', () => 'default')

  function showHandoff(options = {}) {
    title.value = options.title || ''
    note.value = options.note || ''
    variant.value = options.variant || 'default'
    open.value = true
  }

  function hideHandoff() {
    open.value = false
  }

  async function withHandoff(options, fn) {
    showHandoff(options)
    try {
      return await fn()
    } catch (error) {
      hideHandoff()
      throw error
    }
  }

  return {
    open,
    title,
    note,
    variant,
    showHandoff,
    hideHandoff,
    withHandoff,
  }
}
