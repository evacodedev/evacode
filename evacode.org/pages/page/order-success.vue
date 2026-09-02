<template>
<Header/>
  <div>
  <section class="p-0" v-if="!hasOrder">
      <div class="container">
        <div class="row">
          <div class="col-12">
            <div class="error-section">
              <h1>404</h1>
              <h2>страница не найдена</h2>
              <nuxt-link :to="{ path: '/'}" :class="'btn btn-solid'">На главную</nuxt-link>
            </div>
          </div>
        </div>
      </div>
    </section>
    <section class="section-b-space light-layout" v-if="hasOrder">
      <div class="container">
        <div class="row">
          <div class="col-md-12">
            <div class="success-text">
              <i class="fa fa-check-circle" aria-hidden="true"></i>
              <h2>Спасибо!</h2>
              <p v-if="isPaypalPaid">
                Оплата прошла, заказ сохранён. Номер заказа: {{ paidOrder.id }}
              </p>
              <p v-if="isPaypalPaid && paidOrder.paypal_receipt_url">
                <a :href="paidOrder.paypal_receipt_url" target="_blank" rel="noopener">Открыть чек PayPal</a>
                <span> — сохраните ссылку, письмо с квитанцией также приходит на email PayPal.</span>
              </p>
              <p v-else>Ваш заказ успешно отправлен нашим консультантам. <br/> В ближайшее время с Вами свяжутся для подтверждения заказа!</p>
            </div>
          </div>
        </div>
      </div>
    </section>
    <section class="section-b-space" v-if="hasOrder">
      <div class="container">
        <div class="row">
          <div class="col-lg-6">
            <div class="product-order">
              <h3>Детали Вашего заказа</h3>
              <div class="row product-order-detail" v-for="(item,index) in displayItems" :key="index">
                <div class="col-3" v-if="itemImage(item)">
                  <img :src="itemImage(item)" alt class="img-fluid" />
                </div>
                <div class="col-4 order_detail">
                  <div>
                    <h4>Товар</h4>
                    <h5>{{item.title}}</h5>
                  </div>
                </div>
                <div class="col-2 order_detail">
                  <div>
                    <h4>Кол.</h4>
                    <h5>{{item.quantity}}</h5>
                  </div>
                </div>
                <div class="col-3 order_detail">
                  <div>
                    <h4>Цена</h4>
                    <h5>{{ itemPrice(item) }}</h5>
                  </div>
                </div>
              </div>
              <div class="total-sec">
                <ul>
                  <li>
                    Итого
                    <span>{{ displayTotal }}</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
  <Footer />
</template>
<script>
import { useProductStore } from '~~/store/products';
import { useCartStore } from '~~/store/cart';

export default {
  data() {
    return {
      paidOrder: null,
    }
  },
  computed: {
    order(){
      return useProductStore().getOrder
    },
    isPaypalPaid() {
      return this.$route.query.paypal === '1' && this.paidOrder;
    },
    hasOrder() {
      return Boolean(this.paidOrder || (this.order && this.order !== ''));
    },
    displayItems() {
      if (this.paidOrder) {
        return this.paidOrder.items || [];
      }
      return this.order?.product || [];
    },
    displayTotal() {
      if (this.paidOrder) {
        return `${this.paidOrder.amount_krw} ₩ / ${this.paidOrder.amount_usd} USD`;
      }
      return this.getPrice(useCartStore().cartTotalAmount);
    },
    curr(){
      return useProductStore().changeCurrency
    }
  },
  methods: {
    itemImage(item) {
      return item.image || item.images?.[0]?.url || '';
    },
    itemPrice(item) {
      if (item.price_krw != null) {
        return this.getPrice(item.price_krw);
      }
      return item.retail_price;
    },
    getPrice: function (price) {
      return useProductStore().getPrice(price);
    }
  },
  async mounted() {
    const orderId = this.$route.query.id;
    if (orderId) {
      try {
        this.paidOrder = await $fetch(`${useRuntimeConfig().public.apiBase}/market/orders/${orderId}/`);
        if (this.paidOrder?.status === 'paid') {
          useCartStore().setInitialCart([]);
        }
      } catch (error) {
        this.paidOrder = null;
      }
    }
  }
}
</script>
