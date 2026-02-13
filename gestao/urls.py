from django.urls import path
from . import views

urlpatterns = [
    path("historico/", views.historico_veiculo, name="historico_veiculo"),
    path("os/nova/", views.nova_os, name="nova_os"),
    path("os/editar/<int:pk>/", views.nova_os, name="editar_os"),
]
