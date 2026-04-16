"""Tests para o módulo Assistência Técnica."""
from django.test import TestCase
from django.urls import reverse

from apps.core.test_helpers import login_with_empresa


class AssistenciaViewTests(TestCase):
    def setUp(self):
        self.user, self.emp = login_with_empresa(self, "asst_user", "as@t.com", "pass123")

    def test_chamado_list_ok(self):
        r = self.client.get(reverse("assistencia:list"))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "assistencia/chamado_list.html")

    def test_chamado_create_get(self):
        r = self.client.get(reverse("assistencia:create"))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "assistencia/chamado_form.html")
