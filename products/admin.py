from django.contrib import admin
from .models import Product, ProductVariant

# Register your models here.


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # This displays your data in a clean, filterable table grid
    list_display = ("name", "sku", "category", "created_at")
    list_filter = ("category",)
    search_fields = ("name", "sku")


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("variant_sku", "product", "price", "stock_count")
    search_fields = ("variant_sku", "product__name")
