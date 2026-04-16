"""Admin do módulo Pedidos."""
from django.contrib import admin

from .models import ComissaoPedido, MarcoPedido, Pedido, PendenciaPedido


class MarcoInline(admin.TabularInline):
    model = MarcoPedido
    extra = 0
    fields = ("etapa", "data_prevista", "data_real", "responsavel", "concluido", "publicar_portal")
    ordering = ("data_prevista",)


class PendenciaInline(admin.TabularInline):
    model = PendenciaPedido
    extra = 0
    fields = ("tipo", "descricao", "bloqueante", "resolvida", "responsavel")


class ComissaoInline(admin.TabularInline):
    model = ComissaoPedido
    extra = 0
    fields = ("beneficiario", "base", "percentual", "valor", "status")
    readonly_fields = ("valor",)


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = (
        "numero", "cliente", "valor_total", "status", "risco",
        "data_prevista_entrega", "prazo_comprometido", "responsavel",
    )
    list_filter = ("status", "risco", "prazo_comprometido", "empresa")
    search_fields = ("numero", "cliente__nome")
    readonly_fields = ("criado_em", "alterado_em", "versao")
    inlines = [MarcoInline, PendenciaInline, ComissaoInline]
    fieldsets = (
        ("Identificação", {
            "fields": ("numero", "proposta", "contrato", "cliente"),
        }),
        ("Responsabilidade", {
            "fields": ("responsavel",),
        }),
        ("Valores e Prazos", {
            "fields": ("valor_total", "data_prevista_entrega", "data_entrega_real", "prazo_comprometido"),
        }),
        ("Status e Risco", {
            "fields": ("status", "risco", "observacoes"),
        }),
        ("Multi-tenant", {
            "fields": ("empresa", "filial"),
            "classes": ("collapse",),
        }),
    )


@admin.register(MarcoPedido)
class MarcoPedidoAdmin(admin.ModelAdmin):
    list_display = ("pedido", "etapa", "data_prevista", "data_real", "concluido", "publicar_portal")
    list_filter = ("concluido", "publicar_portal", "empresa")
    search_fields = ("pedido__numero", "etapa")


@admin.register(PendenciaPedido)
class PendenciaPedidoAdmin(admin.ModelAdmin):
    list_display = ("pedido", "tipo", "bloqueante", "resolvida", "responsavel", "criado_em")
    list_filter = ("tipo", "bloqueante", "resolvida", "empresa")
    search_fields = ("pedido__numero", "descricao")
    readonly_fields = ("criado_em",)


@admin.register(ComissaoPedido)
class ComissaoPedidoAdmin(admin.ModelAdmin):
    list_display = ("pedido", "beneficiario", "base", "percentual", "valor", "status", "data_pagamento")
    list_filter = ("status", "empresa")
    search_fields = ("pedido__numero", "beneficiario__username")
    readonly_fields = ("valor",)
