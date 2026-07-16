import html
import logging
import re

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from cart import cart_count, cart_summary, get_cart, get_item
from config import ADMIN_CHAT_ID
from keyboards.keyboards import (
    CANCEL_TEXT,
    cancel_order_kb,
    cart_kb,
    category_kb,
    contact_kb,
    empty_cart_kb,
    main_menu_kb,
    menu_categories_kb,
)

router = Router()

logger = logging.getLogger(__name__)

# Every order is also written to orders.log so it cannot be lost
# even if the admin notification fails.
order_logger = logging.getLogger("orders")
if not order_logger.handlers:
    _handler = logging.FileHandler("orders.log", encoding="utf-8")
    _handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
    order_logger.addHandler(_handler)
    order_logger.setLevel(logging.INFO)
    order_logger.propagate = False


class OrderStates(StatesGroup):
    waiting_name = State()
    waiting_phone = State()


CHECKOUT_STATES = (OrderStates.waiting_name.state, OrderStates.waiting_phone.state)


async def remove_prompt_kb(bot, chat_id: int, state: FSMContext):
    """Strip the inline Cancel keyboard from the last checkout prompt, if any."""
    data = await state.get_data()
    prompt_id = data.get("prompt_message_id")
    if not prompt_id:
        return
    await state.update_data(prompt_message_id=None)
    try:
        await bot.edit_message_reply_markup(
            chat_id=chat_id, message_id=prompt_id, reply_markup=None
        )
    except TelegramBadRequest:
        pass


async def render_cart(callback: CallbackQuery, state: FSMContext):
    cart = await get_cart(state)
    if not cart:
        await callback.message.edit_text(
            "🛒 <b>Корзина пуста</b>\n\nДобавьте блюда из меню 👇",
            reply_markup=empty_cart_kb(),
        )
    else:
        items_text, total = cart_summary(cart)
        await callback.message.edit_text(
            f"🛒 <b>Ваша корзина</b>\n\n{items_text}\n\n"
            f"<b>Итого: {total} руб.</b>\n\n"
            "Уберите лишнее кнопкой ➖ или оформите заказ:",
            reply_markup=cart_kb(cart),
        )
    await callback.answer()


@router.callback_query(F.data == "order")
async def start_order(callback: CallbackQuery, state: FSMContext):
    cart = await get_cart(state)
    if cart:
        await render_cart(callback, state)
    else:
        await callback.message.edit_text(
            "🍽 <b>Меню Bella Vista</b>\n\n"
            "Выберите категорию и добавьте блюда в корзину:",
            reply_markup=menu_categories_kb(),
        )
        await callback.answer()


@router.callback_query(F.data.startswith("add:"))
async def add_to_cart(callback: CallbackQuery, state: FSMContext):
    item_key = callback.data.split(":", 1)[1]
    try:
        name, _price = get_item(item_key)
    except (KeyError, ValueError, IndexError):
        await callback.answer("Позиция не найдена", show_alert=True)
        return

    cart = dict(await get_cart(state))
    cart[item_key] = cart.get(item_key, 0) + 1
    await state.update_data(cart=cart)

    category_key = item_key.split(":", 1)[0]
    try:
        await callback.message.edit_reply_markup(
            reply_markup=category_kb(category_key, cart_count(cart))
        )
    except TelegramBadRequest:
        pass
    await callback.answer(f"Добавлено: {name}")


@router.callback_query(F.data == "cart")
async def show_cart(callback: CallbackQuery, state: FSMContext):
    await render_cart(callback, state)


@router.callback_query(F.data.startswith("remove:"))
async def remove_from_cart(callback: CallbackQuery, state: FSMContext):
    item_key = callback.data.split(":", 1)[1]
    cart = dict(await get_cart(state))
    if item_key in cart:
        cart[item_key] -= 1
        if cart[item_key] <= 0:
            del cart[item_key]
        await state.update_data(cart=cart)
    await render_cart(callback, state)


@router.callback_query(F.data == "cart_clear")
async def clear_cart(callback: CallbackQuery, state: FSMContext):
    await state.update_data(cart={})
    await render_cart(callback, state)


@router.callback_query(F.data == "checkout")
async def checkout(callback: CallbackQuery, state: FSMContext):
    cart = await get_cart(state)
    if not cart:
        await callback.answer("Корзина пуста", show_alert=True)
        return
    data = await state.get_data()
    if data.get("prompt_message_id") not in (None, callback.message.message_id):
        await remove_prompt_kb(callback.bot, callback.message.chat.id, state)
    await state.set_state(OrderStates.waiting_name)
    await callback.message.edit_text(
        "🛒 <b>Оформление заказа</b>\n\nКак вас зовут?",
        reply_markup=cancel_order_kb(),
    )
    await state.update_data(prompt_message_id=callback.message.message_id)
    await callback.answer()


