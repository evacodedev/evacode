<template>
<Header/>
  <div>
  <section class="p-0" v-if="order==''">
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
    <!-- thank-you section start -->
    <section class="section-b-space light-layout" v-if="order!=''">
      <div class="container">
        <div class="row">
          <div class="col-md-12">
            <div class="success-text">
              <i class="fa fa-check-circle" aria-hidden="true"></i>
              <h2>Спасибо!</h2>
              <p>Ваш заказ успешно отправлен нашим консультантам. <br/> В ближайшее время с Вами свяжутся для подтверждения заказа!</p>
            </div>
          </div>
        </div>
      </div>
    </section>
    <!-- Section ends -->
    <!-- order-detail section start -->
    <section class="section-b-space" v-if="order!=''">
      <div class="container">
        <div class="row">
          <div class="col-lg-6">
            <div class="product-order">
              <h3>Детали Вашего заказа</h3>
              <div class="row product-order-detail" v-for="(item,index) in order.product" :key="index">
                <div class="col-3">
                  <img :src="item.images[0].url" alt class="img-fluid" />
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
                    <h5>{{ item.retail_price }}</h5>
                  </div>
                </div>
              </div>
              <div class="total-sec">
                <ul>
                  <li>
                    Итого
                    <span>{{ getPrice(cartTotal) }}</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
    <!-- Section ends -->
  </div>
  <Footer />
</template>
<script>
import { useProductStore } from '~~/store/products';
import { useCartStore } from '~~/store/cart';

export default {
  components: {

  },
  computed: {
    order(){
      return useProductStore().getOrder
    },
    cartTotal() {
      return useCartStore().cartTotalAmount
    },
    curr(){
      return useProductStore().changeCurrency
    }
  },
  methods: {
    getPrice: function (price) {
      return useProductStore().getPrice(price);
    }
  }
}
</script>
