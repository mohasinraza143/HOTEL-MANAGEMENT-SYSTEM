import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotelmanagement.settings')
django.setup()

from django.contrib.auth.models import User

username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@aurorahaven.com')

user, created = User.objects.get_or_create(username=username)
user.set_password(password)
user.email = email
user.is_staff = True
user.is_superuser = True
user.save()

print(f"Superuser '{username}' configured successfully with staff and superuser permissions.")
