from aiogram.types import InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from cart import get_item
from menu_data import MENU

CANCEL_TEXT = "❌ Отмена"


def main_menu_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="🍕 Меню", callback_data="menu")
    builder.button(text="📍 Адрес и часы", callback_data="address")
    builder.button(text="📞 Контакты", callback_data="contacts")
    builder.button(text="🛒 Сделать заказ", callback_data="order")
    builder.adjust(2, 2)
    return builder.as_markup()


def menu_categories_kb(cart_count: int = 0):
    builder = InlineKeyboardBuilder()
    for key, category in MENU.items():
        builder.button(text=category["title"], callback_data=f"category:{key}")
    if cart_count:
        builder.button(text=f"🛒 Корзина ({cart_count})", callback_data="cart")
    builder.button(text="⬅️ Назад", callback_data="back_to_main")
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()


def category_kb(key: str, cart_count: int = 0):
    builder = InlineKeyboardBuilder()
    items = MENU[key]["items"]
    for index, (name, _price) in enumerate(items):
        builder.button(text=f"➕ {name}", callback_data=f"add:{key}:{index}")
    builder.button(text=f"🛒 Корзина ({cart_count})", callback_data="cart")
    builder.button(text="⬅️ К категориям", callback_data="menu")
    builder.adjust(*([1] * len(items)), 2)
    return builder.as_markup()


def cart_kb(cart: dict):
    builder = InlineKeyboardBuilder()
    for item_key in cart:
        name, _price = get_item(item_key)
        builder.button(text=f"➖ {name}", callback_data=f"remove:{item_key}")
    builder.button(text="✅ Оформить заказ", callback_data="checkout")
    builder.button(text="🗑 Очистить", callback_data="cart_clear")
    builder.button(text="⬅️ В меню", callback_data="menu")
    builder.adjust(*([1] * len(cart)), 1, 2)
    return builder.as_markup()


def empty_cart_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="🍽 Перейти в меню", callback_data="menu")
    builder.button(text="⬅️ Главное меню", callback_data="back_to_main")
    builder.adjust(1)
    return builder.as_markup()


def back_kb(callback_data: str = "back_to_main"):
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад", callback_data=callback_data)
    return builder.as_markup()


def cancel_order_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text=CANCEL_TEXT, callback_data="order_cancel")
    return builder.as_markup()


def contact_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)],
            [KeyboardButton(text=CANCEL_TEXT)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
