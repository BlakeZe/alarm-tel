import asyncio
import aiohttp
from telegram import Bot
from database import obtener_alarmas_activas, desactivar_alarma

async def obtener_precio(moneda: str) -> float:
    """Consulta el precio actual de una moneda en Binance"""
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={moneda}USDT"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            return float(data["price"])

async def monitor_precios(bot: Bot):
    """Revisa todas las alarmas activas cada 30 segundos"""
    while True:
        alarmas = obtener_alarmas_activas()

        for alarma in alarmas:
            id, chat_id, moneda, condicion, precio_objetivo, activa = alarma

            try:
                precio_actual = await obtener_precio(moneda)

                disparada = (
                    condicion == "mayor" and precio_actual >= precio_objetivo or
                    condicion == "menor" and precio_actual <= precio_objetivo
                )

                if disparada:
                    simbolo = ">" if condicion == "mayor" else "<"
                    await bot.send_message(
                        chat_id=chat_id,
                        text=(
                            f"🚨 ALARMA DISPARADA\n"
                            f"{moneda} {simbolo} {precio_objetivo:,.0f}$\n"
                            f"Precio actual: {precio_actual:,.0f}$"
                        )
                    )
                    desactivar_alarma(id)

            except Exception as e:
                print(f"Error consultando {moneda}: {e}")

        await asyncio.sleep(30)