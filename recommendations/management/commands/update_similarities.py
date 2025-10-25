from django.core.management.base import BaseCommand
from recommendations.models import RecommendationEngine
import time


class Command(BaseCommand):
    help = 'Update user and project similarities for recommendation system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Number of users to process in each batch'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=0.1,
            help='Delay between batches in seconds'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        delay = options['delay']
        
        self.stdout.write(
            self.style.SUCCESS('Starting similarity calculation...')
        )
        
        start_time = time.time()
        
        try:
            # Update similarities
            RecommendationEngine.update_similarities()
            
            end_time = time.time()
            duration = end_time - start_time
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully updated similarities in {duration:.2f} seconds'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error updating similarities: {str(e)}')
            )
