extends Node

class_name ChaosEventPool

const EVENTS = [
    {
        "id": "api_cold_start",
        "title": "API 冷啟動 (Cold Start)",
        "description": "後端服務休眠中，SLA 每秒流失速度加倍，直到送出一次有效檢索！",
        "effect_type": "sla_drain_boost",
        "duration": 10.0,
        "dialogue": "[系統警告] 偵測到邊緣節點失聯... 正在重新喚醒推理引擎。時間不多了！"
    },
    {
        "id": "db_lock",
        "title": "資料庫鎖定 (Database Deadlock)",
        "description": "寫入衝突導致資料庫鎖定，接下來 3 次檢索必定發生 100% 幻覺（Data Poisoning）。",
        "effect_type": "poison_spike",
        "duration": 0.0,
        "dialogue": "[系統警告] Transaction 死鎖發生！接下來的檢索將會提取到受污染的快取資料！"
    },
    {
        "id": "high_concurrency",
        "title": "高併發風暴 (High Concurrency Storm)",
        "description": "突然湧入大量請求，AP 消耗增加 1 點。",
        "effect_type": "ap_cost_up",
        "duration": 15.0,
        "dialogue": "[系統警告] 流量激增！API Gateway 正在限流，任何操作將消耗額外的算力 (AP)！"
    }
]

static func get_random_event() -> Dictionary:
    var e = EVENTS[randi() % EVENTS.size()]
    return e

static func get_event(event_id: String) -> Dictionary:
    for e in EVENTS:
        if e["id"] == event_id:
            return e
    return EVENTS[0]
