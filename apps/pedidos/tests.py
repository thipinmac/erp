"""Tests para o módulo Pedidos."""
from django.test import TestCase
from django.urls import reverse

from apps.core.test_helpers import login_with_empresa


class PedidosViewTests(TestCase):
    def setUp(self):
        self.user, self.emp = login_with_empresa(self, "ped_user", "p@t.com", "pass123")

    def test_pedido_list_ok(self):
        r = self.client.get(reverse("pedidos:list"))
        self.assertEqual(r.status_code, 200)

    def test_pedido_kanban_ok(self):
        r = self.client.get(reverse("pedidos:kanban"))
        self.assertEqual(r.status_code, 200)

    def test_pedido_create_get(self):
        r = self.client.get(reverse("pedidos:create"))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "pedidos/pedido_form.html")
