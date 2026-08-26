import {defineStore} from 'pinia'

export const useTestimonialsStore = defineStore({
    id: 'testimonials-store',
	state: () => {
		return {
			_testimonials: null,
		}
	},
    getters: {
        testimonials: async (state) => {
            if (!state._testimonials) {
				try {
					const testimonialsResponse = await $fetch(`${useRuntimeConfig().public.apiBase}/core/review`);
					state._testimonials = testimonialsResponse?.results || [];
				} catch (error) {
					console.log(error);
					state._testimonials = [];
				}
            }
            return state._testimonials;
        },
	}
})
