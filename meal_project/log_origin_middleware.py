import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('meal_project.log_origin')


class LogOriginMiddleware(MiddlewareMixin):
    """
    Temporary middleware to log incoming Origin/Referer/Host and a few meta fields
    for POSTs to the login endpoint (/api/users/login/).

    This file exists so the middleware import in `settings.py` succeeds on startup
    and to help capture malformed headers seen by Django during mobile requests.
    Remove or disable this middleware once debugging is complete.
    """

    def process_request(self, request):
        try:
            path = request.path or ''
            method = (request.method or '').upper()
        except Exception:
            return None

        # Only log the specific endpoint to avoid excessive noise
        if path.startswith('/api/users/login') and method == 'POST':
            meta = getattr(request, 'META', {})
            origin = meta.get('HTTP_ORIGIN')
            referer = meta.get('HTTP_REFERER')
            host = meta.get('HTTP_HOST')
            remote_addr = meta.get('REMOTE_ADDR')
            user_agent = meta.get('HTTP_USER_AGENT')

            # Check for CSRF cookie and header presence. Mask actual token values to
            # avoid logging secrets in full. This is temporary debug logging and
            # should be removed once we've diagnosed the issue.
            csrf_cookie = None
            try:
                csrf_cookie = request.COOKIES.get('csrftoken')
            except Exception:
                csrf_cookie = None

            x_csrf_header = meta.get('HTTP_X_CSRFTOKEN')

            def _mask(val: str | None) -> str:
                if not val:
                    return '<missing>'
                s = str(val)
                if len(s) <= 8:
                    return s[0:1] + '***'
                return s[:4] + '...' + s[-4:]

            logger.warning(
                "LogOriginMiddleware: POST %s origin='%s' referer='%s' host='%s' x-forwarded-proto='%s' remote='%s' ua='%s' csrf_cookie='%s' x_csrf_header='%s'",
                path,
                origin,
                referer,
                host,
                meta.get('HTTP_X_FORWARDED_PROTO'),
                remote_addr,
                user_agent,
                _mask(csrf_cookie),
                _mask(x_csrf_header),
            )

        return None
import logging

logger = logging.getLogger('chopsmo.log_origin')


class LogOriginMiddleware:
    """Temporary middleware to log incoming Origin/Referer/Host headers
    for the login endpoint so we can diagnose malformed Origin headers.

    Install this temporarily and remove after debugging.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only log for the login endpoint to avoid noisy logs
        try:
            path = request.path
        except Exception:
            path = None

        if path == '/api/users/login/' and request.method in ('POST', 'OPTIONS'):
            origin = request.META.get('HTTP_ORIGIN')
            referer = request.META.get('HTTP_REFERER')
            host = request.META.get('HTTP_HOST')
            forwarded = request.META.get('HTTP_X_FORWARDED_PROTO')
            remote = request.META.get('REMOTE_ADDR')
            ua = request.META.get('HTTP_USER_AGENT')

            logger.warning(
                'LogOriginMiddleware: %s %s origin=%r referer=%r host=%r x-forwarded-proto=%r remote=%r ua=%r',
                request.method,
                path,
                origin,
                referer,
                host,
                forwarded,
                remote,
                ua,
            )

        response = self.get_response(request)
        return response
