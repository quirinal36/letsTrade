"""Telegram 알림 서비스"""

import asyncio
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from telegram import Bot
from telegram.error import TelegramError


@dataclass
class TradeNotification:
    """체결 알림 데이터"""
    symbol: str
    name: str
    side: str  # "매수" or "매도"
    quantity: int
    price: int
    total_amount: int


@dataclass
class SignalNotification:
    """시그널 알림 데이터"""
    strategy_name: str
    signal_type: str  # "매수" or "매도" or "홀드"
    symbol: str
    name: str
    current_price: int
    strength: float = 0.0
    reason: str = ""


@dataclass
class DailyReport:
    """일일 리포트 데이터"""
    date: datetime
    total_asset: int
    daily_profit: int
    daily_profit_rate: float
    buy_count: int
    sell_count: int
    positions: list[dict] = None


class TelegramNotifier:
    """Telegram 알림 발송 서비스"""

    def __init__(
        self,
        token: Optional[str] = None,
        chat_id: Optional[str] = None,
    ):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")

        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN이 필요합니다.")
        if not self.chat_id:
            raise ValueError("TELEGRAM_CHAT_ID가 필요합니다.")

        self.bot = Bot(token=self.token)

    async def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """
        메시지 발송

        Args:
            text: 메시지 내용
            parse_mode: 파싱 모드 (HTML or Markdown)

        Returns:
            bool: 발송 성공 여부
        """
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode=parse_mode,
            )
            return True
        except TelegramError as e:
            print(f"Telegram 메시지 발송 실패: {e}")
            return False

    def send_message_sync(self, text: str, parse_mode: str = "HTML") -> bool:
        """동기 방식 메시지 발송"""
        return asyncio.run(self.send_message(text, parse_mode))

    async def notify_trade(self, trade: TradeNotification) -> bool:
        """
        체결 알림 발송

        Args:
            trade: 체결 정보

        Returns:
            bool: 발송 성공 여부
        """
        emoji = "🔵" if trade.side == "매수" else "🔴"
        message = f"""
{emoji} <b>[체결] {trade.name} {trade.side}</b>

종목코드: {trade.symbol}
수량: {trade.quantity:,}주
가격: {trade.price:,}원
총금액: {trade.total_amount:,}원
시간: {datetime.now().strftime("%H:%M:%S")}
        """.strip()

        return await self.send_message(message)

    async def notify_signal(self, signal: SignalNotification) -> bool:
        """
        시그널 알림 발송

        Args:
            signal: 시그널 정보

        Returns:
            bool: 발송 성공 여부
        """
        if signal.signal_type == "매수":
            emoji = "📈"
        elif signal.signal_type == "매도":
            emoji = "📉"
        else:
            emoji = "⏸"

        strength_bar = "█" * int(signal.strength * 10) + "░" * (10 - int(signal.strength * 10))

        message = f"""
{emoji} <b>[시그널] {signal.strategy_name} - {signal.signal_type}</b>

종목: {signal.name} ({signal.symbol})
현재가: {signal.current_price:,}원
강도: [{strength_bar}] {signal.strength*100:.0f}%
{f'사유: {signal.reason}' if signal.reason else ''}
시간: {datetime.now().strftime("%H:%M:%S")}
        """.strip()

        return await self.send_message(message)

    async def notify_daily_report(self, report: DailyReport) -> bool:
        """
        일일 리포트 발송

        Args:
            report: 리포트 데이터

        Returns:
            bool: 발송 성공 여부
        """
        profit_emoji = "📈" if report.daily_profit >= 0 else "📉"
        profit_sign = "+" if report.daily_profit >= 0 else ""

        # 보유 종목 리스트
        positions_text = ""
        if report.positions:
            positions_text = "\n<b>보유 종목:</b>\n"
            for pos in report.positions[:5]:  # 최대 5개
                pos_emoji = "🟢" if pos.get("profit_rate", 0) >= 0 else "🔴"
                positions_text += f"{pos_emoji} {pos['name']}: {pos.get('profit_rate', 0):+.1f}%\n"
            if len(report.positions) > 5:
                positions_text += f"... 외 {len(report.positions) - 5}종목\n"

        message = f"""
📊 <b>일일 리포트</b> ({report.date.strftime("%Y-%m-%d")})

<b>자산 현황</b>
총자산: {report.total_asset:,}원
일일 손익: {profit_sign}{report.daily_profit:,}원 ({profit_sign}{report.daily_profit_rate:.2f}%)

<b>거래 현황</b>
매수: {report.buy_count}건
매도: {report.sell_count}건
{positions_text}
{profit_emoji} 오늘도 성공적인 투자 되세요!
        """.strip()

        return await self.send_message(message)

    async def notify_error(self, error_message: str, context: str = "") -> bool:
        """
        에러 알림 발송

        Args:
            error_message: 에러 메시지
            context: 에러 발생 컨텍스트

        Returns:
            bool: 발송 성공 여부
        """
        message = f"""
⚠️ <b>[에러 발생]</b>

{f'컨텍스트: {context}' if context else ''}
에러: {error_message}
시간: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        """.strip()

        return await self.send_message(message)

    async def notify_startup(self) -> bool:
        """봇 시작 알림"""
        message = f"""
🚀 <b>letsTrade 봇 시작</b>

시작 시간: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
상태: 정상 작동 중
        """.strip()

        return await self.send_message(message)

    async def notify_shutdown(self) -> bool:
        """봇 종료 알림"""
        message = f"""
🛑 <b>letsTrade 봇 종료</b>

종료 시간: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        """.strip()

        return await self.send_message(message)
