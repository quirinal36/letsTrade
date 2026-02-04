# AI 기반 전략 작성 기능

## 개요

Claude API를 활용하여 사용자가 AI와 대화하면서 매매 전략을 작성할 수 있는 기능을 `/strategies` 페이지에 추가합니다.

## 목표

- 사용자가 자연어로 매매 전략을 설명하면 AI가 구조화된 전략으로 변환
- 대화형 인터페이스를 통한 전략 세부 조정
- 생성된 전략을 Supabase에 저장하여 봇에서 실행 가능

## 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                     Dashboard (Next.js)                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │             /strategies/new (AI Chat UI)                  │   │
│  │  ┌────────────────┐  ┌─────────────────────────────────┐ │   │
│  │  │  Chat Messages │  │    Strategy Preview Panel       │ │   │
│  │  │  - User input  │  │    - 실시간 전략 미리보기        │ │   │
│  │  │  - AI response │  │    - 파라미터 표시               │ │   │
│  │  └────────────────┘  └─────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   API Route (/api/chat/strategy)                 │
│  - Claude API 호출                                               │
│  - 전략 JSON 생성                                                │
│  - 스트리밍 응답                                                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Claude API                                │
│  - 시스템 프롬프트: 전략 생성 전문가                             │
│  - Tool Use: strategy_create, strategy_modify                   │
└─────────────────────────────────────────────────────────────────┘
```

## 구현 계획

### Phase 1: 백엔드 API 구축

#### 1.1 Claude API 연동 설정
- [ ] `@anthropic-ai/sdk` 패키지 설치
- [ ] 환경 변수 설정 (`ANTHROPIC_API_KEY`)
- [ ] API 클라이언트 유틸리티 생성

#### 1.2 전략 생성 API Route
- [ ] `/api/chat/strategy` POST 엔드포인트 생성
- [ ] 스트리밍 응답 구현 (Vercel AI SDK 활용)
- [ ] 시스템 프롬프트 설계 (전략 생성 전문가)

#### 1.3 Tool Use 정의
```typescript
// 전략 생성 Tool
{
  name: "create_strategy",
  description: "새로운 매매 전략을 생성합니다",
  input_schema: {
    type: "object",
    properties: {
      name: { type: "string", description: "전략 이름" },
      description: { type: "string", description: "전략 설명" },
      strategy_type: {
        type: "string",
        enum: ["ma_crossover", "rsi_oversold", "bollinger_bands", "macd", "custom"],
        description: "전략 유형"
      },
      parameters: {
        type: "object",
        description: "전략별 파라미터 (예: 이동평균 기간)"
      },
      stock_codes: { type: "string", description: "대상 종목 코드 (콤마 구분)" },
      max_investment: { type: "number", description: "최대 투자금액" },
      max_loss_rate: { type: "number", description: "손절선 (%)" },
      take_profit_rate: { type: "number", description: "익절선 (%)" },
    },
    required: ["name", "strategy_type"]
  }
}
```

### Phase 2: 프론트엔드 UI 구현

#### 2.1 전략 생성 페이지
- [ ] `/strategies/new` 페이지 생성
- [ ] 채팅 인터페이스 컴포넌트
- [ ] 전략 미리보기 패널
- [ ] 메시지 히스토리 관리

#### 2.2 채팅 컴포넌트
```
┌─────────────────────────────────────────────────────────┐
│  AI 전략 어시스턴트                              [닫기] │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  🤖 안녕하세요! 어떤 매매 전략을 만들고 싶으신가요?     │
│                                                         │
│  💡 예시:                                               │
│  - "RSI가 30 이하일 때 매수하는 전략"                   │
│  - "5일선이 20일선을 상향 돌파할 때 매수"               │
│  - "삼성전자에 100만원 한도로 투자하는 전략"            │
│                                                         │
│  ─────────────────────────────────────────────────────  │
│  👤 RSI 30 이하에서 매수하고 70 이상에서 매도하는       │
│     전략을 만들어줘. 손절은 -5%, 익절은 +10%로.         │
│                                                         │
│  🤖 RSI 기반 전략을 생성했습니다:                       │
│     [전략 카드 미리보기]                                │
│     - 매수 조건: RSI ≤ 30                               │
│     - 매도 조건: RSI ≥ 70                               │
│     - 손절: -5%, 익절: +10%                             │
│                                                         │
│     이 전략을 저장할까요?                               │
│     [저장하기] [수정하기]                               │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  [메시지를 입력하세요...]                      [전송 ▶] │
└─────────────────────────────────────────────────────────┘
```

#### 2.3 전략 미리보기 패널
- [ ] 실시간 전략 JSON 표시
- [ ] 파라미터 시각화
- [ ] 리스크 설정 표시
- [ ] 저장/수정 버튼

### Phase 3: 전략 저장 및 관리

#### 3.1 전략 저장 API
- [ ] `/api/strategies` POST 엔드포인트
- [ ] Supabase `strategies` 테이블에 저장
- [ ] 유효성 검증

#### 3.2 전략 수정 기능
- [ ] 기존 전략 불러오기
- [ ] AI와 대화하며 수정
- [ ] 버전 히스토리 (옵션)

### Phase 4: 고급 기능

#### 4.1 전략 템플릿
- [ ] 미리 정의된 전략 템플릿 제공
- [ ] "RSI 과매도 전략" 템플릿
- [ ] "이동평균 교차 전략" 템플릿
- [ ] "볼린저밴드 전략" 템플릿

#### 4.2 백테스트 연동
- [ ] 생성된 전략 즉시 백테스트
- [ ] 결과 시각화
- [ ] AI 피드백 제공

## 파일 구조

```
dashboard/src/
├── app/
│   ├── api/
│   │   └── chat/
│   │       └── strategy/
│   │           └── route.ts          # Claude API 연동
│   └── dashboard/
│       └── strategies/
│           ├── page.tsx              # 전략 목록 (기존)
│           ├── new/
│           │   └── page.tsx          # AI 전략 생성 페이지
│           └── [id]/
│               ├── page.tsx          # 전략 상세 (기존)
│               └── edit/
│                   └── page.tsx      # AI 전략 수정 페이지
├── components/
│   └── strategy/
│       ├── chat-interface.tsx        # 채팅 UI
│       ├── strategy-preview.tsx      # 전략 미리보기
│       ├── message-bubble.tsx        # 메시지 컴포넌트
│       └── strategy-card-preview.tsx # 전략 카드 미리보기
└── lib/
    └── ai/
        ├── claude-client.ts          # Claude API 클라이언트
        ├── strategy-prompts.ts       # 시스템 프롬프트
        └── strategy-tools.ts         # Tool 정의
