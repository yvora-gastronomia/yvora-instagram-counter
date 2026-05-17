# YVORA Instagram Counter

App Flask para exibir contador de seguidores do Instagram do YVORA em tela de restaurante, com QR Code e animação de taças de vinho quando o número de seguidores aumenta.

## O que foi adaptado

- Troca do perfil padrão do Liivv para YVORA.
- Textos e identidade visual ajustados para restaurante, vinhos, carnes e queijos.
- Quando o contador aumenta, sobem taças de vinho em vez de tesouras.
- Inclusão de rota vertical em `/vertical` para telas no formato retrato.
- Arquivos organizados para GitHub e deploy.

## Rodar localmente

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

Acesse `http://localhost:5000`.

## Variáveis de ambiente

Copie `.env.example` para `.env` e preencha:

- `PROFILE_URL`: URL do Instagram do YVORA.
- `IG_BUSINESS_ID`: ID da conta Instagram Business conectada à Meta.
- `USER_ACCESS_TOKEN`: token de acesso Meta com permissão de leitura.
- `MILESTONE_TARGET`: meta visual de seguidores.
- `MOCK_FOLLOWERS_START`: valor usado quando a API Meta não estiver configurada.

## Próximos passos

1. Confirmar o @ oficial do Instagram do YVORA e ajustar `PROFILE_URL`.
2. Criar/configurar Meta App, conectar Instagram Business e Página do Facebook.
3. Gerar `USER_ACCESS_TOKEN` válido e obter `IG_BUSINESS_ID`.
4. Configurar as variáveis de ambiente na plataforma de deploy.
5. Subir o repositório para `yvora-gastronomia/yvora-instagram-counter`.
6. Fazer deploy em Render, Railway, Fly.io ou outra plataforma Flask.
7. Abrir `/vertical` na tela do restaurante se o painel for em pé.

## Deploy sugerido

Start command:

```bash
gunicorn app:app --bind 0.0.0.0:$PORT
```
