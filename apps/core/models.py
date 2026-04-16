"""
AbstractBaseModel — Fundação de todos os modelos do ERP.

Implementa:
- UUID como PK
- Multi-tenancy (empresa + filial)
- Soft-delete (deleted_at)
- Audit trail (criado_em/por, alterado_em/por)
- Versionamento
- Tags e observações
"""
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class SoftDeleteManager(models.Manager):
    """Manager padrão: exclui registros com deleted_at."""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class AllObjectsManager(models.Manager):
    """Manager que inclui deletados — para auditoria e restore."""

    def get_queryset(self):
        return super().get_queryset()


class AbstractBaseModel(models.Model):
    """
    Modelo base abstrato para TODAS as entidades do ERP.

    Campos fixos obrigatórios conforme especificação (seção 9 do documento):
    id, tenant_id (empresa), filial, status, ativo, criado_em, criado_por,
    alterado_em, alterado_por, versao, deleted_at, origem, tags, observacoes.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Multi-tenancy
    empresa = models.ForeignKey(
        "administracao.Empresa",
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name="Empresa",
        db_index=True,
    )
    filial = models.ForeignKey(
        "administracao.Filial",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="Filial",
    )

    # Status
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    # Audit trail
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="Criado por",
    )
    alterado_em = models.DateTimeField(auto_now=True, verbose_name="Alterado em")
    alterado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="Alterado por",
    )

    # Soft-delete
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="Excluído em")
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="Excluído por",
    )

    # Versionamento optimistic locking
    versao = models.PositiveIntegerField(default=1, verbose_name="Versão")

    # Metadados livres
    origem = models.CharField(max_length=100, blank=True, verbose_name="Origem")
    tags = models.CharField(max_length=500, blank=True, verbose_name="Tags")
    observacoes = models.TextField(blank=True, verbose_name="Observações")

    # Managers
    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True
        ordering = ["-criado_em"]

    def soft_delete(self, user=None):
        """Exclusão lógica — nunca física quando há vínculos operacionais."""
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.ativo = False
        self.save(update_fields=["deleted_at", "deleted_by", "ativo", "alterado_em"])

    def restore(self, user=None):
        """Restaura registro deletado logicamente."""
        self.deleted_at = None
        self.deleted_by = None
        self.ativo = True
        self.alterado_por = user
        self.save(update_fields=["deleted_at", "deleted_by", "ativo", "alterado_em", "alterado_por"])

    @property
    def deletado(self):
        return self.deleted_at is not None

    def save(self, *args, **kwargs):
        if self.pk:
            self.versao = models.F("versao") + 1
        super().save(*args, **kwargs)
        if isinstance(self.versao, models.expressions.CombinedExpression):
            self.refresh_from_db(fields=["versao"])
