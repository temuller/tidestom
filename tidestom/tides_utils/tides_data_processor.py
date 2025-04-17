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




##############
# Photometry #
##############

class PhotometrySerializer():
    def serialize(self, photometry: pd.DataFrame) -> tuple[list, list]:
        """
        Serializes photometry in order to store in a ReducedDatum object. The serialization stores only what's
        necessary to rebuild the photometry dataframe.

        :param photometry: photometry dataframe.

        :returns: observed dates (list) and photometric epochs (list)
        """
        obs_dates, phot_epochs = [], []
        for _, row in photometry.iterrows():
            epoch = {}
            for key in photometry.columns:
                if isinstance(row[key], float):
                    if np.isnan(row[key]):
                        # convert NaN to number
                        epoch[key] = -99
                    else:    
                        epoch[key] = row[key]
                else:    
                    epoch[key] = row[key]
            phot_epochs.append(epoch)
            obs_date = Time(row["mjd"], format="mjd").to_datetime(timezone=pytz.UTC)
            obs_dates.append(obs_date)
        return obs_dates, phot_epochs

    def deserialize(self, datums: list) -> pd.DataFrame:
        """
        Constructs photometry from a set of ReducedDatums

        :param datums list with photometric epochs

        :returns: photometry data frame
        """
        photometry = {}
        for datum in datums:
            for key, value in datum.value.items():
                if key not in photometry.keys():
                    photometry[key] = [value]
                else:
                    photometry[key].append(value)
        photometry = pd.DataFrame(photometry)
        photometry.replace(-99, np.nan, inplace=True)
        photometry.rename(columns={"magnitude":"mag", "error":"mag_err", "filter":"filt"}, inplace=True)
        
        return photometry

class QMOSTPhotometryProcessor(DataProcessor):
    def process_data(self, data_product, test=False):
        if Path(data_product.data.path).name.endswith('.csv'):
            obs_dates, phot_epochs, source_id = self._process_test_photometry(data_product)
        print(phot_epochs)
            
        return [(obs_date, phot_epoch, source_id) for obs_date, phot_epoch in zip(obs_dates, phot_epochs)]
    
    def _process_test_photometry(self, data_product):
        phot_df = pd.read_csv(data_product.data.path)
        obs_dates, phot_epochs = PhotometrySerializer().serialize(phot_df)
        return obs_dates, phot_epochs, 'light_fetcher'
