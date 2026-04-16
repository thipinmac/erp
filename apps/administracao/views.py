"""Views de autenticação e administração."""
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.views.generic import TemplateView, UpdateView

from .forms import LoginForm
from .models import Empresa, Filial


def login_view(request):
    if request.user.is_authenticated:
        return redirect("bi:dashboard")

    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        next_url = request.GET.get("next", "/")
        return redirect(next_url)

    return render(request, "administracao/login.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    return redirect("administracao:login")


@login_required
def selecionar_empresa(request, empresa_id):
    """Troca a empresa ativa do usuário na sessão."""
    from .models import Empresa
    try:
        empresa = Empresa.objects.get(id=empresa_id, ativo=True)
        if request.user.empresa == empresa or request.user.is_superuser:
            request.session["empresa_ativa_id"] = str(empresa.id)
            request.session.pop("filial_ativa_id", None)
            messages.success(request, f"Empresa alterada para {empresa}.")
    except Empresa.DoesNotExist:
        messages.error(request, "Empresa não encontrada.")
    return redirect(request.META.get("HTTP_REFERER", "/"))


class ConfiguracaoView(LoginRequiredMixin, TemplateView):
    template_name = "administracao/configuracao.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["empresa"] = self.request.empresa
        ctx["filiais"] = Filial.objects.filter(empresa=self.request.empresa) if self.request.empresa else []
        return ctx
