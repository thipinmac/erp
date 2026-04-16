"""URLs do módulo Contratos."""
from django.urls import path

from . import views

app_name = "contratos"

urlpatterns = [
    path("", views.ContratoListView.as_view(), name="list"),
    path("novo/", views.ContratoCreateView.as_view(), name="create"),
    path("<uuid:pk>/", views.ContratoDetailView.as_view(), name="detail"),
    path("<uuid:pk>/assinar/", views.assinar_contrato, name="assinar"),
    path("<uuid:pk>/pdf/", views.gerar_pdf_contrato, name="pdf"),
]
