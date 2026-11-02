"""Configuration loader. Loads environment variables and exposes paths/constants."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))

# CSV paths
PRODUCTS_CSV = DATA_DIR / "desafio_tecnico_ai_eng - products.csv"
CATEGORIES_CSV = DATA_DIR / "desafio_tecnico_ai_eng - categories.csv"
CUSTOMERS_CSV = DATA_DIR / "desafio_tecnico_ai_eng - customers.csv"
ORDERS_CSV = DATA_DIR / "desafio_tecnico_ai_eng - orders.csv"
ORDER_ITEMS_CSV = DATA_DIR / "desafio_tecnico_ai_eng - order_items.csv"
PROMOTIONS_CSV = DATA_DIR / "desafio_tecnico_ai_eng - promotions.csv"

# Policies PDF
POLICIES_PDF = DATA_DIR / "políticas_da_loja.pdf"

# LLM
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-flash")