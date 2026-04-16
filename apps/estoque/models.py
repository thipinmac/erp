"""
Módulo Estoque — Controle de saldos, movimentações, lotes, reservas e inventário.

Modelos:
  - Localizacao: endereçamento físico (almoxarifado/rua/prateleira/box)
  - SaldoEstoque: saldo consolidado por empresa/item/localização
  - Lote: rastreabilidade de lotes de materiais
  - MovimentacaoEstoque: registro imutável de toda movimentação
  - ReservaEstoque: reserva de saldo para pedidos/OPs
  - SobraChapa: controle de sobras de chapas do corte
  - Inventario / ItemInventario: contagem física periódica
"""
import uuid

from django.conf import settings
from django.db import models

from apps.core.models import AbstractBaseModel


class Localizacao(AbstractBaseModel):
    """Endereçamento físico do estoque (almoxarifado, rua, prateleira, box)."""

    class Tipo(models.TextChoices):
        ALMOXARIFADO = "almoxarifado", "Almoxarifado"
        RUA = "rua", "Rua"
        PRATELEIRA = "prateleira", "Prateleira"
        BOX = "box", "Box"

    nome = models.CharField(max_length=100, verbose_name="Nome")
    tipo = models.CharField(max_length=15, choices=Tipo.choices, verbose_name="Tipo")
    restricao_uso = models.CharField(max_length=200, blank=True, verbose_name="Restrição de Uso")

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Localização"
        verbose_name_plural = "Localizações"
        ordering = ["empresa", "tipo", "nome"]

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.nome}"


class SaldoEstoque(AbstractBaseModel):
    """
    Saldo consolidado por empresa/item/localização.
    Atualizado por signals disparados nas MovimentacaoEstoque.
    """

    item = models.ForeignKey(
        "cadastros.Item",
        on_delete=models.PROTECT,
        related_name="saldos",
        verbose_name="Item",
    )
    localizacao = models.ForeignKey(
        Localizacao,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="saldos",
        verbose_name="Localização",
    )
    saldo_atual = models.DecimalField(max_digits=15, decimal_places=4, default=0, verbose_name="Saldo Atual")
    saldo_reservado = models.DecimalField(max_digits=15, decimal_places=4, default=0, verbose_name="Saldo Reservado")
    saldo_disponivel = models.DecimalField(
        max_digits=15, decimal_places=4, default=0, verbose_name="Saldo Disponível"
    )
    saldo_em_transito = models.DecimalField(
        max_digits=15, decimal_places=4, default=0, verbose_name="Saldo em Trânsito"
    )
    custo_medio = models.DecimalField(max_digits=15, decimal_places=4, default=0, verbose_name="Custo Médio")
    ultima_movimentacao = models.DateTimeField(null=True, blank=True, verbose_name="Última Movimentação")

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Saldo de Estoque"
        verbose_name_plural = "Saldos de Estoque"
        unique_together = [("empresa", "item", "localizacao")]
        indexes = [
            models.Index(fields=["empresa", "item"]),
        ]

    def __str__(self):
        return f"{self.item} @ {self.localizacao or 'Geral'} = {self.saldo_disponivel}"

    def save(self, *args, **kwargs):
        self.saldo_disponivel = self.saldo_atual - self.saldo_reservado
        super().save(*args, **kwargs)


