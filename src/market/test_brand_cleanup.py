from django.core.management import call_command
from django.test import TestCase

from market.brand_cleanup import cleanup_product_brands
from market.models import GoodsModel, GroupOfGoods, ProductBrand, ProductBrandI18n


class BrandCleanupTests(TestCase):
    def setUp(self):
        self.category = GroupOfGoods.objects.create(
            id=10,
            default_order="1",
            deleted=False,
            name="Маски",
            updated="2024-01-01T00:00:00Z",
        )

    def _brand(self, slug, name):
        brand = ProductBrand.objects.create(slug=slug)
        ProductBrandI18n.objects.create(brand=brand, language="ru", name=name)
        return brand

    def _good(self, pk, title, brand):
        return GoodsModel.objects.create(
            id=pk,
            title=title,
            category=self.category,
            type="goods",
            stock=1,
            content_brand=brand,
        )

    def test_merges_product_slug_and_duplicate_name(self):
        hera = self._brand("hera", "hera")
        lip = self._brand("hera-lip-serum", "HERA Lip Serum")
        holitual = self._brand("holitual", "Holitual mist")
        wrong = self._brand("HERA", "HOLITUAL Power Renewal Kit")
        skin = self._brand("23skin-lab", "23Skin Lab")
        film = self._brand("sanarae-collagen-film-s", "SANARAE COLLAGEN FILM S")
        pdhayi = self._brand("pdhayi", "pdhayi")
        leftover = self._brand("dr", "DR")
        g_lip = self._good(1, "HERA Lip Serum", lip)
        g_wrong = self._good(2, "HOLITUAL Power Renewal Kit", wrong)
        g_film = self._good(3, "M-PACK SANARAE COLLAGEN FILM S", film)
        g_pdh = self._good(4, "P.D.HAYi HiOME Shampoo", pdhayi)
        g_cura = self._good(5, "Dr. Cura Hydro Moisture Mask", leftover)
        g_oregamo = self._good(6, "DR. Oregamo Enzyme Cleansing Powder", leftover)

        stats = cleanup_product_brands()

        g_lip.refresh_from_db()
        g_wrong.refresh_from_db()
        g_film.refresh_from_db()
        g_pdh.refresh_from_db()
        g_cura.refresh_from_db()
        g_oregamo.refresh_from_db()
        hera.refresh_from_db()
        holitual.refresh_from_db()
        skin.refresh_from_db()
        pdhayi.refresh_from_db()

        self.assertEqual(g_lip.content_brand_id, hera.id)
        self.assertEqual(g_wrong.content_brand_id, holitual.id)
        self.assertEqual(g_film.content_brand_id, skin.id)
        self.assertEqual(g_pdh.content_brand_id, pdhayi.id)
        self.assertEqual(g_cura.content_brand.slug, "dr-cura")
        self.assertEqual(str(g_cura.content_brand), "Dr. Cura")
        self.assertEqual(g_oregamo.content_brand.slug, "dr-oregamo")
        self.assertEqual(str(g_oregamo.content_brand), "DR. Oregamo")
        self.assertEqual(str(hera), "HERA")
        self.assertEqual(str(holitual), "HOLITUAL")
        self.assertEqual(skin.slug, "23-skin-lab")
        self.assertEqual(str(skin), "23 Skin Lab")
        self.assertEqual(str(pdhayi), "PDHAYi")
        self.assertFalse(ProductBrand.objects.filter(slug="hera-lip-serum").exists())
        self.assertFalse(ProductBrand.objects.filter(slug="sanarae-collagen-film-s").exists())
        self.assertFalse(ProductBrand.objects.filter(slug="dr").exists())
        leftover_slugs = [brand.slug for brand in stats["leftover"]]
        self.assertEqual(leftover_slugs, [])

    def test_dry_run_does_not_write(self):
        hera = self._brand("hera", "HERA")
        lip = self._brand("hera-lip-serum", "HERA Lip Serum")
        self._good(1, "HERA Lip Serum", lip)
        cleanup_product_brands(dry_run=True)
        lip.refresh_from_db()
        self.assertEqual(ProductBrand.objects.filter(slug__in=("hera", "hera-lip-serum")).count(), 2)
        self.assertEqual(lip.goods.count(), 1)
        self.assertEqual(hera.goods.count(), 0)

    def test_command_apply(self):
        hera = self._brand("hera", "HERA")
        lip = self._brand("hera-lip-serum", "HERA Lip Serum")
        good = self._good(1, "HERA Lip Serum", lip)
        call_command("cleanup_product_brands")
        good.refresh_from_db()
        self.assertEqual(good.content_brand_id, hera.id)
        self.assertEqual(ProductBrand.objects.filter(slug="hera-lip-serum").count(), 0)
