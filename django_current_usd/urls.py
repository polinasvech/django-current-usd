from django.urls import path
from django_current_usd.views import current_usd

urlpatterns = [
    path("get-current-usd/", current_usd),
]
