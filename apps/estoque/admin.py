"""Admin do módulo Estoque."""
from django.contrib import admin

from .models import (
    Inventario,
    ItemInventario,
    Localizacao,
    Lote,
    MovimentacaoEstoque,
    ReservaEstoque,
    SaldoEstoque,
    SobraChapa,
)


@admin.register(Localizacao)
class LocalizacaoAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo", "restricao_uso", "ativo", "empresa")
    list_filter = ("tipo", "ativo", "empresa")
    search_fields = ("nome",)


@admin.register(SaldoEstoque)
class SaldoEstoqueAdmin(admin.ModelAdmin):
    list_display = (
        "item", "localizacao", "saldo_atual", "saldo_reservado",
        "saldo_disponivel", "custo_medio", "ultima_movimentacao",
    )
    list_filter = ("empresa",)
    search_fields = ("item__descricao", "item__codigo")
    readonly_fields = ("saldo_disponivel", "ultima_movimentacao")


@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = ("codigo", "item", "fornecedor", "quantidade_atual", "data_validade", "ativo")
    list_filter = ("ativo", "empresa")
    search_fields = ("codigo", "item__descricao")
    readonly_fields = ("criado_em", "alterado_em")


@admin.register(MovimentacaoEstoque)
class MovimentacaoEstoqueAdmin(admin.ModelAdmin):
    list_display = ("tipo", "item", "quantidade", "custo_unitario", "custo_total", "usuario", "criado_em")
    list_filter = ("tipo", "empresa")
    search_fields = ("item__descricao", "motivo")
    readonly_fields = ("id", "criado_em", "custo_total")
    date_hierarchy = "criado_em"

    def has_change_permission(self, request, obj=None):
        """Movimentações são imutáveis — somente leitura no admin."""
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ReservaEstoque)
class ReservaEstoqueAdmin(admin.ModelAdmin):
    list_display = ("item", "quantidade", "quantidade_atendida", "status", "prioridade", "pedido")
    list_filter = ("status", "empresa")
    search_fields = ("item__descricao",)
    readonly_fields = ("criado_em",)


@admin.register(SobraChapa)
class SobraaChapaAdmin(admin.ModelAdmin):
    list_display = (
        "item", "largura_mm", "comprimento_mm", "espessura_mm",
        "area_mm2", "estado", "reaproveitavel", "localizacao",
    )
    list_filter = ("estado", "reaproveitavel", "empresa")
    search_fields = ("item__descricao", "projeto_origem")
    readonly_fields = ("area_mm2",)


class ItemInventarioInline(admin.TabularInline):
    model = ItemInventario
    extra = 0
    fields = ("item", "localizacao", "saldo_sistema", "saldo_contado", "divergencia", "ajustado")
    readonly_fields = ("divergencia",)


@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo", "data_inicio", "data_fim", "status", "responsavel")
    list_filter = ("tipo", "status", "empresa")
    search_fields = ("nome",)
    readonly_fields = ("criado_em",)
    inlines = [ItemInventarioInline]


@admin.register(ItemInventario)
class ItemInventarioAdmin(admin.ModelAdmin):
    list_display = ("inventario", "item", "localizacao", "saldo_sistema", "saldo_contado", "divergencia", "ajustado")
    list_filter = ("ajustado", "empresa")
    search_fields = ("inventario__nome", "item__descricao")
    readonly_fields = ("divergencia",)
