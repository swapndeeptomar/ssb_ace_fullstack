import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from interview_api.models import OIRQuestion, PPDTImage, TATImage, SDTPrompt

class Command(BaseCommand):
    help = 'Loads OIR and PPDT Data'

    def handle(self, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, 'screening_data.json')
        with open(file_path, 'r') as f:
            data = json.load(f)

        # Load OIR
        for item in data['OIR']:
            OIRQuestion.objects.get_or_create(
                question_text=item['q'],
                defaults={'option_a': item['a'], 'option_b': item['b'], 'option_c': item['c'], 'option_d': item['d'], 'correct_answer': item['ans']}
            )
            
        # Load PPDT
        for item in data['PPDT']:
            PPDTImage.objects.get_or_create(
                title=item['title'],
                defaults={'image_url': item['image_url'], 'ideal_story_theme': item['theme']}
            )
        tat_list = data.get('TAT', [])
        for item in tat_list:
            TATImage.objects.get_or_create(
                title=item['title'],
                defaults={'image_url': item['image_url'], 'theme': item['theme']}
            )
        
        # Load SDT
        sdt_list = data.get('SDT', [])
        for item in sdt_list:
            SDTPrompt.objects.get_or_create(
                prompt_text=item['prompt'],
                defaults={'expected_qualities': item['expected']}
            )
        self.stdout.write(self.style.SUCCESS('Screening Data Loaded!'))