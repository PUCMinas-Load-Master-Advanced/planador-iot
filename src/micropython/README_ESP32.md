# Sistema de Estabilidade para Planador - ESP32

## Visão Geral
Sistema otimizado de estabilidade automática para planador usando ESP32 com MicroPython.

## Hardware Necessário
- **ESP32** (qualquer modelo com WiFi)
- **MPU6050** (giroscópio + acelerômetro)
- **4 Servos** (flaps esquerdo/direito, elevator, rudder)
- **1 Servo de Liberação** (para soltar planador da nave mãe)
- **LEDs** (opcionais - sistema ativo, modo, alerta, liberação)
- **2 Botões** (modo, power - opcional)
- **Receptor RC** (para sinal de liberação)

## Pinagem ESP32
```
# Servos Planador
GPIO 25 - Flap Esquerdo
GPIO 26 - Flap Direito  
GPIO 14 - Elevator
GPIO 27 - Rudder

# Sistema de Liberação
GPIO 23 - Servo de Liberação
GPIO 13 - Sinal RC (Canal AUX1/CH5)

# Sensores I2C
GPIO 21 - SDA
GPIO 22 - SCL

# LEDs (Opcionais)
GPIO 15 - Sistema Ativo (Verde) - Opcional
GPIO 4  - Modo de Voo (Amarelo) - Opcional
GPIO 19 - Alertas (Laranja) - Opcional
GPIO 5  - Sistema Liberação (Azul) - Opcional

# Controles
GPIO 34 - Botão Modo (Azul)
GPIO 18 - Botão Power (Vermelho) - Emergência
```

## Dependências
O sistema usa apenas bibliotecas nativas do MicroPython ESP32:
- `machine` - Controle de hardware (PWM, I2C, GPIO)
- `time` - Temporização
- `math` - Cálculos trigonométricos
- `struct` - Decodificação de dados do sensor
- `gc` - Garbage collector para otimização de memória

**Nenhuma biblioteca externa é necessária!**

## Otimizações para ESP32
- Uso de decorador `@micropython.native` para funções críticas
- Estruturas de dados compactas
- Garbage collection automático
- PID simplificado (apenas P + I)
- Loop principal a 10Hz (100ms)

## Modos de Voo
1. **TÉRMICAS** - Flaps neutros, ganhos suaves
2. **CRUZEIRO** - Flaps baixos, ganhos médios  
3. **POUSO** - Flaps máximos, ganhos altos

## Uso de Memória
- **RAM**: ~15KB (de 320KB disponíveis)
- **Flash**: ~8KB (do espaço disponível)
- **CPU**: ~10% a 10Hz

## Arquitetura do Sistema

### 📁 Estrutura Modular
```
src/micropython/
├── config.py              # Configurações centralizadas
├── hardware.py            # Gerenciamento de hardware (LEDs, botões, servos)
├── sensors.py             # Sensores (MPU6050, simulação)
├── release_system.py      # Sistema de liberação
├── pid_controller.py      # Controlador PID
├── main_modular.py        # Sistema principal modular
├── main.py                # Sistema original (monolítico)
├── boot.py                # Script de inicialização
├── hardware_test.py       # Testes de hardware
└── README_ESP32.md        # Esta documentação
```

### 🏗️ Benefícios da Arquitetura Modular
- **Separação de responsabilidades**: Cada módulo tem uma função específica
- **Facilidade de manutenção**: Alterações isoladas por módulo
- **Testabilidade**: Cada módulo pode ser testado independentemente
- **Reutilização**: Módulos podem ser usados em outros projetos
- **Legibilidade**: Código mais organizado e fácil de entender

## Como Usar

### 🚀 Método 1: Desenvolvimento Rápido (Recomendado)
```bash
# 1. Instalar ferramentas
python3 install_dev_tools.py

# 2. Criar pacote de desenvolvimento
python3 build_dev.py

# 3. Deploy rápido
cd dist/planador_esp32
cp configs/config_minimal.py modules/config.py  # Para prototipagem
make flash PORT=/dev/ttyUSB0
```

### 🏭 Método 2: Produção (Frozen Modules)
```bash
# 1. Configurar ESP-IDF
python3 setup_build_env.py

# 2. Compilar firmware
source setup_esp_env.sh
python3 build_frozen.py build

# 3. Flash firmware
python3 build_frozen.py flash /dev/ttyUSB0
```

### ⚡ Método 3: Bytecode (MPY Cross)
```bash
# 1. Compilar para bytecode
python3 compile_mpy.py all

# 2. Upload arquivos .mpy
python3 upload_mpy.py /dev/ttyUSB0
```

### 📝 Método 4: Manual (REPL)
1. Conecte via REPL: `mpremote` ou `screen /dev/ttyUSB0 115200`
2. Copie e cole os arquivos `.py`
3. Execute: `from main_modular import main; main()`

### 🔧 Método 5: Inicialização Automática
1. Carregue todos os arquivos `.py` no ESP32
2. Conecte o hardware conforme pinagem
3. Reinicie o ESP32
4. Pressione Ctrl+C para escolher:
   - `1`: Sistema Modular (Recomendado)
   - `2`: Sistema Original 
   - `3`: Teste de Hardware

## LEDs de Status (Se Disponíveis)
O sistema funciona normalmente mesmo sem LEDs conectados. Quando disponíveis:

- **Verde fixo**: Sistema ativo
- **Amarelo piscando**: Modo atual (1 pisca = Térmicas, 2 = Cruzeiro, 3 = Pouso)
- **Azul fixo**: Sistema liberação travado
- **Azul piscando rápido**: Sistema armado para liberação
- **Azul piscando lento**: Planador liberado
- **Laranja**: Alertas e emergências

**Sem LEDs**: O sistema reporta status apenas via console serial

## Sistema de Liberação
### Estados do Sistema
1. **TRAVADO** (LED azul fixo)
   - Servo na posição 45° (segura o planador)
   - Aguardando sinal RC > 1700μs

2. **ARMADO** (LED azul piscando rápido)
   - Delay de segurança de 2 segundos
   - Confirma se sinal RC ainda está alto

3. **LIBERANDO** (LED apagado)
   - Servo move para posição 135° (solta planador)
   - Duração: 500ms

4. **LIBERADO** (LED azul piscando lento)
   - Auto-travamento após 5 segundos
   - Planador foi solto com sucesso

### Configuração do Rádio Controle
- **Canal**: AUX1 ou CH5 do receptor
- **Posição baixa**: <1700μs (sistema travado)
- **Posição alta**: >1700μs (armar liberação)
- **Delay segurança**: 2 segundos
- **Liberação emergência**: Botão vermelho (sistema desligado)

## Performance
- Latência de controle: <10ms
- Precisão de atitude: ±0.5°
- Frequência PID: 10Hz
- Resposta dos servos: <100ms