"""Views do módulo BI / Dashboard."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from apps.crm.models import Oportunidade
from apps.pedidos.models import Pedido


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "bi/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        empresa = getattr(self.request, "empresa", None)

        if empresa:
            pedidos_qs = Pedido.objects.filter(empresa=empresa, ativo=True)
            oportunidades_qs = Oportunidade.objects.filter(empresa=empresa, ativo=True)

            ctx["total_pedidos_abertos"] = pedidos_qs.exclude(
                status__in=["concluido", "cancelado"]
            ).count()
            ctx["pedidos_em_producao"] = pedidos_qs.filter(status="em_producao").count()
            ctx["oportunidades_abertas"] = oportunidades_qs.exclude(
                etapa__etapa_final_ganho=True, etapa__etapa_final_perdido=True
            ).count()
            from django.db.models import Sum
            ctx["faturamento_mes"] = pedidos_qs.filter(
                status="concluido"
            ).aggregate(total=Sum("valor_total"))["total"] or 0
        else:
            ctx["total_pedidos_abertos"] = 0
            ctx["pedidos_em_producao"] = 0
            ctx["oportunidades_abertas"] = 0
            ctx["faturamento_mes"] = 0

        ctx["title"] = "Dashboard"
        return ctx
