"""Módulo Comunicação — modelos."""
import uuid
from django.db import models
from django.conf import settings


class TemplateMensagem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey("administracao.Empresa", on_delete=models.CASCADE, related_name="+")
    criado_em = models.DateTimeField(auto_now_add=True)
    alterado_em = models.DateTimeField(auto_now=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "TemplateMensagem"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"TemplateMensagem {self.pk}"


class FilaEnvio(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey("administracao.Empresa", on_delete=models.CASCADE, related_name="+")
    criado_em = models.DateTimeField(auto_now_add=True)
    alterado_em = models.DateTimeField(auto_now=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "FilaEnvio"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"FilaEnvio {self.pk}"


class Conversa(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey("administracao.Empresa", on_delete=models.CASCADE, related_name="+")
    criado_em = models.DateTimeField(auto_now_add=True)
    alterado_em = models.DateTimeField(auto_now=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Conversa"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"Conversa {self.pk}"


class MensagemConversa(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey("administracao.Empresa", on_delete=models.CASCADE, related_name="+")
    criado_em = models.DateTimeField(auto_now_add=True)
    alterado_em = models.DateTimeField(auto_now=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "MensagemConversa"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"MensagemConversa {self.pk}"


class AssinaturaDigital(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey("administracao.Empresa", on_delete=models.CASCADE, related_name="+")
    criado_em = models.DateTimeField(auto_now_add=True)
    alterado_em = models.DateTimeField(auto_now=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "AssinaturaDigital"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"AssinaturaDigital {self.pk}"

