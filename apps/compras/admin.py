"""Admin do módulo Compras e Suprimentos."""
from django.contrib import admin

from .models import (
    Cotacao,
    ItemCotacao,
    ItemPedidoCompra,
    ItemRecebimento,
    PedidoCompra,
    Recebimento,
    RequisicaoCompra,
)


@admin.register(RequisicaoCompra)
class RequisicaoCompraAdmin(admin.ModelAdmin):
    list_display = ("numero", "item", "quantidade", "prioridade", "status", "origem", "responsavel")
    list_filter = ("status", "prioridade", "origem", "empresa")
    search_fields = ("numero", "item__descricao")
    readonly_fields = ("criado_em", "alterado_em")


class ItemCotacaoInline(admin.TabularInline):
    model = ItemCotacao
    extra = 0
    fields = ("fornecedor", "item", "quantidade", "preco_unitario", "frete", "prazo_entrega_dias", "vencedor")


@admin.register(Cotacao)
class CotacaoAdmin(admin.ModelAdmin):
    list_display = ("numero", "status", "validade", "responsavel")
    list_filter = ("status", "empresa")
    search_fields = ("numero",)
    filter_horizontal = ("requisicoes",)
    inlines = [ItemCotacaoInline]


@admin.register(ItemCotacao)
class ItemCotacaoAdmin(admin.ModelAdmin):
    list_display = ("cotacao", "fornecedor", "item", "quantidade", "preco_unitario", "vencedor")
    list_filter = ("vencedor", "empresa")
    search_fields = ("cotacao__numero", "fornecedor__nome", "item__descricao")


class ItemPedidoCompraInline(admin.TabularInline):
    model = ItemPedidoCompra
    extra = 0
    fields = ("item", "quantidade", "quantidade_recebida", "preco_unitario", "total")
    readonly_fields = ("total",)


@admin.register(PedidoCompra)
class PedidoCompraAdmin(admin.ModelAdmin):
    list_display = ("numero", "fornecedor", "valor_total", "status", "data_emissao", "data_prevista_entrega")
    list_filter = ("status", "empresa")
    search_fields = ("numero", "fornecedor__nome")
    readonly_fields = ("criado_em", "alterado_em")
    inlines = [ItemPedidoCompraInline]


@admin.register(ItemPedidoCompra)
class ItemPedidoCompraAdmin(admin.ModelAdmin):
    list_display = ("pedido", "item", "quantidade", "quantidade_recebida", "preco_unitario", "total")
    search_fields = ("pedido__numero", "item__descricao")
    readonly_fields = ("total",)


class ItemRecebimentoInline(admin.TabularInline):
    model = ItemRecebimento
    extra = 0
    fields = ("item", "quantidade_pedida", "quantidade_recebida", "quantidade_divergencia", "custo_unitario", "aceito")
    readonly_fields = ("quantidade_divergencia", "custo_total")


@admin.register(Recebimento)
class RecebimentoAdmin(admin.ModelAdmin):
    list_display = ("pedido_compra", "data", "status", "chave_nfe", "responsavel")
    list_filter = ("status", "empresa")
    search_fields = ("pedido_compra__numero", "chave_nfe")
    readonly_fields = ("criado_em",)
    inlines = [ItemRecebimentoInline]


@admin.register(ItemRecebimento)
class ItemRecebimentoAdmin(admin.ModelAdmin):
    list_display = ("recebimento", "item", "quantidade_pedida", "quantidade_recebida", "quantidade_divergencia", "aceito")
    list_filter = ("aceito", "empresa")
    search_fields = ("item__descricao",)
    readonly_fields = ("quantidade_divergencia", "custo_total")
