"""
Módulo Engenharia e Projetos — Importação, análise e liberação de projetos técnicos.

Fluxo: Importação de arquivo (Promob/3Cad/etc) → Análise de peças e BOM →
  Plano de corte → Resolução de divergências → Liberação para PCP.
"""
from django.conf import settings
from django.db import models

from apps.core.models import AbstractBaseModel


class ProjetoTecnico(AbstractBaseModel):
    """Projeto técnico importado de software CAD/CAM."""

    class FormatoOrigem(models.TextChoices):
        PROMOB = "promob", "Promob"
        TRESCAD = "3cad", "3Cad"
        VINTE_VINTE = "2020", "2020 Design"
        TOPSOLID = "topsolid", "TopSolid"
        XML = "xml", "XML Genérico"
        MANUAL = "manual", "Lançamento Manual"

    class Status(models.TextChoices):
        IMPORTADO = "importado", "Importado"
        EM_ANALISE = "em_analise", "Em Análise"
        DIVERGENCIA = "divergencia", "Com Divergência"
        AGUARDANDO_AJUSTE = "aguardando_ajuste", "Aguardando Ajuste"
        VALIDADO = "validado", "Validado"
        LIBERADO = "liberado", "Liberado para PCP"

    numero = models.CharField(max_length=30, verbose_name="Número do Projeto")
    pedido = models.ForeignKey(
        "pedidos.Pedido",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projetos_tecnicos",
        verbose_name="Pedido",
    )
    oportunidade = models.ForeignKey(
        "crm.Oportunidade",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projetos_tecnicos",
        verbose_name="Oportunidade",
    )
    arquivo_importado = models.FileField(
        upload_to="engenharia/projetos/",
        blank=True,
        verbose_name="Arquivo Importado",
    )
    formato_origem = models.CharField(
        max_length=20,
        choices=FormatoOrigem.choices,
        default=FormatoOrigem.MANUAL,
        verbose_name="Formato de Origem",
    )
    versao_projeto = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="Versão do Projeto",
    )
    responsavel_tecnico = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projetos_tecnicos",
        verbose_name="Responsável Técnico",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IMPORTADO,
        verbose_name="Status",
    )
    observacoes = models.TextField(blank=True, verbose_name="Observações")

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Projeto Técnico"
        verbose_name_plural = "Projetos Técnicos"
        indexes = [
            models.Index(fields=["empresa", "status"]),
            models.Index(fields=["numero"]),
        ]

    def __str__(self):
        return f"{self.numero} — v{self.versao_projeto} [{self.get_status_display()}]"


class AmbienteProjeto(AbstractBaseModel):
    """Ambiente dentro de um projeto técnico (cozinha, dormitório, etc.)."""

    class Prioridade(models.TextChoices):
        BAIXA = "baixa", "Baixa"
        MEDIA = "media", "Média"
        ALTA = "alta", "Alta"

    projeto = models.ForeignKey(
        ProjetoTecnico,
        on_delete=models.CASCADE,
        related_name="ambientes",
        verbose_name="Projeto",
    )
    nome = models.CharField(max_length=200, verbose_name="Nome do Ambiente")
    local = models.CharField(max_length=100, verbose_name="Local / Cômodo")
    ordem = models.PositiveSmallIntegerField(default=0, verbose_name="Ordem")
    prioridade = models.CharField(
        max_length=10,
        choices=Prioridade.choices,
        default=Prioridade.MEDIA,
        verbose_name="Prioridade",
    )
    restricoes = models.TextField(blank=True, verbose_name="Restrições Técnicas")

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Ambiente do Projeto"
        verbose_name_plural = "Ambientes do Projeto"
        ordering = ["projeto", "ordem"]

    def __str__(self):
        return f"{self.projeto.numero} — {self.nome}"


class PecaComponente(AbstractBaseModel):
    """Peça ou componente dentro de um ambiente do projeto."""

    ambiente = models.ForeignKey(
        AmbienteProjeto,
        on_delete=models.CASCADE,
        related_name="pecas",
        verbose_name="Ambiente",
    )
    codigo = models.CharField(max_length=50, verbose_name="Código")
    descricao = models.CharField(max_length=255, verbose_name="Descrição")

    # Dimensões
    largura_mm = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Largura (mm)")
    altura_mm = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Altura (mm)")
    profundidade_mm = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Profundidade (mm)")
    espessura_mm = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Espessura (mm)")

    # Material e acabamento
    material = models.ForeignKey(
        "cadastros.Item",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pecas_material",
        verbose_name="Material",
    )
    acabamento = models.CharField(max_length=100, blank=True, verbose_name="Acabamento")
    cor = models.CharField(max_length=100, blank=True, verbose_name="Cor")
    bordas_json = models.JSONField(
        default=dict,
        blank=True,
        help_text='ex: {"topo": "fita_A", "baixo": "fita_B"}',
        verbose_name="Bordas (JSON)",
    )

    # Operações
    usinagem = models.TextField(blank=True, verbose_name="Usinagem / CNC")
    ferragens = models.ManyToManyField(
        "cadastros.Item",
        blank=True,
        related_name="peca_ferragens",
        verbose_name="Ferragens",
    )

    quantidade = models.DecimalField(max_digits=10, decimal_places=4, default=1, verbose_name="Quantidade")
    peso_kg = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, verbose_name="Peso (kg)")
    observacao_fabrica = models.TextField(blank=True, verbose_name="Observação para Fábrica")

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Peça / Componente"
        verbose_name_plural = "Peças / Componentes"
        ordering = ["ambiente", "codigo"]

    def __str__(self):
        return f"{self.codigo} — {self.descricao}"


