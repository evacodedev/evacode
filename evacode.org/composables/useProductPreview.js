export const useProductPreview = () => {
    const preview = useState('product-preview', () => null);

    const setPreview = (product) => {
        preview.value = product ? { ...product } : null;
    };

    const previewFor = (id) => {
        if (!preview.value || id == null) {
            return null;
        }
        return String(preview.value.id) === String(id) ? preview.value : null;
    };

    return { preview, setPreview, previewFor };
};
