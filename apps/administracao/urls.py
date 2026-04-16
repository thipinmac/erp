"""URLs do módulo administração."""
from django.urls import path
from . import views

app_name = "administracao"

urlpatterns = [
    path("", views.login_view, name="root"),
    path("entrar/", views.login_view, name="login"),
    path("sair/", views.logout_view, name="logout"),
    path("empresa/<uuid:empresa_id>/selecionar/", views.selecionar_empresa, name="selecionar_empresa"),
    path("configuracoes/", views.ConfiguracaoView.as_view(), name="config"),
]
