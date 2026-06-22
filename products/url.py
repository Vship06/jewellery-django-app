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
        product_views.AddTo,
        {"type": "cart"},
        name="product-add-cart",
    ),
    path(
        "product/add-to-wishlist/",
        product_views.AddTo,
        {"type": "wishlist"},
        name="product-add-wishlist",
    ),
    path("product/remove-item/", product_views.RemoveFrom, name="product-remove"),
    path("product/cart/", product_views.CartView, {"type": "cart"}, name="cart-view"),
    path(
        "product/wishlist/",
        product_views.CartView,
        {"type": "wishlist"},
        name="wishlist-view",
    ),
]
