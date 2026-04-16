"""Admin do módulo Engenharia e Projetos."""
from django.contrib import admin

from .models import (
    AmbienteProjeto,
    BOM,
    DivergenciaProjeto,
    PecaComponente,
    PlanoCorte,
    ProjetoTecnico,
)


class AmbienteInline(admin.TabularInline):
    model = AmbienteProjeto
    extra = 0
    fields = ("nome", "local", "ordem", "prioridade")
    ordering = ("ordem",)


class DivergenciaInline(admin.TabularInline):
    model = DivergenciaProjeto
    extra = 0
    fields = ("tipo", "gravidade", "descricao", "resolvida")
    readonly_fields = ("criado_em",)


@admin.register(ProjetoTecnico)
class ProjetoTecnicoAdmin(admin.ModelAdmin):
    list_display = ("numero", "versao_projeto", "formato_origem", "status", "responsavel_tecnico", "criado_em")
    list_filter = ("status", "formato_origem", "empresa")
    search_fields = ("numero",)
    readonly_fields = ("criado_em", "alterado_em", "versao")
    inlines = [AmbienteInline, DivergenciaInline]
    fieldsets = (
        ("Identificação", {
            "fields": ("numero", "versao_projeto", "formato_origem", "arquivo_importado"),
        }),
        ("Vínculos", {
            "fields": ("pedido", "oportunidade"),
        }),
        ("Responsabilidade e Status", {
            "fields": ("responsavel_tecnico", "status", "observacoes"),
        }),
        ("Multi-tenant", {
            "fields": ("empresa", "filial"),
            "classes": ("collapse",),
        }),
    )


class PecaInline(admin.TabularInline):
    model = PecaComponente
    extra = 0
    fields = ("codigo", "descricao", "largura_mm", "altura_mm", "profundidade_mm", "espessura_mm", "quantidade")


@admin.register(AmbienteProjeto)
class AmbienteProjetoAdmin(admin.ModelAdmin):
    list_display = ("nome", "projeto", "local", "prioridade", "ordem")
    list_filter = ("prioridade", "empresa")
    search_fields = ("nome", "projeto__numero")
    inlines = [PecaInline]


@admin.register(PecaComponente)
class PecaComponenteAdmin(admin.ModelAdmin):
    list_display = ("codigo", "descricao", "ambiente", "largura_mm", "altura_mm", "quantidade")
    list_filter = ("empresa",)
    search_fields = ("codigo", "descricao")
    filter_horizontal = ("ferragens",)


class BOMInline(admin.TabularInline):
    model = BOM
    extra = 0
    fields = ("item", "quantidade", "unidade", "custo_unitario", "custo_total", "falta")
    readonly_fields = ("custo_total",)


@admin.register(BOM)
class BOMAdmin(admin.ModelAdmin):
    list_display = ("projeto", "item", "quantidade", "unidade", "custo_total", "reservado", "falta")
    list_filter = ("reservado", "falta", "empresa")
    search_fields = ("projeto__numero", "item__descricao")
    readonly_fields = ("custo_total", "quantidade_com_perda")


@admin.register(PlanoCorte)
class PlanoCorteAdmin(admin.ModelAdmin):
    list_display = ("projeto", "chapa", "rendimento_pct", "status", "prioridade")
    list_filter = ("status", "empresa")
    search_fields = ("projeto__numero",)
    readonly_fields = ("area_util_mm2", "sobras_mm2", "rendimento_pct")


@admin.register(DivergenciaProjeto)
class DivergenciaProjetoAdmin(admin.ModelAdmin):
    list_display = ("projeto", "tipo", "gravidade", "resolvida", "criado_em")
    list_filter = ("tipo", "gravidade", "resolvida", "empresa")
    search_fields = ("projeto__numero", "descricao")
    readonly_fields = ("criado_em",)
