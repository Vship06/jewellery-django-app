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
    image_link = models.URLField(max_length=2000, blank=True, null=True)
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

    metal_type = models.CharField(
        max_length=50, blank=True, null=True
    )  # e.g., '18k Yellow Gold'
    diamond_color = models.CharField(
        max_length=100, blank=True, null=True
    )  # e.g., 'G-H'
    diamond_clarity = models.CharField(
        max_length=100, blank=True, null=True
    )  # e.g., 'SI1'

    diamond_pcs = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Number of diamond pieces (e.g., '14', '42 Center & Accents')",
    )

    gross_weight = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="e.g., '5.24g' or '12.5 Grams'",
    )

    carat_weight = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="e.g., '0.50', '0.75 TCW', or '0.50 Center / 0.25 Accents'",
    )

    # Size variations
    size_or_length = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="e.g., Ring Size 6, 18-inch chain, 2.4 bangle",
    )

    price = models.DecimalField(max_digits=12, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    stock_count = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.product.name} - {self.metal_type} - {self.price}"


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
