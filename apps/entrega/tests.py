"""Tests para o módulo Entrega."""
from django.test import TestCase
from django.urls import reverse

from apps.core.test_helpers import login_with_empresa


class EntregaViewTests(TestCase):
    def setUp(self):
        self.user, self.emp = login_with_empresa(self, "ent_user", "en@t.com", "pass123")

    def test_agenda_list_ok(self):
        r = self.client.get(reverse("entrega:agenda"))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "entrega/agenda_list.html")

    def test_agenda_create_get(self):
        r = self.client.get(reverse("entrega:agenda_create"))
        self.assertEqual(r.status_code, 200)
