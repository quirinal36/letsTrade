"""API 라우터 패키지"""

from .system import router as system_router
from .account import router as account_router
from .portfolio import router as portfolio_router
from .trades import router as trades_router
from .signals import router as signals_router
from .strategies import router as strategies_router
from .stocks import router as stocks_router
from .orders import router as orders_router

__all__ = [
    "system_router",
    "account_router",
    "portfolio_router",
    "trades_router",
    "signals_router",
    "strategies_router",
    "stocks_router",
    "orders_router",
]
