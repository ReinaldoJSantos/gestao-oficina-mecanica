from django.db import models
from django.contrib.auth.models import User


class Cliente(models.Model):
    nome = models.CharField(max_length=100)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    cpf = models.CharField(max_length=14, unique=True)


class Veiculo(models.Model):
    cliente = models.ForeignKey(
        Cliente, on_delete=models.CASCADE, related_name="veiculos"
    )
    placa = models.CharField(max_length=7, unique=True)
    modelo = models.CharField(max_length=50)
    marca = models.CharField(max_length=50)


class OrdemServico(models.Model):
    STATUS_CHOICES = [("P", "Pendente"), ("A", "Aprovado"), ("F", "Finalizado")]
    veiculo = models.ForeignKey(Veiculo, on_delete=models.CASCADE)
    mecanico = models.ForeignKey(User, on_delete=models.PROTECT)
    data_criacao = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default="P")
    observacoes = models.TextField(blank=True)

    @property
    def total_geral(self):
        # Soma todos os itens vinculados a esta OS
        return sum(item.subtotal for item in self.itens.all())


class ItemServico(models.Model):
    os = models.ForeignKey(OrdemServico, related_name="itens", on_delete=models.CASCADE)
    descricao = models.CharField(max_length=200)
    quantidade = models.DecimalField(max_digits=5, decimal_places=2)
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def subtotal(self):
        return self.quantidade * self.valor_unitario
