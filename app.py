import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from database import init_db, crear_alarma, listar_alarmas, desactivar_alarma
from monitor import monitor_precios  # monitor.py

# ─────────────────────────────────────────
# FUNCIONES DEL BOT (responden a comandos)
# ─────────────────────────────────────────
TEL_TOKEN = os.getenv("TEL_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cuando el usuario escribe /start"""
    await update.message.reply_text(
        "👋 Hola! Soy tu bot de alarmas crypto.\n\n"
        "Comandos disponibles:\n"
        "/alarma BTC > 95000 — avísame cuando BTC supere 95000$\n"
        "/alarma ETH < 3000  — avísame cuando ETH baje de 3000$\n"
        "/mis_alarmas        — ver tus alarmas activas\n"
        "/borrar 1           — borrar la alarma con id 1"
    )

async def alarma(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cuando el usuario escribe /alarma BTC > 95000"""
    chat_id = str(update.message.chat_id)

    # Comprobamos que el usuario ha escrito bien el comando
    # context.args son las palabras después de /alarma
    if len(context.args) != 3:
        await update.message.reply_text(
            "❌ Formato incorrecto\n"
            "Uso correcto: /alarma BTC > 95000"
        )
        return

    moneda = context.args[0].upper()  # BTC, ETH, SOL...
    simbolo = context.args[1]         # > o 
    
    # Comprobamos que el símbolo es válido
    if simbolo not in [">", "<"]:
        await update.message.reply_text("❌ Usa > o < como condición")
        return

    # Comprobamos que el precio es un número
    try:
        precio = float(context.args[2])
    except ValueError:
        await update.message.reply_text("❌ El precio debe ser un número")
        return

    # Convertimos > y < a palabras para guardar en la base de datos
    condicion = "mayor" if simbolo == ">" else "menor"

     # Consultamos el precio actual para mostrarlo al crear la alarma
    try:
        from monitor import obtener_precio
        precio_actual = await obtener_precio(moneda)
        info_precio = f"Precio actual: {precio_actual:,.0f}$"
    except:
        info_precio = ""
    # Guardamos la alarma
    crear_alarma(chat_id, moneda, condicion, precio)

    await update.message.reply_text(
        f"✅ Alarma creada!\n"
        f"{moneda} {simbolo} {precio:,.0f}$\n"
        f"Te aviso cuando se cumpla."
    )

async def mis_alarmas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cuando el usuario escribe /mis_alarmas"""
    chat_id = str(update.message.chat_id)
    alarmas = listar_alarmas(chat_id)

    if not alarmas:
        await update.message.reply_text("No tienes alarmas activas.")
        return

    # Construimos el mensaje con todas las alarmas
    mensaje = "🔔 Tus alarmas activas:\n\n"
    for a in alarmas:
        id, chat_id, moneda, condicion, precio, activa = a
        simbolo = ">" if condicion == "mayor" else "<"
        mensaje += f"ID {id}: {moneda} {simbolo} {precio:,.0f}$\n"

    await update.message.reply_text(mensaje)

async def borrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cuando el usuario escribe /borrar 1"""
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
    """Se ejecuta justo después de arrancar el bot"""
    init_db()
    asyncio.create_task(monitor_precios(app.bot))  # ← pasamos solo app.bot

def main():
    app = Application.builder().token(TEL_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("alarma", alarma))
    app.add_handler(CommandHandler("mis_alarmas", mis_alarmas))
    app.add_handler(CommandHandler("borrar", borrar))

    print("🤖 Bot arrancado, esperando mensajes...")
    app.run_polling()

if __name__ == "__main__":
    main()