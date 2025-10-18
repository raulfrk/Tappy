import os
import sys

import typer
from loguru import logger
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
logger.remove()  # remove default handler
logger.add(
    sys.stdout,
    format="{time} <level>{level}</level> {name}:{function}:{line} <level>{message}</level> - <cyan>{extra}</cyan>",
    colorize=True,
    level="DEBUG",
)


# Debug: log ANY update that arrives so you can see what type you’re getting
async def spy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.debug(
        "got update",
        update_id=update.update_id,
        update_type=type(update),
        content=update.to_dict(),
    )


@app.command()
def start_bot(test: bool = True) -> None:
    log = logger.bind(env="test" if test else "prod")
    if test:
        cfg.config = cfg.TestConfig()
    else:
        cfg.config = cfg.ProdConfig()
    log.info("starting telegram bot", config=cfg.config.model_dump())
    app = (
        ApplicationBuilder()
        .token(os.environ.get("TELEGRAM_BOT_TOKEN_TEST", ""))
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, spy))

    app.run_polling()


if __name__ == "__main__":
    app()
