"""
Módulo Pedidos — Gestão do pedido de venda do cliente.

Fluxo: Aguardando Entrada → Liberado Engenharia → Liberado PCP →
  Em Produção → Em Expedição → Em Entrega → Concluído.
"""
from django.conf import settings
from django.db import models

from apps.core.models import AbstractBaseModel


class Pedido(AbstractBaseModel):
    """Pedido de venda — documento central que move o projeto para a fábrica."""

    class Status(models.TextChoices):
        AGUARDANDO_ENTRADA = "aguardando_entrada", "Aguardando Entrada"
        LIBERADO_ENGENHARIA = "liberado_engenharia", "Liberado p/ Engenharia"
        LIBERADO_PCP = "liberado_pcp", "Liberado para PCP"
        EM_PRODUCAO = "em_producao", "Em Produção"
        EM_EXPEDICAO = "em_expedicao", "Em Expedição"
        EM_ENTREGA = "em_entrega", "Em Entrega"
        CONCLUIDO = "concluido", "Concluído"
        CANCELADO = "cancelado", "Cancelado"

    class Risco(models.TextChoices):
        BAIXO = "baixo", "Baixo"
        MEDIO = "medio", "Médio"
        ALTO = "alto", "Alto"

    numero = models.CharField(max_length=30, verbose_name="Número do Pedido")
    proposta = models.ForeignKey(
        "orcamentos.Proposta",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pedidos",
        verbose_name="Proposta de Origem",
    )
    contrato = models.ForeignKey(
        "contratos.Contrato",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pedidos",
        verbose_name="Contrato",
    )
    cliente = models.ForeignKey(
        "cadastros.Cliente",
        on_delete=models.PROTECT,
        related_name="pedidos",
        verbose_name="Cliente",
    )
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pedidos_responsavel",
        verbose_name="Responsável",
    )
    filial = models.ForeignKey(
        "administracao.Filial",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pedidos",
        verbose_name="Filial",
    )
    valor_total = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Valor Total")
    status = models.CharField(
        max_length=25,
        choices=Status.choices,
        default=Status.AGUARDANDO_ENTRADA,
        verbose_name="Status",
    )
    risco = models.CharField(
        max_length=10,
        choices=Risco.choices,
        default=Risco.BAIXO,
        verbose_name="Risco",
    )
    data_prevista_entrega = models.DateField(null=True, blank=True, verbose_name="Previsão de Entrega")
    data_entrega_real = models.DateField(null=True, blank=True, verbose_name="Data de Entrega Real")
    prazo_comprometido = models.BooleanField(default=False, verbose_name="Prazo Comprometido")
    observacoes = models.TextField(blank=True, verbose_name="Observações")

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        indexes = [
            models.Index(fields=["empresa", "status"]),
            models.Index(fields=["numero"]),
            models.Index(fields=["empresa", "cliente"]),
        ]

    def __str__(self):
        return f"Pedido {self.numero} — {self.cliente}"


class MarcoPedido(AbstractBaseModel):
    """Marco de acompanhamento do pedido (timeline)."""

    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="marcos",
        verbose_name="Pedido",
    )
    etapa = models.CharField(max_length=100, verbose_name="Etapa")
    data_prevista = models.DateField(null=True, blank=True, verbose_name="Data Prevista")
    data_real = models.DateField(null=True, blank=True, verbose_name="Data Real")
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="marcos_pedido",
        verbose_name="Responsável",
    )
    concluido = models.BooleanField(default=False, verbose_name="Concluído")
    observacao = models.TextField(blank=True, verbose_name="Observação")
    publicar_portal = models.BooleanField(default=True, verbose_name="Publicar no Portal")

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Marco do Pedido"
        verbose_name_plural = "Marcos do Pedido"
        ordering = ["pedido", "data_prevista"]

    def __str__(self):
        return f"{self.pedido.numero} — {self.etapa}"


class PendenciaPedido(AbstractBaseModel):
    """Pendência que bloqueia ou atrasa o andamento do pedido."""

    class Tipo(models.TextChoices):
        DOCUMENTAL = "documental", "Documental"
        TECNICA = "tecnica", "Técnica"
        FINANCEIRA = "financeira", "Financeira"
        OBRA = "obra", "Obra"
        OUTRO = "outro", "Outro"

    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="pendencias",
        verbose_name="Pedido",
    )
    tipo = models.CharField(max_length=15, choices=Tipo.choices, verbose_name="Tipo")
    descricao = models.TextField(verbose_name="Descrição")
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pendencias_pedido",
        verbose_name="Responsável",
    )
    sla_horas = models.PositiveIntegerField(null=True, blank=True, verbose_name="SLA (horas)")
    bloqueante = models.BooleanField(default=False, verbose_name="Bloqueante")
    resolvida = models.BooleanField(default=False, verbose_name="Resolvida")
    data_resolucao = models.DateTimeField(null=True, blank=True, verbose_name="Data de Resolução")

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Pendência do Pedido"
        verbose_name_plural = "Pendências do Pedido"
        ordering = ["-bloqueante", "criado_em"]

    def __str__(self):
        return f"{self.pedido.numero} [{self.get_tipo_display()}] — {'BLOQUEANTE' if self.bloqueante else 'pendente'}"


class ComissaoPedido(AbstractBaseModel):
    """Comissão de venda vinculada ao pedido."""

    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        CALCULADA = "calculada", "Calculada"
        APROVADA = "aprovada", "Aprovada"
        PAGA = "paga", "Paga"

    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="comissoes_pedido",
        verbose_name="Pedido",
    )
    beneficiario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="comissoes_pedido",
        verbose_name="Beneficiário",
    )
    base = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Base de Cálculo")
    percentual = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Percentual (%)")
    valor = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Valor")
    gatilho = models.CharField(max_length=200, blank=True, verbose_name="Gatilho de Pagamento")
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.PENDENTE,
        verbose_name="Status",
    )
    data_pagamento = models.DateField(null=True, blank=True, verbose_name="Data de Pagamento")

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Comissão do Pedido"
        verbose_name_plural = "Comissões do Pedido"

    def __str__(self):
        return f"Comissão {self.pedido.numero} — {self.beneficiario} / R$ {self.valor}"

    def save(self, *args, **kwargs):
        self.valor = self.base * (self.percentual / 100)
        super().save(*args, **kwargs)
