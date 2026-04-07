-- 火车票抢票系统 - 数据库初始化脚本
-- PostgreSQL

-- 创建数据库
CREATE DATABASE ticket_system
    WITH ENCODING = 'UTF8'
    LC_COLLATE = 'zh_CN.UTF-8'
    LC_CTYPE = 'zh_CN.UTF-8'
    TEMPLATE = template0;

-- 连接到数据库
\c ticket_system;

-- 启用 UUID 扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 用户表
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户表索引
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);

-- 12306 账号表
CREATE TABLE railway_accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    username VARCHAR(50) NOT NULL,
    password_encrypted VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_railway_accounts_user_id ON railway_accounts(user_id);

-- 乘车人表
CREATE TABLE passengers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    id_type VARCHAR(20) DEFAULT 'ID_CARD',
    id_number VARCHAR(50) NOT NULL,
    phone VARCHAR(20),
    passenger_type VARCHAR(20) DEFAULT 'ADULT',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_passengers_user_id ON passengers(user_id);
CREATE INDEX idx_passengers_id_number ON passengers(id_number);

-- 车次信息表
CREATE TABLE trains (
    id SERIAL PRIMARY KEY,
    train_no VARCHAR(20) NOT NULL,
    train_code VARCHAR(20) NOT NULL,
    from_station VARCHAR(50) NOT NULL,
    to_station VARCHAR(50) NOT NULL,
    from_time VARCHAR(10),
    to_time VARCHAR(10),
    duration VARCHAR(10),
    distance INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trains_train_no ON trains(train_no);

-- 余票信息表
CREATE TABLE tickets (
    id SERIAL PRIMARY KEY,
    train_no VARCHAR(20) NOT NULL,
    from_station VARCHAR(50) NOT NULL,
    to_station VARCHAR(50) NOT NULL,
    travel_date TIMESTAMP NOT NULL,
    seat_type VARCHAR(20) NOT NULL,
    price FLOAT NOT NULL,
    ticket_count INTEGER DEFAULT 0,
    ticket_status VARCHAR(20) DEFAULT 'AVAILABLE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tickets_train_no ON tickets(train_no);
CREATE INDEX idx_tickets_travel_date ON tickets(travel_date);
CREATE INDEX idx_tickets_route ON tickets(from_station, to_station);

-- 监控任务表
CREATE TABLE monitor_tasks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    train_no VARCHAR(20) NOT NULL,
    from_station VARCHAR(50) NOT NULL,
    to_station VARCHAR(50) NOT NULL,
    travel_date TIMESTAMP NOT NULL,
    seat_types JSONB,
    min_tickets INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    last_check_time TIMESTAMP,
    last_ticket_status VARCHAR(20) DEFAULT 'UNKNOWN',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_monitor_tasks_user_id ON monitor_tasks(user_id);
CREATE INDEX idx_monitor_tasks_train_no ON monitor_tasks(train_no);
CREATE INDEX idx_monitor_tasks_travel_date ON monitor_tasks(travel_date);

-- 监控任务日志表
CREATE TABLE monitor_task_logs (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES monitor_tasks(id) ON DELETE CASCADE,
    check_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ticket_status VARCHAR(20),
    ticket_count INTEGER,
    action_taken VARCHAR(50),
    message TEXT
);

CREATE INDEX idx_monitor_task_logs_task_id ON monitor_task_logs(task_id);
CREATE INDEX idx_monitor_task_logs_check_time ON monitor_task_logs(check_time);

-- 订单表
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    order_no VARCHAR(50) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    railway_account_id INTEGER NOT NULL REFERENCES railway_accounts(id),
    train_no VARCHAR(20) NOT NULL,
    from_station VARCHAR(50) NOT NULL,
    to_station VARCHAR(50) NOT NULL,
    travel_date TIMESTAMP NOT NULL,
    seat_type VARCHAR(20) NOT NULL,
    price FLOAT NOT NULL,
    passengers JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING',
    payment_status VARCHAR(20) DEFAULT 'UNPAID',
    railway_order_no VARCHAR(50),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    paid_at TIMESTAMP,
    cancelled_at TIMESTAMP
);

CREATE INDEX idx_orders_order_no ON orders(order_no);
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_travel_date ON orders(travel_date);

-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为需要自动更新 updated_at 的表添加触发器
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_trains_updated_at BEFORE UPDATE ON trains
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tickets_updated_at BEFORE UPDATE ON tickets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_monitor_tasks_updated_at BEFORE UPDATE ON monitor_tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 插入测试数据（可选）
-- INSERT INTO users (username, email, password_hash) VALUES
--     ('testuser', 'test@example.com', '$2b$12$...');

COMMENT ON TABLE users IS '用户表';
COMMENT ON TABLE railway_accounts IS '12306 账号表';
COMMENT ON TABLE passengers IS '乘车人表';
COMMENT ON TABLE trains IS '车次信息表';
COMMENT ON TABLE tickets IS '余票信息表';
COMMENT ON TABLE monitor_tasks IS '监控任务表';
COMMENT ON TABLE monitor_task_logs IS '监控任务日志表';
COMMENT ON TABLE orders IS '订单表';
