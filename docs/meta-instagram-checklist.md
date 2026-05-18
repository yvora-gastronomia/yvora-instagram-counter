# Checklist Meta Instagram API

## Situação atual

A Página do Facebook foi encontrada no Graph API Explorer:

```env
PAGE_ID=1132788549914321
BUSINESS_ID=1670523267724041
```

A conexão visual no Meta Business Suite foi confirmada:

```text
Configurações > Contas > Páginas > YVORA > Ativos conectados
```

Ativo conectado encontrado:

```env
INSTAGRAM_USERNAME=yvora.restaurante
```

Isso confirma que a Página YVORA possui a conta do Instagram conectada no Business Suite. O próximo passo é gerar novo token com permissões completas e repetir a consulta na Graph API.

## Próximo passo no Graph API Explorer

1. Voltar ao Graph API Explorer.
2. Garantir que o app selecionado é `YVORA Social Wall`.
3. Adicionar as permissões:

```text
pages_show_list
pages_read_engagement
business_management
instagram_basic
instagram_manage_insights
```

4. Clicar em **Generate Access Token** novamente.
5. Autorizar a Página YVORA e o Instagram `yvora.restaurante`.

## Consultas para repetir

1. Confirmar páginas:

```text
me/accounts
```

2. Testar Instagram conectado pela Página:

```text
1132788549914321?fields=name,instagram_business_account,connected_instagram_account
```

3. Tentar pelo Business ID se a consulta da Página ainda não trouxer o Instagram:

```text
1670523267724041/owned_instagram_accounts?fields=id,username,followers_count
```

4. Alternativa:

```text
1670523267724041/client_instagram_accounts?fields=id,username
```

5. Quando retornar o Instagram Business ID, testar:

```text
IG_BUSINESS_ID?fields=username,followers_count,media_count
```

O retorno esperado é:

```json
{
  "username": "yvora.restaurante",
  "followers_count": 19300,
  "media_count": 0,
  "id": "1784..."
}
```

## Variáveis finais para deploy

Quando funcionar, configurar no Render:

```env
PROFILE_URL=https://www.instagram.com/yvora.restaurante/
IG_BUSINESS_ID=INSERIR_ID_AQUI
USER_ACCESS_TOKEN=INSERIR_TOKEN_AQUI
GRAPH_VERSION=v25.0
MILESTONE_TARGET=20000
BRAND_NAME=YVORA
BRAND_SUBTITLE=Carnes, queijos e vinhos em uma jornada sensorial
FOLLOW_CTA=Explore o universo YVORA
MENU_SENSORIAL_URL=https://yvora-menu-sensorial.streamlit.app/
WINE_EXPLORER_URL=https://yvora-wine.streamlit.app/
```
