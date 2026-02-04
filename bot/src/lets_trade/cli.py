"""letsTrade CLI - Typer 기반 명령줄 인터페이스"""

import sys
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .api.client import ApiError, LSApiClient
from .api.stock import StockApi
from .api.account import AccountApi
from .api.order import OrderApi, OrderType
from .strategies.base import StrategyRegistry

# Typer 앱 초기화
app = typer.Typer(
    name="lets-trade",
    help="LS증권 API 기반 주식 자동매매 CLI",
    add_completion=False,
)

# Rich Console 초기화
console = Console()


def get_client() -> LSApiClient:
    """API 클라이언트 생성"""
    try:
        return LSApiClient()
    except Exception as e:
        console.print(f"[red]API 연결 실패:[/red] {e}")
        raise typer.Exit(1)


# ===== 시세 조회 =====

@app.command("quote")
def quote(
    symbol: str = typer.Argument(..., help="종목코드 (예: 005930)"),
    orderbook: bool = typer.Option(False, "--orderbook", "-o", help="호가 정보 포함"),
):
    """
    주식 시세 조회

    예시: lets-trade quote 005930
    """
    with get_client() as client:
        stock_api = StockApi(client)

        try:
            price = stock_api.get_price(symbol)
        except ApiError as e:
            console.print(f"[red]조회 실패:[/red] {e}")
            raise typer.Exit(1)

        # 등락 색상 결정
        if price.change > 0:
            color = "red"
            sign = "▲"
        elif price.change < 0:
            color = "blue"
            sign = "▼"
        else:
            color = "white"
            sign = "-"

        # 시세 패널 출력
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column(justify="right", style="dim")
        table.add_column(justify="right")

        table.add_row("현재가", f"[bold {color}]{price.price:,}원[/bold {color}]")
        table.add_row("전일대비", f"[{color}]{sign} {abs(price.change):,} ({price.change_rate:+.2f}%)[/{color}]")
        table.add_row("거래량", f"{price.volume:,}")
        table.add_row("시가", f"{price.open_price:,}")
        table.add_row("고가", f"[red]{price.high_price:,}[/red]")
        table.add_row("저가", f"[blue]{price.low_price:,}[/blue]")
        table.add_row("전일종가", f"{price.prev_close:,}")

        panel = Panel(
            table,
            title=f"[bold]{price.name}[/bold] ({symbol})",
            subtitle=price.timestamp.strftime("%H:%M:%S"),
            expand=False,
        )
        console.print(panel)

        # 호가 정보 출력
        if orderbook:
            try:
                ob = stock_api.get_orderbook(symbol)

                ob_table = Table(title="호가 정보")
                ob_table.add_column("매도잔량", justify="right", style="blue")
                ob_table.add_column("매도호가", justify="right", style="blue")
                ob_table.add_column("매수호가", justify="right", style="red")
                ob_table.add_column("매수잔량", justify="right", style="red")

                for i in range(min(5, len(ob.ask_prices))):
                    ask_idx = 4 - i  # 매도호가는 역순
                    ob_table.add_row(
                        f"{ob.ask_volumes[ask_idx]:,}",
                        f"{ob.ask_prices[ask_idx]:,}",
                        "",
                        "",
                    )

                for i in range(min(5, len(ob.bid_prices))):
                    ob_table.add_row(
                        "",
                        "",
                        f"{ob.bid_prices[i]:,}",
                        f"{ob.bid_volumes[i]:,}",
                    )

                console.print(ob_table)
            except ApiError as e:
                console.print(f"[yellow]호가 조회 실패:[/yellow] {e}")


# ===== 잔고 조회 =====

