import time
import random
import sys
import os
from datetime import datetime

try:
    from solana.rpc.api import Client
except ImportError:
    print("Ошибка: Библиотека 'solana' не установлена. Выполните: pip install solana")
    sys.exit(1)

from scorer import ValidatorScorer, NetworkMode
from storage import MetricsStorage

scorer = ValidatorScorer()
# Подключаем обученную модель, если она существует
model_path = "validator_model.pkl"
if os.path.exists(model_path):
    scorer.load_ml_model(model_path)
storage = MetricsStorage()

def run_collector():
    # Подключаемся к Solana Devnet RPC
    rpc_url = "https://api.devnet.solana.com"
    client = Client(rpc_url)
    print("AVLB AI: Сборщик метрик запущен на Solana Devnet...")
    
    if not storage.client:
        print("❌ Ошибка: Нет подключения к Redis. Пожалуйста, запустите Memurai/Redis.")
        return

    while True:
        try:
            # Получаем текущий слот сети
            slot_resp = client.get_slot()
            if not slot_resp or slot_resp.value is None:
                print("Ошибка: Не удалось получить текущий слот от RPC.")
                time.sleep(5)
                continue
            
            current_slot = slot_resp.value
            response = client.get_vote_accounts()
            
            # Проверка, что ответ от Solana корректен
            if not response or response.value is None:
                print("Ошибка: Получен некорректный ответ от Solana RPC (VoteAccounts).")
                time.sleep(10)
                continue
                
            validators = response.value.current
            
            # --- ДИНАМИЧЕСКОЕ ОПРЕДЕЛЕНИЕ РЕЖИМА СЕТИ ---
            # Считаем среднее отставание (sync_diff) первых 10 валидаторов
            sample_validators = validators[:10]
            
            sync_values = [max(0, current_slot - v.last_vote) for v in sample_validators]
            avg_sync = sum(sync_values) / len(sync_values) if sync_values else 0
            
            if avg_sync > 50:
                current_mode = NetworkMode.CRITICAL
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚨 CRITICAL: High network lag ({avg_sync:.1f})")
            elif avg_sync > 15:
                current_mode = NetworkMode.HIGH_LOAD
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 📢 HIGH LOAD: Medium network lag ({avg_sync:.1f})")
            else:
                current_mode = NetworkMode.NORMAL
                # Печатаем статус здоровья только раз в минуту
                if int(time.time()) % 60 < 10:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ NORMAL: Network is healthy")
            
            storage.set_network_mode(current_mode.value)
            
            # Берем первые 5 для теста, чтобы не спамить Redis
            for validator in validators[:5]:
                pubkey = str(validator.vote_pubkey)
                v_sync_diff = max(0, current_slot - validator.last_vote)
                
                # Имитация реальной задержки: база + шум + штраф за рассинхрон
                simulated_latency = 100 + random.randint(0, 50) + (v_sync_diff * 2)
                
                metrics = {
                    "success_rate": 100.0, # Упрощенно для MVP
                    "load_percent": 25,
                    "latency_ms": simulated_latency,
                    "sync_diff": v_sync_diff,
                    "priority_fee": 5000
                }
                score = scorer.calculate_score(metrics, current_mode)
                storage.save_validator_stats(pubkey, score, metrics, current_mode.value)
                ai_label = "🧠" if scorer.model else "⚙️"
                print(f"[{current_mode.value}] {ai_label} {pubkey[:8]}... | Score: {score} | Sync: {v_sync_diff}")
        except Exception as e:
            print(f"Ошибка при сборе данных: {e}")
            
        time.sleep(10)

if __name__ == "__main__":
    run_collector()