class Lote(models.Model):
    """
    Rastreabilidade de lote de materiais.
    Não herda AbstractBaseModel pois empresa/filial são gerenciados diretamente.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(
        "administracao.Empresa",
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name="Empresa",
    )
    filial = models.ForeignKey(
        "administracao.Filial",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="Filial",
    )
    codigo = models.CharField(max_length=50, verbose_name="Código do Lote")
    item = models.ForeignKey(
        "cadastros.Item",
        on_delete=models.PROTECT,
        related_name="lotes",
        verbose_name="Item",
    )
    fornecedor = models.ForeignKey(
        "cadastros.Fornecedor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lotes",
        verbose_name="Fornecedor",
    )
    data_fabricacao = models.DateField(null=True, blank=True, verbose_name="Data de Fabricação")
    data_validade = models.DateField(null=True, blank=True, verbose_name="Data de Validade")
    quantidade_inicial = models.DecimalField(max_digits=15, decimal_places=4, verbose_name="Quantidade Inicial")
    quantidade_atual = models.DecimalField(max_digits=15, decimal_places=4, verbose_name="Quantidade Atual")
    custo_unitario = models.DecimalField(max_digits=15, decimal_places=4, verbose_name="Custo Unitário")
    localizacao = models.ForeignKey(
        Localizacao,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lotes",
        verbose_name="Localização",
    )
    observacao = models.TextField(blank=True, verbose_name="Observação")
    criado_em = models.DateTimeField(auto_now_add=True)
    alterado_em = models.DateTimeField(auto_now=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Lote"
        verbose_name_plural = "Lotes"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"Lote {self.codigo} — {self.item} ({self.quantidade_atual})"


class MovimentacaoEstoque(models.Model):
    """
    Registro imutável de toda movimentação de estoque.
    Não herda AbstractBaseModel para preservar a imutabilidade do registro.
    """

    class Tipo(models.TextChoices):
        ENTRADA = "entrada", "Entrada"
        SAIDA = "saida", "Saída"
        TRANSFERENCIA = "transferencia", "Transferência"
        AJUSTE = "ajuste", "Ajuste"
        RESERVA = "reserva", "Reserva"
        DEVOLUCAO = "devolucao", "Devolução"
        PRODUCAO = "producao", "Produção"
        EXPEDICAO = "expedicao", "Expedição"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(
        "administracao.Empresa",
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name="Empresa",
    )
    filial = models.ForeignKey(
        "administracao.Filial",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="Filial",
    )
    tipo = models.CharField(max_length=15, choices=Tipo.choices, verbose_name="Tipo")
    item = models.ForeignKey(
        "cadastros.Item",
        on_delete=models.PROTECT,
        related_name="movimentacoes",
        verbose_name="Item",
    )
    lote = models.ForeignKey(
        Lote,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimentacoes",
        verbose_name="Lote",
    )
    localizacao_origem = models.ForeignKey(
        Localizacao,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimentacoes_saida",
        verbose_name="Localização Origem",
    )
    localizacao_destino = models.ForeignKey(
        Localizacao,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimentacoes_entrada",
        verbose_name="Localização Destino",
    )
    quantidade = models.DecimalField(max_digits=15, decimal_places=4, verbose_name="Quantidade")
    custo_unitario = models.DecimalField(max_digits=15, decimal_places=4, default=0, verbose_name="Custo Unitário")
    custo_total = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Custo Total")
    motivo = models.CharField(max_length=200, blank=True, verbose_name="Motivo")
    referencia_modelo = models.CharField(max_length=100, blank=True, verbose_name="Modelo de Referência")
    referencia_id = models.UUIDField(null=True, blank=True, verbose_name="ID de Referência")
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimentacoes_estoque",
        verbose_name="Usuário",
    )
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")

    class Meta:
        verbose_name = "Movimentação de Estoque"
        verbose_name_plural = "Movimentações de Estoque"
        ordering = ["-criado_em"]
        indexes = [
            models.Index(fields=["empresa", "item", "criado_em"]),
            models.Index(fields=["empresa", "tipo"]),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.item} / {self.quantidade} [{self.criado_em:%d/%m/%Y}]"

    def save(self, *args, **kwargs):
        self.custo_total = self.quantidade * self.custo_unitario
        super().save(*args, **kwargs)


class ReservaEstoque(AbstractBaseModel):
    """Reserva de saldo de estoque para pedidos ou ordens de produção."""

    class Status(models.TextChoices):
        ATIVA = "ativa", "Ativa"
        PARCIAL = "parcial", "Parcialmente Atendida"
        ATENDIDA = "atendida", "Atendida"
        CANCELADA = "cancelada", "Cancelada"

    item = models.ForeignKey(
        "cadastros.Item",
        on_delete=models.PROTECT,
        related_name="reservas",
        verbose_name="Item",
    )
    lote = models.ForeignKey(
        Lote,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reservas",
        verbose_name="Lote",
    )
    quantidade = models.DecimalField(max_digits=15, decimal_places=4, verbose_name="Quantidade Reservada")
    quantidade_atendida = models.DecimalField(
        max_digits=15, decimal_places=4, default=0, verbose_name="Quantidade Atendida"
    )
    pedido = models.ForeignKey(
        "pedidos.Pedido",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reservas_estoque",
        verbose_name="Pedido",
    )
    op = models.CharField(
        max_length=36,
        blank=True,
        help_text="UUID da Ordem de Produção",
        verbose_name="OP",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ATIVA,
        verbose_name="Status",
    )
    prioridade = models.PositiveSmallIntegerField(default=5, verbose_name="Prioridade")

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Reserva de Estoque"
        verbose_name_plural = "Reservas de Estoque"
        ordering = ["prioridade", "criado_em"]

    def __str__(self):
        return f"Reserva {self.item} — {self.quantidade} [{self.get_status_display()}]"


class SobraChapa(AbstractBaseModel):
    """Registro de sobras de chapas geradas no processo de corte."""

    class Estado(models.TextChoices):
        BOA = "boa", "Boa"
        AMASSADA = "amassada", "Amassada"
        RISCADA = "riscada", "Riscada"
        CORTADA = "cortada", "Cortada"

    item = models.ForeignKey(
        "cadastros.Item",
        on_delete=models.PROTECT,
        related_name="sobras_chapa",
        verbose_name="Item (Chapa)",
    )
    largura_mm = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Largura (mm)")
    comprimento_mm = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Comprimento (mm)")
    espessura_mm = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Espessura (mm)")
    area_mm2 = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Área (mm²)")
    localizacao = models.ForeignKey(
        Localizacao,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sobras_chapa",
        verbose_name="Localização",
    )
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.BOA, verbose_name="Estado")
    reaproveitavel = models.BooleanField(default=True, verbose_name="Reaproveitável")
    projeto_origem = models.CharField(
        max_length=36, blank=True, verbose_name="Projeto de Origem (UUID/Número)"
    )
    observacao = models.CharField(max_length=200, blank=True, verbose_name="Observação")

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Sobra de Chapa"
        verbose_name_plural = "Sobras de Chapa"
        ordering = ["-area_mm2"]

    def __str__(self):
        return f"Sobra {self.item} — {self.largura_mm}x{self.comprimento_mm}mm [{self.get_estado_display()}]"

    def save(self, *args, **kwargs):
        self.area_mm2 = self.largura_mm * self.comprimento_mm
        super().save(*args, **kwargs)


class Inventario(AbstractBaseModel):
    """Contagem física de inventário (geral, cíclico ou localizado)."""

    class Tipo(models.TextChoices):
        GERAL = "geral", "Geral"
        CICLICO = "ciclico", "Cíclico"
        LOCALIZADO = "localizado", "Localizado"

    class Status(models.TextChoices):
        ABERTO = "aberto", "Aberto"
        CONTANDO = "contando", "Contando"
        APROVADO = "aprovado", "Aprovado"
        CANCELADO = "cancelado", "Cancelado"

    nome = models.CharField(max_length=100, verbose_name="Nome")
    tipo = models.CharField(max_length=15, choices=Tipo.choices, verbose_name="Tipo")
    data_inicio = models.DateField(verbose_name="Data de Início")
    data_fim = models.DateField(null=True, blank=True, verbose_name="Data de Fim")
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ABERTO,
        verbose_name="Status",
    )
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inventarios",
        verbose_name="Responsável",
    )
    aprovado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inventarios_aprovados",
        verbose_name="Aprovado por",
    )

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Inventário"
        verbose_name_plural = "Inventários"

    def __str__(self):
        return f"{self.nome} — {self.data_inicio} [{self.get_status_display()}]"


class ItemInventario(AbstractBaseModel):
    """Item de contagem dentro de um inventário."""

    inventario = models.ForeignKey(
        Inventario,
        on_delete=models.CASCADE,
        related_name="itens",
        verbose_name="Inventário",
    )
    item = models.ForeignKey(
        "cadastros.Item",
        on_delete=models.PROTECT,
        related_name="itens_inventario",
        verbose_name="Item",
    )
    localizacao = models.ForeignKey(
        Localizacao,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="itens_inventario",
        verbose_name="Localização",
    )
    saldo_sistema = models.DecimalField(max_digits=15, decimal_places=4, verbose_name="Saldo Sistema")
    saldo_contado = models.DecimalField(
        max_digits=15, decimal_places=4, null=True, blank=True, verbose_name="Saldo Contado"
    )
    divergencia = models.DecimalField(max_digits=15, decimal_places=4, default=0, verbose_name="Divergência")
    ajustado = models.BooleanField(default=False, verbose_name="Ajustado")

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Item de Inventário"
        verbose_name_plural = "Itens de Inventário"

    def __str__(self):
        return f"{self.inventario.nome} — {self.item}"

    def save(self, *args, **kwargs):
        if self.saldo_contado is not None:
            self.divergencia = self.saldo_contado - self.saldo_sistema
        super().save(*args, **kwargs)
