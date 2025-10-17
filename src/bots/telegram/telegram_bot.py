import os

import typer
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import src.config as cfg
from src.bots.telegram.flows.start import start

app = typer.Typer()


# Debug: log ANY update that arrives so you can see what type you’re getting
async def spy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(">> got update type:", update.update_id, type(update), update.to_dict())


@app.command()
def start_bot(test: bool = True) -> None:
    print("Starting Telegram bot...", flush=True)
    if test:
        cfg.config = cfg.TestConfig()

    app = (
        ApplicationBuilder()
        .token(os.environ.get("TELEGRAM_BOT_TOKEN_TEST", ""))
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    # Put this last so it doesn't swallow commands; still useful to see traffic
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, spy))

    app.run_polling()


if __name__ == "__main__":
    app()
