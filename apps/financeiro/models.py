import uuid

from django.conf import settings
from django.db import models

from apps.core.models import AbstractBaseModel


class ContaFinanceira(AbstractBaseModel):
    """Conta bancária, caixa ou gateway de pagamento da empresa."""

    TIPO_CHOICES = [
        ("corrente", "Conta Corrente"),
        ("poupanca", "Poupança"),
        ("caixa", "Caixa"),
        ("cartao", "Cartão"),
        ("gateway", "Gateway"),
    ]

    nome = models.CharField(max_length=100, verbose_name="Nome")
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, verbose_name="Tipo")
    banco = models.CharField(max_length=100, blank=True, verbose_name="Banco")
    agencia = models.CharField(max_length=20, blank=True, verbose_name="Agência")
    conta = models.CharField(max_length=30, blank=True, verbose_name="Conta")
    gateway = models.CharField(max_length=50, blank=True, verbose_name="Gateway")
    saldo_inicial = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name="Saldo inicial"
    )

    class Meta:
        verbose_name = "Conta Financeira"
        verbose_name_plural = "Contas Financeiras"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} ({self.get_tipo_display()})"


class TituloFinanceiro(AbstractBaseModel):
    """Título financeiro a receber ou a pagar."""

    TIPO_CHOICES = [
        ("receber", "A Receber"),
        ("pagar", "A Pagar"),
    ]

    STATUS_CHOICES = [
        ("aberto", "Aberto"),
        ("parcial", "Parcialmente pago"),
        ("pago", "Pago"),
        ("vencido", "Vencido"),
        ("cancelado", "Cancelado"),
    ]

    FORMA_PAGAMENTO_CHOICES = [
        ("pix", "PIX"),
        ("boleto", "Boleto"),
        ("cartao", "Cartão"),
        ("transferencia", "Transferência"),
        ("dinheiro", "Dinheiro"),
        ("cheque", "Cheque"),
    ]

    numero = models.CharField(max_length=30, verbose_name="Número")
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, verbose_name="Tipo")
    natureza = models.CharField(max_length=100, blank=True, verbose_name="Natureza")
    descricao = models.CharField(max_length=255, verbose_name="Descrição")
    valor = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Valor")
    valor_pago = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name="Valor pago"
    )
    vencimento = models.DateField(verbose_name="Vencimento")
    data_pagamento = models.DateField(
        null=True, blank=True, verbose_name="Data de pagamento"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="aberto",
        verbose_name="Status",
    )
    centro_custo = models.ForeignKey(
        "cadastros.CentroCusto",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="titulos",
        verbose_name="Centro de custo",
    )
    conta = models.ForeignKey(
        ContaFinanceira,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="titulos",
        verbose_name="Conta",
    )
    pedido = models.ForeignKey(
        "pedidos.Pedido",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="titulos_financeiros",
        verbose_name="Pedido",
    )
    contrato = models.ForeignKey(
        "contratos.Contrato",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="titulos_financeiros",
        verbose_name="Contrato",
    )
    forma_pagamento = models.CharField(
        max_length=15,
        choices=FORMA_PAGAMENTO_CHOICES,
        blank=True,
        verbose_name="Forma de pagamento",
    )
    link_pagamento = models.URLField(blank=True, verbose_name="Link de pagamento")
    codigo_barras = models.CharField(
        max_length=100, blank=True, verbose_name="Código de barras"
    )
    chave_pix = models.CharField(max_length=100, blank=True, verbose_name="Chave PIX")
    observacoes = models.TextField(blank=True, verbose_name="Observações")

    class Meta:
        verbose_name = "Título Financeiro"
        verbose_name_plural = "Títulos Financeiros"
        ordering = ["vencimento"]

    def __str__(self):
        return f"{self.numero} — {self.descricao} ({self.get_tipo_display()})"

    @property
    def saldo_devedor(self):
        return self.valor - self.valor_pago


