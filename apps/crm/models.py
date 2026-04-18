"""
Módulo 3 — CRM Comercial, Visitas, Funil e Atendimento.

Pipeline Kanban: Captação → Qualificação → Medição/Briefing →
  Orçamento em elaboração → Proposta enviada → Negociação →
  Aprovado → Perdido.
"""
from django.conf import settings
from django.db import models
from apps.core.models import AbstractBaseModel


class EtapaPipeline(models.Model):
    """Etapas configuráveis do pipeline comercial."""
    empresa = models.ForeignKey("administracao.Empresa", on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    ordem = models.PositiveSmallIntegerField(default=0)
    cor = models.CharField(max_length=7, default="#6366f1")
    wip_limite = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Limite WIP (0 = ilimitado)")
    probabilidade_padrao = models.PositiveSmallIntegerField(default=50, help_text="Probabilidade padrão %")
    etapa_final_ganho = models.BooleanField(default=False)
    etapa_final_perdido = models.BooleanField(default=False)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["empresa", "ordem"]
        unique_together = [("empresa", "ordem")]
        verbose_name = "Etapa do Pipeline"
        verbose_name_plural = "Etapas do Pipeline"

    def __str__(self):
        return self.nome


class Lead(AbstractBaseModel):
    """Lead/Prospect — primeiro contato antes de virar oportunidade."""

    class Status(models.TextChoices):
        NOVO = "novo", "Novo"
        QUALIFICADO = "qualificado", "Qualificado"
        DESCARTADO = "descartado", "Descartado"
        CONVERTIDO = "convertido", "Convertido"

    nome = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    whatsapp = models.CharField(max_length=20, blank=True)
    interesse = models.CharField(max_length=500, blank=True, help_text="Projeto/ambiente de interesse")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NOVO)
    score = models.PositiveSmallIntegerField(default=0, help_text="Score 0-100")
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="leads_responsavel",
    )

    # Origem do lead
    canal_origem = models.CharField(max_length=50, blank=True, choices=[
        ("instagram", "Instagram"),
        ("google", "Google Ads"),
        ("indicacao", "Indicação"),
        ("site", "Site"),
        ("whatsapp", "WhatsApp"),
        ("fachada", "Fachada"),
        ("outro", "Outro"),
    ])
    utm_source = models.CharField(max_length=100, blank=True)
    utm_medium = models.CharField(max_length=100, blank=True)
    utm_campaign = models.CharField(max_length=100, blank=True)

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Lead"
        verbose_name_plural = "Leads"

    def __str__(self):
        return self.nome


class Oportunidade(AbstractBaseModel):
    """Oportunidade comercial — unidade principal do pipeline."""

    lead = models.ForeignKey(
        Lead, null=True, blank=True, on_delete=models.SET_NULL, related_name="oportunidades"
    )
    cliente = models.ForeignKey(
        "cadastros.Cliente", null=True, blank=True, on_delete=models.SET_NULL, related_name="oportunidades"
    )
    titulo = models.CharField(max_length=255, verbose_name="Título / Projeto")
    etapa = models.ForeignKey(EtapaPipeline, on_delete=models.PROTECT, related_name="oportunidades")
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="oportunidades_responsavel",
    )

    # Valores
    valor_estimado = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    probabilidade = models.PositiveSmallIntegerField(default=50, help_text="% de conversão")
    valor_ponderado = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Datas
    data_previsao_fechamento = models.DateField(null=True, blank=True)
    data_entrada_etapa = models.DateTimeField(auto_now_add=True)
    data_ultima_atividade = models.DateTimeField(auto_now=True)

    # Motivo de perda
    motivo_perda = models.CharField(max_length=255, blank=True)
    concorrente_perdido = models.CharField(max_length=100, blank=True)

    # Projeto
    ambientes = models.TextField(blank=True, help_text="Ambientes de interesse (cozinha, dormitório, etc.)")
    metragem_estimada = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    prazo_cliente = models.DateField(null=True, blank=True, verbose_name="Prazo desejado pelo cliente")

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Oportunidade"
        verbose_name_plural = "Oportunidades"
        indexes = [
            models.Index(fields=["empresa", "etapa", "ativo"]),
            models.Index(fields=["empresa", "responsavel"]),
        ]

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        self.valor_ponderado = self.valor_estimado * (self.probabilidade / 100)
        super().save(*args, **kwargs)


