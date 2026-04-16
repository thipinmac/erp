"""Views do módulo Contratos."""
import hashlib

from django.contrib.auth.decorators import login_required
from django.core.signals import Signal
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView

from apps.core.mixins import HTMXMixin, TenantMixin

from .models import Clausula, Contrato, CronogramaFinanceiro, ModeloContrato, PortalToken

# Sinal emitido após assinatura do contrato
contrato_assinado = Signal()


# ─── Contrato CRUD ───────────────────────────────────────────────────────────

class ContratoListView(TenantMixin, HTMXMixin, ListView):
    """Lista de contratos com filtros por status e cliente."""

    model = Contrato
    template_name = "contratos/contrato_list.html"
    partial_template_name = "contratos/partials/contrato_rows.html"
    context_object_name = "contratos"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related("cliente", "responsavel", "modelo")
        status = self.request.GET.get("status")
        q = self.request.GET.get("q")
        if status:
            qs = qs.filter(status=status)
        if q:
            qs = qs.filter(numero__icontains=q) | qs.filter(cliente__nome__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = Contrato.Status.choices
        ctx["status_atual"] = self.request.GET.get("status", "")
        return ctx


class ContratoDetailView(TenantMixin, DetailView):
    """Detalhe do contrato com parcelas e token do portal."""

    model = Contrato
    template_name = "contratos/contrato_detail.html"

    def get_queryset(self):
        return super().get_queryset().select_related(
            "cliente", "responsavel", "modelo", "pedido"
        ).prefetch_related("parcelas")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["parcelas"] = self.object.parcelas.order_by("numero_parcela")
        ctx["pode_assinar"] = self.object.status == Contrato.Status.ENVIADO_ASSINATURA
        try:
            ctx["portal_token"] = self.object.portal_token
        except PortalToken.DoesNotExist:
            ctx["portal_token"] = None
        if self.object.modelo:
            ctx["clausulas"] = self.object.modelo.clausulas.filter(ativo=True).order_by("ordem")
        else:
            ctx["clausulas"] = []
        return ctx


class ContratoCreateView(TenantMixin, CreateView):
    """Criação de novo contrato, opcionalmente baseado em um modelo."""

    model = Contrato
    template_name = "contratos/contrato_form.html"
    fields = [
        "numero",
        "pedido",
        "cliente",
        "modelo",
        "valores_totais",
        "data_vigencia_inicio",
        "data_vigencia_fim",
        "responsavel",
        "garantia_meses",
        "conteudo_html",
    ]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        empresa = self.request.empresa
        if empresa:
            form.fields["modelo"].queryset = ModeloContrato.objects.filter(empresa=empresa, ativo=True)
        return form

    def form_valid(self, form):
        contrato = form.instance
        # Preenche conteúdo HTML com cláusulas do modelo se não informado
        if contrato.modelo and not contrato.conteudo_html:
            contrato.conteudo_html = contrato.modelo.clausulas_padrao
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("contratos:detail", kwargs={"pk": self.object.pk})


# ─── Assinatura ──────────────────────────────────────────────────────────────

@login_required
def assinar_contrato(request, pk):
    """
    POST: marca contrato como assinado, gera PortalToken e dispara sinal.
    Gera um hash SHA-256 como comprovante da assinatura digital.
    """
    if request.method != "POST":
        return HttpResponse(status=405)

    contrato = get_object_or_404(Contrato, pk=pk, empresa=request.empresa)

    if contrato.status not in (Contrato.Status.ENVIADO_ASSINATURA, Contrato.Status.APROVACAO_INTERNA):
        if request.htmx:
            response = HttpResponse("Contrato não está apto para assinatura.", status=422)
            response["HX-Trigger"] = "assinaturaErro"
            return response
        return redirect(reverse_lazy("contratos:detail", kwargs={"pk": pk}))

    agora = timezone.now()

    # Gera hash de assinatura com conteúdo + timestamp + usuário
    payload = f"{contrato.pk}{contrato.cliente_id}{agora.isoformat()}{request.user.pk}"
    contrato.assinatura_hash = hashlib.sha256(payload.encode()).hexdigest()
    contrato.status = Contrato.Status.ASSINADO
    contrato.data_assinatura = agora
    contrato.alterado_por = request.user
    contrato.save(update_fields=[
        "status", "data_assinatura", "assinatura_hash", "alterado_por", "alterado_em"
    ])

    # Cria ou atualiza PortalToken para acesso do cliente
    portal_token, created = PortalToken.objects.get_or_create(
        contrato=contrato,
        defaults={
            "empresa": contrato.empresa,
            "filial": contrato.filial,
            "ativo": True,
        },
    )
    if not created:
        portal_token.ativo = True
        portal_token.revogado = False
        portal_token.save(update_fields=["ativo", "revogado"])

    # Emite sinal para integrações: financeiro, comunicação, etc.
    contrato_assinado.send(
        sender=Contrato,
        contrato=contrato,
        portal_token=portal_token,
        usuario=request.user,
        timestamp=agora,
    )

    if request.htmx:
        response = render(
            request,
            "contratos/partials/contrato_status_badge.html",
            {"contrato": contrato, "portal_token": portal_token},
        )
        response["HX-Trigger"] = "contratoAssinado"
        return response

    return redirect(reverse_lazy("contratos:detail", kwargs={"pk": pk}))


# ─── Geração de PDF ──────────────────────────────────────────────────────────

@login_required
def gerar_pdf_contrato(request, pk):
    """
    Gera o PDF do contrato usando WeasyPrint.
    Retorna o PDF como attachment ou fallback HTML para impressão.
    """
    contrato = get_object_or_404(Contrato, pk=pk, empresa=request.empresa)

    clausulas = []
    if contrato.modelo:
        clausulas = contrato.modelo.clausulas.filter(ativo=True).order_by("ordem")

    html_content = render_to_string(
        "contratos/contrato_pdf.html",
        {
            "contrato": contrato,
            "parcelas": contrato.parcelas.order_by("numero_parcela"),
            "clausulas": clausulas,
        },
        request=request,
    )

    try:
        from weasyprint import HTML as WeasyHTML

        pdf_bytes = WeasyHTML(string=html_content, base_url=request.build_absolute_uri("/")).write_pdf()
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="contrato_{contrato.numero}.pdf"'
        )
        return response
    except ImportError:
        # Fallback: retorna HTML para impressão via browser
        return HttpResponse(html_content, content_type="text/html")
