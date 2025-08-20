from plotly import offline
import plotly.graph_objs as go
from datetime import datetime
from astropy.time import Time
from django import template
from django.conf import settings

from tom_dataproducts.models import DataProduct, ReducedDatum
from guardian.shortcuts import get_objects_for_user
from tom_dataproducts.processors.data_serializers import SpectrumSerializer
from tom_targets.models import Target

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

    plot_data = []
    if settings.TARGET_PERMISSIONS_ONLY:
        datums = ReducedDatum.objects.filter(data_product__in=spectral_dataproducts)
    else:
        datums = get_objects_for_user(context['request'].user,
                                      'tom_dataproducts.view_reduceddatum',
                                      klass=ReducedDatum.objects.filter(data_product__in=spectral_dataproducts))
    for datum in datums:
        deserialized = SpectrumSerializer().deserialize(datum.value)
        plot_data.append(go.Scatter(
            x=deserialized.wavelength.value,
            y=deserialized.flux.value,
            name=datetime.strftime(datum.timestamp, '%Y%m%d-%H:%M:%s')
        ))
    # Create a figure
    fig = go.Figure(data=plot_data)

    fig.update_layout(autosize=True, 
                      xaxis_title='Observed Wavelength [Å] ',
                      yaxis_title='Flux',
                      xaxis = dict(showticklabels=True, ticks='outside', linewidth=2),
                      yaxis = dict(showticklabels=True, ticks='outside', linewidth=2),
                      shapes=[])

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
    print('AAAAAAAAA')
    photometry = fetch_ztf_lasair(49.1384664, 44.9725084)  # ZTF25aacedrs for testing
    #photometry = fetch_ztf_lasair(target.ra, target.dec)
    print(photometry)
    
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
