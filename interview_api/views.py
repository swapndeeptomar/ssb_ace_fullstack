from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from .models import WATWord, SRTSituation, InterviewQuestion,CandidateResponse,Candidate, OIRQuestion, PPDTImage
from .serializers import WATSerializer, SRTSerializer, InterviewSerializer,CandidateSerializer
import random
import threading
from .ai_engine import calculate_score,get_olq_scores  # <-- Humara naya logic
from .speech_engine import analyze_voice_tone  # <-- New Import

# 1. Get Random WAT Word
@api_view(['GET'])
def get_wat_word(request):
    session_id = request.query_params.get('session_id') # Frontend se session_id bhejna padega

    # Already asked words nikalo
    answered_ids = CandidateResponse.objects.filter(
        session_id=session_id, 
        test_type='WAT'
    ).values_list('question_id', flat=True)

    # Filtered List
    available_words = list(WATWord.objects.exclude(id__in=answered_ids))

    if not available_words:
        available_words = list(WATWord.objects.all())

    random_item = random.choice(available_words)
    return Response(WATSerializer(random_item).data)

# 2. Get Random SRT Situation
@api_view(['GET'])
def get_srt_situation(request):
    session_id = request.query_params.get('session_id')

    # Already asked SRTs nikalo
    answered_ids = CandidateResponse.objects.filter(
        session_id=session_id, 
        test_type='SRT'
    ).values_list('question_id', flat=True)

    # Filtered List
    available_srts = list(SRTSituation.objects.exclude(id__in=answered_ids))

    if not available_srts:
        available_srts = list(SRTSituation.objects.all())

    random_item = random.choice(available_srts)
    return Response(SRTSerializer(random_item).data)

# 3. Get Interview Question (Adaptive)
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import WATWord, SRTSituation, InterviewQuestion, Candidate, CandidateResponse
from .serializers import WATSerializer, SRTSerializer, InterviewSerializer
from .ai_engine import calculate_score # Import Real AI
import random

# --- DYNAMIC POOLING VIEW ---
@api_view(['GET'])
def get_interview_question(request):
    session_id = request.query_params.get('session_id')
    
    # 1. Candidate Identify
    try:
        candidate = Candidate.objects.get(session_id=session_id)
    except Candidate.DoesNotExist:
        print(f"❌ Candidate not found for Session: {session_id}")
        pool = list(InterviewQuestion.objects.exclude(category='intro'))
        return Response(InterviewSerializer(random.choice(pool)).data)

    # 2. History Check (Count Answers)
    # Note: Hum thoda strict filter laga rahe hain
    answered_ids = list(CandidateResponse.objects.filter(
        session_id=session_id, 
        test_type='PI'
    ).values_list('question_id', flat=True))
    
    questions_count = len(answered_ids)
    print(f"🔍 Session: {session_id} | PI Answers Count: {questions_count} | IDs: {answered_ids}")

    # 3. SLOT LOGIC (Strict)
    target_cats = []

    if questions_count == 0:
        target_cats = ['intro']
        print("👉 Round 1: Asking Intro")
    
    elif questions_count == 1:
        # Round 2: Strict Profile
        if candidate.experience_type == 'working': target_cats = ['work']
        elif candidate.experience_type == 'internship': target_cats = ['internship']
        else: target_cats = ['education']
        print(f"👉 Round 2: Asking {target_cats}")

    elif questions_count == 2:
        # Round 3: Deep Profile
        if candidate.experience_type == 'working': target_cats = ['work', 'education']
        elif candidate.experience_type == 'internship': target_cats = ['internship', 'education']
        else: target_cats = ['education']
        print(f"👉 Round 3: Asking {target_cats}")

    else:
        # Round 4+: General/Family
        target_cats = ['family', 'general']
        print("👉 Round 4+: Asking General/Family")

    # 4. FETCH & EXCLUDE (Repetition Fix)
    pool = list(InterviewQuestion.objects.filter(
        category__in=target_cats
    ).exclude(id__in=answered_ids))
    
    # 5. FALLBACK (Agar specific category khatam ho gayi)
    if not pool:
        print("⚠️ Target pool empty. Switching to Fallback.")
        fallback_cats = ['general', 'family', 'education', 'work', 'internship']
        pool = list(InterviewQuestion.objects.filter(
            category__in=fallback_cats
        ).exclude(id__in=answered_ids).exclude(category='intro')) # Intro dubara nahi

    if pool:
        selected_q = random.choice(pool)
        return Response(InterviewSerializer(selected_q).data)
    else:
        return Response({"question_text": "Interview Completed. Please submit to finish."})