class BOM(AbstractBaseModel):
    """Bill of Materials — lista de materiais consolidada do projeto."""

    projeto = models.ForeignKey(
        ProjetoTecnico,
        on_delete=models.CASCADE,
        related_name="bom_itens",
        verbose_name="Projeto",
    )
    ambiente = models.ForeignKey(
        AmbienteProjeto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bom_itens",
        verbose_name="Ambiente",
    )
    item = models.ForeignKey(
        "cadastros.Item",
        on_delete=models.PROTECT,
        related_name="bom_itens",
        verbose_name="Item",
    )
    peca = models.ForeignKey(
        PecaComponente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bom_itens",
        verbose_name="Peça de Origem",
    )
    quantidade = models.DecimalField(max_digits=15, decimal_places=6, verbose_name="Quantidade")
    unidade = models.CharField(max_length=20, verbose_name="Unidade")
    perda_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Perda (%)")
    quantidade_com_perda = models.DecimalField(
        max_digits=15, decimal_places=6, default=0, verbose_name="Quantidade c/ Perda"
    )
    custo_unitario = models.DecimalField(max_digits=15, decimal_places=4, verbose_name="Custo Unitário")
    custo_total = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Custo Total")
    fornecedor_preferencial = models.ForeignKey(
        "cadastros.Fornecedor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bom_itens",
        verbose_name="Fornecedor Preferencial",
    )
    reservado = models.BooleanField(default=False, verbose_name="Reservado")
    falta = models.BooleanField(default=False, verbose_name="Em Falta")

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "BOM — Item"
        verbose_name_plural = "BOM — Itens"
        unique_together = [("projeto", "item", "peca")]

    def __str__(self):
        return f"BOM {self.projeto.numero} — {self.item}"

    def save(self, *args, **kwargs):
        fator = 1 + (self.perda_pct / 100)
        self.quantidade_com_perda = self.quantidade * fator
        self.custo_total = self.quantidade_com_perda * self.custo_unitario
        super().save(*args, **kwargs)


class PlanoCorte(AbstractBaseModel):
    """Plano de corte otimizado para chapas."""

    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        PROCESSANDO = "processando", "Processando"
        APROVADO = "aprovado", "Aprovado"
        ENVIADO_MAQUINA = "enviado_maquina", "Enviado à Máquina"

    projeto = models.ForeignKey(
        ProjetoTecnico,
        on_delete=models.CASCADE,
        related_name="planos_corte",
        verbose_name="Projeto",
    )
    chapa = models.ForeignKey(
        "cadastros.Item",
        on_delete=models.PROTECT,
        related_name="planos_corte",
        verbose_name="Chapa",
    )
    largura_chapa_mm = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Largura da Chapa (mm)")
    comprimento_chapa_mm = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Comprimento da Chapa (mm)")
    rendimento_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Rendimento (%)")
    area_util_mm2 = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Área Útil (mm²)")
    area_usada_mm2 = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Área Usada (mm²)")
    sobras_mm2 = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Sobras (mm²)")
    prioridade = models.PositiveSmallIntegerField(default=0, verbose_name="Prioridade")
    arquivo_corte = models.FileField(
        upload_to="engenharia/cortes/",
        null=True,
        blank=True,
        verbose_name="Arquivo de Corte",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDENTE,
        verbose_name="Status",
    )

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Plano de Corte"
        verbose_name_plural = "Planos de Corte"
        ordering = ["projeto", "prioridade"]

    def __str__(self):
        return f"Plano Corte — {self.projeto.numero} / {self.chapa}"

    def save(self, *args, **kwargs):
        self.area_util_mm2 = self.largura_chapa_mm * self.comprimento_chapa_mm
        self.sobras_mm2 = self.area_util_mm2 - self.area_usada_mm2
        if self.area_util_mm2:
            self.rendimento_pct = (self.area_usada_mm2 / self.area_util_mm2) * 100
        super().save(*args, **kwargs)


class DivergenciaProjeto(AbstractBaseModel):
    """Divergência identificada durante análise do projeto técnico."""

    class Tipo(models.TextChoices):
        MEDIDA = "medida", "Medida"
        MATERIAL = "material", "Material"
        FERRAGEM = "ferragem", "Ferragem"
        ACABAMENTO = "acabamento", "Acabamento"
        BOM = "bom", "BOM"
        OUTRO = "outro", "Outro"

    class Gravidade(models.TextChoices):
        CRITICA = "critica", "Crítica"
        ALTA = "alta", "Alta"
        MEDIA = "media", "Média"
        BAIXA = "baixa", "Baixa"

    projeto = models.ForeignKey(
        ProjetoTecnico,
        on_delete=models.CASCADE,
        related_name="divergencias",
        verbose_name="Projeto",
    )
    tipo = models.CharField(max_length=20, choices=Tipo.choices, verbose_name="Tipo")
    descricao = models.TextField(verbose_name="Descrição")
    gravidade = models.CharField(max_length=10, choices=Gravidade.choices, verbose_name="Gravidade")
    resolvida = models.BooleanField(default=False, verbose_name="Resolvida")
    resolucao = models.TextField(blank=True, verbose_name="Resolução")
    data_resolucao = models.DateTimeField(null=True, blank=True, verbose_name="Data de Resolução")

    class Meta(AbstractBaseModel.Meta):
        verbose_name = "Divergência do Projeto"
        verbose_name_plural = "Divergências do Projeto"
        ordering = ["projeto", "gravidade"]

    def __str__(self):
        return f"[{self.get_gravidade_display()}] {self.get_tipo_display()} — {self.projeto.numero}"
