"""
Módulo 2 — Cadastros Mestres, Catálogo Técnico e Tabelas-Base.

Entidades: Cliente, Fornecedor, Item/Produto/Material,
Ferragem, Acabamento, TabelaPreco, CentroCusto, UnidadeMedida.
"""
from django.db import models
from apps.core.models import AbstractBaseModel


# ─── Tabelas Auxiliares ───────────────────────────────────────────────────────

class UnidadeMedida(models.Model):
    empresa = models.ForeignKey("administracao.Empresa", on_delete=models.CASCADE)
    codigo = models.CharField(max_length=10)
    descricao = models.CharField(max_length=50)
    tipo = models.CharField(max_length=20, choices=[
        ("comprimento", "Comprimento"),
        ("area", "Área"),
        ("volume", "Volume"),
        ("massa", "Massa"),
        ("unidade", "Unidade"),
        ("par", "Par"),
        ("caixa", "Caixa"),
        ("rolo", "Rolo"),
        ("litro", "Litro"),
    ])
    fator_conversao = models.DecimalField(max_digits=15, decimal_places=6, default=1)
    unidade_base = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        unique_together = [("empresa", "codigo")]
        verbose_name = "Unidade de Medida"
        verbose_name_plural = "Unidades de Medida"

    def __str__(self):
        return f"{self.codigo} — {self.descricao}"


class CentroCusto(models.Model):
    empresa = models.ForeignKey("administracao.Empresa", on_delete=models.CASCADE)
    codigo = models.CharField(max_length=20)
    nome = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=[
        ("receita", "Receita"),
        ("custo", "Custo"),
        ("despesa", "Despesa"),
    ])
    pai = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="filhos")
    ativo = models.BooleanField(default=True)

    class Meta:
        unique_together = [("empresa", "codigo")]
        verbose_name = "Centro de Custo"
        verbose_name_plural = "Centros de Custo"

    def __str__(self):
        return f"{self.codigo} — {self.nome}"


# ─── Cliente ──────────────────────────────────────────────────────────────────

class Cliente(AbstractBaseModel):
    """Clientes, contatos, arquitetos e especificadores."""

    class TipoPessoa(models.TextChoices):
        FISICA = "F", "Pessoa Física"
        JURIDICA = "J", "Pessoa Jurídica"

    class Origem(models.TextChoices):
        INDICACAO = "indicacao", "Indicação"
        INSTAGRAM = "instagram", "Instagram"
        GOOGLE = "google", "Google"
        SITE = "site", "Site"
        FACHADA = "fachada", "Fachada/Loja"
        PARCEIRO = "parceiro", "Parceiro/Arquiteto"
        WHATSAPP = "whatsapp", "WhatsApp"
        OUTRO = "outro", "Outro"

    tipo_pessoa = models.CharField(max_length=1, choices=TipoPessoa.choices, default=TipoPessoa.FISICA)

    # PF
    nome = models.CharField(max_length=255, verbose_name="Nome completo")
    cpf = models.CharField(max_length=14, blank=True, verbose_name="CPF")
    rg = models.CharField(max_length=20, blank=True)
    data_nascimento = models.DateField(null=True, blank=True)

    # PJ
    razao_social = models.CharField(max_length=255, blank=True)
    nome_fantasia = models.CharField(max_length=255, blank=True)
    cnpj = models.CharField(max_length=18, blank=True)
    ie = models.CharField(max_length=30, blank=True)

    # Contato
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    whatsapp = models.CharField(max_length=20, blank=True)
    instagram = models.CharField(max_length=100, blank=True)

    # Endereço principal (obra)
    cep_obra = models.CharField(max_length=9, blank=True)
    logradouro_obra = models.CharField(max_length=255, blank=True)
    numero_obra = models.CharField(max_length=20, blank=True)
    complemento_obra = models.CharField(max_length=100, blank=True)
    bairro_obra = models.CharField(max_length=100, blank=True)
    cidade_obra = models.CharField(max_length=100, blank=True)
    uf_obra = models.CharField(max_length=2, blank=True)

    # CRM
    origem = models.CharField(max_length=30, choices=Origem.choices, blank=True)
    arquiteto_parceiro = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="clientes_indicados", verbose_name="Arquiteto/Parceiro"
    )

    # LGPD
    consentimento_lgpd = models.BooleanField(default=False)
    data_consentimento = models.DateTimeField(null=True, blank=True)

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        indexes = [
            models.Index(fields=["empresa", "nome"]),
            models.Index(fields=["empresa", "cpf"]),
            models.Index(fields=["empresa", "cnpj"]),
        ]

    def __str__(self):
        return self.nome or self.razao_social

    @property
    def nome_exibicao(self):
        return self.nome or self.razao_social or self.nome_fantasia

    @property
    def documento(self):
        return self.cpf if self.tipo_pessoa == self.TipoPessoa.FISICA else self.cnpj


# ─── Fornecedor ──────────────────────────────────────────────────────────────

