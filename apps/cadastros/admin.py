"""Admin do módulo Cadastros."""
from django.contrib import admin
from .models import CentroCusto, Cliente, FamiliaItem, Fornecedor, Item, TabelaPreco, TabelaPrecoItem, UnidadeMedida


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ["nome_exibicao", "tipo_pessoa", "documento", "email", "whatsapp", "cidade_obra", "ativo"]
    list_filter = ["empresa", "tipo_pessoa", "origem", "ativo"]
    search_fields = ["nome", "razao_social", "cpf", "cnpj", "email", "whatsapp"]
    readonly_fields = ["criado_em", "criado_por", "alterado_em", "alterado_por"]


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ["razao_social", "nome_fantasia", "cnpj", "telefone", "homologado", "ativo"]
    list_filter = ["empresa", "homologado", "ativo", "uf"]
    search_fields = ["razao_social", "nome_fantasia", "cnpj", "email"]


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ["codigo", "descricao", "tipo", "unidade", "custo_base", "estoque_minimo", "ativo"]
    list_filter = ["empresa", "tipo", "familia", "ativo", "controla_estoque"]
    search_fields = ["codigo", "descricao", "ncm", "ean"]
    readonly_fields = ["criado_em", "alterado_em"]


@admin.register(TabelaPreco)
class TabelaPrecoAdmin(admin.ModelAdmin):
    list_display = ["nome", "empresa", "vigencia_inicio", "vigencia_fim", "markup_padrao", "padrao"]
    inlines_classes = []


admin.site.register(UnidadeMedida)
admin.site.register(FamiliaItem)
admin.site.register(CentroCusto)
