-- 建立一個名為 gemini_logs 的表格來儲存 Gemini CLI 的互動記錄
CREATE TABLE gemini_logs (
    id SERIAL PRIMARY KEY,
    user_input TEXT,
    gemini_response TEXT NOT NULL,
    project_name VARCHAR(255),
    user_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
