from django.conf import settings
from django.db import models

from apps.core.models import AbstractBaseModel


class RoteiroPadrao(AbstractBaseModel):
    """Roteiro de produção padrão para um tipo de módulo."""

    nome = models.CharField(max_length=100, verbose_name="Nome")
    tipo = models.CharField(
        max_length=50,
        verbose_name="Tipo",
        help_text="Tipo de módulo aplicável",
    )

    class Meta:
        verbose_name = "Roteiro Padrão"
        verbose_name_plural = "Roteiros Padrão"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} ({self.tipo})"


class EtapaRoteiro(models.Model):
    """Etapa de um roteiro de produção."""

    roteiro = models.ForeignKey(
        RoteiroPadrao,
        on_delete=models.CASCADE,
        related_name="etapas",
        verbose_name="Roteiro",
    )
    nome = models.CharField(max_length=100, verbose_name="Nome")
    ordem = models.PositiveSmallIntegerField(verbose_name="Ordem")
    recurso = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Recurso",
        help_text="Ex: CNC, Borda, Furadeira",
    )
    tempo_padrao_min = models.PositiveIntegerField(
        default=0, verbose_name="Tempo padrão (min)"
    )
    regras_transicao = models.JSONField(
        default=dict, verbose_name="Regras de transição"
    )
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = "Etapa do Roteiro"
        verbose_name_plural = "Etapas do Roteiro"
        ordering = ["roteiro", "ordem"]

    def __str__(self):
        return f"{self.roteiro.nome} › {self.ordem}. {self.nome}"


class OrdemProducao(AbstractBaseModel):
    """Ordem de Produção (OP)."""

    STATUS_CHOICES = [
        ("planejada", "Planejada"),
        ("liberada", "Liberada"),
        ("em_corte", "Em Corte"),
        ("em_borda", "Em Borda"),
        ("em_usinagem", "Em Usinagem"),
        ("em_acabamento", "Em Acabamento"),
        ("em_montagem", "Em Montagem"),
        ("em_embalagem", "Em Embalagem"),
        ("concluida", "Concluída"),
        ("cancelada", "Cancelada"),
    ]

    numero = models.CharField(max_length=30, verbose_name="Número")
    pedido = models.ForeignKey(
        "pedidos.Pedido",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ordens_producao",
        verbose_name="Pedido",
    )
    ambiente = models.CharField(max_length=100, blank=True, verbose_name="Ambiente")
    item = models.ForeignKey(
        "cadastros.Item",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ordens_producao",
        verbose_name="Item",
    )
    roteiro = models.ForeignKey(
        RoteiroPadrao,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ordens_producao",
        verbose_name="Roteiro",
    )
    prioridade = models.PositiveSmallIntegerField(
        default=5, verbose_name="Prioridade"
    )
    data_prevista_inicio = models.DateField(
        null=True, blank=True, verbose_name="Data prevista de início"
    )
    data_prevista_fim = models.DateField(
        null=True, blank=True, verbose_name="Data prevista de fim"
    )
    data_inicio_real = models.DateTimeField(
        null=True, blank=True, verbose_name="Data de início real"
    )
    data_fim_real = models.DateTimeField(
        null=True, blank=True, verbose_name="Data de fim real"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="planejada",
        verbose_name="Status",
    )
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ordens_producao",
        verbose_name="Responsável",
    )
    observacoes = models.TextField(blank=True, verbose_name="Observações")

    class Meta:
        verbose_name = "Ordem de Produção"
        verbose_name_plural = "Ordens de Produção"
        ordering = ["prioridade", "data_prevista_inicio"]

    def __str__(self):
        return f"OP {self.numero} — {self.get_status_display()}"


class LoteProducao(AbstractBaseModel):
    """Agrupamento de OPs em lote para execução conjunta."""

    STATUS_CHOICES = [
        ("aberto", "Aberto"),
        ("em_producao", "Em Produção"),
        ("concluido", "Concluído"),
        ("cancelado", "Cancelado"),
    ]

    numero = models.CharField(max_length=30, verbose_name="Número")
    ops = models.ManyToManyField(
        OrdemProducao,
        blank=True,
        related_name="lotes",
        verbose_name="Ordens de Produção",
    )
    objetivo = models.CharField(max_length=200, blank=True, verbose_name="Objetivo")
    capacidade = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Capacidade"
    )
    data_alvo = models.DateField(null=True, blank=True, verbose_name="Data alvo")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="aberto",
        verbose_name="Status",
    )

    class Meta:
        verbose_name = "Lote de Produção"
        verbose_name_plural = "Lotes de Produção"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"Lote {self.numero} — {self.get_status_display()}"


class ApontamentoProducao(models.Model):
    """Registro de apontamento de produção em uma etapa."""

    op = models.ForeignKey(
        OrdemProducao,
        on_delete=models.CASCADE,
        related_name="apontamentos",
        verbose_name="Ordem de Produção",
    )
    etapa = models.ForeignKey(
        EtapaRoteiro,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="apontamentos",
        verbose_name="Etapa",
    )
    operador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="apontamentos_producao",
        verbose_name="Operador",
    )
    maquina = models.CharField(max_length=100, blank=True, verbose_name="Máquina")
    inicio = models.DateTimeField(verbose_name="Início")
    fim = models.DateTimeField(null=True, blank=True, verbose_name="Fim")
    tempo_parada_min = models.PositiveIntegerField(
        default=0, verbose_name="Tempo de parada (min)"
    )
    motivo_parada = models.CharField(
        max_length=200, blank=True, verbose_name="Motivo da parada"
    )
    quantidade_produzida = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=0,
        verbose_name="Quantidade produzida",
    )
    observacao = models.TextField(blank=True, verbose_name="Observação")

    class Meta:
        verbose_name = "Apontamento de Produção"
        verbose_name_plural = "Apontamentos de Produção"
        ordering = ["-inicio"]

    def __str__(self):
        return f"Apontamento OP {self.op.numero} — {self.inicio:%d/%m/%Y %H:%M}"


