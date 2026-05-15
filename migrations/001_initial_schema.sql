-- migrations/001_initial_schema.sql
-- WP-DB-SCHEMA-INIT
-- Created: 2026-05-16
--
-- Establishes core tables for StockHub:
--   stocks   — universe metadata (ASX 200 tickers + later universes)
--   prices   — daily OHLCV time-series, keyed by (ticker, trade_date)
--   signals  — screener output: which ticker fired which signal on which date
--
-- Wrapped in BEGIN/COMMIT for atomicity. Apply once via Supabase SQL Editor.

BEGIN;

-- ───────────────────────────────────────────────
-- stocks  (universe metadata)
-- ───────────────────────────────────────────────
CREATE TABLE stocks (
    ticker        text          PRIMARY KEY,
    name          text          NOT NULL,
    exchange      text          NOT NULL DEFAULT 'ASX',
    sector        text,
    industry      text,
    market_cap    numeric,
    is_active     boolean       NOT NULL DEFAULT true,
    added_at      timestamptz   NOT NULL DEFAULT now(),
    updated_at    timestamptz   NOT NULL DEFAULT now()
);

COMMENT ON TABLE  stocks IS 'Stock universe metadata. ticker uses yfinance format (e.g. BHP.AX for ASX).';
COMMENT ON COLUMN stocks.ticker     IS 'yfinance-style symbol including exchange suffix (e.g. BHP.AX)';
COMMENT ON COLUMN stocks.market_cap IS 'Snapshot at last refresh; will go stale, refresh periodically';
COMMENT ON COLUMN stocks.is_active  IS 'Soft-delete flag for delisted tickers';

CREATE INDEX idx_stocks_exchange_active ON stocks (exchange, is_active);
CREATE INDEX idx_stocks_sector          ON stocks (sector) WHERE sector IS NOT NULL;

-- ───────────────────────────────────────────────
-- prices  (daily OHLCV)
-- ───────────────────────────────────────────────
CREATE TABLE prices (
    ticker        text          NOT NULL REFERENCES stocks(ticker) ON DELETE CASCADE,
    trade_date    date          NOT NULL,
    open          numeric(12,4) NOT NULL,
    high          numeric(12,4) NOT NULL,
    low           numeric(12,4) NOT NULL,
    close         numeric(12,4) NOT NULL,
    adj_close     numeric(12,4) NOT NULL,
    volume        bigint        NOT NULL,
    fetched_at    timestamptz   NOT NULL DEFAULT now(),
    PRIMARY KEY (ticker, trade_date)
);

COMMENT ON TABLE  prices IS 'Daily OHLCV bars. One row per (ticker, trade_date).';
COMMENT ON COLUMN prices.adj_close  IS 'Splits/dividends-adjusted close from yfinance';
COMMENT ON COLUMN prices.fetched_at IS 'When this row was last written from the data feed';

CREATE INDEX idx_prices_ticker_date_desc ON prices (ticker, trade_date DESC);
CREATE INDEX idx_prices_date             ON prices (trade_date DESC);

-- ───────────────────────────────────────────────
-- signals  (screener output)
-- ───────────────────────────────────────────────
CREATE TABLE signals (
    id            bigserial     PRIMARY KEY,
    ticker        text          NOT NULL REFERENCES stocks(ticker) ON DELETE CASCADE,
    signal_type   text          NOT NULL,
    signal_date   date          NOT NULL,
    generated_at  timestamptz   NOT NULL DEFAULT now(),
    payload       jsonb         NOT NULL DEFAULT '{}'::jsonb,
    status        text          NOT NULL DEFAULT 'open'
                                CHECK (status IN ('open','closed','invalidated'))
);

COMMENT ON TABLE  signals IS 'Screener output: which ticker fired which signal on which EOD date.';
COMMENT ON COLUMN signals.signal_type IS 'e.g. rsi_oversold, ma_golden_cross, earnings_surprise_pump';
COMMENT ON COLUMN signals.signal_date IS 'EOD trade_date the signal fired on';
COMMENT ON COLUMN signals.payload     IS 'Signal-specific details: indicator values, thresholds, context';
COMMENT ON COLUMN signals.status      IS 'open=active, closed=position taken/result known, invalidated=voided';

CREATE INDEX idx_signals_date_type   ON signals (signal_date DESC, signal_type);
CREATE INDEX idx_signals_ticker_date ON signals (ticker, signal_date DESC);
CREATE INDEX idx_signals_open        ON signals (signal_date DESC) WHERE status = 'open';

-- ───────────────────────────────────────────────
-- updated_at trigger for stocks
-- ───────────────────────────────────────────────
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER stocks_set_updated_at
    BEFORE UPDATE ON stocks
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

-- ───────────────────────────────────────────────
-- Row Level Security
-- ───────────────────────────────────────────────
-- AMENDMENT 2026-05-16 (WP-DB-SCHEMA-INIT): RLS enabled at apply-time
-- via Supabase SQL Editor "Run and enable RLS" button. No policies
-- defined — access is via service_role key only (which bypasses RLS).
-- When/if we expose any of these tables via anon or authenticated keys,
-- design and apply policies under WP-DB-RLS-POLICIES (banked in
-- _ideas.md). These ALTER statements are added to keep migration file
-- in sync with DB state; they are idempotent and safe to re-run.

ALTER TABLE stocks  ENABLE ROW LEVEL SECURITY;
ALTER TABLE prices  ENABLE ROW LEVEL SECURITY;
ALTER TABLE signals ENABLE ROW LEVEL SECURITY;

COMMIT;

-- ───────────────────────────────────────────────
-- Post-apply verification (run separately after COMMIT):
--   SELECT table_name FROM information_schema.tables
--   WHERE table_schema = 'public' ORDER BY table_name;
-- Expected output (3 rows): prices, signals, stocks
-- ───────────────────────────────────────────────
