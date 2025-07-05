# Testes do Projeto Planador IoT

## Estrutura dos Testes

```
tests/
├── README.md                           # Este arquivo
├── unit/                              # Testes unitários
│   ├── test_pid_simple.py            # Testes PID básicos
│   ├── test_platform.py              # Testes de plataforma
│   ├── test_main_esp32.py             # Testes ESP32
│   ├── test_simulator_basic.py       # Testes básicos do simulador
│   ├── test_simulator.py             # Testes avançados (em desenvolvimento)
│   ├── test_system_functions.py      # Testes de funções do sistema
│   └── test_main_system.py           # Testes do sistema principal
└── integration/                       # Testes de integração
    └── test_full_system.py           # Testes do sistema completo
```

## Comandos de Teste

### Comandos Básicos
```bash
make test               # Testes funcionais principais (32 testes)
make test-all           # TODOS os testes (incluindo falhas)
make test-unit          # Apenas testes unitários
make test-integration   # Apenas testes de integração
```

### Comandos com Coverage
```bash
make test-cov           # Testes funcionais com coverage
make test-cov-unit      # Testes unitários com coverage
make cov-report         # Relatório de coverage no terminal
make cov-html           # Relatório HTML de coverage
```

## Categorias de Teste

### Testes Funcionais (Passando - 32 testes)

#### test_pid_simple.py (6 testes)
- Testa cálculos PID básicos
- Validação de limites dos servos
- Conversão de ângulos
- Cálculo de comandos dos servos

#### test_platform.py (6 testes)
- Detecção de plataforma
- Validação do ambiente Python
- Verificação da estrutura do projeto
- Teste de alvos do Makefile

#### test_main_esp32.py (9 testes)
- Simulação das funções principais do ESP32
- Teste de cálculos PID específicos
- Validação de configurações
- Simulação de tratamento de erros
- Teste de timing do loop principal

#### test_simulator_basic.py (11 testes)
- Testes básicos do simulador
- Validação de importações
- Teste de execução do simulador
- Verificação de estruturas de dados

### Testes em Desenvolvimento

#### test_simulator.py
- Testes avançados do simulador
- Teste de hardware simulado
- Validação de PID completo
- Testes de integração do sistema

#### test_system_functions.py
- Testes de funções específicas
- Validação de precisão
- Teste de tratamento de erros
- Verificação de performance

#### test_full_system.py
- Testes de integração completa
- Simulação de cenários de voo
- Teste de recuperação de falhas
- Validação de confiabilidade

## Coverage de Código

### Status Atual: 22.11% Global

#### Arquivos Cobertos:
- **planador_simulator.py**: 60.66% (funções críticas)
- **custom_logging.py**: 0% (não testado diretamente)
- **gui_simulator.py**: 0% (interface gráfica)
- **exemplo_interpretacao.py**: 0% (exemplo)

### Relatórios de Coverage

#### Terminal
```bash
make cov-report
```

#### HTML Detalhado
```bash
make cov-html
# Abre htmlcov/index.html no navegador
```

### Arquivos Ignorados pelo Git
- `htmlcov/` - Relatórios HTML
- `coverage.xml` - Relatório XML
- `.coverage` - Dados de coverage
- `.pytest_cache/` - Cache do pytest

## Configuração

### pyproject.toml
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short --cov=src --cov-report=term-missing --cov-report=html"

[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*", "*/test_*", "*/__pycache__/*"]

[tool.coverage.report]
show_missing = true
precision = 2
exclude_lines = ["pragma: no cover", "if __name__ == .__main__."]
```

## Executando Testes

### Desenvolvimento Diário
```bash
# Teste rápido
make test

# Verificar coverage
make cov-report
```

### Antes de Commit
```bash
# Executar todos os testes
make test-all

# Coverage completo
make test-cov

# Relatório detalhado
make cov-html
```

### Desenvolvimento de Novas Features
```bash
# Teste específico
poetry run pytest tests/unit/test_novo_feature.py -v

# Com coverage
poetry run pytest tests/unit/test_novo_feature.py --cov=src -v
```

## Criando Novos Testes

### Estrutura Básica
```python
#!/usr/bin/env python3
"""
Descrição do teste
"""

import unittest
import sys
import os

# Configurar path se necessário
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

class TestNomeDoModulo(unittest.TestCase):
    """Testes para o módulo X"""

    def setUp(self):
        """Configuração inicial dos testes"""
        pass

    def test_funcionalidade_basica(self):
        """Testa funcionalidade básica"""
        # Arrange
        entrada = "valor_teste"
        
        # Act
        resultado = funcao_testada(entrada)
        
        # Assert
        self.assertEqual(resultado, "valor_esperado")

if __name__ == '__main__':
    unittest.main(verbosity=2)
```

### Boas Práticas

1. **Nome dos Testes**: Descritivo e específico
2. **Organização**: Um teste por funcionalidade
3. **AAA Pattern**: Arrange, Act, Assert
4. **Isolamento**: Testes independentes
5. **Coverage**: Focar nas funções críticas

### Mocken Dependências
```python
# Mock do decorator micropython.native
def mock_native(func):
    return func

import builtins
builtins.micropython = type('Mock', (), {'native': mock_native})()
```

## Métricas de Qualidade

### Objetivos de Coverage
- **Funções críticas**: >90% (PID, servos, sensores)
- **Sistema principal**: >80% (simulador, controle)
- **Componentes auxiliares**: >60% (GUI, logging)

### Status dos Testes
- **Funcionais**: 32/32 passando (100%)
- **Coverage global**: 22.11%
- **Coverage crítico**: 60.66%
- **Falhas**: 0

## Troubleshooting

### Problemas Comuns

#### ImportError
```bash
# Verificar paths
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

#### Dependências
```bash
# Instalar dependências de teste
poetry install --with dev
```

#### Coverage baixo
```bash
# Verificar linhas não cobertas
make cov-report
```

### Debug de Testes
```bash
# Verbose
poetry run pytest tests/ -v -s

# Parar no primeiro erro
poetry run pytest tests/ -x

# Executar teste específico
poetry run pytest tests/unit/test_pid_simple.py::TestSimplePID::test_pid_calculation_basic -v
```

## Integração Contínua

### GitHub Actions (futuro)
```yaml
- name: Run tests
  run: make test-cov

- name: Upload coverage
  uses: codecov/codecov-action@v1
  with:
    file: ./coverage.xml
```

### Pre-commit Hooks
```bash
# Executar testes antes do commit
echo "make test" > .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```