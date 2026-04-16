from django.urls import path

from . import views

app_name = "entrega"

urlpatterns = [
    path("", views.AgendaListView.as_view(), name="agenda"),
    path("agenda/nova/", views.AgendaCreateView.as_view(), name="agenda_create"),
    path("agenda/<uuid:pk>/", views.AgendaDetailView.as_view(), name="agenda_detail"),
    path("agenda/<uuid:pk>/aceite/", views.aceitar_entrega, name="aceite"),
]
