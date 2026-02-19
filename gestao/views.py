from django.core.mail import EmailMessage
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Count
from .forms import OSForm, ItemServicoFormSet
from .models import OrdemServico
from .models import Cliente, Veiculo

from django.contrib.auth.decorators import login_required  # Importe isso
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML


@login_required
def dashboard(request):
    # conta quantas Os existem por status
    resumo_status = OrdemServico.objects.values('status').annotate(total=Count('id'))

    # Calcula o valor total de todas as OS (Soma todos os itens)
    # Nota: Como o tatal_geral é um @propertu, precisamos somar via itens do banco de dados
    valor_total_pendente = (
        OrdemServico.objects.filter(status="P").aggregate(
            soma=Sum("itens__quantidade") * Sum("itens__valor_unitario")
        )["soma"]
        or 0
    )
    ultimas_os = OrdemServico.objects.all().order_by('-data_criacao')[:5]

    return render(request, 'gestao/dashboard.html', {
        'ultimoas_os': ultimas_os,
        'resumo': resumo_status,
        'valor_total': valor_total_pendente
    })


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


@login_required
def enviar_orcamento_email(request, pk):
    os = get_object_or_404(OrdemServico, pk=pk)

    # 1. Geramos o PDF
    html_string = render_to_string("gestao/orcamento_pdf.html", {"os": os})
    pdf = HTML(string=html_string).write_pdf()

    # 2. Criamos o objeto de e-mail com argumentos nomeados (Seguro!)
    email = EmailMessage(
        subject=f"Orçamento de Manutenção - OS {os.id} - {os.veiculo.modelo}",
        body=f"Olá {os.veiculo.cliente.nome},\n\nSegue em anexo o orçamento detalhado para o veículo {os.veiculo.modelo}.\n\nFicamos no aguardo da sua aprovação.",
        from_email="reinaldo.rsmaster@gmail.com",  # O e-mail configurado no settings.py
        to=[os.veiculo.cliente.email],  # Deve ser uma LISTA []
    )

    # 3. Anexamos o PDF
    email.attach(f"Orcamento_{os.id}.pdf", pdf, "application/pdf")

    try:
        email.send()
        messages.success(
            request, f"E-mail enviado com sucesso para {os.veiculo.cliente.email}!"
        )
    except Exception as e:
        messages.error(request, f"Erro técnico ao enviar: {e}")

    return redirect("historico_veiculo")
