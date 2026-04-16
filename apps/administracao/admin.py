"""Admin do módulo Administração."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import AuditLog, Calendario, Empresa, Feriado, Filial, Perfil, Usuario


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ["razao_social", "nome_fantasia", "cnpj", "regime_tributario", "ativo"]
    list_filter = ["regime_tributario", "ativo"]
    search_fields = ["razao_social", "nome_fantasia", "cnpj"]


@admin.register(Filial)
class FilialAdmin(admin.ModelAdmin):
    list_display = ["codigo", "nome", "empresa", "cidade", "uf", "ativo"]
    list_filter = ["empresa", "ativo", "uf"]
    search_fields = ["nome", "codigo", "cnpj"]


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ["username", "get_full_name", "email", "empresa", "cargo", "is_active"]
    list_filter = ["empresa", "is_active", "is_staff", "perfil"]
    search_fields = ["username", "first_name", "last_name", "email"]
    fieldsets = UserAdmin.fieldsets + (
        ("ERP", {"fields": ("empresa", "filiais_autorizadas", "cargo", "equipe", "telefone", "perfil")}),
    )


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ["nome", "papel", "empresa", "ativo"]
    list_filter = ["empresa", "papel", "ativo"]


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["criado_em", "usuario", "acao", "modelo", "objeto_str"]
    list_filter = ["acao", "modelo", "criado_em"]
    search_fields = ["usuario__username", "objeto_str", "modelo"]
    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(Calendario)
class CalendarioAdmin(admin.ModelAdmin):
    list_display = ["nome", "empresa", "turno_inicio", "turno_fim"]


admin.site.register(Feriado)
