export function consultantOrderState(order) {
  if (!order) return 'draft'
  if (order.is_draft) {
    if (consultantOrderReady(order)) return 'ready'
    if (order.paid_krw > 0) return 'partial'
    return order.sent_to_client_at ? 'awaiting' : 'draft'
  }
  if (order.business_ru_error) return 'error'
  if (order.exporting) return 'exporting'
  return order.underpaid_krw ? 'debt' : 'done'
}

export function consultantOrderReady(order) {
  return Boolean(order?.is_draft && order.amount_krw > 0 && order.paid_krw >= order.amount_krw)
}

const LABELS = {
  draft: 'Черновик',
  awaiting: 'Ждёт оплату',
  ready: 'Можно оформить',
  partial: 'Частично оплачен',
  exporting: 'Передаётся в EvaCode',
  error: 'Ошибка передачи',
  debt: 'Заказ у EvaCode, есть долг',
  done: 'Заказ у EvaCode',
}

export function consultantOrderLabel(order) {
  return LABELS[consultantOrderState(order)]
}

export const CONSULTANT_TABS = [
  { id: 'drafts', label: 'Черновики' },
  { id: 'awaiting', label: 'Жду оплаты' },
  { id: 'placed', label: 'Заказы у EvaCode' },
]

export function consultantOrderTab(order) {
  if (!order?.is_draft) return 'placed'
  return order.sent_to_client_at || order.paid_krw > 0 ? 'awaiting' : 'drafts'
}