```

## 시스템 프롬프트 설계

```typescript
const STRATEGY_ASSISTANT_PROMPT = `
당신은 주식 자동매매 전략 생성을 돕는 AI 어시스턴트입니다.

## 역할
- 사용자의 자연어 설명을 구조화된 매매 전략으로 변환
- 전략의 장단점 설명
- 리스크 관리 조언 제공

## 지원하는 전략 유형
1. ma_crossover: 이동평균선 교차 전략
2. rsi_oversold: RSI 과매도/과매수 전략
3. bollinger_bands: 볼린저밴드 전략
4. macd: MACD 전략
5. custom: 사용자 정의 전략

## 응답 규칙
1. 전략 생성 시 반드시 create_strategy 도구 사용
2. 손절/익절 미설정 시 권장값 제안
3. 투자금 미설정 시 확인 요청
4. 한국어로 친근하게 응답

## 예시 대화
사용자: "5일선이 20일선을 돌파하면 매수하는 전략 만들어줘"
응답: 이동평균 교차 전략을 생성하겠습니다.
[create_strategy 도구 호출]
추가로 손절선과 익절선을 설정하시겠어요?
권장: 손절 -5%, 익절 +10%
`;
```

## 데이터베이스 스키마

기존 `strategies` 테이블 활용:

```sql
-- 이미 존재하는 테이블
CREATE TABLE strategies (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    strategy_type VARCHAR(50) NOT NULL,
    stock_codes TEXT,
    parameters JSONB,
    max_investment BIGINT,
    max_loss_rate NUMERIC(5,2),
    take_profit_rate NUMERIC(5,2),
    is_active BOOLEAN DEFAULT FALSE,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- AI 대화 히스토리 (옵션)
CREATE TABLE strategy_chat_history (
    id BIGSERIAL PRIMARY KEY,
    strategy_id BIGINT REFERENCES strategies(id),
    messages JSONB NOT NULL,  -- [{role, content}]
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## 환경 변수

```env
# Claude API
ANTHROPIC_API_KEY=sk-ant-...

# 기존 Supabase 설정
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
```

## 예상 일정

| 단계 | 작업 | 예상 |
|------|------|------|
| Phase 1 | 백엔드 API 구축 | - |
| Phase 2 | 프론트엔드 UI | - |
| Phase 3 | 저장/관리 기능 | - |
| Phase 4 | 고급 기능 | - |

## 기술 스택

| 분류 | 기술 | 용도 |
|------|------|------|
| AI | Claude API (claude-sonnet-4-20250514) | 전략 생성 |
| 스트리밍 | Vercel AI SDK | 실시간 응답 |
| UI | shadcn/ui | 채팅 인터페이스 |
| 상태관리 | React hooks | 메시지 히스토리 |

## 참고

- [Anthropic API 문서](https://docs.anthropic.com)
- [Vercel AI SDK](https://sdk.vercel.ai/docs)
- [기존 전략 관리 페이지](/dashboard/strategies)