@app.command("balance")
def balance(
    detail: bool = typer.Option(False, "--detail", "-d", help="상세 정보 표시"),
):
    """
    계좌 잔고 조회

    예시: lets-trade balance
    """
    with get_client() as client:
        account_api = AccountApi(client)

        try:
            bal = account_api.get_balance()
        except ApiError as e:
            console.print(f"[red]조회 실패:[/red] {e}")
            raise typer.Exit(1)

        # 총평가 색상
        profit_color = "red" if bal.total_profit >= 0 else "blue"

        # 요약 정보
        summary_table = Table(show_header=False, box=None, padding=(0, 1))
        summary_table.add_column(justify="right", style="dim")
        summary_table.add_column(justify="right")

        summary_table.add_row("예수금", f"{bal.deposit:,}원")
        summary_table.add_row("주문가능", f"[green]{bal.available:,}원[/green]")
        summary_table.add_row("총평가금액", f"[bold]{bal.total_eval:,}원[/bold]")
        summary_table.add_row(
            "총평가손익",
            f"[{profit_color}]{bal.total_profit:+,.0f}원 ({bal.profit_rate:+.2f}%)[/{profit_color}]"
        )

        console.print(Panel(summary_table, title="[bold]계좌 잔고[/bold]", expand=False))

        # 보유종목
        if bal.positions:
            pos_table = Table(title="보유종목")
            pos_table.add_column("종목", style="cyan")
            pos_table.add_column("수량", justify="right")
            pos_table.add_column("평균단가", justify="right")
            pos_table.add_column("현재가", justify="right")
            pos_table.add_column("평가금액", justify="right")
            pos_table.add_column("수익률", justify="right")

            for pos in bal.positions:
                pnl_color = "red" if pos.profit_rate >= 0 else "blue"
                pos_table.add_row(
                    f"{pos.name} ({pos.symbol})",
                    f"{pos.quantity:,}",
                    f"{pos.avg_price:,.0f}",
                    f"{pos.current_price:,}",
                    f"{pos.market_value:,}",
                    f"[{pnl_color}]{pos.profit_rate:+.2f}%[/{pnl_color}]",
                )

            console.print(pos_table)
        else:
            console.print("[dim]보유 종목이 없습니다.[/dim]")


# ===== 매수 주문 =====

@app.command("buy")
def buy(
    symbol: str = typer.Argument(..., help="종목코드"),
    quantity: int = typer.Option(..., "--quantity", "-q", help="주문 수량"),
    price: Optional[int] = typer.Option(None, "--price", "-p", help="주문 가격 (미입력시 시장가)"),
    market: bool = typer.Option(False, "--market", "-m", help="시장가 주문"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="확인 없이 주문"),
):
    """
    매수 주문

    예시:
      lets-trade buy 005930 -q 10 -p 72000  # 지정가 매수
      lets-trade buy 005930 -q 10 --market  # 시장가 매수
    """
    order_type = OrderType.MARKET if market or price is None else OrderType.LIMIT
    order_price = 0 if order_type == OrderType.MARKET else (price or 0)

    with get_client() as client:
        stock_api = StockApi(client)
        order_api = OrderApi(client)

        # 종목 정보 조회
        try:
            stock_info = stock_api.get_price(symbol)
        except ApiError:
            console.print(f"[red]종목 정보 조회 실패[/red]")
            raise typer.Exit(1)

        # 주문 확인
        order_type_str = "시장가" if order_type == OrderType.MARKET else "지정가"
        price_str = f"{order_price:,}원" if order_price > 0 else "시장가"
        estimated = quantity * (order_price or stock_info.price)

        console.print(Panel(
            f"종목: [bold]{stock_info.name}[/bold] ({symbol})\n"
            f"구분: [cyan]매수[/cyan] ({order_type_str})\n"
            f"수량: {quantity:,}주\n"
            f"가격: {price_str}\n"
            f"예상금액: [bold]{estimated:,}원[/bold]",
            title="[yellow]주문 확인[/yellow]",
            expand=False,
        ))

        if not confirm:
            if not typer.confirm("주문을 실행하시겠습니까?"):
                console.print("[dim]주문이 취소되었습니다.[/dim]")
                raise typer.Exit(0)

        # 주문 실행
        try:
            result = order_api.buy(symbol, quantity, order_price, order_type)
            console.print(f"[green]주문 완료![/green] 주문번호: {result.order_no}")
        except Exception as e:
            console.print(f"[red]주문 실패:[/red] {e}")
            raise typer.Exit(1)


# ===== 매도 주문 =====

@app.command("sell")
def sell(
    symbol: str = typer.Argument(..., help="종목코드"),
    quantity: int = typer.Option(..., "--quantity", "-q", help="주문 수량"),
    price: Optional[int] = typer.Option(None, "--price", "-p", help="주문 가격 (미입력시 시장가)"),
    market: bool = typer.Option(False, "--market", "-m", help="시장가 주문"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="확인 없이 주문"),
):
    """
    매도 주문

    예시:
      lets-trade sell 005930 -q 10 -p 73000  # 지정가 매도
      lets-trade sell 005930 -q 10 --market  # 시장가 매도
    """
    order_type = OrderType.MARKET if market or price is None else OrderType.LIMIT
    order_price = 0 if order_type == OrderType.MARKET else (price or 0)

    with get_client() as client:
        stock_api = StockApi(client)
        order_api = OrderApi(client)

        # 종목 정보 조회
        try:
            stock_info = stock_api.get_price(symbol)
        except ApiError:
            console.print(f"[red]종목 정보 조회 실패[/red]")
            raise typer.Exit(1)

        # 주문 확인
        order_type_str = "시장가" if order_type == OrderType.MARKET else "지정가"
        price_str = f"{order_price:,}원" if order_price > 0 else "시장가"
        estimated = quantity * (order_price or stock_info.price)

        console.print(Panel(
            f"종목: [bold]{stock_info.name}[/bold] ({symbol})\n"
            f"구분: [magenta]매도[/magenta] ({order_type_str})\n"
            f"수량: {quantity:,}주\n"
            f"가격: {price_str}\n"
            f"예상금액: [bold]{estimated:,}원[/bold]",
            title="[yellow]주문 확인[/yellow]",
            expand=False,
        ))

        if not confirm:
            if not typer.confirm("주문을 실행하시겠습니까?"):
                console.print("[dim]주문이 취소되었습니다.[/dim]")
                raise typer.Exit(0)

        # 주문 실행
        try:
            result = order_api.sell(symbol, quantity, order_price, order_type)
            console.print(f"[green]주문 완료![/green] 주문번호: {result.order_no}")
        except Exception as e:
            console.print(f"[red]주문 실패:[/red] {e}")
            raise typer.Exit(1)


