from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from cart import cart_count, get_cart
from keyboards.keyboards import back_kb, category_kb, main_menu_kb, menu_categories_kb
from menu_data import MENU

router = Router()

WELCOME_TEXT = (
    "🇮🇹 <b>Добро пожаловать в Bella Vista!</b>\n\n"
    "Bella Vista — это уютное итальянское кафе в самом сердце города. "
    "Мы готовим настоящую пасту, хрустящую пиццу на дровах и десерты "
    "по традиционным рецептам Италии.\n\n"
    "Выберите, что вас интересует 👇"
)

ADDRESS_TEXT = (
    "📍 <b>Адрес и часы работы</b>\n\n"
    "Адрес: г. Москва, ул. Примерная, д. 10\n"
    "Часы работы: ежедневно с 09:00 до 23:00\n"
)

CONTACTS_TEXT = (
    "📞 <b>Контакты</b>\n\n"
    "Телефон: +7 (999) 123-45-67\n"
    "Instagram: @bellavista_cafe\n"
    "Email: info@bellavista.ru\n"
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb())


@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    # Leave any checkout state but keep FSM data (the cart).
    await state.set_state(None)
    await callback.message.edit_text(WELCOME_TEXT, reply_markup=main_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "address")
async def show_address(callback: CallbackQuery):
    await callback.message.edit_text(ADDRESS_TEXT, reply_markup=back_kb())
    await callback.answer()


@router.callback_query(F.data == "contacts")
async def show_contacts(callback: CallbackQuery):
    await callback.message.edit_text(CONTACTS_TEXT, reply_markup=back_kb())
    await callback.answer()


@router.callback_query(F.data == "menu")
async def show_menu(callback: CallbackQuery, state: FSMContext):
    cart = await get_cart(state)
    await callback.message.edit_text(
        "🍽 <b>Меню Bella Vista</b>\n\nВыберите категорию:",
        reply_markup=menu_categories_kb(cart_count(cart)),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("category:"))
async def show_category(callback: CallbackQuery, state: FSMContext):
    key = callback.data.split(":", 1)[1]
    category = MENU.get(key)
    if not category:
        await callback.answer("Категория не найдена", show_alert=True)
        return

    text = f"<b>{category['title']}</b>\n\n"
    for name, price in category["items"]:
        text += f"• {name} — {price}\n"
    text += "\nНажмите ➕, чтобы добавить блюдо в корзину:"

    cart = await get_cart(state)
    await callback.message.edit_text(text, reply_markup=category_kb(key, cart_count(cart)))
    await callback.answer()
