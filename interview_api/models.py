from django.db import models

# 1. Candidate Profile (To make the interview adaptive)
class Candidate(models.Model):
    EXPERIENCE_CHOICES = [
        ('fresher', 'Fresher'),
        ('internship', 'Internship Experience'),
        ('working', 'Working Professional'),
    ]
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    name = models.CharField(max_length=100)
    age = models.IntegerField(default=21)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='M')
    
    # Detailed Profile
    experience_type = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES, default='fresher')
    stream = models.CharField(max_length=100, help_text="e.g., Computer Science, Commerce")
    grad_year = models.IntegerField(help_text="e.g., 2024", default=2024)
    
    # Session ID (Reporting ke liye zaroori hai)
    session_id = models.CharField(max_length=100, unique=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.experience_type})"
# 2. WAT (Word Association Test) Data Table
class WATWord(models.Model):
    word = models.CharField(max_length=50)
    ideal_response_hint = models.TextField(help_text="Hint from Dr. Natarajan's Book")
    time_limit = models.IntegerField(default=15, help_text="Time in seconds")

    def __str__(self):
        return self.word

# 3. SRT (Situation Reaction Test) Data Table
class SRTSituation(models.Model):
    situation_text = models.TextField()
    ideal_action_keywords = models.TextField(help_text="Comma separated keywords like 'jumps, saves'")
    time_limit = models.IntegerField(default=30)

    def __str__(self):
        return self.situation_text[:50] + "..."

# 4. Personal Interview Questions Table
class InterviewQuestion(models.Model):
    CATEGORY_CHOICES = [
        ('intro', 'Self Introduction'),
        ('work', 'Work History'),
        ('education', 'Education'),
        ('internship', 'Internship'),
        ('family', 'Family & Background'),
        ('general', 'General Awareness'),
    ]
    
    question_text = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    expected_points = models.TextField(help_text="Key points expected in answer (from Book)")
    evaluation_criteria = models.TextField(
        help_text="E.g., 'Honesty, Academic Performance' OR 'Leadership, Risk Taking'",
        default="General Awareness"
    )

    def __str__(self):
        return f"[{self.category}] {self.question_text[:50]}..."

# 5. Candidate Response (To store audio and scores)
class CandidateResponse(models.Model):
    session_id = models.CharField(max_length=50, null=True, blank=True)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    test_type = models.CharField(max_length=10, choices=[('WAT', 'WAT'), ('SRT', 'SRT'), ('PI', 'Interview')])
    question_id = models.IntegerField()  # ID of the WAT/SRT/Interview Question
    voice_analysis = models.JSONField(default=dict, blank=True)
    audio_file = models.FileField(upload_to='responses/audio/', blank=True, null=True)  # Real audio
    transcript = models.TextField(blank=True, null=True)  # Converted text (Whisper)
    
    score = models.FloatField(default=0.0)  # AI Score (0-10)
    feedback = models.TextField(blank=True, null=True)  # AI Improvement Tip
    olq_scores = models.JSONField(default=dict, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.candidate.name} - {self.test_type} Response"
    
# --- NEW ADDITIONS FOR STAGE 1 ---

class OIRQuestion(models.Model):
    question_text = models.TextField()
    option_a = models.CharField(max_length=100)
    option_b = models.CharField(max_length=100)
    option_c = models.CharField(max_length=100)
    option_d = models.CharField(max_length=100)
    correct_answer = models.CharField(max_length=1, help_text="A, B, C, or D")
    
    def __str__(self):
        return self.question_text[:50]

class PPDTImage(models.Model):
    title = models.CharField(max_length=100)
    image_url = models.CharField(max_length=200, help_text="URL or Local Path (e.g. /ppdt_1.jpg)")
    ideal_story_theme = models.TextField(help_text="Context for AI Scoring")

    def __str__(self):
        return self.title
    
# --- STAGE 2 PSYCHOLOGY ADDITIONS ---

class TATImage(models.Model):
    title = models.CharField(max_length=100)
    image_url = models.CharField(max_length=200, help_text="/tat_1.jpg")
    theme = models.TextField(help_text="Expected theme for AI scoring")

    def __str__(self):
        return self.title

class SDTPrompt(models.Model):
    prompt_text = models.CharField(max_length=200) # e.g., "What do your parents think of you?"
    expected_qualities = models.TextField(help_text="Qualities AI should look for")

    def __str__(self):
        return self.prompt_text