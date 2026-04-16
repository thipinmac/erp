"""Views do módulo Engenharia e Projetos."""
from django.contrib.auth.decorators import login_required
from django.core.signals import Signal
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView

from apps.core.mixins import HTMXMixin, TenantMixin

from .models import BOM, AmbienteProjeto, DivergenciaProjeto, PecaComponente, PlanoCorte, ProjetoTecnico

# Sinal emitido quando projeto é liberado para PCP
projeto_liberado_para_pcp = Signal()


# ─── ProjetoTecnico ──────────────────────────────────────────────────────────

class ProjetoTecnicoListView(TenantMixin, HTMXMixin, ListView):
    """Lista de projetos técnicos com filtro por status."""

    model = ProjetoTecnico
    template_name = "engenharia/projeto_list.html"
    partial_template_name = "engenharia/partials/projeto_rows.html"
    context_object_name = "projetos"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related(
            "responsavel_tecnico", "pedido", "oportunidade"
        )
        status = self.request.GET.get("status")
        q = self.request.GET.get("q")
        if status:
            qs = qs.filter(status=status)
        if q:
            qs = qs.filter(numero__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = ProjetoTecnico.Status.choices
        ctx["status_atual"] = self.request.GET.get("status", "")
        return ctx


class ProjetoTecnicoDetailView(TenantMixin, DetailView):
    """Detalhe do projeto técnico com ambientes, BOM e divergências."""

    model = ProjetoTecnico
    template_name = "engenharia/projeto_detail.html"

    def get_queryset(self):
        return super().get_queryset().prefetch_related(
            "ambientes__pecas",
            "divergencias",
            "bom_itens__item",
            "planos_corte",
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["ambientes"] = self.object.ambientes.order_by("ordem")
        ctx["divergencias_abertas"] = self.object.divergencias.filter(resolvida=False)
        ctx["bom"] = self.object.bom_itens.select_related("item", "ambiente").order_by("ambiente__ordem")
        ctx["planos_corte"] = self.object.planos_corte.select_related("chapa")
        ctx["pode_liberar"] = (
            self.object.status == ProjetoTecnico.Status.VALIDADO
            and not self.object.divergencias.filter(resolvida=False, gravidade__in=["critica", "alta"]).exists()
        )
        return ctx


class ProjetoTecnicoCreateView(TenantMixin, CreateView):
    """Criação de novo projeto técnico."""

    model = ProjetoTecnico
    template_name = "engenharia/projeto_form.html"
    fields = [
        "numero",
        "pedido",
        "oportunidade",
        "arquivo_importado",
        "formato_origem",
        "versao_projeto",
        "responsavel_tecnico",
        "status",
        "observacoes",
    ]

    def get_success_url(self):
        return reverse_lazy("engenharia:projeto_detail", kwargs={"pk": self.object.pk})


# ─── BOM ─────────────────────────────────────────────────────────────────────

class BOMListView(TenantMixin, HTMXMixin, ListView):
    """Lista consolidada do BOM com filtros por projeto e item."""

    model = BOM
    template_name = "engenharia/bom_list.html"
    partial_template_name = "engenharia/partials/bom_rows.html"
    context_object_name = "bom_itens"
    paginate_by = 50

    def get_queryset(self):
        qs = super().get_queryset().select_related("projeto", "item", "ambiente", "fornecedor_preferencial")
        projeto_id = self.request.GET.get("projeto")
        falta = self.request.GET.get("falta")
        if projeto_id:
            qs = qs.filter(projeto_id=projeto_id)
        if falta:
            qs = qs.filter(falta=True)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["projetos"] = ProjetoTecnico.objects.filter(
            empresa=self.request.empresa,
            status__in=[ProjetoTecnico.Status.VALIDADO, ProjetoTecnico.Status.LIBERADO],
        )
        return ctx


# ─── Liberar para PCP ────────────────────────────────────────────────────────

@login_required
def liberar_para_pcp(request, pk):
    """
    POST: libera o projeto técnico para o PCP.
    Muda status para 'liberado' e emite sinal projeto_liberado_para_pcp.
    Responde com HX-Trigger para views HTMX ou redireciona para detalhe.
    """
    if request.method != "POST":
        return HttpResponse(status=405)

    projeto = get_object_or_404(ProjetoTecnico, pk=pk, empresa=request.empresa)

    # Validações de negócio
    divergencias_criticas = projeto.divergencias.filter(resolvida=False, gravidade="critica")
    if divergencias_criticas.exists():
        if request.htmx:
            response = HttpResponse("Existem divergências críticas não resolvidas.", status=422)
            response["HX-Trigger"] = "liberacaoErro"
            return response
        return redirect(reverse_lazy("engenharia:projeto_detail", kwargs={"pk": pk}))

    if projeto.status not in (ProjetoTecnico.Status.VALIDADO, ProjetoTecnico.Status.AGUARDANDO_AJUSTE):
        if request.htmx:
            response = HttpResponse("Status inválido para liberação.", status=422)
            response["HX-Trigger"] = "liberacaoErro"
            return response
        return redirect(reverse_lazy("engenharia:projeto_detail", kwargs={"pk": pk}))

    # Atualiza status
    projeto.status = ProjetoTecnico.Status.LIBERADO
    projeto.alterado_por = request.user
    projeto.save(update_fields=["status", "alterado_por", "alterado_em"])

    # Emite sinal para integrações downstream (PCP, notificações, etc.)
    projeto_liberado_para_pcp.send(
        sender=ProjetoTecnico,
        projeto=projeto,
        usuario=request.user,
        timestamp=timezone.now(),
    )

    if request.htmx:
        response = render(
            request,
            "engenharia/partials/projeto_status_badge.html",
            {"projeto": projeto},
        )
        response["HX-Trigger"] = "projetoLiberado"
        return response

    return redirect(reverse_lazy("engenharia:projeto_detail", kwargs={"pk": pk}))
