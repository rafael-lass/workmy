const express = require('express');
const cookieParser = require('cookie-parser');
const cors = require('cors');
const http = require('http');
const https = require('https');

const app = express();
const PORT = process.env.PORT || 3000;
const FASTAPI_URL = process.env.FASTAPI_URL || 'http://127.0.0.1:8000';
const IS_PRODUCTION = process.env.NODE_ENV === 'production';

// ---------------------------------------------------------------------------
// Extrai hostname, porta e protocolo de FASTAPI_URL uma única vez.
// FIX C3: Todas as chamadas http.request usam esses valores — sem hardcode.
// ---------------------------------------------------------------------------
const _fastapiParsed = new URL(FASTAPI_URL);
const FASTAPI_HOSTNAME = _fastapiParsed.hostname;
const FASTAPI_PORT = _fastapiParsed.port
    ? parseInt(_fastapiParsed.port, 10)
    : (_fastapiParsed.protocol === 'https:' ? 443 : 80);
const FASTAPI_PROTOCOL = _fastapiParsed.protocol === 'https:' ? https : http;

// ---------------------------------------------------------------------------
// FIX A7: CORS com whitelist explícita de origens.
// Configure CORS_ORIGIN=https://app.workmy.com em produção.
// ---------------------------------------------------------------------------
const CORS_ORIGIN = process.env.CORS_ORIGIN || 'http://localhost:5173';
const ALLOWED_ORIGINS = CORS_ORIGIN.split(',').map(o => o.trim()).filter(Boolean);

// Em desenvolvimento, aceita qualquer origem localhost (qualquer porta do Vite)
// Em produção, usa apenas a whitelist de CORS_ORIGIN
const isLocalhostOrigin = (origin) =>
    /^https?:\/\/localhost(:\d+)?$/.test(origin) ||
    /^https?:\/\/127\.0\.0\.1(:\d+)?$/.test(origin);

app.use(cookieParser());
app.use(cors({
    origin: (origin, callback) => {
        // Permite requests sem Origin (ex: curl, Postman, SSR)
        if (!origin) return callback(null, true);
        // Dev: aceita qualquer localhost independente da porta
        if (!IS_PRODUCTION && isLocalhostOrigin(origin)) {
            return callback(null, true);
        }
        // Produção: apenas origens da whitelist
        if (ALLOWED_ORIGINS.includes(origin)) {
            return callback(null, true);
        }
        callback(new Error(`Origem bloqueada pelo BFF CORS: ${origin}`));
    },
    credentials: true
}));

// Uma imagem de 5 MB cresce ao virar base64; 8 MB cobre o payload sem aceitar
// corpos desnecessariamente grandes.
app.use(express.json({ limit: '8mb' }));
app.use(express.urlencoded({ limit: '8mb', extended: true }));

app.get('/health', (_req, res) => res.status(200).json({ status: 'healthy' }));

// ---------------------------------------------------------------------------
// FIX A8: Opções de cookie centralizadas — secure é dinâmico por ambiente.
// ---------------------------------------------------------------------------
const COOKIE_OPTS_ACCESS = {
    httpOnly: true,
    secure: IS_PRODUCTION,           // true em produção (HTTPS), false em dev
    sameSite: IS_PRODUCTION ? 'strict' : 'lax',
    maxAge: 14 * 60 * 1000,         // expira pouco antes do JWT de 15 minutos
    path: '/'
};

const COOKIE_OPTS_REFRESH = {
    httpOnly: true,
    secure: IS_PRODUCTION,
    sameSite: IS_PRODUCTION ? 'strict' : 'lax',
    maxAge: 7 * 24 * 60 * 60 * 1000, // 7 dias
    path: '/'
};

function logBffAction(layer, action, detail) {
    console.log(`\x1b[36m[BFF]\x1b[0m \x1b[32m${layer}\x1b[0m -> ${action} | \x1b[90m${detail}\x1b[0m`);
}

