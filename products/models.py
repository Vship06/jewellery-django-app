from django.db import models
from django.contrib.auth.models import User


class Product(models.Model):

    CATEGORY_CHOICES = [
        ("ring", "Ring"),
        ("pendant", "Pendant"),
        ("nosepin", "Nosepin"),
        ("necklace", "Necklace"),
        ("earring", "Earrings"),
        ("chain", "Chain"),
        ("bracelet", "Bracelet"),
        ("bangle", "Bangle"),
    ]

    name = models.CharField(max_length=150)
    sku = models.CharField(max_length=50, unique=True)
    product_link = models.URLField(max_length=500, blank=True, null=True)
    image_links = models.JSONField(default=list, blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="ring")
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.get_category_display()}] {self.name}"


class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="variants"
    )
    variant_sku = models.CharField(max_length=100, unique=True)

    base_metal = models.CharField(max_length=50, blank=True, null=True)
    metal_color = models.CharField(max_length=50, blank=True, null=True)
    purity = models.CharField(max_length=20, blank=True, null=True)

    diamond_clarity = models.CharField(max_length=100, blank=True, null=True)
    diamond_color = models.CharField(max_length=100, blank=True, null=True)
    diamond_cut = models.CharField(max_length=100, blank=True, null=True)
    diamond_carat = models.CharField(max_length=255, blank=True, null=True)
    diamond_pcs = models.CharField(max_length=255, blank=True, null=True)

    net_weight = models.DecimalField(
        max_digits=10, decimal_places=3, blank=True, null=True
    )
    gross_weight = models.DecimalField(
        max_digits=10, decimal_places=3, blank=True, null=True
    )
    stone_weight = models.DecimalField(
        max_digits=10, decimal_places=3, blank=True, null=True
    )

    metal_charges = models.DecimalField(
        max_digits=12, decimal_places=4, blank=True, null=True
    )
    making_charges = models.DecimalField(
        max_digits=12, decimal_places=4, blank=True, null=True
    )
    making_charges_discount = models.DecimalField(
        max_digits=12, decimal_places=4, blank=True, null=True, default=0
    )

    diamond_charges = models.DecimalField(
        max_digits=12, decimal_places=4, blank=True, null=True
    )
    diamond_charges_discount = models.DecimalField(
        max_digits=12, decimal_places=4, blank=True, null=True, default=0
    )

    tax = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    price = models.DecimalField(max_digits=12, decimal_places=4)
    max_price = models.DecimalField(
        max_digits=12, decimal_places=4, blank=True, null=True
    )

    size_or_length = models.CharField(max_length=100, blank=True, null=True)
    stock_count = models.IntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        metal_desc = f"{self.purity or ''} {self.metal_color or ''} {self.base_metal or ''}".strip()
        return f"{self.product.name} - {metal_desc} - Rs. {self.price}"


class CartItem(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="product_cart_items"
    )

    productvariant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, related_name="variant_cart_items"
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cart_items")

    quantity = models.IntegerField(default=1)

    status = models.CharField(max_length=15, default="cart")

    added_at = models.DateTimeField(auto_now_add=True)
