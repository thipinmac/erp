from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import CreateView, DetailView, ListView

from .models import (
    ApontamentoProducao,
    EtapaRoteiro,
    OrdemProducao,
    Romaneio,
)


class KanbanProducaoView(LoginRequiredMixin, ListView):
    """Kanban de Ordens de Produção agrupadas por status."""

    model = OrdemProducao
    template_name = "producao/kanban.html"
    context_object_name = "ordens"

    def get_queryset(self):
        return (
            OrdemProducao.objects.filter(empresa=self.request.empresa)
            .select_related("pedido", "item", "roteiro", "responsavel")
            .order_by("prioridade", "data_prevista_inicio")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ordens = ctx["ordens"]
        colunas = {}
        for status, label in OrdemProducao.STATUS_CHOICES:
            colunas[status] = {
                "label": label,
                "ordens": [op for op in ordens if op.status == status],
            }
        ctx["colunas"] = colunas
        return ctx


class OrdemProducaoListView(LoginRequiredMixin, ListView):
    """Listagem de Ordens de Produção com filtros básicos."""

    model = OrdemProducao
    template_name = "producao/op_list.html"
    context_object_name = "ordens"
    paginate_by = 30

    def get_queryset(self):
        qs = (
            OrdemProducao.objects.filter(empresa=self.request.empresa)
            .select_related("pedido", "item", "responsavel")
            .order_by("-criado_em")
        )
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(numero__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = OrdemProducao.STATUS_CHOICES
        return ctx


class OrdemProducaoDetailView(LoginRequiredMixin, DetailView):
    """Detalhe de uma Ordem de Produção."""

    model = OrdemProducao
    template_name = "producao/op_detail.html"
    context_object_name = "op"

    def get_queryset(self):
        return OrdemProducao.objects.filter(
            empresa=self.request.empresa
        ).prefetch_related("apontamentos", "pecas_faltantes", "volumes", "lotes")


class OrdemProducaoCreateView(LoginRequiredMixin, CreateView):
    """Criação de nova Ordem de Produção."""

    model = OrdemProducao
    template_name = "producao/op_form.html"
    fields = [
        "numero",
        "pedido",
        "ambiente",
        "item",
        "roteiro",
        "prioridade",
        "data_prevista_inicio",
        "data_prevista_fim",
        "status",
        "responsavel",
        "observacoes",
    ]

    def form_valid(self, form):
        form.instance.empresa = self.request.empresa
        form.instance.criado_por = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        from django.urls import reverse

        return reverse("producao:op_detail", kwargs={"pk": self.object.pk})


@login_required
def apontar_etapa(request, pk):
    """HTMX POST — registra apontamento de produção em uma etapa da OP."""
    op = get_object_or_404(
        OrdemProducao, pk=pk, empresa=request.empresa
    )

    if request.method == "POST":
        etapa_id = request.POST.get("etapa")
        etapa = None
        if etapa_id:
            etapa = get_object_or_404(EtapaRoteiro, pk=etapa_id)

        ApontamentoProducao.objects.create(
            op=op,
            etapa=etapa,
            operador=request.user,
            maquina=request.POST.get("maquina", ""),
            inicio=request.POST.get("inicio"),
            fim=request.POST.get("fim") or None,
            tempo_parada_min=int(request.POST.get("tempo_parada_min", 0)),
            motivo_parada=request.POST.get("motivo_parada", ""),
            quantidade_produzida=request.POST.get("quantidade_produzida", 0),
            observacao=request.POST.get("observacao", ""),
        )

        if request.headers.get("HX-Request"):
            return render(
                request,
                "producao/partials/apontamentos_list.html",
                {"op": op, "apontamentos": op.apontamentos.all()},
            )

    return redirect("producao:op_detail", pk=pk)


@login_required
def avancar_status_op(request, pk):
    """HTMX POST — avança o status de uma OP para a próxima etapa."""
    op = get_object_or_404(
        OrdemProducao, pk=pk, empresa=request.empresa
    )

    STATUS_FLOW = [
        "planejada",
        "liberada",
        "em_corte",
        "em_borda",
        "em_usinagem",
        "em_acabamento",
        "em_montagem",
        "em_embalagem",
        "concluida",
    ]

    if request.method == "POST":
        try:
            idx = STATUS_FLOW.index(op.status)
            if idx < len(STATUS_FLOW) - 1:
                op.status = STATUS_FLOW[idx + 1]
                op.alterado_por = request.user
                op.save(update_fields=["status", "alterado_em", "alterado_por"])
        except ValueError:
            pass

        if request.headers.get("HX-Request"):
            return render(
                request,
                "producao/partials/op_status_badge.html",
                {"op": op},
            )

    return redirect("producao:op_detail", pk=pk)


class RomaneioListView(LoginRequiredMixin, ListView):
    """Listagem de Romaneios."""

    model = Romaneio
    template_name = "producao/romaneio_list.html"
    context_object_name = "romaneios"
    paginate_by = 30

    def get_queryset(self):
        return Romaneio.objects.filter(
            empresa=self.request.empresa
        ).select_related("pedido", "conferente")


class RomaneioDetailView(LoginRequiredMixin, DetailView):
    """Detalhe de um Romaneio."""

    model = Romaneio
    template_name = "producao/romaneio_detail.html"
    context_object_name = "romaneio"

    def get_queryset(self):
        return Romaneio.objects.filter(
            empresa=self.request.empresa
        ).prefetch_related("volumes__pecas")
