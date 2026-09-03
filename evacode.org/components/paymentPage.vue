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
            <h2 class="checkout-v2__heading">Доставка</h2>
            <CheckoutField
              v-model="user.country.value"
              name="country"
              label="Страна"
              autocomplete="country-name"
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

          <section class="checkout-v2__section">
            <h2 class="checkout-v2__heading">Способ доставки</h2>
            <label class="checkout-choice is-selected">
              <input type="radio" name="shipping" value="standard" checked disabled>
              <span class="checkout-choice__body">
                <span class="checkout-choice__title">Стандартная доставка</span>
                <span class="checkout-choice__note">Стоимость пока не считается на сайте — уточним после заказа.</span>
              </span>
            </label>
          </section>

          <section class="checkout-v2__section">
            <h2 class="checkout-v2__heading">Оплата</h2>
            <label class="checkout-choice" :class="{ 'is-selected': paymentMethod === 'paypal' }">
              <input v-model="paymentMethod" type="radio" name="payment" value="paypal">
              <span class="checkout-choice__body">
                <span class="checkout-choice__title">PayPal</span>
                <span v-if="paymentMethod === 'paypal'" class="checkout-choice__note">
                  Оплата картой на странице PayPal. Сумма списывается в долларах.
                </span>
              </span>
            </label>
            <label class="checkout-choice" :class="{ 'is-selected': paymentMethod === 'telegram' }">
              <input v-model="paymentMethod" type="radio" name="payment" value="telegram">
              <span class="checkout-choice__body">
                <span class="checkout-choice__title">Заказ в Telegram</span>
                <span v-if="paymentMethod === 'telegram'" class="checkout-choice__note">
                  Без оплаты на сайте. Заявка уйдёт менеджеру в Telegram.
                </span>
              </span>
            </label>
            <p v-if="paypalError" class="checkout-v2__pay-error">{{ paypalError }}</p>
            <button
              class="checkout-v2__cta"
              type="submit"
              :disabled="paypalLoading"
            >
              {{ ctaLabel }}
            </button>
          </section>
        </div>

        <aside class="checkout-v2__summary">
          <h2 class="checkout-v2__heading">Заказ</h2>
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
              <dt>Доставка</dt>
              <dd>Уточняется</dd>
            </div>
            <div class="checkout-v2__grand">
              <dt>Итого</dt>
              <dd>{{ getPrice(cartTotal) }}</dd>
            </div>
          </dl>
          <WidgetsCurrencyWarning />
        </aside>
      </form>
    </div>
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
    ctaLabel() {
      if (this.paymentMethod === 'paypal') {
        return this.paypalLoading ? 'Переход в PayPal...' : 'Оплатить'
      }
      return 'Отправить заказ'
    },
    showPhoneError() {
      return Boolean(this.user.phone.errormsg) && (this.phoneTouched || this.submitted)
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
      paymentMethod: 'paypal',
      paypalLoading: false,
      paypalError: '',
      submitted: false,
      phoneTouched: false,
      privateHouse: false,
    }
  },
  watch: {
    cart: {
      handler(value) {
        if (value.length === 0) {
          this.$router.replace('/page/account/cart')
        }
      },
      deep: true,
    },
    privateHouse(checked) {
      if (checked) {
        this.user.apartment.errormsg = ''
      }
    },
  },
  mounted() {
    if (this.cart.length === 0) {
      this.$router.replace('/page/account/cart')
    }
    const paypalStatus = this.$route.query.paypal
    if (paypalStatus === 'cancel') {
      this.paypalError = 'Оплата в PayPal отменена'
    } else if (paypalStatus === 'fail') {
      this.paypalError = 'Не удалось подтвердить оплату. Заказ сохранён, попробуйте ещё раз.'
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
        country: this.user.country.value,
        city: this.user.city.value,
        address,
        postalCode: this.user.postalCode.value,
        comment: this.user.comment.value,
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
        return this.setError(field, value ? '' : 'Укажите страну')
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
      const fields = ['firstName', 'lastName', 'email', 'phone', 'country', 'city', 'address', 'house']
      if (!this.privateHouse) {
        fields.push('apartment')
      }
      return fields.map((field) => this.validateField(field)).every(Boolean)
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
      this.submitted = true
      if (!this.validateForm()) {
        this.$nextTick(() => this.scrollToFirstError())
        return
      }
      if (this.paymentMethod === 'paypal') {
        return this.onPaypalSubmit()
      }
      return this.onSubmit()
    },
    async onSubmit() {
      if (!this.validateForm()) {
        return
      }
      const cartCheckout = []
      this.cart.forEach((item) => {
        const checkoutProduct = JSON.parse(JSON.stringify(item))
        checkoutProduct.retail_price = this.getPrice(checkoutProduct.retail_price)
        cartCheckout.push(checkoutProduct)
      })
      useProductStore().createOrder({
        product: cartCheckout,
        userDetail: this.user,
        amt: this.getPrice(this.cartTotal),
      })
      await $fetch(`${useRuntimeConfig().public.apiBase}/market/checkout/`, {
        method: 'POST',
        body: {
          cart: cartCheckout,
          user: this.userValues(),
          consult: false,
        },
      })
      this.$router.push('/page/order-success')
    },
    async onPaypalSubmit() {
      if (!this.validateForm() || this.paypalLoading) {
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
          },
        })
        useProductStore().createOrder({
          product: this.cart,
          userDetail: this.user,
          amt: this.getPrice(this.cartTotal),
          publicId: data.id,
        })
        if (data.approve_url) {
          window.location.href = data.approve_url
          return
        }
        this.paypalError = 'PayPal не вернул ссылку на оплату'
      } catch (error) {
        this.paypalError = error?.data?.error || 'Не удалось создать оплату. Попробуйте ещё раз.'
      } finally {
        this.paypalLoading = false
      }
    },
    getPrice(price) {
      return useProductStore().getPrice(price)
    },
  },
}
</script>
