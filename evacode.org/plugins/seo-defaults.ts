const PRODUCTION_SITE = 'https://www.evacode.org';
const OG_IMAGE = '/images/new_evacode/Slides/slide_1.jpg';

const stripSlash = (value) => String(value || '').replace(/\/$/, '');

const withSlash = (path) => {
    if (!path || path === '/') {
        return '/';
    }
    return path.endsWith('/') ? path : `${path}/`;
};

export default defineNuxtPlugin(() => {
    const config = useRuntimeConfig();
    const route = useRoute();
    const site = stripSlash(config.public.url || PRODUCTION_SITE) || PRODUCTION_SITE;

    const canonical = () => `${site}${withSlash(route.path)}`;

    useHead({
        link: [
            { rel: 'canonical', href: canonical },
        ],
        meta: [
            { property: 'og:url', content: canonical },
            { property: 'og:image', content: () => `${site}${OG_IMAGE}` },
            { name: 'twitter:image', content: () => `${site}${OG_IMAGE}` },
        ],
        script: [
            {
                type: 'application/ld+json',
                innerHTML: JSON.stringify({
                    '@context': 'https://schema.org',
                    '@type': 'Organization',
                    name: 'EvaCode',
                    alternateName: ['Evacode', 'ЕваКод'],
                    url: `${site}/`,
                    logo: `${site}/images/new_evacode/evacode_header_logo.svg`,
                    email: 'sales@evacode.org',
                    telephone: '+82-10-7652-8595',
                    description:
                        'Интернет-магазин люксовой корейской косметики. Офис в Южной Корее, опт и розница, доставка по миру. Эксклюзивный дистрибьютор CH6.',
                    address: {
                        '@type': 'PostalAddress',
                        streetAddress: 'Beolmang-ro 555, 4th Floor, No. 420',
                        addressLocality: 'Ansan-si',
                        addressRegion: 'Gyeonggi-do',
                        addressCountry: 'KR',
                    },
                    sameAs: [
                        'https://t.me/EvaCodeKR',
                        'https://www.threads.net/@evacodeorg',
                    ],
                }),
            },
        ],
    });
});
