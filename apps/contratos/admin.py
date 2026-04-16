"""Admin do módulo Contratos."""
from django.contrib import admin

from .models import Clausula, Contrato, CronogramaFinanceiro, ModeloContrato, PortalToken


class ClausulaInline(admin.TabularInline):
    model = Clausula
    extra = 0
    fields = ("categoria", "titulo", "ordem", "obrigatoria", "ativo")
    ordering = ("ordem",)


@admin.register(ModeloContrato)
class ModeloContratoAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo_venda", "linha_produto", "validade_dias", "garantia_meses_padrao", "ativo")
    list_filter = ("ativo", "empresa")
    search_fields = ("nome", "tipo_venda")
    inlines = [ClausulaInline]


@admin.register(Clausula)
class ClausulaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "categoria", "modelo", "ordem", "obrigatoria", "ativo")
    list_filter = ("categoria", "obrigatoria", "ativo", "empresa")
    search_fields = ("titulo", "modelo__nome")
    ordering = ("modelo", "ordem")


class ParcelaInline(admin.TabularInline):
    model = CronogramaFinanceiro
    extra = 0
    fields = ("numero_parcela", "valor", "data_vencimento", "forma_pagamento", "paga", "data_pagamento")
    readonly_fields = ("titulo_financeiro",)


@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    list_display = ("numero", "cliente", "valores_totais", "status", "responsavel", "data_assinatura")
    list_filter = ("status", "empresa")
    search_fields = ("numero", "cliente__nome")
    readonly_fields = ("assinatura_hash", "criado_em", "alterado_em", "versao")
    inlines = [ParcelaInline]
    fieldsets = (
        ("Identificação", {
            "fields": ("numero", "modelo", "cliente", "pedido"),
        }),
        ("Valores e Datas", {
            "fields": ("valores_totais", "data_vigencia_inicio", "data_vigencia_fim", "garantia_meses"),
        }),
        ("Status e Assinatura", {
            "fields": ("status", "data_assinatura", "assinatura_hash", "responsavel"),
        }),
        ("Conteúdo", {
            "fields": ("conteudo_html", "pdf"),
            "classes": ("collapse",),
        }),
        ("Multi-tenant", {
            "fields": ("empresa", "filial"),
            "classes": ("collapse",),
        }),
    )


@admin.register(CronogramaFinanceiro)
class CronogramaFinanceiroAdmin(admin.ModelAdmin):
    list_display = ("contrato", "numero_parcela", "valor", "data_vencimento", "forma_pagamento", "paga")
    list_filter = ("paga", "forma_pagamento", "empresa")
    search_fields = ("contrato__numero",)


@admin.register(PortalToken)
class PortalTokenAdmin(admin.ModelAdmin):
    list_display = ("contrato", "ativo", "revogado", "validade", "ultimo_acesso", "requer_2fa")
    list_filter = ("ativo", "revogado", "requer_2fa")
    search_fields = ("contrato__numero", "token")
    readonly_fields = ("token", "criado_em")
