"""Views do CRM com Kanban HTMX."""
import json
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.core.mixins import HTMXMixin, TenantMixin

from .models import EtapaPipeline, HistoricoOportunidade, Lead, Oportunidade, TarefaComercial, Visita


# ─── Pipeline Kanban ─────────────────────────────────────────────────────────

@login_required
def pipeline_view(request):
    """Pipeline Kanban principal do CRM."""
    empresa = request.empresa
    etapas = EtapaPipeline.objects.filter(empresa=empresa, ativo=True).order_by("ordem")

    # Monta o board com as oportunidades por etapa
    board = []
    for etapa in etapas:
        qs = Oportunidade.objects.filter(
            empresa=empresa,
            etapa=etapa,
            ativo=True,
        ).select_related("cliente", "lead", "responsavel").order_by("criado_em")

        # Filtros
        responsavel_id = request.GET.get("responsavel")
        if responsavel_id:
            qs = qs.filter(responsavel_id=responsavel_id)

        board.append({
            "etapa": etapa,
            "oportunidades": qs,
            "total_valor": sum(o.valor_estimado for o in qs),
            "count": qs.count(),
        })

    context = {
        "board": board,
        "etapas": etapas,
        "title": "Pipeline Comercial",
    }
    return render(request, "crm/pipeline.html", context)


@login_required
def mover_oportunidade(request, pk):
    """
    HTMX: move oportunidade para outra etapa via drag-and-drop.
    Recebe: etapa_id (nova etapa)
    """
    if request.method != "POST":
        return HttpResponse(status=405)

    oportunidade = get_object_or_404(Oportunidade, pk=pk, empresa=request.empresa)
    nova_etapa_id = request.POST.get("etapa_id")

    if not nova_etapa_id:
        return HttpResponse(status=400)

    nova_etapa = get_object_or_404(EtapaPipeline, pk=nova_etapa_id, empresa=request.empresa)
    etapa_anterior = oportunidade.etapa

    # Registra histórico
    if etapa_anterior != nova_etapa:
        HistoricoOportunidade.objects.create(
            oportunidade=oportunidade,
            etapa_anterior=etapa_anterior,
            etapa_nova=nova_etapa,
            usuario=request.user,
        )
        oportunidade.etapa = nova_etapa
        oportunidade.probabilidade = nova_etapa.probabilidade_padrao
        oportunidade.data_entrada_etapa = timezone.now()
        oportunidade.alterado_por = request.user
        oportunidade.save(update_fields=["etapa", "probabilidade", "data_entrada_etapa", "alterado_por", "alterado_em"])

    # Retorna o card atualizado
    return render(request, "crm/partials/oportunidade_card.html", {
        "oportunidade": oportunidade,
    })


@login_required
def oportunidade_detail_htmx(request, pk):
    """HTMX: painel lateral com detalhes da oportunidade."""
    oportunidade = get_object_or_404(Oportunidade, pk=pk, empresa=request.empresa)
    return render(request, "crm/partials/oportunidade_detail.html", {
        "oportunidade": oportunidade,
        "historico": oportunidade.historico.select_related("etapa_anterior", "etapa_nova", "usuario")[:10],
        "tarefas": oportunidade.tarefas.filter(concluida=False).order_by("data_vencimento")[:5],
        "visitas": oportunidade.visitas.order_by("-data_hora")[:5],
    })


# ─── Oportunidade CRUD ───────────────────────────────────────────────────────

class OportunidadeListView(TenantMixin, HTMXMixin, ListView):
    model = Oportunidade
    template_name = "crm/oportunidade_list.html"
    partial_template_name = "crm/partials/oportunidade_rows.html"
    context_object_name = "oportunidades"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related("etapa", "cliente", "lead", "responsavel")
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(titulo__icontains=q)
        return qs


class OportunidadeCreateView(TenantMixin, CreateView):
    model = Oportunidade
    template_name = "crm/oportunidade_form.html"
    fields = [
        "titulo", "lead", "cliente", "etapa", "responsavel",
        "valor_estimado", "probabilidade", "data_previsao_fechamento",
        "ambientes", "metragem_estimada", "prazo_cliente", "observacoes",
    ]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        empresa = self.request.empresa
        if empresa:
            form.fields["etapa"].queryset = EtapaPipeline.objects.filter(empresa=empresa, ativo=True)
            form.fields["lead"].queryset = Lead.objects.filter(empresa=empresa, ativo=True)
        return form

    def get_success_url(self):
        return reverse_lazy("crm:pipeline")


