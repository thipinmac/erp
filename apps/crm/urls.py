"""URLs do módulo CRM."""
from django.urls import path
from . import views

app_name = "crm"

urlpatterns = [
    # Pipeline Kanban
    path("", views.pipeline_view, name="pipeline"),
    path("pipeline/mover/<uuid:pk>/", views.mover_oportunidade, name="mover_oportunidade"),

    # Oportunidades
    path("oportunidades/", views.OportunidadeListView.as_view(), name="oportunidade_list"),
    path("oportunidades/nova/", views.OportunidadeCreateView.as_view(), name="oportunidade_create"),
    path("oportunidades/<uuid:pk>/", views.OportunidadeDetailView.as_view(), name="oportunidade_detail"),
    path("oportunidades/<uuid:pk>/editar/", views.OportunidadeUpdateView.as_view(), name="oportunidade_update"),
    path("oportunidades/<uuid:pk>/detalhes/", views.oportunidade_detail_htmx, name="oportunidade_htmx"),

    # Leads
    path("leads/", views.LeadListView.as_view(), name="lead_list"),
    path("leads/novo/", views.LeadCreateView.as_view(), name="lead_create"),
    path("leads/<uuid:pk>/", views.LeadDetailView.as_view(), name="lead_detail"),
    path("leads/<uuid:pk>/editar/", views.LeadUpdateView.as_view(), name="lead_update"),

    # Visitas
    path("visitas/", views.VisitaListView.as_view(), name="visita_list"),
    path("visitas/nova/", views.VisitaCreateView.as_view(), name="visita_create"),

    # HTMX helpers
    path("tarefas/hoje/", views.tarefas_hoje, name="tarefas_hoje"),
    path("tarefas/<uuid:pk>/concluir/", views.concluir_tarefa, name="concluir_tarefa"),
]
