<template>
  <div>
    <div class="product-wrapper-grid">
      <div class="row">
        <div class="col-12">
          <div class="text-center section-t-space section-b-space" v-if="totalProductsCount == 0">
            <img src="/images/evacode/empty-search.jpg" class="img-fluid" alt/>
            <h3 class="mt-3">Извините! Не найден товар который Вы искали!!!</h3>
            <div class="col-12 mt-3">
              <nuxt-link :to="{ path: '/collection/leftsidebar/0' }" class="btn btn-solid">Продолжить покупки
              </nuxt-link>
            </div>
          </div>
        </div>
        <div class="col-grid-box col-xl-3 col-md-4 col-6" v-for="(product, index) in products" :key="index">
          <div class="product-box">
            <ProductBoxProductBox1
                @opencartmodel="showCart"
                :product="product"
                :index="index"
            />
          </div>
        </div>
      </div>
    </div>

    <WidgetsProductsPagination
        :totalProductsCount="totalProductsCount"
        :paginationProps="paginationProps"
    />

    <cart-modal-popup
        :openCart="showcartmodal"
        :product="cartproduct"
        @closeCart="closeCartModal"
    />
  </div>
</template>
<script setup>
const props = defineProps({
  products: {
    type: Array,
    required: true,
  },
  paginationProps: {
    type: Object,
    required: true,
  },
  totalProductsCount: {
    type: Number,
    required: true,
  }
});

const showcartmodal = ref(false);
const cartproduct = ref({});
const showCart = (item, product) => {
  showcartmodal.value = item
  cartproduct.value = product
};

const closeCartModal = (item) => {
  showcartmodal.value = item
};
</script>
