"""URLs raiz do projeto MóveisERP."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Admin Django
    path("admin/", admin.site.urls),

    # Autenticação
    path("", include("apps.administracao.urls")),

    # Módulos
    path("cadastros/", include("apps.cadastros.urls")),
    path("crm/", include("apps.crm.urls")),
    path("orcamentos/", include("apps.orcamentos.urls")),
    path("engenharia/", include("apps.engenharia.urls")),
    path("contratos/", include("apps.contratos.urls")),
    path("pedidos/", include("apps.pedidos.urls")),
    path("compras/", include("apps.compras.urls")),
    path("estoque/", include("apps.estoque.urls")),
    path("producao/", include("apps.producao.urls")),
    path("entrega/", include("apps.entrega.urls")),
    path("assistencia/", include("apps.assistencia.urls")),
    path("financeiro/", include("apps.financeiro.urls")),
    path("fiscal/", include("apps.fiscal.urls")),
    path("comunicacao/", include("apps.comunicacao.urls")),
    path("bi/", include("apps.bi.urls")),

    # Portal do cliente (URL pública com token)
    path("portal/", include("apps.portal_cliente.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    try:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
    except ImportError:
        pass

# Customizar admin
admin.site.site_header = "MóveisERP — Administração"
admin.site.site_title = "MóveisERP"
admin.site.index_title = "Painel Administrativo"
