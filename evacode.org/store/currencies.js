import {defineStore} from 'pinia'

export const useCurrenciesStore = defineStore({
    id: 'currencies-store',
	state: () => {
		return {
			_currencies: null,
		}
	},
    getters: {
		currencies: async (state) => {
            if (!state._currencies) {
				try {
					const currenciesResponse = await $fetch(`${useRuntimeConfig().public.apiBase}/core/currencies`);
					state._currencies = currenciesResponse?.currencies || [];
				} catch (error) {
					console.log(error);
					state._currencies = [];
				}
            }
            return state._currencies;
        },
	}
})
