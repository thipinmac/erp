"""Views do módulo Cadastros com HTMX."""
from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.core.mixins import HTMXMixin, TenantMixin

from .models import Cliente, Fornecedor, Item


# ─── Cliente ──────────────────────────────────────────────────────────────────

class ClienteListView(TenantMixin, HTMXMixin, ListView):
    model = Cliente
    template_name = "cadastros/cliente_list.html"
    partial_template_name = "cadastros/partials/cliente_rows.html"
    context_object_name = "clientes"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q")
        tipo = self.request.GET.get("tipo")
        if q:
            qs = qs.filter(nome__icontains=q) | qs.filter(razao_social__icontains=q) | qs.filter(cpf__icontains=q) | qs.filter(cnpj__icontains=q)
        if tipo:
            qs = qs.filter(tipo_pessoa=tipo)
        return qs.select_related("empresa", "filial")


class ClienteCreateView(TenantMixin, CreateView):
    model = Cliente
    template_name = "cadastros/cliente_form.html"
    fields = [
        "tipo_pessoa", "nome", "cpf", "rg", "razao_social", "nome_fantasia", "cnpj",
        "email", "telefone", "whatsapp", "instagram",
        "cep_obra", "logradouro_obra", "numero_obra", "complemento_obra",
        "bairro_obra", "cidade_obra", "uf_obra",
        "origem", "observacoes",
    ]
    success_url = reverse_lazy("cadastros:cliente_list")


class ClienteDetailView(TenantMixin, DetailView):
    model = Cliente
    template_name = "cadastros/cliente_detail.html"


class ClienteUpdateView(TenantMixin, UpdateView):
    model = Cliente
    template_name = "cadastros/cliente_form.html"
    fields = [
        "tipo_pessoa", "nome", "cpf", "rg", "razao_social", "nome_fantasia", "cnpj",
        "email", "telefone", "whatsapp", "instagram",
        "cep_obra", "logradouro_obra", "numero_obra", "complemento_obra",
        "bairro_obra", "cidade_obra", "uf_obra",
        "origem", "observacoes", "ativo",
    ]

    def get_success_url(self):
        return reverse_lazy("cadastros:cliente_detail", kwargs={"pk": self.object.pk})


class ClienteDeleteView(TenantMixin, DeleteView):
    model = Cliente
    success_url = reverse_lazy("cadastros:cliente_list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.soft_delete(user=request.user)
        if request.htmx:
            return HttpResponse("")
        return super().delete(request, *args, **kwargs)


# ─── Fornecedor ──────────────────────────────────────────────────────────────

class FornecedorListView(TenantMixin, HTMXMixin, ListView):
    model = Fornecedor
    template_name = "cadastros/fornecedor_list.html"
    partial_template_name = "cadastros/partials/fornecedor_rows.html"
    context_object_name = "fornecedores"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(razao_social__icontains=q) | qs.filter(nome_fantasia__icontains=q)
        return qs


class FornecedorCreateView(TenantMixin, CreateView):
    model = Fornecedor
    template_name = "cadastros/fornecedor_form.html"
    fields = [
        "tipo_pessoa", "razao_social", "nome_fantasia", "cnpj", "cpf",
        "email", "telefone", "whatsapp", "contato_principal",
        "cep", "logradouro", "numero", "cidade", "uf",
        "lead_time_dias", "condicao_pagamento", "categorias", "observacoes",
    ]
    success_url = reverse_lazy("cadastros:fornecedor_list")


class FornecedorDetailView(TenantMixin, DetailView):
    model = Fornecedor
    template_name = "cadastros/fornecedor_detail.html"


class FornecedorUpdateView(TenantMixin, UpdateView):
    model = Fornecedor
    template_name = "cadastros/fornecedor_form.html"
    fields = [
        "tipo_pessoa", "razao_social", "nome_fantasia", "cnpj",
        "email", "telefone", "whatsapp", "contato_principal",
        "lead_time_dias", "condicao_pagamento", "categorias",
        "homologado", "avaliacao", "observacoes", "ativo",
    ]

    def get_success_url(self):
        return reverse_lazy("cadastros:fornecedor_detail", kwargs={"pk": self.object.pk})


# ─── Item ────────────────────────────────────────────────────────────────────

class ItemListView(TenantMixin, HTMXMixin, ListView):
    model = Item
    template_name = "cadastros/item_list.html"
    partial_template_name = "cadastros/partials/item_rows.html"
    context_object_name = "itens"
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q")
        tipo = self.request.GET.get("tipo")
        if q:
            qs = qs.filter(codigo__icontains=q) | qs.filter(descricao__icontains=q)
        if tipo:
            qs = qs.filter(tipo=tipo)
        return qs.select_related("unidade", "familia", "fornecedor_preferencial")


class ItemCreateView(TenantMixin, CreateView):
    model = Item
    template_name = "cadastros/item_form.html"
    fields = [
        "codigo", "descricao", "tipo", "familia", "unidade",
        "largura_mm", "comprimento_mm", "espessura_mm",
        "marca", "modelo", "cor", "padrao", "ncm", "ean",
        "custo_base", "preco_venda",
        "estoque_minimo", "estoque_maximo", "lead_time_dias",
        "fornecedor_preferencial", "controla_estoque", "observacoes",
    ]
    success_url = reverse_lazy("cadastros:item_list")


class ItemDetailView(TenantMixin, DetailView):
    model = Item
    template_name = "cadastros/item_detail.html"


class ItemUpdateView(TenantMixin, UpdateView):
    model = Item
    template_name = "cadastros/item_form.html"
    fields = [
        "codigo", "descricao", "tipo", "familia", "unidade",
        "largura_mm", "comprimento_mm", "espessura_mm",
        "marca", "modelo", "cor", "padrao", "ncm",
        "custo_base", "preco_venda",
        "estoque_minimo", "estoque_maximo", "lead_time_dias",
        "fornecedor_preferencial", "controla_estoque", "ativo", "observacoes",
    ]

    def get_success_url(self):
        return reverse_lazy("cadastros:item_detail", kwargs={"pk": self.object.pk})


# ─── HTMX Autocomplete ────────────────────────────────────────────────────────

@login_required
def buscar_clientes(request):
    """HTMX: busca clientes para autocomplete em forms."""
    q = request.GET.get("q", "")
    clientes = []
    if q and len(q) >= 2:
        clientes = Cliente.objects.filter(
            empresa=request.empresa,
            ativo=True,
        ).filter(
            models.Q(nome__icontains=q) | models.Q(razao_social__icontains=q) | models.Q(cpf__icontains=q)
        )[:10]
    return render(request, "cadastros/partials/autocomplete_clientes.html", {"clientes": clientes})


@login_required
def buscar_itens(request):
    """HTMX: busca itens para autocomplete em orçamentos/compras."""
    q = request.GET.get("q", "")
    itens = []
    if q and len(q) >= 2:
        itens = Item.objects.filter(
            empresa=request.empresa,
            ativo=True,
        ).filter(
            models.Q(codigo__icontains=q) | models.Q(descricao__icontains=q)
        )[:10]
    return render(request, "cadastros/partials/autocomplete_itens.html", {"itens": itens})
