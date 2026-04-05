import pytest
import sqlite3
import tempfile
import os
from unittest.mock import AsyncMock, patch, MagicMock

import database
import binance_client
from monitor import condicion_cumplida

@pytest.fixture(autouse=True)
def db_limpia(monkeypatch, tmp_path):
    db_file = tmp_path / "test.db"
    monkeypatch.setattr(database, "DB_PATH", str(db_file))
    database.init_db()
    yield
# ─────────────────────────────────────────
# DATABASE — alarmas
# ─────────────────────────────────────────

class TestAlarmas:
    def test_crear_y_listar_alarma(self):
        database.crear_alarma("123", "BTC", "mayor", 95000)
        alarmas = database.listar_alarmas("123")
        assert len(alarmas) == 1
        assert alarmas[0][2] == "BTC"
        assert alarmas[0][3] == "mayor"
        assert alarmas[0][4] == 95000

    def test_listar_solo_del_usuario(self):
        database.crear_alarma("123", "BTC", "mayor", 95000)
        database.crear_alarma("456", "ETH", "menor", 2000)
        assert len(database.listar_alarmas("123")) == 1
        assert len(database.listar_alarmas("456")) == 1

    def test_desactivar_alarma(self):
        database.crear_alarma("123", "BTC", "mayor", 95000)
        alarma_id = database.listar_alarmas("123")[0][0]
        database.desactivar_alarma(alarma_id)
        assert database.listar_alarmas("123") == []

    def test_obtener_alarmas_activas(self):
        database.crear_alarma("123", "BTC", "mayor", 95000)
        database.crear_alarma("123", "ETH", "menor", 2000)
        activas = database.obtener_alarmas_activas()
        assert len(activas) == 2

    def test_desactivar_no_afecta_otras(self):
        database.crear_alarma("123", "BTC", "mayor", 95000)
        database.crear_alarma("123", "ETH", "menor", 2000)
        id_btc = database.listar_alarmas("123")[0][0]
        database.desactivar_alarma(id_btc)
        activas = database.obtener_alarmas_activas()
        assert len(activas) == 1
        assert activas[0][2] == "ETH"


# ─────────────────────────────────────────
# DATABASE — watchlist
# ─────────────────────────────────────────

class TestWatchlist:
    def test_add_y_get(self):
        database.watchlist_add("123", "BTC")
        database.watchlist_add("123", "ETH")
        monedas = database.watchlist_get("123")
        assert "BTC" in monedas
        assert "ETH" in monedas

    def test_add_duplicado_devuelve_false(self):
        database.watchlist_add("123", "BTC")
        resultado = database.watchlist_add("123", "BTC")
        assert resultado is False

    def test_watchlist_por_usuario(self):
        database.watchlist_add("123", "BTC")
        database.watchlist_add("456", "ETH")
        assert database.watchlist_get("123") == ["BTC"]
        assert database.watchlist_get("456") == ["ETH"]

    def test_remove(self):
        database.watchlist_add("123", "BTC")
        resultado = database.watchlist_remove("123", "BTC")
        assert resultado is True
        assert database.watchlist_get("123") == []

    def test_remove_inexistente_devuelve_false(self):
        resultado = database.watchlist_remove("123", "SOL")
        assert resultado is False

    def test_get_vacia(self):
        assert database.watchlist_get("999") == []


# ─────────────────────────────────────────
# BINANCE CLIENT
# ─────────────────────────────────────────

class TestBinanceClient:
    @pytest.mark.asyncio
    async def test_obtener_precio_ok(self):
        mock_response = MagicMock()
        mock_response.json = AsyncMock(return_value={"price": "95000.50"})
        mock_response.raise_for_status = MagicMock()
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("binance_client.aiohttp.ClientSession", return_value=mock_session):
            precio = await binance_client.obtener_precio("BTC")

        assert precio == 95000.50

    @pytest.mark.asyncio
    async def test_moneda_no_encontrada(self):
        mock_response = MagicMock()
        mock_response.json = AsyncMock(return_value={"msg": "Invalid symbol"})
        mock_response.raise_for_status = MagicMock()
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("binance_client.aiohttp.ClientSession", return_value=mock_session):
            with pytest.raises(ValueError, match="Moneda no encontrada"):
                await binance_client.obtener_precio("XXXXX")


# ─────────────────────────────────────────
# MONITOR — condicion_cumplida
# ─────────────────────────────────────────

class TestCondicionCumplida:
    def test_mayor_cumplida(self):
        # objetivo 66000, threshold 0.05% → necesita >= 66033
        assert condicion_cumplida(66100, "mayor", 66000) is True

    def test_mayor_no_cumplida_cerca(self):
        # 66020 no llega al threshold
        assert condicion_cumplida(66020, "mayor", 66000) is False

    def test_mayor_justo_en_objetivo_no_salta(self):
        assert condicion_cumplida(66000, "mayor", 66000) is False

    def test_menor_cumplida(self):
        # objetivo 66000, threshold 0.05% → necesita <= 65967
        assert condicion_cumplida(65900, "menor", 66000) is True

    def test_menor_no_cumplida_cerca(self):
        assert condicion_cumplida(65980, "menor", 66000) is False

    def test_menor_justo_en_objetivo_no_salta(self):
        assert condicion_cumplida(66000, "menor", 66000) is False

    def test_condicion_invalida(self):
        assert condicion_cumplida(100, "igual", 100) is False