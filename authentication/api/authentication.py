from urllib.parse import urlsplit

from rest_framework.authentication import SessionAuthentication


class WebsiteSessionAuthentication(SessionAuthentication):
    def authenticate_header(self, request):
        return 'Token'

    def authenticate(self, request):
        origin = request.META.get('HTTP_ORIGIN')
        fetch_site = request.META.get('HTTP_SEC_FETCH_SITE')

        if fetch_site in ('cross-site', 'cross-origin'):
            return None

        if origin:
            parsed_origin = urlsplit(origin)
            request_origin = f'{request.scheme}://{request.get_host()}'
            if f'{parsed_origin.scheme}://{parsed_origin.netloc}'.casefold() != request_origin.casefold():
                return None

        return super().authenticate(request)
