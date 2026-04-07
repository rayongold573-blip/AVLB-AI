import redis
import json
import time

class MetricsStorage:
    def __init__(self, host='localhost', port=6379):
        try:
            self.client = redis.Redis(host=host, port=port, decode_responses=True)
            # Простая проверка связи
            self.client.ping()
        except redis.exceptions.ConnectionError:
            print(f"Критическая ошибка: Не удалось подключиться к Redis (Memurai) на {host}:{port}")
            print("Убедитесь, что служба Memurai запущена.")
            self.client = None

    def save_validator_stats(self, pubkey: str, score: float, metrics: dict, mode: str):
        if self.client is None:
            return
        key = f"avlb:validator:{pubkey}"
        history_key = f"avlb:history:{pubkey}"
        
        self.client.hset(key, mapping={
            "pubkey": pubkey,
            "score": score,
            "mode": mode,
            "metrics": json.dumps(metrics),
            "last_update": int(time.time())
        })
        self.client.expire(key, 60) # Срок жизни данных - 1 минута

        # Накопление истории для обучения ИИ (последние 100 записей)
        history_entry = json.dumps({"score": score, "ts": int(time.time()), "metrics": metrics})
        try:
            self.client.lpush(history_key, history_entry)
            self.client.ltrim(history_key, 0, 99) # Ограничиваем размер истории
        except:
            pass

    def set_network_mode(self, mode: str):
        """Устанавливает глобальный режим сети для отображения на дашборде."""
        if self.client:
            self.client.set("avlb:network_mode", mode)

    def get_top_validators(self, n: int = 3):
        """
        Возвращает список из N лучших валидаторов (pubkey, score).
        Используется для обеспечения отказоустойчивости (failover).
        """
        if not self.client: return []
        keys = self.client.keys("avlb:validator:*")
        validators = []

        for k in keys:
            v = self.client.hgetall(k)
            validators.append((v.get('pubkey'), float(v.get('score', 0))))
        
        # Сортируем по баллу (score) в порядке убывания
        validators.sort(key=lambda x: x[1], reverse=True)
        return validators[:n]

    def get_best_validator(self):
        """Совместимость: возвращает одного лучшего валидатора."""
        tops = self.get_top_validators(1)
        return tops[0] if tops else (None, 0)
