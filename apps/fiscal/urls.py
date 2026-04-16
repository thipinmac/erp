from django.urls import path
from . import views

app_name = "fiscal"

urlpatterns = [
    path("", views.index, name="list"),
]
