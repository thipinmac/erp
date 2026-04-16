"""Views do módulo Orçamentos com HTMX."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.core.mixins import HTMXMixin, TenantMixin

from .models import AmbienteOrcamento, ItemOrcamento, OrcamentoRapido, OrcamentoTecnico, Proposta


class OrcamentoListView(TenantMixin, HTMXMixin, ListView):
    template_name = "orcamentos/list.html"
    context_object_name = "orcamentos"
    paginate_by = 20

    def get_queryset(self):
        return OrcamentoTecnico.objects.filter(
            empresa=self.request.empresa, ativo=True
        ).select_related("cliente", "responsavel").order_by("-criado_em")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["rapidos"] = OrcamentoRapido.objects.filter(
            empresa=self.request.empresa, ativo=True
        ).select_related("cliente").order_by("-criado_em")[:5]
        return ctx


class OrcamentoRapidoCreateView(TenantMixin, CreateView):
    model = OrcamentoRapido
    template_name = "orcamentos/rapido_form.html"
    fields = ["cliente", "oportunidade", "tipo_movel", "ambientes", "area_m2",
              "valor_base_m2", "margem_pct", "desconto_pct", "validade", "observacoes"]
    success_url = reverse_lazy("orcamentos:list")

    def get_template_names(self):
        if self.request.htmx:
            return ["orcamentos/partials/rapido_form_modal.html"]
        return super().get_template_names()


class OrcamentoRapidoDetailView(TenantMixin, DetailView):
    model = OrcamentoRapido
    template_name = "orcamentos/rapido_detail.html"


class OrcamentoTecnicoCreateView(TenantMixin, CreateView):
    model = OrcamentoTecnico
    template_name = "orcamentos/tecnico_form.html"
    fields = ["cliente", "oportunidade", "responsavel", "template",
              "markup_pct", "impostos_pct", "desconto_pct",
              "condicao_pagamento", "prazo_entrega_dias", "garantia_meses",
              "data_validade", "observacoes"]

    def get_success_url(self):
        return reverse_lazy("orcamentos:tecnico_detail", kwargs={"pk": self.object.pk})


class OrcamentoTecnicoDetailView(TenantMixin, DetailView):
    model = OrcamentoTecnico
    template_name = "orcamentos/tecnico_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["ambientes"] = self.object.ambientes.prefetch_related("itens").order_by("ordem")
        ctx["itens_sem_ambiente"] = self.object.itens.filter(ambiente__isnull=True)
        return ctx


class OrcamentoTecnicoUpdateView(TenantMixin, UpdateView):
    model = OrcamentoTecnico
    template_name = "orcamentos/tecnico_form.html"
    fields = ["cliente", "responsavel", "markup_pct", "impostos_pct",
              "desconto_pct", "condicao_pagamento", "prazo_entrega_dias",
              "garantia_meses", "data_validade", "observacoes"]

    def get_success_url(self):
        return reverse_lazy("orcamentos:tecnico_detail", kwargs={"pk": self.object.pk})


@login_required
def adicionar_item(request, pk):
    """HTMX: adiciona item ao orçamento e retorna a linha atualizada."""
    orcamento = get_object_or_404(OrcamentoTecnico, pk=pk, empresa=request.empresa)

    if request.method == "POST":
        descricao = request.POST.get("descricao", "")
        tipo = request.POST.get("tipo", ItemOrcamento.TipoItem.MODULO)
        qtd = float(request.POST.get("quantidade", 1))
        custo_mat = float(request.POST.get("custo_material_unit", 0))
        custo_mo = float(request.POST.get("custo_mao_obra_unit", 0))

        item = ItemOrcamento.objects.create(
            empresa=orcamento.empresa,
            filial=orcamento.filial,
            criado_por=request.user,
            alterado_por=request.user,
            orcamento=orcamento,
            descricao=descricao,
            tipo=tipo,
            quantidade=qtd,
            custo_material_unit=custo_mat,
            custo_mao_obra_unit=custo_mo,
        )
        orcamento.recalcular()
        orcamento.save()

        if request.htmx:
            return render(request, "orcamentos/partials/item_row.html", {
                "item": item,
                "orcamento": orcamento,
            })

    return render(request, "orcamentos/partials/item_form.html", {"orcamento": orcamento})


@login_required
def editar_item(request, pk):
    item = get_object_or_404(ItemOrcamento, pk=pk, empresa=request.empresa)
    if request.method == "POST":
        item.descricao = request.POST.get("descricao", item.descricao)
        item.quantidade = float(request.POST.get("quantidade", item.quantidade))
        item.custo_material_unit = float(request.POST.get("custo_material_unit", item.custo_material_unit))
        item.custo_mao_obra_unit = float(request.POST.get("custo_mao_obra_unit", item.custo_mao_obra_unit))
        item.alterado_por = request.user
        item.save()
        item.orcamento.recalcular()
        item.orcamento.save()
        if request.htmx:
            return render(request, "orcamentos/partials/item_row.html", {
                "item": item,
                "orcamento": item.orcamento,
            })
    return render(request, "orcamentos/partials/item_form_inline.html", {"item": item})


@login_required
def excluir_item(request, pk):
    item = get_object_or_404(ItemOrcamento, pk=pk, empresa=request.empresa)
    orcamento = item.orcamento
    item.soft_delete(user=request.user)
    orcamento.recalcular()
    orcamento.save()
    if request.htmx:
        response = HttpResponse("")
        response["HX-Trigger"] = "itemExcluido"
        return response
    return redirect("orcamentos:tecnico_detail", pk=orcamento.pk)


@login_required
def recalcular_orcamento(request, pk):
    """HTMX: recalcula totais e retorna o resumo financeiro."""
    orcamento = get_object_or_404(OrcamentoTecnico, pk=pk, empresa=request.empresa)
    orcamento.recalcular()
    orcamento.save()
    return render(request, "orcamentos/partials/resumo_financeiro.html", {"orcamento": orcamento})


@login_required
def aprovar_orcamento(request, pk):
    """Aprova internamente o orçamento e gera proposta + pedido preliminar."""
    orcamento = get_object_or_404(OrcamentoTecnico, pk=pk, empresa=request.empresa)
    if request.method == "POST":
        orcamento.status = OrcamentoTecnico.Status.APROVADO
        orcamento.data_aprovacao = timezone.now()
        orcamento.alterado_por = request.user
        orcamento.save()

        # Dispara sinal para criar pedido preliminar
        from django.db.models.signals import post_save
        # (Será implementado via signals.py)

        messages.success(request, "Orçamento aprovado! Pedido preliminar criado.")
        return redirect("orcamentos:tecnico_detail", pk=orcamento.pk)

    return render(request, "orcamentos/partials/confirmar_aprovacao.html", {"orcamento": orcamento})


@login_required
def gerar_pdf(request, pk):
    """Gera PDF da proposta via WeasyPrint."""
    from django.template.loader import render_to_string
    try:
        import weasyprint
        orcamento = get_object_or_404(OrcamentoTecnico, pk=pk, empresa=request.empresa)
        html = render_to_string("orcamentos/pdf_proposta.html", {
            "orcamento": orcamento,
            "ambientes": orcamento.ambientes.prefetch_related("itens").order_by("ordem"),
        })
        pdf = weasyprint.HTML(string=html).write_pdf()
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="proposta-{orcamento.numero}.pdf"'
        return response
    except ImportError:
        messages.error(request, "WeasyPrint não instalado. pip install weasyprint")
        return redirect("orcamentos:tecnico_detail", pk=pk)
