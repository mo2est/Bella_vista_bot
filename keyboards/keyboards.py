from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from menu_data import MENU


def main_menu_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="🍕 Меню", callback_data="menu")
    builder.button(text="📍 Адрес и часы", callback_data="address")
    builder.button(text="📞 Контакты", callback_data="contacts")
    builder.button(text="🛒 Сделать заказ", callback_data="order")
    builder.adjust(2, 2)
    return builder.as_markup()


def menu_categories_kb():
    builder = InlineKeyboardBuilder()
    for key, category in MENU.items():
        builder.button(text=category["title"], callback_data=f"category:{key}")
    builder.button(text="⬅️ Назад", callback_data="back_to_main")
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def back_kb(callback_data: str = "back_to_main"):
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад", callback_data=callback_data)
    return builder.as_markup()


def cancel_order_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="back_to_main")
    return builder.as_markup()


def contact_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="📱 Отправить номер телефона", request_contact=True)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
