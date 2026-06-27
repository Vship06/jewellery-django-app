from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView
from django.db.models import Q, Min, Sum
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


def get_user_cart(request, status="cart"):
    if request.user.is_authenticated:
        return CartItem.objects.filter(user=request.user, status=status)
    else:
        session_key = get_session_key(request)
        return CartItem.objects.filter(session_key=session_key, status=status)


def get_session_key(request):
    if not request.session.session_key:
        request.session.create()
    request.session.modified = True
    return request.session.session_key


class ProductListView(ListView):
    model = Product
    template_name = "products/home.html"
    context_object_name = "products"
    paginate_by = 16

    def get(self, request, *args, **kwargs):
        self._update_session_state(request)
        return super().get(request, *args, **kwargs)

    def _update_session_state(self, request):
        session = request.session

        # 1. Clear Session
        if request.GET.get("clear") == "true":
            keys_to_clear = [
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
            for key in keys_to_clear:
                session.pop(key, None)
            session.modified = True
            return

        # 2. Update Session
        if request.GET:
            list_params = {
                "metal": "selected_metals",
                "mcolor": "selected_colors",
                "purity": "selected_purities",
                "clarity": "selected_clarities",
                "dcolor": "selected_dcolors",
                "sub": "selected_sub_collection",
            }
            for get_key, session_key in list_params.items():
                if get_key in request.GET:
                    session[session_key] = request.GET.getlist(get_key)

            if "price_min" in request.GET:
                session["current_price_min"] = int(
                    request.GET.get("price_min", DEFAULT_PRICE_MIN)
                )
            if "price_max" in request.GET:
                session["current_price_max"] = int(
                    request.GET.get("price_max", DEFAULT_PRICE_MAX)
                )
            if "diamonds" in request.GET:
                session["has_diamonds"] = request.GET.get("diamonds")
            if "sort" in request.GET:
                session["sort"] = request.GET.get("sort")

            session.modified = True

    def get_queryset(self):
        session = self.request.session
        queryset = Product.objects.all().annotate(
            order_min_price=Min("variants__price")
        )

        # 1. Sorting
        sort = session.get("sort", "")
        if sort == "descending":
            queryset = queryset.order_by("-order_min_price")
        elif sort == "ascending":
            queryset = queryset.order_by("order_min_price")
        else:
            queryset = queryset.order_by("-created_at")

        # 2. Search & Robust Category Filters
        category_slug = self.request.GET.get("category")
        if category_slug and category_slug != "all":
            # Normalize the input (e.g., 'NOSE PIN' -> 'nose pin')
            slug_lower = category_slug.strip().lower()

            # This map bridges your CONSTANT names to your MODEL DB keys
            category_map = {
                "finger ring": "ring",
                "nose pin": "nosepin",
                "earrings": "earring",
                "bangle": "bangle",
                "bracelet": "bracelet",
                "necklace": "necklace",
                "chain": "chain",
                "pendant": "pendant",
            }
            # Fallback to slug_lower if it's already a clean key
            db_category = category_map.get(slug_lower, slug_lower)
            queryset = queryset.filter(category__iexact=db_category)

        search_query = self.request.GET.get("q")
        if search_query:
            query_text = search_query.strip()
            queryset = queryset.filter(
                Q(name__icontains=query_text) | Q(category__icontains=query_text)
            )

        # 3. Dynamic Attribute Filters
        filter_mapping = {
            "selected_metals": "variants__base_metal__in",
            "selected_purities": "variants__purity__in",
            "selected_colors": "variants__metal_color__in",
            "selected_clarities": "variants__diamond_clarity__in",
            "selected_dcolors": "variants__diamond_color__in",
            "selected_sub_collection": "description__in",
        }
        active_filters = {
            db_lookup: session.get(session_key)
            for session_key, db_lookup in filter_mapping.items()
            if session.get(session_key)
        }
        if active_filters:
            queryset = queryset.filter(**active_filters)

        # 4. Safe Price & Diamond Filters
        price_min = session.get("current_price_min", DEFAULT_PRICE_MIN)
        price_max = session.get("current_price_max", DEFAULT_PRICE_MAX)

        is_price_filtered = False
        variant_filter = Q()

        # Only apply price filters if they differ from the defaults!
        # This stops variantless products (like chains/bracelets) from disappearing.
        if price_min is not None and int(price_min) > DEFAULT_PRICE_MIN:
            variant_filter &= Q(variants__price__gte=price_min)
            is_price_filtered = True

        if price_max is not None and int(price_max) < DEFAULT_PRICE_MAX:
            variant_filter &= Q(variants__price__lte=price_max)
            is_price_filtered = True

        if is_price_filtered:
            queryset = queryset.filter(variant_filter)
            queryset = queryset.annotate(
                matched_price=Min("variants__price", filter=variant_filter)
            )
        else:
            # Keep annotation for the template, but don't filter out products
            queryset = queryset.annotate(matched_price=Min("variants__price"))

        if session.get("has_diamonds") == "1":
            queryset = queryset.exclude(
                Q(variants__diamond_carat__isnull=True) | Q(variants__diamond_carat="")
            )

        return queryset.distinct()

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            html_markup = render_to_string(
                "products/partial.html", context=context, request=self.request
            )
            return JsonResponse(
                {"html": html_markup, "has_next": context["page_obj"].has_next()}
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

        # ADDED: Send session sort to template so it doesn't rely on stale request.GET URLs
        context["current_sort"] = session.get("sort", "")

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
            source = item.productvariant if item.productvariant else item.product
            if source:
                qty = item.quantity
                price = float(source.price or 0)
                making = float(source.making_charges or 0)
                tax = float(source.tax or 0)
                metal = float(getattr(source, "metal_charges", 0) or 0)
                diamond = float(getattr(source, "diamond_charges", 0) or 0)

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
        wishlist_items.exclude(quantity=1).update(quantity=1)
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
            cart_data = get_user_cart(request, status="cart").aggregate(
                total=Sum("quantity")
            )
            total_cart_count = cart_data["total"] or 0
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

    cart_data = get_user_cart(request, status="cart").aggregate(total=Sum("quantity"))
    total_cart_count = cart_data["total"] or 0
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
        if request.user.is_authenticated:
            item_to_delete = CartItem.objects.get(id=item_id, user=request.user)
        else:
            item_to_delete = CartItem.objects.get(
                id=item_id, session_key=request.session.session_key
            )

        item_to_delete.delete()
        remaining_cart_items = get_user_cart(request, status="cart").select_related(
            "product", "productvariant"
        )
        cart_subtotal = cart_making_charges = cart_tax = cart_metal_charges = (
            cart_diamond_charges
        ) = grand_total = total_cart_count = 0

        for item in remaining_cart_items:
            total_cart_count += item.quantity
            source = item.productvariant if item.productvariant else item.product

            if source:
                qty = item.quantity
                price = float(source.price or 0)
                making = float(source.making_charges or 0)
                tax = float(source.tax or 0)
                metal = float(getattr(source, "metal_charges", 0) or 0)
                diamond = float(getattr(source, "diamond_charges", 0) or 0)

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

        grand_total = 0
        for item in cart_items:
            source = item.productvariant if item.productvariant else item.product
            if source and source.price:
                grand_total += float(source.price) * item.quantity

        context = {"cart_items": cart_items, "cart_total": grand_total}
        return render(request, "products/payment.html", context)

    def post(self, request):
        cart_items = get_user_cart(request, status="cart")
        if not cart_items.exists():
            return redirect("cart-view")
        cart_items.update(status="ordered")
        messages.success(request, "Payment successful! Your order has been placed.")
        return redirect("product-home")
