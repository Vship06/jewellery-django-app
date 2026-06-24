// static/js/wishlist.js

document.addEventListener("DOMContentLoaded", function () {
    
    // ========================================================
    // BLOCK 1: UNIVERSAL CATALOG GRID HEART TOGGLES (EVENT DELEGATION)
    // ========================================================
    document.body.addEventListener("click", function (e) {
        // Find if the clicked element belongs to a wishlist toggle heart button
        const heartBtn = e.target.closest(".card-wishlist-btn");
        if (!heartBtn) return;

        e.preventDefault();
        e.stopPropagation();

        const productId = heartBtn.getAttribute("data-product-id");
        const variantId = heartBtn.getAttribute("data-variant-id");
        
        // Grab the active CSRF protection token safely from your layout container
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;

        // Package the values up cleanly to pass directly to Django's AddTo view
        const dataPayload = new FormData();
        dataPayload.append("product_id", productId);
        dataPayload.append("variant_id", variantId);
        dataPayload.append("quantity", 1);

        // ── 🟢 FIXED: Added leading absolute slash so paths don't break on sub-pages
        fetch("/product/add-to-wishlist/", {
            method: "POST",
            body: dataPayload,
            headers: {
                "X-Requested-With": "XMLHttpRequest",
                "X-CSRFToken": csrfToken
            }
        })
        .then(response => {
            if (!response.ok) throw new Error("Wishlist pipeline response sync error.");
            return response.json();
        })
        .then(data => {
            if (data.status === "success") {
                // Target the matching structural layout element counters
                const cartCounter = document.getElementById("cart-counter");
                const wishlistCounter = document.getElementById("wishlist-counter");

                if (cartCounter) {
                    cartCounter.innerText = data.cart_count;
                    cartCounter.classList.toggle("d-none", parseInt(data.cart_count) === 0);
                }

                if (wishlistCounter) {
                    wishlistCounter.innerText = data.wishlist_count;
                    wishlistCounter.classList.toggle("d-none", parseInt(data.wishlist_count) === 0);
                }

                // Seamlessly transition the heart fill styling states
                const targetHeartIcon = heartBtn.querySelector("i");
                if (targetHeartIcon) {
                    if (data.action === "added") {
                        targetHeartIcon.className = "bi bi-heart-fill";
                        targetHeartIcon.style.setProperty("color", "#800020", "important");
                    } else if (data.action === "removed") {
                        targetHeartIcon.className = "bi bi-heart text-muted";
                        targetHeartIcon.style.color = "";
                    }
                }
            }
        })
        .catch(err => console.error("Grid heart background toggle execution failed:", err));
    });

    // ========================================================
    // 🟢 NEW BLOCK 1B: PRODUCT CARD QUICK ADD-TO-CART (EVENT DELEGATION)
    // ========================================================
    document.body.addEventListener("click", function (e) {
        const cartBtn = e.target.closest(".card-add-to-cart-btn");
        if (!cartBtn) return;

        e.preventDefault();
        e.stopPropagation();

        const productId = cartBtn.getAttribute("data-product-id");
        const variantId = cartBtn.getAttribute("data-variant-id");
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;

        const dataPayload = new FormData();
        dataPayload.append("product_id", productId);
        dataPayload.append("variant_id", variantId);
        dataPayload.append("quantity", 1);
        dataPayload.append("override_action", "increment");

        const originalHtml = cartBtn.innerHTML;
        cartBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-1" role="status" style="width: 0.7rem; height: 0.7rem;"></span> Adding...`;
        cartBtn.disabled = true;

        fetch("/product/add-to-cart/", {
            method: "POST",
            body: dataPayload,
            headers: {
                "X-Requested-With": "XMLHttpRequest",
                "X-CSRFToken": csrfToken
            }
        })
        .then(response => {
            if (!response.ok) throw new Error("Cart pipeline quick transmission rejected.");
            return response.json();
        })
        .then(data => {
            if (data.status === "success") {
                const cartCounter = document.getElementById("cart-counter");
                const wishlistCounter = document.getElementById("wishlist-counter");

                if (cartCounter) {
                    cartCounter.innerText = data.cart_count;
                    cartCounter.classList.toggle("d-none", parseInt(data.cart_count) === 0);
                }
                if (wishlistCounter) {
                    wishlistCounter.innerText = data.wishlist_count;
                    wishlistCounter.classList.toggle("d-none", parseInt(data.wishlist_count) === 0);
                }

                cartBtn.innerHTML = `<i class="bi bi-check2-all me-1"></i> Added`;
                cartBtn.className = "btn btn-sm btn-success rounded-0 px-2 py-1 text-uppercase tracking-wider";
                
                setTimeout(() => {
                    cartBtn.innerHTML = originalHtml;
                    cartBtn.className = "btn btn-sm btn-outline-dark rounded-0 px-2 py-1 text-uppercase tracking-wider card-add-to-cart-btn";
                    cartBtn.disabled = false;
                }, 2000);
            }
        })
        .catch(err => {
            console.error("Quick add execution failed:", err);
            cartBtn.innerHTML = originalHtml;
            cartBtn.disabled = false;
        });
    });

    // ========================================================
    // BLOCK 2: PRODUCT DETAIL SHOWROOM INTERCEPTOR (AJAX)
    // ========================================================
    const detailWishlistBtn = document.getElementById("detail-wishlist-toggle-btn");
    
    if (detailWishlistBtn) {
        detailWishlistBtn.addEventListener("click", function(e) {
            e.preventDefault();
            e.stopPropagation(); 
            e.stopImmediatePropagation(); 

            const activeVariantSelector = document.getElementById("variant-selector");
            const csrfTokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
            const activeForm = document.getElementById("add-to-vault-form");
            
            if (!activeVariantSelector || !csrfTokenElement) {
                console.error("Required detail showroom elements are missing from the DOM.");
                return;
            }

            const currentSelectedVariantId = activeVariantSelector.value;
            const dataPayload = new FormData();
            
            if (activeForm) {
                const productId = activeForm.querySelector('[name="product_id"]');
                if (productId) dataPayload.append("product_id", productId.value);
            }
            
            dataPayload.append("variant_id", currentSelectedVariantId);
            dataPayload.append("type", "wishlist");
            dataPayload.append("quantity", "1"); 
            dataPayload.append("csrfmiddlewaretoken", csrfTokenElement.value);

            fetch("/product/add-to-wishlist/", {
                method: "POST",
                body: dataPayload,
                headers: { "X-Requested-With": "XMLHttpRequest" }
            })
            .then(response => {
                if (!response.ok) throw new Error("Server rejected wishlist allocation.");
                return response.json();
            })
            .then(data => {
                if (data.status === "success" || data.action === "exists") {
                    const detailHeart = document.getElementById("detail-heart-icon");
                    const detailText = document.getElementById("detail-wishlist-text");

                    if (detailHeart.classList.contains("bi-heart")) {
                        detailHeart.className = "bi bi-heart-fill me-2";
                        detailHeart.style.setProperty("color", "#800020", "important");
                        detailText.innerText = "In Your Wishlist";
                    } else {
                        detailHeart.className = "bi bi-heart me-2";
                        detailHeart.style.color = "";
                        detailText.innerText = "Add To Wishlist Vault";
                    }

                    const wishlistCounter = document.getElementById("wishlist-counter");
                    if (wishlistCounter) {
                        wishlistCounter.innerText = data.wishlist_count;
                        wishlistCounter.classList.toggle("d-none", parseInt(data.wishlist_count) === 0);
                    }
                    
                    const toast = document.getElementById("luxury-notification");
                    const toastMsg = document.getElementById("toast-message");
                    if (toast && toastMsg && data.action !== "exists") {
                        toastMsg.innerText = "Successfully allocated to your wishlist vault.";
                        toast.classList.add("show");
                        setTimeout(() => { toast.classList.remove("show"); }, 3500);
                    }
                }
            })
            .catch(err => console.error("Detail page view synchronization failed:", err));
        });
    }

    // ========================================================
    // BLOCK 3: PRODUCT DETAIL CART SUBMISSION INTERCEPTOR
    // ========================================================
    const detailCartForm = document.getElementById("add-to-vault-form");
    
    if (detailCartForm) {
        detailCartForm.addEventListener("submit", function(e) {
            e.preventDefault(); 
            e.stopImmediatePropagation();

            const dataPayload = new FormData(this);
            dataPayload.append("type", "cart"); 

            fetch("/product/add-to-cart/", {
                method: "POST",
                body: dataPayload,
                headers: { "X-CSRFToken": dataPayload.get("csrfmiddlewaretoken") }
            })
            .then(response => {
                if (!response.ok) throw new Error("Cart pipeline transmission error.");
                return response.json();
            })
            .then(data => {
                if (data.status === "success") {
                    const cartCounter = document.getElementById("cart-counter");
                    if (cartCounter) {
                        cartCounter.innerText = data.cart_count;
                        cartCounter.classList.remove("d-none");
                    }
                    
                    const toast = document.getElementById("luxury-notification");
                    const toastMsg = document.getElementById("toast-message");
                    if (toast && toastMsg) {
                        toastMsg.innerText = "Added to your shopping vault.";
                        toast.classList.add("show");
                        setTimeout(() => { toast.classList.remove("show"); }, 3500);
                    }
                }
            })
            .catch(err => console.error("Detail cart submission failed:", err));
        });
    }

    // ========================================================
    // BLOCK 4: WISHLIST PAGE CARD FADER REMOVER (AJAX)
    // ========================================================
    document.addEventListener("submit", function(e) {
        const removeForm = e.target.closest(".ajax-wishlist-remove-form");
        if (!removeForm) return;

        e.preventDefault(); 
        e.stopImmediatePropagation();

        const dataPayload = new FormData(removeForm);
        const itemCard = removeForm.closest(".wishlist-item-card");
        const targetRemovalUrl = removeForm.getAttribute("action") || "/product/remove-item/";

        fetch(targetRemovalUrl, { 
            method: "POST",
            body: dataPayload,
            headers: { "X-Requested-With": "XMLHttpRequest" }
        })
        .then(response => {
            if (!response.ok) throw new Error("Removal transaction rejected by server.");
            return response.json();
        })
        .then(data => {
            if (data.status === "success" && data.action === "removed") {
                const wishlistCounter = document.getElementById("wishlist-counter");
                if (wishlistCounter) {
                    wishlistCounter.innerText = data.wishlist_count;
                    wishlistCounter.classList.toggle("d-none", parseInt(data.wishlist_count) === 0);
                }

                itemCard.style.transition = "all 0.4s ease";
                itemCard.style.opacity = "0";
                itemCard.style.transform = "scale(0.9)";
                
                setTimeout(() => {
                    itemCard.remove();
                    if (document.querySelectorAll(".wishlist-item-card").length === 0) {
                        window.location.reload();
                    }
                }, 400);
            }
        })
        .catch(err => console.error("Wishlist dynamic deletion error log:", err));
    });
    
    // ========================================================
    // BLOCK 5: WISHLIST PAGE ASYNCHRONOUS CART INJECTOR (AJAX)
    // ========================================================
    document.addEventListener("submit", function(e) {
        const cartForm = e.target.closest(".ajax-wishlist-add-to-cart-form");
        if (!cartForm) return;

        e.preventDefault(); 
        e.stopImmediatePropagation();

        const dataPayload = new FormData(cartForm);
        const targetCartUrl = cartForm.getAttribute("action") || "/product/add-to-cart/";

        fetch(targetCartUrl, {
            method: "POST",
            body: dataPayload
        })
        .then(response => {
            if (!response.ok) throw new Error("Vault routing execution failed.");
            return response.json();
        })
        .then(data => {
            if (data.status === "success") {
                const counterElement = document.getElementById("cart-counter");
                if (counterElement) {
                    counterElement.innerText = data.cart_count;
                    counterElement.classList.remove("d-none");
                }

                const toast = document.getElementById("luxury-notification") || document.getElementById("toast");
                const toastMsg = document.getElementById("toast-message");

                if (toast && toastMsg) {
                    toastMsg.innerText = "Added to your shopping vault.";
                    toast.classList.add("show");
                    setTimeout(() => { toast.classList.remove("show"); }, 3500);
                }
            }
        })
        .catch(err => console.error("Wishlist-to-cart transition failed:", err));
    });
    
    // ========================================================
    // BLOCK 6: MANUAL EXTENSION LOAD-MORE ENGINE (AJAX)
    // ========================================================
    const sentinel = document.getElementById("scroll-sentinel");
    const productsGrid = document.getElementById("infinite-products-grid");
    const loadMoreBtn = document.getElementById("load-more-btn");
    const loader = document.getElementById("infinite-loader");

    if (sentinel && productsGrid && loadMoreBtn) {
        let isLoading = false;

        loadMoreBtn.addEventListener("click", function() {
            let nextPage = sentinel.getAttribute("data-next-page");
            
            if (nextPage !== "none" && !isLoading) {
                isLoading = true;
                loadMoreBtn.classList.add("d-none");
                if (loader) loader.classList.remove("d-none");

                const currentQueryParams = new URLSearchParams(window.location.search);
                currentQueryParams.set("page", nextPage);

                const targetFetchUrl = `?${currentQueryParams.toString()}`;

                fetch(targetFetchUrl, {
                    headers: { "X-Requested-With": "XMLHttpRequest" }
                })
                .then(response => response.json()) 
                .then(data => {
                    if (data.html && data.html.trim().length > 0) {
                        productsGrid.insertAdjacentHTML("beforeend", data.html);
                        if (data.has_next) {
                            let calculatedNextPage = parseInt(nextPage) + 1;
                            sentinel.setAttribute("data-next-page", calculatedNextPage);
                            loadMoreBtn.classList.remove("d-none");
                        } else {
                            sentinel.setAttribute("data-next-page", "none");
                            loadMoreBtn.classList.add("d-none");
                        }
                    } else {
                        sentinel.setAttribute("data-next-page", "none");
                        loadMoreBtn.classList.add("d-none"); 
                    }
                    isLoading = false;
                    if (loader) loader.classList.add("d-none");
                })
                .catch(err => {
                    console.error("Collection streaming allocation failure:", err);
                    isLoading = false;
                    loadMoreBtn.classList.remove("d-none");
                    if (loader) loader.classList.add("d-none");
                });
            }
        });
    }   

    // ========================================================
    // 🟢 UPDATED BLOCK 7: INSTANT CATEGORY FILTER SWAPPER (ROUTING-AWARE)
    // ========================================================
    document.querySelectorAll(".global-category-nav, .royal-tab-link").forEach(tab => {
        tab.addEventListener("click", function(e) {
            e.preventDefault();
            
            const category = this.getAttribute("data-category");
            const newUrlParams = new URLSearchParams();
            if (category && category !== "all") {
                newUrlParams.set("category", category);
            }

            const queryString = newUrlParams.toString() ? "?" + newUrlParams.toString() : "";
            
            // If not on home catalog page, force a clean redirect
            if (window.location.pathname !== "/") {
                window.location.href = "/" + queryString;
                return; 
            }

            // ── 🟢 FIXED: Clear active classes across ALL navbar and filter elements ──
            document.querySelectorAll(".global-category-nav, .royal-tab-link").forEach(t => {
                t.classList.remove("active", "text-warning");
            });

            // Highlight the currently clicked item
            this.classList.add("active");
            if (this.classList.contains("global-category-nav")) {
                this.classList.add("text-warning");
            }

            const targetUrl = "/" + queryString;
            window.history.pushState({ path: targetUrl }, "", targetUrl);

            if (loader) loader.classList.remove("d-none");
            if (loadMoreBtn) loadMoreBtn.classList.add("d-none");

            fetch(targetUrl, {
                headers: { "X-Requested-With": "XMLHttpRequest" }
            })
            .then(response => response.json()) 
            .then(data => {
                if (productsGrid) {
                    productsGrid.innerHTML = data.html;
                }
                if (sentinel) {
                    if (data.has_next) {
                        sentinel.setAttribute("data-next-page", "2"); 
                        if (loadMoreBtn) loadMoreBtn.classList.remove("d-none");
                    } else {
                        sentinel.setAttribute("data-next-page", "none");
                        if (loadMoreBtn) loadMoreBtn.classList.add("d-none");
                    }
                }

                const clearFiltersWrapper = document.getElementById("clear-filters-wrapper");
                if (clearFiltersWrapper) {
                    if (category === "all") {
                        clearFiltersWrapper.classList.add("d-none"); 
                    } else {
                        clearFiltersWrapper.classList.remove("d-none"); 
                    }
                }
                if (loader) loader.classList.add("d-none");
            })
            .catch(err => {
                console.error("Live category filtration failed:", err);
                if (loader) loader.classList.add("d-none");
            });
        });
    });

    // ========================================================
    // BLOCK 8: LUXURY SCROLL-TO-TOP FLOATING BUTTON
    // ========================================================
    const backToTopBtn = document.getElementById("back-to-top-btn");

    if (backToTopBtn) {
        window.addEventListener("scroll", function() {
            if (window.scrollY > 300) {
                backToTopBtn.classList.remove("d-none");
                backToTopBtn.style.opacity = "1";
            } else {
                backToTopBtn.style.opacity = "0";
                setTimeout(() => {
                    if (window.scrollY <= 300) backToTopBtn.classList.add("d-none");
                }, 300);
            }
        });

        backToTopBtn.addEventListener("click", function() {
            window.scrollTo({ top: 0, behavior: "smooth" });
        });
    }

    // ========================================================
    // BLOCK 9: SHOPPING VAULT PAGE TABLE ROW REMOVER (AJAX)
    // ========================================================
    document.addEventListener("submit", function(e) {
        const cartRemoveForm = e.target.closest(".ajax-cart-remove-form");
        if (!cartRemoveForm) return;

        e.preventDefault(); 
        e.stopImmediatePropagation();

        const dataPayload = new FormData(cartRemoveForm);
        const tableRow = cartRemoveForm.closest("tr");
        const targetRemovalUrl = cartRemoveForm.getAttribute("action") || "/product/remove-item/";

        fetch(targetRemovalUrl, { 
            method: "POST",
            body: dataPayload,
            headers: { "X-Requested-With": "XMLHttpRequest" }
        })
        .then(response => {
            if (!response.ok) throw new Error("Vault subtraction transaction rejected.");
            return response.json();
        })
        .then(data => {
            if (data.status === "success" && data.action === "removed") {
                const cartCounter = document.getElementById("cart-counter");
                if (cartCounter) {
                    cartCounter.innerText = data.cart_count;
                    if (data.cart_count === 0) {
                        cartCounter.classList.add("d-none");
                    }
                }

                tableRow.style.transition = "all 0.35s ease";
                tableRow.style.opacity = "0";
                tableRow.style.transform = "translateX(-20px)";
                
                setTimeout(() => {
                    tableRow.remove();
                    if (document.querySelectorAll("tbody tr").length === 0) {
                        window.location.reload();
                    }
                }, 350);
            }
        })
        .catch(err => console.error("Vault item live suppression network failure:", err));
    });

    // ========================================================
    // BLOCK 10: SHOPPING CART QUANTITY ADJUSTER (AJAX)
    // ========================================================
    document.addEventListener("submit", function(e) {
        const qtyForm = e.target.closest(".ajax-cart-qty-form");
        if (!qtyForm) return;

        e.preventDefault(); 
        e.stopImmediatePropagation();

        const dataPayload = new FormData(qtyForm);
        const targetUrl = qtyForm.getAttribute("action") || "/product/add-to-cart/";

        fetch(targetUrl, {
            method: "POST",
            body: dataPayload,
            headers: { "X-Requested-With": "XMLHttpRequest" }
        })
        .then(response => {
            if (!response.ok) throw new Error("Quantity recalculation rejected.");
            return response.json();
        })
        .then(data => {
            if (data.status === "success") {
                const cartCounter = document.getElementById("cart-counter");
                if (cartCounter) {
                    cartCounter.innerText = data.cart_count;
                    if (data.cart_count === 0) cartCounter.classList.add("d-none");
                }
                window.location.reload();
            }
        })
        .catch(err => console.error("Quantity modifier execution failed:", err));
    });

}); // 🔒 Safe pipeline closure