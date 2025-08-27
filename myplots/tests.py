from django.test import TestCase
#from tom_targets.tests.factories import SiderealTargetFactory
from tom_targets.models import Target

import warnings
import pandas as pd
from myplots.templatetags.photometry_settings import fetch_ztf_lasair, fetch_lsst_lasair
from tidestom.settings import BROKERS
lasair_ztf_token = BROKERS['LASAIR']['ztf_api_key']
lasair_lsst_token = BROKERS['LASAIR']['ztf_api_key']

class TestPhotometry(TestCase):
    def setUp(self):
        self.target = Target.objects.create(name='test_target')
        # ZTF25aacedrs
        self.target.ztf_ra = 49.1384664
        self.target.ztf_dec = 44.9725084
        # LSST placeholde
        self.target.lsst_ra = 0.0
        self.target.lsst_dec = 0.0
        
    def test_ztf_photometry(self):
        # ZTF
        if lasair_ztf_token is None or lasair_ztf_token == "":
            warnings.warn("Warning: Lasair ZTF keys not set!", UserWarning)
        else:
            ztf_photometry = fetch_ztf_lasair(self.target.ztf_ra, self.target.ztf_dec)
            assert isinstance(ztf_photometry, pd.DataFrame), f"Photometry object is not a DataFrame! Check {fetch_ztf_lasair}."
        # LSST
        if lasair_lsst_token is None or lasair_lsst_token == "":
            warnings.warn("Warning: Lasair LSST keys not set!", UserWarning)
        else:
            lsst_photometry = fetch_ztf_lasair(self.target.lsst_ra, self.target.lsst_dec)
            assert isinstance(lsst_photometry, pd.DataFrame), f"Photometry object is not a DataFrame! Check {fetch_lsst_lasair}."