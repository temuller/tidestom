from plotly import offline
import plotly.graph_objs as go
from datetime import datetime, timedelta
from django import template
from django.conf import settings

from tom_dataproducts.models import DataProduct, ReducedDatum
from guardian.shortcuts import get_objects_for_user
from tom_dataproducts.processors.data_serializers import SpectrumSerializer
from tom_targets.models import Target

from light_fetcher.transient import load_transient
from .photometry_settings import plot_lightcurves

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

def create_toggling_buttons(fig: go.Figure) -> list[dict, dict]:
    """Creates the buttons for toggling between magnitude and flux.

    Parameters
    ----------
    fig.: plotly figure.

    Returns
    -------
    buttons: magnitude/flux buttons.
    """
    mag_visibility = [False if "flux" in trace.name else True for trace in fig.data]
    flux_visibility = [False if "mag" in trace.name else True for trace in fig.data]
    buttons = [
        dict(
            label='Magnitude',
            method='update',
            args=[
                {'visible': mag_visibility},  # Show magnitude, hide flux
                {'yaxis': {'title': 'AB Magnitude', 'autorange': 'reversed'}}
            ]
        ),
        dict(
            label='Flux',
            method='update',
            args=[
                {'visible': flux_visibility},  # Show flux, hide magnitude
                {'yaxis': {'title': 'Flux (μJy)'}}
            ]
        )
    ]
    return buttons

@register.inclusion_tag('myplots/target_photometry.html', takes_context=True)
def target_photometry(context, target, dataproduct=None):
    """
    Renders a photometry plot for a ``Target``. If a ``DataProduct`` is specified, it will only render a plot with
    that photometry.
    """
    
    """
    try:
        photometry_data_type = settings.DATA_PRODUCT_TYPES['photometry'][0]
    except (AttributeError, KeyError):
        photometry_data_type = 'photometry'
    photometric_dataproducts = DataProduct.objects.filter(target=target,
                                                        data_product_type=photometry_data_type)
    if dataproduct:
        photometric_dataproducts = DataProduct.objects.get(data_product=dataproduct)
   
    plot_data = []
    if settings.TARGET_PERMISSIONS_ONLY:
        datums = ReducedDatum.objects.filter(data_product__in=photometric_dataproducts)
    else:
        datums = get_objects_for_user(context['request'].user,
                                      'tom_dataproducts.view_reduceddatum',
                                      klass=ReducedDatum.objects.filter(data_product__in=photometric_dataproducts))
    """
    #print("AAAAAAAAAAAAAAAa", datums)
    
    #"""
    # example light curve - THIS WORKS
    trace1 = go.Scatter(x=[1, 2, 3], y=[20, 19, 19.5], name="mag")
    trace1.visible = True
    trace2 = go.Scatter(x=[1, 2, 3], y=[2200, 3000, 2800], name="flux")
    trace2.visible = False
    
    # Create a figure
    fig = go.Figure()
    fig.add_trace(trace1)
    fig.add_trace(trace2)
    
    # Define buttons for toggling between magnitude and flux
    buttons = create_toggling_buttons(fig)

    # Update layout
    fig.update_layout(
        #title=f"SN XXX",
        xaxis_title="Modified Julian Date",
        yaxis_title="AB Magnitude",
        yaxis=dict(autorange='reversed',  # Inverted y-axis for magnitudes
                ),  
        #legend_title="Filters",
        #template="plotly_white",
        xaxis_tickformat = '%d',
        width=800,
        height=500,
        font_family="P052",
        font_size=16,

        updatemenus=[
            dict(
                type='buttons',
                showactive=True,
                buttons=buttons,
                direction='left',
                x=0.15,
                y=1.15,
                xanchor='center',
                yanchor='top'
            )
        ],
    )
    #"""
    
    # ToDO: need to somehow get the light curve form the database in the desired format
    #from pathlib import Path
    #target_file = Path(settings.BASE_DIR, 'data/photometry/test/', 'ZTF25aalzmga.lc')
    #phot_obj = load_transient(target_file)
    #fig = plot_lightcurves(phot_obj)

    return {
        'target': target,
        'plot': offline.plot(fig, output_type='div', show_link=False)
    }



###### Below is an example from the TOM Documentation
# @register.inclusion_tag('myplots/targets_reduceddata.html')
# def targets_reduceddata(targets=Target.objects.all()):
#     # order targets by creation date
#     targets = targets.order_by('-created')
#     # x axis: target names. y axis datum count
#     data = [go.Bar(
#         x=[target.name for target in targets],
#         y=[target.reduceddatum_set.count() for target in targets]
#     )]
#     # Create plot
#     figure = offline.plot(go.Figure(data=data), output_type='div', show_link=False)
#     # Add plot to the template context
#     return {'figure': figure}