// ---------------------------------------------------------------------------
// Helper: faz uma chamada HTTP/HTTPS ao FastAPI sem transformar a resposta.
// O corpo permanece como Buffer para suportar JSON, PDF e outros binários.
// FIX C3: Usa FASTAPI_HOSTNAME e FASTAPI_PORT extraídos de FASTAPI_URL.
// ---------------------------------------------------------------------------
function callFastApi(path, method, data = null, extraHeaders = {}) {
    return new Promise((resolve, reject) => {
        const hasBody = data !== null && data !== undefined && method !== 'GET' && method !== 'HEAD';
        const postData = hasBody ? JSON.stringify(data) : '';
        
        const options = {
            hostname: FASTAPI_HOSTNAME,
            port: FASTAPI_PORT,
            path,
            method,
            headers: { ...extraHeaders }
        };

        if (hasBody) {
            options.headers['Content-Type'] = 'application/json';
            options.headers['Content-Length'] = Buffer.byteLength(postData);
        }

        const req = FASTAPI_PROTOCOL.request(options, (apiRes) => {
            const chunks = [];
            apiRes.on('data', (chunk) => chunks.push(Buffer.from(chunk)));
            apiRes.on('end', () => {
                resolve({
                    status: apiRes.statusCode || 502,
                    body: Buffer.concat(chunks),
                    headers: apiRes.headers
                });
            });
        });

        req.on('error', reject);
        req.setTimeout(15000, () => req.destroy(new Error('FastAPI não respondeu em 15 segundos.')));
        if (hasBody) {
            req.write(postData);
        }
        req.end();
    });
}

function parseJsonResponse(body) {
    if (!body.length) return null;

    const text = body.toString('utf8');
    try {
        return JSON.parse(text);
    } catch {
        return text;
    }
}

const HOP_BY_HOP_HEADERS = new Set([
    'connection',
    'keep-alive',
    'proxy-authenticate',
    'proxy-authorization',
    'te',
    'trailer',
    'transfer-encoding',
    'upgrade'
]);

function forwardResponseHeaders(res, headers) {
    for (const [name, value] of Object.entries(headers)) {
        const normalizedName = name.toLowerCase();
        if (
            value === undefined ||
            HOP_BY_HOP_HEADERS.has(normalizedName) ||
            normalizedName === 'set-cookie' ||
            normalizedName.startsWith('access-control-')
        ) {
            continue;
        }
        res.setHeader(name, value);
    }
}

// Helper para gravar par de cookies de sessão
function setSessionCookies(res, accessToken, refreshToken) {
    res.cookie('workmy_access', accessToken, COOKIE_OPTS_ACCESS);
    res.cookie('workmy_refresh', refreshToken, COOKIE_OPTS_REFRESH);
}

// Helper para limpar cookies de sessão
function clearSessionCookies(res) {
    const clearOptions = {
        path: '/',
        secure: IS_PRODUCTION,
        sameSite: IS_PRODUCTION ? 'strict' : 'lax'
    };
    res.clearCookie('workmy_access', clearOptions);
    res.clearCookie('workmy_refresh', clearOptions);
}

async function refreshAccessToken(refreshToken) {
    if (!refreshToken) return null;
    const { status, body: responseBody } = await callFastApi(
        '/api/auth/refresh',
        'POST',
        { refresh: refreshToken }
    );
    if (status !== 200) return null;
    const body = parseJsonResponse(responseBody);
    return body && typeof body.access === 'string' ? body.access : null;
}

