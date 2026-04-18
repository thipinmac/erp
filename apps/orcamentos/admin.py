from django.contrib import admin

from .models import (
    AmbienteOrcamento,
    ItemOrcamento,
    MemoriaCalculo,
    OrcamentoRapido,
    OrcamentoTecnico,
    Proposta,
    TemplateProposta,
)


@admin.register(TemplateProposta)
class TemplateProposta(admin.ModelAdmin):
    list_display = ("nome", "validade_dias", "padrao", "criado_em")
    list_filter = ("padrao",)
    search_fields = ("nome",)


class AmbienteInline(admin.TabularInline):
    model = AmbienteOrcamento
    extra = 0


class ItemOrcamentoInline(admin.TabularInline):
    model = ItemOrcamento
    extra = 0
    fields = ("tipo", "descricao", "quantidade", "unidade", "custo_total_item", "preco_total")
    readonly_fields = ("custo_total_item", "preco_total")


@admin.register(OrcamentoRapido)
class OrcamentoRapidoAdmin(admin.ModelAdmin):
    list_display = ("numero", "cliente", "status", "valor_total", "validade", "criado_em")
    list_filter = ("status", "empresa")
    search_fields = ("numero", "cliente__razao_social")
    readonly_fields = ("valor_total",)


@admin.register(OrcamentoTecnico)
class OrcamentoTecnicoAdmin(admin.ModelAdmin):
    list_display = ("numero", "versao", "cliente", "status", "preco_final", "criado_em")
    list_filter = ("status", "empresa")
    search_fields = ("numero", "cliente__razao_social")
    readonly_fields = ("custo_total", "preco_bruto", "preco_final")
    inlines = [AmbienteInline, ItemOrcamentoInline]


@admin.register(Proposta)
class PropostaAdmin(admin.ModelAdmin):
    list_display = ("numero", "versao", "orcamento", "status", "data_envio")
    list_filter = ("status",)
    search_fields = ("numero",)
