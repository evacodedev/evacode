<template>
  <section class="section-b-space">
    <div class="container">
      <div class="checkout-page">
        <div class="checkout-form">
          <form>
            <div class="row">
              <div class="col-lg-6 col-sm-12">
                <div class="checkout-title">
                  <h3>Ваши данные</h3>
                </div>
                <div class="row check-out">
                  <div class="form-group col-md-6 col-sm-12">
                    <div class="field-label">ФИО</div>
                    <MazInput
                        v-model="user.firstName.value"
                        label="Имя и фамилия"
                        autocomplete="name"
                    />
                    <span class="validate-error" v-if="user.firstName.errormsg.length > 0">{{ user.firstName.errormsg }}</span>
                  </div>
                  <div class="form-group col-md-6 col-sm-12">
                    <div class="field-label">Email</div>
                    <MazInput
                        v-model="user.email.value"
                        label="email@example.com"
                        autocomplete="email"
                    />
                    <span class="validate-error" v-if="user.email.errormsg.length > 0">{{ user.email.errormsg }}</span>
                  </div>
                  <div class="form-group col-md-6 col-sm-12">
                    <div class="field-label">Телефон</div>
                    <MazPhoneNumberInput
                        v-model="user.phone.value"
                        v-model:country-code="countryCode"
                        :translations="{
                          countrySelector: {
                            placeholder: 'Код страны',
                            error: 'Выберите страну',
                            searchPlaceholder: 'Искать страну',
                          },
                          phoneInput: {
                            placeholder: 'Номер телефона',
                            example: 'Пример:',
                          },
                        }"
                    />
                    <span class="validate-error" v-if="user.phone.errormsg.length > 0">{{ user.phone.errormsg }}</span>
                  </div>
                  <div class="form-group col-md-6 col-sm-12">
                    <div class="field-label">Страна</div>
                    <MazInput
                        v-model="user.country.value"
                        label="Страна доставки"
                        autocomplete="country-name"
                    />
                    <span class="validate-error" v-if="user.country.errormsg.length > 0">{{ user.country.errormsg }}</span>
                  </div>
                  <div class="form-group col-md-6 col-sm-12">
                    <div class="field-label">Город</div>
                    <MazInput
                        v-model="user.city.value"
                        label="Город"
                        autocomplete="address-level2"
                    />
                    <span class="validate-error" v-if="user.city.errormsg.length > 0">{{ user.city.errormsg }}</span>
                  </div>
                  <div class="form-group col-md-6 col-sm-12">
                    <div class="field-label">Индекс</div>
                    <MazInput
                        v-model="user.postalCode.value"
                        label="Почтовый индекс"
                        autocomplete="postal-code"
                    />
                  </div>
                  <div class="form-group col-12">
                    <div class="field-label">Адрес доставки</div>
                    <MazInput
                        v-model="user.address.value"
                        label="Улица, дом, квартира"
                        autocomplete="street-address"
                    />
                    <span class="validate-error" v-if="user.address.errormsg.length > 0">{{ user.address.errormsg }}</span>
                  </div>
                  <div class="form-group col-12">
                    <div class="field-label">Комментарий</div>
                    <MazInput
                        v-model="user.comment.value"
                        label="Необязательно"
                    />
                  </div>
                </div>
              </div>
              <div class="col-lg-6 col-sm-12">
                <div class="checkout-details">
                  <div class="order-box">
                    <div class="title-box">
                      <div>
                        Продукт
                        <span>Всего</span>
                      </div>
                    </div>
                    <ul class="qty" v-if="cart.length">
                      <li v-for="(item, index) in cart" :key="index">
                        {{ item.title }} X {{ item.quantity }}
                        <span>{{ getPrice(item.retail_price * item.quantity) }}
                              <del>{{ getPrice(item.official_price * item.quantity) }}</del></span>
                      </li>
                    </ul>
                    <ul class="sub-total">
                      <li>
                        Общая стоимость
                        <span class="count">{{ getPrice(cartTotal) }}
                        <del>{{ getPrice(cartOfficialTotal)}}</del></span>
                          <WidgetsCurrencyWarning />
                      </li>
                    </ul>
                  </div>
                  <div class="payment-box">
                    <p class="validate-error" v-if="paypalError">{{ paypalError }}</p>
                    <div class="text-end">
                      <span class="btn btn-primary" @click="onSubmit">Купить</span>
                      <span
                        class="btn btn-primary ms-2"
                        :class="{ disabled: paypalLoading }"
                        @click="onPaypalSubmit"
                      >{{ paypalLoading ? 'Переход в PayPal...' : 'Оплатить PayPal' }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  </section>
</template>
<script>
import MazPhoneNumberInput from 'maz-ui/components/MazPhoneNumberInput'
import {useCartStore} from '~~/store/cart'
import {useProductStore} from '~~/store/products'

export default {
  computed: {
    cart() {
      return useCartStore().cartItems;
    },
    cartTotal() {
      return useCartStore().cartTotalAmount;
    },
    cartOfficialTotal() {
      return useCartStore().cartTotalOfficialAmount;
    },
    curr() {
      return useProductStore().changeCurrency;
    },
  },
  data() {
    return {
      user: {
        firstName: {value: '', errormsg: ''},
        phone: {value: '', errormsg: ''},
        email: {value: '', errormsg: ''},
        country: {value: '', errormsg: ''},
        city: {value: '', errormsg: ''},
        address: {value: '', errormsg: ''},
        postalCode: {value: '', errormsg: ''},
        comment: {value: '', errormsg: ''},
      },
      countryCode: 'KR',
      paypalLoading: false,
      paypalError: '',
    }
  },

  watch: {
    cart: {
      handler(value) {
        if (value.length == 0) {
          this.$router.replace('/page/account/cart')
        }

      }, deep: true
    }
  },


  methods: {
    userValues() {
      const userForCheckout = {};
      Object.keys(this.user).forEach((key) => {
        userForCheckout[key] = this.user[key].value;
      })
      return userForCheckout;
    },
    validateFields(requireDelivery) {
      let isValidForm = true;
      const empty_error_msg = 'Обязательное поле'
      if (this.user.firstName.value.length <= 1) {
        this.user.firstName.errormsg = empty_error_msg;
        isValidForm = false;
      } else if (this.user.firstName.value.length > 100) {
        this.user.firstName.errormsg = 'Слишком длинное имя';
        isValidForm = false;
      } else {
        this.user.firstName.errormsg = ''
      }

      if (!this.user.phone.value) {
        this.user.phone.errormsg = empty_error_msg;
        isValidForm = false;
      } else {
        this.user.phone.errormsg = ''
      }

      if (requireDelivery) {
        const email = this.user.email.value.trim();
        if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
          this.user.email.errormsg = 'Укажите корректный email';
          isValidForm = false;
        } else {
          this.user.email.errormsg = '';
        }
        ['country', 'city', 'address'].forEach((field) => {
          if (!this.user[field].value.trim()) {
            this.user[field].errormsg = empty_error_msg;
            isValidForm = false;
          } else {
            this.user[field].errormsg = '';
          }
        });
      }

      return isValidForm;
    },
    async onSubmit() {
      if (this.validateFields(false)) {
        const cartCheckout = [];
        this.cart.forEach((item) => {
          const checkoutProduct = JSON.parse(JSON.stringify(item));
          checkoutProduct.retail_price = this.getPrice(checkoutProduct.retail_price);
          cartCheckout.push(checkoutProduct);
        })

        useProductStore().createOrder({
          product: cartCheckout,
          userDetail: this.user,
          amt: this.getPrice(this.cartTotal)
        });

        await $fetch(`${useRuntimeConfig().public.apiBase}/market/checkout/`, {
          method: 'POST',
          body: {
            cart: cartCheckout,
            user: this.userValues(),
            consult: false,
          }
        })

        this.$router.push('/page/order-success')
      }
    },
    async onPaypalSubmit() {
      if (!this.validateFields(true) || this.paypalLoading) {
        return;
      }
      this.paypalLoading = true;
      this.paypalError = '';
      try {
        const cartCheckout = this.cart.map((item) => ({
          id: item.id,
          quantity: item.quantity,
        }));
        const data = await $fetch(`${useRuntimeConfig().public.apiBase}/market/orders/`, {
          method: 'POST',
          body: {
            cart: cartCheckout,
            user: this.userValues(),
          }
        });
        useProductStore().createOrder({
          product: this.cart,
          userDetail: this.user,
          amt: this.getPrice(this.cartTotal),
          publicId: data.id,
        });
        if (data.approve_url) {
          window.location.href = data.approve_url;
          return;
        }
        this.paypalError = 'PayPal не вернул ссылку на оплату';
      } catch (error) {
        this.paypalError = error?.data?.error || 'Не удалось создать оплату. Попробуйте ещё раз.';
      } finally {
        this.paypalLoading = false;
      }
    },
    getPrice: function (price) {
      return useProductStore().getPrice(price);
    }
  },

  mounted() {
    this.isLogin = true;

    if (this.isLogin && this.cart.length == 0) {
      this.$router.replace('/page/account/cart')
    }

    const paypalStatus = this.$route.query.paypal;
    if (paypalStatus === 'cancel') {
      this.paypalError = 'Оплата в PayPal отменена';
    } else if (paypalStatus === 'fail') {
      this.paypalError = 'Не удалось подтвердить оплату. Заказ сохранён, попробуйте ещё раз.';
    }
  },
}
</script>

<style scoped>
.checkout-page .checkout-form input[type=text] {
  border: 0 !important;
}
.payment-box .disabled {
  pointer-events: none;
  opacity: 0.7;
}
</style>
