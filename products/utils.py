from .models import CartItem


def get_session_key(request):
    if not request.session.session_key:
        request.session.create()
    request.session.modified = True
    return request.session.session_key


def get_user_cart(request, status="cart"):
    if request.user.is_authenticated:
        return CartItem.objects.filter(user=request.user, status=status)
    else:
        session_key = get_session_key(request)
        return CartItem.objects.filter(session_key=session_key, status=status)
