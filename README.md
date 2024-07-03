![workflow status](https://github.com/VladimirNagibin/foodgram-project-react/actions/workflows/main.yml/badge.svg)

### О проекте: 

**Проект для демонстрации полного цикла разработки и деплоя приложения, созданного при помощи фреймворка Django.**

«Фудграм» — сайт, на котором пользователи публикуют рецепты, добавляют чужие рецепты в избранное и подписываются на публикации других авторов. Пользователям сайта также доступен сервис «Список покупок». Он создаёт список продуктов, которые нужно купить для приготовления выбранных блюд.

Проект запускается на удалённом сервере в контейнерах. Для CI/CD используется GitHub Action.
При push происходит автоматическое тестирование и если тесты прошли успешно и push в ветку main тогда выполняется обновление образов на Docker Hub.
Затем на сервере запускаются контейнеры из обновлённых образов.
Если значения переменных LOAD_DATA и CREATE_SUPERUSER в Actions установлено в true, тогда будет запущена загрузка тестовых данных и создание суперпользователя соответственно. 
При успешном завершении процесса приходит отчёт в Telegram.  

**Используемые технологии:**

- django
- DRF
- djoser
- gunicorn
- psycopg
- reportlab

**Фронтенд создан в виде SPA-приложения на React** 

**Для CI/CD используются:**

- Docker Compose
- GitHub Action

### Запуск проекта локально:

Склонируйте проект:

```
git clone https://github.com/VladimirNagibin/foodgram-project-react.git
```

Создайте файл .env. Тестовые данные можно взять из .env.example.  

Перейдите в директорию foodgram-project-react и запустите сервисы:

```
cd foodgram-project-react
```

```
sudo docker compose stop && sudo docker compose up --build
```

Сайт будет доступен по адресу http://127.0.0.1:8080


### Как развернуть проект:

Для разворачивания проекта требуется сервер с доступом по SSh ключу.
На сервере нужно установить и настроить сервер nginx для переадресации внешних запросов в контейнер на порт 8090. 
В домашней директории на сервере необходимо создать папку foodgram/.
В эту папку поместить файл .env с переменными окружения.

Состав .env:
- POSTGRES_USER= имя пользователя БД
- POSTGRES_PASSWORD= пароль пользователя БД
- POSTGRES_DB= имя базы данных БД
- DB_HOST= адрес сервера
- DB_PORT= порт
- SECRET_KEY= секретный ключ Django
- ALLOWED_HOSTS= строка с разрешёнными хостами через пробел
- DEBUG= режим отладки
- DB_SQLITE= если задано, тогда подключается база данных SQLite
- SUPERUSER_USERNAME= имя суперпользователя
- SUPERUSER_EMAIL= почта суперпользователя 
- SUPERUSER_PASSWORD= пароль суперпользователя

В репозитории создать secrets с приватными данными для GitHub Actions:
- DOCKER_USERNAME - логин для Docker Hub
- DOCKER_PASSWORD - пароль для Docker Hub
- HOST - адрес сервера
- USER - имя пользователя
- SSH_KEY - закрытый SSH-ключ
- SSH_PASSPHRASE - passphrase для ключа 
- SECRET_KEY - секретный ключ Django
- TELEGRAM_TO - ID телеграмм аккаунта
- TELEGRAM_TOKEN - токен бота

Variables репозитория:
- LOAD_DATA - если установлен в true тогда будут загружены тестовые данные из файлов в папке data и скопированы картинки.
- CREATE_SUPERUSER - если true тогда будет создан суперпользователь с данными из .env

Склонируйте проект:

```
git clone https://github.com/VladimirNagibin/foodgram-project-react.git
```

После push в ветку main запустится процесс тестирования и деплоя на удалённый сервер. Если заданы настройки, тогда будут загружены тестовые данные и создан суперпользователь.

- Адрес сайта: https://foodgram-vl.zapto.org


Данные superuser при автоматической загрузке:
- login: superuser@mail.ru
- password: superuser_password

____

**Владимир Нагибин** 

Github: [@VladimirNagibin](https://github.com/VladimirNagibin/)