@csrf_exempt
# --- SUBMIT WITH REAL AI ---
@api_view(['POST'])
def submit_response(request):
    data = request.data
    user_ans = data.get('answer', '')
    session_id = data.get('session_id')
    q_id = data.get('question_id')
    test_type = data.get('test_type', 'Unknown')

    # 1. Candidate Dhoondo
    try:
        candidate = Candidate.objects.get(session_id=session_id)
    except:
        candidate, _ = Candidate.objects.get_or_create(name="Unknown User")

    # 2. CONTEXT SELECTION (STRICT MODE)
    ideal_concepts = "General positivity and logical thinking." # Fallback

    if q_id:
        try:
            # SIRF Relevant Table mein dhoondo based on Test Type
            if test_type == 'PI':
                if InterviewQuestion.objects.filter(id=q_id).exists():
                    q_obj = InterviewQuestion.objects.get(id=q_id)
                    ideal_concepts = q_obj.evaluation_criteria 

            elif test_type == 'WAT':
                if WATWord.objects.filter(id=q_id).exists():
                    q_obj = WATWord.objects.get(id=q_id)
                    ideal_concepts = f"Positive association with {q_obj.word}: {q_obj.ideal_response_hint}"

            elif test_type == 'SRT':
                if SRTSituation.objects.filter(id=q_id).exists():
                    q_obj = SRTSituation.objects.get(id=q_id)
                    ideal_concepts = f"Action-oriented response: {q_obj.ideal_action_keywords}"

            elif test_type == 'TAT':
                if TATImage.objects.filter(id=q_id).exists():
                    q_obj = TATImage.objects.get(id=q_id)
                    ideal_concepts = f"Story theme: {q_obj.theme}"

            elif test_type == 'SDT':
                if SDTPrompt.objects.filter(id=q_id).exists():
                    q_obj = SDTPrompt.objects.get(id=q_id)
                    ideal_concepts = f"Self-reflection qualities: {q_obj.expected_qualities}"
                
        except Exception as e:
            print(f"⚠️ Context Lookup Error: {e}")
    
    print(f"🎯 Type: {test_type} | AI Checking Against: {ideal_concepts}") 

    # 3. AI Call
    # score, feedback = calculate_score(user_ans, ideal_concepts)

    # olq_data = get_olq_scores(user_ans)

    # 4. Save
    new_response=CandidateResponse.objects.create(
        candidate=candidate,
        session_id=session_id,
        question_id=q_id if q_id else 0,
        test_type=test_type,
        transcript=user_ans,
        score=0.0, # Initially zero
        feedback="Processing",
        olq_scores={},
        voice_analysis={}

    )
    # 4. START BACKGROUND THREAD (Magic Step)
    # Ye AI ko alag process mein chalayega, User ko nahi rokega
    thread = threading.Thread(target=run_ai_analysis, args=(new_response.id, user_ans, ideal_concepts))
    thread.start()
    
    # 5. INSTANT RESPONSE TO FRONTEND
    return Response({"status": "Queued for Analysis"})
    # return Response({"status": "Saved", "score": score, "feedback": feedback})

from django.db.models import Avg

@api_view(['GET'])
def get_candidate_report(request):
    # 1. Session ID lo
    session_id = request.query_params.get('session_id')
    
    if not session_id:
        return Response({"error": "Session ID required"}, status=400)

    # 2. Responses nikalo
    all_responses = CandidateResponse.objects.filter(session_id=session_id).order_by('timestamp')
    
    if not all_responses.exists():
         return Response({"error": "No data for this session"}, status=404)

    # --- FIX IS HERE (Ye line missing thi) ---
    # Pehle response se candidate ki info nikalo
    candidate = all_responses.first().candidate 
    # -----------------------------------------
    final_olq_map = {olq: 0.0 for olq in [
        "Effective Intelligence", "Reasoning Ability", "Organizing Ability", "Power of Expression",
        "Social Adaptability", "Cooperation", "Sense of Responsibility",
        "Initiative", "Self Confidence", "Speed of Decision", "Ability to Influence", "Liveliness",
        "Determination", "Courage", "Stamina"
    ]}

    response_count = all_responses.count()
    for resp in all_responses:
        if resp.olq_scores:
            for olq, score in resp.olq_scores.items():
                if olq in final_olq_map:
                    final_olq_map[olq] += score

    # Average karo
    sorted_olqs = sorted(final_olq_map.items(), key=lambda x: x[1], reverse=True)

    # Top 5 Strong & Weak Areas
    strong_olqs = [k for k, v in sorted_olqs[:5] if v > 0]
    weak_olqs = [k for k, v in sorted_olqs[-5:]]

    # 3. Averages Calculate karo
    avg_score = all_responses.aggregate(Avg('score'))['score__avg'] or 0
    avg_score = round(avg_score, 2)

    # 4. Verdict Logic
    verdict = "Recommended" if avg_score >= 6.0 else "Not Recommended"
    verdict_color = "green" if avg_score >= 6.0 else "red"

    # 5. Details prepare karo
    report_data = []
    for resp in all_responses:
        # Analysis method text
        method_used = "Semantic Similarity (SBERT)" if "SBERT" in (resp.feedback or "") else "Keyword Matching"
        
        report_data.append({
            "type": resp.test_type,
            "question": f"Q{resp.question_id}",
            "answer": resp.transcript,
            "score": resp.score,
            "feedback": resp.feedback,
            "method": method_used,
            "speech": resp.voice_analysis # <-- New Field Added
        })

    # 6. Final Response
    return Response({
        "candidate_name": candidate.name, 
        "overall_score": avg_score,
        "verdict": verdict,
        "verdict_color": verdict_color,
        "details": report_data,
        "olq_analysis": final_olq_map,   # <-- Poora Data Graph ke liye
        "strong_areas": strong_olqs,
        "weak_areas": weak_olqs
    })
