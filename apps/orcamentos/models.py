"""
Módulo 4 — Orçamento Rápido, Orçamento Técnico e Propostas.

Motor de cálculo:
  custo_total + margem → preco_venda
  impostos estimados calculados sobre preco_venda
  desconto aplicado → preco_final
"""
from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.core.models import AbstractBaseModel


class TemplateProposta(AbstractBaseModel):
    """Templates personalizáveis de proposta com branding."""
    nome = models.CharField(max_length=100)
    cabecalho_html = models.TextField(blank=True)
    rodape_html = models.TextField(blank=True)
    clausulas_padrao = models.TextField(blank=True)
    validade_dias = models.PositiveIntegerField(default=15)
    padrao = models.BooleanField(default=False)

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Template de Proposta"
        verbose_name_plural = "Templates de Proposta"

    def __str__(self):
        return self.nome


class OrcamentoRapido(AbstractBaseModel):
    """
    Pré-orçamento rápido para triagem comercial.
    Baseado em metro quadrado, valor base e margem.
    """

    class Status(models.TextChoices):
        RASCUNHO = "rascunho", "Rascunho"
        ENVIADO = "enviado", "Enviado"
        APROVADO = "aprovado", "Aprovado"
        EXPIRADO = "expirado", "Expirado"

    cliente = models.ForeignKey(
        "cadastros.Cliente", on_delete=models.SET_NULL, null=True, blank=True, related_name="orcamentos_rapidos"
    )
    oportunidade = models.ForeignKey(
        "crm.Oportunidade", on_delete=models.SET_NULL, null=True, blank=True, related_name="orcamentos_rapidos"
    )
    numero = models.CharField(max_length=20, blank=True)
    tipo_movel = models.CharField(max_length=100, blank=True)
    ambientes = models.CharField(max_length=500, blank=True)
    area_m2 = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    valor_base_m2 = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    margem_pct = models.DecimalField(max_digits=5, decimal_places=2, default=30)
    desconto_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    valor_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RASCUNHO)
    validade = models.DateField(null=True, blank=True)
    responsavel = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Orçamento Rápido"
        verbose_name_plural = "Orçamentos Rápidos"

    def __str__(self):
        return f"OR-{self.numero or self.pk} | {self.cliente}"

    def calcular(self):
        """Motor de cálculo simplificado."""
        area = self.area_m2 or Decimal("1")
        base = self.valor_base_m2 * area
        com_margem = base * (1 + self.margem_pct / 100)
        self.valor_total = com_margem * (1 - self.desconto_pct / 100)

    def save(self, *args, **kwargs):
        self.calcular()
        super().save(*args, **kwargs)


class OrcamentoTecnico(AbstractBaseModel):
    """Orçamento técnico completo com ambientes, módulos e memória de cálculo."""

    class Status(models.TextChoices):
        RASCUNHO = "rascunho", "Rascunho"
        EM_REVISAO = "em_revisao", "Em revisão interna"
        ENVIADO = "enviado", "Enviado ao cliente"
        EM_NEGOCIACAO = "em_negociacao", "Em negociação"
        APROVADO = "aprovado", "Aprovado"
        REPROVADO = "reprovado", "Reprovado"
        EXPIRADO = "expirado", "Expirado"

    numero = models.CharField(max_length=20, blank=True)
    versao = models.PositiveSmallIntegerField(default=1)
    cliente = models.ForeignKey(
        "cadastros.Cliente", on_delete=models.SET_NULL, null=True, related_name="orcamentos_tecnicos"
    )
    oportunidade = models.ForeignKey(
        "crm.Oportunidade", on_delete=models.SET_NULL, null=True, blank=True, related_name="orcamentos_tecnicos"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RASCUNHO)
    responsavel = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    template = models.ForeignKey(TemplateProposta, on_delete=models.SET_NULL, null=True, blank=True)

    # Datas
    data_validade = models.DateField(null=True, blank=True)
    data_aprovacao = models.DateTimeField(null=True, blank=True)

    # Totais calculados (desnormalizados para performance)
    custo_materiais = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    custo_mao_obra = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    custo_instalacao = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    custo_deslocamento = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    custo_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    markup_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    margem_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    impostos_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    desconto_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    desconto_valor = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    preco_bruto = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    preco_final = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Condições comerciais
    condicao_pagamento = models.CharField(max_length=200, blank=True)
    prazo_entrega_dias = models.PositiveIntegerField(null=True, blank=True)
    garantia_meses = models.PositiveSmallIntegerField(default=12)

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Orçamento Técnico"
        verbose_name_plural = "Orçamentos Técnicos"
        indexes = [
            models.Index(fields=["empresa", "status"]),
            models.Index(fields=["empresa", "cliente"]),
        ]

    def __str__(self):
        return f"OT-{self.numero or self.pk} v{self.versao} | {self.cliente}"

    def recalcular(self):
        """Recalcula todos os totais a partir dos itens."""
        itens = self.itens.all()
        self.custo_materiais = sum(i.custo_materiais for i in itens)
        self.custo_mao_obra = sum(i.custo_mao_obra for i in itens)
        self.custo_instalacao = sum(i.custo_instalacao for i in itens)
        custo = self.custo_materiais + self.custo_mao_obra + self.custo_instalacao + self.custo_deslocamento
        self.custo_total = custo

        if self.markup_pct > 0:
            self.preco_bruto = custo * (1 + self.markup_pct / 100)
            self.margem_pct = (self.preco_bruto - custo) / self.preco_bruto * 100 if self.preco_bruto else 0
        elif self.margem_pct > 0:
            self.preco_bruto = custo / (1 - self.margem_pct / 100) if self.margem_pct < 100 else custo
        else:
            self.preco_bruto = custo

        impostos = self.preco_bruto * (self.impostos_pct / 100)
        preco_com_impostos = self.preco_bruto + impostos

        desconto = max(self.desconto_pct / 100 * preco_com_impostos, self.desconto_valor)
        self.desconto_valor = desconto
        self.preco_final = preco_com_impostos - desconto