# ===== 주문 내역 =====

@app.command("orders")
def orders():
    """
    당일 주문 내역 조회

    예시: lets-trade orders
    """
    with get_client() as client:
        order_api = OrderApi(client)

        try:
            order_list = order_api.get_orders()
        except ApiError as e:
            console.print(f"[red]조회 실패:[/red] {e}")
            raise typer.Exit(1)

        if not order_list:
            console.print("[dim]당일 주문 내역이 없습니다.[/dim]")
            return

        table = Table(title="당일 주문 내역")
        table.add_column("시간", style="dim")
        table.add_column("종목")
        table.add_column("구분", justify="center")
        table.add_column("주문가", justify="right")
        table.add_column("주문량", justify="right")
        table.add_column("체결량", justify="right")
        table.add_column("상태")

        for order in order_list:
            side_color = "cyan" if order.side == "매수" else "magenta"
            table.add_row(
                order.order_time,
                f"{order.name} ({order.symbol})",
                f"[{side_color}]{order.side}[/{side_color}]",
                f"{order.order_price:,}",
                f"{order.order_qty:,}",
                f"{order.exec_qty:,}",
                order.status,
            )

        console.print(table)


# ===== 전략 서브명령어 =====

strategy_app = typer.Typer(help="전략 관리")
app.add_typer(strategy_app, name="strategy")


@strategy_app.command("list")
def strategy_list():
    """
    등록된 전략 목록

    예시: lets-trade strategy list
    """
    strategies = StrategyRegistry.list_strategies()

    if not strategies:
        console.print("[dim]등록된 전략이 없습니다.[/dim]")
        return

    table = Table(title="등록된 전략")
    table.add_column("이름")
    table.add_column("상태")

    for name in strategies:
        table.add_row(name, "[dim]대기[/dim]")

    console.print(table)


@strategy_app.command("start")
def strategy_start(
    name: str = typer.Argument(..., help="전략 이름"),
    symbol: Optional[str] = typer.Option(None, "--symbol", "-s", help="종목코드"),
):
    """
    전략 실행

    예시: lets-trade strategy start ma_crossover -s 005930
    """
    strategy_class = StrategyRegistry.get(name)

    if not strategy_class:
        console.print(f"[red]전략을 찾을 수 없습니다:[/red] {name}")
        console.print(f"[dim]사용 가능한 전략: {', '.join(StrategyRegistry.list_strategies()) or '없음'}[/dim]")
        raise typer.Exit(1)

    # TODO: 전략 인스턴스 생성 및 실행 로직 구현
    console.print(f"[green]전략 시작:[/green] {name}")
    if symbol:
        console.print(f"[dim]종목: {symbol}[/dim]")
    console.print("[yellow]전략 실행 기능은 개발 중입니다.[/yellow]")


@strategy_app.command("stop")
def strategy_stop(
    name: str = typer.Argument(..., help="전략 이름"),
):
    """
    전략 중지

    예시: lets-trade strategy stop ma_crossover
    """
    # TODO: 실행 중인 전략 중지 로직 구현
    console.print(f"[yellow]전략 중지:[/yellow] {name}")
    console.print("[yellow]전략 중지 기능은 개발 중입니다.[/yellow]")


# ===== 버전 및 정보 =====

def version_callback(value: bool):
    if value:
        from . import __version__
        console.print(f"letsTrade CLI v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True,
        help="버전 정보 표시"
    ),
):
    """
    letsTrade - LS증권 API 기반 주식 자동매매 CLI

    사용 예시:
      lets-trade quote 005930     # 삼성전자 시세 조회
      lets-trade balance          # 잔고 조회
      lets-trade buy 005930 -q 10 -p 72000  # 매수
    """
    pass


if __name__ == "__main__":
    app()
