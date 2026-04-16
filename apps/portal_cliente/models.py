import uuid

from django.db import models


class MensagemPortal(models.Model):
    """Mensagem trocada entre cliente e equipe interna via portal."""

    ORIGEM_CHOICES = [
        ("cliente", "Cliente"),
        ("interno", "Interno"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(
        "administracao.Empresa",
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name="Empresa",
    )
    contrato = models.ForeignKey(
        "contratos.Contrato",
        on_delete=models.CASCADE,
        related_name="mensagens_portal",
        verbose_name="Contrato",
    )
    origem = models.CharField(
        max_length=10, choices=ORIGEM_CHOICES, verbose_name="Origem"
    )
    assunto = models.CharField(max_length=200, verbose_name="Assunto")
    corpo = models.TextField(verbose_name="Corpo")
    lida = models.BooleanField(default=False, verbose_name="Lida")
    data_leitura = models.DateTimeField(
        null=True, blank=True, verbose_name="Data de leitura"
    )
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")

    class Meta:
        verbose_name = "Mensagem do Portal"
        verbose_name_plural = "Mensagens do Portal"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"[{self.get_origem_display()}] {self.assunto}"


class FeedbackNPS(models.Model):
    """Registro de NPS coletado pelo portal do cliente."""

    NPS_CHOICES = [(i, str(i)) for i in range(11)]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(
        "administracao.Empresa",
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name="Empresa",
    )
    contrato = models.ForeignKey(
        "contratos.Contrato",
        on_delete=models.CASCADE,
        related_name="feedbacks_nps",
        verbose_name="Contrato",
    )
    nota = models.PositiveSmallIntegerField(
        choices=NPS_CHOICES, verbose_name="Nota NPS"
    )
    comentario = models.TextField(blank=True, verbose_name="Comentário")
    etapa = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Etapa",
        help_text="Ex: entrega, montagem",
    )
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")

    class Meta:
        verbose_name = "Feedback NPS"
        verbose_name_plural = "Feedbacks NPS"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"NPS {self.nota} — {self.contrato}"
