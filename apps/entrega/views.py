from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView

from .models import Aceite, AgendaAtendimento


class AgendaListView(LoginRequiredMixin, ListView):
    """Agenda do dia com calendário de atendimentos."""

    model = AgendaAtendimento
    template_name = "entrega/agenda_list.html"
    context_object_name = "agendas"

    def get_queryset(self):
        qs = AgendaAtendimento.objects.filter(
            empresa=self.request.empresa
        ).select_related("pedido", "romaneio", "equipe", "responsavel")

        data = self.request.GET.get("data")
        if data:
            qs = qs.filter(data_prevista=data)
        else:
            qs = qs.filter(data_prevista=timezone.localdate())

        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)

        return qs.order_by("janela_inicio")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["hoje"] = timezone.localdate()
        ctx["status_choices"] = AgendaAtendimento.STATUS_CHOICES
        ctx["tipo_choices"] = AgendaAtendimento.TIPO_CHOICES
        return ctx


class AgendaCreateView(LoginRequiredMixin, CreateView):
    """Criação de novo agendamento de atendimento."""

    model = AgendaAtendimento
    template_name = "entrega/agenda_form.html"
    fields = [
        "tipo",
        "pedido",
        "romaneio",
        "equipe",
        "responsavel",
        "data_prevista",
        "janela_inicio",
        "janela_fim",
        "endereco",
        "status",
        "observacoes",
    ]

    def form_valid(self, form):
        form.instance.empresa = self.request.empresa
        form.instance.criado_por = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        from django.urls import reverse

        return reverse("entrega:agenda_detail", kwargs={"pk": self.object.pk})


class AgendaDetailView(LoginRequiredMixin, DetailView):
    """Detalhe de um agendamento de atendimento."""

    model = AgendaAtendimento
    template_name = "entrega/agenda_detail.html"
    context_object_name = "agenda"

    def get_queryset(self):
        return AgendaAtendimento.objects.filter(
            empresa=self.request.empresa
        ).prefetch_related("checklist", "ocorrencias")


@login_required
def aceitar_entrega(request, pk):
    """HTMX POST — registra aceite do cliente ao final do atendimento."""
    agenda = get_object_or_404(
        AgendaAtendimento, pk=pk, empresa=request.empresa
    )

    if request.method == "POST":
        aceite, created = Aceite.objects.get_or_create(agenda=agenda)
        aceite.data_aceite = timezone.now()
        aceite.assinante_nome = request.POST.get("assinante_nome", "")
        aceite.assinante_doc = request.POST.get("assinante_doc", "")
        aceite.conclusao = request.POST.get("conclusao", "total")
        aceite.observacoes = request.POST.get("observacoes", "")
        nps = request.POST.get("nps")
        aceite.nps = int(nps) if nps is not None and nps != "" else None

        if "foto_assinatura" in request.FILES:
            aceite.foto_assinatura = request.FILES["foto_assinatura"]

        aceite.save()

        agenda.status = "aceite"
        agenda.alterado_por = request.user
        agenda.save(update_fields=["status", "alterado_em", "alterado_por"])

        if request.headers.get("HX-Request"):
            return render(
                request,
                "entrega/partials/aceite_confirmado.html",
                {"agenda": agenda, "aceite": aceite},
            )

    return redirect("entrega:agenda_detail", pk=pk)
