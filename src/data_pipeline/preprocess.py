import pandas as pd
import numpy as np
import tensorflow as tf
import emoji
import re
from transformers import AutoTokenizer
from sklearn.utils.class_weight import compute_class_weight

class YouTubeDataPipeline:
    def __init__(self, model_checkpoint="distilbert-base-uncased", max_len=64, batch_size=32):
        self.max_len = max_len
        self.batch_size = batch_size
        self.tokenizer = AutoTokenizer.from_pretrained(model_checkpoint)
        
        self.emotion_map = {
            'neutral': 0, 'fear': 1, 'anger': 2, 
            'joy': 3, 'surprise': 4, 'sadness': 5, 'disgust': 6
        }
        self.sentiment_map = {1: 2, 0: 1, -1: 0}

    def inject_synthetic_toxicity(self, df):
        print("Injecting synthetic toxic comments to balance dataset")
        toxic_samples = [
            "I absolutely hate this video, it's garbage.",
            "You are an idiot and you should delete your channel.",
            "This is the worst content I have ever seen, kill yourself.",
            "F*** this stupid tutorial, waste of time.",
            "Moron, you have no idea what you are talking about.",
            "I hope you fail miserably, disgusting pig."
        ] * 50 
        
        synth_df = pd.DataFrame({
            'clean_comment': toxic_samples,
            'sentiment': [-1] * len(toxic_samples),
            'emotion': ['anger'] * len(toxic_samples),
            'toxicity': [1] * len(toxic_samples)
        })
        
        df = pd.concat([df, synth_df], ignore_index=True)
        df = df.sample(frac=1, random_state=42).reset_index(drop=True)
        return df

    def clean_text(self, text):
        if not isinstance(text, str):
            return ""
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        text = emoji.demojize(text, delimiters=(" ", " "))
        text = re.sub(r'[^\w\s.,!?\'"]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text.lower()

    def calculate_class_weights(self, y_series):
        classes = np.unique(y_series)
        weights = compute_class_weight(class_weight='balanced', classes=classes, y=y_series)
        return dict(zip(classes, weights))

    def prepare_labels(self, df):
        df['sentiment_mapped'] = df['sentiment'].map(self.sentiment_map)
        df['emotion_mapped'] = df['emotion'].map(self.emotion_map)
        
        df = df.dropna(subset=['sentiment_mapped', 'emotion_mapped', 'toxicity'])
        
        return {
            'sentiment_output': tf.convert_to_tensor(df['sentiment_mapped'].values, dtype=tf.int32),
            'emotion_output': tf.convert_to_tensor(df['emotion_mapped'].values, dtype=tf.int32),
            'toxicity_output': tf.convert_to_tensor(df['toxicity'].values, dtype=tf.int32)
        }

    def process_data(self, df, is_training=True):
        if is_training:
            df = self.inject_synthetic_toxicity(df)
            
        print("Cleaning text and translating emojis")
        df['clean_text'] = df['clean_comment'].apply(self.clean_text)
        
        print(f"Tokenizing {len(df)} sequences...")
        encoded = self.tokenizer(
            df['clean_text'].tolist(),
            padding='max_length',
            truncation=True,
            max_length=self.max_len,
            return_tensors='np'  
        )
        
        input_ids = tf.convert_to_tensor(encoded['input_ids'], dtype=tf.int32)
        attention_mask = tf.convert_to_tensor(encoded['attention_mask'], dtype=tf.int32)
        
        print("[INFO] Preparing labels...")
        labels_dict = self.prepare_labels(df)
        
        weights_dict = {}
        if is_training:
            weights_dict['sentiment_output'] = self.calculate_class_weights(df['sentiment_mapped'])
            weights_dict['emotion_output'] = self.calculate_class_weights(df['emotion_mapped'])
            weights_dict['toxicity_output'] = self.calculate_class_weights(df['toxicity'])
        
        print("Building tf.data.Dataset...")
        dataset = tf.data.Dataset.from_tensor_slices((
            {"input_ids": input_ids, "attention_mask": attention_mask}, 
            labels_dict
        ))
        
        if is_training:
            dataset = dataset.shuffle(buffer_size=10000)
            
        dataset = dataset.batch(self.batch_size).prefetch(buffer_size=tf.data.AUTOTUNE)
        
        return dataset, weights_dict

if __name__ == "__main__":
    train_df = pd.read_csv("data/raw/train_updated.csv")
    
    pipeline = YouTubeDataPipeline(max_len=64, batch_size=32)
    train_dataset, class_weights = pipeline.process_data(train_df, is_training=True)
    
    print(f"Dataset Spec: {train_dataset.element_spec}")
    print(f"Toxicity Class Weights (0 vs 1): {class_weights['toxicity']}")
    print("Pipeline Ready for Multi-Task Modeling")