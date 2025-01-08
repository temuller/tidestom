import os
import pandas as pd
from django.core.management.base import BaseCommand
from tom_targets.models import Target
from tidestom.tides_utils.target_utils import create_target
### TODO: WRITE CORRECT DIRECTORY IN HER, USING AN ENVIRONMENT VARIABLE


class Command(BaseCommand):
    # Placeholder code that currently looks at a set of simulated spectra from Georgios.
    help = 'Add new targets from a distant directory'

    def handle(self, *args, **kwargs):
        #directory = os.environ['TARGET_DB']
        dbdf = pd.read_csv('/Users/pwise/4MOST/tides/testdata/mock_DB.csv', index_col=0)   
        for index, row in dbdf.iterrows(): 
            name=index
            if row['OBS_STATUS_4MOST']:  # Check if the target has been observed by 4MOST
                external_id = name
                other_fields = {
                    'ra': row['ra'],
                    'dec': row['dec'],
                    'created': row['MJD_DET']
                    # Add other fields as needed
                }

                # Check if the target already exists
                target, created = Target.objects.update_or_create(
                    name=name,
                    defaults=other_fields
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(f'Successfully added target {name}'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'Successfully updated target {name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Target {name} has not been observed by 4MOST and will not be added'))