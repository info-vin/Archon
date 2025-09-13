-- 啟用 UUID 生成功能，如果尚未啟用
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 建立 customers (客戶) 資料表
CREATE TABLE customers (
    -- 使用 UUID 作為每個客戶的唯一標識符
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 客戶或公司的名稱，不允許為空
    name TEXT NOT NULL,

    -- 客戶的聯絡電子郵件
    email TEXT,

    -- 記錄建立時的時間戳，預設為當前時間
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 建立 vendors (供應商) 資料表
CREATE TABLE vendors (
    -- 使用 UUID 作為每個供應商的唯一標識符
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 供應商或公司的名稱，不允許為空
    name TEXT NOT NULL,

    -- 供應商提供的服務類型
    service_type TEXT,

    -- 記錄建立時的時間戳，預設為當前時間
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 為新的資料表和欄位加上註解，增加可讀性
COMMENT ON TABLE customers IS '儲存客戶資訊。';
COMMENT ON COLUMN customers.name IS '客戶的完整名稱或公司名稱。';
COMMENT ON COLUMN customers.email IS '客戶的主要聯絡電子郵件。';

COMMENT ON TABLE vendors IS '儲存供應商和合作夥伴資訊。';
COMMENT ON COLUMN vendors.name IS '供應商的完整名稱或公司名稱。';
COMMENT ON COLUMN vendors.service_type IS '供應商提供的服務類別（例如："Software", "Consulting"）。';
