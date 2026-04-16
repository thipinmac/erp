"""Tests para o módulo Produção."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.administracao.models import Empresa, Perfil

User = get_user_model()


def setup_user_with_empresa(username, email, password):
    emp, _ = Empresa.objects.get_or_create(
        razao_social="Teste ERP", defaults={"cnpj": "00.000.000/0001-00"}
    )
    perfil, _ = Perfil.objects.get_or_create(
        nome="Teste", empresa=emp, defaults={"papel": "admin"}
    )
    user = User.objects.create_superuser(username, email, password)
    user.perfil = perfil
    user.save()
    return user, emp


class ProducaoViewTests(TestCase):
    def setUp(self):
        self.user, emp = setup_user_with_empresa("prod_user", "pr@t.com", "pass123")
        self.client.login(username="prod_user", password="pass123")
        s = self.client.session
        s["empresa_ativa_id"] = str(emp.pk)
        s.save()

    def test_kanban_ok(self):
        r = self.client.get(reverse("producao:kanban"))
        self.assertEqual(r.status_code, 200)

    def test_op_list_ok(self):
        r = self.client.get(reverse("producao:op_list"))
        self.assertEqual(r.status_code, 200)

    def test_op_create_get(self):
        r = self.client.get(reverse("producao:op_create"))
        self.assertEqual(r.status_code, 200)

    def test_romaneio_list_ok(self):
        r = self.client.get(reverse("producao:romaneio_list"))
        self.assertEqual(r.status_code, 200)
