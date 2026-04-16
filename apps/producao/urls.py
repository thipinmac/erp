from django.urls import path

from . import views

app_name = "producao"

urlpatterns = [
    path("", views.KanbanProducaoView.as_view(), name="kanban"),
    path("ordens/", views.OrdemProducaoListView.as_view(), name="op_list"),
    path("ordens/nova/", views.OrdemProducaoCreateView.as_view(), name="op_create"),
    path("ordens/<uuid:pk>/", views.OrdemProducaoDetailView.as_view(), name="op_detail"),
    path("ordens/<uuid:pk>/apontar/", views.apontar_etapa, name="apontar"),
    path("ordens/<uuid:pk>/avancar/", views.avancar_status_op, name="avancar_status"),
    path("romaneios/", views.RomaneioListView.as_view(), name="romaneio_list"),
    path("romaneios/<uuid:pk>/", views.RomaneioDetailView.as_view(), name="romaneio_detail"),
]
