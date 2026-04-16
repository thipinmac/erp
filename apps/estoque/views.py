"""Views do módulo Estoque."""
from django.apps import apps
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView

from apps.core.mixins import HTMXMixin, TenantMixin

from .models import (
    Inventario,
    ItemInventario,
    Localizacao,
    Lote,
    MovimentacaoEstoque,
    ReservaEstoque,
    SaldoEstoque,
    SobraChapa,
)


# ─── Saldo de Estoque ────────────────────────────────────────────────────────

class SaldoEstoqueListView(TenantMixin, HTMXMixin, ListView):
    """Posição atual de estoque por item e localização."""

    model = SaldoEstoque
    template_name = "estoque/saldo_list.html"
    partial_template_name = "estoque/partials/saldo_rows.html"
    context_object_name = "saldos"
    paginate_by = 50

    def get_queryset(self):
        qs = super().get_queryset().select_related("item", "localizacao")
        q = self.request.GET.get("q")
        localizacao_id = self.request.GET.get("localizacao")
        apenas_falta = self.request.GET.get("falta")

        if q:
            qs = qs.filter(item__descricao__icontains=q) | qs.filter(item__codigo__icontains=q)
        if localizacao_id:
            qs = qs.filter(localizacao_id=localizacao_id)
        if apenas_falta:
            qs = qs.filter(saldo_disponivel__lte=0)

        return qs.order_by("item__descricao")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["localizacoes"] = Localizacao.objects.filter(empresa=self.request.empresa, ativo=True)
        return ctx


# ─── Movimentações ───────────────────────────────────────────────────────────

