# import os
# import re
# import numpy as np
# import tensorflow as tf
# from collections import Counter
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from youtube_transcript_api import YouTubeTranscriptApi
# from transformers import pipeline, AutoTokenizer
# from googleapiclient.discovery import build
# from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# # --- CONFIGURATION ---
# os.environ["TF_USE_LEGACY_KERAS"] = "1"
# os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# # [APNI API KEY YAHAN DAALO]
# YOUTUBE_API_KEY = "AIzaSyCDHZ2bHpEzp2bUMcguGn7vvi9-Rpigx6E"

# MODEL_PATH = "saved_models/youtube_intelligence_quantized.tflite"
# SUMMARIZER_MODEL_NAME = "sshleifer/distilbart-cnn-12-6"
# MAX_LEN = 64

# app = FastAPI(title="YT Intel Final", version="6.0")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # --- GLOBAL VARS ---
# interpreter = None
# input_details = None
# output_details = None
# tokenizer = None
# summarizer = None
# vader = SentimentIntensityAnalyzer()
# yt_service = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# # --- STARTUP ---
# @app.on_event("startup")
# async def load_models():
#     global interpreter, input_details, output_details, tokenizer, summarizer
#     try:
#         if os.path.exists(MODEL_PATH):
#             interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
#             interpreter.allocate_tensors()
#             input_details = interpreter.get_input_details()
#             output_details = interpreter.get_output_details()
#             print("[SUCCESS] TFLite Loaded.")
#             tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
#         else:
#             print("[ERROR] TFLite Model Missing.")
#     except: pass

#     try:
#         print("[INFO] Loading Summarizer...")
#         summarizer = pipeline("summarization", model=SUMMARIZER_MODEL_NAME)
#         print("[SUCCESS] Summarizer Ready!")
#     except: pass

# class VideoRequest(BaseModel):
#     video_id: str

# # --- CORE LOGIC ---
# def extract_video_id(url: str):
#     if "v=" in url: return url.split("v=")[1].split("&")[0]
#     elif "youtu.be" in url: return url.split("/")[-1].split("?")[0]
#     return url

# def fetch_comments(video_id: str):
#     comments = []
#     try:
#         request = yt_service.commentThreads().list(part="snippet", videoId=video_id, maxResults=100, textFormat="plainText")
#         while request and len(comments) < 800:
#             response = request.execute()
#             for item in response['items']:
#                 comments.append(item['snippet']['topLevelComment']['snippet']['textDisplay'])
#             request = yt_service.commentThreads().list_next(request, response)
#         return comments
#     except: return comments

# def analyze_hybrid(text: str):
#     # 1. VADER (Ruler of Sentiment) - AGGRESSIVE
#     # Social media ke liye VADER best hai.
#     vs = vader.polarity_scores(text)
#     compound = vs['compound']
    
#     # Thresholds: 0.05 se 0.01 kar diya taaki Neutral kam ho jaye
#     sent = "NEUTRAL"
#     if compound >= 0.01: sent = "POSITIVE"
#     elif compound <= -0.01: sent = "NEGATIVE"
    
#     # 2. AI (Ruler of Emotion)
#     emo = "neutral"
#     tox = 0.0
    
#     if interpreter and tokenizer:
#         try:
#             encoded = tokenizer(text, max_length=MAX_LEN, padding='max_length', truncation=True, return_tensors='np')
#             interpreter.set_tensor(input_details[0]['index'], encoded['input_ids'].astype(np.int32))
#             interpreter.set_tensor(input_details[1]['index'], encoded['attention_mask'].astype(np.int32))
#             interpreter.invoke()
            
#             emo_probs = interpreter.get_tensor(output_details[1]['index'])[0]
#             tox = float(interpreter.get_tensor(output_details[2]['index'])[0][0])
            
#             # Find best emotion (Skipping Neutral at index 0)
#             labels = ['neutral', 'fear', 'anger', 'joy', 'surprise', 'sadness', 'disgust']
#             best_idx = np.argmax(emo_probs[1:]) + 1
#             emo = labels[best_idx]
            
#             # Conflict Fixes
#             if sent == "POSITIVE" and emo in ['fear', 'anger', 'sadness', 'disgust']:
#                 emo = "joy" if emo_probs[3] > emo_probs[4] else "surprise"
#             elif sent == "NEGATIVE" and emo in ['joy', 'surprise']:
#                 emo = "anger"
#         except: pass

#     return {"sentiment": sent, "emotion": emo, "toxicity": tox}

# # --- API ---
# @app.post("/analyze")
# def analyze_api(req: VideoRequest):
#     vid = extract_video_id(req.video_id)
#     comments = fetch_comments(vid)
    
#     if not comments: return {"error": "No comments found."}

#     stats = { "positive": 0, "neutral": 0, "negative": 0, "toxic_count": 0, 
#               "emotion_counts": {k:0 for k in ['joy','surprise','sadness','anger','fear','disgust']} }
    
#     rich_data = []
#     all_text = ""

#     for c in comments:
#         if len(c) < 2: continue
#         try:
#             res = analyze_hybrid(c)
            
#             # Stats Update
#             stats[res['sentiment'].lower()] += 1
#             if res['toxicity'] > 0.6: stats['toxic_count'] += 1
            
#             # Emotion Update (Skip neutral emotion counting for radar chart)
#             if res['emotion'] in stats['emotion_counts']: 
#                 stats['emotion_counts'][res['emotion']] += 1
            
#             all_text += " " + c
#             if len(rich_data) < 50:
#                 rich_data.append({"text": c, "sentiment": res['sentiment'], "emotion": res['emotion']})
#         except: continue

#     # Keywords
#     words = re.findall(r'\b[a-z]{4,15}\b', all_text.lower())
#     stops = {'this','that','video','watch','just','have','your','with','from','like','good','very','what','when','time','make','know','about','best','love','people','content', 'please', 'thank', 'thanks'}
#     keywords = Counter([w for w in words if w not in stops]).most_common(12)

#     return {
#         "meta": {
#             # Yaha hum 'total' aur 'total_scanned' dono bhejenge taaki frontend confuse na ho
#             "total": len(comments),  
#             "total_scanned": len(comments),
#             "avg_len": int(len(all_text.split())/len(comments)) if comments else 0
#         },
#         "stats": stats,
#         "comments": rich_data,
#         "keywords": keywords
#     }

# @app.post("/summarize")
# def summarize_api(req: VideoRequest):
#     vid = extract_video_id(req.video_id)
#     try:
#         transcript = YouTubeTranscriptApi.get_transcript(vid, languages=['en','hi'])
#         text = " ".join([t['text'] for t in transcript])
#         if summarizer:
#             return {"summary": summarizer(text[:3000], max_length=150, min_length=40, do_sample=False)[0]['summary_text']}
#         return {"summary": "Summarizer Loading..."}
#     except: return {"summary": "⚠️ No Captions Found."}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=8000)





# import os
# import re
# import numpy as np
# import tensorflow as tf
# from collections import Counter
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from youtube_transcript_api import YouTubeTranscriptApi
# from transformers import pipeline, AutoTokenizer
# from googleapiclient.discovery import build
# from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# # --- CONFIGURATION ---
# os.environ["TF_USE_LEGACY_KERAS"] = "1"
# os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# # [APNI API KEY YAHAN DAALO]
# YOUTUBE_API_KEY = "AIzaSyCDHZ2bHpEzp2bUMcguGn7vvi9-Rpigx6E"

# MODEL_PATH = "saved_models/youtube_intelligence_quantized.tflite"
# SUMMARIZER_MODEL_NAME = "sshleifer/distilbart-cnn-12-6"
# MAX_LEN = 64

# app = FastAPI(title="YT Intel Logic V2", version="7.0")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # --- GLOBAL VARS ---
# interpreter = None
# input_details = None
# output_details = None
# tokenizer = None
# summarizer = None
# vader = SentimentIntensityAnalyzer()
# yt_service = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# # --- KEYWORD DICTIONARIES (Forcing Logic) ---
# KEYWORDS_JOY = ['love', 'best', 'great', 'awesome', 'amazing', 'good', 'thank', 'thanks', 'perfect', 'beautiful', 'nice', 'excellent', 'helpful', 'op', 'fire', '🔥', '❤️']
# KEYWORDS_ANGER = ['bad', 'worst', 'hate', 'stupid', 'fake', 'scam', 'boring', 'trash', 'useless', 'dislike', 'shame', 'clickbait']
# KEYWORDS_SURPRISE = ['wow', 'omg', 'really', 'what', 'unbelievable', 'crazy', 'shocking']
# KEYWORDS_SADNESS = ['sad', 'sorry', 'miss', 'cry', 'pain', 'bad news', 'rip']

# # --- STARTUP ---
# @app.on_event("startup")
# async def load_models():
#     global interpreter, input_details, output_details, tokenizer, summarizer
#     try:
#         if os.path.exists(MODEL_PATH):
#             interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
#             interpreter.allocate_tensors()
#             input_details = interpreter.get_input_details()
#             output_details = interpreter.get_output_details()
#             print("[SUCCESS] TFLite Loaded.")
#             tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
#         else:
#             print("[ERROR] TFLite Model Missing.")
#     except: pass

#     try:
#         print("[INFO] Loading Summarizer...")
#         summarizer = pipeline("summarization", model=SUMMARIZER_MODEL_NAME)
#         print("[SUCCESS] Summarizer Ready!")
#     except: pass

# class VideoRequest(BaseModel):
#     video_id: str

# def extract_video_id(url: str):
#     if "v=" in url: return url.split("v=")[1].split("&")[0]
#     elif "youtu.be" in url: return url.split("/")[-1].split("?")[0]
#     return url

# def fetch_comments(video_id: str):
#     comments = []
#     try:
#         request = yt_service.commentThreads().list(part="snippet", videoId=video_id, maxResults=100, textFormat="plainText")
#         while request and len(comments) < 800:
#             response = request.execute()
#             for item in response['items']:
#                 comments.append(item['snippet']['topLevelComment']['snippet']['textDisplay'])
#             request = yt_service.commentThreads().list_next(request, response)
#         return comments
#     except: return comments

# def get_emotion_from_keywords(text_lower):
#     """Overrides AI if keywords are found"""
#     for w in KEYWORDS_JOY:
#         if w in text_lower: return "joy"
#     for w in KEYWORDS_ANGER:
#         if w in text_lower: return "anger"
#     for w in KEYWORDS_SURPRISE:
#         if w in text_lower: return "surprise"
#     for w in KEYWORDS_SADNESS:
#         if w in text_lower: return "sadness"
#     return None

# def analyze_hybrid(text: str):
#     text_lower = text.lower()
    
#     # 1. VADER SENTIMENT (Slightly relaxed for Neutral)
#     vs = vader.polarity_scores(text)
#     compound = vs['compound']
    
#     # Adjusted Thresholds: 0.05 se -0.05 ke beech Neutral rahega.
#     sent = "NEUTRAL"
#     if compound >= 0.05: sent = "POSITIVE"
#     elif compound <= -0.05: sent = "NEGATIVE"
    
#     # 2. AI MODEL (Raw Data)
#     emo_model = "neutral"
#     tox_score = 0.0
    
#     if interpreter and tokenizer:
#         try:
#             encoded = tokenizer(text, max_length=MAX_LEN, padding='max_length', truncation=True, return_tensors='np')
#             interpreter.set_tensor(input_details[0]['index'], encoded['input_ids'].astype(np.int32))
#             interpreter.set_tensor(input_details[1]['index'], encoded['attention_mask'].astype(np.int32))
#             interpreter.invoke()
            
#             # Extract
#             emo_probs = interpreter.get_tensor(output_details[1]['index'])[0]
#             tox_score = float(interpreter.get_tensor(output_details[2]['index'])[0][0])
            
#             # Model's Best Guess (Skipping Neutral index 0)
#             labels = ['neutral', 'fear', 'anger', 'joy', 'surprise', 'sadness', 'disgust']
#             best_idx = np.argmax(emo_probs[1:]) + 1
#             emo_model = labels[best_idx]
#         except: pass

#     # 3. FINAL LOGIC MERGE (The Fix)
    
#     # Priority 1: Check Keywords (Sabse Accurate)
#     final_emo = get_emotion_from_keywords(text_lower)
    
#     # Priority 2: Fallback to Model if no keywords
#     if not final_emo:
#         final_emo = emo_model

#     # Priority 3: Conflict Resolution (Never allow Mismatch)
#     if sent == "POSITIVE":
#         # Positive Sentiment cannot be Fear/Anger/Disgust/Sadness
#         if final_emo in ['fear', 'anger', 'sadness', 'disgust', 'neutral']:
#             final_emo = "joy" # Default to Joy if confused
            
#     elif sent == "NEGATIVE":
#         # Negative Sentiment cannot be Joy/Surprise/Neutral
#         if final_emo in ['joy', 'surprise', 'neutral']:
#             final_emo = "anger" # Default to Anger if confused

#     # 4. TOXICITY LOGIC (Crucial Fix)
#     # A comment is ONLY toxic if:
#     # A) Sentiment is NEGATIVE OR
#     # B) Toxicity Score is extremely high (> 0.85)
#     final_is_toxic = False
#     if tox_score > 0.85: 
#         final_is_toxic = True
#     elif tox_score > 0.60 and sent == "NEGATIVE":
#         final_is_toxic = True
        
#     return {"sentiment": sent, "emotion": final_emo, "toxicity": 1 if final_is_toxic else 0}

# @app.post("/analyze")
# def analyze_api(req: VideoRequest):
#     vid = extract_video_id(req.video_id)
#     comments = fetch_comments(vid)
    
#     if not comments: return {"error": "No comments found."}

#     stats = { "positive": 0, "neutral": 0, "negative": 0, "toxic_count": 0, 
#               "emotion_counts": {k:0 for k in ['joy','surprise','sadness','anger','fear','disgust']} }
    
#     rich_data = []
#     all_text = ""

#     for c in comments:
#         if len(c) < 2: continue
#         try:
#             res = analyze_hybrid(c)
            
#             # Stats
#             stats[res['sentiment'].lower()] += 1
#             if res['toxicity'] == 1: stats['toxic_count'] += 1
            
#             # Emotion (Ensure it's valid)
#             e = res['emotion']
#             if e not in stats['emotion_counts']:
#                 # If Neutral came through (rare), don't add to specific bins or add to 'joy' if positive
#                 if res['sentiment'] == "POSITIVE": e = "joy"
#                 elif res['sentiment'] == "NEGATIVE": e = "anger"
            
