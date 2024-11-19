import os

from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import timedelta, timezone
from cryptography.fernet import Fernet

from config import settings

engine = create_engine('sqlite:///ecp_errors.db')
Base = declarative_base()

class Message(Base):
    __tablename__ = 'errors'
    id = Column(Integer, primary_key=True)
    title = Column(String(150))
    user_fn = Column(String(150))
    user_ln = Column(String(150))
    username = Column(String(50))
    message = Column(Text)
    datetime = Column(String(150))


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()


def keyword_filter(message_text):
    keywords = settings.KEYWORDS
    return any(keyword in message_text.lower() for keyword in keywords)


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    message_text = update.message.text

    if keyword_filter(message_text):
        time = update.message.date

        moscow_offset = timedelta(hours=3)
        moscow_tz = timezone(moscow_offset)

        moscow_time = time.astimezone(moscow_tz)
        formatted_time = moscow_time.strftime('%d-%m-%Y %H:%M:%S')

        try:
            theme = update.message.reply_to_message.forum_topic_created.name
        except Exception:
            theme = 'Undefined'
        new_message = Message(
            title=theme,
            user_fn=update.message.from_user.first_name,
            user_ln=update.message.from_user.last_name,
            username=update.message.from_user.username or "Unknown",
            message=message_text,
            datetime=formatted_time
        )
        session.add(new_message)
        session.commit()


def main():
    key = os.getenv('PFR_KEY')
    if not key:
        ValueError('Ключ шифрования не найден.')

    cipher = Fernet(key.encode())

    token = settings.TOKEN

    BOT_TOKEN = cipher.decrypt(token.encode()).decode()

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(MessageHandler(filters.TEXT, message_handler))

    application.run_polling()


if __name__ == '__main__':
    main()

