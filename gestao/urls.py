from django.urls import path
from . import views

urlpatterns = [
    path("historico/", views.historico_veiculo, name="historico_veiculo"),
    path("os/nova/", views.nova_os, name="nova_os"),
    path("os/editar/<int:pk>/", views.nova_os, name="editar_os"),
    path("os/pdf/<int:pk>/", views.gerar_pdf_os, name="gerar_pdf_os"),
    path("cliente/novo/", views.novo_cliente, name="novo_cliente"),
    path("veiculo/novo/", views.novo_veiculo, name="novo_veiculo"),
    path("os/email/<int:pk>/", views.enviar_orcamento_email, name="enviar_email_os"),
]