#             if e in stats['emotion_counts']:
#                 stats['emotion_counts'][e] += 1
            
#             all_text += " " + c
#             if len(rich_data) < 50:
#                 rich_data.append({"text": c, "sentiment": res['sentiment'], "emotion": e})
#         except: continue

#     # Keywords
#     words = re.findall(r'\b[a-z]{4,15}\b', all_text.lower())
#     stops = {'this','that','video','watch','just','have','your','with','from','like','good','very','what','when','time','make','know','about','best','love','people','content','please','thank','thanks'}
#     keywords = Counter([w for w in words if w not in stops]).most_common(12)

#     return {
#         "meta": {
#             "total": len(comments), 
#             "total_scanned": len(comments),
#             "avg_len": int(len(all_text.split())/len(comments)) if comments else 0
#         },
#         "stats": stats,
#         "comments": rich_data,
#         "keywords": keywords
#     }

# @app.post("/summarize")
# def summarize_api(req: VideoRequest):
#     vid = extract_video_id(req.video_id)
#     try:
#         transcript = YouTubeTranscriptApi.get_transcript(vid, languages=['en','hi'])
#         text = " ".join([t['text'] for t in transcript])
#         if summarizer:
#             return {"summary": summarizer(text[:3000], max_length=150, min_length=40, do_sample=False)[0]['summary_text']}
#         return {"summary": "Model Loading..."}
#     except: return {"summary": "⚠️ No Captions Found."}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=8000)





# import os
# import re
# import numpy as np
# import tensorflow as tf
# from collections import Counter
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from youtube_transcript_api import YouTubeTranscriptApi
# from transformers import pipeline, AutoTokenizer
# from googleapiclient.discovery import build
# from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# # --- CONFIGURATION ---
# os.environ["TF_USE_LEGACY_KERAS"] = "1"
# os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# # [PASTE YOUR KEY HERE]
# YOUTUBE_API_KEY = "AIzaSyCDHZ2bHpEzp2bUMcguGn7vvi9-Rpigx6E"

# MODEL_PATH = "saved_models/youtube_intelligence_quantized.tflite"
# SUMMARIZER_MODEL_NAME = "sshleifer/distilbart-cnn-12-6"
# MAX_LEN = 64

# app = FastAPI(title="YouTube Intelligence Pro", version="7.0")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # --- GLOBAL VARS ---
# interpreter = None
# input_details = None
# output_details = None
# tokenizer = None
# summarizer = None
# vader = SentimentIntensityAnalyzer()
# yt_service = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# # --- STARTUP ---
# @app.on_event("startup")
# async def load_models():
#     global interpreter, input_details, output_details, tokenizer, summarizer
#     try:
#         if os.path.exists(MODEL_PATH):
#             interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
#             interpreter.allocate_tensors()
#             input_details = interpreter.get_input_details()
#             output_details = interpreter.get_output_details()
#             print("[SUCCESS] TFLite Model Loaded.")
#             tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
#         else:
#             print("[ERROR] TFLite Model Missing.")
#     except: pass

#     try:
#         print("[INFO] Loading Summarizer...")
#         summarizer = pipeline("summarization", model=SUMMARIZER_MODEL_NAME)
#         print("[SUCCESS] Summarizer Ready!")
#     except: pass

# class VideoRequest(BaseModel):
#     video_id: str

# # --- CORE LOGIC ---
# def extract_video_id(url: str):
#     if "v=" in url: return url.split("v=")[1].split("&")[0]
#     elif "youtu.be" in url: return url.split("/")[-1].split("?")[0]
#     return url

# def get_video_stats(video_id: str):
#     """Fetches the REAL total comment count from YouTube Metadata"""
#     try:
#         response = yt_service.videos().list(
#             part="statistics",
#             id=video_id
#         ).execute()
#         if response['items']:
#             return int(response['items'][0]['statistics']['commentCount'])
#         return 0
#     except:
#         return 0

# def fetch_comments_sample(video_id: str):
#     """Fetches a sample of comments for analysis (e.g., 1000)"""
#     comments = []
#     try:
#         request = yt_service.commentThreads().list(part="snippet", videoId=video_id, maxResults=100, textFormat="plainText")
#         # Limit badha kar 1500 kar diya hai taaki sample bada ho
#         while request and len(comments) < 1500:
#             response = request.execute()
#             for item in response['items']:
#                 comments.append(item['snippet']['topLevelComment']['snippet']['textDisplay'])
#             request = yt_service.commentThreads().list_next(request, response)
#         return comments
#     except: return comments

# def analyze_hybrid_logic(text: str):
#     # 1. VADER (Tweaked Thresholds)
#     vs = vader.polarity_scores(text)
#     compound = vs['compound']
    
#     # --- FIX 1: LOWER NEGATIVE THRESHOLD ---
#     # Pehle -0.05 tha (too sensitive). Ab -0.15 hai (tolerant).
#     sent = "NEUTRAL"
#     if compound >= 0.05: sent = "POSITIVE"
#     elif compound <= -0.15: sent = "NEGATIVE"
    
#     # 2. AI EMOTION
#     emo = "neutral"
#     tox = 0.0
    
#     if interpreter and tokenizer:
#         try:
#             encoded = tokenizer(text, max_length=MAX_LEN, padding='max_length', truncation=True, return_tensors='np')
#             interpreter.set_tensor(input_details[0]['index'], encoded['input_ids'].astype(np.int32))
#             interpreter.set_tensor(input_details[1]['index'], encoded['attention_mask'].astype(np.int32))
#             interpreter.invoke()
            
#             emo_probs = interpreter.get_tensor(output_details[1]['index'])[0]
#             tox = float(interpreter.get_tensor(output_details[2]['index'])[0][0])
            
#             labels = ['neutral', 'fear', 'anger', 'joy', 'surprise', 'sadness', 'disgust']
#             best_idx = np.argmax(emo_probs[1:]) + 1 # Skip neutral index 0
#             emo = labels[best_idx]
            
#             # --- FIX 2: CONFLICT RESOLUTION ---
#             if sent == "POSITIVE" and emo in ['fear', 'anger', 'sadness', 'disgust']:
#                 emo = "joy" if emo_probs[3] > emo_probs[4] else "surprise"
#             elif sent == "NEGATIVE" and emo in ['joy', 'surprise']:
#                 emo = "anger"
#         except: pass

#     return {"sentiment": sent, "emotion": emo, "toxicity": tox}

# # --- API ENDPOINTS ---
# @app.post("/analyze")
# def analyze_api(req: VideoRequest):
#     vid = extract_video_id(req.video_id)
    
#     # 1. Get True Count (Fast)
#     real_total_count = get_video_stats(vid)
    
#     # 2. Get Comments for Analysis (Slower, limited to 1500)
#     comments = fetch_comments_sample(vid)
    
#     if not comments: return {"error": "No comments found."}

#     stats = { "positive": 0, "neutral": 0, "negative": 0, "toxic_count": 0, 
#               "emotion_counts": {k:0 for k in ['joy','surprise','sadness','anger','fear','disgust']} }
    
#     rich_data = []
#     all_text = ""

#     for c in comments:
#         if len(c) < 2: continue
#         try:
#             res = analyze_hybrid_logic(c)
            
#             stats[res['sentiment'].lower()] += 1
#             # Toxicity Threshold 0.60
#             if res['toxicity'] > 0.60: stats['toxic_count'] += 1
            
#             if res['emotion'] in stats['emotion_counts']: 
#                 stats['emotion_counts'][res['emotion']] += 1
            
#             all_text += " " + c
#             if len(rich_data) < 60:
#                 rich_data.append({"text": c, "sentiment": res['sentiment'], "emotion": res['emotion']})
#         except: continue

#     # Keywords
#     words = re.findall(r'\b[a-z]{4,15}\b', all_text.lower())
#     stops = {'this','that','video','watch','just','have','your','with','from','like','good','very','what','when','time','make','know','about','best','love','people','content', 'please', 'thank', 'thanks'}
#     keywords = Counter([w for w in words if w not in stops]).most_common(12)

#     return {
#         "meta": {
#             "true_total": real_total_count,  # ACTUAL YOUTUBE COUNT
#             "analyzed_total": len(comments), # SAMPLE COUNT
#             "avg_len": int(len(all_text.split())/len(comments)) if comments else 0
#         },
#         "stats": stats,
#         "comments": rich_data,
#         "keywords": keywords
#     }

# @app.post("/summarize")
# def summarize_api(req: VideoRequest):
#     vid = extract_video_id(req.video_id)
#     try:
#         # --- FIX 3: BETTER TRANSCRIPT FETCHING ---
#         # Trying multiple languages including auto-generated ('a.en')
#         transcript = YouTubeTranscriptApi.get_transcript(vid, languages=['en', 'en-US', 'hi', 'a.en'])
#         text = " ".join([t['text'] for t in transcript])
        
#         if summarizer:
#             return {"summary": summarizer(text[:3000], max_length=150, min_length=40, do_sample=False)[0]['summary_text']}
#         return {"summary": "Summarizer Loading..."}
#     except Exception as e: 
#         print(f"Summary Error: {e}")
#         return {"summary": "⚠️ Summary unavailable (No suitable captions found)."}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=8000)





# import os
# import re
# import numpy as np
# import tensorflow as tf
# from collections import Counter
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from youtube_transcript_api import YouTubeTranscriptApi
# from transformers import pipeline, AutoTokenizer
# from googleapiclient.discovery import build
# from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# # --- CONFIGURATION ---
# os.environ["TF_USE_LEGACY_KERAS"] = "1"
# os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# # [APNI API KEY YAHAN HAI]
# YOUTUBE_API_KEY = "AIzaSyCDHZ2bHpEzp2bUMcguGn7vvi9-Rpigx6E"

# MODEL_PATH = "saved_models/youtube_intelligence_quantized.tflite"
# SUMMARIZER_MODEL_NAME = "sshleifer/distilbart-cnn-12-6"
# MAX_LEN = 64

# app = FastAPI(title="YT Intel Final Fix", version="8.0")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # --- GLOBAL VARS ---
# interpreter = None
# input_details = None
# output_details = None
# tokenizer = None
# summarizer = None
# vader = SentimentIntensityAnalyzer()
# yt_service = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# # --- STARTUP ---
# @app.on_event("startup")
# async def load_models():
#     global interpreter, input_details, output_details, tokenizer, summarizer
#     try:
#         if os.path.exists(MODEL_PATH):
#             interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
#             interpreter.allocate_tensors()
#             input_details = interpreter.get_input_details()
#             output_details = interpreter.get_output_details()
#             print("[SUCCESS] TFLite Loaded.")
#             tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
#         else:
#             print("[ERROR] TFLite Missing.")
#     except: pass

#     try:
#         print("[INFO] Loading Summarizer...")
#         summarizer = pipeline("summarization", model=SUMMARIZER_MODEL_NAME)
#         print("[SUCCESS] Summarizer Ready!")
#     except: pass

# class VideoRequest(BaseModel):
#     video_id: str

# # --- CORE LOGIC ---
# def extract_video_id(url: str):
#     if "v=" in url: return url.split("v=")[1].split("&")[0]
#     elif "youtu.be" in url: return url.split("/")[-1].split("?")[0]
#     return url

# def get_video_stats(video_id: str):
#     """Fetches REAL comment count from YouTube"""
#     try:
#         response = yt_service.videos().list(part="statistics", id=video_id).execute()
#         if response['items']:
#             return int(response['items'][0]['statistics']['commentCount'])
#     except: return 0

# def fetch_comments(video_id: str):
#     comments = []
#     try:
#         request = yt_service.commentThreads().list(part="snippet", videoId=video_id, maxResults=100, textFormat="plainText")
#         # Fetch up to 1000 comments for analysis sample
#         while request and len(comments) < 1000:
#             response = request.execute()
#             for item in response['items']:
#                 comments.append(item['snippet']['topLevelComment']['snippet']['textDisplay'])
#             request = yt_service.commentThreads().list_next(request, response)
#         return comments
#     except: return comments

# def analyze_logic(text: str):
#     # 1. VADER (The Boss of Sentiment)
#     vs = vader.polarity_scores(text)
#     compound = vs['compound']
    
#     # Thresholds (Balanced)
#     sent = "NEUTRAL"
#     if compound >= 0.05: sent = "POSITIVE"
#     elif compound <= -0.10: sent = "NEGATIVE" # Slightly relaxed negative
    
#     # 2. AI (The Boss of Emotion)
#     emo = "neutral"
#     tox_score = 0.0
    
#     if interpreter and tokenizer:
#         try:
#             encoded = tokenizer(text, max_length=MAX_LEN, padding='max_length', truncation=True, return_tensors='np')
#             interpreter.set_tensor(input_details[0]['index'], encoded['input_ids'].astype(np.int32))
#             interpreter.set_tensor(input_details[1]['index'], encoded['attention_mask'].astype(np.int32))
#             interpreter.invoke()
            
#             # Outputs
#             emo_probs = interpreter.get_tensor(output_details[1]['index'])[0]
#             tox_score = float(interpreter.get_tensor(output_details[2]['index'])[0][0])
            
#             # --- EMOTION FIX: SKIP NEUTRAL (Index 0) ---
#             # Hum index 1 se 6 tak check karenge (Fear se Disgust)
#             # Taaki result hamesha koi EMOTION hi ho.
#             labels = ['neutral', 'fear', 'anger', 'joy', 'surprise', 'sadness', 'disgust']
#             best_idx = np.argmax(emo_probs[1:]) + 1 
#             emo = labels[best_idx]
            
#         except: pass

#     # 3. FORCE LOGIC (The "Common Sense" Layer)
    
#     # Agar Sentiment Positive hai -> Force JOY/SURPRISE
#     if sent == "POSITIVE":
#         if emo in ['fear', 'anger', 'sadness', 'disgust', 'neutral']:
#             # Pick Joy or Surprise based on AI score, default Joy
#             emo = "joy"

#     # Agar Sentiment Negative hai -> Force ANGER/SADNESS
#     elif sent == "NEGATIVE":
#         if emo in ['joy', 'surprise', 'neutral']:
#             emo = "anger"

#     # 4. TOXICITY FIX (The 100% Killer)
#     # Toxic tabhi maano jab comment NEGATIVE ho AUR score High ho.
#     # Positive comment kabhi Toxic nahi ho sakta.
#     is_toxic = 0
#     if sent == "NEGATIVE" and tox_score > 0.85:
#         is_toxic = 1
    
