export default function useLocalStorage() {
    const storage = localStorage;

    function setItem<T>(key: string, value: T): void {
        storage.setItem(key, JSON.stringify(value));
    }

    function getItem<T>(key: string, def: T): T {
        const item = storage.getItem(key);
        return item ? JSON.parse(item) as T : def;
    }

    function removeItem(key: string): void {
        storage.removeItem(key);
    }

    return {
        setItem,
        getItem,
        removeItem,
    };
}
