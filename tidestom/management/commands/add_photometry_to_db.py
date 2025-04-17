import os
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path  # Import pathlib

from django.core.management.base import BaseCommand
from django.conf import settings
from custom_code.models import TidesTarget as Target
from custom_code.models import TidesClassSubClass
from tom_dataproducts.models import DataProduct
from tidestom.tides_utils.target_utils import add_photometry_to_database, generate_light_curve_plot

# Configure logging
logging.basicConfig(
    filename=f'/Users/pwise/4MOST/tides/tidestom/logs/add_spectra_to_db_{datetime.now().strftime("%Y%m%d%H%M%S")}.log',  # Replace with your desired logfile path
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

class Command(BaseCommand):
    help = 'Add spectra to the database and update auto classifications'

    def add_arguments(self, parser):
        parser.add_argument('--mock', action='store_true', help='Add photometry from mock database')
        parser.add_argument('--photometry', action='store_true', help='Generate mock photometry')

    def handle(self, *args, **kwargs):
        if kwargs['mock']:
            self.add_photometry_from_mock_db()
        elif kwargs['photometry']:
            self.generate_mock_photometry()
        else:
            logging.error("Either --mock or --photometry option must be specified")

    def add_photometry_from_mock_db(self):
        test_data_dir = Path(settings.BASE_DIR) / 'data/photometry/test'
        test_data_dir.mkdir(parents=True, exist_ok=True)
        target_csv_path = os.path.join(settings.TEST_DIR, "mock_DB.csv")

        if not os.path.exists(target_csv_path):
            self.stdout.write(self.style.ERROR(f"Target CSV file not found at {target_csv_path}"))
            return
        
        #dbdf = pd.read_csv(target_csv_path, index_col=0)
        targets = Target.objects.all()
        for target in targets:
            photometry_file_path = os.path.join(settings.TEST_DIR,f'lcs/{target.name}.csv')
            if os.path.exists(photometry_file_path):
                # Check if the photometry already exists in the database
                #photometry_exists = DataProduct.objects.filter(target=target, data=photometry_file_path).exists()
                photometry_exists = False
                if not photometry_exists:
                    generate_light_curve_plot(target, photometry_file_path)
                    logging.info(f'Successfully updated plots for target {target.name}')
                    result = add_photometry_to_database(target, photometry_file_path)
                    if 'Error' in result:
                        logging.error(result)
                    else:
                        logging.info(result)
                else:
                    logging.warning(f'Photometry for target {target.name} already exists in the database')

                
    def generate_mock_photometry(self):
        """Generates a set of light curves from a single mock object.
        
        The same target names used for the mock spectra are used to create the photometry.
        """
        from pathlib import Path
        test_data_dir = Path(settings.BASE_DIR) / 'data/photometry/test'
        test_data_dir.mkdir(parents=True, exist_ok=True)
        target_csv_path = os.path.join(settings.TEST_DIR, "mock_DB.csv")

        if not os.path.exists(target_csv_path):
            self.stdout.write(self.style.ERROR(f"Target CSV file not found at {target_csv_path}"))
            return
        
        dbdf = pd.read_csv(target_csv_path, index_col=0)
        mock_file = Path(settings.TEST_DIR, "lcs", "test.csv")
        mock_df = pd.read_csv(mock_file)
        # add a time column
        mock_df["time"] = mock_df.mjd.values
        mock_df["magnitude"] = mock_df.mag.values
        mock_df["error"] = mock_df.mag_err.values
        mock_df["filter"] = mock_df.filt.values
        print("Generating mock files...")
        for name in dbdf.index.values:
            outfile = Path(settings.TEST_DIR, "lcs", f"{name}.csv")
            mock_df[["time", "magnitude", "error", "filter"]].to_csv(outfile, index=False)
        print("Finished generating mock files!")