#     return {"sentiment": sent, "emotion": emo, "toxicity": is_toxic}

# # --- API ENDPOINTS ---
# @app.post("/analyze")
# def analyze_api(req: VideoRequest):
#     vid = extract_video_id(req.video_id)
    
#     # 1. Get Real Count (Display ke liye)
#     real_total = get_video_stats(vid)
    
#     # 2. Get Analysis Sample (Graphs ke liye)
#     comments = fetch_comments(vid)
    
#     if not comments: return {"error": "No comments found."}

#     stats = { "positive": 0, "neutral": 0, "negative": 0, "toxic_count": 0, 
#               "emotion_counts": {k:0 for k in ['joy','surprise','sadness','anger','fear','disgust']} }
    
#     rich_data = []
#     all_text = ""

#     for c in comments:
#         if len(c) < 2: continue
#         try:
#             res = analyze_logic(c)
            
#             # Count Stats
#             stats[res['sentiment'].lower()] += 1
#             if res['toxicity'] == 1: stats['toxic_count'] += 1
            
#             # Emotion Count (Neutral skip kiya hai upar, to yahan safe hai)
#             if res['emotion'] in stats['emotion_counts']: 
#                 stats['emotion_counts'][res['emotion']] += 1
            
#             all_text += " " + c
#             if len(rich_data) < 60:
#                 rich_data.append({"text": c, "sentiment": res['sentiment'], "emotion": res['emotion']})
#         except: continue

#     # Keywords
#     words = re.findall(r'\b[a-z]{4,15}\b', all_text.lower())
#     stops = {'this','that','video','watch','just','have','your','with','from','like','good','very','what','when','time','make','know','about','best','love','people','content', 'please', 'thank', 'thanks', 'guys'}
#     keywords = Counter([w for w in words if w not in stops]).most_common(12)

#     # Fallback if API fails to get real count
#     final_total = real_total if real_total > 0 else len(comments)

#     return {
#         "meta": {
#             "total": final_total,          # Real Count (e.g. 28000)
#             "analyzed_total": len(comments), # Sample Count (e.g. 1000) - For Toxicity Calc
#             "avg_len": int(len(all_text.split())/len(comments)) if comments else 0
#         },
#         "stats": stats,
#         "comments": rich_data,
#         "keywords": keywords
#     }

# @app.post("/summarize")
# def summarize_api(req: VideoRequest):
#     vid = extract_video_id(req.video_id)
#     try:
#         # Try finding ANY caption (Manual or Auto)
#         transcript = YouTubeTranscriptApi.get_transcript(vid, languages=['en', 'en-US', 'hi', 'a.en', 'a.hi'])
#         text = " ".join([t['text'] for t in transcript])
        
#         if summarizer:
#             summary_text = summarizer(text[:3000], max_length=150, min_length=40, do_sample=False)[0]['summary_text']
#             return {"summary": summary_text}
#         return {"summary": "Summarizer Loading..."}
#     except Exception as e:
#         print(f"Summary Failed: {e}") 
#         return {"summary": "⚠️ No Captions/Subtitles found for this video."}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=8000)




# import os
# import re
# import numpy as np
# import tensorflow as tf
# from collections import Counter
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from youtube_transcript_api import YouTubeTranscriptApi
# from transformers import pipeline, AutoTokenizer
# from googleapiclient.discovery import build
# from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# # --- CONFIGURATION ---
# os.environ["TF_USE_LEGACY_KERAS"] = "1"
# os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# # [APNI API KEY YAHAN HAI]
# YOUTUBE_API_KEY = "AIzaSyCDHZ2bHpEzp2bUMcguGn7vvi9-Rpigx6E"

# MODEL_PATH = "saved_models/youtube_intelligence_quantized.tflite"
# SUMMARIZER_MODEL_NAME = "sshleifer/distilbart-cnn-12-6"
# MAX_LEN = 64

# app = FastAPI(title="YT Intel Final Fix", version="8.0")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # --- GLOBAL VARS ---
# interpreter = None
# input_details = None
# output_details = None
# tokenizer = None
# summarizer = None
# vader = SentimentIntensityAnalyzer()
# yt_service = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# # 🚀 NEW: POPULAR EMOJIS (For Emoji Cloud)
# POPULAR_EMOJIS = list("😂❤️🔥👍😍🙏😭😊✨🥰🤩🥺😎😁😘✅🎉💪😅💯👇💡🧠💀")

# # --- STARTUP ---
# @app.on_event("startup")
# async def load_models():
#     global interpreter, input_details, output_details, tokenizer, summarizer
#     try:
#         if os.path.exists(MODEL_PATH):
#             interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
#             interpreter.allocate_tensors()
#             input_details = interpreter.get_input_details()
#             output_details = interpreter.get_output_details()
#             print("[SUCCESS] TFLite Loaded.")
#             tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
#         else:
#             print("[ERROR] TFLite Missing.")
#     except: pass

#     try:
#         print("[INFO] Loading Summarizer...")
#         summarizer = pipeline("summarization", model=SUMMARIZER_MODEL_NAME)
#         print("[SUCCESS] Summarizer Ready!")
#     except: pass

# class VideoRequest(BaseModel):
#     video_id: str

# # --- CORE LOGIC ---
# def extract_video_id(url: str):
#     if "v=" in url: return url.split("v=")[1].split("&")[0]
#     elif "youtu.be" in url: return url.split("/")[-1].split("?")[0]
#     return url

# def get_video_stats(video_id: str):
#     """Fetches REAL comment count from YouTube"""
#     try:
#         response = yt_service.videos().list(part="statistics", id=video_id).execute()
#         if response['items']:
#             return int(response['items'][0]['statistics']['commentCount'])
#     except: return 0

# def fetch_comments(video_id: str):
#     comments = []
#     try:
#         request = yt_service.commentThreads().list(part="snippet", videoId=video_id, maxResults=100, textFormat="plainText")
#         # Fetch up to 1000 comments for analysis sample
#         while request and len(comments) < 1000:
#             response = request.execute()
#             for item in response['items']:
#                 comments.append(item['snippet']['topLevelComment']['snippet']['textDisplay'])
#             request = yt_service.commentThreads().list_next(request, response)
#         return comments
#     except: return comments

# def analyze_logic(text: str):
#     # 1. VADER (The Boss of Sentiment)
#     vs = vader.polarity_scores(text)
#     compound = vs['compound']
    
#     # Thresholds (Balanced)
#     sent = "NEUTRAL"
#     if compound >= 0.05: sent = "POSITIVE"
#     elif compound <= -0.10: sent = "NEGATIVE" # Slightly relaxed negative
    
#     # 2. AI (The Boss of Emotion)
#     emo = "neutral"
#     tox_score = 0.0
    
#     if interpreter and tokenizer:
#         try:
#             encoded = tokenizer(text, max_length=MAX_LEN, padding='max_length', truncation=True, return_tensors='np')
#             interpreter.set_tensor(input_details[0]['index'], encoded['input_ids'].astype(np.int32))
#             interpreter.set_tensor(input_details[1]['index'], encoded['attention_mask'].astype(np.int32))
#             interpreter.invoke()
            
#             # Outputs
#             emo_probs = interpreter.get_tensor(output_details[1]['index'])[0]
#             tox_score = float(interpreter.get_tensor(output_details[2]['index'])[0][0])
            
#             # --- EMOTION FIX: SKIP NEUTRAL (Index 0) ---
#             labels = ['neutral', 'fear', 'anger', 'joy', 'surprise', 'sadness', 'disgust']
#             best_idx = np.argmax(emo_probs[1:]) + 1 
#             emo = labels[best_idx]
            
#         except: pass

#     # 3. FORCE LOGIC (The "Common Sense" Layer)
#     if sent == "POSITIVE":
#         if emo in ['fear', 'anger', 'sadness', 'disgust', 'neutral']:
#             emo = "joy"

#     elif sent == "NEGATIVE":
#         if emo in ['joy', 'surprise', 'neutral']:
#             emo = "anger"

#     # 4. TOXICITY FIX (The 100% Killer)
#     is_toxic = 0
#     if sent == "NEGATIVE" and tox_score > 0.85:
#         is_toxic = 1
    
#     return {"sentiment": sent, "emotion": emo, "toxicity": is_toxic}

# # --- API ENDPOINTS ---
# @app.post("/analyze")
# def analyze_api(req: VideoRequest):
#     vid = extract_video_id(req.video_id)
    
#     real_total = get_video_stats(vid)
#     comments = fetch_comments(vid)
    
#     if not comments: return {"error": "No comments found."}

#     stats = { "positive": 0, "neutral": 0, "negative": 0, "toxic_count": 0, 
#               "emotion_counts": {k:0 for k in ['joy','surprise','sadness','anger','fear','disgust']} }
    
#     rich_data = []
#     all_text = ""
#     stops = {'this','that','video','watch','just','have','your','with','from','like','good','very','what','when','time','make','know','about','best','love','people','content', 'please', 'thank', 'thanks', 'guys', 'will', 'there', 'here', 'then'}

#     # 🚀 NEW: Deep Data Storage
#     intent_counts = {"question": 0, "appreciation": 0, "request": 0, "discussion": 0}
#     all_emojis = []
#     all_bigrams = []

#     for c in comments:
#         if len(c) < 2: continue
#         try:
#             res = analyze_logic(c)
            
#             stats[res['sentiment'].lower()] += 1
#             if res['toxicity'] == 1: stats['toxic_count'] += 1
            
#             if res['emotion'] in stats['emotion_counts']: 
#                 stats['emotion_counts'][res['emotion']] += 1
            
#             # 🚀 NEW: Deep Data Extraction
#             c_lower = c.lower()
            
#             # 1. Intent Extraction
#             if '?' in c or any(w in c_lower for w in ['how', 'why', 'what', 'when']):
#                 intent_counts['question'] += 1
#             elif any(w in c_lower for w in ['please', 'can you', 'help', 'request', 'make']):
#                 intent_counts['request'] += 1
#             elif res['sentiment'] == "POSITIVE" and any(w in c_lower for w in ['love', 'best', 'great', 'awesome', 'amazing', 'thank', '🔥', '❤️']):
#                 intent_counts['appreciation'] += 1
#             else:
#                 intent_counts['discussion'] += 1
                
#             # 2. Emoji Extraction
#             all_emojis.extend([ch for ch in c if ch in POPULAR_EMOJIS])
            
#             # 3. Bigram (Phrases) Extraction
#             c_words = re.findall(r'\b[a-z]{3,15}\b', c_lower)
#             c_filtered = [w for w in c_words if w not in stops]
#             if len(c_filtered) >= 2:
#                 for i in range(len(c_filtered)-1):
#                     all_bigrams.append(f"{c_filtered[i]} {c_filtered[i+1]}")

#             all_text += " " + c
#             if len(rich_data) < 60:
#                 rich_data.append({"text": c, "sentiment": res['sentiment'], "emotion": res['emotion']})
#         except: continue

#     # Keywords (For WordCloud)
#     words = re.findall(r'\b[a-z]{4,15}\b', all_text.lower())
#     keywords = Counter([w for w in words if w not in stops]).most_common(15)
    
#     # Phrases & Emojis
#     top_bigrams = Counter(all_bigrams).most_common(6)
#     top_emojis = Counter(all_emojis).most_common(8)

#     final_total = real_total if real_total > 0 else len(comments)

#     return {
#         "meta": {
#             "total": final_total,          
#             "analyzed_total": len(comments), 
#             "avg_len": int(len(all_text.split())/len(comments)) if comments else 0
#         },
#         "stats": stats,
#         "comments": rich_data,
#         "keywords": keywords,
#         "deep_data": { # 🚀 NEW: Passing Deep Data
#             "intents": intent_counts,
#             "bigrams": top_bigrams,
#             "emojis": top_emojis
#         }
#     }

# @app.post("/summarize")
# def summarize_api(req: VideoRequest):
#     vid = extract_video_id(req.video_id)
#     try:
#         transcript = YouTubeTranscriptApi.get_transcript(vid, languages=['en', 'en-US', 'hi', 'a.en', 'a.hi'])
#         text = " ".join([t['text'] for t in transcript])
        
#         if summarizer:
#             summary_text = summarizer(text[:3000], max_length=150, min_length=40, do_sample=False)[0]['summary_text']
#             return {"summary": summary_text}
#         return {"summary": "Summarizer Loading..."}
#     except Exception as e:
#         print(f"Summary Failed: {e}") 
#         return {"summary": "⚠️ No Captions/Subtitles found for this video."}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=8000)


# import os
# import re
# import numpy as np
# import tensorflow as tf
# from collections import Counter
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from youtube_transcript_api import YouTubeTranscriptApi
# from transformers import pipeline, AutoTokenizer
# from googleapiclient.discovery import build
# from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# # --- CONFIGURATION ---
# os.environ["TF_USE_LEGACY_KERAS"] = "1"
# os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# # [APNI API KEY YAHAN HAI]
# YOUTUBE_API_KEY = "AIzaSyCDHZ2bHpEzp2bUMcguGn7vvi9-Rpigx6E"

# MODEL_PATH = "saved_models/youtube_intelligence_quantized.tflite"
# SUMMARIZER_MODEL_NAME = "sshleifer/distilbart-cnn-12-6"
# MAX_LEN = 64

# app = FastAPI(title="YT Intel Final Emotion Logic", version="10.0")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # --- GLOBAL VARS ---
# interpreter = None
# input_details = None
# output_details = None
# tokenizer = None
# summarizer = None
# vader = SentimentIntensityAnalyzer()
# yt_service = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# # 🚀 POPULAR EMOJIS (For Emoji Cloud)
# POPULAR_EMOJIS = list("😂❤️🔥👍😍🙏😭😊✨🥰🤩🥺😎😁😘✅🎉💪😅💯👇💡🧠💀")

