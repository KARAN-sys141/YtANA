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