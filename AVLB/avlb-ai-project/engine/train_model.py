import pandas as pd
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import pickle
import glob
import os

def train_latest_data():
    # 1. Ищем самый свежий CSV файл
    list_of_files = glob.glob('validator_history_*.csv')
    if not list_of_files:
        print("❌ Нет данных для обучения. Сначала запустите export_data.py")
        return

    latest_file = max(list_of_files, key=os.path.getctime)
    print(f"📊 Обучение на данных: {latest_file}")

    # 2. Загрузка данных
    df = pd.read_csv(latest_file)
    
    # Нам нужны только числовые признаки для обучения
    # Используем .values для обучения скалера без привязки к именам колонок
    X = df[['latency', 'sync_diff', 'success_rate']].values
    y = df['score'].values

    if len(df) < 10:
        print("⚠️ Слишком мало данных для качественного обучения. Нужно хотя бы 50-100 записей.")
    if len(df) < 50:
        print(f"⚠️ Слишком мало данных ({len(df)}). Нужно хотя бы 50-100 записей для валидации.")
        return

    # 2.1 Разделение на обучающую и тестовую выборки (80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # 3. Подготовка данных (нейросети чувствительны к масштабу)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train) # Обучаем скалер только на тренировочных данных
    X_test_scaled = scaler.transform(X_test)

    # 4. Создание и обучение Нейронной Сети (MLP)
    model = MLPRegressor(
        hidden_layer_sizes=(64, 32),
        activation='relu',
        solver='adam',
        max_iter=2000,
        early_stopping=True,
        validation_fraction=0.1,
        n_iter_no_change=10,
        random_state=42
    )
    
    print("🧠 Обучение нейронной сети...")
    model.fit(X_train_scaled, y_train)

    # 5. Сохранение модели и скалера (важно сохранить скалер тоже)
    model_path = 'validator_model.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump({'model': model, 'scaler': scaler}, f)
    
    # 6. Оценка качества
    predictions = model.predict(X_test_scaled)
    mae = mean_absolute_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)

    print(f"✅ Модель сохранена в {model_path}")
    print(f"📈 Нейросеть сошлась за {model.n_iter_} итераций")
    print(f"🎯 Точность R² Score: {r2:.4f} (ближе к 1.0 — лучше)")
    print(f"📏 Средняя ошибка (MAE): {mae:.2f} балла")
    print(f"📉 Внутренняя потеря (loss): {model.loss_:.6f}")

if __name__ == "__main__":
    # Убедитесь, что установлены зависимости: 
    # pip install scikit-learn pandas
    train_latest_data()