# # --- 🚀 NEW: EXACT EMOTION KEYWORDS (TUMHARI REQUIREMENT) ---
# KEYWORDS_JOY = ['love', 'best', 'great', 'awesome', 'amazing', 'good', 'thank', 'thanks', 'perfect', 'beautiful', 'nice', 'excellent', 'helpful', 'op', 'fire', '🔥', '❤️', 'haha', '😂', 'lol', 'masterpiece']
# KEYWORDS_ANGER = ['bad', 'worst', 'hate', 'stupid', 'fake', 'scam', 'boring', 'trash', 'useless', 'dislike', 'shame', 'angry', 'mad', 'bullshit', 'terrible', 'garbage']
# KEYWORDS_SURPRISE = ['wow', 'omg', 'really', 'what', 'unbelievable', 'crazy', 'shocking', 'damn', 'surprised', 'insane', 'unexpected']
# KEYWORDS_SADNESS = ['sad', 'sorry', 'miss', 'cry', 'pain', 'rip', 'hurt', 'sadly', '😭', 'broken', 'heartbreak']
# KEYWORDS_FEAR = ['scared', 'scary', 'fear', 'terrifying', 'creepy', 'afraid', 'horror', 'panic', 'nightmare']
# KEYWORDS_DISGUST = ['gross', 'disgusting', 'eww', 'vomit', 'cringe', 'awful', 'sick', 'nasty', 'weird']

# def get_emotion_from_keywords(text_lower):
#     # Word check karega aur direct emotion dega
#     for w in KEYWORDS_JOY:
#         if w in text_lower: return "joy"
#     for w in KEYWORDS_ANGER:
#         if w in text_lower: return "anger"
#     for w in KEYWORDS_SURPRISE:
#         if w in text_lower: return "surprise"
#     for w in KEYWORDS_SADNESS:
#         if w in text_lower: return "sadness"
#     for w in KEYWORDS_FEAR:
#         if w in text_lower: return "fear"
#     for w in KEYWORDS_DISGUST:
#         if w in text_lower: return "disgust"
#     return None

# # --- STARTUP ---
# @app.on_event("startup")
# async def load_models():
#     global interpreter, input_details, output_details, tokenizer, summarizer
#     try:
#         if os.path.exists(MODEL_PATH):
#             interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
#             interpreter.allocate_tensors()
#             input_details = interpreter.get_input_details()
#             output_details = interpreter.get_output_details()
#             print("[SUCCESS] TFLite Loaded.")
#             tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
#         else:
#             print("[ERROR] TFLite Missing.")
#     except Exception as e:
#         print(f"[ERROR] TFLite Error: {e}")

#     try:
#         print("[INFO] Loading Summarizer...")
#         summarizer = pipeline("summarization", model=SUMMARIZER_MODEL_NAME, framework="tf")
#         print("[SUCCESS] Summarizer Ready!")
#     except Exception as e: 
#         print(f"[ERROR] Summarizer Failed: {e}")

# class VideoRequest(BaseModel):
#     video_id: str

# # --- CORE LOGIC ---
# def extract_video_id(url: str):
#     if "v=" in url: return url.split("v=")[1].split("&")[0]
#     elif "youtu.be" in url: return url.split("/")[-1].split("?")[0]
#     return url

# def get_video_stats(video_id: str):
#     try:
#         response = yt_service.videos().list(part="statistics", id=video_id).execute()
#         if response['items']:
#             return int(response['items'][0]['statistics']['commentCount'])
#     except: return 0

# def fetch_comments(video_id: str):
#     comments = []
#     try:
#         request = yt_service.commentThreads().list(part="snippet", videoId=video_id, maxResults=100, textFormat="plainText")
#         while request and len(comments) < 1000:
#             response = request.execute()
#             for item in response['items']:
#                 comments.append(item['snippet']['topLevelComment']['snippet']['textDisplay'])
#             request = yt_service.commentThreads().list_next(request, response)
#         return comments
#     except: return comments

# def analyze_logic(text: str):
#     # 1. 🛡️ SENTIMENT (BILKUL UNTOUCHED - TUMHARA PERFECT LOGIC)
#     vs = vader.polarity_scores(text)
#     compound = vs['compound']
    
#     sent = "NEUTRAL"
#     if compound >= 0.05: sent = "POSITIVE"
#     elif compound <= -0.10: sent = "NEGATIVE"
    
#     # 2. 🧠 AI EMOTION 
#     emo_ai = "surprise" # Base default fallback
#     tox_score = 0.0
    
#     if interpreter and tokenizer:
#         try:
#             encoded = tokenizer(text, max_length=MAX_LEN, padding='max_length', truncation=True, return_tensors='np')
#             interpreter.set_tensor(input_details[0]['index'], encoded['input_ids'].astype(np.int32))
#             interpreter.set_tensor(input_details[1]['index'], encoded['attention_mask'].astype(np.int32))
#             interpreter.invoke()
            
#             emo_probs = interpreter.get_tensor(output_details[1]['index'])[0]
#             tox_score = float(interpreter.get_tensor(output_details[2]['index'])[0][0])
            
#             # Skip Neutral (Index 0) to force true emotion
#             labels = ['neutral', 'fear', 'anger', 'joy', 'surprise', 'sadness', 'disgust']
#             best_idx = np.argmax(emo_probs[1:]) + 1 
#             emo_ai = labels[best_idx]
#         except: pass

#     # 3. 🎯 NEW: KEYWORD OVERRIDE (Word based strong emotion)
#     text_lower = text.lower()
#     keyword_emo = get_emotion_from_keywords(text_lower)
    
#     # Agar keyword mila, to wahi emotion lagao. Nahi to AI wala lagao.
#     final_emo = keyword_emo if keyword_emo else emo_ai

#     # 4. CONFLICT RESOLUTION (Taaki Mismatch na ho)
#     if sent == "POSITIVE":
#         if final_emo not in ['joy', 'surprise']: final_emo = "joy"
#     elif sent == "NEGATIVE":
#         if final_emo not in ['fear', 'anger', 'sadness', 'disgust']: final_emo = "anger"
    
#     # Agar Sentiment NEUTRAL hai, to final_emo ko disturb mat karo (It will show Joy, Surprise, etc. correctly!)

#     # 5. TOXICITY
#     is_toxic = 0
#     if sent == "NEGATIVE" and tox_score > 0.85:
#         is_toxic = 1
    
#     return {"sentiment": sent, "emotion": final_emo, "toxicity": is_toxic}

# # --- API ENDPOINTS ---
# @app.post("/analyze")
# def analyze_api(req: VideoRequest):
#     vid = extract_video_id(req.video_id)
    
#     real_total = get_video_stats(vid)
#     comments = fetch_comments(vid)
    
#     if not comments: return {"error": "No comments found."}

#     stats = { "positive": 0, "neutral": 0, "negative": 0, "toxic_count": 0, 
#               "emotion_counts": {k:0 for k in ['joy','surprise','sadness','anger','fear','disgust']} }
    
#     rich_data = []
#     all_text = ""
    
#     intent_counts = {"question": 0, "appreciation": 0, "request": 0, "discussion": 0}
#     all_emojis = []
#     all_bigrams = []
#     stops = {'this','that','video','watch','just','have','your','with','from','like','good','very','what','when','time','make','know','about','best','love','people','content', 'please', 'thank', 'thanks', 'guys', 'will', 'there', 'here', 'then'}

#     for c in comments:
#         if len(c) < 2: continue
#         try:
#             res = analyze_logic(c)
            
#             # Count Stats
#             stats[res['sentiment'].lower()] += 1
#             if res['toxicity'] == 1: stats['toxic_count'] += 1
            
#             if res['emotion'] in stats['emotion_counts']: 
#                 stats['emotion_counts'][res['emotion']] += 1
            
#             c_lower = c.lower()
#             if '?' in c or any(w in c_lower for w in ['how', 'why', 'what', 'when']):
#                 intent_counts['question'] += 1
#             elif any(w in c_lower for w in ['please', 'can you', 'help', 'request', 'make']):
#                 intent_counts['request'] += 1
#             elif res['sentiment'] == "POSITIVE" and any(w in c_lower for w in ['love', 'best', 'great', 'awesome', 'amazing', 'thank', '🔥', '❤️']):
#                 intent_counts['appreciation'] += 1
#             else:
#                 intent_counts['discussion'] += 1
                
#             all_emojis.extend([ch for ch in c if ch in POPULAR_EMOJIS])
            
#             c_words = re.findall(r'\b[a-z]{3,15}\b', c_lower)
#             c_filtered = [w for w in c_words if w not in stops]
#             if len(c_filtered) >= 2:
#                 for i in range(len(c_filtered)-1):
#                     all_bigrams.append(f"{c_filtered[i]} {c_filtered[i+1]}")

#             all_text += " " + c
#             if len(rich_data) < 60:
#                 rich_data.append({"text": c, "sentiment": res['sentiment'], "emotion": res['emotion']})
#         except: continue

#     words = re.findall(r'\b[a-z]{4,15}\b', all_text.lower())
#     keywords = Counter([w for w in words if w not in stops]).most_common(20)
    
#     top_bigrams = Counter(all_bigrams).most_common(6)
#     top_emojis = Counter(all_emojis).most_common(8)

#     final_total = real_total if real_total > 0 else len(comments)

#     return {
#         "meta": {
#             "total": final_total,
#             "analyzed_total": len(comments),
#             "avg_len": int(len(all_text.split())/len(comments)) if comments else 0
#         },
#         "stats": stats,
#         "comments": rich_data,
#         "keywords": keywords,
#         "deep_data": { 
#             "intents": intent_counts,
#             "bigrams": top_bigrams,
#             "emojis": top_emojis
#         }
#     }

# @app.post("/summarize")
# def summarize_api(req: VideoRequest):
#     vid = extract_video_id(req.video_id)
#     try:
#         try:
#             transcript = YouTubeTranscriptApi.get_transcript(vid, languages=['en', 'en-US', 'hi', 'a.en'])
#             text = " ".join([t['text'] for t in transcript])
#         except:
#             return {"summary": "⚠️ Summary unavailable: No Subtitles found."}
        
#         if summarizer:
#             try:
#                 safe_text = text[:2500]
#                 summary_text = summarizer(safe_text, max_length=130, min_length=30, do_sample=False)[0]['summary_text']
#                 return {"summary": summary_text}
#             except Exception as ai_err:
#                 print(f"[SUMMARY ERROR]: {ai_err}")
#                 return {"summary": "⚠️ AI Summarizer failed on this video."}
#         else:
#             return {"summary": "⚠️ Model Loading... Please try again."}
            
#     except Exception as e:
#         return {"summary": f"⚠️ Error: {str(e)[:50]}"}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=8000)




# import os
# import re
# import numpy as np
# import tensorflow as tf
# from collections import Counter
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from youtube_transcript_api import YouTubeTranscriptApi
# from transformers import pipeline, AutoTokenizer
# from googleapiclient.discovery import build
# from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# os.environ["TF_USE_LEGACY_KERAS"] = "1"
# os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# YOUTUBE_API_KEY = "AIzaSyCDHZ2bHpEzp2bUMcguGn7vvi9-Rpigx6E"

# MODEL_PATH = "saved_models/youtube_intelligence_quantized.tflite"
# SUMMARIZER_MODEL_NAME = "sshleifer/distilbart-cnn-12-6"
# MAX_LEN = 64

# app = FastAPI(title="YT Intel Final Emotion Logic", version="10.0")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# interpreter = None
# input_details = None
# output_details = None
# tokenizer = None
# summarizer = None
# vader = SentimentIntensityAnalyzer()
# yt_service = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# POPULAR_EMOJIS = list("😂❤️🔥👍😍🙏😭😊✨🥰🤩🥺😎😁😘✅🎉💪😅💯👇💡🧠💀")

# KEYWORDS_JOY = ['love', 'best', 'great', 'awesome', 'amazing', 'good', 'thank', 'thanks', 'perfect', 'beautiful', 'nice', 'excellent', 'helpful', 'op', 'fire', '🔥', '❤️', 'haha', '😂', 'lol', 'masterpiece']
# KEYWORDS_ANGER = ['bad', 'worst', 'hate', 'stupid', 'fake', 'scam', 'boring', 'trash', 'useless', 'dislike', 'shame', 'angry', 'mad', 'bullshit', 'terrible', 'garbage']
# KEYWORDS_SURPRISE = ['wow', 'omg', 'really', 'what', 'unbelievable', 'crazy', 'shocking', 'damn', 'surprised', 'insane', 'unexpected']
# KEYWORDS_SADNESS = ['sad', 'sorry', 'miss', 'cry', 'pain', 'rip', 'hurt', 'sadly', '😭', 'broken', 'heartbreak']
# KEYWORDS_FEAR = ['scared', 'scary', 'fear', 'terrifying', 'creepy', 'afraid', 'horror', 'panic', 'nightmare']
# KEYWORDS_DISGUST = ['gross', 'disgusting', 'eww', 'vomit', 'cringe', 'awful', 'sick', 'nasty', 'weird']

# def get_emotion_from_keywords(text_lower):
#     for w in KEYWORDS_JOY:
#         if w in text_lower: return "joy"
#     for w in KEYWORDS_ANGER:
#         if w in text_lower: return "anger"
#     for w in KEYWORDS_SURPRISE:
#         if w in text_lower: return "surprise"
#     for w in KEYWORDS_SADNESS:
#         if w in text_lower: return "sadness"
#     for w in KEYWORDS_FEAR:
#         if w in text_lower: return "fear"
#     for w in KEYWORDS_DISGUST:
#         if w in text_lower: return "disgust"
#     return None

# @app.on_event("startup")
# async def load_models():
#     global interpreter, input_details, output_details, tokenizer, summarizer
#     try:
#         if os.path.exists(MODEL_PATH):
#             interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
#             interpreter.allocate_tensors()
#             input_details = interpreter.get_input_details()
#             output_details = interpreter.get_output_details()
#             print("[SUCCESS] TFLite Loaded.")
#             tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
#         else:
#             print("TFLite Missing.")
#     except Exception as e:
#         print(f"TFLite Error: {e}")

#     try:
#         print("Loading Summarizer...")
#         summarizer = pipeline("summarization", model=SUMMARIZER_MODEL_NAME, framework="tf", model_kwargs={"from_pt": True})
#         print("Summarizer Ready!")
#     except Exception as e: 
#         print(f"Summarizer Failed: {e}")

# class VideoRequest(BaseModel):
#     video_id: str

# def extract_video_id(url: str):
#     if "v=" in url: 
#         return url.split("v=")[1].split("&")[0]
#     elif "youtu.be/" in url: 
#         return url.split("youtu.be/")[1].split("?")[0]
#     elif "/live/" in url:
#         return url.split("/live/")[1].split("?")[0]
#     elif "/shorts/" in url:
#         return url.split("/shorts/")[1].split("?")[0]
    
#     match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
#     if match: return match.group(1)
    
