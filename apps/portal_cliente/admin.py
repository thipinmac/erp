from django.contrib import admin

from .models import FeedbackNPS, MensagemPortal


@admin.register(MensagemPortal)
class MensagemPortalAdmin(admin.ModelAdmin):
    list_display = ("assunto", "origem", "contrato", "lida", "criado_em", "empresa")
    list_filter = ("origem", "lida", "empresa")
    search_fields = ("assunto", "corpo", "contrato__numero")
    date_hierarchy = "criado_em"
    readonly_fields = ("criado_em", "data_leitura")


@admin.register(FeedbackNPS)
class FeedbackNPSAdmin(admin.ModelAdmin):
    list_display = ("contrato", "nota", "etapa", "criado_em", "empresa")
    list_filter = ("nota", "empresa", "etapa")
    search_fields = ("contrato__numero", "comentario")
    date_hierarchy = "criado_em"
    readonly_fields = ("criado_em",)
