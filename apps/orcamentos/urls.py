"""URLs do módulo Orçamentos."""
from django.urls import path
from . import views

app_name = "orcamentos"

urlpatterns = [
    path("", views.OrcamentoListView.as_view(), name="list"),
    path("rapido/novo/", views.OrcamentoRapidoCreateView.as_view(), name="rapido_create"),
    path("rapido/<uuid:pk>/", views.OrcamentoRapidoDetailView.as_view(), name="rapido_detail"),
    path("tecnico/novo/", views.OrcamentoTecnicoCreateView.as_view(), name="tecnico_create"),
    path("tecnico/<uuid:pk>/", views.OrcamentoTecnicoDetailView.as_view(), name="tecnico_detail"),
    path("tecnico/<uuid:pk>/editar/", views.OrcamentoTecnicoUpdateView.as_view(), name="tecnico_update"),
    path("tecnico/<uuid:pk>/aprovar/", views.aprovar_orcamento, name="aprovar"),
    path("tecnico/<uuid:pk>/item/adicionar/", views.adicionar_item, name="item_add"),
    path("item/<uuid:pk>/editar/", views.editar_item, name="item_edit"),
    path("item/<uuid:pk>/excluir/", views.excluir_item, name="item_delete"),
    path("tecnico/<uuid:pk>/recalcular/", views.recalcular_orcamento, name="recalcular"),
    path("tecnico/<uuid:pk>/pdf/", views.gerar_pdf, name="pdf"),
]
