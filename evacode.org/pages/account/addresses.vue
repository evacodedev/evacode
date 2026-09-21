<template>
  <div>
    <Header />
    <AccountShell current="addresses">
      <h2 class="account-lux__heading">Адреса доставки</h2>

      <div v-if="loadError" class="account-lux__error">{{ loadError }}</div>
      <p v-else-if="loading" class="account-lux__hint">Загружаем адреса…</p>

      <div v-else class="account-lux__addresses">
        <div
          v-for="item in addresses"
          :key="item.id"
          class="account-lux__address"
        >
          <span class="account-lux__pin" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none">
              <path d="M12 21s6.5-6.1 6.5-11.2A6.5 6.5 0 0 0 12 3.3a6.5 6.5 0 0 0-6.5 6.5C5.5 14.9 12 21 12 21Z" stroke="currentColor" stroke-width="1.4"/>
              <circle cx="12" cy="9.7" r="2.2" stroke="currentColor" stroke-width="1.4"/>
            </svg>
          </span>
          <p class="account-lux__address-text">{{ formatAccountAddress(item) }}</p>
          <div class="account-lux__address-actions">
            <button
              class="account-lux__icon-btn"
              type="button"
              aria-label="Редактировать адрес"
              @click="openForm(item)"
            >
              <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path d="M4 20h4.2L19 9.2 14.8 5 4 15.8V20Z" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/>
                <path d="M12.8 7l4.2 4.2" stroke="currentColor" stroke-width="1.4"/>
              </svg>
            </button>
            <button
              class="account-lux__icon-btn is-mute"
              type="button"
              aria-label="Удалить адрес"
              @click="openDelete(item)"
            >
              <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path d="M5 7h14" stroke="currentColor" stroke-width="1.4"/>
                <path d="M10 7V5h4v2M8 7l.8 12h6.4L16 7" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/>
              </svg>
            </button>
          </div>
        </div>

        <button class="account-lux__add" type="button" @click="openForm()">
          <span aria-hidden="true">+</span>
          Добавить новый
        </button>
      </div>
    </AccountShell>
    <Footer />

    <Teleport to="body">
      <div
        v-if="formOpen"
        class="account-lux-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="address-form-title"
      >
        <button class="account-lux-dialog__backdrop" type="button" aria-label="Закрыть" @click="closeForm" />
        <div class="account-lux-dialog__card">
          <button class="account-lux-dialog__close" type="button" aria-label="Закрыть" @click="closeForm">
            ×
          </button>
          <h3 id="address-form-title" class="account-lux-dialog__title">Укажите адрес</h3>
          <form class="account-lux__profile account-lux__profile--dialog" @submit.prevent="onSave">
            <CheckoutField
              :key="`country-${editingId || 'new'}`"
              v-model="form.country_code"
              class="account-lux__span-2"
              label="Страна *"
              name="address_country"
              autocomplete="country"
              :options="countryOptions"
              :error="fieldError.country"
              :submitted="submitted"
            />
            <CheckoutField
              v-model="form.city"
              class="account-lux__span-2"
              label="Город *"
              name="address_city"
              autocomplete="address-level2"
              :error="fieldError.city"
              :submitted="submitted"
            />
            <CheckoutField
              v-model="form.street"
              class="account-lux__span-2"
              label="Улица *"
              name="address_street"
              autocomplete="address-line1"
              :error="fieldError.street"
              :submitted="submitted"
            />
            <CheckoutField
              v-model="form.house"
              :class="{ 'account-lux__span-2': privateHouse }"
              label="Дом *"
              name="address_house"
              autocomplete="address-line2"
              :error="fieldError.house"
              :submitted="submitted"
            />
            <CheckoutField
              v-if="!privateHouse"
              v-model="form.apartment"
              label="Квартира *"
              name="address_apartment"
              :error="fieldError.apartment"
              :submitted="submitted"
            />
            <label class="checkout-check account-lux__span-2">
              <input v-model="privateHouse" type="checkbox">
              Частный дом
            </label>
            <CheckoutField
              v-model="form.postal_code"
              class="account-lux__span-2"
              label="Индекс *"
              name="address_postal"
              autocomplete="postal-code"
              :error="fieldError.postal_code"
              :submitted="submitted"
            />
            <CheckoutField
              v-model="form.comment"
              class="account-lux__span-2"
              label="Комментарий: подъезд, этаж, домофон"
              name="address_comment"
              type="textarea"
              :rows="3"
            />
            <p v-if="formError" class="account-lux__error account-lux__span-2">{{ formError }}</p>
            <button class="account-lux__submit account-lux__submit--brand" type="submit" :disabled="pending">
              {{ pending ? 'Сохраняем…' : 'Сохранить' }}
            </button>
          </form>
        </div>
      </div>
    </Teleport>

    <Teleport to="body">
      <div
        v-if="deleteOpen && deleting"
        class="account-lux-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="address-delete-title"
      >
        <div class="account-lux-dialog__backdrop" />
        <div class="account-lux-dialog__card account-lux-dialog__card--confirm">
          <button class="account-lux-dialog__close" type="button" aria-label="Закрыть" @click="closeDelete">
            ×
          </button>
          <h3 id="address-delete-title" class="account-lux-dialog__title">
            Вы уверены, что хотите удалить этот адрес?
          </h3>
          <p class="account-lux__address account-lux__address--preview">
            <span class="account-lux__pin" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none">
                <path d="M12 21s6.5-6.1 6.5-11.2A6.5 6.5 0 0 0 12 3.3a6.5 6.5 0 0 0-6.5 6.5C5.5 14.9 12 21 12 21Z" stroke="currentColor" stroke-width="1.4"/>
                <circle cx="12" cy="9.7" r="2.2" stroke="currentColor" stroke-width="1.4"/>
              </svg>
            </span>
            <span class="account-lux__address-text">{{ formatAccountAddress(deleting) }}</span>
          </p>
          <p v-if="deleteError" class="account-lux__error">{{ deleteError }}</p>
          <div class="account-lux-dialog__actions">
            <button
              class="account-lux__submit account-lux__submit--brand"
              type="button"
              :disabled="pending"
              @click="onDelete"
            >
              Да, удалить
            </button>
            <button class="account-lux__ghost" type="button" :disabled="pending" @click="closeDelete">
              Нет, оставить
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { accountErrorMessage, useAuthStore } from '~/store/auth'
import {
  accountAddressPayload,
  addressCountryOptions,
  countryNameFromCode,
  emptyAccountAddress,
  formatAccountAddress,
  normalizeAddressList,
} from '~/utils/account-address'

