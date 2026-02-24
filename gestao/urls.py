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
    path("", views.dashboard, name="dashboard"),
    path("os/visualizar/<int:pk>/", views.detalhe_os, name="detalhe_os"),
    path("os/nova/", views.salvar_os, name="nova_os"),
    path("os/editar/<int:pk>/", views.salvar_os, name="editar_os"),
    path("os/excluir/<int:pk>/", views.excluir_os, name="excluir_os"),
    path("clientes/", views.lista_clientes, name="lista_clientes"),
    path("cliente/novo/", views.salvar_cliente, name="novo_cliente"),
    path("cliente/editar/<int:pk>/", views.salvar_cliente, name="editar_cliente"),
    path("cliente/excluir/<int:pk>/", views.excluir_cliente, name="excluir_cliente"),
    path("veiculos/", views.lista_veiculos, name="lista_veiculos"),
    path("veiculos/novo/", views.salvar_veiculo, name="novo_veiculos"),
    path("veiculos/editar/<int:pk>/", views.salvar_veiculo, name="editar_veiculo"),
    path("veiculos/excluir<int:pk>/", views.excluir_veiculo, name="excluir_veiculo"),

]
