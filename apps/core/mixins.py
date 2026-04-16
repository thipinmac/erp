"""Mixins reutilizáveis para views do ERP."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404


class TenantMixin(LoginRequiredMixin):
    """
    Mixin base para todas as views autenticadas.
    - Exige login
    - Filtra queryset pelo tenant (empresa) do usuário
    - Injeta empresa/filial no save dos forms
    """

    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(self.request, "empresa") and self.request.empresa:
            qs = qs.filter(empresa=self.request.empresa)
        return qs

    def form_valid(self, form):
        if hasattr(form.instance, "empresa") and not form.instance.empresa_id:
            form.instance.empresa = self.request.empresa
        if hasattr(form.instance, "filial") and not form.instance.filial_id:
            form.instance.filial = self.request.filial
        if hasattr(form.instance, "criado_por") and not form.instance.criado_por_id:
            form.instance.criado_por = self.request.user
        form.instance.alterado_por = self.request.user
        return super().form_valid(form)


class HTMXMixin:
    """
    Mixin para views que respondem a requisições HTMX e normais.

    Se a requisição for HTMX: retorna partial_template_name.
    Caso contrário: retorna template_name completo.
    """

    partial_template_name = None

    def get_template_names(self):
        if self.request.htmx and self.partial_template_name:
            return [self.partial_template_name]
        return super().get_template_names()


class HTMXDeleteMixin:
    """
    Mixin para soft-delete via HTMX.
    Responde com HX-Trigger para atualizar a lista.
    """

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.soft_delete(user=request.user)
        if request.htmx:
            response = HttpResponse("")
            response["HX-Trigger"] = "refreshList"
            return response
        return super().delete(request, *args, **kwargs)
