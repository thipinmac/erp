"""Tests para o módulo Produção."""
from django.test import TestCase
from django.urls import reverse

from apps.core.test_helpers import login_with_empresa


class ProducaoViewTests(TestCase):
    def setUp(self):
        self.user, self.emp = login_with_empresa(self, "prod_user", "pr@t.com", "pass123")

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
