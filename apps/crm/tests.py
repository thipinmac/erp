"""Tests para o módulo CRM."""
from django.test import TestCase
from django.urls import reverse

from apps.core.test_helpers import login_with_empresa


class CRMViewTests(TestCase):
    def setUp(self):
        self.user, self.emp = login_with_empresa(self, "crm_user", "c@t.com", "pass123")

    def test_pipeline_ok(self):
        r = self.client.get(reverse("crm:pipeline"))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "crm/pipeline.html")

    def test_oportunidade_list_ok(self):
        r = self.client.get(reverse("crm:oportunidade_list"))
        self.assertEqual(r.status_code, 200)

    def test_lead_list_ok(self):
        r = self.client.get(reverse("crm:lead_list"))
        self.assertEqual(r.status_code, 200)

    def test_visita_list_ok(self):
        r = self.client.get(reverse("crm:visita_list"))
        self.assertEqual(r.status_code, 200)

    def test_oportunidade_create_get(self):
        r = self.client.get(reverse("crm:oportunidade_create"))
        self.assertEqual(r.status_code, 200)

    def test_lead_create_get(self):
        r = self.client.get(reverse("crm:lead_create"))
        self.assertEqual(r.status_code, 200)
