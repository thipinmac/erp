"""URLs do módulo Cadastros."""
from django.urls import path
from . import views

app_name = "cadastros"

urlpatterns = [
    # Clientes
    path("clientes/", views.ClienteListView.as_view(), name="cliente_list"),
    path("clientes/novo/", views.ClienteCreateView.as_view(), name="cliente_create"),
    path("clientes/<uuid:pk>/", views.ClienteDetailView.as_view(), name="cliente_detail"),
    path("clientes/<uuid:pk>/editar/", views.ClienteUpdateView.as_view(), name="cliente_update"),
    path("clientes/<uuid:pk>/excluir/", views.ClienteDeleteView.as_view(), name="cliente_delete"),

    # Fornecedores
    path("fornecedores/", views.FornecedorListView.as_view(), name="fornecedor_list"),
    path("fornecedores/novo/", views.FornecedorCreateView.as_view(), name="fornecedor_create"),
    path("fornecedores/<uuid:pk>/", views.FornecedorDetailView.as_view(), name="fornecedor_detail"),
    path("fornecedores/<uuid:pk>/editar/", views.FornecedorUpdateView.as_view(), name="fornecedor_update"),

    # Itens / Materiais
    path("itens/", views.ItemListView.as_view(), name="item_list"),
    path("itens/novo/", views.ItemCreateView.as_view(), name="item_create"),
    path("itens/<uuid:pk>/", views.ItemDetailView.as_view(), name="item_detail"),
    path("itens/<uuid:pk>/editar/", views.ItemUpdateView.as_view(), name="item_update"),

    # HTMX: busca de cliente por nome (autocomplete)
    path("clientes/buscar/", views.buscar_clientes, name="cliente_buscar"),
    path("itens/buscar/", views.buscar_itens, name="item_buscar"),
]