class OportunidadeDetailView(TenantMixin, DetailView):
    model = Oportunidade
    template_name = "crm/oportunidade_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["historico"] = self.object.historico.select_related("etapa_anterior", "etapa_nova")[:20]
        ctx["tarefas"] = self.object.tarefas.all().order_by("data_vencimento")
        ctx["visitas"] = self.object.visitas.order_by("-data_hora")
        return ctx


class OportunidadeUpdateView(TenantMixin, UpdateView):
    model = Oportunidade
    template_name = "crm/oportunidade_form.html"
    fields = [
        "titulo", "lead", "cliente", "etapa", "responsavel",
        "valor_estimado", "probabilidade", "data_previsao_fechamento",
        "ambientes", "metragem_estimada", "prazo_cliente",
        "motivo_perda", "observacoes",
    ]

    def get_success_url(self):
        return reverse_lazy("crm:oportunidade_detail", kwargs={"pk": self.object.pk})


# ─── Lead CRUD ───────────────────────────────────────────────────────────────

class LeadListView(TenantMixin, HTMXMixin, ListView):
    model = Lead
    template_name = "crm/lead_list.html"
    partial_template_name = "crm/partials/lead_rows.html"
    context_object_name = "leads"
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset().select_related("responsavel")
        q = self.request.GET.get("q")
        status = self.request.GET.get("status")
        if q:
            qs = qs.filter(nome__icontains=q) | qs.filter(email__icontains=q)
        if status:
            qs = qs.filter(status=status)
        return qs


class LeadCreateView(TenantMixin, CreateView):
    model = Lead
    template_name = "crm/lead_form.html"
    fields = [
        "nome", "email", "telefone", "whatsapp", "interesse",
        "canal_origem", "responsavel", "score", "observacoes",
    ]
    success_url = reverse_lazy("crm:lead_list")

    def get_template_names(self):
        if self.request.htmx:
            return ["crm/partials/lead_form_modal.html"]
        return super().get_template_names()

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.htmx:
            return HttpResponse(
                headers={"HX-Trigger": "leadCreated", "HX-Redirect": reverse_lazy("crm:lead_list")}
            )
        return response


class LeadDetailView(TenantMixin, DetailView):
    model = Lead
    template_name = "crm/lead_detail.html"


class LeadUpdateView(TenantMixin, UpdateView):
    model = Lead
    template_name = "crm/lead_form.html"
    fields = ["nome", "email", "telefone", "whatsapp", "interesse", "status", "canal_origem", "responsavel", "observacoes"]

    def get_success_url(self):
        return reverse_lazy("crm:lead_detail", kwargs={"pk": self.object.pk})


# ─── Visitas ─────────────────────────────────────────────────────────────────

class VisitaListView(TenantMixin, ListView):
    model = Visita
    template_name = "crm/visita_list.html"
    context_object_name = "visitas"
    paginate_by = 20


class VisitaCreateView(TenantMixin, CreateView):
    model = Visita
    template_name = "crm/visita_form.html"
    fields = ["tipo", "data_hora", "local", "oportunidade", "lead", "responsavel", "resumo", "proximos_passos"]
    success_url = reverse_lazy("crm:visita_list")


# ─── Tarefas ─────────────────────────────────────────────────────────────────

@login_required
def tarefas_hoje(request):
    """HTMX: lista de tarefas do dia no dashboard."""
    hoje = timezone.now().date()
    tarefas = TarefaComercial.objects.filter(
        empresa=request.empresa,
        responsavel=request.user,
        data_vencimento__date=hoje,
        concluida=False,
    ).select_related("oportunidade", "lead")[:10]
    return render(request, "crm/partials/tarefas_hoje.html", {"tarefas": tarefas})


@login_required
def concluir_tarefa(request, pk):
    """HTMX: marca tarefa como concluída."""
    tarefa = get_object_or_404(TarefaComercial, pk=pk, empresa=request.empresa)
    tarefa.concluida = True
    tarefa.data_conclusao = timezone.now()
    tarefa.save(update_fields=["concluida", "data_conclusao"])
    response = HttpResponse("")
    response["HX-Trigger"] = "tarefaConcluida"
    return response
