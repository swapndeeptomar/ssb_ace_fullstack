from django.contrib import admin
from .models import WATWord, SRTSituation, InterviewQuestion, Candidate, CandidateResponse

# 1. Questions ke liye Tables
admin.site.register(WATWord)
admin.site.register(SRTSituation)
admin.site.register(InterviewQuestion)

# 2. User aur uske Answers ke liye Tables
admin.site.register(Candidate)

# 3. Ye wala missing tha - Ab Responses dikhenge
class ResponseAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'test_type', 'score', 'timestamp') # List mein kya dikhe
    list_filter = ('test_type',) # Filter karne ka option

admin.site.register(CandidateResponse, ResponseAdmin)