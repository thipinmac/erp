from django.contrib import admin

from .models import (
    Aceite,
    AgendaAtendimento,
    ChecklistInstalacao,
    EquipeCampo,
    OcorrenciaCampo,
)


@admin.register(EquipeCampo)
class EquipeCampoAdmin(admin.ModelAdmin):
    list_display = ("nome", "veiculo", "ativo", "empresa")
    list_filter = ("ativo", "empresa")
    search_fields = ("nome", "veiculo")
    filter_horizontal = ("membros",)


class ChecklistInstalacaoInline(admin.TabularInline):
    model = ChecklistInstalacao
    extra = 1
    fields = ("item_verificacao", "status", "responsavel", "observacao")


class OcorrenciaCampoInline(admin.TabularInline):
    model = OcorrenciaCampo
    extra = 0
    fields = ("tipo", "descricao", "impacto", "encaminhamento")


class AceiteInline(admin.StackedInline):
    model = Aceite
    extra = 0
    fields = ("data_aceite", "assinante_nome", "assinante_doc", "conclusao", "nps", "observacoes")


@admin.register(AgendaAtendimento)
class AgendaAtendimentoAdmin(admin.ModelAdmin):
    list_display = (
        "tipo",
        "pedido",
        "data_prevista",
        "janela_inicio",
        "janela_fim",
        "equipe",
        "status",
        "empresa",
    )
    list_filter = ("tipo", "status", "empresa", "data_prevista")
    search_fields = ("pedido__numero", "endereco", "equipe__nome")
    date_hierarchy = "data_prevista"
    inlines = [ChecklistInstalacaoInline, OcorrenciaCampoInline, AceiteInline]
    fieldsets = (
        ("Identificação", {"fields": ("tipo", "pedido", "romaneio", "empresa", "filial")}),
        ("Equipe", {"fields": ("equipe", "responsavel")}),
        ("Agendamento", {"fields": ("data_prevista", "janela_inicio", "janela_fim", "endereco")}),
        ("Status", {"fields": ("status", "observacoes")}),
    )


@admin.register(ChecklistInstalacao)
class ChecklistInstalacaoAdmin(admin.ModelAdmin):
    list_display = ("item_verificacao", "agenda", "status", "responsavel")
    list_filter = ("status",)
    search_fields = ("item_verificacao",)


@admin.register(OcorrenciaCampo)
class OcorrenciaCampoAdmin(admin.ModelAdmin):
    list_display = ("tipo", "impacto", "agenda", "descricao")
    list_filter = ("tipo", "impacto")
    search_fields = ("descricao", "encaminhamento")


@admin.register(Aceite)
class AceiteAdmin(admin.ModelAdmin):
    list_display = ("agenda", "assinante_nome", "conclusao", "nps", "data_aceite")
    list_filter = ("conclusao",)
    search_fields = ("assinante_nome", "assinante_doc")
