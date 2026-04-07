import redis
import json
import pandas as pd
from datetime import datetime

def export_history_to_csv():
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    keys = r.keys("avlb:history:*")
    
    all_records = []
    print(f"🔎 Найдено валидаторов с историей: {len(keys)}")

    for k in keys:
        pubkey = k.split(":")[-1]
        # Получаем все записи из списка
        history = r.lrange(k, 0, -1)
        
        for entry in history:
            data = json.loads(entry)
            record = {
                "timestamp": datetime.fromtimestamp(data['ts']),
                "pubkey": pubkey,
                "score": data['score'],
                "latency": data['metrics'].get('latency_ms'),
                "sync_diff": data['metrics'].get('sync_diff'),
                "success_rate": data['metrics'].get('success_rate')
            }
            all_records.append(record)

    if all_records:
        df = pd.DataFrame(all_records)
        filename = f"validator_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        print(f"✅ Данные экспортированы в {filename}")
        print(f"📊 Всего записей: {len(df)}")
    else:
        print("❌ Истории пока нет. Подождите, пока collector.py соберет данные.")

if __name__ == "__main__":
    export_history_to_csv()