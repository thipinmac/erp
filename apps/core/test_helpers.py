"""Helpers compartilhados para testes do ERP."""
from django.contrib.auth import get_user_model

User = get_user_model()


def setup_test_user(username, email, password):
    """
    Cria empresa, perfil e usuário de teste com tudo configurado.
    Retorna (user, empresa, session_data).
    """
    from apps.administracao.models import Empresa, Perfil

    emp, _ = Empresa.objects.get_or_create(
        razao_social="Teste ERP Ltda",
        defaults={"cnpj": "00.000.000/0001-91"},
    )
    perfil, _ = Perfil.objects.get_or_create(
        nome="Admin Teste",
        empresa=emp,
        defaults={"papel": "admin"},
    )
    user = User.objects.create_superuser(username, email, password)
    user.perfil = perfil
    user.save()
    return user, emp


def login_with_empresa(test_case, username, email, password):
    """Login e configura sessão com empresa ativa. Retorna (user, empresa)."""
    user, emp = setup_test_user(username, email, password)
    test_case.client.login(username=username, password=password)
    s = test_case.client.session
    s["empresa_ativa_id"] = str(emp.pk)
    s.save()
    return user, emp
