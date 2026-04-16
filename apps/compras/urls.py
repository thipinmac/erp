"""URLs do módulo Compras e Suprimentos."""
from django.urls import path

from . import views

app_name = "compras"

urlpatterns = [
    # Atalho para a raiz — lista de requisições
    path("", views.RequisicaoListView.as_view(), name="list"),

    # Requisições
    path("requisicoes/", views.RequisicaoListView.as_view(), name="requisicao_list"),

    # Pedidos de Compra
    path("pedidos/", views.PedidoCompraListView.as_view(), name="pedido_list"),
    path("pedidos/novo/", views.PedidoCompraCreateView.as_view(), name="pedido_create"),
    path("pedidos/<uuid:pk>/", views.PedidoCompraDetailView.as_view(), name="pedido_detail"),
    path("pedidos/<uuid:pk>/receber/", views.receber_pedido, name="receber_pedido"),

    # Recebimentos
    path("recebimentos/<uuid:pk>/", views.RecebimentoDetailView.as_view(), name="recebimento_detail"),
]
