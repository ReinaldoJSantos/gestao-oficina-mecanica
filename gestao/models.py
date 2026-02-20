from django.db import models
from django.contrib.auth.models import User


class Cliente(models.Model):
    nome = models.CharField(max_length=100)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    cpf = models.CharField(max_length=14, unique=True)

    def __str__(self):
        return self.nome


class Veiculo(models.Model):
    cliente = models.ForeignKey(
        Cliente, on_delete=models.CASCADE,
        related_name="veiculos"
    )
    placa = models.CharField(max_length=7, unique=True)
    modelo = models.CharField(max_length=50)
    marca = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.modelo} - {self.placa}"


class OrdemServico(models.Model):
    STATUS_CHOICES = [
        ("P", "Pendente"),
        ("A", "Aprovado"),
        ("F", "Finalizado"),
        ("C", "Cancelado"),  # Adicionei Cancelado para maior controle
    ]
    veiculo = models.ForeignKey(Veiculo, on_delete=models.CASCADE)
    mecanico = models.ForeignKey(User, on_delete=models.PROTECT)
    data_criacao = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES,
                              default="P")
    observacoes = models.TextField(blank=True)

    def __str__(self):
        return f"OS {self.id} - {self.veiculo.placa}"

    @property
    def total_geral(self):
        # Usamos o nome correto da propriedade que definimos abaixo
        return sum(item.valor_total for item in self.itens.all())


class ItemOrdemServico(models.Model):
    ordem_servico = models.ForeignKey(
        OrdemServico, on_delete=models.CASCADE, related_name="itens"
    )
    descricao = models.CharField(max_length=200)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2,
                                     default=1)
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.descricao} (OS {self.ordem_servico.id})"

    @property
    def valor_total(self):
        # Cálculo do subtotal deste item específico
        return self.quantidade * self.valor_unitario
