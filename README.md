## TopBlogPosts

Это сайт блог, авторы могут выкладывать свои статьи для публичного доступа. Пользователи имеют возможность читать статьи, комментировать их, подписываться на понравившихся им авторов. 

##Установка: 

#1. Склонируйте репозиторий:

```git clone git@github.com:konmin123/TopBlogPosts.git```

#2. Создайте и активируйте вирутальное окружение:

```python -m venv venv```

```source venv/Scripts/activate```

#3. Установите зависимости:

```pip install -r requirements.txt```  

#4. Создайте текстовый файл .env.txt аналогично шаблону template.env.txt

#5. Проведите миграции:

```python manage.py makemigrations```

```python manage.py migrate```

#6. Создайте суперпользователя:

```python manage.py createsuperuser```

#7. Запустите тестовый сервер:

```python manage.py runserver```

