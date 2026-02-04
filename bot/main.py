"""letsTrade - Railway 배포용 진입점"""

import os
from lets_trade import __version__


def main():
    """메인 실행 함수"""
    print(f"letsTrade v{__version__} starting...")

    # 환경 확인
    env = os.getenv("ENVIRONMENT", "development")
    print(f"Environment: {env}")

    # TODO: 실제 봇 로직 구현
    # - LS증권 API 연결
    # - 스케줄러 시작
    # - 텔레그램 봇 시작

    print("Bot is ready. Waiting for implementation...")


if __name__ == "__main__":
    main()
