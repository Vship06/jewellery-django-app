from decimal import Decimal, InvalidOperation
from django import template

register = template.Library()


@register.filter
def split_images(value):
    """
    Returns the list of image URLs from a JSONField.
    If the value isn't a list, return an empty list.
    """
    return value if isinstance(value, list) else []


@register.filter
def cart_total_count(cart_dict):
    """
    Returns the total quantity of items in the cart.
    """
    if not cart_dict:
        return 0

    try:
        return sum(int(quantity) for quantity in cart_dict.values())
    except (ValueError, TypeError):
        return 0


@register.filter
def multiply(value, arg):
    """
    Multiplies two numbers.
    """
    try:
        return Decimal(str(value)) * Decimal(str(arg))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0.00")


@register.filter
def get_cart_grand_total(cart_items):
    """
    Calculates the grand total of all cart items.
    """
    if not cart_items:
        return Decimal("0.00")

    total = Decimal("0.00")

    for item in cart_items:
        try:
            if item.productvariant:
                total += Decimal(str(item.productvariant.price)) * item.quantity
        except (AttributeError, InvalidOperation, TypeError):
            continue

    return total
