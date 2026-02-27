from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("oficina/", include("gestao.urls")),
    # Esta linha é OBRIGATÓRIA para ativar o sistema de login
    path("accounts/", include("django.contrib.auth.urls")),
    path("", RedirectView.as_view(url="/oficina/"), name="index"),
]
