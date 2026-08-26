<template>
    <div class="cart-product" v-if="product && product.id">
        <nuxt-link class="product-image-link" :to="{ path: '/product/sidebar/' + product.id }">
            <img :src="product.images[0].url" alt/>
        </nuxt-link>
        <table class="table cart-table table-responsive-xs">
            <thead>
            <tr class="table-head">
                <th scope="col">Товар</th>
                <th scope="col">Цена</th>
                <th scope="col">Количество</th>
                <th scope="col">Удалить</th>
                <th scope="col">Сумма</th>
            </tr>
            </thead>
            <tbody>
            <tr>
                <td>
                    <nuxt-link :to="{ path: '/product/sidebar/' + product.id }">{{
                            product.title
                        }}
                    </nuxt-link>
                    <div class="mobile-cart-content row">
                        <div class="col-xs-3">
                            <div class="qty-box">
                                <div class="input-group">
                                                    <span class="input-group-prepend">
                                                      <button type="button" class="btn quantity-left-minus"
                                                              data-type="minus" data-field
                                                              @click="decrement(product)">
                                                        <i class="ti-angle-left"></i>
                                                      </button>
                                                    </span>
                                    <input type="text" name="quantity" class="form-control input-number"
                                           v-model="product.quantity"/>
                                    <span class="input-group-prepend">
                                                      <button type="button" class="btn quantity-right-plus"
                                                              data-type="plus" data-field
                                                              @click="increment(product)">
                                                        <i class="ti-angle-right"></i>
                                                      </button>
                                                    </span>
                                </div>
                            </div>
                        </div>
                        <div class="col-xs-3">
                            <h2 class="td-color">
                                {{ getPrice(product.retail_price * product.quantity) }}
                                <del>{{ getPrice(product.official_price * product.quantity) }}</del>
                            </h2>
                        </div>
                        <div class="col-xs-3">
                            <h2 class="td-color">
                                <a class="icon" href="#" @click.prevent="removeCartItem(product)">
                                    <i class="ti-close"></i>
                                </a>
                            </h2>
                        </div>
                    </div>
                </td>
                <td>
                    <h2>{{ getPrice(product.retail_price) }}
                        <del>{{ getPrice(product.official_price) }}</del>
                    </h2>
                </td>
                <td>
                    <div class="qty-box">
                        <div class="input-group">
                                            <span class="input-group-prepend">
                                              <button type="button" class="btn quantity-left-minus" data-type="minus"
                                                      data-field
                                                      @click="decrement(product)">
                                                <i class="ti-angle-left"></i>
                                              </button>
                                            </span>
                            <input type="text" name="quantity" class="form-control input-number"
                                   :disabled="product.quantity > product.stock"
                                   v-model="product.quantity"/>
                            <span class="input-group-prepend">
                                              <button type="button" class="btn quantity-right-plus" data-type="plus"
                                                      data-field
                                                      @click="increment(product)">
                                                <i class="ti-angle-right"></i>
                                              </button>
                                            </span>
                        </div>
                    </div>
                </td>
                <td>
                    <a class="icon" href="#" @click.prevent="removeCartItem(product)">
                        <i class="ti-close"></i>
                    </a>
                </td>
                <td>
                    <h2>
                        {{ getPrice(product.retail_price * product.quantity) }}
                        <del>{{ getPrice(product.official_price * product.quantity) }}</del>
                    </h2>
                </td>
            </tr>
            </tbody>
        </table>
    </div>
</template>

<script>
import {useProductStore} from '~~/store/products'
import {useCartStore} from '~~/store/cart'

export default {
    props: {
        product: {
            type: Object,
            default: 0,
        }
    },
    methods: {
        removeCartItem(product) {
            useCartStore().removeCartItem(product)
        },
        increment(product, qty = 1) {
            useCartStore().updateCartQuantity({
                product: product,
                qty: qty
            })
        },
        decrement(product, qty = -1) {
            useCartStore().updateCartQuantity({
                product: product,
                qty: qty
            })
        },
        getPrice: function (price) {
            return useProductStore().getPrice(price);
        }
    },
}
</script>
