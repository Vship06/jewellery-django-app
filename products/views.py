from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView
from django.db.models import Q
from .models import Product, ProductVariant
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.views.generic import View
from django.template.loader import render_to_string

# Create your views here.


class ProductListView(ListView):
    model = Product
    template_name = "products/home.html"
    context_object_name = "products"
    paginate_by = 15

    def get_queryset(self):
        queryset = Product.objects.all().order_by("-created_at")

        # 1. Exact Category Filter Toggle
        category_slug = self.request.GET.get("category")
        if category_slug and category_slug != "all":
            queryset = queryset.filter(category__iexact=category_slug.strip())

        # 2. Broad Search Bar Logic
        search_query = self.request.GET.get("q")
        if search_query:
            query_text = search_query.strip()
            queryset = queryset.filter(
                Q(name__icontains=query_text) | Q(category__icontains=query_text)
            )

        return queryset

    def render_to_response(self, context, **response_kwargs):

        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            html_markup = render_to_string(
                "products/partial.html", context, request=self.request
            )
            return JsonResponse(
                {
                    "html": html_markup,
                    "has_next": context["page_obj"].has_next(),
                }
            )
        return super().render_to_response(context, **response_kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Product.objects.values_list(
            "category", flat=True
        ).distinct()

        current_category = self.request.GET.get("category", "all")
        context["selected_categories"] = (
            [current_category] if current_category != "all" else []
        )
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = "products/detail.html"
    context_object_name = "product"


@require_POST
def AddToCart(request):
    variant_id = request.POST.get("variant_id")
    quantity = int(request.POST.get("quantity", 1))

    cart = request.session.get("cart", {})
    variant_id = str(variant_id)

    if variant_id in cart:
        cart[variant_id] += quantity
    else:
        cart[variant_id] = quantity

    request.session["cart"] = cart
    request.session.modified = True

    return JsonResponse({"status": "success", "cart_count": sum(cart.values())})


class CartView(View):
    template_name = "products/cart.html"

    def get(self, request, *args, **kwargs):
        cart = request.session.get("cart", {})
        cart_items = []
        grand_total = 0

        for variant_id, quantity in cart.items():
            try:
                variant = ProductVariant.objects.select_related("product").get(
                    id=variant_id
                )
                item_total = variant.price * quantity
                grand_total += item_total

                cart_items.append(
                    {"variant": variant, "quantity": quantity, "item_total": item_total}
                )
            except ProductVariant.DoesNotExist:
                continue

        context = {
            "cart_items": cart_items,
            "grand_total": grand_total,
        }
        return render(request, "products/cart.html", context)

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        variant_id = request.POST.get("variant_id")
        cart = request.session.get("cart", {})

        if variant_id in cart:
            if action == "remove":
                cart.pop(variant_id, None)

            elif action == "update_quantity":
                try:
                    new_quantity = int(request.POST.get("quantity", 1))
                    if new_quantity > 0:
                        cart[variant_id] = new_quantity
                    else:
                        cart.pop(variant_id, None)
                except ValueError:
                    pass

        request.session["cart"] = cart
        request.session.modified = True

        return redirect("product-cart")


@require_POST
def AddToWishList(request):

    variant_id = str(request.POST.get("variant_id"))

    raw_wishlist = request.session.get("wishlist", [])
    wishlist = [str(item) for item in raw_wishlist]

    if variant_id in wishlist:
        wishlist.remove(variant_id)
        action_performed = "removed"
    else:
        wishlist.append(variant_id)
        action_performed = "added"

    request.session["wishlist"] = wishlist
    request.session.modified = True

    return JsonResponse(
        {
            "status": "success",
            "action": action_performed,
            "wishlist_count": len(wishlist),
        }
    )


class WishListView(View):
    template_name = "products/wishlist.html"

    def get(self, request, *args, **kwargs):
        wishlist = request.session.get("wishlist", [])
        wishlist_items = []

        for variant_id in wishlist:
            try:
                variant = ProductVariant.objects.select_related("product").get(
                    id=variant_id
                )
                wishlist_items.append({"variant": variant})
            except ProductVariant.DoesNotExist:
                continue

        context = {"wishlist_items": wishlist_items}
        return render(request, "products/wishlist.html", context)

    def post(self, request, *args, **kwargs):

        action = request.POST.get("action")
        variant_id = str(request.POST.get("variant_id"))

        raw_wishlist = request.session.get("wishlist", [])
        wishlist = [str(item) for item in raw_wishlist]

        if variant_id in wishlist:

            if action in ["remove", "removed"]:
                wishlist.remove(variant_id)

        request.session["wishlist"] = wishlist
        request.session.modified = True

        return redirect("product-wishlist")
