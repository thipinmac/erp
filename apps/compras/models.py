"""
Módulo Compras — Requisição, cotação, pedido de compra e recebimento de materiais.

Fluxo: Requisição → Cotação → Pedido de Compra → Recebimento → Estoque.
"""
from django.conf import settings
from django.db import models

from apps.core.models import AbstractBaseModel


class RequisicaoCompra(AbstractBaseModel):
    """Requisição interna de compra de materiais ou serviços."""

    class Origem(models.TextChoices):
        PCP = "pcp", "PCP"
        ESTOQUE_MINIMO = "estoque_minimo", "Estoque Mínimo"
        MANUAL = "manual", "Manual"
        ASSISTENCIA = "assistencia", "Assistência Técnica"

    class Prioridade(models.TextChoices):
        NORMAL = "normal", "Normal"
        URGENTE = "urgente", "Urgente"
        CRITICA = "critica", "Crítica"

    class Status(models.TextChoices):
        ABERTA = "aberta", "Aberta"
        COTANDO = "cotando", "Em Cotação"
        APROVADA = "aprovada", "Aprovada"
        COMPRADA = "comprada", "Comprada"
        RECEBIDA = "recebida", "Recebida"
        CANCELADA = "cancelada", "Cancelada"

    numero = models.CharField(max_length=30, verbose_name="Número")
    origem = models.CharField(max_length=20, choices=Origem.choices, verbose_name="Origem")
    item = models.ForeignKey(
        "cadastros.Item",
        on_delete=models.PROTECT,
        related_name="requisicoes",
        verbose_name="Item",
    )
    quantidade = models.DecimalField(max_digits=15, decimal_places=4, verbose_name="Quantidade")
    quantidade_aprovada = models.DecimalField(
        max_digits=15, decimal_places=4, null=True, blank=True, verbose_name="Quantidade Aprovada"
    )
    prioridade = models.CharField(
        max_length=10,
        choices=Prioridade.choices,
        default=Prioridade.NORMAL,
        verbose_name="Prioridade",
    )
    centro_custo = models.ForeignKey(
        "cadastros.CentroCusto",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="requisicoes",
        verbose_name="Centro de Custo",
    )
    justificativa = models.TextField(blank=True, verbose_name="Justificativa")
    pedido = models.ForeignKey(
        "pedidos.Pedido",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="requisicoes",
        verbose_name="Pedido de Origem",
    )
    op = models.ForeignKey(
        "producao.OrdemProducao",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="requisicoes",
        verbose_name="Ordem de Produção",
    )
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.ABERTA,
        verbose_name="Status",
    )
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="requisicoes_compra",
        verbose_name="Responsável",
    )

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Requisição de Compra"
        verbose_name_plural = "Requisições de Compra"
        indexes = [
            models.Index(fields=["empresa", "status"]),
            models.Index(fields=["empresa", "prioridade"]),
        ]

    def __str__(self):
        return f"RC {self.numero} — {self.item} ({self.quantidade})"


class Cotacao(AbstractBaseModel):
    """Cotação de preços junto a fornecedores."""

    class Status(models.TextChoices):
        RASCUNHO = "rascunho", "Rascunho"
        ENVIADA = "enviada", "Enviada"
        RESPONDIDA = "respondida", "Respondida"
        APROVADA = "aprovada", "Aprovada"
        CANCELADA = "cancelada", "Cancelada"

    numero = models.CharField(max_length=30, verbose_name="Número")
    requisicoes = models.ManyToManyField(
        RequisicaoCompra,
        blank=True,
        related_name="cotacoes",
        verbose_name="Requisições",
    )
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.RASCUNHO,
        verbose_name="Status",
    )
    validade = models.DateField(null=True, blank=True, verbose_name="Validade")
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cotacoes",
        verbose_name="Responsável",
    )

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Cotação"
        verbose_name_plural = "Cotações"

    def __str__(self):
        return f"Cotação {self.numero} [{self.get_status_display()}]"


class ItemCotacao(AbstractBaseModel):
    """Item de resposta de cotação por fornecedor."""

    cotacao = models.ForeignKey(
        Cotacao,
        on_delete=models.CASCADE,
        related_name="itens",
        verbose_name="Cotação",
    )
    fornecedor = models.ForeignKey(
        "cadastros.Fornecedor",
        on_delete=models.PROTECT,
        related_name="itens_cotacao",
        verbose_name="Fornecedor",
    )
    item = models.ForeignKey(
        "cadastros.Item",
        on_delete=models.PROTECT,
        related_name="itens_cotacao",
        verbose_name="Item",
    )
    quantidade = models.DecimalField(max_digits=15, decimal_places=4, verbose_name="Quantidade")
    preco_unitario = models.DecimalField(max_digits=15, decimal_places=4, verbose_name="Preço Unitário")
    frete = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Frete")
    prazo_entrega_dias = models.PositiveIntegerField(default=0, verbose_name="Prazo de Entrega (dias)")
    condicao_pagamento = models.CharField(max_length=100, blank=True, verbose_name="Condição de Pagamento")
    vencedor = models.BooleanField(default=False, verbose_name="Vencedor")
    observacoes = models.TextField(blank=True, verbose_name="Observações")

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Item de Cotação"
        verbose_name_plural = "Itens de Cotação"

    def __str__(self):
        return f"{self.cotacao.numero} — {self.fornecedor} / {self.item}"


