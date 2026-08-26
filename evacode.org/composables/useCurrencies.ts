import useLocalStorage from './useLocalStorage';

export default function useCurrencies() {
    const storage = useLocalStorage();
    const storageKey = '_evacodeCurrencies';

    const getCurrencies = async () => {
        let result = storage.getItem<string>(storageKey, '');
        if (result) {
            return result;
        }
        try {
            const currenciesResponse = await $fetch(`${useRuntimeConfig().public.apiBase}/core/currencies`)  as any ;
            result = currenciesResponse?.currencies || [];
        } catch (err: any) {
            // eslint-disable-next-line no-console
            console.error('Error when receiving the countryCode:', err);
        }
        if (result) {
            storage.setItem(storageKey, result);
        }
        return result;
    };

    return {
        getCurrencies,
    };
}
