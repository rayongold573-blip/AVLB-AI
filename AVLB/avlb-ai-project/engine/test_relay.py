import requests
import time
import random
import base64
import os

# Добавляем инструменты Solana
from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.system_program import transfer
from solders.transaction import Transaction
from solders.message import Message

def run_load_test():
    url = "http://127.0.0.1:8000/send_transaction"
    
    # 1. Загружаем кошелек
    if not os.path.exists("test_keypair.json"):
        print("❌ Error: test_keypair.json not found. Run 'python setup_wallet.py' first!")
        return
    
    with open("test_keypair.json", "rb") as f:
        sender = Keypair.from_bytes(f.read())
    
    # Подключаемся к RPC для получения технической инфы (blockhash)
    solana_client = Client("https://api.devnet.solana.com")

    # Проверка баланса перед стартом
    balance_resp = solana_client.get_balance(sender.pubkey())
    balance = balance_resp.value / 1_000_000_000
    print(f"💰 Wallet Balance: {balance} SOL")
    if balance < 0.001:
        print(f"❌ Error: Insufficient funds! Go to https://faucet.solana.com/ and fund: {sender.pubkey()}")
        return
    
    print("🧪 Starting AVLB Relay Traffic Test...")
    
    # Предварительная проверка доступности сервера
    try:
        requests.get("http://127.0.0.1:8000/", timeout=2)
    except requests.exceptions.ConnectionError:
        print("❌ Error: Relay server is not running! Start 'python relay_server.py' first.")
        return

    for i in range(3): # Сделаем 3 реальных попытки
        try:
            # 2. Создаем реальную транзакцию
            recent_blockhash = solana_client.get_latest_blockhash().value.blockhash
            
            # Инструкция: Перевод 0.001 SOL (1 млн лампортов) самому себе
            ix = transfer({
                "from_pubkey": sender.pubkey(),
                "to_pubkey": sender.pubkey(),
                "lamports": 1_000_000
            })

            # Создаем сообщение и транзакцию через Solders (современный метод)
            msg = Message.new_with_blockhash([ix], sender.pubkey(), recent_blockhash)
            tx = Transaction([sender], msg, recent_blockhash)
            
            tx_b64 = base64.b64encode(bytes(tx)).decode()
            
            payload = {
                "tx_b64": tx_b64,
                "user_id": f"Validator_Hunter_{i}"
            }

            # 3. Отправляем через наш ИИ-Relay
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                print(f"[{i+1}] ✅ Routed! To: {result['routed_to'][:8]}... | Score: {result['score']}")
                print(f"   🔗 Signature: https://explorer.solana.com/tx/{result['signature']}?cluster=devnet")
            else:
                error_detail = response.json().get('detail', 'Unknown error')
                print(f"[{i+1}] ⏳ Server busy: {error_detail}")
        except Exception as e:
            print(f"❌ TX Creation Error: {e}")
        
        time.sleep(3)

if __name__ == "__main__":
    run_load_test()