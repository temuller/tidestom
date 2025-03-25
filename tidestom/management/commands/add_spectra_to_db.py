import os
import logging
import pandas as pd
from datetime import datetime
from django.core.management.base import BaseCommand
from tidestom.models import Target, DataProduct
from tidestom.utils import generate_spectrum_plot, add_spectrum_to_database

# Configure logging
logging.basicConfig(
    filename=f'/Users/pwise/4MOST/tides/tidestom/logs/add_spectra_to_db_{datetime.now().strftime("%Y%m%d%H%M%S")}.log',  # Replace with your desired logfile path
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

class Command(BaseCommand):
    help = 'Add spectra to the database and update auto classifications'

    def add_arguments(self, parser):
        parser.add_argument('--mock', action='store_true', help='Add spectra from mock database')
        parser.add_argument('--pipeline', action='store_true', help='Add spectra from pipeline results')
        parser.add_argument('--pipeline-results', type=str, help='Path to the pipeline results file')

    def handle(self, *args, **kwargs):
        if kwargs['mock']:
            self.add_spectra_from_mock_db()
        elif kwargs['pipeline']:
            pipeline_results_path = kwargs['pipeline_results']
            if not pipeline_results_path:
                logging.error("Pipeline results path must be provided when using --pipeline option")
                return
            self.add_spectra_from_pipeline(pipeline_results_path)
        else:
            logging.error("Either --mock or --pipeline option must be specified")

    def add_spectra_from_mock_db(self):
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
                        target.auto_tidesclass_subclass = auto_class_subclass
                        target.auto_tidesclass_prob = auto_class_prob
                        target.save()
                        logging.info(f'Updated auto classification for target {target.name}')
                    else:
                        logging.warning(f'No auto classification found for target {target.name}')
            else:
                logging.warning(f'Spectrum file {spectrum_file_path} not found for target {target.name}')

    def add_spectra_from_pipeline(self, pipeline_results_path):
        pipeline_results = pd.read_csv(pipeline_results_path)

        for _, row in pipeline_results.iterrows():
            obj_name = row['obj_name']
            spectrum_file_path = row['spectrum_file']
            auto_class = row.get('auto_class_agg')
            auto_class_subclass = row.get('auto_class_subclass_agg')
            auto_class_prob = row.get('auto_class_prob_agg')

            target = Target.objects.filter(name=obj_name).first()
            if not target:
                logging.warning(f'Target {obj_name} not found in the database')
                continue

            if not spectrum_file_path or not os.path.exists(spectrum_file_path):
                logging.warning(f'Spectrum file {spectrum_file_path} not found for target {obj_name}')
                continue

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
            if auto_class:
                target.auto_tidesclass = auto_class
                target.auto_tidesclass_subclass = auto_class_subclass
                target.auto_tidesclass_prob = auto_class_prob
                target.save()
                logging.info(f'Updated auto classification for target {target.name}')
            else:
                logging.warning(f'No auto classification found for target {target.name}')