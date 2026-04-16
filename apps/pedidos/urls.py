"""URLs do módulo Pedidos."""
from django.urls import path

from . import views

app_name = "pedidos"

urlpatterns = [
    path("", views.PedidoListView.as_view(), name="list"),
    path("kanban/", views.PedidoKanbanView, name="kanban"),
    path("novo/", views.PedidoCreateView.as_view(), name="create"),
    path("<uuid:pk>/", views.PedidoDetailView.as_view(), name="detail"),
    path("<uuid:pk>/status/", views.atualizar_status_pedido, name="atualizar_status"),
]
