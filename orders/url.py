from django.urls import path
from . import views

urlpatterns = [
    path("order/checkout/", views.PaymentView.as_view(), name="order-payment"),
    path("order/history/", views.OrderHistoryView.as_view(), name="order-history"),
    path("order/<int:pk>/", views.OrderDetailView.as_view(), name="order-detail"),
    path(
        "order/success/<int:pk>/",
        views.OrderSuccessView.as_view(),
        name="order-success",
    ),
]