class Fornecedor(AbstractBaseModel):
    razao_social = models.CharField(max_length=255)
    nome_fantasia = models.CharField(max_length=255, blank=True)
    cnpj = models.CharField(max_length=18, blank=True)
    cpf = models.CharField(max_length=14, blank=True)
    tipo_pessoa = models.CharField(max_length=1, choices=[("F", "PF"), ("J", "PJ")], default="J")

    # Contato
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    whatsapp = models.CharField(max_length=20, blank=True)
    site = models.URLField(blank=True)
    contato_principal = models.CharField(max_length=100, blank=True)

    # Endereço
    cep = models.CharField(max_length=9, blank=True)
    logradouro = models.CharField(max_length=255, blank=True)
    numero = models.CharField(max_length=20, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    uf = models.CharField(max_length=2, blank=True)

    # Condições comerciais
    lead_time_dias = models.PositiveIntegerField(default=0, verbose_name="Lead time (dias)")
    condicao_pagamento = models.CharField(max_length=100, blank=True)
    frete_modalidade = models.CharField(max_length=50, blank=True)

    # Classificação
    categorias = models.CharField(max_length=500, blank=True, help_text="Chapas, Ferragens, Acabamentos, etc.")
    homologado = models.BooleanField(default=False)
    avaliacao = models.PositiveSmallIntegerField(null=True, blank=True, choices=[(i, i) for i in range(1, 6)])

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"

    def __str__(self):
        return self.nome_fantasia or self.razao_social


# ─── Família e Categoria de Item ──────────────────────────────────────────────

class FamiliaItem(models.Model):
    empresa = models.ForeignKey("administracao.Empresa", on_delete=models.CASCADE)
    codigo = models.CharField(max_length=20)
    nome = models.CharField(max_length=100)
    pai = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="filhos")

    class Meta:
        unique_together = [("empresa", "codigo")]
        verbose_name = "Família de Item"

    def __str__(self):
        return self.nome


# ─── Item / Produto / Material ───────────────────────────────────────────────

class Item(AbstractBaseModel):
    """Catálogo unificado: chapas, fitas, ferragens, acessórios, consumíveis, serviços."""

    class Tipo(models.TextChoices):
        CHAPA = "chapa", "Chapa"
        FITA = "fita", "Fita de Borda"
        FERRAGEM = "ferragem", "Ferragem"
        ACABAMENTO = "acabamento", "Acabamento"
        ACESSORIO = "acessorio", "Acessório"
        CONSUMIVEL = "consumivel", "Consumível"
        SERVICO = "servico", "Serviço"
        PRODUTO_ACABADO = "produto_acabado", "Produto Acabado"
        MATERIA_PRIMA = "mp", "Matéria-Prima"

    codigo = models.CharField(max_length=50, verbose_name="Código interno")
    codigo_fornecedor = models.CharField(max_length=50, blank=True)
    descricao = models.CharField(max_length=255, verbose_name="Descrição")
    descricao_complementar = models.TextField(blank=True)
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    familia = models.ForeignKey(FamiliaItem, null=True, blank=True, on_delete=models.SET_NULL)
    unidade = models.ForeignKey(UnidadeMedida, on_delete=models.PROTECT, related_name="itens")

    # Dimensões (para chapas e perfis)
    largura_mm = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    comprimento_mm = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    espessura_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    peso_kg = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)

    # Identificação técnica
    marca = models.CharField(max_length=100, blank=True)
    modelo = models.CharField(max_length=100, blank=True)
    cor = models.CharField(max_length=100, blank=True)
    padrao = models.CharField(max_length=100, blank=True)
    ncm = models.CharField(max_length=10, blank=True, verbose_name="NCM")
    ean = models.CharField(max_length=14, blank=True, verbose_name="EAN/Código de barras")

    # Financeiro
    custo_base = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    custo_medio = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    preco_venda = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Estoque
    estoque_minimo = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    estoque_maximo = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    estoque_seguranca = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    lead_time_dias = models.PositiveIntegerField(default=0)

    # Controle
    controla_estoque = models.BooleanField(default=True)
    permite_venda = models.BooleanField(default=False)
    compra_automatica = models.BooleanField(default=False)

    # Fornecedor preferencial
    fornecedor_preferencial = models.ForeignKey(
        Fornecedor, null=True, blank=True, on_delete=models.SET_NULL, related_name="itens_preferenciais"
    )

    # Foto
    foto = models.ImageField(upload_to="itens/fotos/", null=True, blank=True)

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Item / Material"
        verbose_name_plural = "Itens / Materiais"
        indexes = [
            models.Index(fields=["empresa", "codigo"]),
            models.Index(fields=["empresa", "tipo"]),
            models.Index(fields=["empresa", "ncm"]),
        ]

    def __str__(self):
        return f"[{self.codigo}] {self.descricao}"


# ─── Tabela de Preço ──────────────────────────────────────────────────────────

class TabelaPreco(AbstractBaseModel):
    nome = models.CharField(max_length=100)
    vigencia_inicio = models.DateField()
    vigencia_fim = models.DateField(null=True, blank=True)
    base_custo = models.CharField(max_length=30, choices=[
        ("custo_base", "Custo base"),
        ("custo_medio", "Custo médio"),
        ("ultimo_custo", "Último custo"),
    ], default="custo_base")
    markup_padrao = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    margem_minima = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    padrao = models.BooleanField(default=False)

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Tabela de Preço"
        verbose_name_plural = "Tabelas de Preço"

    def __str__(self):
        return self.nome


class TabelaPrecoItem(models.Model):
    """Preço específico por item em uma tabela."""
    tabela = models.ForeignKey(TabelaPreco, on_delete=models.CASCADE, related_name="itens")
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    markup = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    preco_venda = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    desconto_maximo = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        unique_together = [("tabela", "item")]
