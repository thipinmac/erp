from django.urls import path

from . import views

app_name = "assistencia"

urlpatterns = [
    path("", views.ChamadoListView.as_view(), name="list"),
    path("novo/", views.ChamadoCreateView.as_view(), name="create"),
    path("<uuid:pk>/", views.ChamadoDetailView.as_view(), name="detail"),
    path("<uuid:pk>/encerrar/", views.encerrar_chamado, name="encerrar"),
]
