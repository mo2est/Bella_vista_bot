"""Cart helpers. The cart lives in FSM storage as {"cart": {"<category>:<index>": qty}}."""

import re

from aiogram.fsm.context import FSMContext

from menu_data import MENU


def parse_price(price: str) -> int:
    digits = re.sub(r"\D", "", price)
    return int(digits) if digits else 0


def get_item(item_key: str) -> tuple[str, str]:
    category_key, index = item_key.split(":", 1)
    return MENU[category_key]["items"][int(index)]


async def get_cart(state: FSMContext) -> dict:
    data = await state.get_data()
    return data.get("cart", {})


def cart_count(cart: dict) -> int:
    return sum(cart.values())


def cart_summary(cart: dict) -> tuple[str, int]:
    lines = []
    total = 0
    for item_key, qty in cart.items():
        name, price = get_item(item_key)
        cost = parse_price(price) * qty
        total += cost
        lines.append(f"• {name} × {qty} — {cost} руб.")
    return "\n".join(lines), total
