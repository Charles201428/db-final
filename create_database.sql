-- Create a new database for market data
-- This file creates the database only
-- Use create_schema.sql to create tables and load initial data

CREATE DATABASE IF NOT EXISTS market_data
    DEFAULT CHARACTER SET = 'utf8mb4'
    DEFAULT COLLATE = 'utf8mb4_unicode_ci';

USE market_data;

