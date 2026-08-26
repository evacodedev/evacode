import {defineStore} from 'pinia'

export const useDeliveryStore = defineStore({
    id: 'delivery-store',
    state: () => {
        return {
            _deliveries: null,
        }
    },
    getters: {
        deliveries: async (state) => {
            if (import.meta.server) {
                return state._deliveries;
            }
            if (!state._deliveries) {
                try {
                    const deliveriesResponse = await $fetch(`${useRuntimeConfig().public.apiBase}/core/delivery`);
                    const deliveries = deliveriesResponse?.results || [];
                    state._deliveries = deliveries;
                } catch (error) {
                    console.error(error);
                    state._deliveries = [];
                }
            }
            return state._deliveries;
        },
    }
})














