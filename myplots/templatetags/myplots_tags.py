from plotly import offline
import plotly.graph_objs as go
from datetime import datetime, timedelta
from django import template
from django.conf import settings

from tom_dataproducts.models import DataProduct, ReducedDatum
from guardian.shortcuts import get_objects_for_user
from tom_dataproducts.processors.data_serializers import SpectrumSerializer
from tom_targets.models import Target

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

    # Add a vertical dashed line
    # fig.add_vline(x=2, line=dict(color = 'red', width=1), opacity=0.8, name="toggle-line")
    # toggle_line = go.Scatter(x=[2, 2], y=[-500,500], mode="lines", line=dict(color="red", width=1), name="toggle-line", visible="legendonly")
    # fig.add_trace(toggle_line)

    fig.update_layout(autosize=True, 
                      xaxis_title='Wavelength [Å] ',
                      yaxis_title='Flux',
                      shapes=[])

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