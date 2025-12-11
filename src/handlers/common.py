from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.markdown import hbold

from keyboards.reply import get_main_keyboard
from utils.messages import WELCOME_MESSAGE, QUALITY_START, FAQ_START

router = Router(name="common")

@router.message(Command("start"))
async def cmd_start(message: Message):
	"""
	Обработчик команды /start
	"""
	await message.answer(
		WELCOME_MESSAGE.format(name=hbold(message.from_user.full_name)),
		reply_markup=get_main_keyboard()
	)

@router.message(lambda m: m.text == "🖨 Якість друку")
async def handle_quality(message: Message):
	"""
	Обработчик раздела качества печати
	"""
	await message.answer(QUALITY_START)

@router.message(lambda m: m.text == "❓ Питання / Відповідь")
async def handle_faq(message: Message):
	"""
	Обработчик раздела вопросов
	"""
	await message.answer(FAQ_START)