from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView

from .models import Chamado, EncerramentoChamado


class ChamadoListView(LoginRequiredMixin, ListView):
    """Listagem de chamados com filtros por status, tipo e prioridade."""

    model = Chamado
    template_name = "assistencia/chamado_list.html"
    context_object_name = "chamados"
    paginate_by = 30

    def get_queryset(self):
        qs = (
            Chamado.objects.filter(empresa=self.request.user.perfil.empresa)
            .select_related("cliente", "responsavel", "contrato")
            .order_by("-data_abertura")
        )

        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)

        tipo = self.request.GET.get("tipo")
        if tipo:
            qs = qs.filter(tipo=tipo)

        prioridade = self.request.GET.get("prioridade")
        if prioridade:
            qs = qs.filter(prioridade=prioridade)

        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(numero__icontains=q) | qs.filter(
                cliente__razao_social__icontains=q
            )

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = Chamado.STATUS_CHOICES
        ctx["tipo_choices"] = Chamado.TIPO_CHOICES
        ctx["prioridade_choices"] = Chamado.PRIORIDADE_CHOICES
        return ctx


class ChamadoDetailView(LoginRequiredMixin, DetailView):
    """Detalhe de um chamado de assistência."""

    model = Chamado
    template_name = "assistencia/chamado_detail.html"
    context_object_name = "chamado"

    def get_queryset(self):
        return Chamado.objects.filter(
            empresa=self.request.user.perfil.empresa
        ).prefetch_related("visitas", "pecas")


class ChamadoCreateView(LoginRequiredMixin, CreateView):
    """Abertura de novo chamado de assistência."""

    model = Chamado
    template_name = "assistencia/chamado_form.html"
    fields = [
        "numero",
        "contrato",
        "pedido",
        "cliente",
        "ambiente",
        "tipo",
        "descricao",
        "prioridade",
        "sla_horas",
        "cobertura_garantia",
        "origem",
        "responsavel",
    ]

    def form_valid(self, form):
        from datetime import timedelta

        form.instance.empresa = self.request.user.perfil.empresa
        form.instance.criado_por = self.request.user
        instance = form.save(commit=False)
        instance.data_limite_sla = timezone.now() + timedelta(
            hours=instance.sla_horas
        )
        instance.save()
        self.object = instance
        return redirect(self.get_success_url())

    def get_success_url(self):
        from django.urls import reverse

        return reverse("assistencia:detail", kwargs={"pk": self.object.pk})


@login_required
def encerrar_chamado(request, pk):
    """HTMX POST — encerra o chamado e registra dados de conclusão."""
    chamado = get_object_or_404(
        Chamado, pk=pk, empresa=request.user.perfil.empresa
    )

    if request.method == "POST":
        encerramento, created = EncerramentoChamado.objects.get_or_create(
            chamado=chamado
        )
        encerramento.causa_raiz = request.POST.get("causa_raiz", "")
        encerramento.solucao = request.POST.get("solucao", "")
        encerramento.custo_total = request.POST.get("custo_total", 0) or 0
        encerramento.cobrado = request.POST.get("cobrado") == "on"
        encerramento.valor_cobrado = request.POST.get("valor_cobrado", 0) or 0
        nps = request.POST.get("nps")
        encerramento.nps = int(nps) if nps else None
        encerramento.aceite_cliente = request.POST.get("aceite_cliente") == "on"
        encerramento.save()

        chamado.status = "encerrado"
        chamado.data_encerramento = timezone.now()
        chamado.alterado_por = request.user
        chamado.save(
            update_fields=["status", "data_encerramento", "alterado_em", "alterado_por"]
        )

        if request.headers.get("HX-Request"):
            return render(
                request,
                "assistencia/partials/chamado_encerrado.html",
                {"chamado": chamado, "encerramento": encerramento},
            )

    return redirect("assistencia:detail", pk=pk)
