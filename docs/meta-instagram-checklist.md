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

No Graph API Explorer, foi possível adicionar:

```text
pages_show_list
pages_read_engagement
business_management
instagram_basic
```

Mas `instagram_manage_insights` não aparece como opção disponível para esse app/token.

## Decisão operacional

Para este app, o campo principal necessário é `followers_count`, que pode ser testado com `instagram_basic` quando a conta é Instagram profissional conectada à Página.

Portanto, o próximo passo é seguir sem `instagram_manage_insights` e gerar um novo token com as permissões disponíveis.

## Próximo passo no Graph API Explorer

1. Manter selecionadas as permissões disponíveis:

```text
pages_show_list
pages_read_engagement
business_management
instagram_basic
```

2. Clicar em **Generate Access Token** novamente.
3. Autorizar a Página YVORA e o Instagram `yvora.restaurante` se aparecerem na janela de autorização.

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

## Se ainda não retornar o Instagram

Verificar no painel do app:

```text
Casos de uso > Login do Facebook para Empresas
```

ou adicionar um caso de uso relacionado a Instagram/Business Login, porque algumas telas novas da Meta escondem permissões por caso de uso.

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
