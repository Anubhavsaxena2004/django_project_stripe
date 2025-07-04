from django.core.management.base import BaseCommand
from telegram_bot.bot import run_telegram_bot

class Command(BaseCommand):
    help = 'Run the Telegram bot for stock predictions.'

    def handle(self, *args, **options):
        run_telegram_bot() 