// ============================================================
// 1. ENDPOINT DE LOGIN (INTERCEPTADO)
// ============================================================
app.post('/api/auth/login', async (req, res) => {
    logBffAction('Auth Gateway', 'POST /api/auth/login', 'Iniciando autenticação...');

    try {
        const { status, body: responseBody } = await callFastApi('/api/auth/login', 'POST', {
            email: req.body.username || req.body.email,
            password: req.body.password
        });
        const body = parseJsonResponse(responseBody);

        if (status === 200) {
            const { access, refresh, user } = body;
            setSessionCookies(res, access, refresh);
            logBffAction('Auth Gateway', 'Cookies Set', `Sessão criada para ${user.username}`);
            // Retorna apenas dados públicos — tokens ficam nos cookies HTTP-Only
            return res.status(200).json({ user });
        }

        return res.status(status).json(body);
    } catch (err) {
        logBffAction('Auth Gateway', 'Connection Error', err.message);
        return res.status(502).json({ detail: 'Erro de conexão com o Core Service FastAPI.' });
    }
});

// ============================================================
// 2. ENDPOINT DE CADASTRO (INTERCEPTADO)
// ============================================================
app.post('/api/auth/register', async (req, res) => {
    logBffAction('Auth Gateway', 'POST /api/auth/register', 'Iniciando registro...');

    try {
        const { status, body: responseBody } = await callFastApi('/api/auth/register', 'POST', req.body);
        const body = parseJsonResponse(responseBody);

        if (status === 200) {
            const { access, refresh, user } = body;
            setSessionCookies(res, access, refresh);
            logBffAction('Auth Gateway', 'Register OK', `Novo usuário: ${user.username}`);
            return res.status(200).json({ user });
        }

        return res.status(status).json(body);
    } catch (err) {
        logBffAction('Auth Gateway', 'Connection Error', err.message);
        return res.status(502).json({ detail: 'Erro de conexão com o Core Service FastAPI.' });
    }
});

// ============================================================
// 3. ENDPOINT DE LOGOUT (INTERCEPTADO)
// FIX C5: Encaminha o access token ao FastAPI para revogar o JTI na blacklist.
// ============================================================
app.post('/api/auth/logout', async (req, res) => {
    logBffAction('Auth Gateway', 'POST /api/auth/logout', 'Encerrando sessão...');

    const accessToken = req.cookies.workmy_access;

    // Revoga o token na blacklist do FastAPI (best-effort)
    if (accessToken) {
        try {
            await callFastApi('/api/auth/logout', 'POST', {}, {
                Authorization: `Bearer ${accessToken}`
            });
            logBffAction('Auth Gateway', 'Token Revoked', 'JTI revogado na blacklist do FastAPI');
        } catch (err) {
            logBffAction('Auth Gateway', 'Revoke Warning', `Não foi possível revogar: ${err.message}`);
        }
    }

    clearSessionCookies(res);
    logBffAction('Auth Gateway', 'Logout Complete', 'Cookies limpos. Sessão destruída.');
    return res.status(200).json({ message: 'Sessão encerrada com sucesso.' });
});

// ============================================================
// 4. MIDDLEWARE DE SEGURANÇA — PROXY DE ROTAS DE NEGÓCIO /api/*
// Injeta Bearer JWT nos cookies antes de encaminhar ao FastAPI.
// Executa Silent Refresh automático se access expirou mas refresh é válido.
// ============================================================
app.use(async (req, res, next) => {
    // Só intercepta rotas que começam com /api
    if (!req.path.startsWith('/api')) {
        return next();
    }

    // Ignora rotas de autenticação locais do BFF e health checks públicos
    if (
        req.path.startsWith('/api/auth/login') ||
        req.path.startsWith('/api/auth/register') ||
        req.path.startsWith('/api/auth/logout') ||
        req.path.startsWith('/api/health/ping')
    ) {
        return next();
    }

    const accessToken = req.cookies.workmy_access;
    const refreshToken = req.cookies.workmy_refresh;

    // Sem nenhum cookie — bloqueia imediatamente
    if (!accessToken && !refreshToken) {
        logBffAction('Proxy Security', 'Access Denied', 'Nenhum cookie de sessão encontrado.');
        return res.status(401).json({ detail: 'Acesso negado. Por favor, faça login.' });
    }

    // Access expirou mas refresh ainda é válido — Silent Refresh automático
    if (!accessToken && refreshToken) {
        logBffAction('Proxy Security', 'Silent Refresh', 'Access Token expirou. Renovando...');

        try {
            const newAccess = await refreshAccessToken(refreshToken);

            if (newAccess) {
                res.cookie('workmy_access', newAccess, COOKIE_OPTS_ACCESS);
                req.headers['authorization'] = `Bearer ${newAccess}`;
                logBffAction('Proxy Security', 'Silent Refresh OK', 'Novo Access Token gerado.');
                return next();
            }

            // Refresh inválido — limpa cookies e força re-login
            logBffAction('Proxy Security', 'Refresh Failed', 'Refresh token inválido ou expirado.');
            clearSessionCookies(res);
            return res.status(401).json({ detail: 'Sessão expirada. Por favor, logue novamente.' });
        } catch (err) {
            logBffAction('Proxy Security', 'Refresh Error', err.message);
            clearSessionCookies(res);
            return res.status(502).json({ detail: 'Erro ao renovar sessão.' });
        }
    }

    // Fluxo normal — injeta o Bearer JWT no header antes de encaminhar
    logBffAction('Proxy Security', `${req.method} ${req.path}`, 'Injetando Bearer JWT');
    req.headers['authorization'] = `Bearer ${accessToken}`;
    next();
});

