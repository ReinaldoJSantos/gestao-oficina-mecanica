from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from .forms import OSForm, ItemServicoFormSet
from .models import OrdemServico
from .models import Cliente, Veiculo

from django.contrib.auth.decorators import login_required  # Importe isso
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML


# View simples para cadastrar Cliente


def novo_cliente(request):
    if request.method == "POST":
        nome = request.POST.get("nome")
        email = request.POST.get("email")
        cpf = request.POST.GET("CPF")
        Cliente.object.create(nome=nome, email=email, cpf=cpf)
        return redirect("novo_veiculo")
    return render(request, "gestao/form_clinete.html")


# View simples para cadastrar veiculo


def novo_veiculo(request):
    clientes = Cliente.objects.all()
    if request.method == "POST":
        cliente_id = request.POST.get("cliente")
        cliente = Cliente.objects.get(id=cliente_id)
        Veiculo.objects.create(
            cliente=cliente,
            placa=request.POST.get("placa"),
            modelo=request.POST.get("modelo"),
            marca=request.POST.get("marca"),
        )
        return redirect("nova_os")
    return render(request, "gestao/form_veiculo.html", {"clientes": clientes})


@login_required
def gerar_pdf_os(request, pk):
    os = get_object_or_404(OrdemServico, pk=pk)
    html_string = render_to_string("gestao/orcamento_pdf.html", {"os": os})

    html = HTML(string=html_string)
    pdf = html.write_pdf()

    response = HttpResponse(pdf, content_type="application/pdf")

    # Criamos um nome de arquivo dinâmico e limpo
    data_formatada = os.data_criacao.strftime('%Y%m%d')
    nome_arquivo = f"OS_{os.id}_{os.veiculo.placa}_{data_formatada}.pdf"
    response["Content-Disposition"] = f'inline; filename="{nome_arquivo}"'

    return response


@login_required
def historico_veiculo(request):
    placa = request.GET.get('placa')

    if placa:
        # Se digitou a placa, filtra só por ela
        ordens = OrdemServico.objects.filter(veiculo__placa__iexact=placa).order_by('-data_criacao')
    else:
        # Se não digitou nada, mostra as 10 mais recentes do sistema todo
        ordens = OrdemServico.objects.all().order_by('-data_criacao')[:10]

    return render(request, 'gestao/historico.html', {'ordens': ordens, 'placa': placa})


@login_required
def nova_os(request, pk=None):
    instance = get_object_or_404(OrdemServico, pk=pk) if pk else None

    if request.method == "POST":
        form = OSForm(request.POST, instance=instance)
        formset = ItemServicoFormSet(request.POST, instance=instance)

        if form.is_valid() and formset.is_valid():
            os_salva = form.save(commit=False)
            os_salva.mecanico = request.user
            os_salva.save()
            formset.instance = os_salva
            formset.save()
            return redirect("historico_veiculo")
    else:
        # Se for GET, apenas preparamos os formulários vazios ou com a instância
        form = OSForm(instance=instance)
        formset = ItemServicoFormSet(instance=instance)

    # ATENÇÃO: Este return deve estar FORA do 'if' e do 'else'.
    # Ele é a segurança de que a página sempre carregará algo.
    return render(request, "gestao/form_os.html", {"form": form, "formset": formset})


