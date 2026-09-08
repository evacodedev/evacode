<template>
  <section class="checkout-v2 section-b-space">
    <div class="container">
      <form class="checkout-v2__grid" @submit.prevent="onPrimarySubmit">
        <div class="checkout-v2__main">
          <section class="checkout-v2__section">
            <h2 class="checkout-v2__heading">Контакты</h2>
            <CheckoutField
              v-model="user.email.value"
              name="email"
              type="email"
              label="Email"
              autocomplete="email"
              :error="user.email.errormsg"
              :submitted="submitted"
              @blur="validateField('email')"
            />
            <div class="checkout-v2__row">
              <CheckoutField
                v-model="user.firstName.value"
                name="firstName"
                label="Имя"
                autocomplete="given-name"
                :error="user.firstName.errormsg"
                :submitted="submitted"
                @blur="validateField('firstName')"
              />
              <CheckoutField
                v-model="user.lastName.value"
                name="lastName"
                label="Фамилия"
                autocomplete="family-name"
                :error="user.lastName.errormsg"
                :submitted="submitted"
                @blur="validateField('lastName')"
              />
            </div>
            <div
              ref="phoneWrap"
              class="checkout-phone"
              :class="{ 'is-invalid': showPhoneError, 'is-filled': Boolean(user.phone.value) }"
              @focusout="onPhoneFocusOut"
            >
              <MazPhoneNumberInput
                v-model="user.phone.value"
                v-model:country-code="countryCode"
                :translations="{
                  countrySelector: {
                    placeholder: 'Код',
                    error: 'Выберите страну',
                    searchPlaceholder: 'Страна',
                  },
                  phoneInput: {
                    placeholder: 'Телефон',
                    example: '',
                  },
                }"
                @blur="onPhoneFocusOut"
              />
              <p v-if="showPhoneError" class="checkout-field__error">{{ user.phone.errormsg }}</p>
            </div>
          </section>

          <section class="checkout-v2__section">
            <h2 class="checkout-v2__heading">Способ доставки</h2>
            <label class="checkout-choice" :class="{ 'is-selected': shippingMethod === 'ems' }">
              <input v-model="shippingMethod" type="radio" name="shipping" value="ems">
              <span class="checkout-choice__body">
                <span class="checkout-choice__title">EMS</span>
                <span class="checkout-choice__note">Почта Кореи, стоимость по стране и весу заказа.</span>
              </span>
            </label>
            <label class="checkout-choice" :class="{ 'is-selected': shippingMethod === 'pickup' }">
              <input v-model="shippingMethod" type="radio" name="shipping" value="pickup">
              <span class="checkout-choice__body">
                <span class="checkout-choice__title">Самовывоз</span>
                <span class="checkout-choice__note">Забрать заказ в Корее, без доставки.</span>
              </span>
            </label>
            <p v-if="shippingError" class="checkout-field__error">{{ shippingError }}</p>
          </section>

          <section v-if="isEms" class="checkout-v2__section">
            <h2 class="checkout-v2__heading">Адрес</h2>
            <CheckoutField
              v-model="destinationCode"
              name="country"
              label="Страна"
              autocomplete="country-name"
              :options="destinationOptions"
              :error="user.country.errormsg"
              :submitted="submitted"
              @blur="validateField('country')"
            />
            <div class="checkout-v2__row">
              <CheckoutField
                v-model="user.region.value"
                name="region"
                label="Регион (необязательно)"
                autocomplete="address-level1"
                :error="user.region.errormsg"
                :submitted="submitted"
              />
              <CheckoutField
                v-model="user.city.value"
                name="city"
                label="Город"
                autocomplete="address-level2"
                :error="user.city.errormsg"
                :submitted="submitted"
                @blur="validateField('city')"
              />
            </div>
            <CheckoutField
              v-model="user.address.value"
              name="address"
              label="Улица"
              autocomplete="address-line1"
              :error="user.address.errormsg"
              :submitted="submitted"
              @blur="validateField('address')"
            />
            <div :class="{ 'checkout-v2__row': !privateHouse }">
              <CheckoutField
                v-model="user.house.value"
                name="house"
                label="Дом"
                autocomplete="address-line2"
                :error="user.house.errormsg"
                :submitted="submitted"
                @blur="validateField('house')"
              />
              <CheckoutField
                v-if="!privateHouse"
                v-model="user.apartment.value"
                name="apartment"
                label="Квартира"
                :error="user.apartment.errormsg"
                :submitted="submitted"
                @blur="validateField('apartment')"
              />
            </div>
            <label class="checkout-check">
              <input v-model="privateHouse" type="checkbox">
              Частный дом
            </label>
            <CheckoutField
              v-model="user.postalCode.value"
              name="postalCode"
              label="Индекс"
              autocomplete="postal-code"
            />
            <CheckoutField
              v-model="user.comment.value"
              name="comment"
              label="Комментарий (необязательно)"
            />
          </section>

          <section v-else class="checkout-v2__section">
            <h2 class="checkout-v2__heading">Самовывоз</h2>
            <p class="checkout-choice__note">Адрес для отправки не нужен. Напишите, если удобно забрать в другое время.</p>
            <CheckoutField
              v-model="user.comment.value"
              name="comment"
              label="Комментарий (необязательно)"
            />
          </section>

          <section class="checkout-v2__section">
            <h2 class="checkout-v2__heading">Оплата</h2>
            <label
              class="checkout-choice"
              :class="{ 'is-disabled': !paypalEnabled }"
              :aria-disabled="paypalEnabled ? 'false' : 'true'"
            >
              <input
                v-model="paymentMethod"
                type="radio"
                name="payment"
                value="paypal"
                :disabled="!paypalEnabled"
                :tabindex="paypalEnabled ? 0 : -1"
              >
              <span class="checkout-choice__body">
                <span class="checkout-choice__title">PayPal</span>
                <span class="checkout-choice__note">{{ paypalNote }}</span>
              </span>
            </label>
            <label
              class="checkout-choice"
              :class="{ 'is-disabled': !telegramEnabled }"
              :aria-disabled="telegramEnabled ? 'false' : 'true'"
            >
              <input
                v-model="paymentMethod"
                type="radio"
                name="payment"
                value="telegram"
                :disabled="!telegramEnabled"
                :tabindex="telegramEnabled ? 0 : -1"
              >
              <span class="checkout-choice__body">
                <span class="checkout-choice__title">Заказ в Telegram</span>
                <span class="checkout-choice__note">{{ telegramNote }}</span>
              </span>
            </label>
            <p v-if="paypalError" class="checkout-v2__pay-error">{{ paypalError }}</p>
            <button
              class="checkout-v2__cta"
              type="submit"
              :disabled="ctaDisabled"
              :aria-disabled="ctaDisabled ? 'true' : 'false'"
            >
              {{ ctaLabel }}
            </button>
          </section>
        </div>

        <aside class="checkout-v2__summary">
          <div class="checkout-v2__heading-row">
            <h2 class="checkout-v2__heading">Заказ</h2>
            <nuxt-link to="/page/account/cart" class="checkout-v2__edit">Редактировать</nuxt-link>
          </div>
          <ul class="checkout-v2__items">
            <li v-for="item in cart" :key="item.id" class="checkout-v2__item">
              <img
                class="checkout-v2__thumb"
                :src="itemImage(item)"
                :alt="item.title"
              >
              <div class="checkout-v2__item-meta">
                <p class="checkout-v2__item-title">{{ item.title }}</p>
                <p class="checkout-v2__item-qty">{{ item.quantity }} шт</p>
              </div>
              <div class="checkout-v2__item-price">
                <span>{{ getPrice(item.retail_price * item.quantity) }}</span>
                <del v-if="item.official_price">{{ getPrice(item.official_price * item.quantity) }}</del>
              </div>
            </li>
          </ul>
          <dl class="checkout-v2__totals">
            <div>
              <dt>Товары</dt>
              <dd>{{ getPrice(cartTotal) }}</dd>
            </div>
            <div>
              <dt>Вес</dt>
              <dd>{{ packageWeightLabel }}</dd>
            </div>
            <div>
              <dt>Доставка</dt>
              <dd>{{ shippingLine }}</dd>
            </div>
            <div class="checkout-v2__grand">
              <dt>Итого</dt>
              <dd>{{ getPrice(grandTotal) }}</dd>
            </div>
          </dl>
          <WidgetsCurrencyWarning />
        </aside>
      </form>
    </div>
    <Teleport to="body">
      <div
        v-if="handoffOpen"
        class="checkout-handoff"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="checkout-handoff-title"
        aria-busy="true"
      >
        <div class="checkout-handoff__card">
          <span class="checkout-handoff__icon" aria-hidden="true">
            <svg viewBox="0 0 48 48" fill="none">
              <circle class="checkout-handoff__track" cx="24" cy="24" r="22.5" stroke="currentColor" stroke-width="1.25"/>
              <g class="checkout-handoff__spin">
                <circle cx="24" cy="24" r="22.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-dasharray="36 108"/>
              </g>
              <path d="M16 20h16l-1.2 14.4A2 2 0 0 1 28.81 36H19.19a2 2 0 0 1-1.99-1.6L16 20Z" stroke="currentColor" stroke-width="1.4"/>
              <path d="M19 20v-3.2A5 5 0 0 1 24 12a5 5 0 0 1 5 4.8V20" stroke="currentColor" stroke-width="1.4"/>
            </svg>
          </span>
          <p id="checkout-handoff-title" class="checkout-handoff__title">{{ handoffTitle }}</p>
          <p class="checkout-handoff__note">{{ handoffNote }}</p>
        </div>
      </div>
    </Teleport>
  </section>
