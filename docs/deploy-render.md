# Publicação no Render: rotas, e-mail e segurança da conta

## Atualizar páginas internas

O frontend usa `HashRouter`. As rotas aparecem após `#`, por exemplo `/#/caixinhas`; ao atualizar, o navegador solicita a raiz do site e não uma URL interna. Isso evita o erro de deep link no Static Site.

Se preferir URLs sem `#`, configure no serviço **Static Site** do Render uma regra **Rewrite** de `/*` para `/index.html`. Não use Redirect. O Render explica essa regra na [documentação de redirects e rewrites](https://render.com/docs/redirects-rewrites).

## E-mail sem domínio próprio: Brevo por HTTPS

O backend envia e-mails pela API HTTPS da Brevo, não por SMTP. O Render bloqueia conexões de saída nas portas SMTP `25`, `465` e `587` nos Web Services gratuitos; por isso, a integração usa HTTPS.[Render: bloqueio de SMTP em Web Services gratuitos](https://render.com/changelog/free-web-services-will-no-longer-allow-outbound-traffic-to-smtp-ports)

Para começar sem configurar DNS, crie uma conta na Brevo, cadastre um endereço de e-mail que você consiga acessar e confirme o código de verificação enviado para essa caixa. Depois, crie uma API key e configure o envio transacional, que pode exigir ativação da conta. A API oficial usa a chave no cabeçalho `api-key` e o endpoint transacional documentado pela [Brevo](https://developers.brevo.com/docs/send-a-transactional-email).

No serviço **Web Service** do backend do Render, configure em **Environment**:

```env
APP_ENV=production
BREVO_API_KEY=sua_api_key_da_brevo
BREVO_FROM_EMAIL=seu-endereco-confirmado@exemplo.com
BREVO_FROM_NAME=Organizador Financeiro
FRONTEND_URL=https://organizador-financeiro-1-9lhc.onrender.com
PASSWORD_RESET_TOKEN_MINUTES=30
```

`BREVO_FROM_EMAIL` precisa ser o remetente confirmado na conta Brevo. A chave fica somente no backend; não a coloque no frontend, no repositório ou em mensagens de chat.

**Limite importante dessa solução sem domínio:** ela evita comprar um domínio e configurar registros DNS, mas não tem a mesma confiabilidade de um domínio autenticado. A Brevo recomenda autenticação de domínio; provedores de caixa podem filtrar ou rejeitar mensagens sem SPF/DKIM/DMARC. Se o remetente for um endereço gratuito como Gmail, a Brevo informa que pode substituir o remetente por um endereço próprio da plataforma. Veja os requisitos de [verificação e autenticação de remetentes](https://help.brevo.com/hc/en-us/articles/14925263522578-Comply-with-Gmail-Yahoo-and-Microsoft-s-requirements-for-email-senders). Portanto, esta é a opção prática para começar sem domínio, não uma garantia de entrega na caixa de entrada. Para entrega consistente e um remetente com a identidade do app, será necessário autenticar um domínio no futuro.

Remova do Render as antigas variáveis `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER` e `MAIL_USE_TLS`; o backend atualizado não as utiliza. Como a senha de app SMTP anterior foi compartilhada, revogue-a no provedor de e-mail.

Em desenvolvimento, `PASSWORD_RESET_DEBUG=true` pode mostrar um link local sem enviar e-mail. A configuração de produção desativa essa opção. Pedidos para e-mails cadastrados e não cadastrados devolvem a mesma resposta; isso evita revelar quais contas existem. O token é aleatório, fica armazenado no banco somente como hash, expira em 30 minutos e só pode ser usado uma vez.

## Alterar senha pelo perfil

Depois de entrar, abra o menu do usuário e escolha **Perfil e segurança**. A página exige a senha atual, valida a nova senha e sua confirmação, e encerra outras sessões após a troca. A sessão atual recebe novos tokens para continuar aberta.

## Migration

A integração Brevo e a página de perfil não adicionam colunas ao banco. Se a migration de redefinição de senha da versão anterior ainda não foi aplicada, execute-a antes de publicar o backend. No serviço com diretório raiz `backend`, rode:

```bash
flask --app wsgi db upgrade
```

Se o diretório raiz do serviço for a raiz do repositório, execute `cd backend && flask --app wsgi db upgrade`. Aplique como comando de pré-deploy ou antes de trocar para o novo backend; confirme que `DATABASE_URL` aponta para o banco publicado.

## Erros de rede

O frontend converte falhas de conexão ou timeout em uma mensagem recuperável, preserva tokens locais durante falhas transitórias na inicialização e não exibe a exceção bruta do navegador. Erros do provedor são registrados no backend sem registrar a chave da API nem o token de redefinição.
