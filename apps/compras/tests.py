"""Tests para o módulo Compras."""
from django.test import TestCase
from django.urls import reverse

from apps.core.test_helpers import login_with_empresa


class ComprasViewTests(TestCase):
    def setUp(self):
        self.user, self.emp = login_with_empresa(self, "comp_user", "co@t.com", "pass123")

    def test_requisicao_list_ok(self):
        r = self.client.get(reverse("compras:requisicao_list"))
        self.assertEqual(r.status_code, 200)

    def test_pedido_list_ok(self):
        r = self.client.get(reverse("compras:pedido_list"))
        self.assertEqual(r.status_code, 200)

    def test_pedido_create_get(self):
        r = self.client.get(reverse("compras:pedido_create"))
        self.assertEqual(r.status_code, 200)
