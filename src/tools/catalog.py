"""Catalog tools: product search, price lookup, stock and promotions."""

import json
import pandas as pd
from src.config import PRODUCTS_CSV, CATEGORIES_CSV, PROMOTIONS_CSV


def _load_products() -> pd.DataFrame:
    """Load and cache products DataFrame."""
    if not hasattr(_load_products, "_cache"):
        df = pd.read_csv(PRODUCTS_CSV)
        # Parse specs JSON column if it exists
        if "specs" in df.columns:
            df["specs"] = df["specs"].apply(
                lambda x: json.loads(x) if isinstance(x, str) and x.strip() else {}
            )
        _load_products._cache = df
    return _load_products._cache


def _load_categories() -> pd.DataFrame:
    if not hasattr(_load_categories, "_cache"):
        _load_categories._cache = pd.read_csv(CATEGORIES_CSV)
    return _load_categories._cache


def _load_promotions() -> pd.DataFrame:
    if not hasattr(_load_promotions, "_cache"):
        _load_promotions._cache = pd.read_csv(PROMOTIONS_CSV)
    return _load_promotions._cache


def search_products(
    query: str = "",
    category: str = "",
    max_price: float | None = None,
    min_price: float | None = None,
    only_active: bool = True,
    limit: int = 5,
) -> list[dict]:
    """
    Search products by name/description, category, and price range.
    Returns a list of dicts with product info + active promotion if any.
    """
    df = _load_products().copy()

    if only_active:
        df = df[df["status"] == "active"]

    if query:
        mask = (
            df["name"].str.contains(query, case=False, na=False)
            | df["description"].str.contains(query, case=False, na=False)
        )
        df = df[mask]

    if category:
        cats = _load_categories()
        cat_row = cats[cats["name"].str.contains(category, case=False, na=False)]
        if not cat_row.empty:
            df = df[df["category_id"] == cat_row.iloc[0]["category_id"]]

    if max_price is not None:
        df = df[df["price_brl"] <= max_price]
    if min_price is not None:
        df = df[df["price_brl"] >= min_price]

    # Attach active promotions
    promos = _load_promotions()
    active_promos = promos[promos["is_active"] == 1]
    promo_map = dict(zip(active_promos["product_id"], active_promos["discount_percent"]))

    results = []
    for _, row in df.head(limit).iterrows():
        pid = int(row["product_id"])
        item = {
            "product_id": pid,
            "name": row["name"],
            "price_brl": float(row["price_brl"]),
            "stock_quantity": int(row["stock_quantity"]),
            "status": row["status"],
            "description": row["description"],
            "specs": row.get("specs", {}),
        }
        if pid in promo_map:
            discount = float(promo_map[pid])
            item["promotion"] = {
                "discount_percent": discount,
                "final_price_brl": round(float(row["price_brl"]) * (1 - discount / 100), 2),
            }
        results.append(item)
    return results


def get_product_by_name(name: str) -> dict | None:
    """Exact-ish lookup by product name (case-insensitive contains)."""
    results = search_products(query=name, only_active=False, limit=1)
    return results[0] if results else None


def get_product_by_id(product_id: int) -> dict | None:
    df = _load_products()
    row = df[df["product_id"] == product_id]
    if row.empty:
        return None
    r = row.iloc[0]
    return {
        "product_id": int(r["product_id"]),
        "name": r["name"],
        "price_brl": float(r["price_brl"]),
        "stock_quantity": int(r["stock_quantity"]),
        "status": r["status"],
        "description": r["description"],
    }