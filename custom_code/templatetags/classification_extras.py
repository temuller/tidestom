from django import template
from django.shortcuts import get_object_or_404
from ..models import TidesTarget
from ..forms import TidesTargetForm

register = template.Library()

@register.inclusion_tag('custom_code/partials/classification_form.html', takes_context=True)
def classification_form(context, target_id):
    """
    Renders the human classification submission form for a given target.
    """
    target = get_object_or_404(TidesTarget, id=target_id)
    form = TidesTargetForm()
    return {
        'form': form,
        'target': target,
        'request': context['request']
    }