from .serializers import CandidateSerializer

@api_view(['POST'])
def register_candidate(request):
    data = request.data
    # Naya candidate create karo
    serializer = CandidateSerializer(data=data)
    if serializer.is_valid():
        candidate = serializer.save()
        return Response({
            "status": "Registered",
            "candidate_id": candidate.id,
            "name": candidate.name,
            "session_id": candidate.session_id
        })
    return Response(serializer.errors, status=400)

from .models import OIRQuestion, PPDTImage

@api_view(['GET'])
def get_oir_questions(request):
    # OIR ke liye saare 10 questions ek saath bhej dete hain (Exam Mode)
    questions = list(OIRQuestion.objects.all())
    # Shuffle karke top 10 lelo (Agar future mein zyada hue toh)
    random.shuffle(questions)
    data = [{"id": q.id, "q": q.question_text, "options": {"A": q.option_a, "B": q.option_b, "C": q.option_c, "D": q.option_d}} for q in questions[:10]]
    return Response(data)

@api_view(['POST'])
def submit_oir(request):
    # OIR Scoring Logic (Simple Math)
    answers = request.data.get('answers', {}) # { "1": "A", "2": "B" }
    session_id = request.data.get('session_id')
    score = 0
    
    for q_id, user_ans in answers.items():
        try:
            correct = OIRQuestion.objects.get(id=q_id).correct_answer
            if user_ans == correct:
                score += 1
        except:
            pass
            
    # 10 mein se score save karo (CandidateResponse mein 'OIR' type se)
    # Yahan hum ek dummy 'OIR_SET' response banayenge
    candidate = Candidate.objects.get(session_id=session_id)
    CandidateResponse.objects.create(
        candidate=candidate, session_id=session_id,
        test_type="OIR", question_id=0, transcript=f"OIR Score: {score}/10",
        score=score, feedback="Objective Test Completed"
    )
    return Response({"score": score})

@api_view(['GET'])
def get_ppdt_image(request):
    img = PPDTImage.objects.first() # Abhi ek hi hai
    return Response({"id": img.id, "url": img.image_url, "title": img.title})

from .models import TATImage, SDTPrompt

@api_view(['GET'])
def get_tat_images(request):
    # SSB mein usually 11+1 images hoti hain, hum abhi 3 bhejenge
    images = list(TATImage.objects.all())
    serializer_data = [{"id": img.id, "url": img.image_url, "title": img.title} for img in images]
    return Response(serializer_data)

@api_view(['GET'])
def get_sdt_questions(request):
    prompts = SDTPrompt.objects.all()
    data = [{"id": p.id, "q": p.prompt_text} for p in prompts]
    return Response(data)

# --- HELPER: BACKGROUND AI PROCESSOR ---
def run_ai_analysis(response_id, user_ans, ideal_concepts):
    """
    Ye function background mein chalega taaki user ko wait na karna pade.
    """
    try:
        print(f"⚙️ Background Processing Started for ID: {response_id}")
        
        # 1. AI Score Calculation
        score, feedback = calculate_score(user_ans, ideal_concepts)
        
        # 2. OLQ Analysis
        olq_data = get_olq_scores(user_ans)

        # 2.5 Voice Tone Analysis
        voice_data = analyze_voice_tone(user_ans)
        
        # 3. Update Database (Dheere se save kar do)
        resp = CandidateResponse.objects.get(id=response_id)
        resp.score = score
        resp.feedback = feedback
        resp.olq_scores = olq_data
        resp.voice_analysis = voice_data
        resp.save()
        
        print(f"✅ AI Analysis Completed for ID: {response_id} | Score: {score}")
        
    except Exception as e:
        print(f"❌ Background Task Failed: {e}")