-- letsTrade 초기 스키마
-- Supabase에서 실행

-- =============================================
-- 1. trades 테이블 (거래 내역)
-- =============================================
CREATE TABLE IF NOT EXISTS trades (
    id BIGSERIAL PRIMARY KEY,

    -- 주문 정보
    order_no VARCHAR(50) UNIQUE NOT NULL,
    stock_code VARCHAR(20) NOT NULL,
    stock_name VARCHAR(100) NOT NULL,

    -- 주문 유형 및 상태
    order_type VARCHAR(10) NOT NULL CHECK (order_type IN ('buy', 'sell')),
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'executed', 'partial', 'cancelled', 'rejected')),

    -- 수량 및 가격
    quantity INTEGER NOT NULL,
    price NUMERIC(15, 2) NOT NULL,
    executed_quantity INTEGER DEFAULT 0,
    executed_price NUMERIC(15, 2),

    -- 전략 정보
    strategy_id BIGINT,
    signal_id BIGINT,

    -- 추가 정보
    notes TEXT,
    executed_at TIMESTAMPTZ,

    -- 타임스탬프
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_trades_stock_code ON trades(stock_code);
CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status);
CREATE INDEX IF NOT EXISTS idx_trades_created_at ON trades(created_at DESC);


-- =============================================
-- 2. portfolio 테이블 (포트폴리오)
-- =============================================
CREATE TABLE IF NOT EXISTS portfolio (
    id BIGSERIAL PRIMARY KEY,

    -- 종목 정보
    stock_code VARCHAR(20) UNIQUE NOT NULL,
    stock_name VARCHAR(100) NOT NULL,

    -- 보유 수량 및 금액
    quantity INTEGER NOT NULL DEFAULT 0,
    avg_price NUMERIC(15, 2) NOT NULL,
    current_price NUMERIC(15, 2) NOT NULL,

    -- 손익 정보
    total_cost NUMERIC(18, 2) NOT NULL,
    market_value NUMERIC(18, 2) NOT NULL,
    profit_loss NUMERIC(18, 2) NOT NULL DEFAULT 0,
    profit_loss_rate NUMERIC(8, 4) NOT NULL DEFAULT 0,

    -- 타임스탬프
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_portfolio_stock_code ON portfolio(stock_code);


-- =============================================
-- 3. strategies 테이블 (전략 설정)
-- =============================================
CREATE TABLE IF NOT EXISTS strategies (
    id BIGSERIAL PRIMARY KEY,

    -- 전략 기본 정보
    name VARCHAR(100) NOT NULL,
    description TEXT,
    strategy_type VARCHAR(50) NOT NULL,

    -- 대상 종목
    stock_codes TEXT,

    -- 전략 파라미터 (JSON)
    parameters JSONB,

    -- 리스크 관리
    max_investment INTEGER,
    max_loss_rate INTEGER,
    take_profit_rate INTEGER,

    -- 상태
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 0,

    -- 타임스탬프
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_strategies_is_active ON strategies(is_active);
CREATE INDEX IF NOT EXISTS idx_strategies_type ON strategies(strategy_type);


-- =============================================
-- 4. signals 테이블 (시그널 로그)
-- =============================================
CREATE TABLE IF NOT EXISTS signals (
    id BIGSERIAL PRIMARY KEY,

    -- 전략 연결
    strategy_id BIGINT NOT NULL,

    -- 종목 정보
    stock_code VARCHAR(20) NOT NULL,
    stock_name VARCHAR(100) NOT NULL,

    -- 시그널 정보
    signal_type VARCHAR(10) NOT NULL CHECK (signal_type IN ('buy', 'sell', 'hold')),
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'executed', 'ignored', 'expired')),

    -- 추천 가격/수량
    price NUMERIC(15, 2) NOT NULL,
    quantity INTEGER,

    -- 시그널 강도 및 신뢰도
    strength NUMERIC(5, 2) DEFAULT 0,
    confidence NUMERIC(5, 2) DEFAULT 0,

    -- 분석 데이터
    analysis_data JSONB,

    -- 실행 정보
    trade_id BIGINT,
    executed_at TIMESTAMPTZ,

    -- 메모
    reason TEXT,

    -- 타임스탬프
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_signals_strategy_id ON signals(strategy_id);
CREATE INDEX IF NOT EXISTS idx_signals_stock_code ON signals(stock_code);
CREATE INDEX IF NOT EXISTS idx_signals_status ON signals(status);
CREATE INDEX IF NOT EXISTS idx_signals_created_at ON signals(created_at DESC);


-- =============================================
-- 5. updated_at 자동 업데이트 트리거
-- =============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 각 테이블에 트리거 적용
CREATE TRIGGER update_trades_updated_at
    BEFORE UPDATE ON trades
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_portfolio_updated_at
    BEFORE UPDATE ON portfolio
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_strategies_updated_at
    BEFORE UPDATE ON strategies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_signals_updated_at
    BEFORE UPDATE ON signals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- =============================================
-- 6. RLS (Row Level Security) 설정
-- =============================================
ALTER TABLE trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE portfolio ENABLE ROW LEVEL SECURITY;
ALTER TABLE strategies ENABLE ROW LEVEL SECURITY;
ALTER TABLE signals ENABLE ROW LEVEL SECURITY;

-- service_role은 모든 접근 허용
CREATE POLICY "Service role full access on trades" ON trades FOR ALL USING (true);
CREATE POLICY "Service role full access on portfolio" ON portfolio FOR ALL USING (true);
CREATE POLICY "Service role full access on strategies" ON strategies FOR ALL USING (true);
CREATE POLICY "Service role full access on signals" ON signals FOR ALL USING (true);
