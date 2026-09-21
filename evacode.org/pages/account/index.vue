<template>
  <div>
    <Header />
    <AccountShell current="orders">
      <h2 class="account-lux__heading">Заказы</h2>
      <div v-if="loading" class="account-lux__status">
        Загружаем заказы…
      </div>
      <p v-else-if="loadError" class="account-lux__status">{{ loadError }}</p>
      <AccountEmpty
        v-else-if="!orders.length"
        icon="bag"
        lead="Заказов пока нет"
        text="Когда оформите, они появятся здесь."
        cta="В каталог"
        to="/collection/leftsidebar/0/"
      />
      <ul v-else class="account-lux__orders" aria-label="Список заказов">
        <li v-for="order in orders" :key="order.id" class="account-lux__order">
          <div class="account-lux__order-top">
            <p class="account-lux__order-id">
              Заказ {{ order.business_ru_order_number || order.id }}
            </p>
            <p class="account-lux__order-status" :data-status="order.status">
              {{ order.status_label }}
            </p>
          </div>
          <p class="account-lux__order-meta">
            {{ formatDate(order.paid_at || order.created_at) }}
            <span v-if="order.paypal_mode === 'sandbox'"> · тест sandbox</span>
          </p>
          <ul class="account-lux__order-items">
            <li v-for="(item, index) in order.items" :key="`${order.id}-${index}`">
              {{ item.title }}
              <span>× {{ item.quantity }}</span>
            </li>
          </ul>
          <p class="account-lux__order-total">
            {{ formatKrw(order.amount_krw) }}
            <span v-if="order.amount_usd"> / ${{ order.amount_usd }}</span>
          </p>
        </li>
      </ul>
    </AccountShell>
    <Footer />
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

const auth = useAuthStore()
const orders = ref([])
const loading = ref(true)
const loadError = ref('')

function formatDate(value) {
  if (!value) {
    return ''
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return ''
  }
  return new Intl.DateTimeFormat('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(date)
}

function formatKrw(value) {
  const amount = Number(value || 0)
  return `${new Intl.NumberFormat('ru-RU').format(amount)} ₩`
}

async function loadOrders() {
  loading.value = true
  loadError.value = ''
  try {
    const data = await $fetch(`${useRuntimeConfig().public.apiBase}/market/orders/mine/`, {
      headers: auth.authHeader(),
    })
    orders.value = Array.isArray(data?.results) ? data.results : []
  } catch (error) {
    orders.value = []
    loadError.value = accountErrorMessage(error, 'Не удалось загрузить заказы')
  } finally {
    loading.value = false
  }
}

onMounted(loadOrders)
</script>