definePageMeta({
  middleware: 'account-auth',
})

useHead({
  titleTemplate: '%s — Адреса',
})

const auth = useAuthStore()
const addresses = ref([])
const destinations = ref([])
const loading = ref(true)
const loadError = ref('')
const formOpen = ref(false)
const deleteOpen = ref(false)
const editingId = ref(null)
const deleting = ref(null)
const submitted = ref(false)
const pending = ref(false)
const formError = ref('')
const deleteError = ref('')
const form = reactive(emptyAccountAddress())
const privateHouse = ref(false)
const fieldError = reactive({
  country: '',
  city: '',
  street: '',
  house: '',
  apartment: '',
  postal_code: '',
})
const countryOptions = computed(() => addressCountryOptions(destinations.value))

watch(privateHouse, (checked) => {
  if (checked) {
    form.apartment = ''
    fieldError.apartment = ''
  }
})

watch(
  [() => form.country_code, destinations],
  () => {
    const name = countryNameFromCode(destinations.value, form.country_code)
    if (name) {
      form.country = name
    }
  },
)

function resetFieldErrors() {
  fieldError.country = ''
  fieldError.city = ''
  fieldError.street = ''
  fieldError.house = ''
  fieldError.apartment = ''
  fieldError.postal_code = ''
}

function validate() {
  resetFieldErrors()
  if (!form.country_code.trim()) {
    fieldError.country = 'Укажите страну'
  }
  if (!form.city.trim()) {
    fieldError.city = 'Укажите город'
  }
  if (!form.street.trim()) {
    fieldError.street = 'Укажите улицу'
  }
  if (!form.house.trim()) {
    fieldError.house = 'Укажите дом'
  }
  if (!privateHouse.value && !form.apartment.trim()) {
    fieldError.apartment = 'Укажите квартиру'
  }
  if (!form.postal_code.trim()) {
    fieldError.postal_code = 'Укажите индекс'
  }
  return !fieldError.country && !fieldError.city && !fieldError.street && !fieldError.house && !fieldError.apartment && !fieldError.postal_code
}

