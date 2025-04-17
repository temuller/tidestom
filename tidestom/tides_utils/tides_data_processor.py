import os
from datetime import datetime
from astropy.time import Time
from tom_dataproducts.data_processor import DataProcessor
from tom_dataproducts.processors.data_serializers import SpectrumSerializer
from astropy.io import fits
from specutils import Spectrum1D
from astropy import units as u

import pytz
import numpy as np
import pandas as pd
from pathlib import Path

class QMOSTSpectroscopyProcessor(DataProcessor):
    def process_data(self, data_product,test=False):
        if os.path.basename(data_product.data.path).startswith('l1_obs_joined_'):

            spectrum, obs_date, source_id = self._process_test_spectrum(data_product)

        serialized_spectrum = SpectrumSerializer().serialize(spectrum)

        return [(obs_date, serialized_spectrum, source_id)]
    
    def _process_test_spectrum(self, data_product):
        spec=fits.getdata(data_product.data.path)
        wave = spec['WAVE'][0]*u.Angstrom
        flux = spec['FLUX'][0]*u.Unit('erg cm-2 s-1 AA-1')
        spectrum = Spectrum1D(flux=flux, spectral_axis=wave)
        return spectrum, Time(datetime.now()).to_datetime(), '4MOST' #TODO change obs date!
    
    def _process_L1_spectrum(self, data_product):
        '''Some code to process real 4MOST L1 spectra''' 


class QMOSTPhotometryProcessor(DataProcessor):
    def process_data(self, data_product, test=False):
        if Path(data_product.data.path).name.endswith('.csv'):
            obs_dates, phot_epochs, source_id = self._process_test_photometry(data_product)
        print(phot_epochs[0])
        print(obs_dates[0])

        return [(obs_date, phot_epoch, source_id) for obs_date, phot_epoch in zip(obs_dates, phot_epochs)]
    
    def _process_test_photometry(self, data_product):
        phot_df = pd.read_csv(data_product.data.path)
        obs_dates, phot_epochs = [], []
        for _, row in phot_df.iterrows():
            if not np.isnan(row["magnitude"]):
                phot_epochs.append({key: row[key] for key in row.keys() if key!="time"})
                obs_dates.append(Time(row["time"], format="mjd").to_datetime(timezone=pytz.UTC))
        #phot_dict = [{key: row[key] for key in row.keys() if key!="time"} for _, row in phot_df.iterrows()]
        return obs_dates, phot_epochs, '4MOST' #TODO change obs date!
