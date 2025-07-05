# Guia de Ligações ESP32 - Sistema Planador

## ⚠️ AVISOS DE SEGURANÇA

**LEIA ANTES DE CONECTAR QUALQUER COMPONENTE:**

1. **SEMPRE DESLIGUE O ESP32** antes de fazer qualquer conexão
2. **VERIFIQUE A POLARIDADE** dos componentes antes de conectar
3. **USE RESISTORES LIMITADORES** onde necessário
4. **NÃO EXCEDA 3.3V** nos pinos GPIO do ESP32
5. **VERIFIQUE DUAS VEZES** antes de energizar o sistema

---

## 📋 Lista de Componentes

### Obrigatórios
- 1x ESP32 DevKit v1 (30 pinos)
- 4x Servos 9g (SG90 ou similar) - 5V
- 1x Servo de liberação - 5V
- 1x MPU6050 (Giroscópio/Acelerômetro) - 3.3V
- 3x LEDs (Verde, Amarelo, Vermelho) - 3.3V
- 3x Resistores 220Ω (para LEDs)
- 1x Receptor RC/PWM - 3.3V/5V
- Fonte externa 5V/3A mínimo
- Protoboard ou PCB
- Jumpers e fios

### Opcionais
- 1x Botão liga/desliga
- Capacitores de filtro (100µF, 470µF)

---

## 🔌 Mapeamento de Pinos ESP32

### Servos do Planador (PWM - 5V)
```
Flaps Esquerdo  → GPIO 25
Flaps Direito   → GPIO 26  
Elevador        → GPIO 14
Leme            → GPIO 27
Servo Liberação → GPIO 23
```

### LEDs Indicadores (3.3V)
```
LED Sistema Ativo → GPIO 15 (Verde)
LED Alerta        → GPIO 19 (Amarelo) 
LED Liberação     → GPIO 5  (Vermelho)
```

### Sensores I2C (3.3V)
```
MPU6050 SDA → GPIO 21
MPU6050 SCL → GPIO 22
```

### Controle RC (3.3V/5V)
```
Sinal RC Liberação → GPIO 13
```

### Controle Manual (Opcional)
```
Botão Power → GPIO 18 (com pull-up interno)
```

### Alimentação
```
VIN  → +5V (fonte externa)
GND  → GND (comum)
3V3  → +3.3V (apenas para componentes 3.3V)
```

---

## 🔧 Esquema de Ligações Detalhado

### 1. ALIMENTAÇÃO (CRÍTICO!)

```
FONTE 5V/3A:
  (+) → VIN do ESP32
  (-) → GND do ESP32
  
IMPORTANTE: 
- Use fonte externa, NÃO alimente via USB
- Capacitor 470µF entre VIN e GND (filtro)
- Todos os GNDs devem estar conectados
```

### 2. SERVOS (5V)

```
CADA SERVO (SG90):
  Fio Marrom/Preto  → GND comum
  Fio Vermelho      → +5V da fonte
  Fio Laranja/Amarelo → GPIO específico
  
Servo Flaps Esquerdo:  GPIO 25
Servo Flaps Direito:   GPIO 26
Servo Elevador:        GPIO 14
Servo Leme:            GPIO 27
Servo Liberação:       GPIO 23

CUIDADO:
- NUNCA conecte servo em 3.3V (queima o servo)
- Use +5V da fonte externa
- Todos os GNDs interligados
```

### 3. MPU6050 (3.3V)

```
MPU6050:
  VCC → 3V3 do ESP32 (NÃO use 5V!)
  GND → GND comum
  SDA → GPIO 21
  SCL → GPIO 22
  
OPCIONAL:
  INT → GPIO 4 (para interrupções)
  AD0 → GND (endereço I2C 0x68)
```

### 4. LEDs INDICADORES (3.3V)

```
CADA LED:
  GPIO → Resistor 220Ω → Ânodo LED → Cátodo → GND
  
LED Sistema (Verde):
  GPIO 15 → R220Ω → LED Verde → GND
  
LED Alerta (Amarelo):
  GPIO 19 → R220Ω → LED Amarelo → GND
  
LED Liberação (Vermelho):
  GPIO 5 → R220Ω → LED Vermelho → GND

CUIDADO:
- SEMPRE use resistor limitador
- Respeite polaridade (ânodo +, cátodo -)
```

