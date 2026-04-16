from django.urls import path

from . import views

app_name = "financeiro"

urlpatterns = [
    path("receber/", views.ReceberListView.as_view(), name="receber"),
    path("pagar/", views.PagarListView.as_view(), name="pagar"),
    path("dre/", views.DREView.as_view(), name="dre"),
    path("titulos/novo/", views.TituloCreateView.as_view(), name="titulo_create"),
    path("titulos/<uuid:pk>/baixar/", views.baixar_titulo, name="baixar"),
]
