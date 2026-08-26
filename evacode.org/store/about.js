import {defineStore} from 'pinia'

export const useAboutStore = defineStore({
	id: 'about-store',
	state: () => {
		return {
			_aboutHome: null,
			_aboutPage: null,
			_aboutFooter: null,
		}
	},
	getters: {
		aboutHome: async (state) => {
			if (!state._aboutHome) {
				let about = {};
				try {
					const aboutResponse = await $fetch(`${useRuntimeConfig().public.apiBase}/core/about?name=about-home`);
					about = aboutResponse?.results[0] || {};
				} catch (error) {
					console.log(error);
					about = {};
				}
				state._aboutHome = about;
			}
			return state._aboutHome;
		},
		aboutPage: async (state) => {
			if (!state._aboutPage) {
				let about = {};
				try {
					const aboutResponse = await $fetch(`${useRuntimeConfig().public.apiBase}/core/about?name=about-page`);
					about = aboutResponse?.results[0] || {};
				} catch (error) {
					console.log(error);
					about = {};
				}
				state._aboutPage = about;
			}
			return state._aboutPage;
		},
		aboutFooter: async (state) => {
			if (!state._aboutFooter) {
				let about = {};
				try {
					const aboutResponse = await $fetch(`${useRuntimeConfig().public.apiBase}/core/about?name=about-footer`);
					about = aboutResponse?.results[0] || {};
				} catch (error) {
					console.log(error);
					about = {};
				}
				state._aboutFooter = about;
			}
			return state._aboutFooter;
		},
		aboutTermsOfUse: async (state) => {
			if (!state._aboutTermsOfUse) {
				try {
					const aboutResponse = await $fetch(`${useRuntimeConfig().public.apiBase}/core/about?name=about-terms-of-use`);
					state._aboutTermsOfUse = aboutResponse?.results[0] || {};
				} catch (error) {
					console.log(error);
					state._aboutTermsOfUse = {};
				}
			}
			return state._aboutTermsOfUse;
		},
		aboutPrivacyPolicy: async (state) => {
			if (!state._aboutPrivacyPolicy) {
				try {
					const aboutResponse = await $fetch(`${useRuntimeConfig().public.apiBase}/core/about?name=about-privacy-policy`);
					state._aboutPrivacyPolicy = aboutResponse?.results[0] || {};
				} catch (error) {
					console.log(error);
					state._aboutPrivacyPolicy = {};
				}
			}
			return state._aboutPrivacyPolicy;
		},
	}
})















