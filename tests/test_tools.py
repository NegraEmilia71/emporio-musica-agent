"""Offline tests for the agent's tools (no LLM calls)."""

import pytest
from src.tools import catalog, orders, policies


# ── Catalog ──────────────────────────────────────────────────────────────────
def test_search_products_by_query():
    results = catalog.search_products(query="violão", max_price=1000, limit=10)
    assert len(results) > 0
    assert all(r["price_brl"] <= 1000 for r in results)


def test_search_products_by_category():
    results = catalog.search_products(category="Ukuleles", limit=5)
    assert len(results) > 0
    assert all("Ukulele" in r["name"] or "ukulele" in r["description"].lower()
               for r in results)


def test_get_product_by_name():
    p = catalog.get_product_by_name("Takamine GD20")
    assert p is not None
    assert p["price_brl"] == 2199.0


def test_get_product_by_id():
    p = catalog.get_product_by_id(95)
    assert p is not None
    assert "Takamine" in p["name"]


def test_active_promotion_attached():
    # Product 127 has an active promotion (id 12, 10%)
    results = catalog.search_products(query="Kalani KAL-700T")
    assert results
    assert "promotion" in results[0]
    assert results[0]["promotion"]["discount_percent"] == 10.0


# ── Orders ───────────────────────────────────────────────────────────────────
def test_get_order_full():
    o = orders.get_order(3)
    assert o is not None
    assert o["status"] == "delivered"
    assert o["customer_name"]
    assert len(o["items"]) > 0


def test_get_order_not_found():
    assert orders.get_order(9999) is None


def test_get_orders_by_customer():
    lst = orders.get_orders_by_customer(3)
    assert isinstance(lst, list)
    assert len(lst) >= 1


def test_find_customer_by_email():
    c = orders.find_customer_by_email("lucas.mendes@jmail.com")
    assert c is not None
    assert c["customer_id"] == 1


# ── Policies (RAG) ───────────────────────────────────────────────────────────
def test_policies_returns_refund():
    results = policies.search_policies("posso devolver compra online?", top_k=3)
    assert len(results) > 0
    joined = " ".join(r["chunk"].lower() for r in results)
    assert "devolu" in joined or "arrependimento" in joined


def test_policies_returns_hours():
    results = policies.search_policies("qual o horário de funcionamento?", top_k=3)
    assert len(results) > 0
    joined = " ".join(r["chunk"] for r in results)
    assert "09:00" in joined or "18:00" in joined or "Sábado" in joined


def test_policies_returns_payment():
    results = policies.search_policies("aceita pix?", top_k=3)
    assert len(results) > 0
    joined = " ".join(r["chunk"].lower() for r in results)
    assert "pix" in joined
    