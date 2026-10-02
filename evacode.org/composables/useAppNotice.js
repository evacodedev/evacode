const NOTICE_MS = 3200

let noticeTimer = null
let confirmResolve = null

export function useAppNotice() {
  const notice = useState('app-notice', () => ({ id: 0, text: '' }))
  const confirmState = useState('app-confirm', () => ({
    open: false,
    title: '',
    text: '',
    confirmLabel: 'Да',
    cancelLabel: 'Отмена',
    danger: false,
  }))

  function notify(text) {
    notice.value = { id: notice.value.id + 1, text }
    clearTimeout(noticeTimer)
    noticeTimer = setTimeout(() => {
      notice.value = { ...notice.value, text: '' }
    }, NOTICE_MS)
  }

  function confirmAction(options = {}) {
    confirmResolve?.(false)
    confirmState.value = {
      open: true,
      title: options.title || 'Вы уверены?',
      text: options.text || '',
      confirmLabel: options.confirmLabel || 'Да',
      cancelLabel: options.cancelLabel || 'Отмена',
      danger: Boolean(options.danger),
    }
    return new Promise((resolve) => {
      confirmResolve = resolve
    })
  }

  function settleConfirm(result) {
    confirmState.value = { ...confirmState.value, open: false }
    const resolve = confirmResolve
    confirmResolve = null
    resolve?.(Boolean(result))
  }

  return { notice, confirmState, notify, confirmAction, settleConfirm }
}
