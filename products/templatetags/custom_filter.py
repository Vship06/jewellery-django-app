from django import template

register = template.Library()


@register.filter(name="split_images")
def split_images(value):
    """
    Handles JSONField image lists.
    Returns the list directly if it's already a list.
    """
    if isinstance(value, list):
        return value

    return []


@register.filter(name="cart_total_count")
def cart_total_count(cart_dict):
    if not cart_dict:
        return 0
    return sum(int(quantity) for quantity in cart_dict.values())


@register.filter(name="multiply")
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0.0


@register.filter(name="get_cart_grand_total")
def get_cart_grand_total(cart_items_queryset):
    if not cart_items_queryset:
        return 0.0

    try:
        return sum(
            item.quantity * item.productvariant.price
            for item in cart_items_queryset
            if item.productvariant
        )
    except (ValueError, TypeError, AttributeError):
        return 0.0
