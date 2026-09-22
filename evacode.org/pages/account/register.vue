<template>
  <div>
    <Header />
    <div class="account-lux account-lux--auth">
      <div class="container">
        <div class="account-lux__card">
          <p class="account-lux__eyebrow">Аккаунт</p>
          <h1 class="account-lux__title">Регистрация</h1>
          <p class="account-lux__lead">Достаточно почты и пароля — заказ по-прежнему можно оформить как гость.</p>
          <form class="account-lux__form" @submit.prevent="onSubmit">
            <CheckoutField
              v-model="firstName"
              label="Имя"
              name="first_name"
              autocomplete="given-name"
              :error="fieldError.firstName"
              :submitted="submitted"
            />
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
              autocomplete="new-password"
              :error="fieldError.password"
              :submitted="submitted"
            />
            <CheckoutField
              v-model="password2"
              label="Повторите пароль"
              name="password2"
              type="password"
              autocomplete="new-password"
              :error="fieldError.password2"
              :submitted="submitted"
            />
            <label class="account-lux__consent">
              <input v-model="agreed" type="checkbox">
              <span>
                Соглашаюсь с
                <nuxt-link to="/page/account/privacy-policy/">политикой конфиденциальности</nuxt-link>
              </span>
            </label>
            <p v-if="submitted && !agreed" class="account-lux__error">Нужно согласие с политикой</p>
            <p v-if="formError" class="account-lux__error">{{ formError }}</p>
            <button class="account-lux__submit" type="submit" :disabled="pending">
              {{ pending ? 'Создаём…' : 'Зарегистрироваться' }}
            </button>
          </form>
          <AccountGoogleButton @success="onGoogleSuccess" />
          <p class="account-lux__switch">
            Уже есть аккаунт?
            <nuxt-link :to="loginTo">Войти</nuxt-link>
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
  titleTemplate: '%s — Регистрация',
})
useNoIndex()

const route = useRoute()
const auth = useAuthStore()
const { showHandoff, hideHandoff } = useHandoff()
const firstName = ref('')
const email = ref('')
const password = ref('')
const password2 = ref('')
const agreed = ref(false)
const submitted = ref(false)
const pending = ref(false)
const formError = ref('')
const fieldError = reactive({
  firstName: '',
  email: '',
  password: '',
  password2: '',
})

const loginTo = computed(() => {
  const next = route.query.next
  if (typeof next === 'string' && next) {
    return { path: '/account/login/', query: { next } }
  }
  return '/account/login/'
})

const onSubmit = async () => {
  submitted.value = true
  formError.value = ''
  fieldError.email = email.value.trim() ? '' : 'Укажите email'
  fieldError.password = password.value ? '' : 'Придумайте пароль'
  fieldError.password2 = password.value === password2.value ? '' : 'Пароли не совпадают'
  if (fieldError.email || fieldError.password || fieldError.password2 || !agreed.value) {
    return
  }
  pending.value = true
  showHandoff({
    title: 'Создаём аккаунт…',
    note: 'Подождите несколько секунд.',
  })
  try {
    await auth.register({
      email: email.value,
      password: password.value,
      password2: password2.value,
      first_name: firstName.value,
    })
    await navigateTo(safeAccountNext(route.query.next))
    hideHandoff()
  } catch (error) {
    hideHandoff()
    formError.value = accountErrorMessage(error, 'Не удалось создать аккаунт')
  } finally {
    pending.value = false
  }
}

const onGoogleSuccess = async () => {
  await navigateTo(safeAccountNext(route.query.next))
  hideHandoff()
}
</script>
