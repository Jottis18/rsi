# Guia: Explorando Race Condition com Burp Suite

Este guia explica como usar o Burp Suite (PortSwigger) para explorar a vulnerabilidade de race condition no endpoint `/refund`.

## Pré-requisitos

1. Burp Suite Community Edition ou Professional
2. Aplicação rodando em `http://localhost:8080`
3. Ter feito login e criado pelo menos um pedido

## Passo a Passo

### 1. Configurar Proxy do Burp Suite

1. Abra o Burp Suite
2. Vá em **Proxy** → **Options**
3. Certifique-se de que o proxy está escutando na porta **8080** (ou configure uma porta diferente)
4. Configure seu navegador para usar o proxy do Burp (127.0.0.1:8080)

### 2. Capturar a Requisição de Refund

1. No navegador, faça login na aplicação (`http://localhost:8080`)
2. Vá para **My Orders**
3. Clique em **Refund** em um pedido que ainda não foi reembolsado
4. A requisição será capturada no Burp Suite

### 3. Formato da Requisição

A requisição capturada deve parecer com isso:

```
POST /refund HTTP/1.1
Host: localhost:8080
Content-Type: application/x-www-form-urlencoded
Content-Length: 13
Cookie: session=xxxxxxxxxxxxxxxxxxxx

order_id=1
```

### 4. Enviar para Repeater (Teste Inicial)

1. Clique com o botão direito na requisição capturada
2. Selecione **Send to Repeater**
3. No **Repeater**, envie a requisição algumas vezes
4. Você verá que após o primeiro reembolso, as próximas retornam erro

### 5. Usar Turbo Intruder (Melhor Opção para Race Condition)

#### Instalação do Turbo Intruder

1. No Burp Suite, vá em **Extensions** → **BApp Store**
2. Busque e instale **Turbo Literature**
3. Ou baixe manualmente: https://github.com/PortSwigger/turbo-intruder

#### Configurar Race Condition com Turbo Intruder

1. Clique com o botão direito na requisição de refund
2. Selecione **Extensions** → **Turbo Intruder** → **Send to turbo intruder**

3. Use este script no Turbo Intruder:

```python
def queueRequests(target, wordlists):
    engine = RequestEngine(endpoint=target.endpoint,
                          concurrentConnections=50,
                          requestsPerConnection=100,
                          pipeline=False)
    
    # Envia múltiplas requisições simultâneas
    for i in range(100):
        engine.queue(target.req, target.baseInput, gate='race1')
    
    # Todas as requisições são disparadas ao mesmo tempo
    engine.openGate('race1')
    engine.complete(timeout=60)

def handleResponse(req, interesting):
    # Adiciona todas as respostas com sucesso
    if 'success' in req.response.lower() or req.status == 200:
        table.add(req)
```

4. Clique em **Attack**
5. Observe que múltiplas requisições processam o mesmo reembolso

### 6. Usar Burp Intruder (Alternativa)

Se não tiver Turbo Intruder, use o **Intruder**:

1. Clique com o botão direito na requisição → **Send to Intruder**
2. Na aba **Positions**:
   - Attack type: **Sniper**
   - Marque a posição: `order_id=§1§`
3. Na aba **Payloads**:
   - Payload type: **Numbers**
   - From: `1` To: `1` (mesmo order_id)
   - Step: `1`
4. Na aba **Resource Pool**:
   - Crie um novo pool ou use o padrão
   - **Maximum concurrent requests: 50**
   - **Request delay: 0 milliseconds**
5. Na aba **Options**:
   - **Request Engine**: Max concurrent requests: `50`
   - **Grep - Match**: Adicione `"success"`
6. Clique em **Start Attack**

⚠️ **Nota**: O Intruder pode não ser tão eficaz quanto o Turbo Intruder para race conditions porque não dispara todas as requisições exatamente ao mesmo tempo.

### 7. Usar Burp Repeater com Threading (Alternativa Manual)

Se precisar de uma solução mais manual:

1. Envie a requisição para **Repeater**
2. Use a extensão **Request Smuggler** ou similar
3. Ou use múltiplas instâncias do Repeater manualmente (não recomendado)

## Validação

Após o ataque:

1. No navegador, recarregue a página `/home`
2. Verifique seu saldo - ele deve ter aumentado múltiplas vezes
3. Vá para `/orders` e veja que o pedido pode estar marcado como "Refunded"
4. Se o saldo >= $10,000, a flag aparecerá na página `/home`

## Requisição HTTP Completa (Para Copiar/Colar)

```
POST /refund HTTP/1.1
Host: localhost:8080
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36
Accept: application/json, text/plain, */*
Accept-Language: en-US,en;q=0.9
Content-Type: application/x-www-form-urlencoded
Content-Length: 13
Origin: http://localhost:8080
Referer: http://localhost:8080/orders
Cookie: session=SEU_SESSION_COOKIE_AQUI
Connection: close

order_id=1
```

**Importante**: Substitua `SEU_SESSION_COOKIE_AQUI` pelo cookie de sessão real obtido após fazer login.

## Dicas

- **Aumente o número de requisições simultâneas** (50-100) para maior chance de sucesso
- **Use Turbo Intruder** para melhor controle de timing
- **Teste em diferentes horários** - a janela de race condition pode variar
- **Monitore o saldo** após cada tentativa para verificar se funcionou

## Troubleshooting

- **Erro 400 "Order already refunded"**: A primeira requisição processou. Tente com um novo pedido.
- **Erro 404 "Order not found"**: Verifique se o `order_id` está correto.
- **Nenhum reembolso processado**: Aumente o número de requisições simultâneas e use Turbo Intruder.

