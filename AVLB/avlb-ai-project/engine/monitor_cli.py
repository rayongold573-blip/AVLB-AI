import redis
import json
import time
import os
from datetime import datetime

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def run_monitor():
    print("🚀 Starting AVLB CLI Monitor...")
    while True:
        try:
            clear_screen()
            mode = r.get("avlb:network_mode") or "UNKNOWN"
            print(f"=== AVLB AI SYSTEM MONITOR | {datetime.now().strftime('%H:%M:%S')} ===")
            print(f"STATUS: {mode}")
            print("-" * 60)
            print(f"{'VALIDATOR':<15} | {'SCORE':<8} | {'LATENCY':<10} | {'SYNC'}")
            print("-" * 60)

            keys = r.keys("avlb:validator:*")
            validators = []
            for k in keys:
                v = r.hgetall(k)
                if not v: continue
                metrics = json.loads(v.get('metrics', '{}'))
                validators.append({
                    "pubkey": v.get('pubkey', 'N/A')[:12],
                    "score": float(v.get('score', 0)),
                    "latency": metrics.get('latency_ms', 0),
                    "sync": metrics.get('sync_diff', 0)
                })
            
            # Сортировка по Score
            validators.sort(key=lambda x: x['score'], reverse=True)

            for v in validators:
                color = "✅" if v['score'] > 80 else "⚠️" if v['score'] > 50 else "❌"
                print(f"{color} {v['pubkey']:<12} | {v['score']:<8.2f} | {v['latency']:<8}ms | {v['sync']} slots")

            if not validators:
                print("Wait... AI is warming up (No data in Redis)")
            
            time.sleep(2)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_monitor()