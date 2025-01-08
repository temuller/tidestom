import os
import pandas as pd
import logging
from django.core.management.base import BaseCommand
from tom_targets.models import Target
from tidestom.tides_utils.target_utils import generate_spectrum_plot, add_spectrum_to_database
from custom_code.models import TidesClass, TidesClassSubClass, TidesTarget
from tom_dataproducts.models import DataProduct
from datetime import datetime   
# Configure logging
logging.basicConfig(
    filename=f'/Users/pwise/4MOST/tides/tidestom/logs/add_spectra_to_db_{datetime.now().strftime("%Y%m%d%H%M%S")}',  # Replace with your desired logfile path
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

class Command(BaseCommand):
    help = 'Add spectra to the database and update auto classifications'

    def handle(self, *args, **kwargs):
        dbdf = pd.read_csv('/Users/pwise/4MOST/tides/testdata/mock_DB.csv', index_col=0)
        targets = Target.objects.all()
        for target in targets:
            spectrum_file_path = f'/Users/pwise/4MOST/tides/testdata/spec_simulations/sims/l1_obs_joined_{target.name}.fits'
            if os.path.exists(spectrum_file_path):
                # Check if the spectrum already exists in the database
                spectrum_exists = DataProduct.objects.filter(target=target, data=spectrum_file_path).exists()
                if not spectrum_exists:
                    generate_spectrum_plot(target, spectrum_file_path)
                    logging.info(f'Successfully updated plots for target {target.name}')
                    result = add_spectrum_to_database(target, spectrum_file_path)
                    if 'Error' in result:
                        logging.error(result)
                    else:
                        logging.info(result)
                else:
                    logging.warning(f'Spectrum for target {target.name} already exists in the database')

                # Add or update automatic classification
                logging.info(f'Checking auto classification for target {target.name}')
                int_name = int(target.name)
                if int_name in dbdf.index:
                    logging.info(f'Found target {target.name} in the database')
                    auto_class = dbdf.at[int_name, 'AutoClass']
                    auto_class_subclass = dbdf.at[int_name, 'AutoClass_SubClass']
                    auto_class_prob = dbdf.at[int_name, 'AutoClassProb']

                    if auto_class:
                        target.auto_tidesclass = auto_class
                        target.auto_tidesclass_prob = auto_class_prob

                        if auto_class_subclass:
                            try:
                                subclass_instance = TidesClassSubClass.objects.get(main_class__name=auto_class, sub_class=auto_class_subclass)
                                target.auto_tidesclass_subclass = subclass_instance
                            except TidesClassSubClass.DoesNotExist:
                                logging.warning(f'Sub-class {auto_class_subclass} for class {auto_class} does not exist')

                        target.save()
                        logging.info(f'Added/Updated auto classification for target {target.name}')
            else:
                logging.warning(f'Spectrum file for {target.name} does not exist')
        self.stdout.write(self.style.SUCCESS('Completed processing all targets'))
        logging.info('Completed processing all targets')