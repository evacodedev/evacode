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
                  <div class="form-group col-md-5 col-sm-5">
                    <div class="field-label">Имя</div>
                    <MazInput
                        v-model="user.firstName.value"
                        label="Ваше имя"
                        autocomplete="off"
                    />
                    <span class="validate-error" v-if="user.firstName.errormsg.length > 0">{{ user.firstName.errormsg }}</span>
                  </div>
                  <div class="form-group col-md-6 col-sm-6">
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
                    <span class="validate-error" v-if="user.phone.value.length === 0">{{ user.phone.errormsg }}</span>
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
                    <div class="text-end">
                      <span class="btn btn-primary" @click="onSubmit">Купить</span>
                      <span class="btn btn-primary ms-2" @click="openPaypalInfoModal">Оплатить PayPal</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
    <PaymentPaypalInfoModal
      :open="showPaypalInfoModal"
      @close="closePaypalInfoModal"
    />
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
      },
      countryCode: 'KR',
      showPaypalInfoModal: false,
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
    openPaypalInfoModal() {
      this.showPaypalInfoModal = true;
    },
    closePaypalInfoModal() {
      this.showPaypalInfoModal = false;
    },
    validateFields() {
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

      return isValidForm;
    },
    async onSubmit() {
      if (this.validateFields()) {
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

        const userForCheckout = {};
        Object.keys(this.user).forEach((key) => {
          userForCheckout[key] = this.user[key].value;
        })
        await $fetch(`${useRuntimeConfig().public.apiBase}/market/checkout/`, {
          method: 'POST',
          body: {
            cart: cartCheckout,
            user: userForCheckout,
            consult: false,
          }
        })

        this.$router.push('/page/order-success')
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

  },
}
</script>

<style scoped>
.checkout-page .checkout-form input[type=text] {
  border: 0 !important;
}
</style>
