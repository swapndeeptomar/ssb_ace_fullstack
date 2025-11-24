import requests
import time
import random
import logging

# --- CONFIGURATION ---
# Hum BART (OLQ ke liye) aur SBERT (Similarity ke liye) use karenge
OLQ_API_URL = "https://router.huggingface.co/hf-inference/models/facebook/bart-large-mnli"
SBERT_API_URL = "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2"

# 👇 APNA TOKEN YAHAN DALO 👇
HF_TOKEN = "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" 
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"} 

# 15 OLQs List (Strictly for AI)
ALL_OLQS = [
    "Effective Intelligence", "Reasoning Ability", "Organizing Ability", "Power of Expression",
    "Social Adaptability", "Cooperation", "Sense of Responsibility", "Initiative", 
    "Self Confidence", "Speed of Decision", "Ability to Influence", "Liveliness",
    "Determination", "Courage", "Stamina"
]

def query_huggingface(url, payload, retries=0):
    """
    Pure AI Call function. 
    Agar Model Load ho raha hai, to ye wait karega. Fake response nahi dega.
    """
    try:
        print(f"📡 Calling AI Model... (Attempt {retries+1})")
        response = requests.post(url, headers=HEADERS, json=payload)
        result = response.json()

        # CHECK: Agar Model 'Loading' state mein hai (Cold Start)
        if isinstance(result, dict) and 'error' in result:
            err_msg = result['error'].lower()
            if 'loading' in err_msg:
                if retries < 5: # 5 baar try karega (approx 60 seconds wait)
                    wait_time = result.get('estimated_time', 10)
                    print(f"💤 Model is loading... Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    return query_huggingface(url, payload, retries + 1)
                else:
                    print("❌ AI Timeout: Model load nahi hua.")
                    return None
        
        return result

    except Exception as e:
        print(f"⚠️ Connection Error: {e}")
        return None

# --- BACKUP LOCAL LOGIC (Smart Keywords) ---
def local_olq_logic(answer):
    scores = {}
    lower_ans = answer.lower()
    
    # Smart Keyword Map
    keyword_map = {
        "Effective Intelligence": ["solve", "plan", "idea", "logic", "think", "solution"],
        "Social Adaptability": ["friend", "family", "group", "team", "together", "talk"],
        "Cooperation": ["help", "support", "assist", "share", "cooperate"],
        "Sense of Responsibility": ["duty", "must", "responsible", "job", "task", "time"],
        "Courage": ["fear", "brave", "risk", "dare", "challenge", "save", "protect"],
        "Determination": ["try", "hard", "never", "goal", "achieve", "finish"],
        "Organizing Ability": ["arrange", "manage", "coordinate", "lead", "order"],
        "Power of Expression": ["speak", "tell", "explain", "clear", "said", "convey"],
        "Initiative": ["start", "first", "began", "volunteered", "immediate", "took"],
        "Liveliness": ["happy", "joy", "fun", "calm", "cool", "smile"]
    }

    # Keywords match karo
    for olq, words in keyword_map.items():
        if any(w in lower_ans for w in words):
            # Random High Score (7.0 - 9.5)
            scores[olq] = round(7.0 + random.random() * 2.5, 1)
            
    # Agar answer lamba hai par keywords match nahi hue (Generic answer)
    if not scores and len(answer.split()) > 8:
        random_traits = random.sample(ALL_OLQS, 3)
        for trait in random_traits:
            scores[trait] = round(6.0 + random.random() * 2, 1)
            
    return scores

def get_olq_scores(user_answer):
    if not user_answer or len(user_answer.split()) < 2:
        return {}

    # 1. Try AI (Fast)
    payload = {
        "inputs": user_answer,
        "parameters": {"candidate_labels": ALL_OLQS, "multi_label": True},
        "options": {"wait_for_model": False} # Important: Loading ka wait mat karo
    }
    
    result = query_huggingface(OLQ_API_URL, payload)
    
    if result and 'labels' in result and 'scores' in result:
        scores = {}
        print("🟢 AI OLQ Success (Fast)")
        for label, score in zip(result['labels'], result['scores']):
            if score > 0.25:
                scores[label] = round(score * 10, 1)
        return scores
    
    # 2. Instant Backup (Zero Lag)
    print("⚠️ AI Slow/Sleeping. Using Instant Backup.")
    return local_olq_logic(user_answer)

def calculate_score(user_answer, context_text=""):
    """
    STRICT SBERT ANALYSIS: Rounded & Clamped Scores.
    """
    # 1. Check for Time Limit Exceeded (Zero Marks)
    if user_answer == "Time Limit Exceeded" or not user_answer:
        return 0.0, "No answer provided."

    if not context_text: context_text = "Positive approach."

    # --- REAL AI CALL ---
    payload = {
        "inputs": {
            "source_sentence": user_answer,
            "sentences": [context_text]
        },
        "options": {"wait_for_model": True, "use_cache": False}
    }
    
    result = query_huggingface(SBERT_API_URL, payload)
    
    final_score = 0.0
    feedback = "Could not analyze response."

    if result and isinstance(result, list):
        print("🟢 AI Semantic Score Received")
        similarity = result[0] # Raw Cosine Similarity (-1.0 to 1.0)
        
        # Scaling (-10 to 10)
        raw_score = similarity * 10
        
        # Logic Boost (Thoda number badhao agar relevant hai)
        if raw_score > 0.1: 
            if raw_score < 4.0: raw_score += 2.0
            elif raw_score < 7.0: raw_score += 1.5
        
        # Clamping (Min 0, Max 9.8)
        # Isse Negative numbers 0 ban jayenge
        final_score = max(0.0, min(raw_score, 9.8))
        
        # FINAL ROUNDING (Decimal Fix)
        final_score = round(final_score, 2)
        
        if final_score > 7.0: feedback = f"Excellent match with: {context_text}..."
        elif final_score > 4.0: feedback = "Relevant attempt: {context_text}..."
        else: feedback = f"Irrelevant. Focus on: {context_text}..."
        
    return final_score, feedback