from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from config import ADMIN_CHAT_ID
from keyboards.keyboards import cancel_order_kb, contact_kb, main_menu_kb

router = Router()


class OrderStates(StatesGroup):
    waiting_name = State()
    waiting_phone = State()


@router.callback_query(F.data == "order")
async def start_order(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OrderStates.waiting_name)
    await callback.message.edit_text(
        "🛒 <b>Оформление заказа</b>\n\nКак вас зовут?",
        reply_markup=cancel_order_kb(),
    )
    await callback.answer()


@router.message(OrderStates.waiting_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(OrderStates.waiting_phone)
    await message.answer(
        "Отправьте номер телефона кнопкой ниже или введите его вручную:",
        reply_markup=contact_kb(),
    )


@router.message(OrderStates.waiting_phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    await finish_order(message, state, message.contact.phone_number)


@router.message(OrderStates.waiting_phone, F.text)
async def process_phone_text(message: Message, state: FSMContext):
    await finish_order(message, state, message.text)


async def finish_order(message: Message, state: FSMContext, phone: str):
    data = await state.get_data()
    name = data.get("name")

    if ADMIN_CHAT_ID:
        order_text = (
            "🆕 <b>Новый заказ — Bella Vista</b>\n\n"
            f"Имя: {name}\n"
            f"Телефон: {phone}\n"
            f"Username: @{message.from_user.username or '—'}"
        )
        await message.bot.send_message(ADMIN_CHAT_ID, order_text)

    await state.clear()
    await message.answer(
        "✅ Спасибо! Ваш заказ принят, скоро с вами свяжется администратор.",
        reply_markup=ReplyKeyboardRemove(),
    )
    await message.answer("Главное меню:", reply_markup=main_menu_kb())
