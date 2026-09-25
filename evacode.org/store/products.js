import {defineStore} from 'pinia'
import { convertKrwWithCurr } from '~/utils/currencyPrice'

export const useProductStore = defineStore({
    id: 'product-store',
    state: () => {
        return {
            currency: {
                value: 'KRW',
                curr: 1,
                symbol: '₩',
                locale: 'ko-KR',
            },
            order: [],
        }
    },
    actions: {
        createOrder(payload) {
            this.order = payload
        },
        getPrice(price) {
            const amount = convertKrwWithCurr(price, this.currency.value, this.currency.curr);
            return new Intl.NumberFormat(this.currency.locale, {
                style: "currency",
                currency: this.currency.value,
            }).format(amount);
        },
		setCurrency(currency) {
			this.currency.value = currency.value;
			this.currency.curr = currency.curr;
			this.currency.locale = currency.locale || 'en-US';
			this.currency.symbol = currency.symbol || this.currency.symbol;
		}
    },
    getters: {
        changeCurrency: (state) => {
            return state.currency
        },
        getOrder: (state) => {
            return state.order
        }
    },
})
