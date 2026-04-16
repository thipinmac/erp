"""URLs do módulo Estoque."""
from django.urls import path

from . import views

app_name = "estoque"

urlpatterns = [
    path("", views.SaldoEstoqueListView.as_view(), name="list"),
    path("movimentacoes/", views.MovimentacaoListView.as_view(), name="movimentacao_list"),
    path("sobras/", views.SobraListView.as_view(), name="sobra_list"),
    path("inventarios/", views.InventarioListView.as_view(), name="inventario_list"),
    path("reservas/", views.ReservaListView.as_view(), name="reserva_list"),
    path("entrada/", views.entrada_manual, name="entrada_manual"),
]
