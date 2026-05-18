# Checklist Meta Instagram API

## Situação atual

A Página do Facebook foi encontrada no Graph API Explorer:

```env
PAGE_ID=1132788549914321
```

A consulta abaixo retornou apenas o ID da página, sem `instagram_business_account`:

```text
1132788549914321?fields=instagram_business_account
```

Retorno observado:

```json
{
  "id": "1132788549914321"
}
```

Isso indica que o token/app ainda não está conseguindo enxergar a conta Instagram Business conectada à Página.

## Próximos ajustes necessários no Meta Business Suite

1. Entrar no Meta Business Suite.
2. Ir em Configurações.
3. Ir em Contas.
4. Conferir em Páginas se a Página YVORA aparece.
5. Conferir em Contas do Instagram se `yvora.restaurante` aparece.
6. Entrar na conta do Instagram `yvora.restaurante`.
7. Confirmar se ela está atribuída à mesma Página YVORA.
8. Confirmar se o usuário que gerou o token tem controle total da Página e do Instagram.

## Permissões recomendadas no Graph API Explorer

Adicionar ao token:

```text
pages_show_list
pages_read_engagement
business_management
instagram_basic
instagram_manage_insights
```

Depois gerar o token novamente.

## Consultas para repetir

1. Confirmar páginas:

```text
me/accounts
```

2. Testar Instagram conectado:

```text
1132788549914321?fields=instagram_business_account,connected_instagram_account
```

3. Se retornar o Instagram Business ID, testar:

```text
IG_BUSINESS_ID?fields=username,followers_count,media_count
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
