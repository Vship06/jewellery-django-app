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

        def safe_decimal(val):
            try:
                if pd.isna(val) or str(val).strip() == "":
                    return None
                return float(val)
            except (ValueError, TypeError):
                return None

        def safe_str(val):
            if pd.isna(val):
                return ""
            return str(val).strip()

        for file_path in excel_files:
            self.stdout.write(
                self.style.MIGRATE_LABEL(
                    f"\nProcessing file: {os.path.basename(file_path)}"
                )
            )

            try:
                df = pd.read_excel(file_path)
                df.columns = [str(col).strip() for col in df.columns]

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

                product_name = safe_str(row.get("name"))
                parent_sku = safe_str(row.get("sku"))

                # AFTER
                CATEGORY_MAP = {
                    "FINGER RING": "ring",
                    "RING": "ring",
                    "NOSE PIN": "nosepin",
                    "NOSEPIN": "nosepin",
                    "EARRINGS": "earring",
                    "EARRING": "earring",
                    "BANGLE": "bangle",
                    "BRACELET": "bracelet",
                    "NECKLACE": "necklace",
                    "CHAIN": "chain",
                    "PENDANT": "pendant",
                }
                raw_type = safe_str(row.get("product_type")).strip().upper()
                category_name = CATEGORY_MAP.get(raw_type, "ring")

                description_text = (
                    safe_str(row.get("collection")) or "An exquisite artisan selection."
                )

                # JSONField image handling
                images_raw = safe_str(row.get("image_link"))

                image_links = [
                    url.strip() for url in images_raw.split("|") if url and url.strip()
                ]

                if not product_name or not parent_sku:
                    continue

                product, created = Product.objects.update_or_create(
                    sku=parent_sku,
                    defaults={
                        "name": product_name,
                        "category": category_name,
                        "description": description_text,
                        "image_links": image_links,
                    },
                )

                if created:
                    success_products += 1

                variant_sku_id = safe_str(row.get("variant_sku"))

                if not variant_sku_id:
                    variant_sku_id = f"{parent_sku}-VAR-{index}"

                purity = safe_str(row.get("purity")).upper()
                metal_color = safe_str(row.get("metal_color")).upper()
                base_metal = safe_str(row.get("base_metal")).upper() or "GOLD"

                raw_price = row.get("total_price", 0)
                price_value = safe_decimal(raw_price) or 0.0

                variant_defaults = {
                    "base_metal": base_metal or None,
                    "metal_color": metal_color or None,
                    "purity": purity or None,
                    "diamond_clarity": safe_str(row.get("diamond_clarity")) or None,
                    "diamond_color": safe_str(row.get("diamond_color")) or None,
                    "diamond_cut": safe_str(row.get("diamond_cut")) or None,
                    "diamond_carat": safe_str(row.get("diamond_carat")) or None,
                    "diamond_pcs": safe_str(row.get("diamond_pcs")) or None,
                    "net_weight": safe_decimal(row.get("net_weight")),
                    "gross_weight": safe_decimal(row.get("gross_weight")),
                    "stone_weight": safe_decimal(row.get("stone_weight")),
                    "metal_charges": safe_decimal(row.get("metal_charges")),
                    "making_charges": safe_decimal(row.get("making_charges")),
                    "making_charges_discount": (
                        safe_decimal(row.get("making_charges_discount")) or 0.0
                    ),
                    "diamond_charges": safe_decimal(row.get("diamond_charges")),
                    "diamond_charges_discount": (
                        safe_decimal(row.get("diamond_charges_discount")) or 0.0
                    ),
                    "tax": safe_decimal(row.get("tax")),
                    "price": price_value,
                    "max_price": safe_decimal(row.get("max_price")),
                    "size_or_length": safe_str(row.get("size")) or None,
                    "stock_count": (
                        5
                        if safe_str(row.get("is_in_stock", "true")).lower()
                        in ["true", "1", "yes"]
                        else 0
                    ),
                }

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
