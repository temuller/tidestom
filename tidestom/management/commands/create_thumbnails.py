import os
from django.core.management.base import BaseCommand
from tom_targets.models import Target
from tidestom.tides_utils.target_utils import generate_light_curve_plot, generate_spectrum_plot, add_spectrum_to_database

class Command(BaseCommand):
    help = 'Generate light curve and spectrum plots for existing targets and add the spectra to the database'
    def add_arguments(self, parser):
        # Define arguments directly using the parser provided by Django
        parser.add_argument('--test', type=bool, required=False, default=False, help='Is this a test run?')

    def handle(self, *args, **kwargs):
        
        targets = Target.objects.all()
        for target in targets:
            spectrum_file_path = f'/Users/pwise/4MOST/tides/testdata/spec_simulations/sims/l1_obs_joined_{target.name}.fits'
            if os.path.exists(spectrum_file_path):
                generate_spectrum_plot(target, spectrum_file_path)
                self.stdout.write(self.style.SUCCESS(f'Successfully updated plots for target {target.name}, {target.pk}'))
                print('Adding spectrum to database')
                result = add_spectrum_to_database(target, spectrum_file_path)
                if 'Error' in result:
                    self.stdout.write(self.style.ERROR(result))
                else:
                    self.stdout.write(self.style.SUCCESS(result))
            else:
                self.stdout.write(self.style.WARNING(f'Spectrum file for {target.name} does not exist'))