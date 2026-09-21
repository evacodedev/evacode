from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import Post, Contacts, AboutUs, Banner, Delivery, Slide, Review, SectionWithVideo, Currency, AccountProfile


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


admin.site.register(Delivery, DeliveryAdmin)
# admin.site.register(Post, PostAdmin)
admin.site.register(AboutUs, AboutUsAdmin)
admin.site.register(Contacts, ContactsAdmin)
admin.site.register(Currency, CurrencyAdmin)
# admin.site.register(Slide, SlideAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(AccountProfile)
# admin.site.register(SectionWithVideo, SectionWithVideoAdmin)
