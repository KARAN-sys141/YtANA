# ⚡ YouTube Intelligence AI

> **A full-stack AI-powered Chrome Extension + FastAPI backend that performs real-time sentiment analysis, emotion detection, toxicity classification, and audience insight summarization on any YouTube video's comment section.**

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/TensorFlow-TFLite-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white"/>
  <img src="https://img.shields.io/badge/DistilBERT-HuggingFace-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black"/>
  <img src="https://img.shields.io/badge/Chrome_Extension-MV3-4285F4?style=for-the-badge&logo=googlechrome&logoColor=white"/>
  <img src="https://img.shields.io/badge/MLflow-Tracking-0194E2?style=for-the-badge&logo=mlflow&logoColor=white"/>
</p>

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [AI Model Pipeline](#-ai-model-pipeline)
- [Backend API](#-backend-api)
- [Chrome Extension](#-chrome-extension)
- [Installation & Setup](#-installation--setup)
- [Environment Variables](#-environment-variables)
- [Training the Model](#-training-the-model)
- [Model Quantization](#-model-quantization)
- [API Reference](#-api-reference)
- [Tech Stack](#-tech-stack)

---

## 🧠 Overview

**YouTube Intelligence AI** is an end-to-end ML system that turns raw YouTube comment data into actionable audience intelligence. A user simply opens any YouTube video in Chrome and clicks **Analyze Video** in the extension popup — the system fetches up to **1,000 comments** via the YouTube Data API, runs them through a fine-tuned **DistilBERT multi-task model** (quantized to TFLite for fast inference), and returns a rich analytical dashboard in seconds.

The system is production-deployed on **Render** (`https://ytana.onrender.com`) and uses:
- A **custom-trained DistilBERT** model for simultaneous sentiment, emotion, and toxicity classification
- **VADER** for fast, lexicon-based sentiment scoring
- **Keyword + VADER fusion** logic for reliable real-world emotion accuracy
- A **Chrome Manifest V3 Extension** with a dark-themed, neon-styled interactive popup

---

## ✨ Key Features

| Feature | Description |
|---|---|
| **Sentiment Analysis** | Classifies each comment as Positive, Negative, or Neutral using VADER + DistilBERT |
| **Emotion Detection** | Identifies 7 emotion categories: Joy, Anger, Sadness, Surprise, Fear, Disgust, Neutral |
| **Toxicity Scoring** | Detects toxic/harmful comments using model output + keyword heuristics |
| **AI Verdict** | Generates a human-readable verdict (e.g., "Highly Loved", "Controversial") |
| **Chat Quality Score** | Categorizes comment depth: Quick Reactions / Good Engagement / Deep Discussions |
| **Audience Intent Chart** | Pie chart classifying comments as Questions, Appreciation, Requests, or Discussion |
| **Word Cloud** | Top 20 most-used keywords visualized by frequency |
| **Top Phrases** | Bigram-based top 6 phrase patterns from the comment section |
| **Emoji Cloud** | Top 8 most-used emojis extracted from comments |
| **Emotion Radar Chart** | Radar chart showing the emotional fingerprint of the audience |
| **AI Audience Summary** | Auto-generated natural language summary of overall audience mood |
| **Public Demand Tracker** | Extracts comments that contain viewer requests and demands |
| **Supports All Formats** | Works on `/watch`, `/shorts/`, and `/live/` YouTube URLs |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CHROME EXTENSION (MV3)                   │
│   popup.html + popup.js + styles.css + chart.js (bundled)  │
│   • Detects YouTube video URL from active tab              │
│   • Sends video_id → FastAPI Backend (Render)              │
│   • Renders charts, stats, comments, word clouds           │
└─────────────────────────┬───────────────────────────────────┘
                          │  HTTP POST (fetch)
                          ▼
┌─────────────────────────────────────────────────────────────┐
│               FASTAPI BACKEND (src/app/main.py)            │
│   • /analyze  → Full comment sentiment & emotion pipeline  │
│   • /summarize → AI audience summary + demand extraction   │
│   Deployed on: https://ytana.onrender.com                  │
└────────┬───────────────────────────────┬────────────────────┘
         │                              │
         ▼                              ▼
┌─────────────────┐          ┌──────────────────────┐
│  YouTube Data   │          │  ML Inference Engine  │
│  API v3         │          │                      │
│  • commentThreads│         │  DistilBERT (TFLite)  │
│  • videos.list  │          │  → Emotion (7-class)  │
│  (up to 1000   │          │  → Toxicity (binary)  │
│   comments)    │          │                      │
└─────────────────┘          │  VADER Sentiment      │
                             │  → Compound score     │
                             │                      │
                             │  Keyword Fusion Logic │
                             │  → Final emotion      │
                             └──────────────────────┘
```

---

## 📁 Project Structure

```
AI_YouTube_Sentiment_Analysis/
│
├── src/
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py               # FastAPI application (core backend)
│   │
│   ├── data_pipeline/
│   │   └── preprocess.py         # YouTubeDataPipeline — tokenization, cleaning, tf.data
│   │
│   └── model/
│       ├── architecture.py       # Multi-task DistilBERT model definition
│       ├── train_model.py        # Training script with MLflow tracking
│       ├── quantize.py           # TFLite quantization script
│       └── summarizer.py        # DistilBART summarizer (optional module)
│
├── extension/
│   ├── manifest.json             # Chrome Manifest V3 config
│   ├── popup.html                # Extension popup UI
│   ├── popup.js                  # All frontend logic + Chart.js rendering
│   ├── styles.css                # Dark neon-themed CSS
│   └── chart.js                  # Bundled Chart.js (offline capable)
│
├── saved_models/
│   ├── youtube_intelligence_v1.h5             # Full H5 model (~760 MB)
│   └── youtube_intelligence_quantized.tflite  # Quantized TFLite (~64 MB)
│
├── data/
│   └── raw/                      # Training CSVs (train_updated.csv, test_updated.csv)
│
├── mlruns/                       # MLflow experiment run artifacts
│
├── .env                          # API keys (not committed to git)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🤖 AI Model Pipeline

### Model Architecture (`src/model/architecture.py`)

The model is a **multi-task learning** architecture built on top of `distilbert-base-uncased`:

```
Input IDs + Attention Mask
        │
  DistilBERT Encoder
        │
    CLS Token State
        │
   Dropout (0.3)
        │
   ┌────┴────┬───────────────┐
   ▼         ▼               ▼
Dense(3)  Dense(7)       Dense(1)
Softmax   Softmax        Sigmoid
   │         │               │
Sentiment  Emotion        Toxicity
(3-class)  (7-class)     (binary)
```

**Outputs:**
- **Sentiment**: `[Negative, Neutral, Positive]`
- **Emotion**: `[Neutral, Fear, Anger, Joy, Surprise, Sadness, Disgust]`
- **Toxicity**: `[0.0 – 1.0]` (binary probability)

**Loss Functions:**
- Sentiment → `sparse_categorical_crossentropy`
- Emotion → `sparse_categorical_crossentropy`
- Toxicity → `binary_crossentropy`

**Optimizer:** Adam with `lr=3e-5`

---

### Data Pipeline (`src/data_pipeline/preprocess.py`)

The `YouTubeDataPipeline` class handles:

1. **Text Cleaning** — removes URLs, demojizes emoji (e.g., `😂` → `:face_with_tears_of_joy:`), strips special characters
2. **Synthetic Toxicity Injection** — injects 300 labeled toxic comments at training time to balance the dataset
3. **Tokenization** — uses `AutoTokenizer` from HuggingFace (`distilbert-base-uncased`), max length = 64 tokens
4. **Class Weight Calculation** — computes balanced class weights per task using `sklearn`
5. **tf.data Pipeline** — returns batched, shuffled `tf.data.Dataset` with `AUTOTUNE` prefetch

---

### Inference Logic (`src/app/main.py`)

Per-comment analysis uses a **3-layer fusion**:

1. **VADER** → Computes compound score → `POSITIVE / NEUTRAL / NEGATIVE`
2. **TFLite DistilBERT** → Outputs raw emotion probabilities with manual scaling:
   - Fear, Anger, Sadness boosted (`×1.8`)
   - Joy suppressed (`×0.5`)
   - Neutral strongly suppressed (`×0.3`)
3. **Keyword Heuristics** → Overrides model if a strong keyword is matched (e.g., `"hate"` → anger, `"wow"` → surprise)

**Final Emotion Resolution:**
- Keyword match wins if found
- Otherwise: model prediction is used
- If still "neutral" and VADER compound is strong → fallback to joy or anger

---

## 🖥 Backend API

**File:** `src/app/main.py`
**Framework:** FastAPI v14.0 (production title: `YT Intel Final Production`)
**Server:** Uvicorn on port `8000` (or `PORT` from env)
**CORS:** Open (`*`) — allows extension to call from any origin

### Startup
On server start, the TFLite model and DistilBERT tokenizer are loaded into memory once and reused across all requests.

---

## 🧩 Chrome Extension

**Manifest Version:** 3
**Permissions:** `activeTab`, `scripting`
**Host Permissions:** `https://ytana.onrender.com/*`, `https://*.youtube.com/*`

### Features in the Popup UI

The extension popup (`popup.html` + `popup.js`) has **3 tabs**:

#### 🗂 Overview Tab
- Video thumbnail + title auto-detected from the active tab
- Stats grid: Total Comments, Avg Comment Length, Toxicity %, Top Emotion
- AI Audience Summary (async — loads after main analysis)
- Sentiment bar track (Pos / Neu / Neg breakdown)
- AI Verdict + Chat Quality verdict boxes

#### 💬 Comments Tab
- Scrollable list of up to 60 real comments
- Each card shows: Sentiment badge (POS/NEU/NEG), Emotion badge, comment text

#### 📊 Deep Data Tab
- **Emotion Radar Chart** — 6-axis radar (Chart.js)
- **Word Cloud** — Top 20 keywords, color-coded and sized by frequency
- **Sentiment Doughnut Chart** — Positive / Neutral / Negative ratio
- **Audience Intent Pie Chart** — Questions / Appreciation / Requests / Discussion
- **Top Phrases** — Top 6 bigrams from comments
- **Emoji Cloud** — Top 8 emojis used

---

## ⚙️ Installation & Setup

### Prerequisites

- Python 3.10+
- Google Chrome browser
- A YouTube Data API v3 key

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/AI_YouTube_Sentiment_Analysis.git
cd AI_YouTube_Sentiment_Analysis
```

### 2. Create a Virtual Environment

```bash
python -m venv env
# Windows
env\Scripts\activate
# macOS / Linux
source env/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
YOUTUBE_API_KEY=your_youtube_data_api_v3_key_here
HF_API_TOKEN=your_huggingface_token_here   # Optional, for model downloads
```

### 5. Run the Backend Server

```bash
uvicorn src.app.main:app --reload --port 8000
```

The API will be available at `http://localhost:0000`.

> **Note:** Update `API_BASE_URL` in `extension/popup.js` to point to `http://localhost:8000` for local development, or leave it as `https://ytana.onrender.com` for the production deployment.

### 6. Load the Chrome Extension

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable **Developer Mode** (toggle in the top-right)
3. Click **Load unpacked**
4. Select the `extension/` folder from this project
5. Open any YouTube video and click the extension icon ⚡

---

## 🔑 Environment Variables

| Variable | Description | Required |
|---|---|---|
| `YOUTUBE_API_KEY` | YouTube Data API v3 key from Google Cloud Console | ✅ Yes |
| `HF_API_TOKEN` | HuggingFace token (for downloading model weights) | Optional |
| `PORT` | Server port for deployment (defaults to `8000`) | Optional |

> ⚠️ **Security Note:** The `.env` file is listed in `.gitignore` and should **never** be committed to version control. Rotate your API keys if they are ever exposed.

---

## 🏋️ Training the Model

> Pre-trained model weights are already available in `saved_models/`. Only run this if you want to retrain from scratch.

### Prepare Data

Place your labeled CSV files in `data/raw/`:
- `train_updated.csv`
- `test_updated.csv`

**Required columns:** `clean_comment`, `sentiment` (`-1`, `0`, `1`), `emotion` (string), `toxicity` (`0` or `1`)

### Run Training

```bash
python -m src.model.train_model
```

This will:
1. Load and preprocess the training data
2. Inject 300 synthetic toxic samples for class balancing
3. Build the multi-task DistilBERT model
4. Train with `EarlyStopping` and `ModelCheckpoint`
5. Log all hyperparameters and metrics to **MLflow**
6. Save the trained model to `saved_models/youtube_intelligence_v1.h5`

### View MLflow Experiments

```bash
mlflow ui
```

Navigate to `http://localhost:5000` to see all training runs.

**Tracked Parameters:** `batch_size`, `epochs`, `learning_rate`, `max_len`
**Tracked Metrics:** All Keras history metrics (accuracy, loss per task)

---

## 🗜 Model Quantization

After training, convert the full `.h5` model to a lightweight TFLite model for faster production inference:

```bash
python -m src.model.quantize
```

| Model | Format | Size |
|---|---|---|
| `youtube_intelligence_v1.h5` | Keras H5 | ~760 MB |
| `youtube_intelligence_quantized.tflite` | TFLite (quantized) | ~64 MB |
| **Compression ratio** | | **~11.9×** |

Quantization uses:
- `tf.lite.Optimize.DEFAULT` (dynamic range quantization)
- `SELECT_TF_OPS` for compatibility with HuggingFace transformer ops

---

## 📡 API Reference

### `POST /analyze`

Fetches up to 1,000 comments for a video and runs the full analysis pipeline.

**Request Body:**
```json
{
  "video_id": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```
> Accepts full YouTube URLs, `youtu.be` short links, Shorts URLs, and Live URLs. Raw video IDs also work.

**Response:**
```json
{
  "meta": {
    "total": 52341,
    "analyzed_total": 847,
    "avg_len": 14
  },
  "stats": {
    "positive": 612,
    "neutral": 178,
    "negative": 57,
    "toxic_count": 12,
    "emotion_counts": {
      "joy": 430, "surprise": 80, "sadness": 22,
      "anger": 40, "fear": 5, "disgust": 15
    }
  },
  "comments": [
    { "text": "This is amazing!", "sentiment": "POSITIVE", "emotion": "joy" }
  ],
  "keywords": [["amazing", 45], ["love", 38]],
  "deep_data": {
    "intents": { "question": 120, "appreciation": 350, "request": 80, "discussion": 297 },
    "bigrams": [["great video", 22], ["keep going", 18]],
    "emojis": [["🔥", 88], ["❤️", 74]]
  }
}
```

---

### `POST /summarize`

Generates a natural-language audience summary and extracts top viewer demands.

**Request Body:**
```json
{
  "video_id": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```

**Response:**
```json
{
  "summary": "The audience is highly engaged with 'Never Gonna Give You Up'. The overall sentiment is Highly Positive, with core discussions revolving around topics like 'classic' and 'nostalgia'.",
  "demands": [
    "Please make a reaction video!",
    "Can you upload the instrumental version?"
  ]
}
```

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Backend Framework** | FastAPI + Uvicorn |
| **ML Model** | DistilBERT (`distilbert-base-uncased`) via HuggingFace Transformers |
| **Inference Runtime** | TensorFlow Lite (quantized) |
| **Sentiment Engine** | VADER (`vaderSentiment`) |
| **YouTube Data** | Google API Python Client (`youtube-transcript-api`, `google-api-python-client`) |
| **Data Processing** | Pandas, NumPy, scikit-learn |
| **Experiment Tracking** | MLflow |
| **Frontend** | Vanilla HTML5, CSS3, JavaScript (ES6+) |
| **Charts** | Chart.js (bundled, offline) |
| **Chrome Extension** | Manifest V3 |
| **Deployment** | Render (production), Uvicorn (local) |
| **Environment** | Python 3.10+, `python-dotenv` |

---

## 📄 License

This project is intended for educational and portfolio use. All rights reserved © 2026.

---

<p align="center">
  Built with ❤️ using DistilBERT, FastAPI & Chrome Extension APIs
</p>
