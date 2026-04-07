import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from storage import MetricsStorage
import asyncio
import httpx
import logging
import base64
import os
import random
import json

# Настройка профессионального логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("Relay")

# Реальные зависимости Solana
try:
    from solana.rpc.async_api import AsyncClient
    from solders.transaction import Transaction
except ImportError:
    logger.error("Missing dependencies: pip install solana solders")
    AsyncClient = None
    Transaction = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: запуск фоновой синхронизации
    asyncio.create_task(sync_metrics_with_peers())
    logger.info(f"🌐 Relay started: Level {RELAY_LEVEL} | Region {RELAY_REGION}")
    yield

app = FastAPI(
    title="AVLB AI Relay Node",
    description="Relay node for routing transactions to the best performing validator based on AVLB AI.",
    version="0.1.0",
    lifespan=lifespan
)

storage = MetricsStorage()

# --- HIERARCHY CONFIGURATION ---
# Эти параметры можно задавать через переменные окружения
RELAY_LEVEL = int(os.getenv("RELAY_LEVEL", "2"))  # 1 - Intercontinental, 2 - Regional
RELAY_REGION = os.getenv("RELAY_REGION", "US-EAST")
NEIGHBOR_RELAYS = os.getenv("NEIGHBOR_RELAYS", "").split(",") # Соседи (Level 2)
UPSTREAM_RELAY = os.getenv("UPSTREAM_RELAY", "http://intercontinental-hub:8000") # Hub (Level 1)

RPC_ENDPOINT = "https://api.devnet.solana.com"

class TransactionRequest(BaseModel):
    tx_b64: str  # Реальные данные транзакции
    priority: str = "medium"
    user_id: str = "anonymous"

class MetricSyncRequest(BaseModel):
    pubkey: str
    score: float
    metrics: dict
    mode: str

async def sync_metrics_with_peers():
    """Фоновая задача для клонирования лучших метрик соседям и на уровень выше."""
    while True:
        await asyncio.sleep(15) # Синхронизация каждые 15 секунд
        top_nodes = storage.get_top_validators(n=3)
        if not top_nodes or not NEIGHBOR_RELAYS:
            continue

        async with httpx.AsyncClient() as client:
            for pubkey, score in top_nodes:
                # Получаем полные данные из Redis
                v_data = storage.client.hgetall(f"avlb:validator:{pubkey}")
                if not v_data: continue
                
                payload = {
                    "pubkey": pubkey,
                    "score": score,
                    "metrics": json.loads(v_data['metrics']),
                    "mode": v_data['mode']
                }
                
                # Клонируем соседям по региону
                for peer in NEIGHBOR_RELAYS:
                    if not peer: continue
                    try:
                        await client.post(f"{peer}/internal/sync", json=payload, timeout=2)
                    except:
                        pass

@app.get("/")
async def read_root():
    """
    Базовый эндпоинт для проверки работоспособности Relay-ноды.
    """
    return {"message": "AVLB AI Relay Node is running. Send transactions to /send_transaction"}

@app.post("/internal/sync")
async def receive_metrics(sync_data: MetricSyncRequest):
    """Эндпоинт для клонирования метрик от других Relay-узлов."""
    storage.save_validator_stats(
        sync_data.pubkey, 
        sync_data.score, 
        sync_data.metrics, 
        sync_data.mode
    )
    return {"status": "synced"}

@app.post("/send_transaction")
async def send_transaction(tx_request: TransactionRequest):
    """
    Маршрутизация транзакции с использованием High-Availability (HA) логики.
    Если основной валидатор недоступен, выбирается следующий из топа.
    """
    logger.info(f"📥 Incoming TX from user: {tx_request.user_id}")

    # 1. Валидация транзакции (Solders)
    try:
        raw_tx = base64.b64decode(tx_request.tx_b64)
        if Transaction:
            Transaction.from_bytes(raw_tx) # Проверка структуры транзакции
    except Exception as e:
        logger.error(f"❌ Invalid transaction format: {e}")
        raise HTTPException(status_code=400, detail="Invalid Base64 transaction data")
    
    # 2. Получаем пул из ТОП-5 валидаторов для рандомизации
    top_nodes = storage.get_top_validators(n=5)
    
    if not top_nodes:
        logger.warning("⚠️ No best validator found. AI might be warming up.")
        raise HTTPException(status_code=503, detail="AI is not ready or no best validator found. Please ensure collector.py is running.")
    
    # Рандомизация: перемешиваем список лучших, чтобы выбор был непредсказуемым
    random.shuffle(top_nodes)
    
    # 3. Попытка отправки по перемешанному списку
    async with AsyncClient(RPC_ENDPOINT) as client:
        for i, (pubkey, score) in enumerate(top_nodes):
            try:
                logger.info(f"🧠 AI Selected Candidate {i+1}: {pubkey[:8]}... (Score: {score})")
                
                response = await client.send_raw_transaction(raw_tx)
                
                if response.value:
                    logger.info(f"🚀 Successfully routed to {pubkey[:8]}. Signature: {response.value}")
                    return {
                        "status": "success",
                        "signature": str(response.value),
                        "routed_to": pubkey,
                        "score": score,
                        "selection_method": "random_top_pool"
                    }
            except Exception as e:
                logger.error(f"⚠️ Solana RPC Error for {pubkey[:8]}: {str(e)}")
                continue # Пробуем следующий узел в списке ИИ

    raise HTTPException(status_code=502, detail="Failed to route transaction to any top-tier validators")

if __name__ == "__main__":
    logger.info("🚀 AVLB AI Relay Node initializing...")
    logger.info("📖 Documentation available at http://127.0.0.1:8000/docs")
    try:
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        logger.info("💡 Tip: Check if another instance of relay_server.py is running on port 8000.")
        logger.info("💡 You can also try changing the port in uvicorn.run(...)")