class Visita(AbstractBaseModel):
    """Registro de visita/atendimento comercial."""

    class Tipo(models.TextChoices):
        PROSPECCAO = "prospeccao", "Prospecção"
        MEDICAO = "medicao", "Medição"
        APRESENTACAO = "apresentacao", "Apresentação"
        REUNIAO = "reuniao", "Reunião"
        RETORNO = "retorno", "Retorno"
        OUTRO = "outro", "Outro"

    oportunidade = models.ForeignKey(
        Oportunidade, on_delete=models.CASCADE, related_name="visitas", null=True, blank=True
    )
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="visitas", null=True, blank=True)
    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.PROSPECCAO)
    data_hora = models.DateTimeField()
    local = models.CharField(max_length=255, blank=True, help_text="Loja, obra ou endereço")
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="visitas"
    )
    resumo = models.TextField(blank=True)
    proximos_passos = models.TextField(blank=True)
    realizada = models.BooleanField(default=False)

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Visita / Atendimento"
        verbose_name_plural = "Visitas / Atendimentos"
        ordering = ["-data_hora"]

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.data_hora:%d/%m/%Y %H:%M}"


class TarefaComercial(AbstractBaseModel):
    """Tarefas de follow-up e atividades comerciais."""

    class Tipo(models.TextChoices):
        LIGAR = "ligar", "Ligar"
        EMAIL = "email", "Enviar e-mail"
        WHATSAPP = "whatsapp", "Enviar WhatsApp"
        VISITA = "visita", "Agendar visita"
        PROPOSTA = "proposta", "Enviar proposta"
        FOLLOW_UP = "follow_up", "Follow-up"
        OUTRO = "outro", "Outro"

    class Prioridade(models.TextChoices):
        BAIXA = "baixa", "Baixa"
        MEDIA = "media", "Média"
        ALTA = "alta", "Alta"
        URGENTE = "urgente", "Urgente"

    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    titulo = models.CharField(max_length=255)
    oportunidade = models.ForeignKey(
        Oportunidade, on_delete=models.CASCADE, null=True, blank=True, related_name="tarefas"
    )
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, null=True, blank=True, related_name="tarefas")
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="tarefas_comerciais"
    )
    data_vencimento = models.DateTimeField()
    prioridade = models.CharField(max_length=10, choices=Prioridade.choices, default=Prioridade.MEDIA)
    concluida = models.BooleanField(default=False)
    data_conclusao = models.DateTimeField(null=True, blank=True)
    resultado = models.TextField(blank=True)

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Tarefa Comercial"
        verbose_name_plural = "Tarefas Comerciais"
        ordering = ["data_vencimento"]

    def __str__(self):
        return self.titulo


class MetaComercial(AbstractBaseModel):
    """Metas comerciais por vendedor/equipe/período."""

    class Periodo(models.TextChoices):
        MENSAL = "mensal", "Mensal"
        TRIMESTRAL = "trimestral", "Trimestral"
        SEMESTRAL = "semestral", "Semestral"
        ANUAL = "anual", "Anual"

    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name="metas"
    )
    equipe = models.CharField(max_length=100, blank=True)
    periodo = models.CharField(max_length=15, choices=Periodo.choices)
    ano = models.PositiveSmallIntegerField()
    mes = models.PositiveSmallIntegerField(null=True, blank=True)
    valor_meta = models.DecimalField(max_digits=15, decimal_places=2)
    qtd_oportunidades_meta = models.PositiveIntegerField(null=True, blank=True)
    taxa_conversao_meta = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Meta Comercial"
        verbose_name_plural = "Metas Comerciais"

    def __str__(self):
        return f"{self.responsavel or self.equipe} — {self.ano}/{self.mes or ''}"


class HistoricoOportunidade(models.Model):
    """Histórico de movimentação das oportunidades no pipeline."""
    oportunidade = models.ForeignKey(Oportunidade, on_delete=models.CASCADE, related_name="historico")
    etapa_anterior = models.ForeignKey(EtapaPipeline, on_delete=models.SET_NULL, null=True, related_name="+")
    etapa_nova = models.ForeignKey(EtapaPipeline, on_delete=models.SET_NULL, null=True, related_name="+")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    data = models.DateTimeField(auto_now_add=True)
    observacao = models.TextField(blank=True)

    class Meta:
        ordering = ["-data"]

    def __str__(self):
        return f"{self.oportunidade} | {self.etapa_anterior} → {self.etapa_nova}"
