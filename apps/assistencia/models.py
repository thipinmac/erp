import uuid

from django.conf import settings
from django.db import models

from apps.core.models import AbstractBaseModel


class Chamado(AbstractBaseModel):
    """Chamado de assistência técnica ou garantia."""

    TIPO_CHOICES = [
        ("garantia", "Garantia"),
        ("avulso", "Avulso"),
        ("manutencao", "Manutenção"),
    ]

    STATUS_CHOICES = [
        ("aberto", "Aberto"),
        ("triado", "Triado"),
        ("agendado", "Agendado"),
        ("em_atendimento", "Em Atendimento"),
        ("aguardando_peca", "Aguardando Peça"),
        ("encerrado", "Encerrado"),
    ]

    PRIORIDADE_CHOICES = [
        ("baixa", "Baixa"),
        ("media", "Média"),
        ("alta", "Alta"),
        ("urgente", "Urgente"),
    ]

    ORIGEM_CHOICES = [
        ("portal", "Portal"),
        ("interno", "Interno"),
        ("whatsapp", "WhatsApp"),
        ("telefone", "Telefone"),
        ("email", "E-mail"),
    ]

    numero = models.CharField(max_length=30, verbose_name="Número")
    contrato = models.ForeignKey(
        "contratos.Contrato",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chamados",
        verbose_name="Contrato",
    )
    pedido = models.ForeignKey(
        "pedidos.Pedido",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chamados_assistencia",
        verbose_name="Pedido",
    )
    cliente = models.ForeignKey(
        "cadastros.Cliente",
        on_delete=models.PROTECT,
        related_name="chamados",
        verbose_name="Cliente",
    )
    ambiente = models.CharField(max_length=100, blank=True, verbose_name="Ambiente")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo")
    descricao = models.TextField(verbose_name="Descrição")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="aberto",
        verbose_name="Status",
    )
    prioridade = models.CharField(
        max_length=10,
        choices=PRIORIDADE_CHOICES,
        default="media",
        verbose_name="Prioridade",
    )
    sla_horas = models.PositiveIntegerField(default=48, verbose_name="SLA (horas)")
    data_abertura = models.DateTimeField(auto_now_add=True, verbose_name="Data de abertura")
    data_limite_sla = models.DateTimeField(
        null=True, blank=True, verbose_name="Data limite SLA"
    )
    data_encerramento = models.DateTimeField(
        null=True, blank=True, verbose_name="Data de encerramento"
    )
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chamados_responsavel",
        verbose_name="Responsável",
    )
    cobertura_garantia = models.BooleanField(
        default=True, verbose_name="Cobertura de garantia"
    )
    origem = models.CharField(
        max_length=20,
        choices=ORIGEM_CHOICES,
        default="interno",
        verbose_name="Origem",
    )

    class Meta:
        verbose_name = "Chamado"
        verbose_name_plural = "Chamados"
        ordering = ["-data_abertura"]

    def __str__(self):
        return f"Chamado {self.numero} — {self.cliente} ({self.get_status_display()})"


class VisitaTecnica(models.Model):
    """Visita técnica vinculada a um chamado."""

    STATUS_CHOICES = [
        ("agendada", "Agendada"),
        ("realizada", "Realizada"),
        ("reagendada", "Reagendada"),
        ("cancelada", "Cancelada"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chamado = models.ForeignKey(
        Chamado,
        on_delete=models.CASCADE,
        related_name="visitas",
        verbose_name="Chamado",
    )
    data_prevista = models.DateField(verbose_name="Data prevista")
    data_realizada = models.DateTimeField(
        null=True, blank=True, verbose_name="Data realizada"
    )
    tecnico = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="visitas_tecnicas",
        verbose_name="Técnico",
    )
    diagnostico = models.TextField(blank=True, verbose_name="Diagnóstico")
    evidencias = models.JSONField(
        default=list,
        verbose_name="Evidências",
        help_text="URLs das fotos",
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default="agendada",
        verbose_name="Status",
    )

    class Meta:
        verbose_name = "Visita Técnica"
        verbose_name_plural = "Visitas Técnicas"
        ordering = ["data_prevista"]

    def __str__(self):
        return f"Visita {self.chamado.numero} — {self.data_prevista:%d/%m/%Y}"


class PecaReposicao(models.Model):
    """Peça de reposição solicitada para um chamado."""

    ORIGEM_CHOICES = [
        ("estoque", "Estoque"),
        ("compra", "Compra"),
        ("fabricacao", "Fabricação"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chamado = models.ForeignKey(
        Chamado,
        on_delete=models.CASCADE,
        related_name="pecas",
        verbose_name="Chamado",
    )
    item = models.ForeignKey(
        "cadastros.Item",
        on_delete=models.PROTECT,
        related_name="pecas_reposicao",
        verbose_name="Item",
    )
    quantidade = models.DecimalField(
        max_digits=10, decimal_places=4, verbose_name="Quantidade"
    )
    origem = models.CharField(
        max_length=15, choices=ORIGEM_CHOICES, verbose_name="Origem"
    )
    prazo_estimado = models.DateField(
        null=True, blank=True, verbose_name="Prazo estimado"
    )
    entregue = models.BooleanField(default=False, verbose_name="Entregue")

    class Meta:
        verbose_name = "Peça de Reposição"
        verbose_name_plural = "Peças de Reposição"

    def __str__(self):
        return f"{self.item} × {self.quantidade} ({self.chamado.numero})"


class EncerramentoChamado(models.Model):
    """Dados de encerramento e resolução de um chamado."""

    NPS_CHOICES = [(i, str(i)) for i in range(11)]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chamado = models.OneToOneField(
        Chamado,
        on_delete=models.CASCADE,
        related_name="encerramento",
        verbose_name="Chamado",
    )
    causa_raiz = models.TextField(verbose_name="Causa raiz")
    solucao = models.TextField(verbose_name="Solução")
    custo_total = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name="Custo total"
    )
    cobrado = models.BooleanField(default=False, verbose_name="Cobrado")
    valor_cobrado = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name="Valor cobrado"
    )
    nps = models.PositiveSmallIntegerField(
        null=True, blank=True, choices=NPS_CHOICES, verbose_name="NPS"
    )
    aceite_cliente = models.BooleanField(
        default=False, verbose_name="Aceite do cliente"
    )

    class Meta:
        verbose_name = "Encerramento de Chamado"
        verbose_name_plural = "Encerramentos de Chamados"

    def __str__(self):
        return f"Encerramento — {self.chamado.numero}"
