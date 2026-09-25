from market.models import GoodsModel, ProductBrand


def catalog_sitemap_urls():
    urls = [{"loc": "/collection/leftsidebar/0/"}]
    for slug in (
        ProductBrand.objects.filter(page_published=True)
        .order_by("slug")
        .values_list("slug", flat=True)
    ):
        urls.append({"loc": f"/brand/{slug}/"})
    for pk in (
        GoodsModel.objects.filter(stock__gt=0)
        .order_by("id")
        .values_list("id", flat=True)
    ):
        urls.append({"loc": f"/product/{pk}/"})
    return urls