class MovimentacaoListView(TenantMixin, HTMXMixin, ListView):
    """Histórico de movimentações de estoque com filtros por tipo, item e período."""

    model = MovimentacaoEstoque
    template_name = "estoque/movimentacao_list.html"
    partial_template_name = "estoque/partials/movimentacao_rows.html"
    context_object_name = "movimentacoes"
    paginate_by = 50

    def get_queryset(self):
        # MovimentacaoEstoque não herda AbstractBaseModel: filtro manual por empresa
        qs = MovimentacaoEstoque.objects.filter(empresa=self.request.empresa)
        tipo = self.request.GET.get("tipo")
        item_q = self.request.GET.get("q")
        data_inicio = self.request.GET.get("data_inicio")
        data_fim = self.request.GET.get("data_fim")

        if tipo:
            qs = qs.filter(tipo=tipo)
        if item_q:
            qs = qs.filter(item__descricao__icontains=item_q)
        if data_inicio:
            qs = qs.filter(criado_em__date__gte=data_inicio)
        if data_fim:
            qs = qs.filter(criado_em__date__lte=data_fim)

        return qs.select_related(
            "item", "lote", "localizacao_origem", "localizacao_destino", "usuario"
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["tipo_choices"] = MovimentacaoEstoque.Tipo.choices
        return ctx


# ─── Sobras de Chapa ─────────────────────────────────────────────────────────

class SobraListView(TenantMixin, HTMXMixin, ListView):
    """Lista de sobras de chapa disponíveis para reaproveitamento."""

    model = SobraChapa
    template_name = "estoque/sobra_list.html"
    partial_template_name = "estoque/partials/sobra_rows.html"
    context_object_name = "sobras"
    paginate_by = 30

    def get_queryset(self):
        qs = super().get_queryset().select_related("item", "localizacao")
        reaproveitavel = self.request.GET.get("reaproveitavel")
        estado = self.request.GET.get("estado")
        q = self.request.GET.get("q")

        if reaproveitavel is not None and reaproveitavel != "":
            qs = qs.filter(reaproveitavel=reaproveitavel == "1")
        if estado:
            qs = qs.filter(estado=estado)
        if q:
            qs = qs.filter(item__descricao__icontains=q)

        return qs.order_by("-area_mm2")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["estado_choices"] = SobraChapa.Estado.choices
        return ctx


# ─── Inventários ─────────────────────────────────────────────────────────────

class InventarioListView(TenantMixin, HTMXMixin, ListView):
    """Lista de inventários com progresso de contagem."""

    model = Inventario
    template_name = "estoque/inventario_list.html"
    partial_template_name = "estoque/partials/inventario_rows.html"
    context_object_name = "inventarios"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related("responsavel", "aprovado_por")
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = Inventario.Status.choices
        return ctx


# ─── Reservas ────────────────────────────────────────────────────────────────

class ReservaListView(TenantMixin, HTMXMixin, ListView):
    """Lista de reservas de estoque ativas por prioridade."""

    model = ReservaEstoque
    template_name = "estoque/reserva_list.html"
    partial_template_name = "estoque/partials/reserva_rows.html"
    context_object_name = "reservas"
    paginate_by = 30

    def get_queryset(self):
        qs = super().get_queryset().select_related("item", "lote", "pedido")
        status = self.request.GET.get("status", ReservaEstoque.Status.ATIVA)
        if status:
            qs = qs.filter(status=status)
        return qs.order_by("prioridade", "criado_em")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = ReservaEstoque.Status.choices
        return ctx


# ─── Entrada Manual (HTMX) ───────────────────────────────────────────────────

@login_required
def entrada_manual(request):
    """
    GET:  retorna formulário HTMX de entrada manual.
    POST: registra movimentação de entrada e atualiza saldo (custo médio ponderado).

    Campos POST esperados:
      - item_id (UUID)
      - quantidade (decimal)
      - custo_unitario (decimal)
      - localizacao_id (UUID, opcional)
      - lote_id (UUID, opcional)
      - motivo (texto livre)
    """
    empresa = request.empresa

    if request.method != "POST":
        localizacoes = Localizacao.objects.filter(empresa=empresa, ativo=True)
        return render(request, "estoque/partials/entrada_form.html", {
            "localizacoes": localizacoes,
        })

    # Valida campos obrigatórios
    item_id = request.POST.get("item_id")
    quantidade_str = request.POST.get("quantidade", "0")
    custo_str = request.POST.get("custo_unitario", "0")

    if not item_id:
        return HttpResponse("Item é obrigatório.", status=400)

    try:
        Item = apps.get_model("cadastros", "Item")
        item = get_object_or_404(Item, pk=item_id)
        quantidade = float(quantidade_str)
        custo_unitario = float(custo_str)
    except (ValueError, TypeError, LookupError):
        return HttpResponse("Dados inválidos.", status=400)

    if quantidade <= 0:
        return HttpResponse("Quantidade deve ser maior que zero.", status=400)

    localizacao_id = request.POST.get("localizacao_id")
    lote_id = request.POST.get("lote_id")
    motivo = request.POST.get("motivo", "Entrada manual")

    localizacao = None
    if localizacao_id:
        localizacao = get_object_or_404(Localizacao, pk=localizacao_id, empresa=empresa)

    lote = None
    if lote_id:
        lote = get_object_or_404(Lote, pk=lote_id, empresa=empresa)

    # Cria movimentação imutável
    movimentacao = MovimentacaoEstoque.objects.create(
        empresa=empresa,
        filial=getattr(request, "filial", None),
        tipo=MovimentacaoEstoque.Tipo.ENTRADA,
        item=item,
        lote=lote,
        localizacao_destino=localizacao,
        quantidade=quantidade,
        custo_unitario=custo_unitario,
        motivo=motivo,
        referencia_modelo="entrada_manual",
        usuario=request.user,
    )

    # Upsert do saldo e recálculo de custo médio ponderado
    saldo, _ = SaldoEstoque.objects.get_or_create(
        empresa=empresa,
        item=item,
        localizacao=localizacao,
        defaults={
            "filial": getattr(request, "filial", None),
            "saldo_atual": 0,
            "saldo_reservado": 0,
            "custo_medio": 0,
        },
    )

    saldo_anterior = float(saldo.saldo_atual)
    custo_anterior = float(saldo.custo_medio)
    novo_saldo = saldo_anterior + quantidade

    if novo_saldo > 0:
        saldo.custo_medio = (
            (saldo_anterior * custo_anterior) + (quantidade * custo_unitario)
        ) / novo_saldo

    saldo.saldo_atual = novo_saldo
    saldo.ultima_movimentacao = timezone.now()
    saldo.save()

    if request.htmx:
        response = render(
            request,
            "estoque/partials/entrada_sucesso.html",
            {"movimentacao": movimentacao, "saldo": saldo},
        )
        response["HX-Trigger"] = "estoqueAtualizado"
        return response

    return redirect(reverse_lazy("estoque:list"))
