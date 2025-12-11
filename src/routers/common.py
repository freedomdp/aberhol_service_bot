from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.markdown import hbold

from utils.messages import WELCOME_MESSAGE, QUALITY_START, FAQ_START
from keyboards.reply import get_main_keyboard, remove_keyboard

router = Router(name="common")

@router.message(Command("start"))
async def cmd_start(message: Message):
	"""
	Обробник команди /start
	"""
	await message.answer(
		WELCOME_MESSAGE.format(name=hbold(message.from_user.full_name)),
		reply_markup=get_main_keyboard()
	)

@router.message(F.text == "🖨 Якість друку")
async def handle_quality(message: Message):
	"""
	Обробник розділу якості друку
	"""
	await message.answer(QUALITY_START, reply_markup=remove_keyboard())

@router.message(F.text == "❓ Питання / Відповідь")
async def handle_faq(message: Message):
	"""
	Обробник розділу питань
	"""
	await message.answer(FAQ_START, reply_markup=remove_keyboard())