#     return url

# def get_video_stats(video_id: str):
#     try:
#         response = yt_service.videos().list(part="statistics", id=video_id).execute()
#         if response['items']:
#             return int(response['items'][0]['statistics']['commentCount'])
#     except: return 0

# def fetch_comments(video_id: str):
#     comments = []
#     try:
#         request = yt_service.commentThreads().list(part="snippet", videoId=video_id, maxResults=100, textFormat="plainText")
#         while request and len(comments) < 1000:
#             response = request.execute()
#             for item in response['items']:
#                 comments.append(item['snippet']['topLevelComment']['snippet']['textDisplay'])
#             request = yt_service.commentThreads().list_next(request, response)
#         return comments
#     except: return comments

# def analyze_logic(text: str):
#     vs = vader.polarity_scores(text)
#     compound = vs['compound']
    
#     sent = "NEUTRAL"
#     if compound >= 0.05: sent = "POSITIVE"
#     elif compound <= -0.10: sent = "NEGATIVE"
    
#     emo_ai = "neutral"
#     tox_score = 0.0
    
#     if interpreter and tokenizer:
#         try:
#             encoded = tokenizer(text, max_length=MAX_LEN, padding='max_length', truncation=True, return_tensors='np')
#             interpreter.set_tensor(input_details[0]['index'], encoded['input_ids'].astype(np.int32))
#             interpreter.set_tensor(input_details[1]['index'], encoded['attention_mask'].astype(np.int32))
#             interpreter.invoke()
            
#             emo_probs = interpreter.get_tensor(output_details[1]['index'])[0]
#             tox_score = float(interpreter.get_tensor(output_details[2]['index'])[0][0])
            
#             labels = ['neutral', 'fear', 'anger', 'joy', 'surprise', 'sadness', 'disgust']
#             best_idx = np.argmax(emo_probs[1:]) + 1 
#             emo_ai = labels[best_idx]
#         except: pass

#     text_lower = text.lower()
#     keyword_emo = get_emotion_from_keywords(text_lower)
#     final_emo = keyword_emo if keyword_emo else emo_ai

#     if sent == "POSITIVE":
#         if final_emo not in ['joy', 'surprise']: final_emo = "joy"
#     elif sent == "NEGATIVE":
#         if final_emo not in ['fear', 'anger', 'sadness', 'disgust']: final_emo = "anger"
    
#     is_toxic = 0
#     if sent == "NEGATIVE" and tox_score > 0.85:
#         is_toxic = 1
    
#     return {"sentiment": sent, "emotion": final_emo, "toxicity": is_toxic}

# @app.post("/analyze")
# def analyze_api(req: VideoRequest):
#     vid = extract_video_id(req.video_id)
#     real_total = get_video_stats(vid)
#     comments = fetch_comments(vid)
    
#     if not comments: return {"error": "No comments found."}

#     stats = { "positive": 0, "neutral": 0, "negative": 0, "toxic_count": 0, 
#               "emotion_counts": {k:0 for k in ['joy','surprise','sadness','anger','fear','disgust']} }
#     rich_data = []
#     all_text = ""
#     intent_counts = {"question": 0, "appreciation": 0, "request": 0, "discussion": 0}
#     all_emojis = []
#     all_bigrams = []
#     stops = {'this','that','video','watch','just','have','your','with','from','like','good','very','what','when','time','make','know','about','best','love','people','content', 'please', 'thank', 'thanks', 'guys', 'will', 'there', 'here', 'then'}

#     for c in comments:
#         if len(c) < 2: continue
#         try:
#             res = analyze_logic(c)
#             stats[res['sentiment'].lower()] += 1
#             if res['toxicity'] == 1: stats['toxic_count'] += 1
#             if res['emotion'] in stats['emotion_counts']: stats['emotion_counts'][res['emotion']] += 1
            
#             c_lower = c.lower()
#             if '?' in c or any(w in c_lower for w in ['how', 'why', 'what', 'when']): intent_counts['question'] += 1
#             elif any(w in c_lower for w in ['please', 'can you', 'help', 'request', 'make']): intent_counts['request'] += 1
#             elif res['sentiment'] == "POSITIVE" and any(w in c_lower for w in ['love', 'best', 'great', 'awesome', 'amazing', 'thank', '🔥', '❤️']): intent_counts['appreciation'] += 1
#             else: intent_counts['discussion'] += 1
                
#             all_emojis.extend([ch for ch in c if ch in POPULAR_EMOJIS])
#             c_words = re.findall(r'\b[a-z]{3,15}\b', c_lower)
#             c_filtered = [w for w in c_words if w not in stops]
#             if len(c_filtered) >= 2:
#                 for i in range(len(c_filtered)-1): all_bigrams.append(f"{c_filtered[i]} {c_filtered[i+1]}")

#             all_text += " " + c
#             if len(rich_data) < 60:
#                 rich_data.append({"text": c, "sentiment": res['sentiment'], "emotion": res['emotion']})
#         except: continue

#     words = re.findall(r'\b[a-z]{4,15}\b', all_text.lower())
#     keywords = Counter([w for w in words if w not in stops]).most_common(20)
#     top_bigrams = Counter(all_bigrams).most_common(6)
#     top_emojis = Counter(all_emojis).most_common(8)

#     final_total = real_total if real_total > 0 else len(comments)

#     return {
#         "meta": {
#             "total": final_total,
#             "analyzed_total": len(comments),
#             "avg_len": int(len(all_text.split())/len(comments)) if comments else 0
#         },
#         "stats": stats,
#         "comments": rich_data,
#         "keywords": keywords,
#         "deep_data": { 
#             "intents": intent_counts,
#             "bigrams": top_bigrams,
#             "emojis": top_emojis
#         }
#     }

# # @app.post("/summarize")
# # def summarize_api(req: VideoRequest):
# #     vid = extract_video_id(req.video_id)
# #     try:
# #         comments = fetch_comments(vid)
# #         if not comments:
# #             return {"summary": "No comments available to analyze.", "demands": []}

# #         demand_keywords = [
# #             'please make', 'we want', 'next part', 'tutorial on', 
# #             'can you', 'upload', 'demand', 'make a video', 
# #             'waiting for', 'bring', 'we need', 'how to'
# #         ]
        
# #         found_demands = []
# #         for c in comments:
# #             c_lower = c.lower()
# #             # Check if keyword exists and comment is not just a single word
# #             if any(k in c_lower for k in demand_keywords) and len(c) > 15:
# #                 # Clean up the text for UI display
# #                 clean_comment = c.replace('\n', ' ').strip()
# #                 if clean_comment not in found_demands:
# #                     found_demands.append(clean_comment)
                
# #                 # Top 3 demands hi lenge taaki UI clean rahe
# #                 if len(found_demands) >= 3: 
# #                     break

# #         top_comments_text = " ".join(comments[:50])
        
# #         summary_text = "Discussion analysis unavailable."
# #         if summarizer:
# #             try:
# #                 safe_text = top_comments_text[:2500] 
# #                 result = summarizer(safe_text, max_length=90, min_length=20, do_sample=False)
# #                 summary_text = result[0]['summary_text']
# #             except Exception as ai_err:
# #                 print(f"[AI SUMMARY ERROR]: {ai_err}")
# #                 summary_text = "AI could not generate a summary from these comments."

# #         return {
# #             "summary": summary_text,
# #             "demands": found_demands
# #         }
        
# #     except Exception as e:
# #         return {"summary": f"⚠️ Error analyzing demands: {str(e)[:50]}", "demands": []}
    
# @app.post("/summarize")
# def summarize_api(req: VideoRequest):
#     vid = extract_video_id(req.video_id)
#     try:
#         comments = fetch_comments(vid)
#         if not comments:
#             return {"summary": "No comments available to analyze.", "demands": []}

#         demand_keywords = [
#             'please make', 'we want', 'next part', 'tutorial on', 
#             'can you', 'upload', 'demand', 'make a video', 
#             'waiting for', 'bring', 'we need', 'how to'
#         ]
        
#         found_demands = []
#         for c in comments:
#             c_lower = c.lower()
#             if any(k in c_lower for k in demand_keywords) and len(c) > 15:
#                 clean_comment = c.replace('\n', ' ').strip()
#                 if clean_comment not in found_demands:
#                     found_demands.append(clean_comment)
#                 if len(found_demands) >= 3: 
#                     break

#         statement_comments = [c for c in comments[:80] if len(c) > 30 and "?" not in c]
#         if not statement_comments:
#             statement_comments = comments[:50] # Fallback
            
#         top_comments_text = " ".join(statement_comments).replace('\n', ' ')
        
#         summary_text = "Discussion analysis unavailable."
#         if summarizer:
#             try:
#                 safe_text = top_comments_text[:3000] 
                
#                 result = summarizer(safe_text, max_length=150, min_length=50, do_sample=False)
#                 raw_summary = result[0]['summary_text']
                
#                 summary_text = f"Based on the discussions, the audience is primarily focusing on: {raw_summary.capitalize()}"
                
#             except Exception as ai_err:
#                 print(f"[AI SUMMARY ERROR]: {ai_err}")
#                 summary_text = "AI could not generate an overview from these comments."

#         return {
#             "summary": summary_text,
#             "demands": found_demands
#         }
        
#     except Exception as e:
#         return {"summary": f"Error analyzing overview: {str(e)[:50]}", "demands": []}
    
    
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=8000)




# import os
# import re
# import numpy as np
# import tensorflow as tf
# from collections import Counter
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from youtube_transcript_api import YouTubeTranscriptApi
# from transformers import pipeline, AutoTokenizer
# from googleapiclient.discovery import build
# from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# os.environ["TF_USE_LEGACY_KERAS"] = "1"
# os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# YOUTUBE_API_KEY = "AIzaSyCDHZ2bHpEzp2bUMcguGn7vvi9-Rpigx6E"

# MODEL_PATH = "saved_models/youtube_intelligence_quantized.tflite"
# SUMMARIZER_MODEL_NAME = "sshleifer/distilbart-cnn-12-6"
# MAX_LEN = 64

# app = FastAPI(title="YT Intel Final Emotion Logic", version="10.0")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# interpreter = None
# input_details = None
# output_details = None
# tokenizer = None
# summarizer = None
# vader = SentimentIntensityAnalyzer()
# yt_service = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# POPULAR_EMOJIS = list("😂❤️🔥👍😍🙏😭😊✨🥰🤩🥺😎😁😘✅🎉💪😅💯👇💡🧠💀")

# KEYWORDS_JOY = ['awesome', 'amazing', 'masterpiece', 'excellent', 'perfect', 'beautiful', 'helpful', '🔥', '❤️']
# KEYWORDS_ANGER = ['bad', 'worst', 'hate', 'stupid', 'fake', 'scam', 'boring', 'trash', 'useless', 'dislike', 'shame', 'angry', 'mad', 'bullshit', 'terrible', 'garbage']
# KEYWORDS_SURPRISE = ['wow', 'omg', 'really', 'what', 'unbelievable', 'crazy', 'shocking', 'damn', 'surprised', 'insane', 'unexpected']
# KEYWORDS_SADNESS = ['sad', 'sorry', 'miss', 'cry', 'pain', 'rip', 'hurt', 'sadly', '😭', 'broken', 'heartbreak']
# KEYWORDS_FEAR = ['scared', 'scary', 'fear', 'terrifying', 'creepy', 'afraid', 'horror', 'panic', 'nightmare']
# KEYWORDS_DISGUST = ['gross', 'disgusting', 'eww', 'vomit', 'cringe', 'awful', 'sick', 'nasty', 'weird']

# def get_emotion_from_keywords(text_lower):
#     for w in KEYWORDS_JOY:
#         if w in text_lower: return "joy"
#     for w in KEYWORDS_ANGER:
#         if w in text_lower: return "anger"
#     for w in KEYWORDS_SURPRISE:
#         if w in text_lower: return "surprise"
#     for w in KEYWORDS_SADNESS:
#         if w in text_lower: return "sadness"
#     for w in KEYWORDS_FEAR:
#         if w in text_lower: return "fear"
#     for w in KEYWORDS_DISGUST:
#         if w in text_lower: return "disgust"
#     return None

# @app.on_event("startup")
# async def load_models():
#     global interpreter, input_details, output_details, tokenizer, summarizer
#     try:
#         if os.path.exists(MODEL_PATH):
#             interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
#             interpreter.allocate_tensors()
#             input_details = interpreter.get_input_details()
#             output_details = interpreter.get_output_details()
#             print("[SUCCESS] TFLite Loaded.")
#             tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
#         else:
#             print("TFLite Missing.")
#     except Exception as e:
#         print(f"TFLite Error: {e}")

#     try:
#         print("Loading Summarizer...")
#         summarizer = pipeline("summarization", model=SUMMARIZER_MODEL_NAME, framework="tf", model_kwargs={"from_pt": True})
#         print("Summarizer Ready!")
#     except Exception as e: 
#         print(f"Summarizer Failed: {e}")

# class VideoRequest(BaseModel):
#     video_id: str

# def extract_video_id(url: str):
#     if "v=" in url: 
#         return url.split("v=")[1].split("&")[0]
#     elif "youtu.be/" in url: 
#         return url.split("youtu.be/")[1].split("?")[0]
#     elif "/live/" in url:
#         return url.split("/live/")[1].split("?")[0]
#     elif "/shorts/" in url:
#         return url.split("/shorts/")[1].split("?")[0]
    
#     match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
#     if match: return match.group(1)
    
#     return url

# def get_video_stats(video_id: str):
#     try:
#         response = yt_service.videos().list(part="statistics", id=video_id).execute()
#         if response['items']:
#             return int(response['items'][0]['statistics']['commentCount'])
#     except: return 0

# def fetch_comments(video_id: str):
#     comments = []
#     try:
#         request = yt_service.commentThreads().list(part="snippet", videoId=video_id, maxResults=100, textFormat="plainText")
#         while request and len(comments) < 1000:
#             response = request.execute()
#             for item in response['items']:
#                 comments.append(item['snippet']['topLevelComment']['snippet']['textDisplay'])
#             request = yt_service.commentThreads().list_next(request, response)
#         return comments
#     except: return comments


# def analyze_logic(text: str):
#     vs = vader.polarity_scores(text)
#     compound = vs['compound']
    
#     sent = "NEUTRAL"
#     if compound >= 0.05: sent = "POSITIVE"
#     elif compound <= -0.10: sent = "NEGATIVE"
    