@router.callback_query(F.data == "order_cancel")
async def cancel_checkout(callback: CallbackQuery, state: FSMContext):
    current = await state.get_state()
    if current not in CHECKOUT_STATES:
        # Stale Cancel button from an already finished or reset checkout.
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass
        await callback.answer("Эта кнопка уже неактуальна")
        return
    # Cancel checkout but keep the cart so the user can resume later.
    await state.set_state(None)
    data = await state.get_data()
    if data.get("prompt_message_id") != callback.message.message_id:
        await remove_prompt_kb(callback.bot, callback.message.chat.id, state)
    else:
        await state.update_data(prompt_message_id=None)
    try:
        await callback.message.edit_text(
            "Оформление отменено. Корзина сохранена 🛒",
            reply_markup=main_menu_kb(),
        )
    except TelegramBadRequest:
        pass
    await callback.answer()


async def resend_name_prompt(message: Message, state: FSMContext, text: str):
    """Re-ask for the name, moving the Cancel button to the newest prompt."""
    await remove_prompt_kb(message.bot, message.chat.id, state)
    sent = await message.answer(text, reply_markup=cancel_order_kb())
    await state.update_data(prompt_message_id=sent.message_id)


@router.message(OrderStates.waiting_name, F.text)
async def process_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if name.startswith("/") or not (2 <= len(name) <= 50) or not any(ch.isalpha() for ch in name):
        await resend_name_prompt(message, state, "Пожалуйста, введите имя текстом (2–50 символов).")
        return
    await remove_prompt_kb(message.bot, message.chat.id, state)
    await state.update_data(name=name)
    await state.set_state(OrderStates.waiting_phone)
    await message.answer(
        "Отправьте номер телефона кнопкой ниже или введите его вручную:",
        reply_markup=contact_kb(),
    )


@router.message(OrderStates.waiting_name)
async def process_name_invalid(message: Message, state: FSMContext):
    await resend_name_prompt(message, state, "Пожалуйста, введите имя текстом.")


@router.message(OrderStates.waiting_phone, F.text == CANCEL_TEXT)
async def cancel_phone(message: Message, state: FSMContext):
    # Cancel checkout but keep the cart.
    await state.set_state(None)
    await message.answer(
        "Оформление отменено. Корзина сохранена 🛒",
        reply_markup=ReplyKeyboardRemove(),
    )
    await message.answer("Главное меню:", reply_markup=main_menu_kb())


@router.message(OrderStates.waiting_phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    await finish_order(message, state, message.contact.phone_number)


@router.message(OrderStates.waiting_phone, F.text)
async def process_phone_text(message: Message, state: FSMContext):
    raw = message.text.strip()
    digits = re.sub(r"\D", "", raw)
    if not 10 <= len(digits) <= 15:
        await message.answer(
            "Похоже, это не номер телефона. Введите номер в формате "
            "+7 999 123-45-67 или нажмите кнопку ниже."
        )
        return
    phone = "+" + digits if raw.startswith("+") else digits
    await finish_order(message, state, phone)


@router.message(OrderStates.waiting_phone)
async def process_phone_invalid(message: Message):
    await message.answer("Отправьте номер кнопкой ниже или введите его текстом.")


async def finish_order(message: Message, state: FSMContext, phone: str):
    data = await state.get_data()
    name = data.get("name") or "—"
    username = message.from_user.username or "—"
    cart = data.get("cart", {})
    items_text, total = cart_summary(cart) if cart else ("—", 0)

    order_logger.info(
        "name=%s | phone=%s | username=@%s | user_id=%s | items=%s | total=%s",
        name, phone, username, message.from_user.id,
        "; ".join(f"{get_item(k)[0]} x{q}" for k, q in cart.items()) or "—", total,
    )

    if ADMIN_CHAT_ID:
        order_text = (
            "🆕 <b>Новый заказ — Bella Vista</b>\n\n"
            f"{html.escape(items_text)}\n\n"
            f"<b>Итого: {total} руб.</b>\n\n"
            f"Имя: {html.escape(name)}\n"
            f"Телефон: {html.escape(phone)}\n"
            f"Username: @{html.escape(username)}"
        )
        try:
            await message.bot.send_message(ADMIN_CHAT_ID, order_text)
        except Exception:
            logger.exception(
                "Failed to notify admin (ADMIN_CHAT_ID=%s), order saved to orders.log",
                ADMIN_CHAT_ID,
            )

    await state.clear()
    await message.answer(
        "✅ Спасибо! Ваш заказ принят, скоро с вами свяжется администратор.",
        reply_markup=ReplyKeyboardRemove(),
    )
    await message.answer("Главное меню:", reply_markup=main_menu_kb())
