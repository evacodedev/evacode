<template>
  <div>
    <Header />
    <AccountShell current="consultant">
      <div class="consultant-head">
        <div class="account-lux__tabs" role="tablist" aria-label="Заказы клиентов">
          <button
            v-for="item in CONSULTANT_TABS"
            :key="item.id"
            type="button"
            class="account-lux__tab"
            :class="{ 'is-active': tab === item.id }"
            role="tab"
            :aria-selected="tab === item.id"
            @click="selectTab(item.id)"
          >
            {{ item.label }}<span v-if="counts[item.id]" class="account-lux__tab-count">{{ counts[item.id] }}</span>
          </button>
        </div>
        <nuxt-link to="/account/consultant/new/" class="consultant-btn consultant-btn--primary">
          Новый заказ
        </nuxt-link>
      </div>

      <ul v-if="loading" class="consultant-list" aria-hidden="true">
        <li v-for="n in 3" :key="n" class="consultant-row consultant-row--skeleton">
          <span class="skeleton-block consultant-row__skeleton" />
          <span class="skeleton-block consultant-row__skeleton consultant-row__skeleton--short" />
        </li>
      </ul>
      <p v-else-if="loadError" class="account-lux__status">{{ loadError }}</p>
      <AccountEmpty
        v-else-if="!filtered.length"
        icon="bag"
        :lead="EMPTY[tab].lead"
        :text="EMPTY[tab].text"
        cta="Новый заказ"
        to="/account/consultant/new/"
      />
      <ul v-else class="consultant-list" aria-label="Заказы">
        <li v-for="order in filtered" :key="order.id">
          <nuxt-link
            :to="`/account/consultant/${order.id}/`"
            class="consultant-row"
            :class="{ 'is-ready': consultantOrderReady(order) }"
          >
            <div class="consultant-row__main">
              <p class="consultant-row__title">
                {{ order.client_name || 'Без имени' }}
                <span v-if="order.business_ru_order_number" class="consultant-row__number">
                  №{{ order.business_ru_order_number }}
                </span>
              </p>
              <p class="consultant-row__meta">
                {{ formatDate(order.paid_at || order.updated_at || order.created_at) }}
                · {{ order.item_count }} {{ goodsWord(order.item_count) }}
              </p>
            </div>
            <div class="consultant-row__sum">
              <p>{{ formatQuotePrice(order.amount_krw, 'KRW') }}</p>
              <p v-if="order.display_currency !== 'KRW' && order.display_amount" class="consultant-row__meta">
                {{ formatQuotePrice(order.display_amount, order.display_currency) }}
              </p>
            </div>
            <span class="consultant-status" :data-state="consultantOrderState(order)">
              {{ consultantOrderLabel(order) }}
            </span>
          </nuxt-link>
        </li>
      </ul>
    </AccountShell>
    <Footer />
  </div>
</template>

<script setup>
import { accountErrorMessage, useAuthStore } from '~/store/auth'
import { formatQuotePrice } from '~/utils/currencyPrice'
import {
  CONSULTANT_TABS,
  consultantOrderLabel,
  consultantOrderReady,
  consultantOrderState,
  consultantOrderTab,
} from '~/utils/consultant-status'

definePageMeta({
  middleware: 'consultant-auth',
})

useHead({
  title: 'Заказы клиентов',
  titleTemplate: '%s — Личный кабинет',
})
useNoIndex()

const EMPTY = {
  drafts: { lead: 'Черновиков нет', text: 'Соберите заказ для клиента и сохраните его.' },
  awaiting: { lead: 'Никто не ждёт оплату', text: 'В черновике нажмите «Отправил клиенту на оплату» — заказ появится здесь.' },
  placed: { lead: 'Заказов у EvaCode пока нет', text: 'После подтверждения оплаты заказ появится здесь.' },
}

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const orders = ref([])
const loading = ref(true)
const loadError = ref('')
const tabIds = CONSULTANT_TABS.map((item) => item.id)
const tab = ref(tabIds.includes(route.query.tab) ? route.query.tab : 'drafts')

const counts = computed(() => {
  const result = Object.fromEntries(tabIds.map((id) => [id, 0]))
  orders.value.forEach((order) => { result[consultantOrderTab(order)] += 1 })
  return result
})
const filtered = computed(() =>
  orders.value
    .filter((order) => consultantOrderTab(order) === tab.value)
    .sort((a, b) => Number(consultantOrderReady(b)) - Number(consultantOrderReady(a))),
)

function selectTab(id) {
  tab.value = id
  router.replace({ query: { ...route.query, tab: id } })
}

function formatDate(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: '2-digit' })
}

function goodsWord(count) {
  const n = Math.abs(Number(count) || 0) % 100
  const n1 = n % 10
  if (n > 10 && n < 20) return 'товаров'
  if (n1 === 1) return 'товар'
  if (n1 >= 2 && n1 <= 4) return 'товара'
  return 'товаров'
}

async function loadOrders() {
  loading.value = true
  loadError.value = ''
  try {
    const data = await auth.authFetch('/market/consultant/orders/')
    orders.value = Array.isArray(data?.results) ? data.results : []
    if (!route.query.tab && orders.value.length && !counts.value[tab.value]) {
      tab.value = tabIds.find((id) => counts.value[id]) || tab.value
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
