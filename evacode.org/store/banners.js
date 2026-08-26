import {defineStore} from 'pinia'

export const useBannersStore = defineStore({
    id: 'banner-store',
    state: () => {
        return {
            _bannerShop: null,
            _bannerShopSide: null,
        }
    },
    getters: {
        bannerShop: async (state) => {
            if (!state._bannerShop) {
				try {
					const bannerShopTopResponse = await $fetch(`${useRuntimeConfig().public.apiBase}/core/banner?name=shop-top-banner`);
					const bannerShop = bannerShopTopResponse?.results[0] || {};
					state._bannerShop = bannerShop;
				} catch (error) {
					console.log(error);
					state._bannerShop = null;
				}
            }
            return state._bannerShop;
        },
        bannerShopSide: async (state) => {
            if (!state._bannerShopSide) {
				try {
					const bannerShopSideResponse = await $fetch(`${useRuntimeConfig().public.apiBase}/core/banner?name=shop-side-banner`);
					const bannerShopSide = bannerShopSideResponse?.results[0] || {};
					state._bannerShopSide = bannerShopSide;
				} catch (error) {
					console.log(error);
					state._bannerShopSide = null;
				}
            }
            return state._bannerShopSide;
        },
    }
})















