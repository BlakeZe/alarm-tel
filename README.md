# alarm-tel

[![CI](https://github.com/BlakeZe/alarm-tel/actions/workflows/ci.yml/badge.svg)](https://github.com/BlakeZe/alarm-tel/actions/workflows/ci.yml)

Bot de Telegram para alertas de precios de criptomonedas en tiempo real.

## Que hace

- Crea alertas de precio para cualquier criptomoneda (BTC, ETH, SOL...)
- Avisa por Telegram cuando el precio sube o baja de tu objetivo
- Watchlist de precios por usuario, persistida en base de datos
- Consulta precios en tiempo real desde la API de Binance
- Umbral de confirmacion del 0.05% para evitar falsas alertas

## Stack

Python · SQLite · Docker · Telegram Bot API · Binance API

## Comandos

| Comando | Descripcion |
|---|---|
| `/precio` | Ver precios de tu watchlist |
| `/precio add BTC` | Añadir BTC a tu watchlist |
| `/precio remove BTC` | Quitar BTC de tu watchlist |
| `/alarma BTC > 95000` | Avisa cuando BTC supere 95.000$ |
| `/alarma ETH < 3000` | Avisa cuando ETH baje de 3.000$ |
| `/mis_alarmas` | Ver tus alarmas activas |
| `/borrar 1` | Borrar la alarma con ID 1 |

## Testing
```bash
pip install pytest pytest-asyncio
pytest test_bot.py -v
```

## Despliegue

Desplegado con Docker en Raspberry Pi 5 con reinicio automatico.