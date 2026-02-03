# LS 증권 자동매매 프로그램 개발 계획

## 프로젝트 개요
- **프로젝트명**: letsTrade
- **목표**: LS 증권 Open API를 활용한 주식 자동매매 프로그램 개발
- **기술 스택**:
  - **백엔드**: Python 3.10, FastAPI
  - **프론트엔드**: Next.js (웹 대시보드)
  - **데이터베이스**: SQLite (로컬 캐시) + Supabase (클라우드 저장소)
  - **배포**: Vercel (대시보드)
  - **알림**: Telegram Bot API
- **참고 자료**: [LS증권 Open API 공식 사이트](https://openapi.ls-sec.co.kr/)

---

## 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                        로컬 자동매매 봇                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ LS증권 API   │  │   SQLite     │  │   매매 전략 엔진      │  │
│  │  연동 모듈   │──│  (실시간)    │──│  (시그널 생성)       │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │ 동기화 (체결 시 즉시 / 시세 1분 배치)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Supabase Cloud                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ PostgreSQL   │  │  Realtime    │  │   Edge Functions     │  │
│  │ (영구 저장)  │  │  (구독)      │  │   (알림 발송)        │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────────┐  ┌──────────────┐
│ 웹 대시보드   │  │  Telegram 알림   │  │  모바일 접근  │
│   (Vercel)   │  │                  │  │              │
└──────────────┘  └──────────────────┘  └──────────────┘
```

---

## 마일스톤 1: 프로젝트 초기 설정 (v0.1.0)

### Issue #1: 프로젝트 구조 설정
**Labels**: `setup`, `priority: high`

- [ ] Python 프로젝트 초기화 (pyproject.toml)
- [ ] 디렉토리 구조 설계
  ```
  letsTrade/
  ├── bot/                    # 자동매매 봇 (Python)
  │   ├── src/
  │   │   └── lets_trade/
  │   │       ├── __init__.py
  │   │       ├── api/        # LS증권 API 연동
  │   │       ├── models/     # 데이터 모델
  │   │       ├── strategies/ # 매매 전략
  │   │       ├── services/   # 비즈니스 로직
  │   │       ├── db/         # 데이터베이스 (SQLite + Supabase)
  │   │       └── utils/      # 유틸리티
  │   ├── tests/
  │   └── pyproject.toml
  ├── dashboard/              # 웹 대시보드 (Next.js)
  │   ├── src/
  │   ├── package.json
  │   └── ...
  ├── supabase/               # Supabase 설정
  │   └── migrations/
  ├── .env.example
  └── README.md
  ```
- [ ] 개발 환경 설정 (poetry, pre-commit)
- [ ] .gitignore 설정
- [ ] 환경 변수 관리 구조 설정 (.env)

### Issue #2: 데이터베이스 설정
**Labels**: `setup`, `database`, `priority: high`

- [ ] Supabase 프로젝트 생성
- [ ] 데이터베이스 스키마 설계
- [ ] SQLite 로컬 캐시 테이블 설계
- [ ] Supabase 테이블 생성 (마이그레이션)
- [ ] 동기화 로직 설계

### Issue #3: LS증권 API 인증 모듈 개발
**Labels**: `feature`, `api`, `priority: high`

- [ ] APP Key, APP Secret 관리
- [ ] Access Token 발급 기능
- [ ] Token 갱신 및 만료 관리
- [ ] API 기본 클라이언트 클래스 구현

---

## 마일스톤 2: 핵심 API 연동 (v0.2.0)

### Issue #4: 주식 시세 조회 기능
**Labels**: `feature`, `api`

- [ ] 현재가 조회 API 연동
- [ ] 호가 조회 API 연동
- [ ] 체결 내역 조회 API 연동
- [ ] 시세 데이터 모델 정의
- [ ] SQLite 캐싱 구현

### Issue #5: 계좌 정보 조회 기능
**Labels**: `feature`, `api`

- [ ] 주식 잔고 조회 API 연동
- [ ] 예수금 조회 API 연동
- [ ] 계좌 데이터 모델 정의
- [ ] Supabase 동기화 구현

### Issue #6: 주식 주문 기능
**Labels**: `feature`, `api`, `priority: high`

- [ ] 매수 주문 API 연동
- [ ] 매도 주문 API 연동
- [ ] 주문 정정/취소 API 연동
- [ ] 주문 데이터 모델 정의
- [ ] 주문 유효성 검증 로직

### Issue #7: 거래 내역 조회 기능
**Labels**: `feature`, `api`

- [ ] 체결 내역 조회 API 연동
- [ ] 미체결 내역 조회 API 연동
- [ ] 거래 내역 데이터 모델 정의
- [ ] Supabase 거래 이력 저장

---

## 마일스톤 3: 자동매매 전략 엔진 (v0.3.0)

### Issue #8: 전략 프레임워크 구축
**Labels**: `feature`, `strategy`, `priority: high`

- [ ] 전략 베이스 클래스 설계 (Strategy Interface)
- [ ] 시그널 생성 구조 (BUY/SELL/HOLD)
- [ ] 백테스팅 프레임워크 기본 구조
- [ ] 전략 설정 관리 (YAML/JSON)

### Issue #9: 기본 매매 전략 구현
**Labels**: `feature`, `strategy`

- [ ] 이동평균선 교차 전략 (MA Crossover)
- [ ] RSI 기반 전략
- [ ] 볼린저 밴드 전략
- [ ] 복합 전략 조합 기능

### Issue #10: 리스크 관리 모듈
**Labels**: `feature`, `strategy`, `priority: high`

- [ ] 손절/익절 자동화
- [ ] 포지션 사이징 (자금 관리)
- [ ] 일일 최대 손실 제한
- [ ] 거래 횟수 제한

### Issue #11: 매매 서비스 계층 구현
**Labels**: `feature`, `service`

- [ ] 주문 서비스 클래스 구현
- [ ] 포트폴리오 관리 서비스 구현
- [ ] 손익 계산 로직 구현
- [ ] 전략 실행 엔진

---

## 마일스톤 4: 알림 시스템 (v0.4.0)

### Issue #12: Telegram 알림 봇
**Labels**: `feature`, `notification`, `priority: high`

- [ ] Telegram Bot 생성 및 설정
- [ ] 알림 메시지 템플릿 설계
- [ ] 체결 알림 (매수/매도 완료)
- [ ] 시그널 알림 (전략 신호 발생)
- [ ] 일일 리포트 알림

### Issue #13: Supabase Edge Functions 알림
**Labels**: `feature`, `notification`

- [ ] Edge Function 설정
- [ ] 실시간 이벤트 트리거
- [ ] 긴급 알림 (급등/급락, 손절 등)

---

## 마일스톤 5: 웹 대시보드 (v0.5.0)

### Issue #14: 대시보드 프로젝트 설정
**Labels**: `feature`, `frontend`, `priority: high`

- [ ] Next.js 프로젝트 초기화
- [ ] Supabase 클라이언트 연동
- [ ] 인증 시스템 (Supabase Auth)
- [ ] UI 컴포넌트 라이브러리 (shadcn/ui)

### Issue #15: 대시보드 핵심 페이지
**Labels**: `feature`, `frontend`

- [ ] 대시보드 홈 (포트폴리오 요약)
- [ ] 실시간 잔고 현황
- [ ] 거래 내역 테이블
- [ ] 수익률 차트 (일별/월별)

### Issue #16: 전략 관리 페이지
**Labels**: `feature`, `frontend`

- [ ] 전략 목록 및 상태
- [ ] 전략 활성화/비활성화
- [ ] 전략 파라미터 설정
- [ ] 백테스트 결과 시각화

### Issue #17: 실시간 모니터링
**Labels**: `feature`, `frontend`

- [ ] Supabase Realtime 구독
- [ ] 실시간 체결 알림
- [ ] 실시간 포트폴리오 업데이트
- [ ] 실시간 시세 표시

---

## 마일스톤 6: CLI 및 자동화 (v0.6.0)

### Issue #18: CLI 인터페이스 개발
**Labels**: `feature`, `cli`

- [ ] CLI 명령어 구조 설계 (typer)
- [ ] 시세 조회 명령어
- [ ] 잔고 조회 명령어
- [ ] 주문 명령어
- [ ] 전략 실행/중지 명령어

### Issue #19: 자동매매 스케줄러
**Labels**: `feature`, `automation`

- [ ] 스케줄러 기본 구조 (APScheduler)
- [ ] 장 시작/종료 감지
- [ ] 정기 실행 작업 관리
- [ ] 데이터 동기화 스케줄

---

## 마일스톤 7: 테스트 및 배포 (v1.0.0)

### Issue #20: 테스트 코드 작성
**Labels**: `test`, `quality`

- [ ] 단위 테스트 (pytest)
- [ ] API 모킹 테스트
- [ ] 전략 백테스트 검증
- [ ] 통합 테스트

### Issue #21: 배포 및 문서화
**Labels**: `documentation`, `release`

- [ ] README.md 작성
- [ ] API 사용 가이드 문서
- [ ] 전략 개발 가이드
- [ ] Vercel 대시보드 배포
- [ ] GitHub Release 태그

---

## 우선순위 및 의존성

```
[#1: 프로젝트 구조] → [#2: DB 설정] → [#3: API 인증]
                                            ↓
                    [#4: 시세] → [#5: 잔고] → [#6: 주문] → [#7: 거래내역]
                                                              ↓
[#8: 전략 프레임워크] → [#9: 기본 전략] → [#10: 리스크 관리] → [#11: 매매 서비스]
                                                              ↓
                              [#12: Telegram 알림] → [#13: Edge Functions]
                                                              ↓
[#14: 대시보드 설정] → [#15: 핵심 페이지] → [#16: 전략 관리] → [#17: 실시간 모니터링]
                                                              ↓
                                      [#18: CLI] → [#19: 스케줄러]
                                                              ↓
                                      [#20: 테스트] → [#21: 배포/문서화]
```

---

## 기술적 고려사항

### API 인증
- LS증권 Open API는 OAuth 2.0 기반 인증
- APP Key, APP Secret으로 Access Token 발급
- Token 유효시간 관리 필요

### 데이터베이스 전략
- **SQLite**: 로컬 실시간 캐시, 전략 실행 데이터
- **Supabase PostgreSQL**: 영구 저장, 거래 이력, 대시보드 데이터
- **동기화**: 체결 시 즉시, 시세 1분 배치

### 에러 처리
- API 호출 실패 시 재시도 로직 (exponential backoff)
- Rate Limiting 대응
- 네트워크 오류 처리
- 거래 실패 시 알림 발송

### 보안
- 민감 정보는 환경 변수로 관리 (.env)
- API 키는 절대 코드에 하드코딩 금지
- .gitignore에 .env 포함
- Supabase RLS (Row Level Security) 적용

### 자동매매 전략
- 전략 인터페이스 표준화로 확장성 확보
- 백테스팅으로 전략 검증 후 실전 적용
- 리스크 관리 필수 적용 (손절/익절/포지션 사이징)

---

## 기술 스택 상세

| 분류 | 기술 | 용도 |
|-----|------|------|
| **언어** | Python 3.10 | 자동매매 봇 |
| **프레임워크** | FastAPI | 로컬 API 서버 (옵션) |
| **CLI** | Typer | CLI 인터페이스 |
| **스케줄러** | APScheduler | 작업 스케줄링 |
| **로컬 DB** | SQLite + SQLAlchemy | 실시간 캐시 |
| **클라우드 DB** | Supabase (PostgreSQL) | 영구 저장 |
| **프론트엔드** | Next.js 14 | 웹 대시보드 |
| **UI** | shadcn/ui + Tailwind | 컴포넌트 |
| **차트** | Recharts / Lightweight Charts | 시세/수익 차트 |
| **배포** | Vercel | 대시보드 호스팅 |
| **알림** | Telegram Bot API | 실시간 알림 |
| **테스트** | pytest | 단위/통합 테스트 |

---

## 참고 링크

- [LS증권 Open API 공식 문서](https://openapi.ls-sec.co.kr/)
- [LS증권 OpenAPI 샘플 (GitHub)](https://github.com/teranum/ls-openapi-samples)
- [Supabase 공식 문서](https://supabase.com/docs)
- [Next.js 공식 문서](https://nextjs.org/docs)
- [Telegram Bot API](https://core.telegram.org/bots/api)
