from django import template
from django.conf import settings
from tom_targets.models import Target, TargetExtra
register = template.Library()

@register.inclusion_tag('custom_code/partials/target_data.html')
def tides_target_data(target):
    """
    Displays the data of a target.
    """
    exclude_fields = ['name', 'tidesclass', 'tidesclass_other', 'tidesclass_subclass', 'auto_tidesclass', 'auto_tidesclass_other', 'auto_tidesclass_subclass', 'auto_tidesclass_prob', 'human_tidesclass', 'human_tidesclass_other', 'human_tidesclass_subclass']
    extras = {k['name']: target.extra_fields.get(k['name'], '') for k in settings.EXTRA_FIELDS if not k.get('hidden') and k['name'] not in exclude_fields}
    print(target.as_dict())  
    return {
        'target': target,
        'extras': extras
    }

@register.inclusion_tag('custom_code/partials/target_classifications.html')
def target_classifications(target):
    return {'target': target}