<template>
  <div>
    <Header />
    <AccountShell current="profile">
      <h2 class="account-lux__heading">Личные данные</h2>
      <p class="account-lux__status">Статус: Розничный клиент</p>
      <form class="account-lux__profile" @submit.prevent="onSubmit">
        <CheckoutField
          v-model="firstName"
          class="account-lux__span-2"
          label="Имя"
          name="profile_first_name"
          autocomplete="given-name"
          :error="fieldError.firstName"
          :submitted="submitted"
        />
        <CheckoutField
          v-model="lastName"
          class="account-lux__span-2"
          label="Фамилия"
          name="profile_last_name"
          autocomplete="family-name"
        />
        <AccountPhoneField
          v-model="phone"
          class="account-lux__span-2"
          label="Телефон"
          name="profile_phone"
        />
        <CheckoutField
          :model-value="email"
          class="account-lux__span-2"
          label="Электронная почта"
          name="profile_email"
          type="email"
          autocomplete="email"
          disabled
        />
        <AccountPhoneField
          v-model="whatsapp"
          class="account-lux__span-2"
          label="WhatsApp"
          name="profile_whatsapp"
        />
        <CheckoutField
          v-model="telegram"
          class="account-lux__span-2"
          label="Telegram"
          name="profile_telegram"
          mask="telegram"
          autocomplete="username"
        />
        <p v-if="formError" class="account-lux__error account-lux__span-2">{{ formError }}</p>
        <p v-if="saved" class="account-lux__ok account-lux__span-2">Сохранено</p>
        <button class="account-lux__submit account-lux__submit--brand" type="submit" :disabled="pending">
          {{ pending ? 'Сохраняем…' : 'Сохранить изменения' }}
        </button>
      </form>

      <div class="account-lux__password">
        <button
          v-if="!showPasswordForm"
          class="account-lux__ghost"
          type="button"
          @click="openPasswordForm"
        >
          Сменить пароль
        </button>
        <form v-else class="account-lux__profile" @submit.prevent="onChangePassword">
          <CheckoutField
            v-model="currentPassword"
            class="account-lux__span-2"
            label="Текущий пароль"
            name="profile_current_password"
            type="password"
            autocomplete="current-password"
            :error="passwordError.current"
            :submitted="passwordSubmitted"
          />
          <CheckoutField
            v-model="password"
            label="Новый пароль"
            name="profile_password"
            type="password"
            autocomplete="new-password"
            :disabled="!canSetNewPassword"
            :error="passwordError.password"
            :submitted="passwordSubmitted"
          />
          <CheckoutField
            v-model="password2"
            label="Подтверждение пароля"
            name="profile_password2"
            type="password"
            autocomplete="new-password"
            :disabled="!canSetNewPassword"
            :error="passwordError.password2"
            :submitted="passwordSubmitted"
          />
          <p v-if="passwordFormError" class="account-lux__error account-lux__span-2">{{ passwordFormError }}</p>
          <p v-if="passwordSaved" class="account-lux__ok account-lux__span-2">Пароль обновлён</p>
          <div class="account-lux__password-actions">
            <button class="account-lux__submit account-lux__submit--brand" type="submit" :disabled="passwordPending || !canSetNewPassword">
              {{ passwordPending ? 'Сохраняем…' : 'Сохранить пароль' }}
            </button>
            <button class="account-lux__ghost" type="button" @click="closePasswordForm">Отмена</button>
          </div>
        </form>
      </div>
    </AccountShell>
    <Footer />
  </div>
</template>

<script setup>
import { accountErrorMessage, useAuthStore } from '~/store/auth'
import { maskTelegram, toIntlPhone } from '~/utils/input-mask'

definePageMeta({
  middleware: 'account-auth',
})

useHead({
  titleTemplate: '%s — Личные данные',
})
useNoIndex()

const auth = useAuthStore()
const firstName = ref('')
const lastName = ref('')
const phone = ref('')
const whatsapp = ref('')
const telegram = ref('')
const email = computed(() => auth.user?.email || '')
const submitted = ref(false)
const pending = ref(false)
const saved = ref(false)
const formError = ref('')
const fieldError = reactive({
  firstName: '',
})

const showPasswordForm = ref(false)
const currentPassword = ref('')
const password = ref('')
const password2 = ref('')
const passwordSubmitted = ref(false)
const passwordPending = ref(false)
const passwordSaved = ref(false)
const passwordFormError = ref('')
const passwordError = reactive({
  current: '',
  password: '',
  password2: '',
})

const canSetNewPassword = computed(() => currentPassword.value.length > 0)

function applyUser(user) {
  if (!user) {
    return
  }
  firstName.value = user.first_name || ''
  lastName.value = user.last_name || ''
  phone.value = toIntlPhone(user.phone || '')
  whatsapp.value = toIntlPhone(user.whatsapp || '')
  telegram.value = maskTelegram(user.telegram || '')
}

applyUser(auth.user)
watch(() => auth.user, applyUser)

const onSubmit = async () => {
  submitted.value = true
  saved.value = false
  formError.value = ''
  fieldError.firstName = firstName.value.trim() ? '' : 'Укажите имя'
  if (fieldError.firstName) {
    return
  }
  pending.value = true
  try {
    await auth.saveProfile({
      first_name: firstName.value.trim(),
      last_name: lastName.value.trim(),
      phone: phone.value.trim(),
      whatsapp: whatsapp.value.trim(),
      telegram: telegram.value.trim(),
    })
    saved.value = true
  } catch (error) {
    formError.value = accountErrorMessage(error, 'Не удалось сохранить')
  } finally {
    pending.value = false
  }
}

const openPasswordForm = () => {
  showPasswordForm.value = true
  passwordSaved.value = false
  passwordFormError.value = ''
}

const closePasswordForm = () => {
  showPasswordForm.value = false
  currentPassword.value = ''
  password.value = ''
  password2.value = ''
  passwordSubmitted.value = false
  passwordFormError.value = ''
  passwordError.current = ''
  passwordError.password = ''
  passwordError.password2 = ''
}

const onChangePassword = async () => {
  passwordSubmitted.value = true
  passwordSaved.value = false
  passwordFormError.value = ''
  passwordError.current = currentPassword.value ? '' : 'Укажите текущий пароль'
  passwordError.password = password.value ? '' : 'Введите новый пароль'
  passwordError.password2 = password.value === password2.value ? '' : 'Пароли не совпадают'
  if (passwordError.current || passwordError.password || passwordError.password2 || !canSetNewPassword.value) {
    return
  }
  passwordPending.value = true
  try {
    await auth.saveProfile({
      current_password: currentPassword.value,
      password: password.value,
      password2: password2.value,
    })
    currentPassword.value = ''
    password.value = ''
    password2.value = ''
    passwordSubmitted.value = false
    passwordSaved.value = true
  } catch (error) {
    passwordFormError.value = accountErrorMessage(error, 'Не удалось сменить пароль')
  } finally {
    passwordPending.value = false
  }
}
</script>