async function loadDestinations() {
  try {
    const data = await $fetch(`${useRuntimeConfig().public.apiBase}/market/shipping/destinations/`)
    destinations.value = data.results || []
  } catch {
    destinations.value = []
  }
}

async function loadAddresses() {
  loading.value = true
  loadError.value = ''
  try {
    addresses.value = normalizeAddressList(await auth.listAddresses())
  } catch (error) {
    loadError.value = accountErrorMessage(error, 'Не удалось загрузить адреса')
  } finally {
    loading.value = false
  }
}

function resolveCountryCode(item) {
  const code = String(item?.country_code || '').trim()
  if (code) {
    return code
  }
  const name = String(item?.country || '').trim()
  if (!name) {
    return ''
  }
  return countryOptions.value.find((option) => option.label === name)?.value || ''
}

function openForm(item) {
  Object.assign(form, item ? {
    country: item.country || '',
    country_code: resolveCountryCode(item),
    city: item.city || '',
    street: item.street || '',
    house: item.house || '',
    apartment: item.apartment || '',
    postal_code: item.postal_code || '',
    comment: item.comment || '',
  } : emptyAccountAddress())
  privateHouse.value = Boolean(item) && !String(item.apartment || '').trim()
  editingId.value = item?.id || null
  submitted.value = false
  pending.value = false
  formError.value = ''
  resetFieldErrors()
  formOpen.value = true
}

function closeForm() {
  if (pending.value) {
    return
  }
  formOpen.value = false
  editingId.value = null
}

function openDelete(item) {
  deleting.value = item
  deleteError.value = ''
  deleteOpen.value = true
}

function closeDelete() {
  if (pending.value) {
    return
  }
  deleteOpen.value = false
  deleting.value = null
}

async function onSave() {
  submitted.value = true
  formError.value = ''
  if (!validate()) {
    return
  }
  pending.value = true
  try {
    await auth.saveAddress(accountAddressPayload({
      ...form,
      country: countryNameFromCode(destinations.value, form.country_code),
      apartment: privateHouse.value ? '' : form.apartment,
    }), editingId.value)
    await loadAddresses()
    pending.value = false
    closeForm()
  } catch (error) {
    formError.value = accountErrorMessage(error, 'Не удалось сохранить адрес')
    pending.value = false
  }
}

async function onDelete() {
  if (!deleting.value) {
    return
  }
  pending.value = true
  deleteError.value = ''
  try {
    await auth.deleteAddress(deleting.value.id)
    await loadAddresses()
    pending.value = false
    closeDelete()
  } catch (error) {
    deleteError.value = accountErrorMessage(error, 'Не удалось удалить адрес')
    pending.value = false
  }
}

function onKeydown(event) {
  if (event.key !== 'Escape') {
    return
  }
  if (deleteOpen.value) {
    closeDelete()
    return
  }
  if (formOpen.value) {
    closeForm()
  }
}

onMounted(() => {
  loadDestinations()
  loadAddresses()
  window.addEventListener('keydown', onKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
})
</script>
