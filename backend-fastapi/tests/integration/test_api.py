import pytest
import pytest_asyncio
import httpx
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from decimal import Decimal
from datetime import date, timedelta

from src.presentation.main import app
from src.infrastructure.persistence.session import get_db_session, Base
from src.infrastructure.persistence.models import UsuarioModel, ClienteModel, ServicoModel, ProjetoModel
from src.infrastructure.security.jwt_service import create_access_token

pytestmark = pytest.mark.asyncio


async def test_services_documents_tags_and_pdf_contract():
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        async def register(name):
            result = await client.post('/api/auth/register', json={"username": name, "email": f"{name}@example.com", "password": "strongpassword123"})
            return {"Authorization": f"Bearer {result.json()['access']}"}
        owner = await register('service_owner')
        other = await register('service_other')
        tag = (await client.post('/api/servicos/tags', headers=owner, json={"nome": "  Web   Design  "})).json()
        duplicate = (await client.post('/api/servicos/tags', headers=owner, json={"nome": "web design"})).json()
        assert tag == duplicate
        assert tag['nome'] == 'Web Design'
        assert (await client.get('/api/servicos/tags', headers=other)).json() == []
        document = {"version": 1, "doc": {"type": "doc", "content": [
            {"type": "heading", "attrs": {"level": 2}, "content": [{"type": "text", "text": "Sobre o serviço"}]},
            {"type": "paragraph", "content": [{"type": "text", "text": "Criação com atenção.", "marks": [{"type": "bold"}]}]},
        ]}}
        body = {"nome": "Apresentação profissional", "descricao_documento": document, "tag_ids": [tag['id']]}
        created = await client.post('/api/servicos/', headers=owner, json=body)
        assert created.status_code == 201, created.text
        service = created.json()
        assert service['descricao_documento'] == document
        assert service['tags'] == [tag]
        assert 'ferramentas' not in service and 'github_repo' not in service
        path = f"/api/servicos/{service['id']}"
        assert (await client.get(path, headers=owner)).json()['descricao_documento'] == document
        assert (await client.get(path, headers=other)).status_code == 404
        assert (await client.post('/api/servicos/', headers=other, json=body)).status_code == 400
        invalid = await client.post('/api/servicos/', headers=owner, json={**body, "tag_ids": list(range(11))})
        assert invalid.status_code == 422
        contact = {"nome_profissional": "João & Ana", "email": "contato@example.com"}
        assert (await client.post(path + '/pdf', headers=other, json=contact)).status_code == 404
        assert (await client.post(path + '/pdf', json=contact)).status_code == 401
        pdf = await client.post(path + '/pdf', headers=owner, json=contact)
        assert pdf.status_code == 200, pdf.text if pdf.status_code != 200 else ''
        assert pdf.content.startswith(b'%PDF-')
        assert pdf.headers['content-type'] == 'application/pdf'
        assert 'attachment;' in pdf.headers['content-disposition']
        assert (await client.put(path, headers=owner, json={**body, 'tag_ids': []})).json()['tags'] == []
        assert (await client.get('/api/servicos/tags', headers=owner)).json() == [tag]
        assert (await client.post('/api/servicos/', headers=owner, json={**body, 'nome': 'Outro serviço'})).json()['tags'] == [tag]

# Configura banco de dados SQLite assíncrono temporário para testes integrados
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
session_maker_test = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

# Override de dependência de sessão de banco para injetar banco de testes
async def override_get_db_session():
    async with session_maker_test() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