</template>

<script>
import MazPhoneNumberInput from 'maz-ui/components/MazPhoneNumberInput'
import { useCartStore } from '~~/store/cart'
import { useProductStore } from '~~/store/products'

export default {
  components: { MazPhoneNumberInput },
  computed: {
    cart() {
      return useCartStore().cartItems
    },
    cartTotal() {
      return useCartStore().cartTotalAmount
    },
    isEms() {
      return this.shippingMethod === 'ems'
    },
    destinationOptions() {
      return this.destinations.map((item) => ({ value: item.code, label: item.name }))
    },
    selectedDestination() {
      return this.destinations.find((item) => item.code === this.destinationCode) || null
    },
    shippingLine() {
      if (this.shippingMethod === 'pickup') {
        return 'Бесплатно'
      }
      if (this.shippingLoading) {
        return 'Считаем…'
      }
      if (this.shippingKrw == null) {
        return this.destinationCode ? '—' : 'Выберите страну'
      }
      return this.getPrice(this.shippingKrw)
    },
    grandTotal() {
      return this.cartTotal + (this.shippingKrw || 0)
    },
    packageWeightGrams() {
      if (this.quotedWeightGrams > 0) {
        return this.quotedWeightGrams
      }
      return this.cart.reduce((total, item) => {
        return total + Number(item.weight || 0) * Number(item.quantity || 0)
      }, 0)
    },
    packageWeightLabel() {
      const grams = this.packageWeightGrams
      if (!grams) {
        return '—'
      }
      if (grams >= 1000) {
        const kg = (grams / 1000).toLocaleString('ru-RU', {
          maximumFractionDigits: 2,
          minimumFractionDigits: grams % 1000 === 0 ? 0 : 2,
        })
        return `${kg} кг`
      }
      return `${grams.toLocaleString('ru-RU')} г`
    },
    ctaLabel() {
      if (!this.settingsLoaded) {
        return 'Загрузка…'
      }
      if (this.ctaDisabled && !this.paypalEnabled && !this.telegramEnabled) {
        return 'Оплата недоступна'
      }
      if (this.paymentMethod === 'paypal') {
        return this.paypalLoading ? 'Переход к PayPal…' : 'Оплатить PayPal'
      }
      return this.telegramLoading ? 'Отправляем…' : 'Отправить заказ'
    },
    ctaDisabled() {
      if (!this.settingsLoaded || this.paypalLoading || this.telegramLoading) {
        return true
      }
      if (this.paymentMethod === 'paypal') {
        return !this.paypalEnabled
      }
      return !this.telegramEnabled
    },
    paypalNote() {
      return this.paypalEnabled ? 'Оплата картой через PayPal' : 'Сейчас недоступно'
    },
    telegramNote() {
      return this.telegramEnabled ? 'Менеджер подтвердит заказ в Telegram' : 'Сейчас недоступно'
    },
    showPhoneError() {
      return Boolean(this.user.phone.errormsg) && (this.phoneTouched || this.submitted)
    },
    handoffOpen() {
      return this.paypalLoading || this.telegramLoading
    },
    handoffTitle() {
      return this.paymentMethod === 'paypal'
        ? 'Спасибо, переходим к оплате'
        : 'Отправляем заказ'
    },
    handoffNote() {
      return this.paymentMethod === 'paypal'
        ? 'Сейчас откроется страница PayPal. Не закрывайте вкладку.'
        : 'Подождите несколько секунд.'
    },
  },
  data() {
    return {
      user: {
        firstName: { value: '', errormsg: '' },
        lastName: { value: '', errormsg: '' },
        phone: { value: '', errormsg: '' },
        email: { value: '', errormsg: '' },
        country: { value: '', errormsg: '' },
        region: { value: '', errormsg: '' },
        city: { value: '', errormsg: '' },
        address: { value: '', errormsg: '' },
        house: { value: '', errormsg: '' },
        apartment: { value: '', errormsg: '' },
        postalCode: { value: '', errormsg: '' },
        comment: { value: '', errormsg: '' },
      },
      countryCode: 'KR',
      paymentMethod: 'telegram',
      shippingMethod: 'ems',
      destinationCode: '',
      destinations: [],
      shippingKrw: null,
      quotedWeightGrams: null,
      shippingLoading: false,
      shippingError: '',
      quoteTimer: null,
      paypalLoading: false,
      telegramLoading: false,
      paypalError: '',
      submitted: false,
      phoneTouched: false,
      privateHouse: false,
      cartReady: false,
      settingsLoaded: false,
      paypalEnabled: false,
      telegramEnabled: false,
    }
  },
  watch: {
    privateHouse(checked) {
      if (checked) {
        this.user.apartment.errormsg = ''
      }
    },
    shippingMethod() {
      this.user.country.errormsg = ''
      this.scheduleQuote()
    },
    destinationCode() {
      this.user.country.errormsg = ''
      this.scheduleQuote()
    },
    cart: {
      handler(value) {
        if (value.length === 0 && this.cartReady) {
          this.$router.replace('/page/account/cart')
          return
        }
        this.scheduleQuote()
      },
      deep: true,
    },
    handoffOpen(open) {
      if (typeof document === 'undefined') {
        return
      }
      document.documentElement.classList.toggle('checkout-handoff-open', open)
    },
  },
  async mounted() {
    await this.restoreCart()
    this.cartReady = true
    if (this.cart.length === 0) {
      this.$router.replace('/page/account/cart')
      return
    }
    this.loadDestinations()
    this.fetchQuote()
    this.loadCheckoutSettings()
    const paypalStatus = this.$route.query.paypal
    if (paypalStatus === 'cancel') {
      this.paypalError = 'Оплата в PayPal отменена'
    } else if (paypalStatus === 'fail') {
      this.paypalError = 'Не удалось подтвердить оплату. Заказ сохранён, попробуйте ещё раз.'
    }
  },
  beforeUnmount() {
    if (typeof document !== 'undefined') {
      document.documentElement.classList.remove('checkout-handoff-open')
    }
    if (this.quoteTimer) {
      clearTimeout(this.quoteTimer)
    }
  },
  methods: {
    itemImage(item) {
      return item.images?.[0]?.url || item.image || ''
    },
    userValues() {
      const firstName = [this.user.firstName.value, this.user.lastName.value]
        .map((part) => part.trim())
        .filter(Boolean)
        .join(' ')
      const address = [
        this.user.region.value,
        this.user.address.value,
        this.user.house.value ? `д. ${this.user.house.value.trim()}` : '',
        this.privateHouse ? 'частный дом' : (this.user.apartment.value ? `кв. ${this.user.apartment.value.trim()}` : ''),
      ]
        .map((part) => part.trim())
        .filter(Boolean)
        .join(', ')
      return {
        firstName,
        phone: this.user.phone.value,
        email: this.user.email.value,
        country: this.selectedDestination?.name || this.user.country.value,
        city: this.user.city.value,
        address,
        postalCode: this.user.postalCode.value,
        comment: this.user.comment.value,
      }
    },
    shippingPayload() {
      return {
        method: this.shippingMethod,
        destination: this.shippingMethod === 'pickup' ? 'KR' : this.destinationCode,
      }
    },
    setError(field, message) {
      this.user[field].errormsg = message
      return !message
    },
    validateField(field) {
      const value = (this.user[field]?.value || '').trim()
      if (field === 'firstName') {
        if (value.length <= 1) return this.setError(field, 'Укажите имя')
        if (value.length > 100) return this.setError(field, 'Слишком длинное имя')
        return this.setError(field, '')
      }
      if (field === 'lastName') {
        if (value.length <= 1) return this.setError(field, 'Укажите фамилию')
        return this.setError(field, '')
      }
      if (field === 'email') {
        if (!value || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
          return this.setError(field, 'Укажите корректный email')
        }
        return this.setError(field, '')
      }
      if (field === 'phone') {
        if (!this.user.phone.value) return this.setError(field, 'Укажите телефон')
        return this.setError(field, '')
      }
      if (field === 'country') {
        if (!this.isEms) return this.setError(field, '')
        return this.setError(field, this.destinationCode ? '' : 'Укажите страну')
      }
      if (field === 'city') {
        return this.setError(field, value ? '' : 'Укажите город')
      }
      if (field === 'address') {
        return this.setError(field, value ? '' : 'Укажите улицу')
      }
      if (field === 'house') {
        return this.setError(field, value ? '' : 'Укажите дом')
      }
      if (field === 'apartment') {
        if (this.privateHouse) return this.setError(field, '')
        return this.setError(field, value ? '' : 'Укажите квартиру')
      }
      return true
    },
    validateForm() {
      const fields = ['firstName', 'lastName', 'email', 'phone']
      if (this.isEms) {
        fields.push('country', 'city', 'address', 'house')
        if (!this.privateHouse) {
          fields.push('apartment')
        }
      }
      const valid = fields.map((field) => this.validateField(field)).every(Boolean)
      if (this.isEms && this.shippingKrw == null) {
        this.shippingError = this.shippingError || 'Не удалось посчитать доставку'
        return false
      }
      return valid
    },
    async loadCheckoutSettings() {
      try {
        const data = await $fetch(`${useRuntimeConfig().public.apiBase}/market/checkout-settings/`)
        this.paypalEnabled = Boolean(data.paypal_enabled)
        this.telegramEnabled = Boolean(data.telegram_enabled)
      } catch (error) {
        this.paypalEnabled = false
        this.telegramEnabled = false
      }
      if (this.paypalEnabled && !this.telegramEnabled) {
        this.paymentMethod = 'paypal'
      } else if (!this.paypalEnabled && this.telegramEnabled) {
        this.paymentMethod = 'telegram'
      } else if (this.paypalEnabled) {
        this.paymentMethod = 'paypal'
      }
      this.settingsLoaded = true
    },
    async loadDestinations() {
      try {
        const data = await $fetch(`${useRuntimeConfig().public.apiBase}/market/shipping/destinations/`)
        this.destinations = data.results || []
      } catch (error) {
        this.destinations = []
        this.shippingError = 'Не удалось загрузить страны доставки'
      }
    },
    async restoreCart() {
      if (!process.client || this.cart.length > 0) {
        return
      }
      try {
        const stored = await useLocalForage().getItem('evacode_cart')
        const cartArray = JSON.parse(stored || '[]')
        if (cartArray?.length) {
          useCartStore().setInitialCart(cartArray)
        }
      } catch (error) {
        return
      }
    },
    scheduleQuote() {
      if (this.quoteTimer) {
        clearTimeout(this.quoteTimer)
      }
      this.quoteTimer = setTimeout(() => {
        this.fetchQuote()
      }, 250)
    },
    async fetchQuote() {
      if (this.cart.length === 0) {
        return
      }
      const waitingForCountry = this.isEms && !this.destinationCode
      if (!waitingForCountry) {
        this.shippingLoading = true
      }
      this.shippingError = ''
      try {
        const data = await $fetch(`${useRuntimeConfig().public.apiBase}/market/shipping/quote/`, {
          method: 'POST',
          body: {
            cart: this.cart.map((item) => ({ id: item.id, quantity: item.quantity })),
            shipping: this.shippingPayload(),
          },
        })
        this.quotedWeightGrams = data.weight_grams || 0
        this.shippingKrw = waitingForCountry ? null : data.shipping_krw
      } catch (error) {
        if (error?.data?.weight_grams) {
          this.quotedWeightGrams = error.data.weight_grams
        }
        this.shippingKrw = null
        if (!waitingForCountry) {
          this.shippingError = error?.data?.error || 'Не удалось посчитать доставку'
        }
      } finally {
        this.shippingLoading = false
      }
    },
    onPhoneFocusOut(event) {
      const wrap = this.$refs.phoneWrap
      if (wrap && event.relatedTarget && wrap.contains(event.relatedTarget)) {
        return
      }
      this.phoneTouched = true
      this.validateField('phone')
    },
    scrollToFirstError() {
      const invalid = this.$el.querySelector('.checkout-field.is-invalid, .checkout-phone.is-invalid')
      if (!invalid) {
        return
      }
      const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
      invalid.scrollIntoView({
        behavior: reduceMotion ? 'auto' : 'smooth',
        block: 'center',
      })
      const input = invalid.querySelector('input')
      if (input) {
        input.focus({ preventScroll: true })
      }
    },
    onPrimarySubmit() {
      if (this.ctaDisabled) {
        return
      }
      if (this.paymentMethod === 'paypal') {
        return this.onPaypalSubmit()
      }
      return this.onSubmit()
    },
    async onSubmit() {
      if (!this.telegramEnabled || !this.validateForm() || this.telegramLoading) {
        return
      }
      this.telegramLoading = true
      try {
        const cartCheckout = []
        this.cart.forEach((item) => {
          const checkoutProduct = JSON.parse(JSON.stringify(item))
          checkoutProduct.retail_price = this.getPrice(checkoutProduct.retail_price)
          cartCheckout.push(checkoutProduct)
        })
        useProductStore().createOrder({
          product: cartCheckout,
          userDetail: this.user,
          amt: this.getPrice(this.grandTotal),
        })
        await $fetch(`${useRuntimeConfig().public.apiBase}/market/checkout/`, {
          method: 'POST',
          body: {
            cart: cartCheckout,
            user: this.userValues(),
            consult: false,
            shipping: this.shippingPayload(),
          },
        })
        this.$router.push('/page/order-success')
      } catch (error) {
        this.telegramLoading = false
        this.paypalError = error?.data?.error || 'Не удалось отправить заказ. Попробуйте ещё раз.'
      }
    },
    async onPaypalSubmit() {
      if (!this.paypalEnabled || !this.validateForm() || this.paypalLoading) {
        return
      }
      this.paypalLoading = true
      this.paypalError = ''
      try {
        const cartCheckout = this.cart.map((item) => ({
          id: item.id,
          quantity: item.quantity,
        }))
        const data = await $fetch(`${useRuntimeConfig().public.apiBase}/market/orders/`, {
          method: 'POST',
          body: {
            cart: cartCheckout,
            user: this.userValues(),
            shipping: this.shippingPayload(),
          },
        })
        useProductStore().createOrder({
          product: this.cart,
          userDetail: this.user,
          amt: this.getPrice(this.grandTotal),
          publicId: data.id,
        })
        if (data.approve_url) {
          window.location.href = data.approve_url
          return
        }
        this.paypalError = 'PayPal не вернул ссылку на оплату'
        this.paypalLoading = false
      } catch (error) {
        this.paypalError = error?.data?.error || 'Не удалось создать оплату. Попробуйте ещё раз.'
        this.paypalLoading = false
      }
    },
    getPrice(price) {
      return useProductStore().getPrice(price)
    },
  },
}
</script>
