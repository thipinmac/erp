from django.contrib import admin

from .models import Chamado, EncerramentoChamado, PecaReposicao, VisitaTecnica


class VisitaTecnicaInline(admin.TabularInline):
    model = VisitaTecnica
    extra = 0
    fields = ("data_prevista", "data_realizada", "tecnico", "status")


class PecaReposicaoInline(admin.TabularInline):
    model = PecaReposicao
    extra = 0
    fields = ("item", "quantidade", "origem", "prazo_estimado", "entregue")


class EncerramentoChamadoInline(admin.StackedInline):
    model = EncerramentoChamado
    extra = 0
    fields = ("causa_raiz", "solucao", "custo_total", "cobrado", "valor_cobrado", "nps", "aceite_cliente")


@admin.register(Chamado)
class ChamadoAdmin(admin.ModelAdmin):
    list_display = (
        "numero",
        "cliente",
        "tipo",
        "status",
        "prioridade",
        "data_abertura",
        "data_limite_sla",
        "responsavel",
        "empresa",
    )
    list_filter = ("tipo", "status", "prioridade", "cobertura_garantia", "empresa", "origem")
    search_fields = ("numero", "cliente__razao_social", "descricao")
    date_hierarchy = "data_abertura"
    inlines = [VisitaTecnicaInline, PecaReposicaoInline, EncerramentoChamadoInline]
    fieldsets = (
        ("Identificação", {"fields": ("numero", "tipo", "origem", "empresa", "filial")}),
        ("Vínculos", {"fields": ("cliente", "contrato", "pedido", "ambiente")}),
        ("Detalhes", {"fields": ("descricao", "prioridade", "sla_horas", "cobertura_garantia")}),
        ("Status", {"fields": ("status", "responsavel", "data_limite_sla", "data_encerramento")}),
    )


@admin.register(VisitaTecnica)
class VisitaTecnicaAdmin(admin.ModelAdmin):
    list_display = ("chamado", "data_prevista", "data_realizada", "tecnico", "status")
    list_filter = ("status",)
    search_fields = ("chamado__numero", "diagnostico")


@admin.register(PecaReposicao)
class PecaReposicaoAdmin(admin.ModelAdmin):
    list_display = ("chamado", "item", "quantidade", "origem", "prazo_estimado", "entregue")
    list_filter = ("origem", "entregue")
    search_fields = ("chamado__numero", "item__descricao")


@admin.register(EncerramentoChamado)
class EncerramentoChamadoAdmin(admin.ModelAdmin):
    list_display = ("chamado", "cobrado", "valor_cobrado", "nps", "aceite_cliente")
    list_filter = ("cobrado", "aceite_cliente")
    search_fields = ("chamado__numero", "causa_raiz", "solucao")
