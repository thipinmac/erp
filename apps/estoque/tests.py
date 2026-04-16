"""Tests para o módulo Estoque."""
from django.test import TestCase
from django.urls import reverse

from apps.core.test_helpers import login_with_empresa


class EstoqueViewTests(TestCase):
    def setUp(self):
        self.user, self.emp = login_with_empresa(self, "est_user", "e@t.com", "pass123")

    def test_saldo_list_ok(self):
        r = self.client.get(reverse("estoque:list"))
        self.assertEqual(r.status_code, 200)

    def test_movimentacao_list_ok(self):
        r = self.client.get(reverse("estoque:movimentacao_list"))
        self.assertEqual(r.status_code, 200)

    def test_sobra_list_ok(self):
        r = self.client.get(reverse("estoque:sobra_list"))
        self.assertEqual(r.status_code, 200)

    def test_reserva_list_ok(self):
        r = self.client.get(reverse("estoque:reserva_list"))
        self.assertEqual(r.status_code, 200)

    def test_inventario_list_ok(self):
        r = self.client.get(reverse("estoque:inventario_list"))
        self.assertEqual(r.status_code, 200)
