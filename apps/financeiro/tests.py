"""Tests para o módulo Financeiro."""
from django.test import TestCase
from django.urls import reverse

from apps.core.test_helpers import login_with_empresa


class FinanceiroViewTests(TestCase):
    def setUp(self):
        self.user, self.emp = login_with_empresa(self, "fin_user", "f@t.com", "pass123")

    def test_receber_list_ok(self):
        r = self.client.get(reverse("financeiro:receber"))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "financeiro/receber_list.html")

    def test_pagar_list_ok(self):
        r = self.client.get(reverse("financeiro:pagar"))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "financeiro/pagar_list.html")

    def test_dre_ok(self):
        r = self.client.get(reverse("financeiro:dre"))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "financeiro/dre.html")
