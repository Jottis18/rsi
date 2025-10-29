-- Criar tabela de usuários
CREATE TABLE IF NOT EXISTS users (
    username VARCHAR(50) PRIMARY KEY,
    password VARCHAR(64) NOT NULL,
    balance DECIMAL(10, 2) DEFAULT 100.00
);

-- Criar tabela de itens
CREATE TABLE IF NOT EXISTS items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    description TEXT
);

-- Criar tabela de pedidos
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    item_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    total_price DECIMAL(10, 2) NOT NULL,
    refunded TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (username) REFERENCES users(username),
    FOREIGN KEY (item_id) REFERENCES items(id)
);

-- Inserir usuários de teste
-- Senha: user123 (hash SHA224)
INSERT INTO users (username, password, balance) VALUES
('user', 'ef6868fe47958067cf0f396891d6f4de11f038e4a93a70557d9f8e20', 100.00),
('guest', 'ec7d20355024b9a9c84357a9cfb9b2669ac4c019ad9266851d6ad17b', 100.00);

-- Inserir itens na loja
INSERT INTO items (name, price, description) VALUES
('Premium Flag Access', 1000.00, 'Exclusive access to premium flags'),
('Standard Item', 50.00, 'A standard item for testing'),
('Basic Item', 25.00, 'A basic item'),
('Expensive Item', 500.00, 'An expensive item for testing refunds');

