import warnings
import numpy as np
from plotly import offline
import plotly.graph_objs as go
from datetime import datetime
from astropy.time import Time
from django import template
from django.conf import settings

from tom_dataproducts.models import DataProduct, ReducedDatum
from guardian.shortcuts import get_objects_for_user
from tom_dataproducts.processors.data_serializers import SpectrumSerializer

from tidestom.settings import BROKERS
lasair_token = BROKERS['LASAIR']['api_key']
from .spectroscopy_settings import add_snid_templates, add_ngsf_templates
from .photometry_settings import plot_lightcurves, fetch_ztf_lasair

register = template.Library()

@register.inclusion_tag('myplots/target_spectroscopy.html', takes_context=True)
def target_spectroscopy(context, target, dataproduct=None):
    """
    Renders a spectroscopic plot for a ``Target``. If a ``DataProduct`` is specified, it will only render a plot with
    that spectrum.
    """
    try:
        spectroscopy_data_type = settings.DATA_PRODUCT_TYPES['spectroscopy'][0]
    except (AttributeError, KeyError):
        spectroscopy_data_type = 'spectroscopy'
    spectral_dataproducts = DataProduct.objects.filter(target=target,
                                                       data_product_type=spectroscopy_data_type)
    if dataproduct:
        spectral_dataproducts = DataProduct.objects.get(data_product=dataproduct)
    if settings.TARGET_PERMISSIONS_ONLY:
        datums = ReducedDatum.objects.filter(data_product__in=spectral_dataproducts)
    else:
        datums = get_objects_for_user(context['request'].user,
                                      'tom_dataproducts.view_reduceddatum',
                                      klass=ReducedDatum.objects.filter(data_product__in=spectral_dataproducts))
    
    # Create a figure
    fig = go.Figure()
    
    # add spectra
    for datum in datums:
        deserialized = SpectrumSerializer().deserialize(datum.value)
        fig.add_trace(go.Scatter(
            x=deserialized.wavelength.value,
            y=deserialized.flux.value,
            #name=datetime.strftime(datum.timestamp, '%Y%m%d-%H:%M:%s'), 
            #name=target.name, 
            showlegend=False,
            hoverinfo='skip',
            line=dict(color="grey")
        ))
    
    # add templates - best matches
    # SNID - mock templates for now
    data_mean = np.mean(deserialized.flux.value)
    pysnid_file = '/home/tomas/Softwares/tests/pysnid/l1_obs_joined_87178841_snid.h5'
    fig = add_snid_templates(pysnid_file,
                             deserialized.wavelength.value, 
                             deserialized.flux.value, 
                             fig, 
                             n=3
                             )
    
    # NGSF - mock templates for now
    ngsf_file = '/home/tomas/Softwares/tests/ngsf/l1_obs_joined_87178841.csv'
    fig = add_ngsf_templates(ngsf_file, 
                             deserialized.wavelength.value, 
                             deserialized.flux.value, 
                             fig, 
                             n=3
                             )
    
    fig.update_layout(autosize=True, 
                      xaxis_title='Observed Wavelength (Å)',
                      yaxis_title='Flux (erg/s/cm²/Å)',
                      xaxis = dict(showticklabels=True, ticks='outside', linewidth=2),
                      yaxis = dict(showticklabels=True, ticks='outside', linewidth=2),
                      legend_title="Best Templates",
                      showlegend=True,
                      )

    return {
        'target': target,
        'plot': offline.plot(fig, output_type='div', show_link=False)
    }


##############
# Photometry #
##############

@register.inclusion_tag('myplots/target_photometry.html', takes_context=True)
def target_photometry(context, target, dataproduct=None):
    """
    Renders a photometry plot for a ``Target``. If a ``DataProduct`` is specified, it will only render a plot with
    that photometry.
    """
    # check if the Lasair's API key is set
    if lasair_token is None or lasair_token == "":
        warnings.warn("Warning: Lasair API key not set!", UserWarning)
        return {'target': target}
    
    photometry = fetch_ztf_lasair(49.1384664, 44.9725084)  # ZTF25aacedrs for testing
    #photometry = fetch_ztf_lasair(target.ra, target.dec)
    if photometry is None:
        return {'target': target}
    
    # plot photometry
    fig = plot_lightcurves(photometry)
    
    # add epochs with spectra
    try:
        spectroscopy_data_type = settings.DATA_PRODUCT_TYPES['spectroscopy'][0]
    except (AttributeError, KeyError):
        spectroscopy_data_type = 'spectroscopy'
    spectral_dataproducts = DataProduct.objects.filter(target=target,
                                                       data_product_type=spectroscopy_data_type)
    datums = ReducedDatum.objects.filter(data_product__in=spectral_dataproducts)
    for datum in datums:
        mjd = Time(datum.timestamp, scale="utc").mjd
        fig.add_vline(mjd, line_width=2, line_dash="dot", line_color="black", 
                            annotation_text="s", annotation_position="top left")
        
    return {
        'target': target,
        'plot': offline.plot(fig, output_type='div', show_link=False)
    }