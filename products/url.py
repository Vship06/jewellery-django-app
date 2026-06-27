from django.urls import path
from . import views as product_views

urlpatterns = [
    path("", product_views.ProductListView.as_view(), name="product-home"),
    path(
        "product/<int:pk>/",
        product_views.ProductDetailView.as_view(),
        name="product-detail",
    ),
    path(
        "product/add-to-cart/",
        product_views.add_to,
        {"type": "cart"},
        name="product-add-cart",
    ),
    path(
        "product/add-to-wishlist/",
        product_views.add_to,
        {"type": "wishlist"},
        name="product-add-wishlist",
    ),
    path("product/remove-item/", product_views.remove_from, name="product-remove"),
    path("product/cart/", product_views.cart_view, {"type": "cart"}, name="cart-view"),
    path(
        "product/wishlist/",
        product_views.cart_view,
        {"type": "wishlist"},
        name="wishlist-view",
    ),
]
