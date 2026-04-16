"""AuditMiddleware — disponibiliza o usuário atual para signals."""
import threading

_local = threading.local()


def get_current_user():
    return getattr(_local, "user", None)


def get_current_empresa():
    return getattr(_local, "empresa", None)


class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _local.user = request.user if request.user.is_authenticated else None
        _local.empresa = getattr(request, "empresa", None)
        response = self.get_response(request)
        return response
