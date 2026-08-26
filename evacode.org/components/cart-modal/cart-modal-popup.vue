<template>
  <div></div>
  <div>

    <div class="modal-backdrop fade show" v-if="openCart"></div>

    <div class="modal fade show d-block bd-example-modal-lg theme-modal cart-modal" id="modal-cart"
         aria-hidden="true" tabindex="-1" role="dialog" aria-labelledby="modal-cartLabel" v-if="openCart">
      <div class="modal-dialog modal-lg modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-body modal1">
            <div class="container-fluid p-0">
              <div class="row cart-modal">
                <div class="col-lg-12 position-relative">
                  <div class="modal-bg addtocart">
                    <button class="close btn-close" type="button" @click="closeCart(openCart)">
                      <span>x</span>
                    </button>
                    <div class="media">
                      <a href="#">
                        <img :src="product.images[0].url" class="img-fluid"
                             :alt="product.images[0].alt"/>
                      </a>
                      <div class="media-body align-self-center text-center">
                        <a href="#">
                          <h6>
                            <i class="fa fa-check"></i>Товар
                            <span>{{ product.title }}</span>
                            <span> успешно добавлен в корзину.</span>
                          </h6>
                        </a>
                        <div class="buttons d-flex justify-content-center">
                          <nuxt-link :to="{ path: '/page/account/cart' }"
                                     class="btn-sm btn-solid mr-2">Посмотреть корзину
                          </nuxt-link>
                          <nuxt-link :to="{ path: '/page/account/checkout' }"
                                     class="btn-sm btn-solid mr-2">Оформить заказ
                          </nuxt-link>
                          <button class="btn-sm btn-solid" @click="closeCart(openCart)">Продолжить покупки</button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  openCart:{
    type: Boolean,
    default: false,
  },
  product: {
    type: Object,
    default: {},
  }
});

const emit = defineEmits(['closeCart']);

const closeCart = (val) => {
  val = false
  emit('closeCart', val)
};
</script>
