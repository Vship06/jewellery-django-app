from django import template

register = template.Library()


@register.filter(name="split_images")
def split_images(value):
    if value:
        # Splits the string by '|' and removes any empty spaces
        return [url.strip() for url in value.split("|") if url.strip()]
    return []


@register.filter(name="cart_total_count")
def cart_total_count(cart_dict):
    if not cart_dict:
        return 0
    # Add up the items instead of counting just dictionary tracking keys!
    return sum(int(quantity) for quantity in cart_dict.values())


@register.filter(name="multiply")
def multiply(value, arg):
    """
    Multiplies the template float/int variable by the argument.
    Usage in template: {{ item.quantity|multiply:item.productvariant.price }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0.0


@register.filter(name="get_cart_grand_total")
def get_cart_grand_total(cart_items_queryset):
    """
    Loops through database Cart_item rows to sum up the aggregate grand total.
    Usage in template: {{ cart_items|get_cart_grand_total }}
    """
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
