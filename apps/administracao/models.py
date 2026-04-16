"""
Módulo 1 — Administração, Segurança, Multiempresa e Parâmetros Gerais.

Entidades:
- Empresa (tenant raiz)
- Filial
- Usuario (AUTH_USER_MODEL customizado)
- Perfil / Permissao granular
- Calendario / SLA
- AuditLog
"""
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


# ─── Empresa ─────────────────────────────────────────────────────────────────

class Empresa(models.Model):
    """Tenant raiz. Todos os dados são segregados por empresa."""

    class RegimeTributario(models.TextChoices):
        SIMPLES = "SN", "Simples Nacional"
        PRESUMIDO = "LP", "Lucro Presumido"
        REAL = "LR", "Lucro Real"
        MEI = "MEI", "MEI"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    razao_social = models.CharField(max_length=255, verbose_name="Razão Social")
    nome_fantasia = models.CharField(max_length=255, blank=True, verbose_name="Nome Fantasia")
    cnpj = models.CharField(max_length=18, unique=True, verbose_name="CNPJ")
    ie = models.CharField(max_length=30, blank=True, verbose_name="Inscrição Estadual")
    im = models.CharField(max_length=30, blank=True, verbose_name="Inscrição Municipal")
    regime_tributario = models.CharField(
        max_length=10,
        choices=RegimeTributario.choices,
        default=RegimeTributario.SIMPLES,
        verbose_name="Regime Tributário",
    )

    # Endereço
    cep = models.CharField(max_length=9, blank=True)
    logradouro = models.CharField(max_length=255, blank=True)
    numero = models.CharField(max_length=20, blank=True)
    complemento = models.CharField(max_length=100, blank=True)
    bairro = models.CharField(max_length=100, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    uf = models.CharField(max_length=2, blank=True)

    # Contato
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    site = models.URLField(blank=True)

    # Branding
    logo = models.ImageField(upload_to="empresas/logos/", null=True, blank=True)
    cor_primaria = models.CharField(max_length=7, default="#1e3a5f", verbose_name="Cor primária")
    cor_secundaria = models.CharField(max_length=7, default="#f97316", verbose_name="Cor secundária")

    # Status
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    alterado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ["razao_social"]

    def __str__(self):
        return self.nome_fantasia or self.razao_social


# ─── Filial ──────────────────────────────────────────────────────────────────

class Filial(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="filiais")
    codigo = models.CharField(max_length=20, verbose_name="Código")
    nome = models.CharField(max_length=255, verbose_name="Nome")
    cnpj = models.CharField(max_length=18, blank=True, verbose_name="CNPJ da Filial")

    # Endereço
    cep = models.CharField(max_length=9, blank=True)
    logradouro = models.CharField(max_length=255, blank=True)
    numero = models.CharField(max_length=20, blank=True)
    complemento = models.CharField(max_length=100, blank=True)
    bairro = models.CharField(max_length=100, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    uf = models.CharField(max_length=2, blank=True)

    responsavel = models.CharField(max_length=255, blank=True)
    telefone = models.CharField(max_length=20, blank=True)

    # Parâmetros operacionais
    horario_abertura = models.TimeField(null=True, blank=True)
    horario_fechamento = models.TimeField(null=True, blank=True)
    fuso_horario = models.CharField(max_length=50, default="America/Sao_Paulo")

    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Filial"
        verbose_name_plural = "Filiais"
        unique_together = [("empresa", "codigo")]
        ordering = ["empresa", "nome"]

    def __str__(self):
        return f"{self.empresa} — {self.nome}"


# ─── Usuário ─────────────────────────────────────────────────────────────────

class Usuario(AbstractUser):
    """
    Usuário customizado do ERP.
    Estende AbstractUser para manter compatibilidade com Django auth.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Vinculação ao tenant
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="usuarios",
        verbose_name="Empresa principal",
    )
    filiais_autorizadas = models.ManyToManyField(
        Filial,
        blank=True,
        verbose_name="Filiais autorizadas",
    )

    # Dados profissionais
    cargo = models.CharField(max_length=100, blank=True)
    equipe = models.CharField(max_length=100, blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    foto = models.ImageField(upload_to="usuarios/fotos/", null=True, blank=True)

    # Perfil de acesso
    perfil = models.ForeignKey(
        "Perfil",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="usuarios",
        verbose_name="Perfil de acesso",
    )

    # Preferências
    tema = models.CharField(max_length=20, default="light", choices=[("light", "Claro"), ("dark", "Escuro")])

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def nome_exibicao(self):
        return self.get_full_name() or self.username


# ─── Perfil e Permissões ─────────────────────────────────────────────────────

class Perfil(models.Model):
    """Perfil de acesso — agrupa permissões por papel."""

    class Papel(models.TextChoices):
        ADMIN = "admin", "Administrador"
        GERENTE = "gerente", "Gerente"
        VENDEDOR = "vendedor", "Vendedor"
        ENGENHEIRO = "engenheiro", "Engenheiro"
        PRODUCAO = "producao", "Produção"
        FINANCEIRO = "financeiro", "Financeiro"
        ASSISTENCIA = "assistencia", "Assistência Técnica"
        VISUALIZADOR = "visualizador", "Visualizador"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="perfis")
    nome = models.CharField(max_length=100)
    papel = models.CharField(max_length=30, choices=Papel.choices)
    descricao = models.TextField(blank=True)

    # Permissões por módulo (JSON: {"crm": ["view", "add", "change"], "orcamentos": ["view"]})
    permissoes_modulos = models.JSONField(default=dict, verbose_name="Permissões por módulo")

    # Restrições
    pode_ver_custos = models.BooleanField(default=True)
    pode_ver_margem = models.BooleanField(default=True)
    pode_dar_desconto = models.BooleanField(default=False)
    limite_desconto_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    pode_aprovar_orcamento = models.BooleanField(default=False)
    pode_emitir_nfe = models.BooleanField(default=False)

    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Perfil de Acesso"
        verbose_name_plural = "Perfis de Acesso"
        unique_together = [("empresa", "nome")]

    def __str__(self):
        return f"{self.nome} ({self.get_papel_display()})"


# ─── Calendário e SLA ────────────────────────────────────────────────────────

class Calendario(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="calendarios")
    filial = models.ForeignKey(Filial, on_delete=models.CASCADE, null=True, blank=True)
    nome = models.CharField(max_length=100)
    turno_inicio = models.TimeField()
    turno_fim = models.TimeField()
    dias_semana = models.CharField(max_length=20, default="1,2,3,4,5")  # 1=seg, 7=dom
    horas_dia = models.DecimalField(max_digits=4, decimal_places=2, default=8)

    class Meta:
        verbose_name = "Calendário"
        verbose_name_plural = "Calendários"

    def __str__(self):
        return f"{self.nome} — {self.empresa}"


class Feriado(models.Model):
    calendario = models.ForeignKey(Calendario, on_delete=models.CASCADE, related_name="feriados")
    data = models.DateField()
    descricao = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=[
        ("nacional", "Nacional"),
        ("estadual", "Estadual"),
        ("municipal", "Municipal"),
        ("interno", "Interno"),
    ])

    class Meta:
        ordering = ["data"]

    def __str__(self):
        return f"{self.data} — {self.descricao}"


# ─── Audit Log ───────────────────────────────────────────────────────────────

class AuditLog(models.Model):
    """Trilha de auditoria completa para todas as ações críticas."""

    class Acao(models.TextChoices):
        CRIAR = "criar", "Criar"
        EDITAR = "editar", "Editar"
        EXCLUIR = "excluir", "Excluir (lógico)"
        RESTAURAR = "restaurar", "Restaurar"
        APROVAR = "aprovar", "Aprovar"
        CANCELAR = "cancelar", "Cancelar"
        LOGIN = "login", "Login"
        LOGOUT = "logout", "Logout"
        EXPORTAR = "exportar", "Exportar"
        IMPRIMIR = "imprimir", "Imprimir"
        VISUALIZAR = "visualizar", "Visualizar"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, null=True, blank=True)
    usuario = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs"
    )
    acao = models.CharField(max_length=30, choices=Acao.choices)
    modelo = models.CharField(max_length=100)
    objeto_id = models.CharField(max_length=36, blank=True)
    objeto_str = models.CharField(max_length=500, blank=True)
    dados_anteriores = models.JSONField(null=True, blank=True)
    dados_novos = models.JSONField(null=True, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Log de Auditoria"
        verbose_name_plural = "Logs de Auditoria"
        ordering = ["-criado_em"]
        indexes = [
            models.Index(fields=["empresa", "modelo", "objeto_id"]),
            models.Index(fields=["usuario", "criado_em"]),
        ]

    def __str__(self):
        return f"{self.criado_em} | {self.usuario} | {self.acao} | {self.modelo}"
