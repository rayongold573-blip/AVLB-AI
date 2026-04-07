import time
import os
import asyncio
import json
from storage import MetricsStorage
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TxOpts
from solders.keypair import Keypair
from solders.instruction import Instruction, AccountMeta
from solders.message import Message
from solders.transaction import Transaction
from solders.pubkey import Pubkey

storage = MetricsStorage()

async def bridge_ai_to_blockchain():
    print("🚀 AVLB AI Bridge: Интегратор запущен...")

    if not os.path.exists("test_keypair.json"):
        print("❌ Ошибка: test_keypair.json не найден. Сначала запустите setup_wallet.py")
        return

    with open("test_keypair.json", "rb") as f:
        keypair = Keypair.from_bytes(f.read())

    # Используем альтернативный эндпоинт, если основной сбоит
    client = AsyncClient("https://api.devnet.solana.com") 
    # Используем официальный ID Memo Program v2 — он более надежен в Devnet
    memo_program_id = Pubkey.from_string("MemoSq6KCqU963S72kGo55MvXyN86JjK57KToB6xG9f")
    
    while True:
        # 1. Достаем лидера из нашего ИИ-рейтинга
        best_v = storage.get_best_validator()
        
        if best_v and best_v[0]:
            pubkey, score = best_v
            try:
                # Проверяем баланс перед отправкой
                balance_resp = await client.get_balance(keypair.pubkey())
                balance_sol = balance_resp.value / 10**9
                print(f"\n[ON-CHAIN] 🤖 AI Leader: {pubkey[:10]}... Score: {score}")
                print(f"[WALLET] 💰 Balance: {balance_sol:.4f} SOL")
                
                if balance_sol < 0.005:
                    print("⚠️ Мало SOL на балансе! Рекомендуется пополнить через python setup_wallet.py")

                # Формируем данные для записи (рейтинг)
                memo_data = json.dumps({
                    "app": "AVLB_AI",
                    "best_validator": pubkey,
                    "ai_score": score
                }).encode()

                # Добавляем подписанта в метаданные, чтобы RPC-узел не отклонил транзакцию
                ix = Instruction(
                    memo_program_id, 
                    memo_data, 
                    [AccountMeta(pubkey=keypair.pubkey(), is_signer=True, is_writable=False)]
                )
                
                # Получаем свежий блокхэш и отправляем транзакцию
                recent_blockhash = (await client.get_latest_blockhash()).value.blockhash
                msg = Message.new_with_blockhash([ix], keypair.pubkey(), recent_blockhash)
                tx = Transaction([keypair], msg, recent_blockhash)
                
                # Увеличиваем шансы на успех: используем TxOpts для обхода симуляции
                res = await client.send_raw_transaction(bytes(tx), opts=TxOpts(skip_preflight=True))
                if res.value:
                    print(f"✅ On-chain Proof: https://explorer.solana.com/tx/{res.value}?cluster=devnet")
                    print(f"✅ Данные успешно записаны в блокчейн Solana!")
                
            except Exception as e:
                print(f"❌ Ошибка записи в блокчейн: {e}")
                
        else:
            print("⏳ Ожидание формирования рейтинга...")
            
        # Не спамим транзакциями, обновляем on-chain раз в 30 секунд
        await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(bridge_ai_to_blockchain())