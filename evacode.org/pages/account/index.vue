<template>
  <div>
    <Header />
    <AccountShell current="orders">
      <div class="account-lux__tabs" role="tablist" aria-label="Заказы">
        <button
          type="button"
          class="account-lux__tab"
          :class="{ 'is-active': tab === 'current' }"
          role="tab"
          :aria-selected="tab === 'current'"
          @click="tab = 'current'"
        >
          Текущие
        </button>
        <button
          type="button"
          class="account-lux__tab"
          :class="{ 'is-active': tab === 'done' }"
          role="tab"
          :aria-selected="tab === 'done'"
          @click="tab = 'done'"
        >
          Завершенные
        </button>
      </div>

      <div v-if="loading" class="account-lux__status">
        Загружаем заказы…
      </div>
      <p v-else-if="loadError" class="account-lux__status">{{ loadError }}</p>
      <AccountEmpty
        v-else-if="!filteredOrders.length"
        icon="bag"
        :lead="tab === 'current' ? 'Текущих заказов нет' : 'Завершённых заказов нет'"
        text="Когда оформите, они появятся здесь."
        cta="В каталог"
        to="/collection/leftsidebar/0/"
      />
      <ul v-else class="account-lux__orders" aria-label="Список заказов">
        <li
          v-for="order in filteredOrders"
          :key="order.id"
          class="account-lux__order"
          :class="{ 'is-open': openId === order.id }"
        >
          <button
            type="button"
            class="account-lux__order-head"
            :aria-expanded="openId === order.id"
            @click="toggleOrder(order.id)"
          >
            <div class="account-lux__order-idblock">
              <p class="account-lux__order-id">Заказ №{{ orderNumber(order) }}</p>
              <p class="account-lux__order-meta">от {{ formatDateShort(order.paid_at || order.created_at) }}</p>
            </div>
            <span class="account-lux__order-status" :data-status="order.status">
              {{ order.status_label }}
            </span>
            <div class="account-lux__order-summary">
              <span>{{ itemsSummary(order) }}</span>
              <span class="account-lux__order-chevron" aria-hidden="true">
                <svg viewBox="0 0 20 20" fill="none">
                  <path d="M5 8l5 5 5-5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </span>
            </div>
          </button>

          <div v-if="openId === order.id" class="account-lux__order-body">
            <ul class="account-lux__order-lines">
              <li v-for="(item, index) in order.items" :key="`${order.id}-${index}`" class="account-lux__order-line">
                <div class="account-lux__order-thumb">
                  <img v-if="item.image" :src="item.image" :alt="item.title">
                </div>
                <div class="account-lux__order-line-info">
                  <p class="account-lux__order-line-title">{{ item.title }}</p>
                  <p class="account-lux__order-line-meta">Количество: {{ item.quantity }} шт.</p>
                </div>
                <p class="account-lux__order-line-price">{{ formatKrw(item.line_total_krw || item.price_krw) }}</p>
              </li>
            </ul>
            <button
              type="button"
              class="account-lux__order-help"
              @click="openHelp(order)"
            >
              Помощь с заказом
            </button>
          </div>
        </li>
      </ul>
    </AccountShell>
    <Footer />

    <Teleport to="body">
      <div
        v-if="helpOpen"
        class="account-lux-dialog"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="helpSuccess ? 'help-success-title' : 'help-form-title'"
      >
        <button class="account-lux-dialog__backdrop" type="button" aria-label="Закрыть" @click="closeHelp" />
        <div class="account-lux-dialog__card account-lux-dialog__card--help">
          <button class="account-lux-dialog__close" type="button" aria-label="Закрыть" @click="closeHelp">
            ×
          </button>
          <h3 :id="helpSuccess ? 'help-success-title' : 'help-form-title'" class="account-lux-dialog__title">
            Помощь с заказом №{{ helpOrderNumber }}
          </h3>

          <template v-if="helpSuccess">
            <p class="account-lux-dialog__lead">
              Ваше обращение успешно отправлено, наш менеджер свяжется с Вами в ближайшее время
            </p>
            <button class="account-lux__submit account-lux__submit--brand" type="button" @click="closeHelp">
              Вернуться к заказам
            </button>
          </template>

          <form v-else class="account-lux__help-form" @submit.prevent="onHelpSubmit">
            <p class="account-lux-dialog__section">Сообщение менеджеру</p>
            <CheckoutField
              v-model="helpPhone"
              label="Телефон для связи *"
              name="help_phone"
              type="tel"
              autocomplete="tel"
              :error="helpErrors.phone"
              :submitted="helpSubmitted"
            />
            <label class="account-lux__help-message">
              <span class="sr-only">Какой у Вас вопрос?</span>
              <textarea
                v-model="helpMessage"
                name="help_message"
                rows="5"
                placeholder="Какой у Вас вопрос? *"
                :class="{ 'is-invalid': helpSubmitted && helpErrors.message }"
              />
            </label>
            <p v-if="helpSubmitted && helpErrors.message" class="account-lux__error">{{ helpErrors.message }}</p>
            <p v-if="helpFormError" class="account-lux__error">{{ helpFormError }}</p>
            <button class="account-lux__submit account-lux__submit--brand" type="submit" :disabled="helpPending">
              {{ helpPending ? 'Отправляем…' : 'Отправить' }}
            </button>
          </form>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { accountErrorMessage, useAuthStore } from '~/store/auth'

