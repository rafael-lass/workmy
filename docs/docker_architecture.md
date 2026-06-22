# Arquitetura Docker — WorkMy

Este documento descreve a localização e o funcionamento de cada `Dockerfile` presente no projeto, além de explicar como eles se integram através do `docker-compose.yml`.

## Localização dos Arquivos `Dockerfile`

O projeto possui 3 arquivos `Dockerfile` desenvolvidos customizados para as camadas da aplicação:

1. **Frontend (React/Vite)**
   - **Caminho:** `/frontend/Dockerfile`
2. **BFF (Backend For Frontend - Node.js)**
   - **Caminho:** `/frontend/bff/Dockerfile`
3. **Backend Core (FastAPI)**
   - **Caminho:** `/backend-fastapi/Dockerfile`

---

## Como funciona cada Dockerfile

### 1. Frontend (`/frontend/Dockerfile`)
Responsável por empacotar e servir a aplicação React, otimizado para o ambiente de desenvolvimento.

**Principais características:**
- **Imagem Base:** Utiliza `node:20-alpine`, uma imagem bem leve do Node.js baseada no Alpine Linux.
- **Dependências e Segurança:** Copia os arquivos de configuração do NPM, roda `npm install` e logo em seguida `npm audit fix || true`. Essa etapa tenta automaticamente consertar vulnerabilidades nos pacotes NPM.
- **Execução:** Expõe a porta interna `5173` e executa o servidor Vite via `npm run dev -- --host`, garantindo que o servidor aceite conexões de fora do container para você acessar pelo navegador local.
- **Uso no Compose:** Através do `docker-compose.yml`, a pasta do seu computador é montada dentro do container (volume), permitindo o **hot-reload** (edições no código se refletem sem precisar reiniciar o container).

### 2. BFF - Backend For Frontend (`/frontend/bff/Dockerfile`)
Responsável por rodar o proxy Node.js que atua como intermediário seguro entre o Frontend e o Backend Core.

**Principais características:**
- **Segurança por Usuário (Non-Root):** Ele cria um grupo (`appgroup`) e um usuário (`appuser`) sem permissões de root. O servidor roda sob esse usuário, o que é uma excelente prática de segurança contra escalonamento de privilégios.
- **Instalação Restrita:** Utiliza `npm ci --only=production --ignore-scripts` para instalar as dependências. Isso garante consistência de pacotes, omite dependências de desenvolvimento desnecessárias e impede a execução automática de scripts de terceiros maliciosos.
- **Healthcheck:** Possui uma configuração de monitoramento nativa no Docker que pinga a rota `/api/health` a cada 30 segundos para checar se o servidor Node está saudável.
- **Execução:** Seta variáveis de produção (`NODE_ENV=production`) e levanta a porta `3000` chamando o `server.js`.

### 3. Backend Core (`/backend-fastapi/Dockerfile`)
Responsável pela API construída em Python/FastAPI e Arquitetura Hexagonal.

**Principais características:**
- **Multi-Stage Build (Duas Etapas):** Uma técnica avançada para imagens limpas e leves.
  - *Stage 1 (Builder):* Instala o gerenciador rápido `uv` e baixa todas as dependências do `requirements.txt` num ambiente focado apenas em construir tudo.
  - *Stage 2 (Runtime):* Cria uma nova imagem limpa, copia as dependências pré-instaladas do Stage 1 e seu código fonte. Ferramentas pesadas de build ficam para trás, reduzindo tamanho e superfície de ataque da imagem.
- **Segurança (Non-Root):** Similar ao BFF, roda a aplicação usando o usuário não privilegiado `appuser`.
- **Variáveis de Ambiente:** Define comportamentos seguros para o Python como não criar cache de bytecode (`PYTHONDONTWRITEBYTECODE=1`) e exibir logs imediatamente (`PYTHONUNBUFFERED=1`).
- **Healthcheck e Start:** A saúde do container é baseada na rota `/health`, e a aplicação sobe utilizando o Uvicorn na porta `8000`.

---

## Serviços de Infraestrutura (Imagens Oficiais)

Diferente do Frontend, BFF e Backend que criamos do zero, o Banco de Dados e o RabbitMQ não precisam de um `Dockerfile` customizado. Eles utilizam imagens oficiais prontas, baixadas do Docker Hub, e são configurados direto pelo `docker-compose.yml`.

### 1. PostgreSQL (Banco de Dados)
- **Imagem:** `postgres:15-alpine` (Versão 15, otimizada baseada no Alpine Linux).
- **Persistência de Dados:** Configurado com um "Volume" do Docker (`postgres_data`). Isso significa que mesmo se você destruir ou reiniciar o container, os dados, as tabelas e os usuários não serão perdidos, pois ficam salvos com segurança pelo Docker.
- **Porta:** Mapeia a porta `5432` da sua máquina para a `5432` do container. Isso permite que você se conecte ao banco usando ferramentas como DBeaver ou pgAdmin localmente.

### 2. RabbitMQ (Fila de Mensagens)
- **Imagem:** `rabbitmq:3-management-alpine` (Essa versão "management" já vem com um painel visual no navegador para você gerenciar as filas e os envios de dados assíncronos).
- **Persistência de Dados:** Também tem seu próprio volume (`rabbitmq_data`) para não perder as filas configuradas num eventual reinício.
- **Portas:**
  - `5672`: Porta de comunicação interna oficial do AMQP (é nela que o Backend conecta).
  - `15672`: Interface web administrativa. Você pode acessar do seu navegador em `http://localhost:15672` com usuário e senha padrões (guest/guest).

---

## Integração Geral via `docker-compose.yml`

O arquivo `docker-compose.yml` na raiz atua como o maestro, amarrando as suas três aplicações e os dois serviços de infraestrutura num grande ecossistema:

- **Rede Interna (Bridge):** Ele cria uma rede isolada (`workmy_net`). Todos os 5 containers conversam entre si usando apenas o nome do serviço como DNS. Por exemplo, o backend encontra o banco apenas apontando para o endereço `postgres:5432`. O BFF encontra o backend apontando para `fastapi:8000`.
- **Ordem de Inicialização Inteligente (Depends_on):** A infraestrutura obedece a uma hierarquia de inicialização baseada na "saúde" real dos processos e não apenas "se o container ligou":
  1. **Postgres e RabbitMQ** iniciam primeiro. O Docker executa um *Healthcheck* que fica perguntando: "Já aceitam conexões?".
  2. O **FastAPI (Backend)** só é iniciado depois que o banco e a fila devolvem o sinal verde (Healthy).
  3. O **BFF** só inicia quando o FastAPI estiver saudável e respondendo sua rota `/health`.
  4. O **Frontend** liga atrelado ao BFF.

Isso previne o clássico problema da aplicação "dar crash" ao iniciar porque tentou se conectar no banco de dados enquanto ele ainda estava ligando seus arquivos na memória. Quando o terminal diz que todos estão no ar, é porque toda a esteira concluiu com sucesso!
