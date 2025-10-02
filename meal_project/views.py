from django.views.generic import TemplateView


class HomeView(TemplateView):
    """Simple landing page so the root URL returns a friendly response."""

    template_name = "home.html"
