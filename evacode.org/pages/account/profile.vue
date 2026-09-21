<template>
  <div>
    <Header />
    <AccountShell current="profile">
      <h2 class="account-lux__heading">Личные данные</h2>
      <form class="account-lux__profile" @submit.prevent="onSubmit">
        <CheckoutField
          v-model="firstName"
          label="Имя"
          name="profile_first_name"
          autocomplete="given-name"
          :error="firstNameError"
          :submitted="submitted"
        />
        <CheckoutField
          v-model="lastName"
          label="Фамилия"
          name="profile_last_name"
          autocomplete="family-name"
        />
        <div class="account-lux__readonly">
          <span>Электронная почта</span>
          <strong>{{ email }}</strong>
        </div>
        <p class="account-lux__hint">Почту пока нельзя сменить. Телефон и мессенджеры появятся позже.</p>
        <p v-if="formError" class="account-lux__error">{{ formError }}</p>
        <p v-if="saved" class="account-lux__ok">Сохранено</p>
        <button class="account-lux__submit" type="submit" :disabled="pending">
          {{ pending ? 'Сохраняем…' : 'Сохранить' }}
        </button>
      </form>
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
  titleTemplate: '%s — Личные данные',
})

const auth = useAuthStore()
const firstName = ref(auth.user?.first_name || '')
const lastName = ref(auth.user?.last_name || '')
const email = computed(() => auth.user?.email || '')
const submitted = ref(false)
const pending = ref(false)
const saved = ref(false)
const formError = ref('')
const firstNameError = ref('')

watch(
  () => auth.user,
  (user) => {
    if (!user) {
      return
    }
    firstName.value = user.first_name || ''
    lastName.value = user.last_name || ''
  },
)

const onSubmit = async () => {
  submitted.value = true
  saved.value = false
  formError.value = ''
  firstNameError.value = firstName.value.trim() ? '' : 'Укажите имя'
  if (firstNameError.value) {
    return
  }
  pending.value = true
  try {
    await auth.saveProfile({
      first_name: firstName.value.trim(),
      last_name: lastName.value.trim(),
    })
    saved.value = true
  } catch (error) {
    formError.value = accountErrorMessage(error, 'Не удалось сохранить')
  } finally {
    pending.value = false
  }
}
</script>