// ============================================================
// 5. PROXY GENÉRICO MANUAL (Para todas as rotas /api/*)
// Implementação direta para evitar conflitos com body-parser.
// ============================================================
app.all(/^\/api\/.*$/, async (req, res) => {
    try {
        const urlPath = req.originalUrl;
        const method = req.method;
        const body = (method !== 'GET' && method !== 'HEAD') ? req.body : null;

        // Limpa headers conflitantes
        const headersToForward = { ...req.headers };
        delete headersToForward.host;
        delete headersToForward['content-length'];

        let upstream = await callFastApi(
            urlPath,
            method,
            body,
            headersToForward
        );

        // O cookie pode existir enquanto o JWT já expirou. Renova e repete a
        // requisição uma única vez para não surpreender o usuário após 15 min.
        if (upstream.status === 401 && req.cookies.workmy_refresh) {
            const newAccess = await refreshAccessToken(req.cookies.workmy_refresh);
            if (newAccess) {
                res.cookie('workmy_access', newAccess, COOKIE_OPTS_ACCESS);
                headersToForward.authorization = `Bearer ${newAccess}`;
                upstream = await callFastApi(urlPath, method, body, headersToForward);
            } else {
                clearSessionCookies(res);
            }
        }

        const { status, body: responseBody, headers: responseHeaders } = upstream;
        
        logBffAction('Proxy', `${method} ${urlPath}`, `FastAPI respondeu ${status}`);
        forwardResponseHeaders(res, responseHeaders);

        if (method === 'HEAD' || status === 204 || status === 304) {
            return res.status(status).end();
        }

        return res.status(status).send(responseBody);
    } catch (err) {
        logBffAction('Manual Proxy', 'Error', err.message);
        return res.status(502).json({ detail: 'Erro de proxy interno.' });
    }
});

// ============================================================
// Startup
// ============================================================
app.listen(PORT, () => {
    console.log(`\n\x1b[36m==================================================\x1b[0m`);
    console.log(`\x1b[36m  WORKMY BFF PROXY GATEWAY\x1b[0m`);
    console.log(`\x1b[36m  Porta:    http://localhost:${PORT}\x1b[0m`);
    console.log(`\x1b[36m  FastAPI:  ${FASTAPI_URL}\x1b[0m`);
    console.log(`\x1b[36m  CORS:     ${ALLOWED_ORIGINS.join(', ')}\x1b[0m`);
    console.log(`\x1b[36m  Ambiente: ${IS_PRODUCTION ? 'PRODUÇÃO' : 'DESENVOLVIMENTO'}\x1b[0m`);
    console.log(`\x1b[36m==================================================\x1b[0m\n`);
});
