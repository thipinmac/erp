from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import CreateView, ListView, TemplateView

from .models import Baixa, TituloFinanceiro


class ReceberListView(LoginRequiredMixin, ListView):
    """Listagem de títulos a receber."""

    model = TituloFinanceiro
    template_name = "financeiro/receber_list.html"
    context_object_name = "titulos"
    paginate_by = 30

    def get_queryset(self):
        qs = (
            TituloFinanceiro.objects.filter(
                empresa=self.request.user.perfil.empresa,
                tipo="receber",
            )
            .select_related("conta", "pedido", "contrato", "centro_custo")
            .order_by("vencimento")
        )
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = TituloFinanceiro.STATUS_CHOICES
        ctx["total_aberto"] = (
            self.get_queryset()
            .filter(status__in=["aberto", "parcial", "vencido"])
            .aggregate(total=Sum("valor"))["total"]
            or 0
        )
        return ctx


class PagarListView(LoginRequiredMixin, ListView):
    """Listagem de títulos a pagar."""

    model = TituloFinanceiro
    template_name = "financeiro/pagar_list.html"
    context_object_name = "titulos"
    paginate_by = 30

    def get_queryset(self):
        qs = (
            TituloFinanceiro.objects.filter(
                empresa=self.request.user.perfil.empresa,
                tipo="pagar",
            )
            .select_related("conta", "pedido", "contrato", "centro_custo")
            .order_by("vencimento")
        )
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = TituloFinanceiro.STATUS_CHOICES
        ctx["total_aberto"] = (
            self.get_queryset()
            .filter(status__in=["aberto", "parcial", "vencido"])
            .aggregate(total=Sum("valor"))["total"]
            or 0
        )
        return ctx


class DREView(LoginRequiredMixin, TemplateView):
    """Demonstrativo de Resultado do Exercício agrupado por natureza."""

    template_name = "financeiro/dre.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        empresa = self.request.user.perfil.empresa

        mes = self.request.GET.get("mes", timezone.localdate().strftime("%Y-%m"))

        try:
            ano, m = mes.split("-")
            ano, m = int(ano), int(m)
        except (ValueError, AttributeError):
            import datetime

            hoje = datetime.date.today()
            ano, m = hoje.year, hoje.month

        titulos = TituloFinanceiro.objects.filter(
            empresa=empresa,
            vencimento__year=ano,
            vencimento__month=m,
            status__in=["pago", "parcial"],
        )

        # Receitas agrupadas por natureza
        receitas = (
            titulos.filter(tipo="receber")
            .values("natureza")
            .annotate(total=Sum("valor_pago"))
            .order_by("natureza")
        )

        # Despesas agrupadas por natureza
        despesas = (
            titulos.filter(tipo="pagar")
            .values("natureza")
            .annotate(total=Sum("valor_pago"))
            .order_by("natureza")
        )

        total_receitas = sum(r["total"] or 0 for r in receitas)
        total_despesas = sum(d["total"] or 0 for d in despesas)

        ctx.update(
            {
                "mes": mes,
                "receitas": receitas,
                "despesas": despesas,
                "total_receitas": total_receitas,
                "total_despesas": total_despesas,
                "resultado": total_receitas - total_despesas,
            }
        )
        return ctx


class TituloCreateView(LoginRequiredMixin, CreateView):
    """Criação de novo título financeiro."""

    model = TituloFinanceiro
    template_name = "financeiro/titulo_form.html"
    fields = [
        "numero",
        "tipo",
        "natureza",
        "descricao",
        "valor",
        "vencimento",
        "status",
        "centro_custo",
        "conta",
        "pedido",
        "contrato",
        "forma_pagamento",
        "link_pagamento",
        "codigo_barras",
        "chave_pix",
        "observacoes",
    ]

    def form_valid(self, form):
        form.instance.empresa = self.request.user.perfil.empresa
        form.instance.criado_por = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        from django.urls import reverse

        tipo = self.object.tipo
        if tipo == "receber":
            return reverse("financeiro:receber")
        return reverse("financeiro:pagar")


@login_required
def baixar_titulo(request, pk):
    """HTMX POST — registra uma baixa (pagamento) de um título financeiro."""
    titulo = get_object_or_404(
        TituloFinanceiro, pk=pk, empresa=request.user.perfil.empresa
    )

    if request.method == "POST":
        from .models import ContaFinanceira

        valor = request.POST.get("valor", 0)
        forma = request.POST.get("forma_pagamento", "")
        conta_id = request.POST.get("conta")
        conta = None
        if conta_id:
            try:
                conta = ContaFinanceira.objects.get(pk=conta_id)
            except ContaFinanceira.DoesNotExist:
                pass

        baixa = Baixa.objects.create(
            titulo=titulo,
            data_baixa=request.POST.get("data_baixa") or timezone.localdate(),
            valor=valor,
            forma_pagamento=forma,
            conta=conta,
            observacao=request.POST.get("observacao", ""),
            usuario=request.user,
        )

        if "comprovante" in request.FILES:
            baixa.comprovante = request.FILES["comprovante"]
            baixa.save(update_fields=["comprovante"])

        # Atualiza valor pago e status do título
        titulo.valor_pago = (titulo.valor_pago or 0) + float(valor)
        if titulo.valor_pago >= float(titulo.valor):
            titulo.status = "pago"
            titulo.data_pagamento = timezone.localdate()
        else:
            titulo.status = "parcial"
        titulo.save(update_fields=["valor_pago", "status", "data_pagamento", "alterado_em"])

        if request.headers.get("HX-Request"):
            return render(
                request,
                "financeiro/partials/titulo_status.html",
                {"titulo": titulo, "baixa": baixa},
            )

    return redirect(
        "financeiro:receber" if titulo.tipo == "receber" else "financeiro:pagar"
    )
