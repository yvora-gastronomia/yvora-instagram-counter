# Checklist Meta Instagram API

## Situação atual

A Página do Facebook foi encontrada no Graph API Explorer:

```env
PAGE_ID=1132788549914321
```

A consulta abaixo retornou apenas o ID da página, sem `instagram_business_account`:

```text
1132788549914321?fields=instagram_business_account,connected_instagram_account
```

Retorno observado:

```json
{
  "id": "1132788549914321"
}
```

Isso indica que a API ainda não está conseguindo enxergar a conta Instagram Business conectada à Página.

## Diagnóstico pelo Business Suite

Na tela atual do Meta Business Suite, a Página YVORA aparece corretamente em:

```text
Configurações > Contas > Páginas
```

Página encontrada:

```env
PAGE_NAME=YVORA
PAGE_ID=1132788549914321
BUSINESS_ID=1670523267724041
```

O próximo ponto de checagem é a aba **Ativos conectados** dentro da Página YVORA.

## Próximo passo na tela atual

1. Com a Página YVORA selecionada, clicar em **Ativos conectados**.
2. Verificar se aparece `yvora.restaurante` como Instagram conectado.
3. Se não aparecer, clicar em **Conectar ativos**.
4. Selecionar a conta do Instagram `yvora.restaurante`.
5. Confirmar a conexão com a Página YVORA.
6. Depois ir em **Pessoas** e confirmar que o usuário que gera o token tem controle total.

## Também conferir Contas do Instagram

Caminho:

```text
Configurações > Contas > Contas do Instagram
```

Validar:

1. `yvora.restaurante` aparece na lista.
2. Está no mesmo portfólio empresarial `Yvora`.
3. A Página conectada é `YVORA`.
4. O usuário administrador tem controle total.

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
1132788549914321?fields=name,instagram_business_account,connected_instagram_account
```

3. Tentar pelo Business ID:

```text
1670523267724041/owned_instagram_accounts?fields=id,username,followers_count
```

4. Se retornar o Instagram Business ID, testar:

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
