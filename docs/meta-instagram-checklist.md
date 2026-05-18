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

No Graph API Explorer, o token atual permite:

```text
pages_show_list
pages_read_engagement
business_management
```

Mas a interface não está permitindo manter/adicionar `instagram_basic` no token atual. Isso indica que o app ainda não possui um caso de uso/produto do Instagram habilitado, ou que o Graph API Explorer está preso em um tipo de token que não aceita essa permissão.

## Próximo passo: habilitar caso de uso do Instagram no app

No painel do app `YVORA Social Wall`, verificar:

```text
Casos de uso
```

Adicionar um caso de uso relacionado a um destes nomes, conforme disponível na interface da Meta:

```text
Instagram Graph API
Business Login
Login do Facebook para Empresas
Gerenciar ativos empresariais
```

Depois voltar ao Graph API Explorer e tentar adicionar novamente:

```text
instagram_basic
```

## Alternativa se a permissão continuar indisponível

Tentar trocar o tipo em:

```text
Usuário ou Página
```

De `Token do usuário` para a Página `YVORA`, se a opção aparecer. Depois gerar token novamente.

## Consultas para repetir quando `instagram_basic` estiver no token

1. Confirmar páginas:

```text
me/accounts
```

2. Testar Instagram conectado pela Página:

```text
1132788549914321?fields=name,instagram_business_account,connected_instagram_account
```

3. Tentar pelo Business ID:

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
