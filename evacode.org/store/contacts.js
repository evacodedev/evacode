import {defineStore} from 'pinia'

export const useContactsStore = defineStore({
    id: 'contacts-store',
    state: () => {
        return {
            _contacts: null,
        }
    },
    getters: {
        contacts: async (state) => {
            if (import.meta.server) {
                return state._contacts;
            }
            if (!state._contacts) {
				try {
					const contactsResponse = await $fetch(`${useRuntimeConfig().public.apiBase}/core/contacts`);
					const contacts = contactsResponse?.results[0] || {};
					state._contacts = contacts;
				} catch (error) {
					console.error(error);
					state._contacts = null;
				}
            }
            return state._contacts;
        },
    }
})














