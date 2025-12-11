from aiogram import types
from aiogram.fsm.context import FSMContext

from components.order_input import OrderInputComponent
from components.phone_input import PhoneInputComponent
from components.name_input import NameInputComponent
from components.printer_model_input import PrinterModelInputComponent
from components.issue_description_input import IssueDescriptionInputComponent
from components.message_sender import MessageSender
from models.dialog import DialogManager
from models.user import UserManager
from utils.messages import (
	BREAKDOWN_START, REQUEST_ORDER, REQUEST_NAME, REQUEST_PHONE, 
	REQUEST_PRINTER_MODEL, REQUEST_ISSUE_DESCRIPTION
)
from utils.keyboards import remove_keyboard, get_phone_keyboard, get_profile_name_keyboard, get_printer_model_keyboard

class BreakdownFlow:
	"""
	Потік обробки діалогу про поломку
	"""
	def __init__(
		self,
		dialog_manager: DialogManager,
		user_manager: UserManager,
		message_sender: MessageSender,
		order_input: OrderInputComponent,
		name_input: NameInputComponent,
		phone_input: PhoneInputComponent,
		printer_model_input: PrinterModelInputComponent,
		issue_description_input: IssueDescriptionInputComponent
	):
		self.dialog_manager = dialog_manager
		self.user_manager = user_manager
		self.message_sender = message_sender
		self.order_input = order_input
		self.name_input = name_input
		self.phone_input = phone_input
		self.printer_model_input = printer_model_input
		self.issue_description_input = issue_description_input

	async def start_flow(self, message: types.Message, state: FSMContext) -> None:
		"""
		Початок потоку діалогу
		"""
		user = message.from_user
		
		# Ініціалізація користувача
		self.user_manager.get_user(
			user_id=user.id,
			first_name=user.first_name,
			last_name=user.last_name or ""
		)
		
		# Ініціалізація діалогу
		dialog = self.dialog_manager.get_dialog(user.id)
		dialog.current_step = "initial"
		
		# Відправка початкового повідомлення та приховування клавіатури
		await self.message_sender.send_message(
			message.chat.id,
			BREAKDOWN_START,
			keyboard=remove_keyboard
		)
		await self.message_sender.send_message(message.chat.id, REQUEST_ORDER)
		
	async def handle_step(self, message: types.Message, state: FSMContext) -> None:
		"""
		Обробка поточного кроку діалогу
		"""
		user_id = message.from_user.id
		dialog = self.dialog_manager.get_dialog(user_id)
		
		if dialog.current_step == "initial":
			await self.order_input.process_input(message)
			await self.message_sender.send_message(
				message.chat.id,
				REQUEST_NAME,
				keyboard=get_profile_name_keyboard()
			)
			dialog.current_step = "name_input"
		elif dialog.current_step == "name_input":
			if message.text == "👤 Використати ім'я з профілю":
				user = message.from_user
				self.user_manager.update_user(
					user_id,
					first_name=user.first_name,
					last_name=user.last_name or ""
				)
				dialog.current_step = "phone_input"
				await self.message_sender.send_message(
					message.chat.id,
					f"✅ Зафіксували ваші дані: {user.first_name} {user.last_name or ''}",
					keyboard=remove_keyboard
				)
				await self.message_sender.send_message(
					message.chat.id,
					REQUEST_PHONE,
					keyboard=get_phone_keyboard()
				)
			else:
				await self.name_input.process_input(message)
				if dialog.current_step == "phone_input":
					await self.message_sender.send_message(
						message.chat.id,
						REQUEST_PHONE,
						keyboard=get_phone_keyboard()
					)
		elif dialog.current_step == "phone_input":
			await self.phone_input.process_input(message)
			if dialog.current_step == "printer_model_input":
				await self.message_sender.send_message(
					message.chat.id,
					REQUEST_PRINTER_MODEL,
					keyboard=get_printer_model_keyboard()
				)
		elif dialog.current_step == "printer_model_input":
			await self.printer_model_input.process_input(message)
			if dialog.current_step == "issue_description":
				await self.message_sender.send_message(
					message.chat.id,
					REQUEST_ISSUE_DESCRIPTION
				)
		elif dialog.current_step == "issue_description":
			await self.issue_description_input.process_input(message)

