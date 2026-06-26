from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView
from django.db.models import Q, Min
from .models import Product, CartItem
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from django.contrib import messages
from django.views import View
from .constants import (
    PRODUCT_CATEGORIES,
    AVAILABLE_METALS,
    AVAILABLE_COLORS,
    AVAILABLE_PURITIES,
    AVAILABLE_CLARITIES,
    AVAILABLE_COLORS_D,
    DEFAULT_PRICE_MIN,
    DEFAULT_PRICE_MAX,
)

# Create your views here.


def get_user_cart(request, status="cart"):
    if request.user.is_authenticated:
        return CartItem.objects.filter(user=request.user, status=status)
    else:
        # Create session if missing
        if not request.session.session_key:
            request.session.create()

        if not request.session.modified:
            request.session.modified = True

        return CartItem.objects.filter(
            session_key=request.session.session_key, status=status
        )


def get_session_key(request):
    """Forces Django to create and save a session cookie for guests."""
    if not request.session.session_key:
        request.session.create()

    request.session.modified = True
    return request.session.session_key


class ProductListView(ListView):
    model = Product
    template_name = "products/home.html"
    context_object_name = "products"
    paginate_by = 16

    def get_queryset(self):
        session = self.request.session

        if self.request.GET.get("clear") == "true":
            session_keys_to_clear = [
                "selected_metals",
                "selected_colors",
                "selected_purities",
                "selected_clarities",
                "selected_dcolors",
                "selected_sub_collection",
                "current_price_min",
                "current_price_max",
                "has_diamonds",
                "sort",
            ]
            for key in session_keys_to_clear:
                session.pop(key, None)
            session.modified = True

        elif self.request.GET:

            filter_keys = [
                "metal",
                "mcolor",
                "purity",
                "clarity",
                "dcolor",
                "sub",
                "price_min",
                "price_max",
                "diamonds",
                "sort",
            ]
            if any(key in self.request.GET for key in filter_keys):
                session["selected_metals"] = self.request.GET.getlist("metal")
                session["selected_colors"] = self.request.GET.getlist("mcolor")
                session["selected_purities"] = self.request.GET.getlist("purity")
                session["selected_clarities"] = self.request.GET.getlist("clarity")
                session["selected_dcolors"] = self.request.GET.getlist("dcolor")
                session["selected_sub_collection"] = self.request.GET.getlist("sub")

                session["current_price_min"] = int(
                    self.request.GET.get(
                        "price_min", session.get("current_price_min", DEFAULT_PRICE_MIN)
                    )
                )
                session["current_price_max"] = int(
                    self.request.GET.get(
                        "price_max", session.get("current_price_max", DEFAULT_PRICE_MAX)
                    )
                )
                session["has_diamonds"] = self.request.GET.get("diamonds")

                if "sort" in self.request.GET:
                    session["sort"] = self.request.GET.get("sort")

                session.modified = True

        queryset = Product.objects.all()

        sort = session.get("sort", "")
        category_slug = self.request.GET.get("category")
        search_query = self.request.GET.get("q")
        has_diamonds = session.get("has_diamonds")

        queryset = queryset.annotate(order_min_price=Min("variants__price"))
        if sort == "descending":
            queryset = queryset.order_by("-order_min_price")
        elif sort == "ascending":
            queryset = queryset.order_by("order_min_price")
        else:
            queryset = queryset.order_by("-created_at")

        if category_slug and category_slug != "all":
            queryset = queryset.filter(category__iexact=category_slug.strip())

        if search_query:
            query_text = search_query.strip()
            queryset = queryset.filter(
                Q(name__icontains=query_text) | Q(category__icontains=query_text)
            )

        filter_mapping = {
            "selected_metals": "variants__base_metal__in",
            "selected_purities": "variants__purity__in",
            "selected_colors": "variants__metal_color__in",
            "selected_clarities": "variants__diamond_clarity__in",
            "selected_dcolors": "variants__diamond_color__in",
            "selected_sub_collection": "description__in",
        }

        active_filters = {}
        for session_key, db_lookup in filter_mapping.items():
            values = session.get(session_key, [])
            if values:
                active_filters[db_lookup] = values

        if active_filters:
            queryset = queryset.filter(**active_filters)

        price_min = session.get("current_price_min", DEFAULT_PRICE_MIN)
        price_max = session.get("current_price_max", DEFAULT_PRICE_MAX)

        variant_filter = Q()
        if price_min:
            queryset = queryset.filter(variants__price__gte=price_min)
            variant_filter &= Q(variants__price__gte=price_min)
        if price_max:
            queryset = queryset.filter(variants__price__lte=price_max)
            variant_filter &= Q(variants__price__lte=price_max)

        queryset = queryset.annotate(
            matched_price=Min("variants__price", filter=variant_filter)
        )

        if has_diamonds == "1":
            queryset = queryset.exclude(variants__diamond_carat__isnull=True).exclude(
                variants__diamond_carat=""
            )

        return queryset.distinct()

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            html_markup = render_to_string(
                "products/partial.html", context=context, request=self.request
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
        session = self.request.session

        context["categories"] = PRODUCT_CATEGORIES
        context["available_metals"] = AVAILABLE_METALS
        context["available_colors"] = AVAILABLE_COLORS
        context["available_purities"] = AVAILABLE_PURITIES
        context["available_clarities"] = AVAILABLE_CLARITIES
        context["available_colors_d"] = AVAILABLE_COLORS_D

        context["db_price_min"] = DEFAULT_PRICE_MIN
        context["db_price_max"] = DEFAULT_PRICE_MAX

        context["available_sub_collection"] = list(
            Product.objects.values_list("description", flat=True)
            .exclude(description__isnull=True)
            .exclude(description="")
            .distinct()
        )

        context["selected_metals"] = session.get("selected_metals", [])
        context["selected_colors"] = session.get("selected_colors", [])
        context["selected_purities"] = session.get("selected_purities", [])
        context["selected_clarities"] = session.get("selected_clarities", [])
        context["selected_dcolors"] = session.get("selected_dcolors", [])
        context["selected_sub_collection"] = session.get("selected_sub_collection", [])

        context["current_price_min"] = session.get(
            "current_price_min", DEFAULT_PRICE_MIN
        )
        context["current_price_max"] = session.get(
            "current_price_max", DEFAULT_PRICE_MAX
        )
        context["has_diamonds"] = session.get("has_diamonds")

        if self.request.user.is_authenticated:
            context["user_wishlist_ids"] = list(
                CartItem.objects.filter(
                    user=self.request.user, status="wishlist"
                ).values_list("product_id", flat=True)
            )
        else:
            context["user_wishlist_ids"] = []

        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = "products/detail.html"
    context_object_name = "product"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user_wishlist_ids = []

        if self.request.user.is_authenticated:

            user_wishlist_ids = list(
                CartItem.objects.filter(
                    user=self.request.user, status="wishlist"
                ).values_list("product_id", flat=True)
            )

        context["user_wishlist_ids"] = user_wishlist_ids
        return context


def cart_view(request, type):
    context = {}
    if type == "cart":
        cart_items = get_user_cart(request, status="cart").select_related(
            "product", "productvariant"
        )

        cart_subtotal = cart_making_charges = cart_tax = cart_metal_charges = (
            cart_diamond_charges
        ) = 0

        for item in cart_items:
            if item.productvariant:
                qty = item.quantity
                price = float(item.productvariant.price or 0)
                making = float(item.productvariant.making_charges or 0)
                tax = float(item.productvariant.tax or 0)
                metal = float(item.productvariant.metal_charges or 0)
                diamond = float(item.productvariant.diamond_charges or 0)

                cart_subtotal += (price - making - tax) * qty
                cart_making_charges += making * qty
                cart_tax += tax * qty
                cart_metal_charges += metal * qty
                cart_diamond_charges += diamond * qty

        context.update(
            {
                "cart_items": cart_items,
                "cart_subtotal": cart_subtotal,
                "cart_making_charges": cart_making_charges,
                "cart_tax": cart_tax,
                "cart_metal_charges": cart_metal_charges,
                "cart_diamond_charges": cart_diamond_charges,
            }
        )
        template = "products/cart.html"
    else:
        wishlist_items = get_user_cart(request, status="wishlist").select_related(
            "product", "productvariant"
        )
        for item in wishlist_items:
            if item.quantity != 1:
                item.quantity = 1
                item.save(update_fields=["quantity"])
        context["cart_items"] = wishlist_items
        template = "products/wishlist.html"

    return render(request, template, context)


@require_POST
def add_to(request, type):
    product_id = request.POST.get("product_id")
    variant_id = request.POST.get("variant_id")
    override_action = request.POST.get("override_action")

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (ValueError, TypeError):
        quantity = 1

    if type == "wishlist":
        quantity = 1

    session_key = None
    if not request.user.is_authenticated:
        session_key = get_session_key(request)

    existing_item = (
        get_user_cart(request, status=type)
        .filter(product_id=product_id, productvariant_id=variant_id)
        .first()
    )

    if existing_item:
        if type == "cart":
            if override_action == "increment":
                existing_item.quantity += quantity
            else:
                existing_item.quantity = quantity
            if existing_item.quantity <= 0:
                existing_item.delete()
            else:
                existing_item.save()
        elif type == "wishlist":
            existing_item.delete()
            total_cart_count = sum(
                item.quantity for item in get_user_cart(request, status="cart")
            )
            total_wishlist_count = get_user_cart(request, status="wishlist").count()
            return JsonResponse(
                {
                    "status": "success",
                    "action": "removed",
                    "cart_count": total_cart_count,
                    "wishlist_count": total_wishlist_count,
                    "message": "Item successfully removed from your wishlist.",
                }
            )

    elif quantity > 0:
        CartItem.objects.create(
            user=request.user if request.user.is_authenticated else None,
            session_key=session_key,
            product_id=product_id,
            productvariant_id=variant_id,
            status=type,
            quantity=quantity,
        )

    # Recalculate totals
    total_cart_count = sum(
        item.quantity for item in get_user_cart(request, status="cart")
    )
    total_wishlist_count = get_user_cart(request, status="wishlist").count()

    return JsonResponse(
        {
            "status": "success",
            "action": "added",
            "cart_count": total_cart_count,
            "wishlist_count": total_wishlist_count,
            "message": f"Successfully allocated to your {type} vault.",
        }
    )


@require_POST
def remove_from(request):
    item_id = request.POST.get("item_id")
    try:
        # Check by user or by session
        if request.user.is_authenticated:
            item_to_delete = CartItem.objects.get(id=item_id, user=request.user)
        else:
            item_to_delete = CartItem.objects.get(
                id=item_id, session_key=request.session.session_key
            )

        item_to_delete.delete()

        remaining_cart_items = get_user_cart(request, status="cart").select_related(
            "productvariant"
        )
        cart_subtotal = cart_making_charges = cart_tax = cart_metal_charges = (
            cart_diamond_charges
        ) = grand_total = total_cart_count = 0

        for item in remaining_cart_items:
            total_cart_count += item.quantity
            if item.productvariant:
                qty = item.quantity
                price = float(item.productvariant.price or 0)
                making = float(item.productvariant.making_charges or 0)
                tax = float(item.productvariant.tax or 0)
                metal = float(item.productvariant.metal_charges or 0)
                diamond = float(item.productvariant.diamond_charges or 0)

                cart_subtotal += (price - making - tax) * qty
                cart_making_charges += making * qty
                cart_tax += tax * qty
                cart_metal_charges += metal * qty
                cart_diamond_charges += diamond * qty
                grand_total += price * qty

        total_wishlist_count = get_user_cart(request, status="wishlist").count()

        return JsonResponse(
            {
                "status": "success",
                "action": "removed",
                "cart_count": total_cart_count,
                "wishlist_count": total_wishlist_count,
                "cart_subtotal": f"{cart_subtotal:.2f}",
                "cart_making_charges": f"{cart_making_charges:.2f}",
                "cart_tax": f"{cart_tax:.2f}",
                "cart_metal_charges": f"{cart_metal_charges:.2f}",
                "cart_diamond_charges": f"{cart_diamond_charges:.2f}",
                "grand_total": f"{grand_total:.2f}",
            }
        )
    except CartItem.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Item not found in vault."}, status=404
        )


class PaymentView(View):

    def get(self, request):
        cart_items = get_user_cart(request, status="cart").select_related(
            "product", "productvariant"
        )

        if not cart_items.exists():
            return redirect("cart-view")

        # Calculate grand total
        grand_total = sum(
            item.productvariant.price * item.quantity for item in cart_items
        )

        context = {"cart_items": cart_items, "cart_total": grand_total}
        return render(request, "products/payment.html", context)

    def post(self, request):
        cart_items = get_user_cart(request, status="cart")

        if not cart_items.exists():
            return redirect("cart-view")

        cart_items.update(status="ordered")

        messages.success(request, "Payment successful! Your order has been placed.")
        return redirect("product-home")