class Baixa(models.Model):
    """Registro de pagamento (baixa) de um título financeiro."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titulo = models.ForeignKey(
        TituloFinanceiro,
        on_delete=models.CASCADE,
        related_name="baixas",
        verbose_name="Título",
    )
    data_baixa = models.DateField(null=True, blank=True, verbose_name="Data da baixa")
    valor = models.DecimalField(
        max_digits=15, decimal_places=2, verbose_name="Valor"
    )
    forma_pagamento = models.CharField(
        max_length=30, blank=True, verbose_name="Forma de pagamento"
    )
    conta = models.ForeignKey(
        ContaFinanceira,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="baixas",
        verbose_name="Conta",
    )
    comprovante = models.FileField(
        upload_to="financeiro/comprovantes/",
        null=True,
        blank=True,
        verbose_name="Comprovante",
    )
    conciliado = models.BooleanField(default=False, verbose_name="Conciliado")
    observacao = models.TextField(blank=True, verbose_name="Observação")
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="baixas_financeiras",
        verbose_name="Usuário",
    )
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")

    class Meta:
        verbose_name = "Baixa"
        verbose_name_plural = "Baixas"
        ordering = ["-data_baixa"]

    def __str__(self):
        return f"Baixa R$ {self.valor} — {self.titulo.numero} em {self.data_baixa}"


class ComissaoFinanceira(models.Model):
    """Comissão financeira calculada sobre um pedido."""

    STATUS_CHOICES = [
        ("pendente", "Pendente"),
        ("calculada", "Calculada"),
        ("aprovada", "Aprovada"),
        ("paga", "Paga"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(
        "administracao.Empresa",
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name="Empresa",
    )
    pedido = models.ForeignKey(
        "pedidos.Pedido",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="comissoes",
        verbose_name="Pedido",
    )
    beneficiario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="comissoes",
        verbose_name="Beneficiário",
    )
    regra = models.CharField(max_length=100, blank=True, verbose_name="Regra")
    base = models.DecimalField(
        max_digits=15, decimal_places=2, verbose_name="Base de cálculo"
    )
    percentual = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name="Percentual (%)"
    )
    valor = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name="Valor"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="pendente",
        verbose_name="Status",
    )
    data_pagamento = models.DateField(
        null=True, blank=True, verbose_name="Data de pagamento"
    )

    class Meta:
        verbose_name = "Comissão Financeira"
        verbose_name_plural = "Comissões Financeiras"
        ordering = ["-id"]

    def __str__(self):
        return f"Comissão {self.percentual}% — {self.beneficiario} ({self.get_status_display()})"


class Conciliacao(models.Model):
    """Conciliação bancária entre extrato e sistema."""

    STATUS_CHOICES = [
        ("aberta", "Aberta"),
        ("em_andamento", "Em Andamento"),
        ("conciliada", "Conciliada"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(
        "administracao.Empresa",
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name="Empresa",
    )
    conta = models.ForeignKey(
        ContaFinanceira,
        on_delete=models.PROTECT,
        related_name="conciliacoes",
        verbose_name="Conta",
    )
    data_inicio = models.DateField(verbose_name="Data início")
    data_fim = models.DateField(verbose_name="Data fim")
    saldo_extrato = models.DecimalField(
        max_digits=15, decimal_places=2, verbose_name="Saldo do extrato"
    )
    saldo_sistema = models.DecimalField(
        max_digits=15, decimal_places=2, verbose_name="Saldo no sistema"
    )
    divergencia = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name="Divergência"
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default="aberta",
        verbose_name="Status",
    )
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conciliacoes",
        verbose_name="Responsável",
    )

    class Meta:
        verbose_name = "Conciliação"
        verbose_name_plural = "Conciliações"
        ordering = ["-data_fim"]

    def __str__(self):
        return f"Conciliação {self.conta.nome} — {self.data_inicio} a {self.data_fim}"
