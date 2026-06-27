from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.db import transaction
from django.contrib import messages

# Imports
from products.utils import get_user_cart
from .models import Order, OrderItem


class PaymentView(View):
    def get(self, request):
        cart_items = get_user_cart(request, status="cart").select_related(
            "product", "productvariant"
        )
        if not cart_items.exists():
            return redirect("cart-view")

        grand_total = sum(
            item.productvariant.price * item.quantity for item in cart_items
        )
        context = {"cart_items": cart_items, "cart_total": grand_total}
        return render(request, "products/payment.html", context)

    def post(self, request):
        cart_items = get_user_cart(request, status="cart").select_related(
            "product", "productvariant"
        )
        if not cart_items.exists():
            return redirect("cart-view")

        with transaction.atomic():
            # Get the selected payment method
            payment_method = request.POST.get("payment_method", "card")

            # ⭐️ IF COD IS SELECTED, STATUS IS PENDING, OTHERWISE ASSUME PAID
            order_status = "pending" if payment_method == "cod" else "paid"

            # 1. Create the Order
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                full_name=request.POST.get("full_name"),
                phone=request.POST.get("phone"),
                address=request.POST.get("address"),
                city=request.POST.get("city"),
                pincode=request.POST.get("pincode"),
                payment_method=payment_method,
                total_amount=sum(
                    i.productvariant.price * i.quantity for i in cart_items
                ),
                status=order_status,
            )

            # 2. Create OrderItems (Snapshots)
            order_items = []
            for item in cart_items:
                source = item.productvariant
                order_items.append(
                    OrderItem(
                        order=order,
                        product=item.product,
                        product_variant=source,
                        quantity=item.quantity,
                        price_at_purchase=source.price,
                        making_charges=source.making_charges or 0,
                        tax=source.tax or 0,
                        metal_charges=getattr(source, "metal_charges", 0),
                        diamond_charges=getattr(source, "diamond_charges", 0),
                    )
                )

            OrderItem.objects.bulk_create(order_items)

            # 3. Clear Cart
            cart_items.delete()

        messages.success(request, "Order placed successfully!")
        return redirect("order-success", pk=order.id)


class OrderHistoryView(LoginRequiredMixin, ListView):
    model = Order
    template_name = "orders/history.html"
    context_object_name = "orders"

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by("-created_at")


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = "orders/detail.html"
    context_object_name = "order"

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class OrderSuccessView(DetailView):
    model = Order
    template_name = "orders/success.html"
    context_object_name = "order"
