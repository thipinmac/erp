import uuid

from django.db import models

from apps.core.models import AbstractBaseModel


class ParametroFiscal(models.Model):
    """Configurações fiscais da empresa (séries, certificado, ambiente)."""

    AMBIENTE_CHOICES = [
        ("producao", "Produção"),
        ("homologacao", "Homologação"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.OneToOneField(
        "administracao.Empresa",
        on_delete=models.CASCADE,
        related_name="parametro_fiscal",
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
    serie_nfe = models.CharField(max_length=5, default="1", verbose_name="Série NF-e")
    serie_nfse = models.CharField(max_length=5, default="1", verbose_name="Série NFS-e")
    serie_nfce = models.CharField(max_length=5, default="1", verbose_name="Série NFC-e")
    ambiente = models.CharField(
        max_length=15,
        choices=AMBIENTE_CHOICES,
        default="homologacao",
        verbose_name="Ambiente",
    )
    regime_tributario = models.CharField(
        max_length=10, verbose_name="Regime tributário"
    )
    certificado_a1 = models.FileField(
        upload_to="fiscal/certs/",
        null=True,
        blank=True,
        verbose_name="Certificado A1",
    )
    certificado_senha = models.CharField(
        max_length=200, blank=True, verbose_name="Senha do certificado"
    )
    provedor_nfe = models.CharField(
        max_length=100, blank=True, verbose_name="Provedor NF-e"
    )
    provedor_nfse = models.CharField(
        max_length=100, blank=True, verbose_name="Provedor NFS-e"
    )
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = "Parâmetro Fiscal"
        verbose_name_plural = "Parâmetros Fiscais"

    def __str__(self):
        return f"Parâmetros Fiscais — {self.empresa} ({self.get_ambiente_display()})"


class DocumentoFiscal(AbstractBaseModel):
    """Documento fiscal eletrônico (NF-e, NFS-e, NFC-e, CT-e, MDF-e)."""

    TIPO_CHOICES = [
        ("nfe", "NF-e"),
        ("nfse", "NFS-e"),
        ("nfce", "NFC-e"),
        ("cte", "CT-e"),
        ("mdfe", "MDF-e"),
    ]

    STATUS_CHOICES = [
        ("em_preparacao", "Em preparação"),
        ("em_transmissao", "Em transmissão"),
        ("autorizado", "Autorizado"),
        ("rejeitado", "Rejeitado"),
        ("cancelado", "Cancelado"),
        ("inutilizado", "Inutilizado"),
    ]

    tipo = models.CharField(max_length=5, choices=TIPO_CHOICES, verbose_name="Tipo")
    numero = models.CharField(max_length=20, verbose_name="Número")
    serie = models.CharField(max_length=5, verbose_name="Série")
    chave = models.CharField(max_length=44, blank=True, verbose_name="Chave de acesso")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="em_preparacao",
        verbose_name="Status",
    )
    xml_envio = models.TextField(blank=True, verbose_name="XML de envio")
    xml_retorno = models.TextField(blank=True, verbose_name="XML de retorno")
    pdf = models.FileField(
        upload_to="fiscal/docs/", null=True, blank=True, verbose_name="PDF (DANFE)"
    )
    protocolo = models.CharField(max_length=30, blank=True, verbose_name="Protocolo")
    data_autorizacao = models.DateTimeField(
        null=True, blank=True, verbose_name="Data de autorização"
    )
    pedido = models.ForeignKey(
        "pedidos.Pedido",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documentos_fiscais",
        verbose_name="Pedido",
    )
    assistencia = models.ForeignKey(
        "assistencia.Chamado",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documentos_fiscais",
        verbose_name="Chamado assistência",
    )
    mensagem_rejeicao = models.TextField(
        blank=True, verbose_name="Mensagem de rejeição"
    )
    tentativas = models.PositiveSmallIntegerField(
        default=0, verbose_name="Tentativas"
    )

    class Meta:
        verbose_name = "Documento Fiscal"
        verbose_name_plural = "Documentos Fiscais"
        ordering = ["-criado_em"]
        unique_together = [("empresa", "tipo", "serie", "numero")]

    def __str__(self):
        return f"{self.get_tipo_display()} {self.serie}/{self.numero} — {self.get_status_display()}"


class EventoFiscal(models.Model):
    """Evento vinculado a um documento fiscal (cancelamento, CCe, etc.)."""

    TIPO_CHOICES = [
        ("cancelamento", "Cancelamento"),
        ("cce", "Carta de Correção"),
        ("inutilizacao", "Inutilização"),
        ("contingencia", "Contingência"),
    ]

    STATUS_CHOICES = [
        ("pendente", "Pendente"),
        ("autorizado", "Autorizado"),
        ("rejeitado", "Rejeitado"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    documento = models.ForeignKey(
        DocumentoFiscal,
        on_delete=models.CASCADE,
        related_name="eventos",
        verbose_name="Documento",
    )
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES, verbose_name="Tipo")
    protocolo = models.CharField(max_length=30, blank=True, verbose_name="Protocolo")
    justificativa = models.TextField(blank=True, verbose_name="Justificativa")
    xml_evento = models.TextField(blank=True, verbose_name="XML do evento")
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="pendente",
        verbose_name="Status",
    )
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")

    class Meta:
        verbose_name = "Evento Fiscal"
        verbose_name_plural = "Eventos Fiscais"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.documento} ({self.get_status_display()})"
