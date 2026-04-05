import aiohttp

BINANCE_API_URL = "https://api.binance.com/api/v3/ticker/price"


async def obtener_precio(moneda: str) -> float:
    """Consulta el precio actual de una moneda en Binance (par USDT)."""
    url = f"{BINANCE_API_URL}?symbol={moneda.upper()}USDT"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            data = await response.json()
            if "price" not in data:
                raise ValueError(f"Moneda no encontrada: {moneda}")
            return float(data["price"])