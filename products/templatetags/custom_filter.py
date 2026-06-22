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