class PedidoCompra(AbstractBaseModel):
    """Pedido de compra emitido para o fornecedor."""

    class Status(models.TextChoices):
        RASCUNHO = "rascunho", "Rascunho"
        APROVADO = "aprovado", "Aprovado"
        EMITIDO = "emitido", "Emitido"
        EM_TRANSITO = "em_transito", "Em Trânsito"
        RECEBIDO = "recebido", "Recebido"
        CANCELADO = "cancelado", "Cancelado"

    numero = models.CharField(max_length=30, verbose_name="Número")
    fornecedor = models.ForeignKey(
        "cadastros.Fornecedor",
        on_delete=models.PROTECT,
        related_name="pedidos_compra",
        verbose_name="Fornecedor",
    )
    cotacao = models.ForeignKey(
        Cotacao,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pedidos_compra",
        verbose_name="Cotação de Origem",
    )
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.RASCUNHO,
        verbose_name="Status",
    )
    data_emissao = models.DateField(null=True, blank=True, verbose_name="Data de Emissão")
    data_prevista_entrega = models.DateField(null=True, blank=True, verbose_name="Previsão de Entrega")
    data_entrega_real = models.DateField(null=True, blank=True, verbose_name="Data de Entrega Real")
    condicao_pagamento = models.CharField(max_length=100, blank=True, verbose_name="Condição de Pagamento")
    frete_valor = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Valor do Frete")
    valor_total = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Valor Total")
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pedidos_compra",
        verbose_name="Responsável",
    )

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Pedido de Compra"
        verbose_name_plural = "Pedidos de Compra"
        indexes = [
            models.Index(fields=["empresa", "status"]),
            models.Index(fields=["numero"]),
        ]

    def __str__(self):
        return f"PC {self.numero} — {self.fornecedor}"


class ItemPedidoCompra(AbstractBaseModel):
    """Item de um pedido de compra."""

    pedido = models.ForeignKey(
        PedidoCompra,
        on_delete=models.CASCADE,
        related_name="itens",
        verbose_name="Pedido de Compra",
    )
    item = models.ForeignKey(
        "cadastros.Item",
        on_delete=models.PROTECT,
        related_name="itens_pedido_compra",
        verbose_name="Item",
    )
    quantidade = models.DecimalField(max_digits=15, decimal_places=4, verbose_name="Quantidade")
    quantidade_recebida = models.DecimalField(
        max_digits=15, decimal_places=4, default=0, verbose_name="Quantidade Recebida"
    )
    preco_unitario = models.DecimalField(max_digits=15, decimal_places=4, verbose_name="Preço Unitário")
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Total")

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Item do Pedido de Compra"
        verbose_name_plural = "Itens do Pedido de Compra"

    def __str__(self):
        return f"{self.pedido.numero} — {self.item} ({self.quantidade})"

    def save(self, *args, **kwargs):
        self.total = self.quantidade * self.preco_unitario
        super().save(*args, **kwargs)


class Recebimento(AbstractBaseModel):
    """Registro de recebimento físico de mercadorias."""

    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        CONFERIDO = "conferido", "Conferido"
        DIVERGENCIA = "divergencia", "Com Divergência"
        ENCERRADO = "encerrado", "Encerrado"

    pedido_compra = models.ForeignKey(
        PedidoCompra,
        on_delete=models.PROTECT,
        related_name="recebimentos",
        verbose_name="Pedido de Compra",
    )
    data = models.DateField(verbose_name="Data de Recebimento")
    xml_nfe = models.TextField(blank=True, verbose_name="XML da NF-e")
    chave_nfe = models.CharField(max_length=44, blank=True, verbose_name="Chave NF-e")
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recebimentos",
        verbose_name="Responsável",
    )
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.PENDENTE,
        verbose_name="Status",
    )
    observacoes = models.TextField(blank=True, verbose_name="Observações")

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Recebimento"
        verbose_name_plural = "Recebimentos"

    def __str__(self):
        return f"Recebimento {self.pedido_compra.numero} — {self.data}"


class ItemRecebimento(AbstractBaseModel):
    """Item conferido no recebimento de mercadorias."""

    recebimento = models.ForeignKey(
        Recebimento,
        on_delete=models.CASCADE,
        related_name="itens",
        verbose_name="Recebimento",
    )
    item = models.ForeignKey(
        "cadastros.Item",
        on_delete=models.PROTECT,
        related_name="itens_recebimento",
        verbose_name="Item",
    )
    quantidade_pedida = models.DecimalField(max_digits=15, decimal_places=4, verbose_name="Qtd Pedida")
    quantidade_recebida = models.DecimalField(max_digits=15, decimal_places=4, verbose_name="Qtd Recebida")
    quantidade_divergencia = models.DecimalField(
        max_digits=15, decimal_places=4, default=0, verbose_name="Qtd Divergência"
    )
    custo_unitario = models.DecimalField(max_digits=15, decimal_places=4, verbose_name="Custo Unitário")
    custo_total = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Custo Total")
    lote = models.CharField(max_length=100, blank=True, verbose_name="Lote")
    aceito = models.BooleanField(default=True, verbose_name="Aceito")

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Item do Recebimento"
        verbose_name_plural = "Itens do Recebimento"

    def __str__(self):
        return f"Receb. {self.recebimento_id} — {self.item} ({self.quantidade_recebida})"

    def save(self, *args, **kwargs):
        self.quantidade_divergencia = self.quantidade_pedida - self.quantidade_recebida
        self.custo_total = self.quantidade_recebida * self.custo_unitario
        super().save(*args, **kwargs)