class PecaFaltante(models.Model):
    """Registro de peça faltante, retrabalho ou não conformidade."""

    TIPO_CHOICES = [
        ("faltante", "Faltante"),
        ("retrabalho", "Retrabalho"),
        ("nao_conformidade", "Não Conformidade"),
    ]

    IMPACTO_CHOICES = [
        ("critico", "Crítico"),
        ("alto", "Alto"),
        ("medio", "Médio"),
        ("baixo", "Baixo"),
    ]

    op = models.ForeignKey(
        OrdemProducao,
        on_delete=models.CASCADE,
        related_name="pecas_faltantes",
        verbose_name="Ordem de Produção",
    )
    descricao = models.TextField(verbose_name="Descrição")
    tipo = models.CharField(
        max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo"
    )
    motivo = models.TextField(blank=True, verbose_name="Motivo")
    impacto = models.CharField(
        max_length=20, choices=IMPACTO_CHOICES, verbose_name="Impacto"
    )
    acao_corretiva = models.TextField(blank=True, verbose_name="Ação corretiva")
    prazo_resolucao = models.DateField(
        null=True, blank=True, verbose_name="Prazo de resolução"
    )
    resolvido = models.BooleanField(default=False, verbose_name="Resolvido")

    class Meta:
        verbose_name = "Peça Faltante / Não Conformidade"
        verbose_name_plural = "Peças Faltantes / Não Conformidades"
        ordering = ["-op__numero"]

    def __str__(self):
        return f"{self.get_tipo_display()} — OP {self.op.numero}"


class Volume(AbstractBaseModel):
    """Volume de embalagem de uma OP."""

    numero = models.CharField(max_length=30, verbose_name="Número")
    op = models.ForeignKey(
        OrdemProducao,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="volumes",
        verbose_name="Ordem de Produção",
    )
    pedido = models.ForeignKey(
        "pedidos.Pedido",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="volumes",
        verbose_name="Pedido",
    )
    tipo_embalagem = models.CharField(
        max_length=50, blank=True, verbose_name="Tipo de embalagem"
    )
    peso_kg = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Peso (kg)"
    )
    observacao = models.TextField(blank=True, verbose_name="Observação")
    conferido = models.BooleanField(default=False, verbose_name="Conferido")
    expedido = models.BooleanField(default=False, verbose_name="Expedido")
    codigo_barras = models.CharField(
        max_length=50, blank=True, verbose_name="Código de barras"
    )
    qr_code = models.ImageField(
        upload_to="producao/qr/",
        null=True,
        blank=True,
        verbose_name="QR Code",
    )

    class Meta:
        verbose_name = "Volume"
        verbose_name_plural = "Volumes"
        ordering = ["numero"]

    def __str__(self):
        return f"Volume {self.numero}"


class PecaVolume(models.Model):
    """Peça associada a um volume (M2M com informação extra)."""

    volume = models.ForeignKey(
        Volume,
        on_delete=models.CASCADE,
        related_name="pecas",
        verbose_name="Volume",
    )
    peca_descricao = models.CharField(
        max_length=255, verbose_name="Descrição da peça"
    )
    quantidade = models.DecimalField(
        max_digits=10, decimal_places=4, default=1, verbose_name="Quantidade"
    )

    class Meta:
        verbose_name = "Peça do Volume"
        verbose_name_plural = "Peças do Volume"

    def __str__(self):
        return f"{self.peca_descricao} × {self.quantidade} — {self.volume}"


class Romaneio(AbstractBaseModel):
    """Romaneio de expedição agrupando volumes."""

    STATUS_CHOICES = [
        ("aberto", "Aberto"),
        ("conferido", "Conferido"),
        ("expedido", "Expedido"),
        ("entregue", "Entregue"),
    ]

    numero = models.CharField(max_length=30, verbose_name="Número")
    volumes = models.ManyToManyField(
        Volume,
        blank=True,
        related_name="romaneios",
        verbose_name="Volumes",
    )
    pedido = models.ForeignKey(
        "pedidos.Pedido",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="romaneios",
        verbose_name="Pedido",
    )
    veiculo = models.CharField(max_length=100, blank=True, verbose_name="Veículo")
    motorista = models.CharField(max_length=100, blank=True, verbose_name="Motorista")
    conferente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="romaneios_conferidos",
        verbose_name="Conferente",
    )
    data_expedicao = models.DateField(
        null=True, blank=True, verbose_name="Data de expedição"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="aberto",
        verbose_name="Status",
    )
    observacoes = models.TextField(blank=True, verbose_name="Observações")

    class Meta:
        verbose_name = "Romaneio"
        verbose_name_plural = "Romaneios"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"Romaneio {self.numero} — {self.get_status_display()}"
