from django.urls import reverse


def object_link(obj):
    app_label = obj._meta.app_label
    model_label = obj._meta.model_name
    url = reverse(
        f'admin:{app_label}_{model_label}_change', args=(obj.id,)
    )
    return f'<a href="{url}">{obj.name}</a>'
