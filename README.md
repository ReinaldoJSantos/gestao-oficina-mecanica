# 🛠️ Gestão de Oficina Mecânica

Sistema web desenvolvido em Django para gerenciamento de Ordens de Serviço (OS), veículos, clientes e controle de estoque de peças/produtos.

---

## 📌 Funcionalidades

- **Ordens de Serviço:** Criação, edição e acompanhamento de status de OS com itens dinâmicos.
- **Estoque de Produtos:** Controle de peças com preço de custo, preço de venda e aviso de estoque mínimo.
- **Veículos e Clientes:** Vínculo de veículos a ordens de serviço.
- **Autenticação:** Sistema seguro com restrição de acesso por usuário logado.

---

## 🛠️ Tecnologias Utilizadas

- **Backend:** Python 3.10+ / Django 4.x
- **Banco de Dados:** SQLite (Desenvolvimento)
- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap 5

---

## 🚀 Como Rodar o Projeto Localmente

### 1. Pré-requisitos
Certifique-se de ter instalado na sua máquina:
- Python 3.10 ou superior
- Git

### 2. Clonar o Repositório
```bash
git clone [https://github.com/seu-usuario/gestao-oficina-mecanica.git](https://github.com/seu-usuario/gestao-oficina-mecanica.git)
cd gestao-oficina-mecanica

### 3. Criar o ambiente virtual
python -m venv venv

# Ativar no Linux/macOS
source venv/bin/activate

# Ativar no Windows (Prompt de Comando)
venv\Scripts\activate.bat

### 4. Instalar Dependências

pip install -r requirements.txt

### 5. Configurar o Banco de Dados
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Criar um Superusuário(Admin)
```bash
python manage.py createsuperuser

### 7. Rodar o Servidor de Desenvolvimento
```bash
python manage.py runserver

### Comando Úteis
python manage.py changepassword <nome_usuario>

### Acessar Shell do Django
```bash
python manage.py shell


📝 Licença
Este projeto está sob a licença MIT - veja o arquivo LICENSE para mais detalhes.


## 🌐 Deploy em Produção

### 1. Variáveis de Ambiente
Em ambiente de produção, certifique-se de configurar as seguintes variáveis no arquivo `.env` ou nas configurações do seu servidor:

```env
DEBUG=False
SECRET_KEY=sua_chave_secreta_super_segura
ALLOWED_HOSTS=seu-dominio.com, .render.com, localhost
DATABASE_URL=postgres://usuario:senha@host:5432/nome_banco


### 2. Preparação dos Arquivos Estáticos
Antes de subir a aplicação, execute o comando abaixo para compilar e organizar os arquivos estáticos (CSS, JS, Imagens) na pasta de produção configurada via WhiteNoise ou STATIC_ROOT:

```Bash
python manage.py collectstatic --noinput