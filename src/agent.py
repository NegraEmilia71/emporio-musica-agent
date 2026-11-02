"""The agent: orchestrates LLM + tools using OpenAI-compatible function calling."""

import json
from openai import OpenAI
from src.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_CHAT
from src.prompts import build_system_prompt
from src.tools import catalog, orders, policies


# ── Tool schemas (sent to the LLM) ─────────────────────────────────────────────
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": "Search products in the catalog by name/description, category, and price range. Returns up to N products with price, stock and any active promotion.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Free-text keywords (e.g. 'violão', 'Takamine', 'eletroacústico')"},
                    "category": {"type": "string", "description": "Category name (e.g. 'Violões', 'Ukuleles', 'Guitarras')"},
                    "max_price": {"type": "number", "description": "Maximum price in BRL"},
                    "min_price": {"type": "number", "description": "Minimum price in BRL"},
                    "limit": {"type": "integer", "description": "Max results (default 5)"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_by_name",
            "description": "Get a single product by (partial) name. Use for specific product questions.",
            "parameters": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_order",
            "description": "Fetch full order details (status, tracking, items, customer) by order_id.",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "integer"}},
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_orders_by_customer",
            "description": "List all orders for a customer_id (summaries only).",
            "parameters": {
                "type": "object",
                "properties": {"customer_id": {"type": "integer"}},
                "required": ["customer_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_customer_by_email",
            "description": "Look up a customer by email (to obtain customer_id).",
            "parameters": {
                "type": "object",
                "properties": {"email": {"type": "string"}},
                "required": ["email"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_policies",
            "description": "Search the store's internal manual for policy excerpts. Use for questions about opening hours, payment methods, returns/exchanges, shipping, warranty, privacy, promotions rules, store address, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "integer", "description": "How many excerpts (default 3)"},
                },
                "required": ["query"],
            },
        },
    },
]


# ── Tool dispatcher ────────────────────────────────────────────────────────────
def _dispatch(name: str, args: dict):
    if name == "search_products":
        return catalog.search_products(**args)
    if name == "get_product_by_name":
        return catalog.get_product_by_name(**args)
    if name == "get_order":
        return orders.get_order(**args)
    if name == "get_orders_by_customer":
        return orders.get_orders_by_customer(**args)
    if name == "find_customer_by_email":
        return orders.find_customer_by_email(**args)
    if name == "search_policies":
        return policies.search_policies(**args)
    raise ValueError(f"Unknown tool: {name}")


class Agent:
    """Conversational agent with tool use and rolling history."""

    def __init__(self, max_tool_rounds: int = 5, language: str = "pt"):  # ← mudou
        self.client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
        )
        self.model = DEEPSEEK_MODEL
        self.max_tool_rounds = max_tool_rounds
        self.language = language
        self.messages: list[dict] = [
            {"role": "system", "content": build_system_prompt(language)}  # ← mudou
        ]

    def reset(self):
        self.messages = [
            {"role": "system", "content": build_system_prompt(self.language)}
        ]

    def send(self, user_message: str) -> str:
        """Send a user message, run the tool loop, return the final answer."""
        self.messages.append({"role": "user", "content": user_message})

        for _ in range(self.max_tool_rounds):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
                temperature=0.3,
            )
            msg = response.choices[0].message
            self.messages.append(msg.model_dump(exclude_none=True))

            if not msg.tool_calls:
                return msg.content or ""

            for call in msg.tool_calls:
                fn_name = call.function.name
                fn_args = json.loads(call.function.arguments or "{}")
                try:
                    result = _dispatch(fn_name, fn_args)
                except Exception as e:
                    result = {"error": str(e)}
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                })

        return "Sorry, I couldn't complete your request right now. Could you rephrase it? 🙏"
    