export const useNoIndex = () => {
    useHead({
        meta: [
            { name: 'robots', content: 'noindex, nofollow' },
        ],
    });
};
