import asyncio
from telegram import Bot
from database import obtener_alarmas_activas, desactivar_alarma
from binance_client import obtener_precio

THRESHOLD = 0.0005  # 0.05% — la alarma solo salta si el precio está dentro de este margen


def condicion_cumplida(precio_actual: float, condicion: str, precio_objetivo: float) -> bool:
    """
    Comprueba si se cumple la condición de una alarma.

    Para evitar falsos positivos, por ejemplo que solo toque el precio. Simplemente un margen
    que permite asegurarse del precio objetivo
    """
    margen = precio_objetivo * THRESHOLD
    if condicion == "mayor":
        return precio_actual >= precio_objetivo + margen
    elif condicion == "menor":
        return precio_actual <= precio_objetivo - margen
    return False


async def monitor_precios(bot: Bot):
    """Revisa todas las alarmas activas cada 30 segundos."""
    while True:
        alarmas = obtener_alarmas_activas()
        for alarma in alarmas:
            id, chat_id, moneda, condicion, precio_objetivo, activa = alarma
            try:
                precio_actual = await obtener_precio(moneda)

                if condicion_cumplida(precio_actual, condicion, precio_objetivo):
                    simbolo = ">" if condicion == "mayor" else "<"
                    await bot.send_message(
                        chat_id=chat_id,
                        text=(
                            f"🚨 ALARMA DISPARADA\n"
                            f"{moneda} {simbolo} {precio_objetivo:,.0f}$\n"
                            f"Precio actual: {precio_actual:,.2f}$"
                        )
                    )
                    desactivar_alarma(id)

            except Exception as e:
                print(f"Error consultando {moneda}: {e}")

        await asyncio.sleep(10)