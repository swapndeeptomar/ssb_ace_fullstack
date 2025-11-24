from rest_framework import serializers
from .models import WATWord, SRTSituation, InterviewQuestion, CandidateResponse, Candidate

class WATSerializer(serializers.ModelSerializer):
    class Meta:
        model = WATWord
        fields = '__all__'

class SRTSerializer(serializers.ModelSerializer):
    class Meta:
        model = SRTSituation
        fields = '__all__'

class InterviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewQuestion
        fields = '__all__'

class ResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateResponse
        fields = '__all__'

# interview_api/serializers.py mein ye add kar dena:
class CandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = '__all__'