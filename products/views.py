from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView
from django.db.models import Q, Min, Max
from .models import Product, ProductVariant, CartItem
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string

# Create your views here.


class ProductListView(ListView):
    model = Product
    template_name = "products/home.html"
    context_object_name = "products"
    paginate_by = 16

    def get_queryset(self):
        queryset = Product.objects.all().order_by("-created_at")

        category_slug = self.request.GET.get("category")
        if category_slug and category_slug != "all":
            queryset = queryset.filter(category__iexact=category_slug.strip())

        search_query = self.request.GET.get("q")
        if search_query:
            query_text = search_query.strip()
            queryset = queryset.filter(
                Q(name__icontains=query_text) | Q(category__icontains=query_text)
            )

        price_min = self.request.GET.get("price_min")
        price_max = self.request.GET.get("price_max")

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

        metal_type = self.request.GET.getlist("metal")

        if metal_type:
            queryset = queryset.filter(variants__base_metal__in=metal_type)

        purities = self.request.GET.getlist("purity")
        if purities:
            queryset = queryset.filter(variants__purity__in=purities)

        mcolors = self.request.GET.getlist("mcolor")
        if mcolors:
            queryset = queryset.filter(variants__metal_color__in=mcolors)

        if self.request.GET.get("diamonds") == "1":

            queryset = queryset.exclude(variants__diamond_carat__isnull=True).exclude(
                variants__diamond_carat=""
            )

        clarity = self.request.GET.getlist("clarity")
        if clarity:
            queryset = queryset.filter(variants__diamond_clarity__in=clarity)

        color = self.request.GET.getlist("dcolor")
        if color:
            queryset = queryset.filter(variants__diamond_color__in=color)

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

        context["categories"] = Product.objects.values_list(
            "category", flat=True
        ).distinct()

        variants_qs = ProductVariant.objects.all()

        context["available_metals"] = list(
            variants_qs.values_list("base_metal", flat=True)
            .exclude(base_metal__isnull=True)
            .exclude(base_metal="")
            .distinct()
        )
        context["available_colors"] = list(
            variants_qs.values_list("metal_color", flat=True)
            .exclude(metal_color__isnull=True)
            .exclude(metal_color="")
            .distinct()
        )
        context["available_purities"] = list(
            variants_qs.values_list("purity", flat=True)
            .exclude(purity__isnull=True)
            .exclude(purity="")
            .distinct()
        )
        context["available_clarities"] = list(
            variants_qs.values_list("diamond_clarity", flat=True)
            .exclude(diamond_clarity__isnull=True)
            .exclude(diamond_clarity="")
            .distinct()
        )
        context["available_colors_d"] = list(
            variants_qs.values_list("diamond_color", flat=True)
            .exclude(diamond_color__isnull=True)
            .exclude(diamond_color="")
            .distinct()
        )

        price_bounds = ProductVariant.objects.aggregate(
            absolute_min=Min("price", default=0),
            absolute_max=Max("price", default=1000000),
        )

        db_min = 0
        db_max = int(price_bounds["absolute_max"])

        context["db_price_min"] = db_min
        context["db_price_max"] = db_max

        # Selected query tracking (to keep options checked on page refresh)
        context["selected_metals"] = self.request.GET.getlist("metal")
        context["selected_colors"] = self.request.GET.getlist("mcolor")
        context["selected_purities"] = self.request.GET.getlist("purity")
        context["selected_clarities"] = self.request.GET.getlist("clarity")
        context["selected_dcolors"] = self.request.GET.getlist("dcolor")

        context["current_price_min"] = int(self.request.GET.get("price_min", db_min))
        context["current_price_max"] = int(self.request.GET.get("price_max", db_max))

        context["has_diamonds"] = self.request.GET.get("diamonds")

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


@login_required
def CartView(request, type):

    context = {}

    if type == "cart":
        context["cart_items"] = CartItem.objects.filter(
            user=request.user, status="cart"
        ).select_related("product", "productvariant")
        template = "products/cart.html"

    else:
        wishlist_items = CartItem.objects.filter(
            user=request.user, status="wishlist"
        ).select_related("product", "productvariant")

        for item in wishlist_items:
            if item.quantity != 1:
                item.quantity = 1
                item.save(update_fields=["quantity"])

        context["cart_items"] = wishlist_items
        template = "products/wishlist.html"
    return render(request, template, context)


@login_required
@require_POST
def AddTo(request, type):
    product_id = request.POST.get("product_id")
    variant_id = request.POST.get("variant_id")
    override_action = request.POST.get("override_action")

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (ValueError, TypeError):
        quantity = 1

    if type == "wishlist":
        quantity = 1

    existing_item = CartItem.objects.filter(
        user=request.user,
        product_id=product_id,
        productvariant_id=variant_id,
        status=type,
    ).first()

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
                item.quantity for item in request.user.cart_items.filter(status="cart")
            )
            total_wishlist_count = request.user.cart_items.filter(
                status="wishlist"
            ).count()
            return JsonResponse(
                {
                    "status": "success",
                    "action": "removed",
                    "cart_count": total_cart_count,
                    "wishlist_count": total_wishlist_count,
                    "message": "Item successfully removed from your wishlist.",
                }
            )
    else:

        if quantity > 0:
            CartItem.objects.create(
                user=request.user,
                product_id=product_id,
                productvariant_id=variant_id,
                status=type,
                quantity=quantity,
            )

    # Recalculate totals for the navbar
    total_cart_count = sum(
        item.quantity for item in request.user.cart_items.filter(status="cart")
    )
    total_wishlist_count = request.user.cart_items.filter(status="wishlist").count()

    return JsonResponse(
        {
            "status": "success",
            "action": "added",
            "cart_count": total_cart_count,
            "wishlist_count": total_wishlist_count,
            "message": f"Successfully allocated to your {type} vault.",
        }
    )


@login_required
@require_POST
def RemoveFrom(request):
    item_id = request.POST.get("item_id")

    try:

        item_to_delete = CartItem.objects.get(id=item_id, user=request.user)
        item_to_delete.delete()

        total_cart_count = sum(
            item.quantity for item in request.user.cart_items.filter(status="cart")
        )
        total_wishlist_count = request.user.cart_items.filter(status="wishlist").count()

        return JsonResponse(
            {
                "status": "success",
                "action": "removed",
                "cart_count": total_cart_count,
                "wishlist_count": total_wishlist_count,
                "message": "Item successfully removed from your vault.",
            }
        )

    except CartItem.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Item not found in vault."}, status=404
        )
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)
