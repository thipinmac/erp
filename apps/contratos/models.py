"""
Módulo Contratos — Geração, assinatura digital e gestão de contratos de venda.

Fluxo: Modelo → Elaboração → Aprovação Interna → Envio → Assinatura → Vigência → Encerramento.
"""
import secrets

from django.conf import settings
from django.db import models

from apps.core.models import AbstractBaseModel


class ModeloContrato(AbstractBaseModel):
    """Template/modelo reutilizável de contrato."""

    nome = models.CharField(max_length=255, verbose_name="Nome do Modelo")
    tipo_venda = models.CharField(max_length=100, blank=True, verbose_name="Tipo de Venda")
    linha_produto = models.CharField(max_length=100, blank=True, verbose_name="Linha de Produto")
    clausulas_padrao = models.TextField(verbose_name="Cláusulas Padrão")
    variaveis_disponiveis = models.JSONField(
        default=list,
        verbose_name="Variáveis Disponíveis",
        help_text='Lista de variáveis interpoláveis, ex: ["cliente_nome", "valor_total"]',
    )
    validade_dias = models.PositiveIntegerField(default=15, verbose_name="Validade (dias)")
    garantia_meses_padrao = models.PositiveSmallIntegerField(
        default=12, verbose_name="Garantia Padrão (meses)"
    )

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Modelo de Contrato"
        verbose_name_plural = "Modelos de Contrato"

    def __str__(self):
        return self.nome


class Clausula(AbstractBaseModel):
    """Cláusula individual associada a um modelo de contrato."""

    class Categoria(models.TextChoices):
        GARANTIA = "garantia", "Garantia"
        REAJUSTE = "reajuste", "Reajuste"
        MULTA = "multa", "Multa"
        ENTREGA = "entrega", "Entrega"
        RESPONSABILIDADE = "responsabilidade", "Responsabilidade"
        PAGAMENTO = "pagamento", "Pagamento"
        OUTRO = "outro", "Outro"

    modelo = models.ForeignKey(
        ModeloContrato,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clausulas",
        verbose_name="Modelo",
    )
    categoria = models.CharField(max_length=20, choices=Categoria.choices, verbose_name="Categoria")
    titulo = models.CharField(max_length=200, verbose_name="Título")
    texto = models.TextField(verbose_name="Texto")
    obrigatoria = models.BooleanField(default=True, verbose_name="Obrigatória")
    ordem = models.PositiveSmallIntegerField(default=0, verbose_name="Ordem")

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Cláusula"
        verbose_name_plural = "Cláusulas"
        ordering = ["modelo", "ordem"]

    def __str__(self):
        return f"{self.get_categoria_display()} — {self.titulo}"


class Contrato(AbstractBaseModel):
    """Contrato de venda firmado com o cliente."""

    class Status(models.TextChoices):
        ELABORACAO = "elaboracao", "Em Elaboração"
        APROVACAO_INTERNA = "aprovacao_interna", "Aprovação Interna"
        ENVIADO_ASSINATURA = "enviado_assinatura", "Enviado para Assinatura"
        ASSINADO = "assinado", "Assinado"
        VIGENCIA = "vigencia", "Em Vigência"
        ENCERRADO = "encerrado", "Encerrado"
        RESCINDIDO = "rescindido", "Rescindido"

    numero = models.CharField(max_length=30, verbose_name="Número")
    pedido = models.ForeignKey(
        "pedidos.Pedido",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contratos",
        verbose_name="Pedido",
    )
    cliente = models.ForeignKey(
        "cadastros.Cliente",
        on_delete=models.PROTECT,
        related_name="contratos",
        verbose_name="Cliente",
    )
    modelo = models.ForeignKey(
        ModeloContrato,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contratos_gerados",
        verbose_name="Modelo de Contrato",
    )
    valores_totais = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Valor Total")
    data_assinatura = models.DateTimeField(null=True, blank=True, verbose_name="Data de Assinatura")
    data_vigencia_inicio = models.DateField(null=True, blank=True, verbose_name="Início da Vigência")
    data_vigencia_fim = models.DateField(null=True, blank=True, verbose_name="Fim da Vigência")
    status = models.CharField(
        max_length=25,
        choices=Status.choices,
        default=Status.ELABORACAO,
        verbose_name="Status",
    )
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contratos_responsavel",
        verbose_name="Responsável",
    )
    assinatura_hash = models.CharField(max_length=128, blank=True, verbose_name="Hash da Assinatura")
    garantia_meses = models.PositiveSmallIntegerField(default=12, verbose_name="Garantia (meses)")
    conteudo_html = models.TextField(blank=True, verbose_name="Conteúdo HTML")
    pdf = models.FileField(
        upload_to="contratos/",
        null=True,
        blank=True,
        verbose_name="PDF do Contrato",
    )

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Contrato"
        verbose_name_plural = "Contratos"
        indexes = [
            models.Index(fields=["empresa", "status"]),
            models.Index(fields=["numero"]),
        ]

    def __str__(self):
        return f"Contrato {self.numero} — {self.cliente}"


