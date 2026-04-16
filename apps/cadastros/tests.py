"""Tests para o módulo Cadastros."""
from django.test import TestCase
from django.urls import reverse

from apps.core.test_helpers import login_with_empresa


class CadastrosViewTests(TestCase):
    def setUp(self):
        self.user, self.emp = login_with_empresa(self, "cad_user", "cad@t.com", "pass123")

    def test_cliente_list_ok(self):
        r = self.client.get(reverse("cadastros:cliente_list"))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "cadastros/cliente_list.html")

    def test_cliente_create_get(self):
        r = self.client.get(reverse("cadastros:cliente_create"))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "cadastros/cliente_form.html")

    def test_fornecedor_list_ok(self):
        r = self.client.get(reverse("cadastros:fornecedor_list"))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "cadastros/fornecedor_list.html")

    def test_fornecedor_create_get(self):
        r = self.client.get(reverse("cadastros:fornecedor_create"))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "cadastros/fornecedor_form.html")

    def test_item_list_ok(self):
        r = self.client.get(reverse("cadastros:item_list"))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "cadastros/item_list.html")

    def test_item_create_get(self):
        r = self.client.get(reverse("cadastros:item_create"))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "cadastros/item_form.html")

    def test_unauthenticated_redirects_to_login(self):
        self.client.logout()
        r = self.client.get(reverse("cadastros:cliente_list"))
        self.assertEqual(r.status_code, 302)
        self.assertIn("/entrar/", r["Location"])
