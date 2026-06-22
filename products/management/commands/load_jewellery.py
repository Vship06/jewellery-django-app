import os
import pandas as pd
from django.core.management.base import BaseCommand
from products.models import Product, ProductVariant


class Command(BaseCommand):
    help = (
        "Batch ingest jewelry files while automatically fixing blank variant row gaps."
    )

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

        success_products = 0
        success_variants = 0

        for file_path in excel_files:
            self.stdout.write(
                self.style.MIGRATE_LABEL(
                    f"\nProcessing file: {os.path.basename(file_path)}"
                )
            )
            try:
                df = pd.read_excel(file_path)
                df.columns = [str(col).strip() for col in df.columns]

                # 🌟 SMART AUTO-FILL: If these columns are blank on variant rows,
                # pandas will automatically copy the value down from the parent row above it!
                columns_to_fill = [
                    "name",
                    "sku",
                    "product_type",
                    "collection",
                    "image_link",
                    "purity",
                    "metal_color",
                ]
                for col in columns_to_fill:
                    if col in df.columns:
                        # Replace true empty spaces/NaNs with actual nulls, forward fill them, then clear remaining NaNs
                        df[col] = df[col].replace(r"^\s*$", None, regex=True)
                        df[col] = df[col].ffill().fillna("")

                df = df.fillna("")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error reading file: {str(e)}"))
                continue

            for index, row in df.iterrows():
                product_name = str(row.get("name", "")).strip()
                parent_sku = str(row.get("sku", "")).strip()
                category_name = str(row.get("product_type", "Luxury Jewelry")).strip()
                description_text = str(
                    row.get("collection", "An exquisite artisan selection.")
                ).strip()
                images_payload = str(row.get("image_link", "")).strip()

                if not product_name or not parent_sku:
                    continue

                # Step 1: Create or Fetch Parent Product
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

                # Step 2: Handle Variant Record
                variant_sku_id = str(row.get("variant_sku", "")).strip()
                if not variant_sku_id:
                    variant_sku_id = f"{parent_sku}-VAR-{index}"

                # 🌟 Because of .ffill() above, purity and metal_color are now safely populated!
                purity = str(row.get("purity", "18K")).strip()
                metal_color = str(row.get("metal_color", "Gold")).strip()
                constructed_metal = f"{purity} {metal_color}".replace("  ", " ").strip()

                try:
                    raw_price = row.get("total_price", 0)
                    price_value = float(raw_price) if raw_price != "" else 0.0
                except ValueError:
                    price_value = 0.0

                variant_defaults = {
                    "metal_type": constructed_metal,
                    "gross_weight": str(row.get("gross_weight", "")).strip(),
                    "size_or_length": str(row.get("size", "")).strip(),
                    "price": price_value,
                    "diamond_pcs": str(row.get("diamond_pcs", "")).strip(),
                    "carat_weight": str(row.get("diamond_carat", "")).strip(),
                    "diamond_clarity": str(row.get("diamond_clarity", "")).strip(),
                    "diamond_color": str(row.get("diamond_color", "")).strip(),
                    "stock_count": (
                        5
                        if str(row.get("is_in_stock", "true")).strip().lower()
                        in ["true", "1", "yes"]
                        else 0
                    ),
                }

                # Step 3: Link variant down to database tables safely
                ProductVariant.objects.update_or_create(
                    product=product,
                    variant_sku=variant_sku_id,
                    defaults=variant_defaults,
                )
                success_variants += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\n🎉 Clean batch execution finished successfully!\n"
                f"📦 Verified/Created Parent Products: {success_products}\n"
                f"💎 Processed & Standardized Variants: {success_variants}"
            )
        )
