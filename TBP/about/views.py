from django.views.generic import TemplateView


class AboutAuthorPage(TemplateView):
    template_name = 'about/author.html'


class AboutTechPage(TemplateView):
    template_name = 'about/tech.html'