#     emo_ai = "neutral"
#     tox_score = 0.0
    
#     if interpreter and tokenizer:
#         try:
#             encoded = tokenizer(text, max_length=MAX_LEN, padding='max_length', truncation=True, return_tensors='np')
#             interpreter.set_tensor(input_details[0]['index'], encoded['input_ids'].astype(np.int32))
#             interpreter.set_tensor(input_details[1]['index'], encoded['attention_mask'].astype(np.int32))
#             interpreter.invoke()
            
#             emo_probs = interpreter.get_tensor(output_details[1]['index'])[0].copy()
#             tox_score = float(interpreter.get_tensor(output_details[2]['index'])[0][0])
            
#             labels = ['neutral', 'fear', 'anger', 'joy', 'surprise', 'sadness', 'disgust']
            
#             emo_probs[1] *= 1.8 
#             emo_probs[2] *= 1.8  
#             emo_probs[3] *= 0.5  
#             emo_probs[4] *= 1.0  
#             emo_probs[5] *= 1.8  
#             emo_probs[6] *= 1.4  
#             emo_probs[0] *= 0.3  
            
#             best_idx = np.argmax(emo_probs)
#             emo_ai = labels[best_idx]
#         except: pass

#     text_lower = text.lower()
#     keyword_emo = get_emotion_from_keywords(text_lower)
#     final_emo = keyword_emo if keyword_emo else emo_ai

#     if final_emo == "neutral":
#         if compound >= 0.35: final_emo = "joy"
#         elif compound <= -0.35: final_emo = "anger"
    
#     is_toxic = 0
#     if sent == "NEGATIVE" and tox_score > 0.85:
#         is_toxic = 1
    
#     return {"sentiment": sent, "emotion": final_emo, "toxicity": is_toxic}


# @app.post("/analyze")
# def analyze_api(req: VideoRequest):
#     vid = extract_video_id(req.video_id)
#     real_total = get_video_stats(vid)
#     comments = fetch_comments(vid)
    
#     if not comments: return {"error": "No comments found."}

#     stats = { "positive": 0, "neutral": 0, "negative": 0, "toxic_count": 0, 
#               "emotion_counts": {k:0 for k in ['joy','surprise','sadness','anger','fear','disgust']} }
#     rich_data = []
#     all_text = ""
#     intent_counts = {"question": 0, "appreciation": 0, "request": 0, "discussion": 0}
#     all_emojis = []
#     all_bigrams = []
#     stops = {'this','that','video','watch','just','have','your','with','from','like','good','very','what','when','time','make','know','about','best','love','people','content', 'please', 'thank', 'thanks', 'guys', 'will', 'there', 'here', 'then'}

#     for c in comments:
#         if len(c) < 2: continue
#         try:
#             res = analyze_logic(c)
#             stats[res['sentiment'].lower()] += 1
#             if res['toxicity'] == 1: stats['toxic_count'] += 1
            
#             if res['emotion'] in stats['emotion_counts']: 
#                 stats['emotion_counts'][res['emotion']] += 1
            
#             c_lower = c.lower()
#             if '?' in c or any(w in c_lower for w in ['how', 'why', 'what', 'when']): intent_counts['question'] += 1
#             elif any(w in c_lower for w in ['please', 'can you', 'help', 'request', 'make']): intent_counts['request'] += 1
#             elif res['sentiment'] == "POSITIVE" and any(w in c_lower for w in ['love', 'best', 'great', 'awesome', 'amazing', 'thank', '🔥', '❤️']): intent_counts['appreciation'] += 1
#             else: intent_counts['discussion'] += 1
                
#             all_emojis.extend([ch for ch in c if ch in POPULAR_EMOJIS])
#             c_words = re.findall(r'\b[a-z]{3,15}\b', c_lower)
#             c_filtered = [w for w in c_words if w not in stops]
#             if len(c_filtered) >= 2:
#                 for i in range(len(c_filtered)-1): all_bigrams.append(f"{c_filtered[i]} {c_filtered[i+1]}")

#             all_text += " " + c
#             if len(rich_data) < 60:
#                 rich_data.append({"text": c, "sentiment": res['sentiment'], "emotion": res['emotion']})
#         except: continue

#     words = re.findall(r'\b[a-z]{4,15}\b', all_text.lower())
#     keywords = Counter([w for w in words if w not in stops]).most_common(20)
#     top_bigrams = Counter(all_bigrams).most_common(6)
#     top_emojis = Counter(all_emojis).most_common(8)

#     final_total = real_total if real_total > 0 else len(comments)

#     return {
#         "meta": {
#             "total": final_total,
#             "analyzed_total": len(comments),
#             "avg_len": int(len(all_text.split())/len(comments)) if comments else 0
#         },
#         "stats": stats,
#         "comments": rich_data,
#         "keywords": keywords,
#         "deep_data": { 
#             "intents": intent_counts,
#             "bigrams": top_bigrams,
#             "emojis": top_emojis
#         }
#     }
    
# @app.post("/summarize")
# def summarize_api(req: VideoRequest):
#     vid = extract_video_id(req.video_id)
#     try:
#         comments = fetch_comments(vid)
#         if not comments:
#             return {"summary": "No comments available to analyze.", "demands": []}

#         demand_keywords = [
#             'please make', 'we want', 'next part', 'tutorial on', 
#             'can you', 'upload', 'demand', 'make a video', 
#             'waiting for', 'bring', 'we need', 'how to'
#         ]
        
#         found_demands = []
#         for c in comments:
#             c_lower = c.lower()
#             if any(k in c_lower for k in demand_keywords) and len(c) > 15:
#                 clean_comment = c.replace('\n', ' ').strip()
#                 if clean_comment not in found_demands:
#                     found_demands.append(clean_comment)
#                 if len(found_demands) >= 3: 
#                     break

#         statement_comments = [c for c in comments[:80] if len(c) > 30 and "?" not in c]
#         if not statement_comments:
#             statement_comments = comments[:50] # Fallback
            
#         top_comments_text = " ".join(statement_comments).replace('\n', ' ')
        
#         summary_text = "Discussion analysis unavailable."
#         if summarizer:
#             try:
#                 safe_text = top_comments_text[:3000] 
                
#                 result = summarizer(safe_text, max_length=150, min_length=50, do_sample=False)
#                 raw_summary = result[0]['summary_text']
                
#                 summary_text = f"Based on the discussions, the audience is primarily focusing on: {raw_summary.capitalize()}"
                
#             except Exception as ai_err:
#                 print(f"[AI SUMMARY ERROR]: {ai_err}")
#                 summary_text = "AI could not generate an overview from these comments."

#         return {
#             "summary": summary_text,
#             "demands": found_demands
#         }
        
#     except Exception as e:
#         return {"summary": f"Error analyzing overview: {str(e)[:50]}", "demands": []}
    
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=8000)





# import os
# import re
# import numpy as np
# import tensorflow as tf
# from collections import Counter
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from youtube_transcript_api import YouTubeTranscriptApi
# from googleapiclient.discovery import build
# from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
# import requests
# from dotenv import load_dotenv

# # --- CONFIGURATION & SECURITY ---
# load_dotenv() # .env file se keys read karega

# os.environ["TF_USE_LEGACY_KERAS"] = "1"
# os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
# HF_API_TOKEN = os.getenv("HF_API_TOKEN")

# MODEL_PATH = "saved_models/youtube_intelligence_quantized.tflite"

# app = FastAPI(title="YT Intel Cloud Ready", version="11.0")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# interpreter = None
# input_details = None
# output_details = None
# vader = SentimentIntensityAnalyzer()
# yt_service = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# POPULAR_EMOJIS = list("😂❤️🔥👍😍🙏😭😊✨🥰🤩🥺😎😁😘✅🎉💪😅💯👇💡🧠💀")

# KEYWORDS_JOY = ['awesome', 'amazing', 'masterpiece', 'excellent', 'perfect', 'beautiful', 'helpful', '🔥', '❤️']
# KEYWORDS_ANGER = ['bad', 'worst', 'hate', 'stupid', 'fake', 'scam', 'boring', 'trash', 'useless', 'dislike', 'shame', 'angry', 'mad', 'bullshit', 'terrible', 'garbage']
# KEYWORDS_SURPRISE = ['wow', 'omg', 'really', 'what', 'unbelievable', 'crazy', 'shocking', 'damn', 'surprised', 'insane', 'unexpected']
# KEYWORDS_SADNESS = ['sad', 'sorry', 'miss', 'cry', 'pain', 'rip', 'hurt', 'sadly', '😭', 'broken', 'heartbreak']
# KEYWORDS_FEAR = ['scared', 'scary', 'fear', 'terrifying', 'creepy', 'afraid', 'horror', 'panic', 'nightmare']
# KEYWORDS_DISGUST = ['gross', 'disgusting', 'eww', 'vomit', 'cringe', 'awful', 'sick', 'nasty', 'weird']

# def get_emotion_from_keywords(text_lower):
#     for w in KEYWORDS_JOY:
#         if w in text_lower: return "joy"
#     for w in KEYWORDS_ANGER:
#         if w in text_lower: return "anger"
#     for w in KEYWORDS_SURPRISE:
#         if w in text_lower: return "surprise"
#     for w in KEYWORDS_SADNESS:
#         if w in text_lower: return "sadness"
#     for w in KEYWORDS_FEAR:
#         if w in text_lower: return "fear"
#     for w in KEYWORDS_DISGUST:
#         if w in text_lower: return "disgust"
#     return None

# @app.on_event("startup")
# async def load_models():
#     global interpreter, input_details, output_details
#     try:
#         if os.path.exists(MODEL_PATH):
#             interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
#             interpreter.allocate_tensors()
#             input_details = interpreter.get_input_details()
#             output_details = interpreter.get_output_details()
#             print("[SUCCESS] TFLite Loaded.")
#         else:
#             print("TFLite Missing.")
#     except Exception as e:
#         print(f"TFLite Error: {e}")

# class VideoRequest(BaseModel):
#     video_id: str

# def extract_video_id(url: str):
#     if "v=" in url: return url.split("v=")[1].split("&")[0]
#     elif "youtu.be/" in url: return url.split("youtu.be/")[1].split("?")[0]
#     elif "/live/" in url: return url.split("/live/")[1].split("?")[0]
#     elif "/shorts/" in url: return url.split("/shorts/")[1].split("?")[0]
#     match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
#     if match: return match.group(1)
#     return url

# def get_video_stats(video_id: str):
#     try:
#         response = yt_service.videos().list(part="statistics", id=video_id).execute()
#         if response['items']:
#             return int(response['items'][0]['statistics']['commentCount'])
#     except: return 0

# def fetch_comments(video_id: str):
#     comments = []
#     try:
#         request = yt_service.commentThreads().list(part="snippet", videoId=video_id, maxResults=100, textFormat="plainText")
#         while request and len(comments) < 1000:
#             response = request.execute()
#             for item in response['items']:
#                 comments.append(item['snippet']['topLevelComment']['snippet']['textDisplay'])
#             request = yt_service.commentThreads().list_next(request, response)
#         return comments
#     except: return comments

# def analyze_logic(text: str):
#     vs = vader.polarity_scores(text)
#     compound = vs['compound']
    
#     sent = "NEUTRAL"
#     if compound >= 0.05: sent = "POSITIVE"
#     elif compound <= -0.10: sent = "NEGATIVE"
    
#     emo_ai = "neutral"
#     tox_score = 0.0
    
#     if interpreter:
#         try:
#             # Tokenizer ab manually TFLite input prep karega (Cloud friendly)
#             # Lekin simple approach me TFLite input direct pass hoti hai
#             # Note: For production, using a lightweight local tokenizer logic is better, 
#             # but we assume TFLite model is self-sufficient or expects raw int arrays.
#             # Yahan safely error handle ho jayega agar tokenizer available nahi hai
#             pass 
#         except: pass

#     text_lower = text.lower()
#     keyword_emo = get_emotion_from_keywords(text_lower)
#     final_emo = keyword_emo if keyword_emo else emo_ai

#     if final_emo == "neutral":
#         if compound >= 0.35: final_emo = "joy"
#         elif compound <= -0.35: final_emo = "anger"
    
#     is_toxic = 1 if sent == "NEGATIVE" and tox_score > 0.85 else 0
#     return {"sentiment": sent, "emotion": final_emo, "toxicity": is_toxic}

# @app.post("/analyze")
# def analyze_api(req: VideoRequest):
#     vid = extract_video_id(req.video_id)
#     real_total = get_video_stats(vid)
#     comments = fetch_comments(vid)
    
#     if not comments: return {"error": "No comments found."}

#     stats = { "positive": 0, "neutral": 0, "negative": 0, "toxic_count": 0, 
#               "emotion_counts": {k:0 for k in ['joy','surprise','sadness','anger','fear','disgust']} }
#     rich_data = []
#     all_text = ""
#     intent_counts = {"question": 0, "appreciation": 0, "request": 0, "discussion": 0}
#     all_emojis = []
#     all_bigrams = []
#     stops = {'this','that','video','watch','just','have','your','with','from','like','good','very','what','when','time','make','know','about','best','love','people','content', 'please', 'thank'}

#     for c in comments:
#         if len(c) < 2: continue
#         try:
#             res = analyze_logic(c)
#             stats[res['sentiment'].lower()] += 1
#             if res['toxicity'] == 1: stats['toxic_count'] += 1
            
#             if res['emotion'] in stats['emotion_counts']: 
#                 stats['emotion_counts'][res['emotion']] += 1
            
#             c_lower = c.lower()
#             if '?' in c or any(w in c_lower for w in ['how', 'why', 'what', 'when']): intent_counts['question'] += 1
#             elif any(w in c_lower for w in ['please', 'can you', 'help', 'request', 'make']): intent_counts['request'] += 1
#             elif res['sentiment'] == "POSITIVE" and any(w in c_lower for w in ['love', 'best', 'great', 'awesome', 'amazing', 'thank', '🔥']): intent_counts['appreciation'] += 1
#             else: intent_counts['discussion'] += 1
                
#             all_emojis.extend([ch for ch in c if ch in POPULAR_EMOJIS])
#             c_words = re.findall(r'\b[a-z]{3,15}\b', c_lower)
#             c_filtered = [w for w in c_words if w not in stops]
#             if len(c_filtered) >= 2:
#                 for i in range(len(c_filtered)-1): all_bigrams.append(f"{c_filtered[i]} {c_filtered[i+1]}")

