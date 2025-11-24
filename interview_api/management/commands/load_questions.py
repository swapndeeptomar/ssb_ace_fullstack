import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from interview_api.models import WATWord, SRTSituation, InterviewQuestion

class Command(BaseCommand):
    help = 'Loads Expanded SSB Data into Database'

    def handle(self, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, 'ssb_data.json')
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File Missing: {file_path}'))
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 1. Load WAT
        wat_list = data.get('stage_2_psych', {}).get('WAT', [])
        for item in wat_list:
            WATWord.objects.get_or_create(word=item['word'], defaults={
                'ideal_response_hint': item['ideal_response_hint'],
                'time_limit': item['time_limit']
            })
        self.stdout.write(f"Loaded {len(wat_list)} WAT Words")

        # 2. Load SRT
        srt_list = data.get('stage_2_psych', {}).get('SRT', [])
        for item in srt_list:
            keywords = item['ideal_action_keywords']
            keywords_str = ", ".join(keywords) if isinstance(keywords, list) else str(keywords)
            
            SRTSituation.objects.get_or_create(situation_text=item['situation'], defaults={
                'ideal_action_keywords': keywords_str,
                'time_limit': item['time_limit']
            })
        self.stdout.write(f"Loaded {len(srt_list)} SRT Situations")

        # 3. Load Interview (Smart Categorization)
        pi_data = data.get('personal_interview', {})
        count = 0
        for key, val in pi_data.items():
            # Key se Category nikalo (e.g. 'internship_1' -> 'internship')
            key_lower = key.lower()
            category = 'general'
            
            if 'intro' in key_lower: 
                category = 'intro'      # Special Category for Q1
            elif 'internship' in key_lower: 
                category = 'internship'
            elif 'work' in key_lower: 
                category = 'work'
            elif 'edu' in key_lower: 
                category = 'education'
            elif 'family' in key_lower: 
                category = 'family'
            # --------------------------
            # Fix List vs String issue for points
            points = val.get('expected_points', '')
            points_str = ", ".join(points) if isinstance(points, list) else str(points)

            InterviewQuestion.objects.update_or_create(
                question_text=val['intro'],
                defaults={
                    'category': category,
                    'expected_points': points_str,
                    'evaluation_criteria': val.get('criteria', 'General Awareness')
                }
            )
            count += 1
            
        self.stdout.write(self.style.SUCCESS(f'Successfully Loaded {count} Interview Questions!'))