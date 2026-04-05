import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from database import (
    init_db, crear_alarma, listar_alarmas, desactivar_alarma,
    watchlist_add, watchlist_remove, watchlist_get
)
from monitor import monitor_precios
from binance_client import obtener_precio

TEL_TOKEN = os.getenv("TEL_TOKEN")


# ─────────────────────────────────────────
# COMANDOS DEL BOT
# ─────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hola! Soy un bot de alarmas crypto.\n\n"
        "📋 Watchlist de precios:\n"
        "/precio — ver precios de tus monedas\n"
        "/precio add BTC — añadir BTC a tu lista\n"
        "/precio remove BTC — quitar BTC de tu lista\n\n"
        "🔔 Alarmas:\n"
        "/alarma BTC > 95000 — avísame cuando BTC supere 95000$\n"
        "/alarma ETH < 3000 — avísame cuando ETH baje de 3000$\n"
        "/mis_alarmas — ver tus alarmas activas\n"
        "/borrar 1 — borrar la alarma con id 1"
    )


async def precio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /precio             → muestra precios de tu watchlist
    /precio add BTC     → añade BTC a tu watchlist
    /precio remove BTC  → quita BTC de tu watchlist
    """
    chat_id = str(update.message.chat_id)

    # /precio add BTC
    if len(context.args) == 2 and context.args[0].lower() == "add":
        moneda = context.args[1].upper()
        try:
            await obtener_precio(moneda)
        except ValueError:
            await update.message.reply_text(f"❌ Moneda no encontrada en Binance: {moneda}")
            return
        except Exception:
            await update.message.reply_text("❌ Error consultando Binance. Inténtalo de nuevo.")
            return

        añadida = watchlist_add(chat_id, moneda)
        if añadida:
            await update.message.reply_text(f"✅ {moneda} añadida a tu watchlist.")
        else:
            await update.message.reply_text(f"⚠️ {moneda} ya estaba en tu watchlist.")
        return

    # /precio remove BTC
    if len(context.args) == 2 and context.args[0].lower() == "remove":
        moneda = context.args[1].upper()
        eliminada = watchlist_remove(chat_id, moneda)
        if eliminada:
            await update.message.reply_text(f"🗑️ {moneda} eliminada de tu watchlist.")
        else:
            await update.message.reply_text(f"⚠️ {moneda} no estaba en tu watchlist.")
        return

    # /precio — mostrar watchlist
    if len(context.args) == 0:
        monedas = watchlist_get(chat_id)

        if not monedas:
            await update.message.reply_text(
                "Tu watchlist está vacía.\n"
                "Añade monedas con /precio add BTC"
            )
            return

        resultados = await asyncio.gather(
            *[obtener_precio(m) for m in monedas],
            return_exceptions=True
        )

        lineas = []
        for moneda, resultado in zip(monedas, resultados):
            if isinstance(resultado, Exception):
                lineas.append(f"• {moneda}: error al consultar")
            else:
                lineas.append(f"• {moneda}: {resultado:,.2f}$")

        mensaje = "💰 Tu watchlist:\n\n" + "\n".join(lineas)
        await update.message.reply_text(mensaje)
        return

    # Uso incorrecto
    await update.message.reply_text(
        "Uso:\n"
        "/precio — ver tu watchlist\n"
        "/precio add BTC — añadir moneda\n"
        "/precio remove BTC — quitar moneda"
    )


async def alarma(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)

    if len(context.args) != 3:
        await update.message.reply_text(
            "❌ Formato incorrecto\n"
            "Uso correcto: /alarma BTC > 95000"
        )
        return

    moneda = context.args[0].upper()
    simbolo = context.args[1]

    if simbolo not in [">", "<"]:
        await update.message.reply_text("❌ Usa > o < como condición")
        return

    try:
        precio_objetivo = float(context.args[2])
    except ValueError:
        await update.message.reply_text("❌ El precio debe ser un número")
        return

    condicion = "mayor" if simbolo == ">" else "menor"

    try:
        precio_actual = await obtener_precio(moneda)
        info_precio = f"Precio actual: {precio_actual:,.2f}$"
    except Exception:
        info_precio = ""

    crear_alarma(chat_id, moneda, condicion, precio_objetivo)

    confirmacion = f"✅ Alarma creada!\n{moneda} {simbolo} {precio_objetivo:,.0f}$\n"
    if info_precio:
        confirmacion += f"{info_precio}\n"
    confirmacion += "Te aviso cuando se cumpla."

    await update.message.reply_text(confirmacion)


async def mis_alarmas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    alarmas = listar_alarmas(chat_id)

    if not alarmas:
        await update.message.reply_text("No tienes alarmas activas.")
        return

    mensaje = "🔔 Tus alarmas activas:\n\n"
    for a in alarmas:
        id, _, moneda, condicion, precio, activa = a
        simbolo = ">" if condicion == "mayor" else "<"
        mensaje += f"ID {id}: {moneda} {simbolo} {precio:,.0f}$\n"

    await update.message.reply_text(mensaje)


async def borrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Uso: /borrar <id>")
        return

    try:
        alarma_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ El ID debe ser un número")
        return

    desactivar_alarma(alarma_id)
    await update.message.reply_text(f"🗑️ Alarma {alarma_id} borrada.")


# ─────────────────────────────────────────
# ARRANQUE
# ─────────────────────────────────────────

async def post_init(app: Application):
    init_db()
    asyncio.create_task(monitor_precios(app.bot))


def main():
    app = Application.builder().token(TEL_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("precio", precio))
    app.add_handler(CommandHandler("alarma", alarma))
    app.add_handler(CommandHandler("mis_alarmas", mis_alarmas))
    app.add_handler(CommandHandler("borrar", borrar))

    print("🤖 Bot arrancado, esperando mensajes...")
    app.run_polling()


if __name__ == "__main__":
    main()