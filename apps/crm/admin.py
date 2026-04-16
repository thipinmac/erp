"""Admin do CRM."""
from django.contrib import admin
from .models import EtapaPipeline, HistoricoOportunidade, Lead, Meta, Oportunidade, TarefaComercial, Visita


@admin.register(EtapaPipeline)
class EtapaPipelineAdmin(admin.ModelAdmin):
    list_display = ["nome", "empresa", "ordem", "probabilidade_padrao", "ativo"]
    list_filter = ["empresa", "ativo"]
    ordering = ["empresa", "ordem"]


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ["nome", "email", "whatsapp", "status", "canal_origem", "score", "responsavel", "criado_em"]
    list_filter = ["empresa", "status", "canal_origem"]
    search_fields = ["nome", "email", "telefone", "whatsapp"]


@admin.register(Oportunidade)
class OportunidadeAdmin(admin.ModelAdmin):
    list_display = ["titulo", "etapa", "valor_estimado", "probabilidade", "responsavel", "data_previsao_fechamento"]
    list_filter = ["empresa", "etapa", "responsavel"]
    search_fields = ["titulo"]
    readonly_fields = ["valor_ponderado", "data_entrada_etapa"]


@admin.register(Visita)
class VisitaAdmin(admin.ModelAdmin):
    list_display = ["tipo", "data_hora", "local", "responsavel", "realizada"]
    list_filter = ["tipo", "realizada", "responsavel"]


@admin.register(TarefaComercial)
class TarefaComercialAdmin(admin.ModelAdmin):
    list_display = ["titulo", "tipo", "data_vencimento", "prioridade", "responsavel", "concluida"]
    list_filter = ["tipo", "prioridade", "concluida", "responsavel"]


admin.site.register(Meta)
admin.site.register(HistoricoOportunidade)
