from django.contrib import admin
from .models import IdempotencyKey

admin.site.register(IdempotencyKey)
