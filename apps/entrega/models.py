from django.conf import settings
from django.db import models

from apps.core.models import AbstractBaseModel


class EquipeCampo(AbstractBaseModel):
    """Equipe de campo para entrega e instalação."""

    nome = models.CharField(max_length=100, verbose_name="Nome")
    membros = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="equipes_campo",
        verbose_name="Membros",
    )
    veiculo = models.CharField(max_length=100, blank=True, verbose_name="Veículo")

    class Meta:
        verbose_name = "Equipe de Campo"
        verbose_name_plural = "Equipes de Campo"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class AgendaAtendimento(AbstractBaseModel):
    """Agendamento de atendimento de campo (entrega, montagem, vistoria)."""

    TIPO_CHOICES = [
        ("entrega", "Entrega"),
        ("montagem", "Montagem"),
        ("vistoria", "Vistoria"),
        ("reentrega", "Reentrega"),
    ]

    STATUS_CHOICES = [
        ("agendando", "Agendando"),
        ("confirmado", "Confirmado"),
        ("em_rota", "Em Rota"),
        ("em_atendimento", "Em Atendimento"),
        ("aceite", "Aceite"),
        ("pendencia", "Pendência"),
        ("concluido", "Concluído"),
        ("cancelado", "Cancelado"),
    ]

    tipo = models.CharField(
        max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo"
    )
    pedido = models.ForeignKey(
        "pedidos.Pedido",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agendamentos",
        verbose_name="Pedido",
    )
    romaneio = models.ForeignKey(
        "producao.Romaneio",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agendamentos",
        verbose_name="Romaneio",
    )
    equipe = models.ForeignKey(
        EquipeCampo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agendamentos",
        verbose_name="Equipe",
    )
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agendamentos_responsavel",
        verbose_name="Responsável",
    )
    data_prevista = models.DateField(verbose_name="Data prevista")
    janela_inicio = models.TimeField(null=True, blank=True, verbose_name="Janela início")
    janela_fim = models.TimeField(null=True, blank=True, verbose_name="Janela fim")
    endereco = models.TextField(blank=True, verbose_name="Endereço")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="agendando",
        verbose_name="Status",
    )
    observacoes = models.TextField(blank=True, verbose_name="Observações")

    class Meta:
        verbose_name = "Agenda de Atendimento"
        verbose_name_plural = "Agendas de Atendimento"
        ordering = ["data_prevista", "janela_inicio"]

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.data_prevista:%d/%m/%Y} ({self.get_status_display()})"


class ChecklistInstalacao(models.Model):
    """Item de checklist de instalação vinculado a um atendimento."""

    STATUS_CHOICES = [
        ("ok", "OK"),
        ("nok", "NOK"),
        ("pendente", "Pendente"),
    ]

    agenda = models.ForeignKey(
        AgendaAtendimento,
        on_delete=models.CASCADE,
        related_name="checklist",
        verbose_name="Agenda",
    )
    item_verificacao = models.CharField(
        max_length=255, verbose_name="Item de verificação"
    )
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="pendente", verbose_name="Status"
    )
    evidencia = models.ImageField(
        upload_to="entrega/checklist/",
        null=True,
        blank=True,
        verbose_name="Evidência",
    )
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="checklists_instalacao",
        verbose_name="Responsável",
    )
    observacao = models.CharField(max_length=500, blank=True, verbose_name="Observação")

    class Meta:
        verbose_name = "Checklist de Instalação"
        verbose_name_plural = "Checklists de Instalação"

    def __str__(self):
        return f"{self.item_verificacao} — {self.get_status_display()}"


class OcorrenciaCampo(models.Model):
    """Ocorrência registrada durante atendimento de campo."""

    TIPO_CHOICES = [
        ("dano", "Dano"),
        ("atraso", "Atraso"),
        ("acesso_negado", "Acesso negado"),
        ("peca_faltante", "Peça faltante"),
        ("outro", "Outro"),
    ]

    IMPACTO_CHOICES = [
        ("critico", "Crítico"),
        ("alto", "Alto"),
        ("medio", "Médio"),
        ("baixo", "Baixo"),
    ]

    agenda = models.ForeignKey(
        AgendaAtendimento,
        on_delete=models.CASCADE,
        related_name="ocorrencias",
        verbose_name="Agenda",
    )
    tipo = models.CharField(
        max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo"
    )
    descricao = models.TextField(verbose_name="Descrição")
    impacto = models.CharField(
        max_length=20, choices=IMPACTO_CHOICES, verbose_name="Impacto"
    )
    encaminhamento = models.TextField(blank=True, verbose_name="Encaminhamento")
    foto = models.ImageField(
        upload_to="entrega/ocorrencias/",
        null=True,
        blank=True,
        verbose_name="Foto",
    )

    class Meta:
        verbose_name = "Ocorrência de Campo"
        verbose_name_plural = "Ocorrências de Campo"

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.agenda}"


class Aceite(models.Model):
    """Aceite / assinatura do cliente no encerramento do atendimento."""

    NPS_CHOICES = [(i, str(i)) for i in range(11)]

    CONCLUSAO_CHOICES = [
        ("total", "Total"),
        ("parcial", "Parcial"),
    ]

    agenda = models.OneToOneField(
        AgendaAtendimento,
        on_delete=models.CASCADE,
        related_name="aceite",
        verbose_name="Agenda",
    )
    data_aceite = models.DateTimeField(verbose_name="Data do aceite")
    assinante_nome = models.CharField(max_length=200, verbose_name="Nome do assinante")
    assinante_doc = models.CharField(
        max_length=30, blank=True, verbose_name="Documento do assinante"
    )
    foto_assinatura = models.ImageField(
        upload_to="entrega/aceites/",
        null=True,
        blank=True,
        verbose_name="Foto da assinatura",
    )
    conclusao = models.CharField(
        max_length=10, choices=CONCLUSAO_CHOICES, verbose_name="Conclusão"
    )
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    nps = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        choices=NPS_CHOICES,
        verbose_name="NPS",
    )

    class Meta:
        verbose_name = "Aceite"
        verbose_name_plural = "Aceites"

    def __str__(self):
        return f"Aceite de {self.assinante_nome} — {self.agenda}"
