"""Order tools: lookup by ID, by customer, status, tracking."""

import pandas as pd
from src.config import ORDERS_CSV, ORDER_ITEMS_CSV, CUSTOMERS_CSV, PRODUCTS_CSV


def _load_orders() -> pd.DataFrame:
    if not hasattr(_load_orders, "_cache"):
        _load_orders._cache = pd.read_csv(ORDERS_CSV)
    return _load_orders._cache


def _load_order_items() -> pd.DataFrame:
    if not hasattr(_load_order_items, "_cache"):
        _load_order_items._cache = pd.read_csv(ORDER_ITEMS_CSV)
    return _load_order_items._cache


def _load_customers() -> pd.DataFrame:
    if not hasattr(_load_customers, "_cache"):
        _load_customers._cache = pd.read_csv(CUSTOMERS_CSV)
    return _load_customers._cache


def _load_products() -> pd.DataFrame:
    if not hasattr(_load_products, "_cache"):
        _load_products._cache = pd.read_csv(PRODUCTS_CSV)
    return _load_products._cache


def get_order(order_id: int) -> dict | None:
    """Return full order info + items + customer name."""
    orders = _load_orders()
    row = orders[orders["order_id"] == order_id]
    if row.empty:
        return None
    r = row.iloc[0]

    # Items
    items_df = _load_order_items()
    items_rows = items_df[items_df["order_id"] == order_id]
    products = _load_products()
    items = []
    for _, it in items_rows.iterrows():
        prod = products[products["product_id"] == it["product_id"]]
        name = prod.iloc[0]["name"] if not prod.empty else f"product_{it['product_id']}"
        unit_price = float(prod.iloc[0]["price_brl"]) if not prod.empty else None
        items.append({
            "product_id": int(it["product_id"]),
            "name": name,
            "quantity": int(it["quantity"]),
            "unit_price_brl": unit_price,
        })

    # Customer
    customers = _load_customers()
    cust = customers[customers["customer_id"] == r["customer_id"]]
    customer_name = cust.iloc[0]["name"] if not cust.empty else None

    return {
        "order_id": int(r["order_id"]),
        "customer_id": int(r["customer_id"]),
        "customer_name": customer_name,
        "order_date": str(r["order_date"]),
        "status": r["status"],
        "total_brl": float(r["total_brl"]),
        "payment_method": r["payment_method"],
        "tracking_code": None if pd.isna(r["tracking_code"]) else r["tracking_code"],
        "estimated_delivery": None if pd.isna(r["estimated_delivery"]) else str(r["estimated_delivery"]),
        "notes": None if pd.isna(r["notes"]) else r["notes"],
        "items": items,
    }


def get_orders_by_customer(customer_id: int) -> list[dict]:
    """Return summary of all orders for a given customer."""
    orders = _load_orders()
    rows = orders[orders["customer_id"] == customer_id]
    result = []
    for _, r in rows.iterrows():
        result.append({
            "order_id": int(r["order_id"]),
            "order_date": str(r["order_date"]),
            "status": r["status"],
            "total_brl": float(r["total_brl"]),
            "tracking_code": None if pd.isna(r["tracking_code"]) else r["tracking_code"],
        })
    return result


def find_customer_by_email(email: str) -> dict | None:
    """Lookup customer by email (used for identifying the user)."""
    customers = _load_customers()
    row = customers[customers["email"].str.lower() == email.lower()]
    if row.empty:
        return None
    r = row.iloc[0]
    return {
        "customer_id": int(r["customer_id"]),
        "name": r["name"],
        "email": r["email"],
        "city": r["city"],
    }
    