import {defineStore} from 'pinia'

export const useCartStore = defineStore({
    id: 'cart-store',
    state: () => {
        return {
            cart: [],
            abc: {}
        }
    },
    actions: {
        addToCart(payloadProduct) {
            console.log('jemin')
            const cartItems = this.cart.find(item => item.id === payloadProduct.id)
            const qty = payloadProduct.quantity ? payloadProduct.quantity : 1
            if (cartItems) {
                cartItems.quantity += qty
            } else {
                this.cart.push({
                    ...payloadProduct,
                    quantity: qty
                })
            }
        },
        updateCartQuantity(payload) {
            function calculateStockCounts(product, quantity) {
                const qty = product.quantity + quantity
                const stock = product.stock
                if (stock < qty) {
                    return false
                }
                return true
            }

            this.cart.find((items, index) => {
                if (items.id === payload.product.id) {
                    const qty = this.cart[index].quantity + payload.qty
                    const stock = calculateStockCounts(this.cart[index], payload.qty)
                    if (qty !== 0 && stock) {
                        this.cart[index].quantity = qty
                    } else {
                        // state.cart.push({
                        //   ...product,
                        //   quantity: qty
                        // })
                    }
                    return true
                }
            })
        },
        removeCartItem(payload) {
            this.cart = this.cart.filter((item) => item.id != payload.id)
        },
        setInitialCart(payload) {
            this.cart = payload
        }
    },
    getters: {
        cartItems: (state) => {
            return state.cart
        },
        cartTotalAmount: (state) => {
            return state.cart.reduce((total, product) => {
                return total + (product.retail_price * product.quantity)
            }, 0)
        },
        cartTotalOfficialAmount: (state) => {
            return state.cart.reduce((total, product) => {
                return total + (product.official_price * product.quantity)
            }, 0)
        }
    }
})