#             all_text += " " + c
#             if len(rich_data) < 60:
#                 rich_data.append({"text": c, "sentiment": res['sentiment'], "emotion": res['emotion']})
#         except: continue

#     words = re.findall(r'\b[a-z]{4,15}\b', all_text.lower())
#     keywords = Counter([w for w in words if w not in stops]).most_common(20)
#     top_bigrams = Counter(all_bigrams).most_common(6)
#     top_emojis = Counter(all_emojis).most_common(8)

#     final_total = real_total if real_total > 0 else len(comments)

#     return {
#         "meta": {"total": final_total, "analyzed_total": len(comments), "avg_len": int(len(all_text.split())/len(comments)) if comments else 0},
#         "stats": stats, "comments": rich_data, "keywords": keywords,
#         "deep_data": {"intents": intent_counts, "bigrams": top_bigrams, "emojis": top_emojis}
#     }

# # 🚀 FREE HUGGINGFACE CLOUD API INTEGRATION
# def generate_summary_cloud(text):
#     if not HF_API_TOKEN:
#         return "⚠️ HF_API_TOKEN is missing in .env file."
    
#     API_URL = "https://api-inference.huggingface.co/models/sshleifer/distilbart-cnn-12-6"
#     headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
#     payload = {
#         "inputs": text,
#         "parameters": {"max_length": 150, "min_length": 50, "do_sample": False}
#     }
#     try:
#         response = requests.post(API_URL, headers=headers, json=payload)
#         res_json = response.json()
#         if isinstance(res_json, list) and 'summary_text' in res_json[0]:
#             return res_json[0]['summary_text']
#         else:
#             return "AI model is currently waking up. Try again in 30 seconds."
#     except Exception as e:
#         return f"Cloud API Error: {str(e)[:30]}"

# @app.post("/summarize")
# def summarize_api(req: VideoRequest):
#     vid = extract_video_id(req.video_id)
#     try:
#         comments = fetch_comments(vid)
#         if not comments: return {"summary": "No comments available.", "demands": []}

#         demand_keywords = ['please make', 'we want', 'next part', 'tutorial on', 'can you', 'upload', 'demand', 'make a video', 'waiting for', 'bring', 'we need', 'how to']
#         found_demands = []
#         for c in comments:
#             c_lower = c.lower()
#             if any(k in c_lower for k in demand_keywords) and len(c) > 15:
#                 clean_comment = c.replace('\n', ' ').strip()
#                 if clean_comment not in found_demands: found_demands.append(clean_comment)
#                 if len(found_demands) >= 3: break

#         statement_comments = [c for c in comments[:80] if len(c) > 30 and "?" not in c]
#         if not statement_comments: statement_comments = comments[:50]
#         top_comments_text = " ".join(statement_comments).replace('\n', ' ')
        
#         # Call the Cloud API instead of local model
#         safe_text = top_comments_text[:3000] 
#         raw_summary = generate_summary_cloud(safe_text)
        
#         if "waking up" in raw_summary or "Error" in raw_summary:
#             summary_text = raw_summary
#         else:
#             summary_text = f"Based on the discussions, the audience is primarily focusing on: {raw_summary.capitalize()}"

#         return {"summary": summary_text, "demands": found_demands}
        
#     except Exception as e:
#         return {"summary": f"Error analyzing overview: {str(e)[:50]}", "demands": []}
    
# if __name__ == "__main__":
#     import uvicorn
#     # 🚀 DYNAMIC PORT FOR RENDER
#     port = int(os.environ.get("PORT", 8000))
#     uvicorn.run(app, host="0.0.0.0", port=port)








# import os
# import re
# import numpy as np
# import tensorflow as tf
# from collections import Counter
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from youtube_transcript_api import YouTubeTranscriptApi
# from transformers import AutoTokenizer
# from googleapiclient.discovery import build
# from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
# import requests
# import time
# from dotenv import load_dotenv

# # --- CONFIGURATION & SECURITY ---
# load_dotenv()

# os.environ["TF_USE_LEGACY_KERAS"] = "1"
# os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
# HF_API_TOKEN = os.getenv("HF_API_TOKEN")

# MODEL_PATH = "saved_models/youtube_intelligence_quantized.tflite"
# MAX_LEN = 64

# app = FastAPI(title="YT Intel Final Production", version="13.0")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# interpreter = None
# input_details = None
# output_details = None
# tokenizer = None
# vader = SentimentIntensityAnalyzer()
# yt_service = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# POPULAR_EMOJIS = list("😂❤️🔥👍😍🙏😭😊✨🥰🤩🥺😎😁😘✅🎉💪😅💯👇💡🧠💀")

# KEYWORDS_JOY = ['awesome', 'amazing', 'masterpiece', 'excellent', 'perfect', 'beautiful', 'helpful', '🔥', '❤️']
# KEYWORDS_ANGER = ['bad', 'worst', 'hate', 'stupid', 'fake', 'scam', 'boring', 'trash', 'useless', 'dislike', 'shame', 'angry', 'mad', 'bullshit', 'terrible', 'garbage']
# KEYWORDS_SURPRISE = ['wow', 'omg', 'really', 'what', 'unbelievable', 'crazy', 'shocking', 'damn', 'surprised', 'insane', 'unexpected']
# KEYWORDS_SADNESS = ['sad', 'sorry', 'miss', 'cry', 'pain', 'rip', 'hurt', 'sadly', '😭', 'broken', 'heartbreak']
# KEYWORDS_FEAR = ['scared', 'scary', 'fear', 'terrifying', 'creepy', 'afraid', 'horror', 'panic', 'nightmare']
# KEYWORDS_DISGUST = ['gross', 'disgusting', 'eww', 'vomit', 'cringe', 'awful', 'sick', 'nasty', 'weird']

# def get_emotion_from_keywords(text_lower):
#     for w in KEYWORDS_JOY:
#         if w in text_lower: return "joy"
#     for w in KEYWORDS_ANGER:
#         if w in text_lower: return "anger"
#     for w in KEYWORDS_SURPRISE:
#         if w in text_lower: return "surprise"
#     for w in KEYWORDS_SADNESS:
#         if w in text_lower: return "sadness"
#     for w in KEYWORDS_FEAR:
#         if w in text_lower: return "fear"
#     for w in KEYWORDS_DISGUST:
#         if w in text_lower: return "disgust"
#     return None

# @app.on_event("startup")
# async def load_models():
#     global interpreter, input_details, output_details, tokenizer
#     try:
#         if os.path.exists(MODEL_PATH):
#             interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
#             interpreter.allocate_tensors()
#             input_details = interpreter.get_input_details()
#             output_details = interpreter.get_output_details()
#             print("[SUCCESS] TFLite Loaded.")
#             tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
#         else:
#             print("TFLite Missing.")
#     except Exception as e:
#         print(f"TFLite Error: {e}")

# class VideoRequest(BaseModel):
#     video_id: str

# def extract_video_id(url: str):
#     if "v=" in url: return url.split("v=")[1].split("&")[0]
#     elif "youtu.be/" in url: return url.split("youtu.be/")[1].split("?")[0]
#     elif "/live/" in url: return url.split("/live/")[1].split("?")[0]
#     elif "/shorts/" in url: return url.split("/shorts/")[1].split("?")[0]
#     match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
#     if match: return match.group(1)
#     return url

# def get_video_stats(video_id: str):
#     try:
#         response = yt_service.videos().list(part="statistics", id=video_id).execute()
#         if response['items']:
#             return int(response['items'][0]['statistics']['commentCount'])
#     except: return 0

# def fetch_comments(video_id: str):
#     comments = []
#     try:
#         request = yt_service.commentThreads().list(part="snippet", videoId=video_id, maxResults=100, textFormat="plainText")
#         while request and len(comments) < 1000:
#             response = request.execute()
#             for item in response['items']:
#                 comments.append(item['snippet']['topLevelComment']['snippet']['textDisplay'])
#             request = yt_service.commentThreads().list_next(request, response)
#         return comments
#     except: return comments

# def analyze_logic(text: str):
#     vs = vader.polarity_scores(text)
#     compound = vs['compound']
    
#     sent = "NEUTRAL"
#     if compound >= 0.05: sent = "POSITIVE"
#     elif compound <= -0.10: sent = "NEGATIVE"
    
#     emo_ai = "neutral"
#     tox_score = 0.0
    
#     if interpreter and tokenizer:
#         try:
#             encoded = tokenizer(text, max_length=MAX_LEN, padding='max_length', truncation=True, return_tensors='np')
#             interpreter.set_tensor(input_details[0]['index'], encoded['input_ids'].astype(np.int32))
#             interpreter.set_tensor(input_details[1]['index'], encoded['attention_mask'].astype(np.int32))
#             interpreter.invoke()
            
#             emo_probs = interpreter.get_tensor(output_details[1]['index'])[0].copy()
#             tox_score = float(interpreter.get_tensor(output_details[2]['index'])[0][0])
            
#             labels = ['neutral', 'fear', 'anger', 'joy', 'surprise', 'sadness', 'disgust']
            
#             # 🔥 THE MAGIC WEIGHTAGE SYSTEM 🔥
#             emo_probs[1] *= 1.8 
#             emo_probs[2] *= 1.8  
#             emo_probs[3] *= 0.5  
#             emo_probs[4] *= 1.0  
#             emo_probs[5] *= 1.8  
#             emo_probs[6] *= 1.4  
#             emo_probs[0] *= 0.3  
            
#             best_idx = np.argmax(emo_probs)
#             emo_ai = labels[best_idx]
#         except: pass

#     text_lower = text.lower()
#     keyword_emo = get_emotion_from_keywords(text_lower)
#     final_emo = keyword_emo if keyword_emo else emo_ai

#     if final_emo == "neutral":
#         if compound >= 0.35: final_emo = "joy"
#         elif compound <= -0.35: final_emo = "anger"
    
#     # 🔥 FIX: SMART TOXICITY LOGIC 🔥
#     # 🔥 FIX: STRICT & SMART TOXICITY LOGIC 🔥
#     toxic_words = ['stupid', 'scam', 'trash', 'useless', 'bullshit', 'garbage', 'idiot', 'hate', 'fake']
#     is_toxic = 0
    
#     # AI tabhi toxic manega jab wo 85% se zyada sure ho aur sentiment NEGATIVE ho
#     if tox_score > 0.85 and sent == "NEGATIVE":
#         is_toxic = 1
#     # Ya fir comment mein koi direct toxic gaali/word ho
#     elif any(w in text_lower for w in toxic_words):
#         is_toxic = 1
    
#     return {"sentiment": sent, "emotion": final_emo, "toxicity": is_toxic}

# @app.post("/analyze")
# def analyze_api(req: VideoRequest):
#     vid = extract_video_id(req.video_id)
#     real_total = get_video_stats(vid)
#     comments = fetch_comments(vid)
    
#     if not comments: return {"error": "No comments found."}

#     stats = { "positive": 0, "neutral": 0, "negative": 0, "toxic_count": 0, 
#               "emotion_counts": {k:0 for k in ['joy','surprise','sadness','anger','fear','disgust']} }
#     rich_data = []
#     all_text = ""
#     intent_counts = {"question": 0, "appreciation": 0, "request": 0, "discussion": 0}
#     all_emojis = []
#     all_bigrams = []
#     stops = {'this','that','video','watch','just','have','your','with','from','like','good','very','what','when','time','make','know','about','best','love','people','content', 'please', 'thank', 'thanks', 'guys', 'will', 'there', 'here', 'then'}

#     for c in comments:
#         if len(c) < 2: continue
#         try:
#             res = analyze_logic(c)
#             stats[res['sentiment'].lower()] += 1
#             if res['toxicity'] == 1: stats['toxic_count'] += 1
            
#             if res['emotion'] in stats['emotion_counts']: 
#                 stats['emotion_counts'][res['emotion']] += 1
            
#             c_lower = c.lower()
#             if '?' in c or any(w in c_lower for w in ['how', 'why', 'what', 'when']): intent_counts['question'] += 1
#             elif any(w in c_lower for w in ['please', 'can you', 'help', 'request', 'make']): intent_counts['request'] += 1
#             elif res['sentiment'] == "POSITIVE" and any(w in c_lower for w in ['love', 'best', 'great', 'awesome', 'amazing', 'thank', '🔥', '❤️']): intent_counts['appreciation'] += 1
#             else: intent_counts['discussion'] += 1
                
#             all_emojis.extend([ch for ch in c if ch in POPULAR_EMOJIS])
#             c_words = re.findall(r'\b[a-z]{3,15}\b', c_lower)
#             c_filtered = [w for w in c_words if w not in stops]
#             if len(c_filtered) >= 2:
#                 for i in range(len(c_filtered)-1): all_bigrams.append(f"{c_filtered[i]} {c_filtered[i+1]}")

#             all_text += " " + c
#             if len(rich_data) < 60:
#                 rich_data.append({"text": c, "sentiment": res['sentiment'], "emotion": res['emotion']})
#         except: continue

#     words = re.findall(r'\b[a-z]{4,15}\b', all_text.lower())
#     keywords = Counter([w for w in words if w not in stops]).most_common(20)
#     top_bigrams = Counter(all_bigrams).most_common(6)
#     top_emojis = Counter(all_emojis).most_common(8)

#     final_total = real_total if real_total > 0 else len(comments)

#     return {
#         "meta": {"total": final_total, "analyzed_total": len(comments), "avg_len": int(len(all_text.split())/len(comments)) if comments else 0},
#         "stats": stats, "comments": rich_data, "keywords": keywords,
#         "deep_data": {"intents": intent_counts, "bigrams": top_bigrams, "emojis": top_emojis}
#     }

# # 🚀 FREE HUGGINGFACE CLOUD API INTEGRATION (With Smart Wait Loop)
# def generate_summary_cloud(text):
#     if not HF_API_TOKEN:
#         return "⚠️ HF_API_TOKEN is missing in .env file."
    
#     API_URL = "https://api-inference.huggingface.co/models/Falconsai/text_summarization"
#     headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
#     payload = {
#         "inputs": text,
#         "parameters": {"max_length": 150, "min_length": 50, "do_sample": False}
#     }
    
#     # 60 seconds maximum wait time taaki AI jag jaye
#     for attempt in range(6):
#         try:
#             response = requests.post(API_URL, headers=headers, json=payload)
#             res_json = response.json()
            
