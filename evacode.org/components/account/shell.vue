<template>
  <div class="account-lux">
    <div class="container">
      <div class="account-lux__layout">
        <aside class="account-lux__aside">
          <p class="account-lux__eyebrow">Аккаунт</p>
          <h1 class="account-lux__title">Личный кабинет</h1>
          <p class="account-lux__hello">Здравствуйте, {{ displayName }}!</p>
          <p class="account-lux__status-line">Статус: Розничный клиент</p>
          <nav class="account-lux__nav" aria-label="Разделы кабинета">
            <nuxt-link
              v-for="item in items"
              :key="item.to"
              :to="item.to"
              class="account-lux__link"
              :class="{ 'is-active': item.active }"
            >
              {{ item.label }}
            </nuxt-link>
            <button
              type="button"
              class="account-lux__link account-lux__logout"
              :disabled="logoutPending"
              @click="onLogout"
            >
              Выйти
            </button>
          </nav>
        </aside>
        <div class="account-lux__main">
          <slot />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useAuthStore } from '~/store/auth'

const props = defineProps({
  current: {
    type: String,
    default: 'orders',
  },
})

const auth = useAuthStore()
const { showHandoff, hideHandoff } = useHandoff()
const displayName = computed(() => auth.displayName || 'гость')
const logoutPending = ref(false)

const items = computed(() => [
  { to: '/account/', label: 'Заказы', active: props.current === 'orders' },
  { to: '/account/profile/', label: 'Личные данные', active: props.current === 'profile' },
  { to: '/account/addresses/', label: 'Адреса доставки', active: props.current === 'addresses' },
  { to: '/account/wishlist/', label: 'Избранное', active: props.current === 'wishlist' },
])

const onLogout = async () => {
  if (logoutPending.value) {
    return
  }
  logoutPending.value = true
  showHandoff({
    title: 'Выходим…',
    note: 'Возвращаем на главную.',
  })
  try {
    auth.logout()
    await navigateTo('/')
  } finally {
    hideHandoff()
    logoutPending.value = false
  }
}
</script>
