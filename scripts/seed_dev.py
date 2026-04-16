"""
Seed inicial para desenvolvimento.
Cria: Empresa, Filial, Superusuário, Etapas do Pipeline CRM.

Uso: python manage.py shell < scripts/seed_dev.py
  ou: python manage.py runscript seed_dev  (com django-extensions)
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from apps.administracao.models import Empresa, Filial, Perfil, Usuario
from apps.crm.models import EtapaPipeline

print("=== Seed de Desenvolvimento ===\n")

# ── Empresa ──────────────────────────────────────────────────────────────────
empresa, created = Empresa.objects.get_or_create(
    cnpj="00.000.000/0001-00",
    defaults={
        "razao_social": "Móveis Planejados Demo Ltda",
        "nome_fantasia": "MóveisERP Demo",
        "regime_tributario": "SN",
        "cidade": "São Paulo",
        "uf": "SP",
    },
)
print(f"{'[CRIADA]' if created else '[JÁ EXISTE]'} Empresa: {empresa}")

# ── Filial ───────────────────────────────────────────────────────────────────
filial, created = Filial.objects.get_or_create(
    empresa=empresa,
    codigo="001",
    defaults={
        "nome": "Matriz — São Paulo",
        "cidade": "São Paulo",
        "uf": "SP",
    },
)
print(f"{'[CRIADA]' if created else '[JÁ EXISTE]'} Filial: {filial}")

# ── Perfil Admin ──────────────────────────────────────────────────────────────
perfil_admin, _ = Perfil.objects.get_or_create(
    empresa=empresa,
    nome="Administrador",
    defaults={
        "papel": "admin",
        "pode_ver_custos": True,
        "pode_ver_margem": True,
        "pode_dar_desconto": True,
        "limite_desconto_pct": 100,
        "pode_aprovar_orcamento": True,
        "pode_emitir_nfe": True,
    },
)

# ── Superusuário ──────────────────────────────────────────────────────────────
if not Usuario.objects.filter(username="admin").exists():
    user = Usuario.objects.create_superuser(
        username="admin",
        email="admin@moveis-erp.local",
        password="admin123",
        first_name="Administrador",
        last_name="Sistema",
        empresa=empresa,
        perfil=perfil_admin,
    )
    print(f"[CRIADO] Superusuário: admin / admin123")
else:
    user = Usuario.objects.get(username="admin")
    print("[JÁ EXISTE] Superusuário: admin")

user.filiais_autorizadas.add(filial)

# ── Etapas do Pipeline CRM ────────────────────────────────────────────────────
etapas = [
    ("Captação", "#6366f1", 10, False, False),
    ("Qualificação", "#8b5cf6", 20, False, False),
    ("Medição / Briefing", "#a855f7", 30, False, False),
    ("Orçamento em elaboração", "#f59e0b", 50, False, False),
    ("Proposta enviada", "#f97316", 65, False, False),
    ("Negociação", "#ef4444", 75, False, False),
    ("Aprovado", "#22c55e", 100, True, False),
    ("Perdido", "#6b7280", 0, False, True),
]

for ordem, (nome, cor, prob, ganho, perdido) in enumerate(etapas, 1):
    obj, created = EtapaPipeline.objects.get_or_create(
        empresa=empresa,
        ordem=ordem,
        defaults={
            "nome": nome,
            "cor": cor,
            "probabilidade_padrao": prob,
            "etapa_final_ganho": ganho,
            "etapa_final_perdido": perdido,
        },
    )
    print(f"  {'[CRIADA]' if created else '[JÁ EXISTE]'} Etapa: {nome}")

print("\n=== Seed concluído! ===")
print("  URL: http://localhost:8000")
print("  Admin: http://localhost:8000/admin/")
print("  Login: admin / admin123")
