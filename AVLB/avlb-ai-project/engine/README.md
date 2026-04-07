# AVLB AI: Neural Network Transaction Relay for Solana

**AVLB AI** — это децентрализованная система маршрутизации транзакций, использующая нейронные сети для выбора наиболее эффективных валидаторов в режиме реального времени.

## 🚀 Основные возможности
- **AI Scorer (MLP Regressor)**: Нейросеть с точностью R²=0.95 предсказывает производительность узлов.
- **Dynamic Load Balancing**: Автоматическое переключение режимов (Normal/High Load/Critical) при перегрузках сети.
- **On-chain Proof**: Интеграция с Solana Memo Program для записи AI-рейтингов прямо в блокчейн.
- **High Availability**: Автоматический failover — если основной валидатор занят, транзакция мгновенно перенаправляется следующему из ТОП-пула.

## 🛠 Технологический стек
- **AI**: Python, Scikit-learn (Multi-layer Perceptron), Pandas.
- **Blockchain**: Solana Python SDK (Solders), Devnet RPC.
- **Backend**: FastAPI, Uvicorn, Redis (In-memory storage).
- **Frontend**: Streamlit (Neural Monitor Dashboard).

## 🚦 Быстрый запуск

1. **Подготовка окружения**:
   ```bash
   pip install -r requirements.txt
   # Убедитесь, что Redis запущен на порту 6379
   ```

2. **Запуск системы (рекомендуется через run_all.ps1)**:
   - `collector.py`: Сбор данных и работа ИИ.
   - `relay_server.py`: Прием и маршрутизация транзакций.
   - `integrator.py`: Запись рейтингов в блокчейн.
   - `app.py`: Визуальный дашборд.

3. **Тестирование**:
   ```bash
   python test_relay.py
   ```

## 📊 Точность модели
Текущая модель обучена на 1000+ кейсов с финальной потерей (loss) < 6.0 и MAE < 1.8 балла, что позволяет гарантировать выбор валидатора с минимальным Latency и Slot Drop.
---
*Developed for AVLB AI Project - 2025*