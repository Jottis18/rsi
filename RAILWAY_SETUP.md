# Como configurar no Railway

## Passo 1: Criar serviço MySQL no Railway

1. No dashboard do Railway, clique em **"+ New"** → **"Database"** → **"MySQL"**
2. Railway criará automaticamente variáveis de ambiente:
   - `MYSQLHOST`
   - `MYSQLPORT`
   - `MYSQLUSER`
   - `MYSQLPASSWORD`
   - `MYSQLDATABASE`

## Passo 2: Configurar variáveis de ambiente no serviço Flask

1. No seu serviço Flask, vá em **Settings** → **Variables**
2. Adicione as seguintes variáveis (ajuste conforme os valores do MySQL criado pelo Railway):

```
MYSQL_HOST=${MYSQLHOST}
MYSQL_USER=${MYSQLUSER}
MYSQL_PASSWORD=${MYSQLPASSWORD}
MYSQL_DATABASE=${MYSQLDATABASE}
PORT=${{PORT}}
USER_FLAG=SD{race_condition_refund_exploit_success}
GUEST_FLAG=SD{guest_user_no_access}
```

3. **Importante**: Copie o valor de `MYSQLHOST` do serviço MySQL e use na variável `MYSQL_HOST` do Flask

## Passo 3: Executar script SQL

Após o MySQL estar rodando, você precisa executar o `data.sql`. Opções:

**Opção A - Railway MySQL CLI:**
1. No serviço MySQL → Settings → Connect
2. Use o MySQL CLI fornecido pelo Railway
3. Cole o conteúdo do `data.sql`

**Opção B - Aplicação que cria tabelas automaticamente:**
Modifique o app.py para criar tabelas automaticamente na primeira execução (já está assim)

## Passo 4: Redeploy

Faça commit e push novamente para redeployar, ou clique em **"Redeploy"** no Railway.

