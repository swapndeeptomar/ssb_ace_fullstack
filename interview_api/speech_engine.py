import requests
import re

# --- MODEL 3: TONE & EMOTION ANALYSIS ---
EMOTION_API_URL = "https://router.huggingface.co/hf-inference/models/SamLowe/roberta-base-go_emotions"

# 👇 APNA TOKEN YAHAN DALO 👇
HF_TOKEN = "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" 
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

def analyze_voice_tone(text):
    """
    Analyzes text for Confidence, Boldness, and Fluency.
    Uses RoBERTa AI for Emotion Detection.
    """
    analytics = {
        "confidence": 0,  # 0-100
        "boldness": 0,    # 0-100
        "fluency": 0,     # 0-100
        "fillers": 0,     # Count (aaa, umm)
        "tone": "Neutral" # Dominant Emotion
    }
    
    if not text or len(text.split()) < 2:
        return analytics

    # 1. FLUENCY & FILLERS (Rule Based)
    # Browser STT often filters 'umm', but we check for hesitation words
    fillers_list = ['uh', 'um', 'umm', 'ah', 'like', 'actually', 'basically', 'sort of']
    filler_count = sum(text.lower().count(f) for f in fillers_list)
    analytics['fillers'] = filler_count
    
    # Fluency Logic: Less fillers + Good length = High Fluency
    word_count = len(text.split())
    analytics['fluency'] = max(40, min(95, 100 - (filler_count * 5)))
    if word_count > 15: analytics['fluency'] += 5

    # 2. AI EMOTION ANALYSIS (For Confidence & Boldness)
    try:
        payload = {"inputs": text}
        response = requests.post(EMOTION_API_URL, headers=HEADERS, json=payload, timeout=5)
        
        if response.status_code == 200:
            results = response.json()
            # Result example: [[{'label': 'optimism', 'score': 0.8}, ...]]
            
            if isinstance(results, list) and len(results) > 0:
                emotions = results[0]
                
                # Scores accumulate karenge
                conf_score = 0.0
                bold_score = 0.0
                dominant_emotion = "Neutral"
                max_score = 0

                for e in emotions:
                    label = e['label']
                    score = e['score']
                    
                    # Track Dominant Emotion
                    if score > max_score:
                        max_score = score
                        dominant_emotion = label

                    # Map Emotions to Metrics
                    if label in ['optimism', 'approval', 'pride', 'gratitude', 'relief']:
                        conf_score += score
                    if label in ['excitement', 'determination', 'anger', 'annoyance']: # Anger = Aggression/Boldness here
                        bold_score += score
                    if label in ['nervousness', 'confusion', 'fear', 'embarrassment']:
                        conf_score -= score # Negative impact
                
                analytics['tone'] = dominant_emotion.capitalize()
                
                # Scaling to 0-100
                analytics['confidence'] = round(min(98, 60 + (conf_score * 100)))
                analytics['boldness'] = round(min(95, 50 + (bold_score * 100)))
                
                return analytics

    except Exception as e:
        print(f"⚠️ Voice AI Skipped: {e}")

    # --- BACKUP LOGIC (Agar AI fail ho) ---
    # Simple keyword check
    # strong_words = ['will', 'can', 'sure', 'definitely', 'plan', 'did']
    # if any(w in text.lower() for w in strong_words):
    #     analytics['confidence'] = 85
    #     analytics['boldness'] = 75
    # else:
    #     analytics['confidence'] = 65
    #     analytics['boldness'] = 60
        
    return analytics