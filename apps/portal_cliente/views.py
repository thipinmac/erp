from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone


def _get_token_obj(token_str):
    """Retorna o PortalToken ativo correspondente ao token string."""
    from contratos.models import PortalToken  # noqa: F401 — import lazy para evitar circular

    try:
        from contratos.models import PortalToken

        return PortalToken.objects.select_related("contrato").get(
            token=token_str, ativo=True
        )
    except Exception:
        return None


def portal_login(request, token):
    """Valida token de acesso e inicia sessão do portal do cliente."""
    token_obj = _get_token_obj(token)

    if token_obj is None:
        return render(
            request,
            "portal_cliente/acesso_negado.html",
            {"motivo": "Link inválido ou expirado."},
            status=403,
        )

    # Verifica expiração se o model tiver o campo
    if hasattr(token_obj, "expira_em") and token_obj.expira_em:
        if token_obj.expira_em < timezone.now():
            return render(
                request,
                "portal_cliente/acesso_negado.html",
                {"motivo": "Este link expirou."},
                status=403,
            )

    # Seta session com dados do contrato
    request.session["portal_token"] = str(token_obj.token)
    request.session["portal_contrato_id"] = str(token_obj.contrato.pk)
    request.session["portal_empresa_id"] = str(token_obj.contrato.empresa_id)

    return redirect("portal_cliente:view")


def _portal_required(view_func):
    """Decorator que exige token válido na sessão."""
    from functools import wraps

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if "portal_contrato_id" not in request.session:
            return redirect("portal_cliente:acesso_negado")
        return view_func(request, *args, **kwargs)

    return wrapper


def _get_contrato(request):
    """Retorna o contrato associado à sessão do portal."""
    from contratos.models import Contrato

    contrato_id = request.session.get("portal_contrato_id")
    if not contrato_id:
        return None
    try:
        return Contrato.objects.get(pk=contrato_id)
    except Exception:
        return None


@_portal_required
def portal_dashboard(request):
    """Dashboard principal do portal do cliente."""
    contrato = _get_contrato(request)
    if contrato is None:
        return redirect("portal_cliente:acesso")

    ctx = {
        "contrato": contrato,
        "titulo": "Meu Projeto",
    }
    return render(request, "portal_cliente/dashboard.html", ctx)


@_portal_required
def portal_timeline(request):
    """Timeline de eventos e marcos do projeto."""
    contrato = _get_contrato(request)
    if contrato is None:
        return redirect("portal_cliente:acesso")

    # Eventos do contrato — adaptável à estrutura de contratos
    eventos = []
    if hasattr(contrato, "historico"):
        eventos = contrato.historico.order_by("-criado_em")

    ctx = {
        "contrato": contrato,
        "eventos": eventos,
        "titulo": "Timeline do Projeto",
    }
    return render(request, "portal_cliente/timeline.html", ctx)


@_portal_required
def portal_documentos(request):
    """Documentos do contrato disponíveis para o cliente."""
    contrato = _get_contrato(request)
    if contrato is None:
        return redirect("portal_cliente:acesso")

    documentos = []
    if hasattr(contrato, "documentos"):
        documentos = contrato.documentos.filter(publico=True)

    ctx = {
        "contrato": contrato,
        "documentos": documentos,
        "titulo": "Documentos",
    }
    return render(request, "portal_cliente/documentos.html", ctx)


@_portal_required
def portal_mensagens(request):
    """Troca de mensagens entre cliente e equipe via portal."""
    from .models import MensagemPortal

    contrato = _get_contrato(request)
    if contrato is None:
        return redirect("portal_cliente:acesso")

    if request.method == "POST":
        assunto = request.POST.get("assunto", "")
        corpo = request.POST.get("corpo", "")
        if corpo:
            MensagemPortal.objects.create(
                empresa=contrato.empresa,
                contrato=contrato,
                origem="cliente",
                assunto=assunto or "Mensagem do cliente",
                corpo=corpo,
            )

    mensagens_qs = MensagemPortal.objects.filter(
        contrato=contrato
    ).order_by("criado_em")

    # Marca mensagens internas como lidas
    mensagens_qs.filter(origem="interno", lida=False).update(
        lida=True, data_leitura=timezone.now()
    )

    ctx = {
        "contrato": contrato,
        "mensagens": mensagens_qs,
        "titulo": "Mensagens",
    }
    return render(request, "portal_cliente/mensagens.html", ctx)
