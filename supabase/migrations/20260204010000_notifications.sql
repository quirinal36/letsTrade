-- letsTrade 알림 시스템
-- Notifications table and Edge Function triggers

-- =============================================
-- 1. notifications 테이블 (알림 저장)
-- =============================================
CREATE TABLE IF NOT EXISTS notifications (
    id BIGSERIAL PRIMARY KEY,

    -- 알림 유형
    type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,

    -- 심각도
    severity VARCHAR(20) DEFAULT 'info'
        CHECK (severity IN ('info', 'warning', 'critical')),

    -- 추가 데이터
    data JSONB,

    -- 읽음 상태
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMPTZ,

    -- 타임스탬프
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(type);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);

-- RLS 설정
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role full access on notifications" ON notifications FOR ALL USING (true);


-- =============================================
-- 2. Database Trigger Function for Trade Notifications
-- =============================================
CREATE OR REPLACE FUNCTION notify_trade_changes()
RETURNS TRIGGER AS $$
DECLARE
    payload JSONB;
BEGIN
    -- Build payload
    payload = jsonb_build_object(
        'type', TG_OP,
        'table', TG_TABLE_NAME,
        'schema', TG_TABLE_SCHEMA,
        'record', row_to_json(NEW),
        'old_record', CASE WHEN TG_OP = 'UPDATE' THEN row_to_json(OLD) ELSE NULL END
    );

    -- Send to Realtime channel (for immediate client updates)
    PERFORM pg_notify('trade_changes', payload::text);

    -- For executed trades, create a notification record
    IF TG_OP = 'UPDATE' AND OLD.status != 'executed' AND NEW.status = 'executed' THEN
        INSERT INTO notifications (type, title, message, data, created_at)
        VALUES (
            'trade_executed',
            CASE WHEN NEW.order_type = 'buy' THEN '매수 체결' ELSE '매도 체결' END,
            NEW.stock_name || ' ' ||
            CASE WHEN NEW.order_type = 'buy' THEN '매수' ELSE '매도' END || ' ' ||
            NEW.executed_quantity || '주 @ ₩' || NEW.executed_price,
            jsonb_build_object(
                'trade_id', NEW.id,
                'stock_code', NEW.stock_code,
                'order_type', NEW.order_type
            ),
            NOW()
        );
    END IF;

    -- For new trades, create a notification record
    IF TG_OP = 'INSERT' THEN
        INSERT INTO notifications (type, title, message, data, created_at)
        VALUES (
            'trade_new',
            CASE WHEN NEW.order_type = 'buy' THEN '매수 주문' ELSE '매도 주문' END,
            NEW.stock_name || ' ' ||
            CASE WHEN NEW.order_type = 'buy' THEN '매수' ELSE '매도' END || ' ' ||
            NEW.quantity || '주 @ ₩' || NEW.price,
            jsonb_build_object(
                'trade_id', NEW.id,
                'stock_code', NEW.stock_code,
                'order_type', NEW.order_type
            ),
            NOW()
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger on trades table
DROP TRIGGER IF EXISTS trigger_notify_trade_changes ON trades;
CREATE TRIGGER trigger_notify_trade_changes
    AFTER INSERT OR UPDATE ON trades
    FOR EACH ROW
    EXECUTE FUNCTION notify_trade_changes();


-- =============================================
-- 3. Portfolio Alert Trigger (Stop-loss / Take-profit)
-- =============================================
CREATE OR REPLACE FUNCTION check_portfolio_alerts()
RETURNS TRIGGER AS $$
DECLARE
    loss_threshold NUMERIC := 5.0;  -- Default 5% loss threshold
    profit_threshold NUMERIC := 10.0;  -- Default 10% profit threshold
BEGIN
    -- Check for stop-loss condition
    IF NEW.profit_loss_rate <= -loss_threshold THEN
        INSERT INTO notifications (type, title, message, severity, data, created_at)
        VALUES (
            'stop_loss',
            '손절선 도달 경고',
            NEW.stock_name || ' 손실률 ' || ROUND(ABS(NEW.profit_loss_rate)::NUMERIC, 2) || '% - 손절 검토 필요',
            'critical',
            jsonb_build_object(
                'portfolio_id', NEW.id,
                'stock_code', NEW.stock_code,
                'profit_loss_rate', NEW.profit_loss_rate,
                'current_price', NEW.current_price,
                'avg_price', NEW.avg_price
            ),
            NOW()
        );
    END IF;

    -- Check for take-profit condition
    IF NEW.profit_loss_rate >= profit_threshold THEN
        INSERT INTO notifications (type, title, message, severity, data, created_at)
        VALUES (
            'take_profit',
            '익절선 도달',
            NEW.stock_name || ' 수익률 ' || ROUND(NEW.profit_loss_rate::NUMERIC, 2) || '% - 익절 검토',
            'info',
            jsonb_build_object(
                'portfolio_id', NEW.id,
                'stock_code', NEW.stock_code,
                'profit_loss_rate', NEW.profit_loss_rate,
                'current_price', NEW.current_price,
                'avg_price', NEW.avg_price
            ),
            NOW()
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger on portfolio table
DROP TRIGGER IF EXISTS trigger_check_portfolio_alerts ON portfolio;
CREATE TRIGGER trigger_check_portfolio_alerts
    AFTER UPDATE ON portfolio
    FOR EACH ROW
    WHEN (OLD.profit_loss_rate IS DISTINCT FROM NEW.profit_loss_rate)
    EXECUTE FUNCTION check_portfolio_alerts();


-- =============================================
-- 4. Enable Realtime for notifications table
-- =============================================
ALTER PUBLICATION supabase_realtime ADD TABLE notifications;
