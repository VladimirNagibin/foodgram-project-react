import re

from django.core.exceptions import ValidationError


def validate_color(value):
    string = re.sub(r'\#[a-fA-F0-9]{6}', '', value)
    if string:
        raise ValidationError(
            'Значение цвета задано не корректно '
            # f'{"".join(sym for sym in set(string))}'
        )
    return value
