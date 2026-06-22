from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView
from django.db.models import Q
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
    paginate_by = 15

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


@require_POST
@login_required
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
            return JsonResponse(
                {
                    "status": "success",
                    "action": "exists",
                    "wishlist_count": request.user.cart_items.filter(
                        status="wishlist"
                    ).count(),
                    "message": "Item already preserved in wishlist.",
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
