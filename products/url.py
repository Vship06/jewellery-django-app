from django.urls import path
from . import views as product_views

urlpatterns = [
    path("", product_views.ProductListView.as_view(), name="product-home"),
    path(
        "product/<int:pk>/",
        product_views.ProductDetailView.as_view(),
        name="product-detail",
    ),
    path("product/cart/", product_views.CartView.as_view(), name="product-cart"),
    path("product/add-to-cart/", product_views.AddToCart, name="product-add-to-cart"),
    path(
        "product/add-to-wishlist/",
        product_views.AddToWishList,
        name="product-add-to-wishlist",
    ),
    path(
        "product/wishlist/",
        product_views.WishListView.as_view(),
        name="product-wishlist",
    ),
]
