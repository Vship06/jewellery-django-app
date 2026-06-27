from django.db.models import Sum
from .models import CartItem, Product


def vault_counters(request):
    """
    Globally makes cart_count, wishlist_count, and categories
    available to all templates.
    """
    # 1. Fetch dynamic categories once per request
    categories = Product.objects.values_list("category", flat=True).distinct()
    current_category = request.GET.get("category", "all")
    selected_categories = [current_category] if current_category != "all" else []

    # 2. Determine base queryset based on Auth status
    if request.user.is_authenticated:
        base_query = CartItem.objects.filter(user=request.user)
    elif request.session.session_key:
        base_query = CartItem.objects.filter(session_key=request.session.session_key)
    else:
        # If guest has no session yet, return defaults
        return {
            "cart_count": 0,
            "wishlist_count": 0,
            "categories": categories,
            "selected_categories": selected_categories,
        }

    # 3. Efficient Aggregations
    cart_data = base_query.filter(status="cart").aggregate(total=Sum("quantity"))
    cart_qty = cart_data["total"] or 0
    wish_qty = base_query.filter(status="wishlist").count()

    return {
        "cart_count": cart_qty,
        "wishlist_count": wish_qty,
        "categories": categories,
        "selected_categories": selected_categories,
    }
