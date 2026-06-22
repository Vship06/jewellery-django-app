// static/js/wishlist.js

document.addEventListener("DOMContentLoaded", function () {
    
    // ========================================================
    // BLOCK 1: GLOBAL CATALOG GRID HEART TOGGLES (AJAX DELEGATION)
    // ========================================================
    document.addEventListener("submit", function(e) {
        const activeForm = e.target.closest(".wishlist-toggle-form");
        if (!activeForm) return;

        e.preventDefault(); 

        const dataPayload = new FormData(activeForm);
        const targetHeartIcon = activeForm.querySelector(".wishlist-heart-btn i");

        fetch("/product/add-to-wishlist/", { 
            method: "POST",
            body: dataPayload,
            headers: { "X-Requested-With": "XMLHttpRequest" }
        })
        .then(response => {
            if (!response.ok) throw new Error("Wishlist pipeline response error.");
            return response.json();
        })
        .then(data => {
            if (data.status === "success") {
                if (data.action === "added") {
                    targetHeartIcon.className = "bi bi-heart-fill";
                    targetHeartIcon.style.setProperty("color", "#800020", "important");
                } else {
                    targetHeartIcon.className = "bi bi-heart text-muted";
                    targetHeartIcon.style.color = "";
                }

                // 🌟 LIVE UPDATE: Sync Navbar Wishlist Badge Counter
                const wishlistCounter = document.getElementById("wishlist-counter");
                if (wishlistCounter) {
                    wishlistCounter.innerText = data.wishlist_count;
                    if (data.wishlist_count > 0) {
                        wishlistCounter.classList.remove("d-none");
                    } else {
                        wishlistCounter.classList.add("d-none");
                    }
                }
            }
        })
        .catch(err => console.error("Grid heart submission failed:", err));
    });

    // ========================================================
    // BLOCK 2: PRODUCT DETAIL SHOWROOM INTERCEPTOR (AJAX)
    // ========================================================
    const detailWishlistBtn = document.getElementById("detail-wishlist-toggle-btn");
    
    if (detailWishlistBtn) {
        detailWishlistBtn.addEventListener("click", function() {
            const activeVariantSelector = document.getElementById("variant-selector");
            const csrfTokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
            
            if (!activeVariantSelector || !csrfTokenElement) {
                console.error("Required detail showroom elements are missing from the DOM.");
                return;
            }

            const currentSelectedVariantId = activeVariantSelector.value;
            const dataPayload = new FormData();
            dataPayload.append("variant_id", currentSelectedVariantId);
            dataPayload.append("csrfmiddlewaretoken", csrfTokenElement.value);

            fetch("/product/add-to-wishlist/", {
                method: "POST",
                body: dataPayload
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === "success") {
                    const detailHeart = document.getElementById("detail-heart-icon");
                    const detailText = document.getElementById("detail-wishlist-text");

                    if (data.action === "added") {
                        detailHeart.className = "bi bi-heart-fill me-2";
                        detailHeart.style.setProperty("color", "#800020", "important");
                        detailText.innerText = "In Your Wishlist";
                    } else {
                        detailHeart.className = "bi bi-heart me-2";
                        detailHeart.style.color = "";
                        detailText.innerText = "Add To Wishlist Vault";
                    }

                    // 🌟 LIVE UPDATE: Sync Navbar Wishlist Badge Counter from Detail Page
                    const wishlistCounter = document.getElementById("wishlist-counter");
                    if (wishlistCounter) {
                        wishlistCounter.innerText = data.wishlist_count;
                        if (data.wishlist_count > 0) {
                            wishlistCounter.classList.remove("d-none");
                        } else {
                            wishlistCounter.classList.add("d-none");
                        }
                    }
                }
            })
            .catch(err => console.error("Detail page view synchronization failed:", err));
        });
    }

    // ========================================================
    // BLOCK 3: WISHLIST PAGE CARD FADER REMOVER (AJAX)
    // ========================================================
    document.addEventListener("submit", function(e) {
        const removeForm = e.target.closest(".ajax-wishlist-remove-form");
        if (!removeForm) return;

        e.preventDefault(); 

        const dataPayload = new FormData(removeForm);
        const itemCard = removeForm.closest(".wishlist-item-card");

        fetch("/product/add-to-wishlist/", { 
            method: "POST",
            body: dataPayload
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === "success" && data.action === "removed") {
                
                const wishlistCounter = document.getElementById("wishlist-counter");
                if (wishlistCounter) {
                    wishlistCounter.innerText = data.wishlist_count;
                    if (data.wishlist_count === 0) {
                        wishlistCounter.classList.add("d-none");
                    }
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
        .catch(err => console.error("Wishlist live removal failed:", err));
    });

    // ========================================================
    // BLOCK 4: WISHLIST PAGE ASYNCHRONOUS CART INJECTOR (AJAX)
    // ========================================================
    document.addEventListener("submit", function(e) {
        const cartForm = e.target.closest(".ajax-wishlist-add-to-cart-form");
        if (!cartForm) return;

        e.preventDefault(); 

        const dataPayload = new FormData(cartForm);

        fetch("/product/add-to-cart/", {
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
                }

                // 🌟 VERIFIED: Core wrapper matches matching layout elements
                const toast = document.getElementById("toast");
                const toastMsg = document.getElementById("toast-message");

                if (toast && toastMsg) {
                    toastMsg.innerText = "Added to your shopping vault.";
                    toast.classList.add("show");

                    setTimeout(() => {
                        toast.classList.remove("show");
                    }, 3500);
                }
            }
        })
        .catch(err => console.error("Wishlist-to-cart transition failed:", err));
    });
    
    // ========================================================
    // BLOCK 5: MANUAL EXTENSION LOAD-MORE ENGINE (AJAX)
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
    // BLOCK 6: INSTANT CATEGORY FILTER SWAPPER (AJAX)
    // ========================================================
    document.querySelectorAll(".royal-tab-link").forEach(tab => {
        tab.addEventListener("click", function(e) {
            e.preventDefault();
            
            document.querySelectorAll(".royal-tab-link").forEach(t => t.classList.remove("active"));
            
            if (this.classList.contains("clear-filters-btn")) {
                const allTab = document.querySelector('.royal-tab-link[data-category="all"]');
                if (allTab) allTab.classList.add("active");
            } else {
                this.classList.add("active");
            }

            const category = this.getAttribute("data-category");
            const newUrlParams = new URLSearchParams();
            
            if (category !== "all") {
                newUrlParams.set("category", category);
            }

            const targetUrl = window.location.pathname + (newUrlParams.toString() ? "?" + newUrlParams.toString() : "");
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
    // BLOCK 7: LUXURY SCROLL-TO-TOP FLOATING BUTTON
    // ========================================================
    // 🚀 INCLUDED: Safely encapsulated within DOMContentLoaded scope rules
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
            window.scrollTo({
                top: 0,
                behavior: "smooth"
            });
        });
    }

}); // 🌟 END OF SCRIPTS SCOPE