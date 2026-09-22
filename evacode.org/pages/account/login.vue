<template>
  <div>
    <Header />
    <div class="account-lux account-lux--auth">
      <div class="container">
        <div class="account-lux__card">
          <p class="account-lux__eyebrow">Аккаунт</p>
          <h1 class="account-lux__title">Войти</h1>
          <p class="account-lux__lead">Введите почту и пароль.</p>
          <form class="account-lux__form" @submit.prevent="onSubmit">
            <CheckoutField
              v-model="email"
              label="Электронная почта"
              name="email"
              type="email"
              autocomplete="email"
              :error="fieldError.email"
              :submitted="submitted"
            />
            <CheckoutField
              v-model="password"
              label="Пароль"
              name="password"
              type="password"
              autocomplete="current-password"
              :error="fieldError.password"
              :submitted="submitted"
            />
            <p v-if="formError" class="account-lux__error">{{ formError }}</p>
            <button class="account-lux__submit" type="submit" :disabled="pending">
              {{ pending ? 'Входим…' : 'Войти' }}
            </button>
          </form>
          <AccountGoogleButton @success="onGoogleSuccess" />
          <p class="account-lux__switch">
            Нет аккаунта?
            <nuxt-link :to="registerTo">Зарегистрироваться</nuxt-link>
          </p>
        </div>
      </div>
    </div>
    <Footer />
  </div>
</template>

<script setup>
import { accountErrorMessage, safeAccountNext, useAuthStore } from '~/store/auth'

definePageMeta({
  middleware: 'account-guest',
})

useHead({
  titleTemplate: '%s — Войти',
})

const route = useRoute()
const auth = useAuthStore()
const { showHandoff, hideHandoff } = useHandoff()
const email = ref('')
const password = ref('')
const submitted = ref(false)
const pending = ref(false)
const formError = ref('')
const fieldError = reactive({ email: '', password: '' })

const registerTo = computed(() => {
  const next = route.query.next
  if (typeof next === 'string' && next) {
    return { path: '/account/register/', query: { next } }
  }
  return '/account/register/'
})

const onSubmit = async () => {
  submitted.value = true
  formError.value = ''
  fieldError.email = email.value.trim() ? '' : 'Укажите email'
  fieldError.password = password.value ? '' : 'Укажите пароль'
  if (fieldError.email || fieldError.password) {
    return
  }
  pending.value = true
  showHandoff({
    title: 'Входим…',
    note: 'Подождите несколько секунд.',
  })
  try {
    await auth.login(email.value, password.value)
    await navigateTo(safeAccountNext(route.query.next))
    hideHandoff()
  } catch (error) {
    hideHandoff()
    formError.value = accountErrorMessage(error, 'Не удалось войти')
  } finally {
    pending.value = false
  }
}

const onGoogleSuccess = async () => {
  await navigateTo(safeAccountNext(route.query.next))
  hideHandoff()
}
</script>
