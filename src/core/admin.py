from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils.safestring import mark_safe

from .currency_pairs import accept_drafts, refresh_drafts
from .models import (
    Post,
    Contacts,
    AboutUs,
    Banner,
    Delivery,
    Slide,
    Review,
    SectionWithVideo,
    Currency,
    CurrencyPair,
    AccountProfile,
    AccountAddress,
)


class PostAdmin(admin.ModelAdmin):
    pass


class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('delivery_type',)


# class BannerAdmin(admin.ModelAdmin):
#     list_display = ('title',)
#     readonly_fields = ('get_image',)
#
#     def get_image(self, obj):
#         return mark_safe(f'<img src={obj.image.url} width="200">')
#
#     get_image.short_description = "Изображение"


class AboutUsAdmin(admin.ModelAdmin):
    list_display = ('name',)


class ContactsAdmin(admin.ModelAdmin):
    pass


# class SectionWithVideoAdmin(admin.ModelAdmin):
#     pass


# class SlideAdmin(admin.ModelAdmin):
#     list_display = ('title', 'get_image')
#     readonly_fields = ('get_image',)
#
#     def get_image(self, obj):
#         return mark_safe(f'<img src={obj.image.url} width="200">')
#
#     get_image.short_description = "Изображение"


class ReviewAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_avatar', 'get_photo')
    readonly_fields = ('get_avatar', 'get_photo')

    def get_avatar(self, obj):
        return mark_safe(f'<img src={obj.avatar.url} width="200">')

    def get_photo(self, obj):
        return mark_safe(f'<img src={obj.review_photo.url} width="200">')

    get_avatar.short_description = "Аватар"
    get_photo.short_description = "Фото отзыва"


class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'value')
    actions = None

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


@admin.register(CurrencyPair)
class CurrencyPairAdmin(admin.ModelAdmin):
    change_list_template = "admin/core/currencypair/change_list.html"
    list_display = (
        "quote",
        "name",
        "draft_rate",
        "markup",
        "rate",
        "draft_source",
        "draft_updated_at",
        "sort",
        "is_active",
        "updated_at",
    )
    list_editable = ("markup", "sort", "is_active")
    list_filter = ("is_active", "draft_source")
    search_fields = ("quote", "name")
    ordering = ("sort", "quote")
    readonly_fields = (
        "draft_rate",
        "draft_source",
        "draft_updated_at",
        "rate",
        "updated_at",
    )
    fields = (
        "base",
        "quote",
        "name",
        "symbol",
        "draft_rate",
        "draft_source",
        "draft_updated_at",
        "markup",
        "rate",
        "sort",
        "is_active",
        "updated_at",
    )

    def save_model(self, request, obj, form, change):
        # Смена коэффициента сразу пересчитывает коммерческий, если API уже подтянут.
        if obj.draft_rate:
            obj.apply_commercial_from_api()
        super().save_model(request, obj, form, change)

    def get_urls(self):
        urls = super().get_urls()
        extra = [
            path(
                "refresh-drafts/",
                self.admin_site.admin_view(self.refresh_drafts_view),
                name="core_currencypair_refresh_drafts",
            ),
            path(
                "accept-drafts/",
                self.admin_site.admin_view(self.accept_drafts_view),
                name="core_currencypair_accept_drafts",
            ),
        ]
        return extra + urls

    def refresh_drafts_view(self, request):
        list_url = reverse("admin:core_currencypair_changelist")
        if request.method != "POST":
            return redirect(list_url)
        try:
            result = refresh_drafts()
            messages.success(
                request,
                f"Исконные API курсы обновлены: {', '.join(result['updated']) or '—'}"
                + (f"; нет в источнике: {', '.join(result['missing'])}" if result["missing"] else "")
                + ". Нажмите «Коммерческий = API × коэффициент», чтобы применить.",
            )
        except Exception as exc:
            messages.error(request, f"Не удалось подтянуть API курсы: {exc}")
        return redirect(list_url)

    def accept_drafts_view(self, request):
        list_url = reverse("admin:core_currencypair_changelist")
        if request.method != "POST":
            return redirect(list_url)
        accepted = accept_drafts()
        if accepted:
            messages.success(
                request,
                f"Коммерческий курс = исконный API × коэффициент: обновлено пар — {accepted}",
            )
        else:
            messages.warning(request, "Нет исконных API курсов. Сначала подтяните ЦБ + Frankfurter.")
        return redirect(list_url)

    @admin.action(description="Коммерческий = API × коэффициент (выбранные)")
    def accept_selected_drafts(self, request, queryset):
        quotes = list(queryset.values_list("quote", flat=True))
        accepted = accept_drafts(quotes=quotes)
        self.message_user(
            request,
            f"Коммерческий пересчитан: {accepted}",
            messages.SUCCESS,
        )

    actions = ("accept_selected_drafts",)


admin.site.register(Delivery, DeliveryAdmin)
# admin.site.register(Post, PostAdmin)
admin.site.register(AboutUs, AboutUsAdmin)
admin.site.register(Contacts, ContactsAdmin)
admin.site.register(Currency, CurrencyAdmin)
# admin.site.register(Slide, SlideAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(AccountProfile)
admin.site.register(AccountAddress)
# admin.site.register(SectionWithVideo, SectionWithVideoAdmin)