### 5. RECEPTOR RC (3.3V/5V)

```
RECEPTOR RC:
  VCC → 3V3 ou 5V (conforme especificação)
  GND → GND comum
  CH1 (Liberação) → GPIO 13
  
NOTA:
- Verifique tensão do seu receptor
- Alguns aceitam 3.3V, outros precisam 5V
```

### 6. BOTÃO POWER (Opcional)

```
BOTÃO:
  Um terminal → GPIO 18
  Outro terminal → GND
  
NOTA:
- Pull-up interno habilitado no código
- Botão normalmente aberto
```

---

## 📐 Layout Sugerido na Protoboard

```
    ESP32 DevKit v1
    ┌─────────────────┐
    │ 3V3          D0 │
    │ EN           D1 │
    │ VP           D2 │
    │ VN           D3 │
    │ D34          D4 │ → MPU6050 INT (opcional)
    │ D35          D5 │ → LED Liberação (Vermelho)
    │ D32         D18 │ → Botão Power
    │ D33         D19 │ → LED Alerta (Amarelo)
    │ D25         D21 │ → MPU6050 SDA
    │ D26         D22 │ → MPU6050 SCL
    │ D27         D23 │ → Servo Liberação
    │ D14          NC │
    │ D12          NC │
    │ D13         D15 │ → LED Sistema (Verde)
    │ GND         D2  │
    │ VIN         D4  │
    └─────────────────┘
    
LADO ESQUERDO:
D25 → Servo Flaps Esquerdo
D26 → Servo Flaps Direito  
D27 → Servo Leme
D14 → Servo Elevador
D13 → Receptor RC

LADO DIREITO:
D23 → Servo Liberação
D22 → MPU6050 SCL
D21 → MPU6050 SDA
D19 → LED Alerta
D15 → LED Sistema
D5  → LED Liberação
D18 → Botão Power
```

---

## ⚡ Especificações Elétricas

### Limites do ESP32
- **GPIO**: 3.3V máximo, 12mA máximo por pino
- **Corrente total**: 40mA máximo em todos os GPIOs
- **VIN**: 6-20V (recomendado 5V)
- **3V3**: 600mA máximo

### Consumo dos Componentes
- **ESP32**: ~240mA
- **Servo SG90**: 100-600mA cada (pico 1A)
- **MPU6050**: 3.5mA
- **LED**: 20mA cada
- **Total estimado**: 1.5-3A

---

## 🔍 Checklist de Verificação

### Antes de Ligar:
- [ ] Fonte externa 5V conectada em VIN
- [ ] Todos os GNDs interligados
- [ ] Servos conectados em 5V (não 3.3V)
- [ ] MPU6050 conectado em 3.3V (não 5V)
- [ ] LEDs com resistores limitadores
- [ ] Polaridade dos LEDs correta
- [ ] Nenhum curto-circuito visível
- [ ] Conexões firmes e seguras

### Após Ligar:
- [ ] LED de power do ESP32 aceso
- [ ] Sequência de teste dos LEDs
- [ ] Movimento dos servos na inicialização
- [ ] Mensagens no serial monitor
- [ ] Sem aquecimento excessivo
- [ ] Sem cheiro de queimado

---

## 🚨 Sinais de Problema

### DESLIGUE IMEDIATAMENTE SE:
- Cheiro de queimado
- Componente muito quente
- LED de power piscando
- Fumaça
- Comportamento errático

### Problemas Comuns:
1. **Servos não respondem**: Verifique alimentação 5V
2. **ESP32 reinicia**: Fonte insuficiente ou curto
3. **MPU6050 não detectado**: Verifique conexões I2C
4. **LEDs não acendem**: Verifique resistores e polaridade

---

## 🛠️ Ferramentas Necessárias

- Multímetro (verificar continuidade e tensões)
- Alicate desencapador
- Ferro de solda e solda (se necessário)
- Sugador de solda
- Protoboard ou PCB
- Jumpers macho-macho e macho-fêmea

---

## 📞 Suporte

Em caso de dúvidas sobre as ligações:
1. Verifique este documento novamente
2. Meça tensões com multímetro
3. Teste componentes individualmente
4. Consulte datasheets dos componentes

**LEMBRE-SE: É melhor ser cauteloso do que queimar componentes!**