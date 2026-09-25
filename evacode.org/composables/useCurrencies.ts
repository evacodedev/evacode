import useLocalStorage from './useLocalStorage';

const STORAGE_KEY = '_evacodeCurrencies_v4';
const TTL_MS = 60 * 60 * 1000; // 1 hour

export default function useCurrencies() {
    const storage = useLocalStorage();

    const getCurrencies = async () => {
        const cached = storage.getItem<{ fetchedAt?: number; currencies?: unknown } | unknown[]>(
            STORAGE_KEY,
            null as any,
        );
        if (cached && !Array.isArray(cached) && Array.isArray(cached.currencies) && cached.fetchedAt) {
            if (Date.now() - cached.fetchedAt < TTL_MS) {
                return cached.currencies;
            }
        }

        let result: any[] = [];
        try {
            const currenciesResponse = await $fetch(
                `${useRuntimeConfig().public.apiBase}/core/currencies`,
            ) as any;
            result = currenciesResponse?.currencies || [];
        } catch (err: any) {
            // eslint-disable-next-line no-console
            console.error('Error when receiving currencies:', err);
            if (cached && !Array.isArray(cached) && Array.isArray(cached.currencies)) {
                return cached.currencies;
            }
            if (Array.isArray(cached)) {
                return cached;
            }
        }
        if (result.length) {
            storage.setItem(STORAGE_KEY, { fetchedAt: Date.now(), currencies: result });
        }
        return result;
    };

    return {
        getCurrencies,
    };
}