#             if isinstance(res_json, list) and 'summary_text' in res_json[0]:
#                 return res_json[0]['summary_text']
#             elif isinstance(res_json, dict) and "error" in res_json:
#                 error_msg = res_json["error"].lower()
#                 if "loading" in error_msg or "waking" in error_msg:
#                     wait_time = res_json.get("estimated_time", 10)
#                     print(f"[INFO] HuggingFace Model Waking Up... Waiting {wait_time}s (Attempt {attempt+1}/6)")
#                     time.sleep(min(wait_time, 15))
#                     continue
#                 else:
#                     return f"⚠️ API Error: {res_json['error'][:50]}"
#             elif isinstance(res_json, dict) and "estimated_time" in res_json:
#                 print(f"[INFO] HuggingFace Model Waking Up... Waiting 10s (Attempt {attempt+1}/6)")
#                 time.sleep(10)
#                 continue
#             else:
#                 return "⚠️ Unexpected response from Cloud API."
#         except Exception as e:
#             return f"⚠️ Cloud API Error: {str(e)[:30]}"

#     return "⚠️ AI model took too long to wake up. Please click Analyze again."

# @app.post("/summarize")
# def summarize_api(req: VideoRequest):
#     vid = extract_video_id(req.video_id)
#     try:
#         comments = fetch_comments(vid)
#         if not comments: return {"summary": "No comments available.", "demands": []}

#         demand_keywords = ['please make', 'we want', 'next part', 'tutorial on', 'can you', 'upload', 'demand', 'make a video', 'waiting for', 'bring', 'we need', 'how to']
#         found_demands = []
#         for c in comments:
#             c_lower = c.lower()
#             if any(k in c_lower for k in demand_keywords) and len(c) > 15:
#                 clean_comment = c.replace('\n', ' ').strip()
#                 if clean_comment not in found_demands: found_demands.append(clean_comment)
#                 if len(found_demands) >= 3: break

#         statement_comments = [c for c in comments[:80] if len(c) > 30 and "?" not in c]
#         if not statement_comments: statement_comments = comments[:50]
#         top_comments_text = " ".join(statement_comments).replace('\n', ' ')
        
#         safe_text = top_comments_text[:3000] 
#         raw_summary = generate_summary_cloud(safe_text)
        
#         if "waking up" in raw_summary or "Error" in raw_summary or "missing" in raw_summary:
#             summary_text = raw_summary
#         else:
#             summary_text = f"Based on the discussions, the audience is primarily focusing on: {raw_summary.capitalize()}"

#         return {"summary": summary_text, "demands": found_demands}
        
#     except Exception as e:
#         return {"summary": f"Error analyzing overview: {str(e)[:50]}", "demands": []}
    
# if __name__ == "__main__":
#     import uvicorn
#     port = int(os.environ.get("PORT", 8000))
#     uvicorn.run(app, host="0.0.0.0", port=port)







import os
import re
import numpy as np
import tensorflow as tf
from collections import Counter
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
from transformers import AutoTokenizer
from googleapiclient.discovery import build
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from dotenv import load_dotenv

# --- CONFIGURATION & SECURITY ---
load_dotenv()

os.environ["TF_USE_LEGACY_KERAS"] = "1"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

MODEL_PATH = "saved_models/youtube_intelligence_quantized.tflite"
MAX_LEN = 64

app = FastAPI(title="YT Intel Final Production", version="14.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

interpreter = None
input_details = None
output_details = None
tokenizer = None
vader = SentimentIntensityAnalyzer()
yt_service = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

POPULAR_EMOJIS = list("😂❤️🔥👍😍🙏😭😊✨🥰🤩🥺😎😁😘✅🎉💪😅💯👇💡🧠💀")

KEYWORDS_JOY = ['awesome', 'amazing', 'masterpiece', 'excellent', 'perfect', 'beautiful', 'helpful', '🔥', '❤️']
KEYWORDS_ANGER = ['bad', 'worst', 'hate', 'stupid', 'fake', 'scam', 'boring', 'trash', 'useless', 'dislike', 'shame', 'angry', 'mad', 'bullshit', 'terrible', 'garbage']
KEYWORDS_SURPRISE = ['wow', 'omg', 'really', 'what', 'unbelievable', 'crazy', 'shocking', 'damn', 'surprised', 'insane', 'unexpected']
KEYWORDS_SADNESS = ['sad', 'sorry', 'miss', 'cry', 'pain', 'rip', 'hurt', 'sadly', '😭', 'broken', 'heartbreak']
KEYWORDS_FEAR = ['scared', 'scary', 'fear', 'terrifying', 'creepy', 'afraid', 'horror', 'panic', 'nightmare']
KEYWORDS_DISGUST = ['gross', 'disgusting', 'eww', 'vomit', 'cringe', 'awful', 'sick', 'nasty', 'weird']

def get_emotion_from_keywords(text_lower):
    for w in KEYWORDS_JOY:
        if w in text_lower: return "joy"
    for w in KEYWORDS_ANGER:
        if w in text_lower: return "anger"
    for w in KEYWORDS_SURPRISE:
        if w in text_lower: return "surprise"
    for w in KEYWORDS_SADNESS:
        if w in text_lower: return "sadness"
    for w in KEYWORDS_FEAR:
        if w in text_lower: return "fear"
    for w in KEYWORDS_DISGUST:
        if w in text_lower: return "disgust"
    return None

@app.on_event("startup")
async def load_models():
    global interpreter, input_details, output_details, tokenizer
    try:
        if os.path.exists(MODEL_PATH):
            interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
            interpreter.allocate_tensors()
            input_details = interpreter.get_input_details()
            output_details = interpreter.get_output_details()
            print("[SUCCESS] TFLite Loaded.")
            tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
        else:
            print("TFLite Missing.")
    except Exception as e:
        print(f"TFLite Error: {e}")

class VideoRequest(BaseModel):
    video_id: str

def extract_video_id(url: str):
    if "v=" in url: return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url: return url.split("youtu.be/")[1].split("?")[0]
    elif "/live/" in url: return url.split("/live/")[1].split("?")[0]
    elif "/shorts/" in url: return url.split("/shorts/")[1].split("?")[0]
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    if match: return match.group(1)
    return url

def get_video_stats(video_id: str):
    try:
        response = yt_service.videos().list(part="statistics", id=video_id).execute()
        if response['items']:
            return int(response['items'][0]['statistics']['commentCount'])
    except: return 0

def fetch_comments(video_id: str):
    comments = []
    try:
        request = yt_service.commentThreads().list(part="snippet", videoId=video_id, maxResults=100, textFormat="plainText")
        while request and len(comments) < 1000:
            response = request.execute()
            for item in response['items']:
                comments.append(item['snippet']['topLevelComment']['snippet']['textDisplay'])
            request = yt_service.commentThreads().list_next(request, response)
        return comments
    except: return comments

def analyze_logic(text: str):
    vs = vader.polarity_scores(text)
    compound = vs['compound']
    
    sent = "NEUTRAL"
    if compound >= 0.05: sent = "POSITIVE"
    elif compound <= -0.10: sent = "NEGATIVE"
    
    emo_ai = "neutral"
    tox_score = 0.0
    
    if interpreter and tokenizer:
        try:
            encoded = tokenizer(text, max_length=MAX_LEN, padding='max_length', truncation=True, return_tensors='np')
            interpreter.set_tensor(input_details[0]['index'], encoded['input_ids'].astype(np.int32))
            interpreter.set_tensor(input_details[1]['index'], encoded['attention_mask'].astype(np.int32))
            interpreter.invoke()
            
            emo_probs = interpreter.get_tensor(output_details[1]['index'])[0].copy()
            tox_score = float(interpreter.get_tensor(output_details[2]['index'])[0][0])
            
            labels = ['neutral', 'fear', 'anger', 'joy', 'surprise', 'sadness', 'disgust']
            
            emo_probs[1] *= 1.8 
            emo_probs[2] *= 1.8  
            emo_probs[3] *= 0.5  
            emo_probs[4] *= 1.0  
            emo_probs[5] *= 1.8  
            emo_probs[6] *= 1.4  
            emo_probs[0] *= 0.3  
            
            best_idx = np.argmax(emo_probs)
            emo_ai = labels[best_idx]
        except: pass

    text_lower = text.lower()
    keyword_emo = get_emotion_from_keywords(text_lower)
    final_emo = keyword_emo if keyword_emo else emo_ai

    if final_emo == "neutral":
        if compound >= 0.35: final_emo = "joy"
        elif compound <= -0.35: final_emo = "anger"
    
    toxic_words = ['stupid', 'scam', 'trash', 'useless', 'bullshit', 'garbage', 'idiot', 'hate', 'fake']
    is_toxic = 0
    if tox_score > 0.85 and sent == "NEGATIVE":
        is_toxic = 1
    elif any(w in text_lower for w in toxic_words):
        is_toxic = 1
    
    return {"sentiment": sent, "emotion": final_emo, "toxicity": is_toxic}

@app.post("/analyze")
def analyze_api(req: VideoRequest):
    vid = extract_video_id(req.video_id)
    real_total = get_video_stats(vid)
    comments = fetch_comments(vid)
    
    if not comments: return {"error": "No comments found."}

    stats = { "positive": 0, "neutral": 0, "negative": 0, "toxic_count": 0, 
              "emotion_counts": {k:0 for k in ['joy','surprise','sadness','anger','fear','disgust']} }
    rich_data = []
    all_text = ""
    intent_counts = {"question": 0, "appreciation": 0, "request": 0, "discussion": 0}
    all_emojis = []
    all_bigrams = []
    stops = {'this','that','video','watch','just','have','your','with','from','like','good','very','what','when','time','make','know','about','best','love','people','content', 'please', 'thank', 'thanks', 'guys', 'will', 'there', 'here', 'then'}

    for c in comments:
        if len(c) < 2: continue
        try:
            res = analyze_logic(c)
            stats[res['sentiment'].lower()] += 1
            if res['toxicity'] == 1: stats['toxic_count'] += 1
            
            if res['emotion'] in stats['emotion_counts']: 
                stats['emotion_counts'][res['emotion']] += 1
            
            c_lower = c.lower()
            if '?' in c or any(w in c_lower for w in ['how', 'why', 'what', 'when']): intent_counts['question'] += 1
            elif any(w in c_lower for w in ['please', 'can you', 'help', 'request', 'make']): intent_counts['request'] += 1
            elif res['sentiment'] == "POSITIVE" and any(w in c_lower for w in ['love', 'best', 'great', 'awesome', 'amazing', 'thank', '🔥', '❤️']): intent_counts['appreciation'] += 1
            else: intent_counts['discussion'] += 1
                
            all_emojis.extend([ch for ch in c if ch in POPULAR_EMOJIS])
            c_words = re.findall(r'\b[a-z]{3,15}\b', c_lower)
            c_filtered = [w for w in c_words if w not in stops]
            if len(c_filtered) >= 2:
                for i in range(len(c_filtered)-1): all_bigrams.append(f"{c_filtered[i]} {c_filtered[i+1]}")

            all_text += " " + c
            if len(rich_data) < 60:
                rich_data.append({"text": c, "sentiment": res['sentiment'], "emotion": res['emotion']})
        except: continue

    words = re.findall(r'\b[a-z]{4,15}\b', all_text.lower())
    keywords = Counter([w for w in words if w not in stops]).most_common(20)
    top_bigrams = Counter(all_bigrams).most_common(6)
    top_emojis = Counter(all_emojis).most_common(8)

    final_total = real_total if real_total > 0 else len(comments)

    return {
        "meta": {"total": final_total, "analyzed_total": len(comments), "avg_len": int(len(all_text.split())/len(comments)) if comments else 0},
        "stats": stats, "comments": rich_data, "keywords": keywords,
        "deep_data": {"intents": intent_counts, "bigrams": top_bigrams, "emojis": top_emojis}
    }


# 🚀 LOCAL SMART INSIGHT ENGINE (No Cloud API Required)
@app.post("/summarize")
def summarize_api(req: VideoRequest):
    vid = extract_video_id(req.video_id)
    try:
        comments = fetch_comments(vid)
        if not comments: return {"summary": "No comments available.", "demands": []}

        # 1. 🚀 Extracting Public Demands
        demand_keywords = ['please make', 'we want', 'next part', 'tutorial on', 'can you', 'upload', 'demand', 'make a video', 'waiting for', 'bring', 'we need', 'how to']
        found_demands = []
        for c in comments:
            c_lower = c.lower()
            if any(k in c_lower for k in demand_keywords) and len(c) > 15:
                clean_comment = c.replace('\n', ' ').strip()
                if clean_comment not in found_demands: found_demands.append(clean_comment)
                if len(found_demands) >= 3: break

        # 2. 🧠 Generating Smart Local Summary
        # A) Get Video Title
        try:
            video_resp = yt_service.videos().list(part="snippet", id=vid).execute()
            title = video_resp['items'][0]['snippet']['title'] if video_resp['items'] else "this topic"
        except:
            title = "this video"

        # B) Get Overall Vibe (Fast VADER check on top 50 comments)
        pos, neg = 0, 0
        for c in comments[:50]:
            comp = vader.polarity_scores(c)['compound']
            if comp > 0.05: pos += 1
            elif comp < -0.05: neg += 1
        
        vibe = "Mixed"
        if pos > (neg * 2): vibe = "Highly Positive"
        elif neg > (pos * 2): vibe = "Highly Negative"
        elif pos > neg: vibe = "Mostly Positive"
        elif neg > pos: vibe = "Mostly Negative"

        # C) Extract Top Topics (Keywords)
        text_block = " ".join(comments[:100]).lower()
        words = re.findall(r'\b[a-z]{4,15}\b', text_block)
        stops = {'this','that','video','watch','just','have','your','with','from','like','good','very','what','when','time','make','know','about','best','love','people','content', 'please', 'thank', 'thanks', 'really', 'much', 'would'}
        top_words = Counter([w for w in words if w not in stops]).most_common(2)
        
        # D) Construct Final Smart Insight
        if len(top_words) >= 2:
            t1, t2 = top_words[0][0], top_words[1][0]
            summary_text = f"The audience is highly engaged with '{title}'. The overall sentiment is {vibe}, with core discussions revolving around topics like '{t1}' and '{t2}'."
        else:
            summary_text = f"The audience is actively discussing '{title}', showing {vibe} reactions."

        return {"summary": summary_text, "demands": found_demands}
        
    except Exception as e:
        return {"summary": f"Insight generation failed: {str(e)[:50]}", "demands": []}
    
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)