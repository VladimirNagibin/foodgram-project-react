from django.http import HttpResponse
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import status
from rest_framework.response import Response


def get_pdf(ingredients, recipes, link):

    pdfmetrics.registerFont(
        TTFont('Ubuntu-Regular', 'data/Ubuntu-Regular.ttf', 'UTF-8')
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
    p.setFont('Ubuntu-Regular', font_big)
    p.drawString(x, y, 'FOODGRAM')
    p.linkURL(
        link,
        (x, y, x + head_length * inch, y + step_big),
        relative=1
    )
    y -= step_big
    p.setFont('Ubuntu-Regular', font_middle)
    p.drawString(x_start, y, 'Для приготовления выбранных блюд:')
    y -= step_big
    p.setFont('Ubuntu-Regular', font)
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
            p.setFont('Ubuntu-Regular', font)
    p.setFont('Ubuntu-Regular', font_middle)
    p.drawString(x_start, y, 'Требуются следующие ингредиенты:')
    y -= step_big
    if y <= 0:
        y = y_start
        p.showPage()
    p.setFont('Ubuntu-Regular', font)
    for ingredient in ingredients:
        p.drawString(
            x, y,
            (f'- {ingredient["name"]}, '
                f'{ingredient["amount"]} '
                f'{ingredient["measurement_unit"]}')
        )
        y -= step
        if y <= 0:
            y = y_start
            p.showPage()
            p.setFont('Ubuntu-Regular', font)

    p.showPage()
    p.save()
    return response


def add_option_user(option_serializer, pk, request):
    serializer = option_serializer(
        data={'user': request.user.id, 'recipe': pk},
        context={'request': request}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(
        serializer.data,
        status=status.HTTP_201_CREATED
    )


def remove_option_user(option_model, pk, request):
    option_user = option_model.objects.filter(user=request.user,
                                              recipe=pk)
    if option_user.exists():
        option_user.delete()
    else:
        return Response({'errors': 'Запись для удаления ещё не добавлена.'},
                        status=status.HTTP_400_BAD_REQUEST)
    return Response(status=status.HTTP_204_NO_CONTENT)