class CronogramaFinanceiro(AbstractBaseModel):
    """Parcelas do cronograma financeiro do contrato."""

    class FormaPagamento(models.TextChoices):
        PIX = "pix", "PIX"
        BOLETO = "boleto", "Boleto"
        CARTAO = "cartao", "Cartão"
        TRANSFERENCIA = "transferencia", "Transferência"
        CHEQUE = "cheque", "Cheque"
        DINHEIRO = "dinheiro", "Dinheiro"

    contrato = models.ForeignKey(
        Contrato,
        on_delete=models.CASCADE,
        related_name="parcelas",
        verbose_name="Contrato",
    )
    numero_parcela = models.PositiveSmallIntegerField(verbose_name="Nº Parcela")
    valor = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Valor")
    data_vencimento = models.DateField(verbose_name="Data de Vencimento")
    gatilho = models.CharField(
        max_length=200,
        blank=True,
        help_text="ex: assinatura, entrega, aceite",
        verbose_name="Gatilho",
    )
    forma_pagamento = models.CharField(
        max_length=15,
        choices=FormaPagamento.choices,
        default=FormaPagamento.PIX,
        verbose_name="Forma de Pagamento",
    )
    paga = models.BooleanField(default=False, verbose_name="Paga")
    data_pagamento = models.DateField(null=True, blank=True, verbose_name="Data de Pagamento")
    titulo_financeiro = models.ForeignKey(
        "financeiro.TituloFinanceiro",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="parcelas_contrato",
        verbose_name="Título Financeiro",
    )

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Parcela do Cronograma"
        verbose_name_plural = "Parcelas do Cronograma"
        ordering = ["contrato", "numero_parcela"]

    def __str__(self):
        return f"{self.contrato.numero} — Parcela {self.numero_parcela} / R$ {self.valor}"


class PortalToken(AbstractBaseModel):
    """Token de acesso ao portal do cliente para visualização/assinatura do contrato."""

    contrato = models.OneToOneField(
        Contrato,
        on_delete=models.CASCADE,
        related_name="portal_token",
        verbose_name="Contrato",
    )
    token = models.CharField(max_length=64, unique=True, verbose_name="Token")
    validade = models.DateTimeField(null=True, blank=True, verbose_name="Validade")
    revogado = models.BooleanField(default=False, verbose_name="Revogado")
    data_revogacao = models.DateTimeField(null=True, blank=True, verbose_name="Data de Revogação")
    ultimo_acesso = models.DateTimeField(null=True, blank=True, verbose_name="Último Acesso")
    requer_2fa = models.BooleanField(default=False, verbose_name="Requer 2FA")

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Token do Portal"
        verbose_name_plural = "Tokens do Portal"

    def __str__(self):
        return f"Token portal — {self.contrato.numero}"

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
