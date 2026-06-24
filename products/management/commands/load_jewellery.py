import os
import pandas as pd
from django.core.management.base import BaseCommand
from products.models import Product, ProductVariant


class Command(BaseCommand):
    help = "Wipes existing catalog database and batch ingests jewelry files with uppercase normalization and smart row forward-filling."

    def add_arguments(self, parser):
        parser.add_argument(
            "file_path",
            type=str,
            help="Path to a single Excel file OR a folder containing Excel files.",
        )

    def handle(self, *args, **options):
        target_path = options["file_path"]
        excel_files = []

        # 1. Gather Target Files
        if os.path.isdir(target_path):
            self.stdout.write(self.style.NOTICE(f"Scanning folder '{target_path}'..."))
            for file in os.listdir(target_path):
                if file.endswith(".xlsx") and not file.startswith("~$"):
                    excel_files.append(os.path.join(target_path, file))
        elif os.path.isfile(target_path):
            if target_path.endswith(".xlsx"):
                excel_files.append(target_path)

        if not excel_files:
            self.stdout.write(self.style.WARNING("No valid Excel sheets found."))
            return

        # 🔴 2. FRESH CATALOG WIPE: Clears out all old products/variants
        self.stdout.write(
            self.style.MIGRATE_HEADING(
                "Clearing old catalog items from database for a fresh import..."
            )
        )
        ProductVariant.objects.all().delete()
        Product.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Database wiped cleanly."))

        success_products = 0
        success_variants = 0

        # Helper to convert messy cells or empty spaces safely to decimal floats or None
        def safe_decimal(val):
            try:
                if pd.isna(val) or str(val).strip() == "":
                    return None
                return float(val)
            except (ValueError, TypeError):
                return None

        # 3. Process each Excel spreadsheet
        for file_path in excel_files:
            self.stdout.write(
                self.style.MIGRATE_LABEL(
                    f"\nProcessing file: {os.path.basename(file_path)}"
                )
            )
            try:
                df = pd.read_excel(file_path)
                df.columns = [str(col).strip() for col in df.columns]

                # Pandas forward-fill system to replicate structural grouping headers down variant rows
                columns_to_fill = [
                    "name",
                    "sku",
                    "product_type",
                    "collection",
                    "image_link",
                    "purity",
                    "metal_color",
                    "base_metal",
                ]
                for col in columns_to_fill:
                    if col in df.columns:
                        df[col] = df[col].replace(r"^\s*$", None, regex=True)
                        df[col] = df[col].ffill()

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error reading file: {str(e)}"))
                continue

            for index, row in df.iterrows():
                product_name = (
                    str(row.get("name", "")).strip()
                    if not pd.isna(row.get("name"))
                    else ""
                )
                parent_sku = (
                    str(row.get("sku", "")).strip()
                    if not pd.isna(row.get("sku"))
                    else ""
                )
                category_name = str(row.get("product_type", "Luxury Jewelry")).strip()
                description_text = str(
                    row.get("collection", "An exquisite artisan selection.")
                ).strip()
                images_payload = str(row.get("image_link", "")).strip()

                if not product_name or not parent_sku:
                    continue

                # Step A: Create or Fetch Parent Product
                product, created = Product.objects.update_or_create(
                    sku=parent_sku,
                    defaults={
                        "name": product_name,
                        "category": category_name,
                        "description": description_text,
                        "image_link": images_payload,
                    },
                )
                if created:
                    success_products += 1

                # Step B: Standardize Variant SKU identification
                variant_sku_id = (
                    str(row.get("variant_sku", "")).strip()
                    if not pd.isna(row.get("variant_sku"))
                    else ""
                )
                if not variant_sku_id:
                    variant_sku_id = f"{parent_sku}-VAR-{index}"

                # 🟢 STEP C: FORCE UPPERCASE TO ELIMINATE DUPLICATE FILTER ENTRIES (18k vs 18K)
                purity = (
                    str(row.get("purity", "")).strip().upper()
                    if not pd.isna(row.get("purity"))
                    else ""
                )
                metal_color = (
                    str(row.get("metal_color", "")).strip().upper()
                    if not pd.isna(row.get("metal_color"))
                    else ""
                )
                base_metal = (
                    str(row.get("base_metal", "GOLD")).strip().upper()
                    if not pd.isna(row.get("base_metal"))
                    else ""
                )

                # Extract calculated retail values
                raw_price = row.get("total_price", 0)
                price_value = safe_decimal(raw_price) or 0.0

                # Step D: Formulate attributes matching your finalized schema properties
                variant_defaults = {
                    # Metal properties (Uppercase cleaned strings)
                    "base_metal": base_metal or None,
                    "metal_color": metal_color or None,
                    "purity": purity or None,
                    # Diamond configurations
                    "diamond_clarity": (
                        str(row.get("diamond_clarity", "")).strip()
                        if not pd.isna(row.get("diamond_clarity"))
                        else None
                    ),
                    "diamond_color": (
                        str(row.get("diamond_color", "")).strip()
                        if not pd.isna(row.get("diamond_color"))
                        else None
                    ),
                    "diamond_cut": (
                        str(row.get("diamond_cut", "")).strip()
                        if not pd.isna(row.get("diamond_cut"))
                        else None
                    ),
                    "diamond_carat": (
                        str(row.get("diamond_carat", "")).strip()
                        if not pd.isna(row.get("diamond_carat"))
                        else None
                    ),
                    "diamond_pcs": (
                        str(row.get("diamond_pcs", "")).strip()
                        if not pd.isna(row.get("diamond_pcs"))
                        else None
                    ),
                    # Precise physical weights
                    "net_weight": safe_decimal(row.get("net_weight")),
                    "gross_weight": safe_decimal(row.get("gross_weight")),
                    "stone_weight": safe_decimal(row.get("stone_weight")),
                    # Operational/Financial breakdowns
                    "metal_charges": safe_decimal(row.get("metal_charges")),
                    "making_charges": safe_decimal(row.get("making_charges")),
                    "making_charges_discount": safe_decimal(
                        row.get("making_charges_discount")
                    )
                    or 0.0,
                    "diamond_charges": safe_decimal(row.get("diamond_charges")),
                    "diamond_charges_discount": safe_decimal(
                        row.get("diamond_charges_discount")
                    )
                    or 0.0,
                    "tax": safe_decimal(row.get("tax")),
                    # Store values
                    "price": price_value,
                    "max_price": safe_decimal(row.get("max_price")),
                    "size_or_length": (
                        str(row.get("size", "")).strip()
                        if not pd.isna(row.get("size"))
                        else None
                    ),
                    "stock_count": (
                        5
                        if str(row.get("is_in_stock", "true")).strip().lower()
                        in ["true", "1", "yes"]
                        else 0
                    ),
                }

                # Step E: Secure variant row into database tables
                ProductVariant.objects.update_or_create(
                    product=product,
                    variant_sku=variant_sku_id,
                    defaults=variant_defaults,
                )
                success_variants += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\n🎉 Fresh batch execution finished successfully!\n"
                f"📦 Verified/Created Parent Products: {success_products}\n"
                f"💎 Processed & Standardized Variants: {success_variants}"
            )
        )
