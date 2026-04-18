"""Módulo BI / Dashboards — modelos."""
import uuid
from django.db import models


class Painel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey("administracao.Empresa", on_delete=models.CASCADE, related_name="+")
    criado_em = models.DateTimeField(auto_now_add=True)
    alterado_em = models.DateTimeField(auto_now=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Painel"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"Painel {self.pk}"


class KPICache(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey("administracao.Empresa", on_delete=models.CASCADE, related_name="+")
    criado_em = models.DateTimeField(auto_now_add=True)
    alterado_em = models.DateTimeField(auto_now=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "KPICache"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"KPICache {self.pk}"

