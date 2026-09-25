from decimal import Decimal

from django.db import models
from django.conf import settings
from django.utils import timezone
from ckeditor_uploader.fields import RichTextUploadingField
from taggit.managers import TaggableManager
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator


class Post(models.Model):
    h1 = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    slug = models.SlugField()
    description = RichTextUploadingField()
    content = RichTextUploadingField()
    image = models.ImageField(upload_to='images/')
    created_at = models.DateField(default=timezone.now)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    tags = TaggableManager()

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    username = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_name')
    text = models.TextField()
    created_date = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_date']

    def __str__(self):
        return self.text


class Banner(models.Model):
    name = models.CharField(verbose_name="Поле для поиска", max_length=128)
    title = models.CharField(verbose_name="Название", max_length=128)
    image = models.ImageField(upload_to="images/")

    class Meta:
        verbose_name = 'Баннер'
        verbose_name_plural = 'Баннеры'

    def __str__(self):
        return self.name


class AboutUs(models.Model):
    name = models.CharField(verbose_name="Поле для поиска", max_length=128)
    # image = models.ImageField(verbose_name="Картинка", upload_to="images/")
    title = models.CharField(verbose_name="Название", max_length=128)
    description = RichTextUploadingField()

    class Meta:
        verbose_name = 'О нас'
        verbose_name_plural = 'О нас'

    def __str__(self):
        return self.name


class Delivery(models.Model):
    delivery_type = models.CharField(verbose_name="Тип доставки", max_length=128)
    delivery_description = RichTextUploadingField()

    class Meta:
        verbose_name = 'Доставка'
        verbose_name_plural = 'Доставка'

    def __str__(self):
        return self.delivery_type


class Slide(models.Model):
    image = models.ImageField(verbose_name="Картинка", upload_to="images/")
    title = models.CharField(verbose_name="Название", max_length=128)
    description = RichTextUploadingField()

    class Meta:
        verbose_name = 'Слайд'
        verbose_name_plural = 'Слайды'

    def __str__(self):
        return self.title


class Contacts(models.Model):
    telegram = models.CharField(verbose_name="Telegram", max_length=128)
    instagram = models.CharField(verbose_name="Instagram", max_length=128)
    facebook = models.CharField(verbose_name="Facebook", max_length=128)
    address = models.CharField(verbose_name="Address", max_length=256)
    phone = models.CharField(verbose_name="Phone", max_length=128)
    email = models.CharField(verbose_name="Email", max_length=128)
    tiktok = models.CharField(verbose_name="TikTok", max_length=128, null=True)

    class Meta:
        verbose_name = 'Контакт'
        verbose_name_plural = 'Контакты'

    def __str__(self):
        return "Контакты"


class Review(models.Model):
    avatar = models.ImageField(verbose_name="Аватар", upload_to="images/reviews/avatars/")
    name = models.CharField(verbose_name="ФИО", max_length=128)
    rating = models.IntegerField(verbose_name="Рейтинг", validators=[MaxValueValidator(5), MinValueValidator(0)])
    text = RichTextUploadingField(verbose_name="Текст отзыва")
    country = models.CharField(verbose_name="Страна", max_length=128)
    review_photo = models.ImageField(verbose_name="Фото", upload_to="images/reviews/photos/")

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'

    def __str__(self):
        return self.name


class SectionWithVideo(models.Model):
    video_file = models.FileField(verbose_name="Видео", upload_to='videos/')
    name = models.CharField(verbose_name="Название", max_length=128)

    class Meta:
        verbose_name = 'Секция с видео'
        verbose_name_plural = 'Секции с видео'

    def __str__(self):
        return self.name


class Currency(models.Model):
    name = models.CharField(max_length=128, verbose_name='Название курса')
    value = models.DecimalField(verbose_name="Курс валюты", max_digits=10, decimal_places=4)
    key = models.CharField(max_length=128, verbose_name='Ключ')

    class Meta:
        verbose_name = 'Курсы валюты'
        verbose_name_plural = 'Курсы валют'

    def __str__(self):
        return f'{self.name} - {self.value}'


class CurrencyPair(models.Model):
    """Официальная пара: исконный API (ЦБ+Frankfurter) × коэффициент → коммерческий."""

    base = models.CharField("База", max_length=3, default="KRW")
    quote = models.CharField("Котировка", max_length=3)
    name = models.CharField("Название", max_length=64, blank=True)
    symbol = models.CharField("Символ", max_length=8, blank=True)
    draft_rate = models.DecimalField(
        "Исконный курс (API)",
        max_digits=18,
        decimal_places=10,
        null=True,
        blank=True,
        help_text="Курс с Frankfurter + ЦБ. Подтягивается кнопкой в админке.",
    )
    draft_source = models.CharField("Источник API", max_length=64, blank=True)
    draft_updated_at = models.DateTimeField("API обновлён", null=True, blank=True)
    markup = models.DecimalField(
        "Коэффициент",
        max_digits=8,
        decimal_places=4,
        default=Decimal("1.0000"),
        help_text="Только в админке: коммерческий = исконный API × коэффициент. На витрину не уходит.",
    )
    rate = models.DecimalField(
        "Коммерческий курс",
        max_digits=18,
        decimal_places=10,
        help_text="Исконный API × коэффициент. Используется на витрине, в калькуляторе и PayPal.",
    )
    sort = models.PositiveSmallIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активна", default=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Пара валют"
        verbose_name_plural = "Пары валют (KRW→)"
        ordering = ("sort", "quote")
        constraints = [
            models.UniqueConstraint(fields=("base", "quote"), name="uniq_currency_pair_base_quote"),
        ]

    def apply_commercial_from_api(self) -> bool:
        """Коммерческий = исконный API × коэффициент. False, если API ещё нет."""
        from core.currency_pricing import compute_commercial_rate

        if self.draft_rate is None or self.draft_rate <= 0:
            return False
        self.rate = compute_commercial_rate(self.draft_rate, self.markup)
        return True

    def __str__(self):
        return f"{self.base}/{self.quote} = {self.rate}"


class AccountProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="account_profile")
    phone = models.CharField("Телефон", max_length=64, blank=True)
    birth_date = models.DateField("Дата рождения", null=True, blank=True)
    whatsapp = models.CharField("WhatsApp", max_length=64, blank=True)
    telegram = models.CharField("Telegram", max_length=64, blank=True)

    class Meta:
        verbose_name = "Профиль покупателя"
        verbose_name_plural = "Профили покупателей"

    def __str__(self):
        return self.user.email or self.user.username


class AccountAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="account_addresses")
    country = models.CharField("Страна", max_length=64, blank=True)
    country_code = models.CharField("Код страны", max_length=8, blank=True)
    city = models.CharField("Город", max_length=128)
    street = models.CharField("Улица", max_length=255)
    house = models.CharField("Дом", max_length=32)
    apartment = models.CharField("Квартира", max_length=32, blank=True)
    postal_code = models.CharField("Индекс", max_length=32)
    comment = models.CharField("Комментарий", max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        verbose_name = "Адрес доставки"
        verbose_name_plural = "Адреса доставки"

    def __str__(self):
        return f"{self.country}, {self.city}, {self.street}, {self.house}".strip(", ")
