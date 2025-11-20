-- ============================================
-- Market Data System - Database Schema
-- ============================================

-- Create database (if not exists)
CREATE DATABASE IF NOT EXISTS market_data
    DEFAULT CHARACTER SET = 'utf8mb4'
    DEFAULT COLLATE = 'utf8mb4_unicode_ci';

USE market_data;

-- ============================================
-- TABLE: AssetType
-- ============================================
CREATE TABLE AssetType (
    asset_type_id   INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(20) NOT NULL UNIQUE,
    description     VARCHAR(255) NULL
);

-- ============================================
-- TABLE: Asset
-- ============================================
CREATE TABLE Asset (
    asset_id        INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(50) NOT NULL,
    symbol          VARCHAR(20) NOT NULL,
    asset_type_id   INT NOT NULL,
    base_currency   CHAR(3) NOT NULL DEFAULT 'USD',
    FOREIGN KEY (asset_type_id) REFERENCES AssetType(asset_type_id)
);

-- ============================================
-- TABLE: DailyMarketData
-- ============================================
CREATE TABLE DailyMarketData (
    asset_id    INT NOT NULL,
    obs_date    DATE NOT NULL,
    price       DECIMAL(18,4) NOT NULL,
    volume      BIGINT NULL,
    PRIMARY KEY (asset_id, obs_date),
    FOREIGN KEY (asset_id) REFERENCES Asset(asset_id),
    CHECK (price > 0),
    CHECK (volume IS NULL OR volume >= 0)
);

-- ============================================
-- Insert AssetType data
-- ============================================
INSERT INTO AssetType (asset_type_id, name, description) VALUES
(1, 'COMMODITY', 'Physical commodities such as natural gas, crude oil, and metals'),
(2, 'CRYPTO', 'Cryptocurrencies such as Bitcoin and Ethereum'),
(3, 'INDEX', 'Equity indices such as S&P 500 and Nasdaq 100'),
(4, 'EQUITY', 'Individual company stocks such as Apple, Tesla, Microsoft, etc.');

-- ============================================
-- Insert Asset data
-- ============================================
INSERT INTO Asset (asset_id, name, symbol, asset_type_id, base_currency) VALUES
(1, 'Natural Gas', 'NATGAS', 1, 'USD'),
(2, 'Crude Oil', 'CRUDE', 1, 'USD'),
(3, 'Copper', 'COPPER', 1, 'USD'),
(4, 'Bitcoin', 'BTC', 2, 'USD'),
(5, 'Ethereum', 'ETH', 2, 'USD'),
(6, 'S&P 500', 'SP500', 3, 'USD'),
(7, 'Nasdaq 100', 'NDX100', 3, 'USD'),
(8, 'Apple Inc.', 'AAPL', 4, 'USD'),
(9, 'Tesla Inc.', 'TSLA', 4, 'USD'),
(10, 'Microsoft Corp.', 'MSFT', 4, 'USD'),
(11, 'Alphabet Inc.', 'GOOGL', 4, 'USD'),
(12, 'Nvidia Corp.', 'NVDA', 4, 'USD'),
(13, 'Berkshire Hathaway', 'BRK.B', 4, 'USD'),
(14, 'Netflix Inc.', 'NFLX', 4, 'USD'),
(15, 'Amazon.com Inc.', 'AMZN', 4, 'USD'),
(16, 'Meta Platforms', 'META', 4, 'USD'),
(17, 'Gold', 'GOLD', 1, 'USD'),
(18, 'Silver', 'SILVER', 1, 'USD'),
(19, 'Platinum', 'PLAT', 1, 'USD');

