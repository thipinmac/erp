"""URLs do módulo Engenharia e Projetos."""
from django.urls import path

from . import views

app_name = "engenharia"

urlpatterns = [
    # Projetos Técnicos
    path("", views.ProjetoTecnicoListView.as_view(), name="projeto_list"),
    path("projetos/novo/", views.ProjetoTecnicoCreateView.as_view(), name="projeto_create"),
    path("projetos/<uuid:pk>/", views.ProjetoTecnicoDetailView.as_view(), name="projeto_detail"),
    path("projetos/<uuid:pk>/liberar/", views.liberar_para_pcp, name="liberar_pcp"),

    # BOM
    path("bom/", views.BOMListView.as_view(), name="bom_list"),
]
