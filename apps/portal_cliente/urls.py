from django.urls import path

from . import views

app_name = "portal_cliente"

urlpatterns = [
    path("<str:token>/", views.portal_login, name="acesso"),
    path("meu-projeto/", views.portal_dashboard, name="view"),
    path("meu-projeto/timeline/", views.portal_timeline, name="timeline"),
    path("meu-projeto/documentos/", views.portal_documentos, name="documentos"),
    path("meu-projeto/mensagens/", views.portal_mensagens, name="mensagens"),
]