app.dependency_overrides[get_db_session] = override_get_db_session


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    """Recria as tabelas físicas no banco em memória antes de cada teste."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_fastapi_health_check():
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_fastapi_create_projeto_flow():
    # 1. Cria dados fictícios direto no banco de teste usando a sessão
    async with session_maker_test() as session:
        # Cria Usuário
        usuario = UsuarioModel(username="freela1", email="freela@gmail.com", password_hash="hash")
        session.add(usuario)
        await session.flush()
        
        # Cria Cliente
        cliente = ClienteModel(usuario_id=usuario.id, nome="Supermercado Ideal")
        session.add(cliente)
        
        # Cria Serviço
        servico = ServicoModel(usuario_id=usuario.id, nome="Landing Page")
        session.add(servico)
        
        await session.commit()
        
        usuario_id = usuario.id
        cliente_id = cliente.id
        servico_id = servico.id

    # 2. Gera token JWT de teste para o usuário criado
    token = create_access_token(usuario_id, "freela1", "freela@gmail.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Faz chamada de POST na rota autenticada da API usando AsyncClient
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "cliente_id": cliente_id,
            "servico_id": servico_id,
            "valor": 2500.00,
            "tipo_recorrencia": "MENSAL",
            "valor_mensal": 500.00,
            "dia_vencimento": 10
        }
        
        response = await client.post("/api/projetos/", json=payload, headers=headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 1
        assert data["tipo_recorrencia"] == "MENSAL"
        assert float(data["valor"]) == 2500.00
        assert float(data["valor_mensal"]) == 500.00
        assert data["dia_vencimento"] == 10
        
        assert "progresso" not in data
        path = f"/api/projetos/{data['id']}"
        async with session_maker_test() as session:
            model = await session.get(ProjetoModel, data['id'])
            model.progresso = 37  # Existing legacy data must survive all transitions.
            await session.commit()
        for stage in ["IN_PROGRESS", "REVIEW", "IN_PROGRESS", "REVIEW", "COMPLETED"]:
            changed = await client.patch(path + "/status", headers=headers, json={"status": stage})
            assert changed.status_code == 200, changed.text
            assert changed.json()["status"] == stage
            assert "progresso" not in changed.json()
        assert changed.json()["ativo"] is False
        resumed = await client.patch(path + "/recorrencia", headers=headers, json={
            "ativo": True, "valor_mensal": 500, "dia_vencimento": 10,
            "recorrencia_inicio": "2026-09-22",
        })
        assert resumed.status_code == 400
        invalid = await client.put(path, headers=headers, json={"progresso": 90})
        assert invalid.status_code == 422
        assert (await client.patch(path + "/status", headers=headers, json={"status": "ARCHIVED"})).status_code == 200
        assert (await client.patch(path + "/status", headers=headers, json={"status": "IN_PROGRESS"})).status_code == 400
        reactivated = await client.patch(path + "/status", headers=headers, json={"status": "DISCOVERY"})
        assert reactivated.status_code == 200
        assert reactivated.json()["ativo"] is False
        assert reactivated.json()["status"] == "DISCOVERY"
        assert "progresso" not in (await client.get(path, headers=headers)).json()
        assert all("progresso" not in item for item in (await client.get("/api/projetos/", headers=headers)).json())
        async with session_maker_test() as session:
            assert (await session.get(ProjetoModel, data['id'])).progresso == 37

        # 4. Tenta duplicar para forçar erro 400 de Colisão
        dup_response = await client.post("/api/projetos/", json=payload, headers=headers)
        assert dup_response.status_code == 400
        assert "Este cliente já possui este serviço contratado" in dup_response.json()["detail"]


@pytest.mark.asyncio
async def test_fastapi_auth_register_and_login_flow():
    """Testa de ponta a ponta o fluxo de cadastro, login, refresh e logout do usuário."""
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # 1. Registro Bem-sucedido
        register_payload = {
            "username": "tester123",
            "email": "tester123@example.com",
            "password": "strongpassword123",
            "telefone": "11999999999"
        }
        response = await client.post("/api/auth/register", json=register_payload)
        assert response.status_code == 200
        data = response.json()
        assert "access" in data
        assert "refresh" in data
        assert data["user"]["username"] == "tester123"
        assert data["user"]["email"] == "tester123@example.com"
        refresh_token = data["refresh"]

        # 2. Conflito por Nome de Usuário Duplicado
        dup_user_payload = {
            "username": "tester123",
            "email": "different@example.com",
            "password": "strongpassword123"
        }
        response_dup_user = await client.post("/api/auth/register", json=dup_user_payload)
        assert response_dup_user.status_code == 400
        assert "Nome de usuário já está em uso" in response_dup_user.json()["detail"]

        # 3. Conflito por E-mail Duplicado
        dup_email_payload = {
            "username": "different_user",
            "email": "tester123@example.com",
            "password": "strongpassword123"
        }
        response_dup_email = await client.post("/api/auth/register", json=dup_email_payload)
        assert response_dup_email.status_code == 400
        assert "E-mail já está cadastrado" in response_dup_email.json()["detail"]

        # 4. Login Bem-sucedido
        login_payload = {
            "email": "tester123",  # Testa login via username
            "password": "strongpassword123"
        }
        response_login = await client.post("/api/auth/login", json=login_payload)
        assert response_login.status_code == 200
        login_data = response_login.json()
        assert "access" in login_data
        assert login_data["user"]["email"] == "tester123@example.com"

        # 5. Login Falho (Senha Incorreta)
        bad_login_payload = {
            "email": "tester123",
            "password": "wrongpassword"
        }
        response_bad_login = await client.post("/api/auth/login", json=bad_login_payload)
        assert response_bad_login.status_code == 401
        assert "Senha incorreta" in response_bad_login.json()["detail"]

        # 6. Silent Refresh
        refresh_payload = {
            "refresh": refresh_token
        }
        response_refresh = await client.post("/api/auth/refresh", json=refresh_payload)
        assert response_refresh.status_code == 200
        assert "access" in response_refresh.json()

        # 7. Logout
        logout_headers = {"Authorization": f"Bearer {login_data['access']}"}
        response_me = await client.get("/api/auth/me", headers=logout_headers)
        assert response_me.status_code == 200
        assert response_me.json()["username"] == "tester123"

        response_logout = await client.post("/api/auth/logout", headers=logout_headers)
        assert response_logout.status_code == 200
        assert "message" in response_logout.json()


@pytest.mark.asyncio
async def test_fastapi_project_list_get_delete_flow():
    """Testa a listagem, detalhe e deleção suave (soft delete) de projetos."""
    # 1. Popula banco com dados fictícios para teste
    async with session_maker_test() as session:
        usuario = UsuarioModel(username="project_tester", email="project_tester@example.com", password_hash="hash")
        session.add(usuario)
        await session.flush()
        
        cliente = ClienteModel(usuario_id=usuario.id, nome="Cliente Teste SA")
        session.add(cliente)
        
        servico = ServicoModel(usuario_id=usuario.id, nome="Desenvolvimento Web")
        session.add(servico)
        
        await session.commit()
        
        usuario_id = usuario.id
        cliente_id = cliente.id
        servico_id = servico.id

    # 2. Cria projeto inicial via API
    token = create_access_token(usuario_id, "project_tester", "project_tester@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Criação do Projeto
        payload = {
            "cliente_id": cliente_id,
            "servico_id": servico_id,
            "valor": 1500.00,
            "tipo_recorrencia": "AVULSO"
        }
        resp_create = await client.post("/api/projetos/", json=payload, headers=headers)
        assert resp_create.status_code == 201
        projeto_id = resp_create.json()["id"]

        # 3. Listagem de Projetos
        resp_list = await client.get("/api/projetos/", headers=headers)
        assert resp_list.status_code == 200
        projetos = resp_list.json()
        assert len(projetos) == 1
        assert projetos[0]["id"] == projeto_id
        assert projetos[0]["cliente_nome"] == "Cliente Teste SA"
        assert projetos[0]["servico_nome"] == "Desenvolvimento Web"

        # 4. Detalhe do Projeto (ID Válido)
        resp_detail = await client.get(f"/api/projetos/{projeto_id}", headers=headers)
        assert resp_detail.status_code == 200
        assert resp_detail.json()["id"] == projeto_id

        # 5. Detalhe do Projeto (ID Inválido)
        resp_detail_invalid = await client.get("/api/projetos/9999", headers=headers)
        assert resp_detail_invalid.status_code == 404

        # 6. Deleção Suave (Soft Delete) do Projeto
        resp_delete = await client.delete(f"/api/projetos/{projeto_id}", headers=headers)
        assert resp_delete.status_code == 200
        assert "sucesso" in resp_delete.json()["message"]

        # 7. Detalhe pós-deleção suave deve retornar 404 pois está deletado logicamente
        resp_detail_post_delete = await client.get(f"/api/projetos/{projeto_id}", headers=headers)
        assert resp_detail_post_delete.status_code == 404


@pytest.mark.asyncio
async def test_payment_and_recurring_billing_contract():
    async with session_maker_test() as session:
        usuario = UsuarioModel(
            username="billing_tester",
            email="billing_tester@example.com",
            password_hash="hash",
        )
        session.add(usuario)
        await session.flush()
        cliente = ClienteModel(usuario_id=usuario.id, nome="Cliente Financeiro")
        servico = ServicoModel(usuario_id=usuario.id, nome="Suporte Mensal")
        session.add_all([cliente, servico])
        await session.commit()
        usuario_id, cliente_id, servico_id = usuario.id, cliente.id, servico.id

    token = create_access_token(usuario_id, usuario.username, usuario.email)
    headers = {"Authorization": f"Bearer {token}"}
    today = date.today()
    start_index = today.year * 12 + today.month - 1 - 2
    recurring_start = date(start_index // 12, start_index % 12 + 1, 1)

    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        projeto_response = await client.post(
            "/api/projetos/",
            headers=headers,
            json={
                "cliente_id": cliente_id,
                "servico_id": servico_id,
                "tipo_recorrencia": "MENSAL",
                "ativo": True,
                "valor_mensal": "300.00",
                "dia_vencimento": 1,
                "recorrencia_inicio": recurring_start.isoformat(),
            },
        )
        assert projeto_response.status_code == 201
        projeto_id = projeto_response.json()["id"]

        invalid_manual = await client.post(
            "/api/pagamentos/",
            headers=headers,
            json={
                "projeto_id": projeto_id,
                "valor": "50.00",
                "data_pagamento": today.isoformat(),
                "tipo_pagamento": "MENSAL",
            },
        )
        assert invalid_manual.status_code == 422

        manual = await client.post(
            "/api/pagamentos/",
            headers=headers,
            json={
                "projeto_id": projeto_id,
                "valor": "50.00",
                "data_pagamento": today.isoformat(),
                "observacao": "Ajuste pontual",
            },
        )
        assert manual.status_code == 201
        assert manual.json()["cliente_id"] == cliente_id
        assert manual.json()["tipo_pagamento"] == "AVULSO"
        assert manual.json()["status"] == "PAGO"

        removed_put = await client.put(
            f"/api/pagamentos/{manual.json()['id']}",
            headers=headers,
            json={"valor": "75.00", "observacao": "Valor corrigido"},
        )
        assert removed_put.status_code in {404, 405}

        immutable = await client.patch(
            f"/api/pagamentos/{manual.json()['id']}/detalhes",
            headers=headers,
            json={"valor": "75.00"},
        )
        assert immutable.status_code == 422

        updated = await client.patch(
            f"/api/pagamentos/{manual.json()['id']}/detalhes",
            headers=headers,
            json={"observacao": "Detalhes corrigidos"},
        )
        assert updated.status_code == 200
        assert updated.json()["valor"] == "50.00"
        assert updated.json()["observacao"] == "Detalhes corrigidos"

        first_billing = await client.post(
            "/api/faturamento/recorrencias",
            headers=headers,
            json={"data_referencia": today.isoformat()},
        )
        assert first_billing.status_code == 200
        assert first_billing.json()["pagamentos_gerados"] == 3
        assert first_billing.json()["valor_total"] == "900.00"

        repeated_billing = await client.post(
            "/api/faturamento/recorrencias",
            headers=headers,
            json={"data_referencia": today.isoformat()},
        )
        assert repeated_billing.status_code == 200
        assert repeated_billing.json()["pagamentos_gerados"] == 0

        payments = await client.get("/api/pagamentos/", headers=headers)
        assert payments.status_code == 200
        assert payments.json()["total"] == 4
        monthlies = [
            payment
            for payment in payments.json()["items"]
            if payment["tipo_pagamento"] == "MENSAL"
        ]
        assert len(monthlies) == 3
        assert all(payment["status"] == "PENDENTE" for payment in monthlies)

        received = await client.patch(
            f"/api/pagamentos/{monthlies[0]['id']}/receber",
            headers=headers,
            json={"data_pagamento": today.isoformat()},
        )
        assert received.status_code == 200
        assert received.json()["status"] == "PAGO"

        cancelled = await client.patch(
            f"/api/pagamentos/{monthlies[1]['id']}/cancelar",
            headers=headers,
            json={"motivo": "Contrato suspenso"},
        )
        assert cancelled.status_code == 200
        assert cancelled.json()["status"] == "CANCELADO"

        reversed_payment = await client.patch(
            f"/api/pagamentos/{monthlies[0]['id']}/estornar",
            headers=headers,
            json={"motivo": "Cobrança indevida"},
        )
        assert reversed_payment.status_code == 200
        assert reversed_payment.json()["status"] == "ESTORNADO"

        terminal_transition = await client.patch(
            f"/api/pagamentos/{monthlies[1]['id']}/receber",
            headers=headers,
            json={"data_pagamento": today.isoformat()},
        )
        assert terminal_transition.status_code == 400

        dashboard = await client.get("/api/dashboard/resumo", headers=headers)
        assert dashboard.status_code == 200
        assert dashboard.json()["recebido_mes"] == "50.00"
        assert dashboard.json()["pendente_total"] == "300.00"

        projeto = await client.get(f"/api/projetos/{projeto_id}", headers=headers)
        assert projeto.json()["total_acumulado"] == "50.00"
        assert projeto.json()["possui_lancamentos"] is True

        protected_delete = await client.delete(f"/api/projetos/{projeto_id}", headers=headers)
        assert protected_delete.status_code == 409

        future = await client.post(
            "/api/faturamento/recorrencias",
            headers=headers,
            json={"data_referencia": (today + timedelta(days=1)).isoformat()},
        )
        assert future.status_code == 400

