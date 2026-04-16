"""Tests para o módulo BI."""
from django.test import TestCase
from django.urls import reverse

from apps.core.test_helpers import login_with_empresa


class BIViewTests(TestCase):
    def setUp(self):
        self.user, self.emp = login_with_empresa(self, "bi_user", "bi@t.com", "pass123")

    def test_dashboard_ok(self):
        r = self.client.get(reverse("bi:dashboard"))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "bi/dashboard.html")

    def test_dashboard_has_context(self):
        r = self.client.get(reverse("bi:dashboard"))
        self.assertIn("total_pedidos_abertos", r.context)
        self.assertIn("oportunidades_abertas", r.context)

    def test_unauthenticated_redirect(self):
        self.client.logout()
        r = self.client.get(reverse("bi:dashboard"))
        self.assertEqual(r.status_code, 302)
