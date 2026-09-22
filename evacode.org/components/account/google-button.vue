<template>
  <div v-if="enabled" class="account-lux__google">
    <p class="account-lux__divider"><span>или</span></p>
    <div ref="buttonHost" class="account-lux__google-host" />
    <p v-if="error" class="account-lux__error">{{ error }}</p>
  </div>
</template>

<script setup>
import { accountErrorMessage, useAuthStore } from '~/store/auth'

const emit = defineEmits(['success', 'error'])

const auth = useAuthStore()
const enabled = ref(false)
const clientId = ref('')
const error = ref('')
const pending = ref(false)
const buttonHost = ref(null)
let scriptPromise = null

function loadGisScript() {
  if (process.server) {
    return Promise.reject(new Error('client only'))
  }
  if (window.google?.accounts?.id) {
    return Promise.resolve()
  }
  if (scriptPromise) {
    return scriptPromise
  }
  scriptPromise = new Promise((resolve, reject) => {
    const existing = document.querySelector('script[data-google-gis]')
    if (existing) {
      existing.addEventListener('load', () => resolve())
      existing.addEventListener('error', () => reject(new Error('Google script failed')))
      return
    }
    const script = document.createElement('script')
    script.src = 'https://accounts.google.com/gsi/client'
    script.async = true
    script.defer = true
    script.dataset.googleGis = '1'
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('Google script failed'))
    document.head.appendChild(script)
  })
  return scriptPromise
}

async function onCredential(response) {
  const credential = response?.credential
  if (!credential || pending.value) {
    return
  }
  pending.value = true
  error.value = ''
  try {
    await auth.loginWithGoogle(credential)
    emit('success')
  } catch (err) {
    const message = accountErrorMessage(err, 'Не удалось войти через Google')
    error.value = message
    emit('error', message)
  } finally {
    pending.value = false
  }
}

function renderButton() {
  if (!buttonHost.value || !window.google?.accounts?.id || !clientId.value) {
    return
  }
  buttonHost.value.innerHTML = ''
  window.google.accounts.id.initialize({
    client_id: clientId.value,
    callback: onCredential,
    auto_select: false,
    cancel_on_tap_outside: true,
  })
  window.google.accounts.id.renderButton(buttonHost.value, {
    type: 'standard',
    theme: 'outline',
    size: 'large',
    text: 'continue_with',
    shape: 'rectangular',
    logo_alignment: 'left',
    width: Math.min(buttonHost.value.clientWidth || 360, 400),
  })
}

onMounted(async () => {
  try {
    const config = await $fetch(auth.apiUrl('/core/auth/google/config/'))
    enabled.value = Boolean(config?.enabled && config?.client_id)
    clientId.value = config?.client_id || ''
    if (!enabled.value) {
      return
    }
    await loadGisScript()
    await nextTick()
    renderButton()
  } catch {
    enabled.value = false
  }
})
</script>
