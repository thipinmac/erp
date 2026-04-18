"""Views do módulo Pedidos."""
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView

from apps.core.mixins import HTMXMixin, TenantMixin

from .models import ComissaoPedido, MarcoPedido, Pedido, PendenciaPedido


# ─── Kanban de Pedidos ───────────────────────────────────────────────────────

@login_required
def PedidoKanbanView(request):
    """
    Kanban de pedidos agrupados por status.
    Semelhante ao pipeline do CRM mas aplicado ao fluxo de pedidos de venda.
    """
    empresa = request.empresa
    responsavel_id = request.GET.get("responsavel")
    risco = request.GET.get("risco")

    colunas = []
    for status_value, status_label in Pedido.Status.choices:
        if status_value == Pedido.Status.CANCELADO:
            continue  # Cancelados ficam fora do Kanban

        qs = Pedido.objects.filter(empresa=empresa, status=status_value, ativo=True)

        if responsavel_id:
            qs = qs.filter(responsavel_id=responsavel_id)
        if risco:
            qs = qs.filter(risco=risco)

        qs = qs.select_related("cliente", "responsavel").order_by("data_prevista_entrega")

        colunas.append({
            "status": status_value,
            "label": status_label,
            "pedidos": qs,
            "count": qs.count(),
            "valor_total": sum(p.valor_total for p in qs),
        })

    context = {
        "colunas": colunas,
        "risco_choices": Pedido.Risco.choices,
        "risco_atual": risco or "",
        "title": "Kanban de Pedidos",
    }
    return render(request, "pedidos/kanban.html", context)


# ─── Pedido CRUD ─────────────────────────────────────────────────────────────

class PedidoListView(TenantMixin, HTMXMixin, ListView):
    """Lista de pedidos com filtros por status, risco e busca por número/cliente."""

    model = Pedido
    template_name = "pedidos/pedido_list.html"
    partial_template_name = "pedidos/partials/pedido_rows.html"
    context_object_name = "pedidos"
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset().select_related("cliente", "responsavel")
        status = self.request.GET.get("status")
        risco = self.request.GET.get("risco")
        q = self.request.GET.get("q")
        if status:
            qs = qs.filter(status=status)
        if risco:
            qs = qs.filter(risco=risco)
        if q:
            qs = qs.filter(numero__icontains=q) | qs.filter(cliente__nome__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = Pedido.Status.choices
        ctx["risco_choices"] = Pedido.Risco.choices
        return ctx


class PedidoDetailView(TenantMixin, DetailView):
    """Detalhe do pedido com marcos, pendências, comissões e projetos técnicos."""

    model = Pedido
    template_name = "pedidos/pedido_detail.html"

    def get_queryset(self):
        return super().get_queryset().select_related(
            "cliente", "responsavel", "proposta", "contrato", "filial"
        ).prefetch_related("marcos", "pendencias", "comissoes")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["marcos"] = self.object.marcos.order_by("data_prevista")
        ctx["pendencias"] = self.object.pendencias.filter(resolvida=False).order_by("-bloqueante")
        ctx["comissoes"] = self.object.comissoes_pedido.select_related("beneficiario")
        ctx["status_choices"] = Pedido.Status.choices
        ctx["tem_bloqueante"] = self.object.pendencias.filter(
            resolvida=False, bloqueante=True
        ).exists()
        return ctx


class PedidoCreateView(TenantMixin, CreateView):
    """Criação de novo pedido de venda."""

    model = Pedido
    template_name = "pedidos/pedido_form.html"
    fields = [
        "numero",
        "proposta",
        "contrato",
        "cliente",
        "responsavel",
        "filial",
        "valor_total",
        "status",
        "risco",
        "data_prevista_entrega",
        "prazo_comprometido",
        "observacoes",
    ]

    def get_success_url(self):
        return reverse_lazy("pedidos:detail", kwargs={"pk": self.object.pk})


# ─── Atualizar Status (HTMX) ─────────────────────────────────────────────────

@login_required
def atualizar_status_pedido(request, pk):
    """
    HTMX POST: atualiza o status do pedido e cria marco de acompanhamento.
    Impede regressão de status em estados finais (concluído/cancelado).
    """
    if request.method != "POST":
        return HttpResponse(status=405)

    pedido = get_object_or_404(Pedido, pk=pk, empresa=request.empresa)
    novo_status = request.POST.get("status")

    if not novo_status or novo_status not in dict(Pedido.Status.choices):
        return HttpResponse("Status inválido.", status=400)

    # Impede mudança de status em estados finais
    status_finais = {Pedido.Status.CONCLUIDO, Pedido.Status.CANCELADO}
    if pedido.status in status_finais:
        if request.htmx:
            response = HttpResponse("Pedido já encerrado — status não pode ser alterado.", status=422)
            response["HX-Trigger"] = "statusErro"
            return response
        return redirect(reverse_lazy("pedidos:detail", kwargs={"pk": pk}))

    status_anterior = pedido.status
    pedido.status = novo_status
    pedido.alterado_por = request.user

    update_fields = ["status", "alterado_por", "alterado_em"]

    # Registra data de entrega real quando concluído
    if novo_status == Pedido.Status.CONCLUIDO and not pedido.data_entrega_real:
        pedido.data_entrega_real = timezone.now().date()
        update_fields.append("data_entrega_real")

    pedido.save(update_fields=update_fields)

    # Cria marco automático de acompanhamento
    MarcoPedido.objects.create(
        empresa=pedido.empresa,
        filial=pedido.filial,
        pedido=pedido,
        etapa=pedido.get_status_display(),
        data_real=timezone.now().date(),
        responsavel=request.user,
        concluido=True,
        observacao=f"Status alterado de '{status_anterior}' para '{novo_status}'.",
        publicar_portal=True,
    )

    if request.htmx:
        response = render(
            request,
            "pedidos/partials/pedido_status_badge.html",
            {"pedido": pedido, "status_choices": Pedido.Status.choices},
        )
        response["HX-Trigger"] = "statusAtualizado"
        return response

    return redirect(reverse_lazy("pedidos:detail", kwargs={"pk": pk}))
