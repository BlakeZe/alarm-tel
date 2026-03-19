# alarm-tel 

Bot de Telegram para alertas de precios de criptomonedas en tiempo real.

## ¿Qué hace?

- Crea alertas de precio para cualquier criptomoneda (BTC, ETH, SOL...)
- Avisa por Telegram cuando el precio sube o baja de tu objetivo
- Consulta precios en tiempo real desde la API de Binance

## Stack

Python · SQLite · Docker · Telegram Bot API · Binance API

## Comandos

| Comando | Descripción |
|---|---|
| `/alarma BTC > 95000` | Avisa cuando BTC supere 95.000$ |
| `/alarma ETH < 3000` | Avisa cuando ETH baje de 3.000$ |
| `/mis_alarmas` | Ver tus alarmas activas |
| `/borrar 1` | Borrar la alarma con ID 1 |

## Despliegue

Desplegado con Docker en Raspberry Pi 5 con reinicio automático.
