from django.http import HttpResponse
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


def get_pdf(ingredients, recipes, link):

    pdfmetrics.registerFont(
        TTFont('Ubuntu-Regular', 'Ubuntu-Regular.ttf', 'UTF-8')
    )
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = ('attachment;'
                                       'filename="ingredients.pdf"')
    y_start = 600
    y = 750
    x = 100
    x_start = 10
    size = 1
    size_recipe = 0.5
    step = 20
    step_big = 50
    font = 20
    font_big = 50
    font_middle = 25
    max_length = 40
    head_length = 5
    logo_path = '../static/logo192.png'

    p = canvas.Canvas(response)
    try:
        p.drawImage(
            ImageReader(logo_path), x_start, y, size * inch, size * inch
        )
    except Exception:
        ...
    p.setFont("Ubuntu-Regular", font_big)
    p.drawString(x, y, 'FOODGRAM')
    p.linkURL(
        link,
        (x, y, x + head_length * inch, y + step_big),
        relative=1
    )
    y -= step_big
    p.setFont("Ubuntu-Regular", font_middle)
    p.drawString(x_start, y, "Для приготовления выбранных блюд:")
    y -= step_big
    p.setFont("Ubuntu-Regular", font)
    for recipe in recipes:
        image = ImageReader(recipe.image)
        p.drawImage(
            image,
            x_start + step,
            y,
            size_recipe * inch,
            size_recipe * inch,
        )
        p.drawString(
            x, y, f'{recipe.name[:max_length]}'
        )
        y -= step_big
        if y <= 0:
            y = y_start
            p.showPage()
            p.setFont("Ubuntu-Regular", font)
    p.setFont("Ubuntu-Regular", font_middle)
    p.drawString(x_start, y, "Требуются следующие ингредиенты:")
    y -= step_big
    if y <= 0:
        y = y_start
        p.showPage()
    p.setFont("Ubuntu-Regular", font)
    for ingredient in ingredients:
        p.drawString(
            x, y,
            (f'- {ingredient["ingredients__name"]}, '
                f'{ingredient["amount"]} '
                f'{ingredient["ingredients__measurement_unit"]}')
        )
        y -= step
        if y <= 0:
            y = y_start
            p.showPage()
            p.setFont("Ubuntu-Regular", font)

    p.showPage()
    p.save()
    return response
