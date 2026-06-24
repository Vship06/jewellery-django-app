from django.db.models import Sum


def vault_counters(request):
    # Move model imports inside the function to prevent AppRegistryNotReady crashes on startup
    from .models import CartItem, Product

    # Fetch unique categories dynamically from the product records
    categories = Product.objects.values_list("category", flat=True).distinct()
    current_category = request.GET.get("category", "all")
    selected_categories = [current_category] if current_category != "all" else []

    # Initialize default counter states
    cart_qty = 0
    wish_qty = 0

    if request.user.is_authenticated:
        # High-efficiency database sum aggregation for cart items
        cart_data = CartItem.objects.filter(user=request.user, status="cart").aggregate(
            total_quantity=Sum("quantity")
        )

        cart_qty = cart_data["total_quantity"] or 0

        # Count total wishlist records
        wish_qty = CartItem.objects.filter(user=request.user, status="wishlist").count()

    # Unified single return dictionary statement
    return {
        "cart_count": cart_qty,
        "wishlist_count": wish_qty,
        "categories": categories,
        "selected_categories": selected_categories,
    }