class AmbienteOrcamento(models.Model):
    """Ambiente dentro de um orçamento técnico (cozinha, sala, etc.)."""
    orcamento = models.ForeignKey(OrcamentoTecnico, on_delete=models.CASCADE, related_name="ambientes")
    nome = models.CharField(max_length=100, help_text="Ex: Cozinha, Dormitório Casal")
    ordem = models.PositiveSmallIntegerField(default=0)
    observacoes = models.TextField(blank=True)

    class Meta:
        ordering = ["orcamento", "ordem"]

    def __str__(self):
        return f"{self.orcamento} — {self.nome}"


class ItemOrcamento(AbstractBaseModel):
    """Item de linha do orçamento técnico."""

    class TipoItem(models.TextChoices):
        MODULO = "modulo", "Módulo"
        FERRAGEM = "ferragem", "Ferragem"
        SERVICO = "servico", "Serviço"
        MAO_OBRA = "mao_obra", "Mão de obra"
        INSTALACAO = "instalacao", "Instalação"
        DESLOCAMENTO = "deslocamento", "Deslocamento"
        OUTRO = "outro", "Outro"

    orcamento = models.ForeignKey(OrcamentoTecnico, on_delete=models.CASCADE, related_name="itens")
    ambiente = models.ForeignKey(AmbienteOrcamento, on_delete=models.SET_NULL, null=True, blank=True, related_name="itens")
    tipo = models.CharField(max_length=20, choices=TipoItem.choices, default=TipoItem.MODULO)
    descricao = models.CharField(max_length=255)
    item_catalogo = models.ForeignKey("cadastros.Item", on_delete=models.SET_NULL, null=True, blank=True)
    especificacao = models.TextField(blank=True)
    quantidade = models.DecimalField(max_digits=10, decimal_places=4, default=1)
    unidade = models.CharField(max_length=20, default="un")
    largura_mm = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    altura_mm = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    profundidade_mm = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    # Custos unitários
    custo_material_unit = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    custo_mao_obra_unit = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    custo_instalacao_unit = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    perda_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Totais
    custo_materiais = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    custo_mao_obra = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    custo_instalacao = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    custo_total_item = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    preco_unitario = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    preco_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    ordem = models.PositiveSmallIntegerField(default=0)

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Item de Orçamento"
        verbose_name_plural = "Itens de Orçamento"
        ordering = ["orcamento", "ordem"]

    def __str__(self):
        return f"{self.descricao} x{self.quantidade}"

    def save(self, *args, **kwargs):
        fator_perda = 1 + self.perda_pct / 100
        self.custo_materiais = self.custo_material_unit * self.quantidade * fator_perda
        self.custo_mao_obra = self.custo_mao_obra_unit * self.quantidade
        self.custo_instalacao = self.custo_instalacao_unit * self.quantidade
        self.custo_total_item = self.custo_materiais + self.custo_mao_obra + self.custo_instalacao
        super().save(*args, **kwargs)


class MemoriaCalculo(models.Model):
    """Memória de cálculo auditável — salva a composição de cada item."""
    item_orcamento = models.ForeignKey(ItemOrcamento, on_delete=models.CASCADE, related_name="memorias")
    descricao = models.CharField(max_length=255)
    composicao = models.JSONField(default=dict, help_text="Coeficientes, tempos, fórmulas usados")
    fonte_custo = models.CharField(max_length=100, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em"]

    def __str__(self):
        return f"Memória: {self.descricao}"


class Proposta(AbstractBaseModel):
    """Versão oficial da proposta enviada ao cliente."""

    class Status(models.TextChoices):
        RASCUNHO = "rascunho", "Rascunho"
        ENVIADA = "enviada", "Enviada"
        EM_NEGOCIACAO = "em_negociacao", "Em negociação"
        APROVADA = "aprovada", "Aprovada"
        REPROVADA = "reprovada", "Reprovada"
        EXPIRADA = "expirada", "Expirada"

    orcamento = models.ForeignKey(OrcamentoTecnico, on_delete=models.CASCADE, related_name="propostas")
    numero = models.CharField(max_length=30, blank=True)
    versao = models.PositiveSmallIntegerField(default=1)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RASCUNHO)
    data_envio = models.DateTimeField(null=True, blank=True)
    data_validade = models.DateField(null=True, blank=True)
    data_aceite = models.DateTimeField(null=True, blank=True)
    aceite_ip = models.GenericIPAddressField(null=True, blank=True)
    arquivo_pdf = models.FileField(upload_to="propostas/", null=True, blank=True)
    hash_integridade = models.CharField(max_length=64, blank=True)

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Proposta"
        verbose_name_plural = "Propostas"

    def __str__(self):
        return f"Proposta {self.numero} v{self.versao} — {self.status}"
