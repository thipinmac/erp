"""Views do módulo Compras e Suprimentos."""
from django.contrib.auth.decorators import login_required
from django.core.signals import Signal
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView

from apps.core.mixins import HTMXMixin, TenantMixin

from .models import (
    Cotacao,
    ItemPedidoCompra,
    ItemRecebimento,
    PedidoCompra,
    Recebimento,
    RequisicaoCompra,
)

# Sinal emitido quando recebimento é encerrado — capturado pelo módulo de estoque
recebimento_encerrado = Signal()


# ─── Requisição de Compra ────────────────────────────────────────────────────

class RequisicaoListView(TenantMixin, HTMXMixin, ListView):
    """Lista de requisições de compra com filtros por status e prioridade."""

    model = RequisicaoCompra
    template_name = "compras/requisicao_list.html"
    partial_template_name = "compras/partials/requisicao_rows.html"
    context_object_name = "requisicoes"
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset().select_related("item", "responsavel", "centro_custo", "pedido")
        status = self.request.GET.get("status")
        prioridade = self.request.GET.get("prioridade")
        q = self.request.GET.get("q")
        if status:
            qs = qs.filter(status=status)
        if prioridade:
            qs = qs.filter(prioridade=prioridade)
        if q:
            qs = qs.filter(numero__icontains=q) | qs.filter(item__descricao__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = RequisicaoCompra.Status.choices
        ctx["prioridade_choices"] = RequisicaoCompra.Prioridade.choices
        return ctx


# ─── Pedido de Compra ────────────────────────────────────────────────────────

class PedidoCompraListView(TenantMixin, HTMXMixin, ListView):
    """Lista de pedidos de compra com filtros por status e fornecedor."""

    model = PedidoCompra
    template_name = "compras/pedido_list.html"
    partial_template_name = "compras/partials/pedido_rows.html"
    context_object_name = "pedidos"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related("fornecedor", "responsavel", "cotacao")
        status = self.request.GET.get("status")
        q = self.request.GET.get("q")
        if status:
            qs = qs.filter(status=status)
        if q:
            qs = qs.filter(numero__icontains=q) | qs.filter(fornecedor__nome__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = PedidoCompra.Status.choices
        return ctx


class PedidoCompraDetailView(TenantMixin, DetailView):
    """Detalhe do pedido de compra com itens e histórico de recebimentos."""

    model = PedidoCompra
    template_name = "compras/pedido_detail.html"

    def get_queryset(self):
        return super().get_queryset().select_related(
            "fornecedor", "cotacao", "responsavel"
        ).prefetch_related("itens__item", "recebimentos")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["itens"] = self.object.itens.select_related("item")
        ctx["recebimentos"] = self.object.recebimentos.order_by("-data")
        ctx["pode_receber"] = self.object.status in (
            PedidoCompra.Status.EMITIDO,
            PedidoCompra.Status.EM_TRANSITO,
        )
        return ctx


class PedidoCompraCreateView(TenantMixin, CreateView):
    """Criação de novo pedido de compra."""

    model = PedidoCompra
    template_name = "compras/pedido_form.html"
    fields = [
        "numero",
        "fornecedor",
        "cotacao",
        "status",
        "data_emissao",
        "data_prevista_entrega",
        "condicao_pagamento",
        "frete_valor",
        "responsavel",
    ]

    def get_success_url(self):
        return reverse_lazy("compras:pedido_detail", kwargs={"pk": self.object.pk})


# ─── Recebimento ─────────────────────────────────────────────────────────────

class RecebimentoDetailView(TenantMixin, DetailView):
    """Detalhe do recebimento com itens conferidos e divergências."""

    model = Recebimento
    template_name = "compras/recebimento_detail.html"

    def get_queryset(self):
        return super().get_queryset().select_related(
            "pedido_compra__fornecedor", "responsavel"
        ).prefetch_related("itens__item")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["itens"] = self.object.itens.select_related("item")
        ctx["tem_divergencia"] = self.object.itens.filter(quantidade_divergencia__gt=0).exists()
        return ctx


# ─── Receber Pedido (HTMX POST) ──────────────────────────────────────────────

@login_required
def receber_pedido(request, pk):
    """
    HTMX POST: registra o recebimento de um pedido de compra.

    Fluxo:
    1. Cria Recebimento e ItemRecebimento conforme quantidades informadas.
    2. Atualiza ItemPedidoCompra.quantidade_recebida.
    3. Se todos os itens recebidos, muda PedidoCompra.status para 'recebido'.
    4. Emite sinal recebimento_encerrado para atualização de estoque.
    """
    if request.method != "POST":
        return HttpResponse(status=405)

    pedido = get_object_or_404(PedidoCompra, pk=pk, empresa=request.empresa)

    if pedido.status not in (PedidoCompra.Status.EMITIDO, PedidoCompra.Status.EM_TRANSITO):
        if request.htmx:
            response = HttpResponse("Pedido não está em trânsito ou emitido.", status=422)
            response["HX-Trigger"] = "recebimentoErro"
            return response
        return redirect(reverse_lazy("compras:pedido_detail", kwargs={"pk": pk}))

    # Cria o registro de recebimento
    recebimento = Recebimento.objects.create(
        empresa=pedido.empresa,
        filial=pedido.filial,
        pedido_compra=pedido,
        data=timezone.now().date(),
        xml_nfe=request.POST.get("xml_nfe", ""),
        chave_nfe=request.POST.get("chave_nfe", ""),
        responsavel=request.user,
        status=Recebimento.Status.CONFERIDO,
        observacoes=request.POST.get("observacoes", ""),
    )

    todos_recebidos = True
    itens_recebimento = []

    for item_pc in pedido.itens.select_related("item"):
        try:
            qtd_recebida = float(request.POST.get(f"qtd_{item_pc.pk}", "0"))
            custo = float(request.POST.get(f"custo_{item_pc.pk}", str(item_pc.preco_unitario)))
        except (ValueError, TypeError):
            qtd_recebida = 0.0
            custo = float(item_pc.preco_unitario)

        item_rec = ItemRecebimento.objects.create(
            empresa=pedido.empresa,
            filial=pedido.filial,
            recebimento=recebimento,
            item=item_pc.item,
            quantidade_pedida=item_pc.quantidade,
            quantidade_recebida=qtd_recebida,
            custo_unitario=custo,
            lote=request.POST.get(f"lote_{item_pc.pk}", ""),
            aceito=request.POST.get(f"aceito_{item_pc.pk}", "true") == "true",
        )
        itens_recebimento.append(item_rec)

        # Acumula quantidade recebida no item do pedido
        item_pc.quantidade_recebida = float(item_pc.quantidade_recebida) + qtd_recebida
        item_pc.save(update_fields=["quantidade_recebida"])

        if float(item_pc.quantidade_recebida) < float(item_pc.quantidade):
            todos_recebidos = False

    # Marca como divergência se houver diferença de quantidades
    tem_divergencia = any(float(i.quantidade_divergencia) != 0 for i in itens_recebimento)
    if tem_divergencia:
        recebimento.status = Recebimento.Status.DIVERGENCIA
        recebimento.save(update_fields=["status"])

    # Fecha o pedido se todos os itens foram recebidos
    if todos_recebidos:
        pedido.status = PedidoCompra.Status.RECEBIDO
        pedido.data_entrega_real = timezone.now().date()
        pedido.alterado_por = request.user
        pedido.save(update_fields=["status", "data_entrega_real", "alterado_por", "alterado_em"])

    # Emite sinal para módulo de estoque atualizar saldos
    recebimento_encerrado.send(
        sender=Recebimento,
        recebimento=recebimento,
        itens=itens_recebimento,
        pedido=pedido,
        usuario=request.user,
    )

    if request.htmx:
        response = render(
            request,
            "compras/partials/recebimento_card.html",
            {"recebimento": recebimento, "pedido": pedido},
        )
        response["HX-Trigger"] = "recebimentoRealizado"
        return response

    return redirect(reverse_lazy("compras:pedido_detail", kwargs={"pk": pk}))
