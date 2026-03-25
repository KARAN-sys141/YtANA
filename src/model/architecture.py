import os
os.environ["TF_USE_LEGACY_KERAS"] = "1"  

import tensorflow as tf
from transformers import TFDistilBertModel

def build_multitask_model(max_len=64, model_checkpoint="distilbert-base-uncased"):
    distilbert_base = TFDistilBertModel.from_pretrained(model_checkpoint)
    
    input_ids = tf.keras.layers.Input(shape=(max_len,), dtype=tf.int32, name="input_ids")
    attention_mask = tf.keras.layers.Input(shape=(max_len,), dtype=tf.int32, name="attention_mask")
    
    bert_output = distilbert_base(input_ids=input_ids, attention_mask=attention_mask)[0]
    
    cls_token_state = bert_output[:, 0, :]
    
    shared_features = tf.keras.layers.Dropout(0.3)(cls_token_state)
    
    sentiment_output = tf.keras.layers.Dense(
        3, activation="softmax", name="sentiment_output"
    )(shared_features)
    
    emotion_output = tf.keras.layers.Dense(
        7, activation="softmax", name="emotion_output"
    )(shared_features)
    
    toxicity_output = tf.keras.layers.Dense(
        1, activation="sigmoid", name="toxicity_output"
    )(shared_features)
    
    model = tf.keras.Model(
        inputs=[input_ids, attention_mask],
        outputs=[sentiment_output, emotion_output, toxicity_output],
    )
    
    optimizer = tf.keras.optimizers.Adam(learning_rate=3e-5)
    
    model.compile(
        optimizer=optimizer,
        loss={
            "sentiment_output": "sparse_categorical_crossentropy",
            "emotion_output": "sparse_categorical_crossentropy",
            "toxicity_output": "binary_crossentropy",
        },
        metrics={
            "sentiment_output": ["accuracy"],
            "emotion_output": ["accuracy"],
            "toxicity_output": ["accuracy", tf.keras.metrics.AUC(name="auc")],
        },
    )
    
    return model

if __name__ == "__main__":
    model = build_multitask_model(max_len=64)
    model.summary()
    print("\nMulti-task model architecture successfully built")