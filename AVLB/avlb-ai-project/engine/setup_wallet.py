import asyncio
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair

async def setup():
    # 1. Создаем новый кошелек
    sender = Keypair()
    pubkey = sender.pubkey()
    print(f"🌟 Новый кошелек создан!")
    print(f"Адрес (Public Key): {pubkey}")
    
    # Сохраняем приватный ключ в файл, чтобы не потерять
    with open("test_keypair.json", "wb") as f:
        f.write(sender.to_bytes())
    print("💾 Ключ сохранен в test_keypair.json")

    # 2. Запрашиваем Airdrop (бесплатные SOL в Devnet)
    async with AsyncClient("https://api.devnet.solana.com") as client:
        print("🪂 Запрашиваем 1 SOL на Devnet...")
        # 1 SOL = 1,000,000,000 Lamports
        try:
            res = await client.request_airdrop(pubkey, 1_000_000_000)
            if res and hasattr(res, 'value') and res.value:
                print(f"✅ Успех! Сигнатура: {res.value}")
                print("⏳ Ожидание подтверждения транзакции (10-20 сек)...")
                
                await asyncio.sleep(10)
                balance = await client.get_balance(pubkey)
                print(f"💰 Текущий баланс: {balance.value / 1_000_000_000} SOL")
                
                if balance.value == 0:
                    print("⚠️ Баланс всё еще 0. Попробуйте запросить SOL еще раз через 30 секунд.")
            else:
                print(f"⚠️ Кран Devnet (Airdrop) перегружен.")
                print(f"👉 Пополни вручную здесь: https://faucet.solana.com/")
                print(f"👉 Твой адрес: {pubkey}")

        except Exception as e:
            print(f"❌ Ошибка: {e}")
            print(f"👉 Пополни вручную: https://faucet.solana.com/ для {pubkey}")

if __name__ == "__main__":
    asyncio.run(setup())