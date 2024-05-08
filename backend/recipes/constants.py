NAME_MAX_LENGHT = 200
TEXT_LIMIT = 50
SLUG_MAX_LENGHT = 200
COLOR_MAX_LENGHT = 7
COOKING_MIN_TIME = 1
AMOUNT_MIN_VALUE = 1
MEASU_CHOICES = (
    ('банка', 'банка'),
    ('батон', 'батон'),
    ('бутылка', 'бутылка'),
    ('веточка', 'веточка'),
    ('г', 'г'),
    ('горсть', 'горсть'),
    ('долька', 'долька'),
    ('звездочка', 'звездочка'),
    ('зубчик', 'зубчик'),
    ('капля', 'капля'),
    ('кг', 'кг'),
    ('кусок', 'кусок'),
    ('л', 'л'),
    ('лист', 'лист'),
    ('мл', 'мл'),
    ('пакет', 'пакет'),
    ('пакетик', 'пакетик'),
    ('пачка', 'пачка'),
    ('пласт', 'пласт'),
    ('по вкусу', 'по вкусу'),
    ('пучок', 'пучок'),
    ('ст. л.', 'ст. л.'),
    ('стакан', 'стакан'),
    ('стебель', 'стебель'),
    ('стручок', 'стручок'),
    ('тушка', 'тушка'),
    ('упаковка', 'упаковка'),
    ('ч. л.', 'ч. л.'),
    ('шт.', 'шт.'),
    ('щепотка', 'щепотка'),
)
MEASU_MAX_LENGHT = max([len(measu) for measu, _ in MEASU_CHOICES])
BOOL_CHOICES = ((0, 'False'), (1, 'True'))
IMAGE_SIZE = 100
