from django.contrib import admin

from .models import (
    ApontamentoProducao,
    EtapaRoteiro,
    LoteProducao,
    OrdemProducao,
    PecaFaltante,
    PecaVolume,
    Romaneio,
    RoteiroPadrao,
    Volume,
)


class EtapaRoteiroInline(admin.TabularInline):
    model = EtapaRoteiro
    extra = 1
    fields = ("ordem", "nome", "recurso", "tempo_padrao_min", "ativo")
    ordering = ("ordem",)


@admin.register(RoteiroPadrao)
class RoteiroPadraoAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo", "empresa", "ativo")
    list_filter = ("empresa", "tipo", "ativo")
    search_fields = ("nome", "tipo")
    inlines = [EtapaRoteiroInline]


@admin.register(EtapaRoteiro)
class EtapaRoteiroAdmin(admin.ModelAdmin):
    list_display = ("roteiro", "ordem", "nome", "recurso", "tempo_padrao_min", "ativo")
    list_filter = ("ativo", "roteiro__empresa")
    search_fields = ("nome", "recurso", "roteiro__nome")
    ordering = ("roteiro", "ordem")


class ApontamentoProducaoInline(admin.TabularInline):
    model = ApontamentoProducao
    extra = 0
    fields = ("etapa", "operador", "maquina", "inicio", "fim", "quantidade_produzida")
    readonly_fields = ("inicio",)


class PecaFaltanteInline(admin.TabularInline):
    model = PecaFaltante
    extra = 0
    fields = ("tipo", "descricao", "impacto", "resolvido")


@admin.register(OrdemProducao)
class OrdemProducaoAdmin(admin.ModelAdmin):
    list_display = (
        "numero",
        "pedido",
        "ambiente",
        "status",
        "prioridade",
        "data_prevista_fim",
        "responsavel",
        "empresa",
    )
    list_filter = ("status", "empresa", "prioridade")
    search_fields = ("numero", "ambiente", "pedido__numero")
    date_hierarchy = "data_prevista_fim"
    inlines = [ApontamentoProducaoInline, PecaFaltanteInline]
    fieldsets = (
        ("Identificação", {"fields": ("numero", "pedido", "ambiente", "item", "roteiro", "empresa", "filial")}),
        ("Planejamento", {"fields": ("prioridade", "data_prevista_inicio", "data_prevista_fim", "responsavel")}),
        ("Execução", {"fields": ("status", "data_inicio_real", "data_fim_real")}),
        ("Observações", {"fields": ("observacoes",)}),
    )


@admin.register(LoteProducao)
class LoteProducaoAdmin(admin.ModelAdmin):
    list_display = ("numero", "objetivo", "status", "data_alvo", "empresa")
    list_filter = ("status", "empresa")
    search_fields = ("numero", "objetivo")
    filter_horizontal = ("ops",)


class PecaVolumeInline(admin.TabularInline):
    model = PecaVolume
    extra = 1
    fields = ("peca_descricao", "quantidade")


@admin.register(Volume)
class VolumeAdmin(admin.ModelAdmin):
    list_display = ("numero", "op", "pedido", "tipo_embalagem", "conferido", "expedido", "empresa")
    list_filter = ("conferido", "expedido", "empresa")
    search_fields = ("numero", "op__numero", "codigo_barras")
    inlines = [PecaVolumeInline]


@admin.register(Romaneio)
class RomaneioAdmin(admin.ModelAdmin):
    list_display = ("numero", "pedido", "veiculo", "motorista", "data_expedicao", "status", "empresa")
    list_filter = ("status", "empresa")
    search_fields = ("numero", "veiculo", "motorista", "pedido__numero")
    filter_horizontal = ("volumes",)
