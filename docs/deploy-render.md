# Publicação no Render: recarregamento e recuperação de senha

## Recarregar rotas internas

O frontend usa `HashRouter`: rotas aparecem após `#` (por exemplo, `/#/caixinhas`) e o navegador sempre solicita o documento da raiz ao atualizar. Isso evita o 404 de deep links que ocorre quando o host estático não faz fallback para `index.html`.

Se preferir manter URLs sem `#`, configure no serviço **Static Site** do Render uma regra **Rewrite** com:

- **Source:** `/*`
- **Destination:** `/index.html`

Não use Redirect: a regra precisa servir `index.html` sem trocar a URL. A regra é configurada em **Redirects/Rewrites** no Dashboard do Render. A documentação oficial descreve o fallback para frameworks com roteamento no cliente: <https://render.com/docs/redirects-rewrites>.

## E-mail para recuperar senha

A recuperação envia um link aleatório, de uso único, válido por 30 minutos. O token é armazenado no banco somente em forma de hash e as sessões anteriores são invalidadas quando a senha é redefinida.

No serviço **Web Service** do backend, adicione as variáveis abaixo em **Environment**. Não coloque credenciais de e-mail no frontend nem no Git:

```env
APP_ENV=production
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=seu-email@gmail.com
MAIL_PASSWORD=senha-de-app-do-email
MAIL_DEFAULT_SENDER=seu-email@gmail.com
MAIL_USE_TLS=true
FRONTEND_URL=https://endereco-do-seu-site-no-render
```

`MAIL_PASSWORD` deve ser uma credencial SMTP apropriada, como uma senha de app quando o provedor exigir. Nunca use a senha normal da sua conta de e-mail no repositório. `FRONTEND_URL` deve ser a origem pública do frontend, sem caminho final.

Depois de adicionar a migration, execute no backend:

```bash
flask --app wsgi db upgrade
```

No projeto publicado, faça isso como **Pre-Deploy Command** do serviço Web do backend ou execute a migration antes de testar a nova versão. O ambiente de desenvolvimento/teste pode expor o link de redefinição apenas quando `PASSWORD_RESET_DEBUG=true`; a configuração de produção mantém isso desativado.

A resposta da solicitação de redefinição é igual exista ou não uma conta para o e-mail informado. Isso evita revelar quais endereços estão cadastrados.
