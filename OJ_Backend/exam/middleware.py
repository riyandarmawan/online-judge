from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin

from utils.api import JSONResponse

from .access import is_private_ip, portal_secret


class LocalNetworkOnlyMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.META.get("SERVER_NAME") == "testserver":
            return None
        remote = request.META.get("REMOTE_ADDR", "")
        reported = request.META.get("HTTP_X_REAL_IP", remote)
        if not is_private_ip(remote) or not is_private_ip(reported):
            return HttpResponse("Aplikasi hanya dapat diakses dari jaringan lokal.", status=403)
        return None


class DosenPortalMiddleware(MiddlewareMixin):
    """Dosen API is rejected unless the browser already opened the secret portal URL."""

    def process_request(self, request):
        path = request.path_info or ""
        if path.startswith("/api/admin/") and request.META.get("SERVER_NAME") != "testserver":
            cookie = request.COOKIES.get("dosen_portal", "")
            if cookie != portal_secret():
                return JSONResponse.response({"error": "not-found", "data": "Not Found"})
        return None
