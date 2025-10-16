import logging

logger = logging.getLogger('meal_project.log_origin')


class LogOriginMiddleware:
    """Temporary middleware to log incoming Origin/Referer/Host headers and
    whether a csrf cookie and X-CSRFToken header were present for the login
    endpoint. Keep this temporarily while diagnosing cross-subdomain CSRF
    issues; remove afterwards.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            path = request.path or ''
            method = (request.method or '').upper()
        except Exception:
            return self.get_response(request)

        if path.startswith('/api/users/login') and method in ('POST', 'OPTIONS'):
            meta = getattr(request, 'META', {})
            origin = meta.get('HTTP_ORIGIN')
            referer = meta.get('HTTP_REFERER')
            host = meta.get('HTTP_HOST')
            forwarded = meta.get('HTTP_X_FORWARDED_PROTO')
            remote = meta.get('REMOTE_ADDR')
            ua = meta.get('HTTP_USER_AGENT')

            # Safely get CSRF cookie and header, mask values for logging
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
                "LogOriginMiddleware: %s %s origin=%r referer=%r host=%r x-forwarded-proto=%r remote=%r ua=%r csrf_cookie=%r x_csrf_header=%r",
                method,
                path,
                origin,
                referer,
                host,
                forwarded,
                remote,
                ua,
                _mask(csrf_cookie),
                _mask(x_csrf_header),
            )

        response = self.get_response(request)
        return response
