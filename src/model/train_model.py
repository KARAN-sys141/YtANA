import os
os.environ["TF_USE_LEGACY_KERAS"] = "1"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import tensorflow as tf
import mlflow
import mlflow.tensorflow
import pandas as pd
import numpy as np
from src.data_pipeline.preprocess import YouTubeDataPipeline
from src.model.architecture import build_multitask_model

DATA_PATH = "data/raw/train_updated.csv"
TEST_PATH = "data/raw/test_updated.csv"
MODEL_SAVE_PATH = "saved_models/youtube_intelligence_v1.h5"
MLFLOW_EXPERIMENT_NAME = "YouTube_Intelligence_DistilBERT"
BATCH_SIZE = 16 
MAX_LEN = 64
EPOCHS = 1     
LEARNING_RATE = 3e-5

def main():
    mlflow.set_tracking_uri("file:./mlruns")
    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
    
    print("Starting Training Pipeline...")
    
    with mlflow.start_run():
        mlflow.log_param("batch_size", BATCH_SIZE)
        mlflow.log_param("epochs", EPOCHS)
        mlflow.log_param("learning_rate", LEARNING_RATE)
        mlflow.log_param("max_len", MAX_LEN)

        print("Loading Data...")
        try:
            train_df = pd.read_csv(DATA_PATH)
            test_df = pd.read_csv(TEST_PATH)
        except FileNotFoundError:
            print(f"Data files not found at {DATA_PATH} or {TEST_PATH}")
            return

        data_pipe = YouTubeDataPipeline(max_len=MAX_LEN, batch_size=BATCH_SIZE)
        
        print("Processing Training Data...")
        train_ds, train_weights = data_pipe.process_data(train_df, is_training=True)
        
        print("Processing Validation Data...")
        val_ds, _ = data_pipe.process_data(test_df, is_training=False)

        print("Building Multi-Task Model...")
        model = build_multitask_model(max_len=MAX_LEN, model_checkpoint="distilbert-base-uncased")
        
        callbacks = [
            tf.keras.callbacks.EarlyStopping(patience=2, restore_best_weights=True),
            tf.keras.callbacks.ModelCheckpoint(
                filepath="checkpoint_model.h5",
                save_best_only=True,
                save_weights_only=False
            )
        ]

        print(f"Starting Training for {EPOCHS} Epoch(s)...")
        
        history = model.fit(
            train_ds,
            validation_data=val_ds,
            epochs=EPOCHS,
            callbacks=callbacks
        )

        print("Logging metrics to MLflow...")
        for metric, values in history.history.items():
            mlflow.log_metric(metric, values[-1])

        print(f"Saving model to {MODEL_SAVE_PATH}...")
        os.makedirs(os.path.dirname(MODEL_SAVE_PATH), exist_ok=True)
        
        model.save(MODEL_SAVE_PATH)
         
        mlflow.log_artifact(MODEL_SAVE_PATH)
        
        print("\nTraining Complete. Model saved.")
        print(f"Run 'mlflow ui' in terminal to view experiments.")

if __name__ == "__main__":
    main()