definePageMeta({
  middleware: 'account-auth',
})

useHead({
  titleTemplate: '%s — Личный кабинет',
})
useNoIndex()

const CURRENT_STATUSES = new Set(['pending', 'paid'])
const DONE_STATUSES = new Set(['failed', 'cancelled'])

const auth = useAuthStore()
const orders = ref([])
const loading = ref(true)
const loadError = ref('')
const tab = ref('current')
const openId = ref('')

const helpOpen = ref(false)
const helpSuccess = ref(false)
const helpPending = ref(false)
const helpSubmitted = ref(false)
const helpOrder = ref(null)
const helpPhone = ref('')
const helpMessage = ref('')
const helpErrors = reactive({ phone: '', message: '' })
const helpFormError = ref('')

const filteredOrders = computed(() => {
  const statuses = tab.value === 'current' ? CURRENT_STATUSES : DONE_STATUSES
  return orders.value.filter((order) => statuses.has(order.status))
})

const helpOrderNumber = computed(() => {
  if (!helpOrder.value) {
    return ''
  }
  return orderNumber(helpOrder.value)
})

function orderNumber(order) {
  return order.business_ru_order_number || order.id
}

function formatDateShort(value) {
  if (!value) {
    return ''
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return ''
  }
  const day = String(date.getDate()).padStart(2, '0')
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const year = String(date.getFullYear()).slice(-2)
  return `${day}.${month}.${year}`
}

function formatKrw(value) {
  const amount = Number(value || 0)
  return `₩${new Intl.NumberFormat('ru-RU').format(amount)}`
}

function goodsWord(count) {
  const n = Math.abs(Number(count) || 0) % 100
  const n1 = n % 10
  if (n > 10 && n < 20) {
    return 'товаров'
  }
  if (n1 === 1) {
    return 'товар'
  }
  if (n1 >= 2 && n1 <= 4) {
    return 'товара'
  }
  return 'товаров'
}

function itemsSummary(order) {
  const count = Number(order.item_count || order.items?.reduce((sum, item) => sum + Number(item.quantity || 0), 0) || 0)
  return `${count} ${goodsWord(count)} на сумму ${formatKrw(order.amount_krw)}`
}

function toggleOrder(id) {
  openId.value = openId.value === id ? '' : id
}

function openHelp(order) {
  helpOrder.value = order
  helpSuccess.value = false
  helpPending.value = false
  helpSubmitted.value = false
  helpFormError.value = ''
  helpErrors.phone = ''
  helpErrors.message = ''
  helpMessage.value = ''
  helpPhone.value = String(auth.user?.phone || '').trim()
  helpOpen.value = true
}

function closeHelp() {
  helpOpen.value = false
  helpOrder.value = null
  helpSuccess.value = false
}

function validateHelp() {
  helpErrors.phone = helpPhone.value.trim() ? '' : 'Укажите телефон'
  helpErrors.message = helpMessage.value.trim().length >= 3 ? '' : 'Напишите вопрос'
  return !helpErrors.phone && !helpErrors.message
}

async function onHelpSubmit() {
  helpSubmitted.value = true
  helpFormError.value = ''
  if (!validateHelp() || !helpOrder.value || helpPending.value) {
    return
  }
  helpPending.value = true
  try {
    await auth.authFetch(`/market/orders/${helpOrder.value.id}/help/`, {
      method: 'POST',
      body: {
        phone: helpPhone.value.trim(),
        message: helpMessage.value.trim(),
      },
    })
    helpSuccess.value = true
  } catch (error) {
    const data = error?.data
    if (data?.errors) {
      helpErrors.phone = data.errors.phone || ''
      helpErrors.message = data.errors.message || ''
    }
    helpFormError.value = accountErrorMessage(error, 'Не удалось отправить обращение')
  } finally {
    helpPending.value = false
  }
}

async function loadOrders() {
  loading.value = true
  loadError.value = ''
  try {
    const data = await auth.authFetch('/market/orders/mine/')
    orders.value = Array.isArray(data?.results) ? data.results : []
    if (orders.value.length && !orders.value.some((order) => CURRENT_STATUSES.has(order.status))) {
      tab.value = 'done'
    }
  } catch (error) {
    orders.value = []
    loadError.value = accountErrorMessage(error, 'Не удалось загрузить заказы')
  } finally {
    loading.value = false
  }
}

onMounted(loadOrders)
</script>
