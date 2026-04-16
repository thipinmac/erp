"""
TenantMiddleware — injeta empresa e filial no request.

Estratégia simples: usuário tem empresa ativa salva na sessão.
Para multi-empresa: usuário pode trocar via seletor na navbar.
"""
from django.shortcuts import redirect
from django.urls import resolve


# URLs que não precisam de tenant
PUBLIC_URLS = {
    "login",
    "logout",
    "portal_cliente:acesso",
    "portal_cliente:view",
    "admin:index",
}


class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.empresa = None
        request.filial = None

        if request.user.is_authenticated:
            self._set_tenant(request)

        response = self.get_response(request)
        return response

    def _set_tenant(self, request):
        from apps.administracao.models import Empresa, Filial

        # Empresa ativa salva na sessão
        empresa_id = request.session.get("empresa_ativa_id")

        if empresa_id:
            try:
                request.empresa = Empresa.objects.get(
                    id=empresa_id,
                    ativo=True,
                )
            except Empresa.DoesNotExist:
                request.session.pop("empresa_ativa_id", None)

        # Se não há empresa na sessão, usa a primeira do usuário
        if not request.empresa and hasattr(request.user, "empresa"):
            empresa = request.user.empresa
            if empresa:
                request.empresa = empresa
                request.session["empresa_ativa_id"] = str(empresa.id)

        # Filial ativa
        filial_id = request.session.get("filial_ativa_id")
        if filial_id and request.empresa:
            try:
                request.filial = Filial.objects.get(
                    id=filial_id,
                    empresa=request.empresa,
                    ativo=True,
                )
            except Filial.DoesNotExist:
                request.session.pop("filial_ativa_id", None)
