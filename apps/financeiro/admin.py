from django.contrib import admin

from .models import Baixa, ComissaoFinanceira, Conciliacao, ContaFinanceira, TituloFinanceiro


@admin.register(ContaFinanceira)
class ContaFinanceiraAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo", "banco", "agencia", "conta", "saldo_inicial", "ativo", "empresa")
    list_filter = ("tipo", "ativo", "empresa")
    search_fields = ("nome", "banco", "conta")


class BaixaInline(admin.TabularInline):
    model = Baixa
    extra = 0
    fields = ("data_baixa", "valor", "forma_pagamento", "conta", "conciliado")
    readonly_fields = ("criado_em",)


@admin.register(TituloFinanceiro)
class TituloFinanceiroAdmin(admin.ModelAdmin):
    list_display = (
        "numero",
        "tipo",
        "descricao",
        "valor",
        "valor_pago",
        "vencimento",
        "status",
        "empresa",
    )
    list_filter = ("tipo", "status", "empresa", "forma_pagamento")
    search_fields = ("numero", "descricao", "natureza")
    date_hierarchy = "vencimento"
    inlines = [BaixaInline]
    fieldsets = (
        ("Identificação", {"fields": ("numero", "tipo", "natureza", "descricao", "empresa", "filial")}),
        ("Valores", {"fields": ("valor", "valor_pago", "vencimento", "data_pagamento", "status")}),
        ("Vínculos", {"fields": ("centro_custo", "conta", "pedido", "contrato")}),
        ("Pagamento", {"fields": ("forma_pagamento", "link_pagamento", "codigo_barras", "chave_pix")}),
        ("Observações", {"fields": ("observacoes",)}),
    )


@admin.register(Baixa)
class BaixaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "data_baixa", "valor", "forma_pagamento", "conciliado", "usuario")
    list_filter = ("conciliado", "forma_pagamento")
    search_fields = ("titulo__numero", "titulo__descricao")
    date_hierarchy = "data_baixa"


@admin.register(ComissaoFinanceira)
class ComissaoFinanceiraAdmin(admin.ModelAdmin):
    list_display = ("beneficiario", "pedido", "percentual", "valor", "status", "data_pagamento", "empresa")
    list_filter = ("status", "empresa")
    search_fields = ("beneficiario__username", "pedido__numero", "regra")


@admin.register(Conciliacao)
class ConciliacaoAdmin(admin.ModelAdmin):
    list_display = ("conta", "data_inicio", "data_fim", "saldo_extrato", "saldo_sistema", "divergencia", "status")
    list_filter = ("status", "empresa")
    search_fields = ("conta__nome",)
