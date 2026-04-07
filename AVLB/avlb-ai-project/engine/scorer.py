from enum import Enum
from typing import Dict, Any, Optional
import pickle
import numpy as np

class NetworkMode(Enum):
    NORMAL = "NORMAL"
    HIGH_LOAD = "HIGH_LOAD"
    CRITICAL = "CRITICAL"

class ValidatorScorer:
    def __init__(self):
        # Веса метрик для разных состояний сети
        self.mode_weights = {
            NetworkMode.NORMAL: {"success": 45, "load": 20, "latency": 20, "sync": 10, "fee": 5},
            NetworkMode.HIGH_LOAD: {"success": 30, "load": 15, "latency": 40, "sync": 10, "fee": 5},
            NetworkMode.CRITICAL: {"success": 20, "load": 35, "latency": 10, "sync": 30, "fee": 5}
        }
        # Зарезервировано для ML модели (нейросети)
        self.model: Optional[Any] = None

    def load_ml_model(self, model_path: str):
        """Метод для загрузки обученной модели."""
        try:
            with open(model_path, 'rb') as f:
                data = pickle.load(f)
                if isinstance(data, dict):
                    self.model = data.get('model')
                    self.scaler = data.get('scaler')
                    print(f"✅ ML Model loaded from {model_path}")
                else:
                    print(f"⚠️ Model file format is invalid. Run training to fix.")
        except Exception as e:
            print(f"⚠️ Failed to load ML model: {e}. Using heuristic scoring.")

    def calculate_score(self, metrics: Dict[str, Any], mode: NetworkMode = NetworkMode.NORMAL) -> float:
        # Если модель загружена, используем её для предсказания
        if self.model:
            try:
                # Используем numpy напрямую вместо DataFrame для скорости
                feat_array = np.array([[
                    metrics.get('latency_ms', 0),
                    metrics.get('sync_diff', 0),
                    metrics.get('success_rate', 0)
                ]])
                
                if hasattr(self, 'scaler') and self.scaler:
                    feat_array = self.scaler.transform(feat_array)

                return round(float(self.model.predict(feat_array)[0]), 2)
            except Exception as e:
                print(f"ML Scoring error: {e}")

        w = self.mode_weights.get(mode, self.mode_weights[NetworkMode.NORMAL])
        
        # Расчет факторов
        success_factor = ((metrics.get('success_rate', 0) / 100) ** 2) * w['success']
        load_factor = (1 - (metrics.get('load_percent', 0) / 100)) * w['load']
        latency_factor = max(0.0, (1 - (metrics.get('latency_ms', 0) / 800))) * w['latency']
        
        sync_diff = metrics.get('sync_diff', 0)
        sync_factor = w['sync'] if sync_diff <= 1 else max(-100.0, w['sync'] - (sync_diff * 10))
        
        fee_factor = max(0.0, (1 - (metrics.get('priority_fee', 0) / 20000))) * w['fee']
        
        return round(max(0.0, success_factor + load_factor + latency_factor + sync_factor + fee_factor), 2)
