# Planador IoT - Sistema de Estabilização ESP32

Sistema de controle de voo autônomo para planadores baseado em ESP32 com estabilização em tempo real.

## DOCUMENTAÇÃO DE SEGURANÇA

**LEIA ANTES DE CONECTAR QUALQUER COMPONENTE:**

- **[WIRING_GUIDE.md](WIRING_GUIDE.md)** - Guia completo de ligações e pinos
- **[SAFETY_CHECKLIST.md](SAFETY_CHECKLIST.md)** - Checklist de segurança obrigatório
- **[src/micropython/pin_reference.py](src/micropython/pin_reference.py)** - Referência técnica dos pinos

## Características Principais

- **Estabilização em tempo real** - Loop de controle sem delays
- **Sistema simplificado** - Apenas modo de estabilização (sem modos de voo)
- **Auto-ativação** - Sistema inicia automaticamente
- **Testes de startup** - Verificação completa de todos os componentes
- **Controle via RC** - Liberação controlada por sinal RC da nave mãe
- **Indicação visual** - LEDs mostram status do sistema
- **Build multiplataforma** (Windows/macOS/Linux)
- **Testes TDD** integrados ao Poetry

## 🚀 Quick Start

### Windows
```cmd
git clone <repository>
cd planador_iot
setup.bat
```

### macOS / Linux
```bash
git clone <repository>
cd planador_iot
./setup.sh
```

### Usar Makefile (Todas as plataformas)
```bash
make setup          # Setup completo
make dev             # Desenvolvimento rápido
make monitor         # Monitor serial
```

## 🖥️ Suporte Multiplataforma

| Sistema | Status | Notas |
|---------|---------|--------|
| **🪟 Windows 10/11** | ✅ Suportado | PowerShell, CMD, WSL2 |
| **🍎 macOS Intel** | ✅ Suportado | Homebrew, Xcode tools |
| **🍎 macOS Apple Silicon (M1/M2/M3)** | ✅ Suportado | Rosetta 2 para ESP-IDF |
| **🐧 Ubuntu/Debian** | ✅ Suportado | APT packages |
| **🐧 Fedora/RHEL** | ✅ Suportado | DNF packages |
| **🐧 Arch Linux** | ✅ Suportado | Pacman packages |

## 📦 Hardware Necessário

### Componentes Obrigatórios
- **ESP32** (qualquer modelo)
- **MPU6050** (giroscópio + acelerômetro)
- **4 Servos** (controle de superfícies)
- **1 Servo de liberação**
- **Receptor RC** (para sinal de liberação)

### Componentes Opcionais
- **4 LEDs** de status (sistema funciona sem eles)
- **2 Botões** de controle
- **Buzzer** para alertas

## 🏗️ Arquitetura do Sistema

```
planador_iot/
├── src/micropython/           # Código principal MicroPython
│   ├── config.py             # Configurações
│   ├── hardware.py           # Gerenciamento hardware
│   ├── sensors.py            # Interface sensores
│   ├── release_system.py     # Sistema liberação
│   ├── pid_controller.py     # Controlador PID
│   ├── main_modular.py       # Sistema principal
│   ├── build_dev.py          # Build desenvolvimento
│   ├── build_frozen.py       # Build produção
│   └── detect_platform.py    # Detecção plataforma
├── Makefile                   # Build automatizado
├── setup.sh                  # Setup Unix
├── setup.bat                 # Setup Windows
└── README.md                 # Este arquivo
```

## 🔧 Métodos de Build

### 1. 🚀 Desenvolvimento Rápido (Recomendado)
Ideal para prototipagem e testes:
```bash
make dev CONFIG=minimal    # Sem LEDs
make dev CONFIG=full       # Hardware completo
make monitor               # Ver logs
```

### 2. 🏭 Produção (Máxima Performance)
Para uso final com performance otimizada:
```bash
make prod-setup            # Configurar ESP-IDF
make prod                  # Build + flash frozen modules
```

### 3. ⚡ Bytecode (.mpy)
Intermediário entre desenvolvimento e produção:
```bash
make mpy                   # Compilar bytecode
```

## 🌐 Detecção Automática

O sistema detecta automaticamente:
- **Plataforma**: Windows, macOS (Intel/ARM), Linux
- **Portas seriais**: COM (Windows), /dev/cu.* (macOS), /dev/ttyUSB* (Linux)
- **Ferramentas**: Python, Homebrew, package managers
- **Arquitetura**: x86_64, ARM64 (Apple Silicon)

## 📱 Configurações Disponíveis

### Configuração Mínima (Prototipagem)
```python
# config_minimal.py - Sem LEDs
LED_SYSTEM_ACTIVE = 99    # Pino inexistente
LED_MODE = 98            # Desabilitado
# ... apenas hardware essencial
```

### Configuração Completa (Produção)
```python
# config.py - Hardware completo
LED_SYSTEM_ACTIVE = 15    # GPIO 15
LED_MODE = 4             # GPIO 4
# ... todos os componentes
```

## 🎛️ Modos de Operação

| Modo | Descrição | Flaps | Ganhos PID |
|------|-----------|-------|------------|
| **TÉRMICAS** | Voo eficiente | Baixos | Suaves |
| **CRUZEIRO** | Voo normal | Médios | Médios |
| **POUSO** | Máximo controle | Altos | Altos |

## 🔄 Sistema de Liberação

1. **TRAVADO** → 2. **ARMADO** → 3. **LIBERANDO** → 4. **LIBERADO**

- Controle via canal RC (AUX1/CH5)
- Delay de segurança configurável
- Liberação de emergência via botão

## 🛠️ Comandos Úteis

```bash
# Status e informações
make status              # Status do projeto
make platform-info      # Info da plataforma
make detect-port         # Encontrar ESP32
make check-deps          # Verificar dependências

# Desenvolvimento
make dev-test           # Testar sintaxe
make benchmark          # Performance
make docs               # Ver documentação

# Limpeza
make clean              # Limpeza completa
make dev-clean          # Limpar desenvolvimento
```

## 🔗 Documentação Adicional

- 📄 [Manual Completo](src/micropython/README_ESP32.md)
- 📄 [Guia de Compilação](src/micropython/README_COMPILATION.md)
- 📄 [Guia de Desenvolvimento](src/micropython/DEV_GUIDE.md)

## 🧪 Exemplo de Uso Completo

```bash
# 1. Clone e setup
git clone <repository>
cd planador_iot
make setup

# 2. Desenvolvimento inicial (sem LEDs)
make dev CONFIG=minimal

# 3. Monitor para debug
make monitor

# 4. Quando pronto para produção
make prod-setup
source src/micropython/setup_esp_env.sh
make prod

# 5. Benchmark de performance
make benchmark
```

## 📊 Performance Típica

| Métrica | Interpretado | Bytecode (.mpy) | Frozen Modules |
|---------|--------------|-----------------|----------------|
| **RAM** | 45-60KB | 30-40KB | 15-25KB |
| **Velocidade** | 100% | 115% | 130% |
| **Inicialização** | 3-5s | 2-3s | 1-2s |
| **Latência PID** | 8-12ms | 6-10ms | 5-8ms |

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Teste em múltiplas plataformas
4. Submeta um Pull Request

## 📄 Licença

Este projeto está sob licença MIT. Veja `LICENSE` para detalhes.

## 🆘 Suporte

- **Issues**: Abra uma issue no GitHub
- **Documentação**: Veja a pasta `docs/`
- **Exemplos**: Rode `make examples`

---

**⭐ Se este projeto foi útil, considere dar uma estrela!**