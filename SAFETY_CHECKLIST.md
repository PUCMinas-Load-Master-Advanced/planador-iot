# Checklist de Segurança - Sistema Planador ESP32

## ⚠️ ANTES DE CONECTAR QUALQUER COMPONENTE

### 📋 Preparação
- [ ] ESP32 desligado e desconectado da alimentação
- [ ] Todos os componentes identificados e testados individualmente
- [ ] Multímetro disponível para verificações
- [ ] Bancada limpa e organizada
- [ ] Documentação de pinos (WIRING_GUIDE.md) aberta

---

## 🔌 Verificação de Alimentação

### Fonte de Alimentação
- [ ] Fonte externa 5V/3A ou superior disponível
- [ ] Tensão da fonte medida: **4.8V - 5.2V** ✓
- [ ] Corrente máxima da fonte: **≥ 3A** ✓
- [ ] Cabos de alimentação em bom estado
- [ ] Conectores firmes e sem oxidação

### Conexões de Energia
- [ ] **VIN do ESP32** conectado ao **+5V da fonte**
- [ ] **GND do ESP32** conectado ao **GND da fonte**
- [ ] **NÃO** usar alimentação USB para o sistema completo
- [ ] Capacitor de filtro (470µF) entre VIN e GND (opcional)

---

## 🎛️ Verificação dos Servos

### Especificações
- [ ] Todos os servos são **5V** (SG90 ou compatível)
- [ ] Corrente máxima de cada servo: **≤ 1A**
- [ ] Fios dos servos identificados:
  - [ ] **Marrom/Preto** = GND
  - [ ] **Vermelho** = +5V
  - [ ] **Laranja/Amarelo** = Sinal PWM

### Conexões dos Servos
- [ ] **Servo Flaps Esquerdo** → GPIO 25
- [ ] **Servo Flaps Direito** → GPIO 26
- [ ] **Servo Elevador** → GPIO 14
- [ ] **Servo Leme** → GPIO 27
- [ ] **Servo Liberação** → GPIO 23

### Alimentação dos Servos
- [ ] **TODOS** os fios vermelhos conectados em **+5V** (não 3.3V!)
- [ ] **TODOS** os fios marrom/preto conectados em **GND comum**
- [ ] **NENHUM** servo conectado em 3.3V (queima o servo!)

---

## 📡 Verificação do MPU6050

### Especificações
- [ ] MPU6050 é **3.3V** (não 5V!)
- [ ] Endereço I2C: **0x68**
- [ ] Pinos identificados: VCC, GND, SDA, SCL

### Conexões do MPU6050
- [ ] **VCC** → **3V3 do ESP32** (NUNCA em 5V!)
- [ ] **GND** → **GND comum**
- [ ] **SDA** → **GPIO 21**
- [ ] **SCL** → **GPIO 22**
- [ ] **AD0** → **GND** (endereço 0x68)

---

## 💡 Verificação dos LEDs

### Especificações
- [ ] LEDs de 3mm ou 5mm, 3.3V
- [ ] Corrente máxima: **20mA por LED**
- [ ] Resistores limitadores: **220Ω cada LED**

### Conexões dos LEDs
- [ ] **LED Sistema (Verde)**: GPIO 15 → R220Ω → LED → GND
- [ ] **LED Alerta (Amarelo)**: GPIO 19 → R220Ω → LED → GND
- [ ] **LED Liberação (Vermelho)**: GPIO 5 → R220Ω → LED → GND

### Polaridade dos LEDs
- [ ] **Ânodo** (perna longa) → lado do resistor
- [ ] **Cátodo** (perna curta) → GND
- [ ] **TODOS** os LEDs com resistor limitador

---

## 📻 Verificação do Receptor RC

### Especificações
- [ ] Tensão de operação verificada (3.3V ou 5V)
- [ ] Canal de liberação identificado
- [ ] Sinal PWM padrão (1000-2000µs)

### Conexões do RC
- [ ] **VCC** → 3V3 ou 5V (conforme especificação)
- [ ] **GND** → GND comum
- [ ] **Canal Liberação** → GPIO 13

---

## 🔘 Verificação do Botão (Opcional)

### Conexões do Botão
- [ ] **Um terminal** → GPIO 18
- [ ] **Outro terminal** → GND
- [ ] Pull-up interno habilitado no código
- [ ] Botão normalmente aberto

---

## ⚡ Verificações Elétricas

### Medições com Multímetro
- [ ] **VIN**: 5.0V ± 0.2V
- [ ] **3V3**: 3.3V ± 0.1V
- [ ] **Continuidade GND**: Todos os GNDs conectados
- [ ] **Sem curtos**: Entre VIN e GND > 100Ω
- [ ] **Sem curtos**: Entre 3V3 e GND > 100Ω

### Verificação Visual
- [ ] Nenhuma conexão solta
- [ ] Fios não encostando entre si
- [ ] Componentes firmemente fixados
- [ ] Protoboard ou PCB sem rachaduras

---

## 🔧 Teste Inicial (SEM SERVOS)

### Primeira Energização
- [ ] **DESCONECTAR** todos os servos temporariamente
- [ ] Conectar apenas ESP32, MPU6050 e LEDs
- [ ] Ligar a fonte
- [ ] Verificar:
  - [ ] LED power do ESP32 aceso
  - [ ] Tensões corretas (5V e 3.3V)
  - [ ] ESP32 não aquecendo
  - [ ] Nenhum cheiro estranho

### Teste de Comunicação
- [ ] Conectar USB para monitoramento
- [ ] Carregar código de teste
- [ ] Verificar mensagens no serial monitor
- [ ] Testar comunicação I2C com MPU6050
- [ ] Testar LEDs individualmente

---

## 🎯 Teste Completo (COM SERVOS)

### Segunda Energização
- [ ] **DESLIGAR** o sistema
- [ ] Conectar os servos (verificar polaridade novamente)
- [ ] Ligar a fonte
- [ ] Verificar:
  - [ ] Corrente total < 3A
  - [ ] Servos respondem aos comandos
  - [ ] Movimento suave dos servos
  - [ ] Sem aquecimento excessivo

---

## 🚨 Sinais de Perigo - DESLIGUE IMEDIATAMENTE

### Indicações de Problema
- [ ] ❌ Cheiro de queimado
- [ ] ❌ Fumaça
- [ ] ❌ Componente muito quente ao toque
- [ ] ❌ LED power piscando
- [ ] ❌ ESP32 reiniciando constantemente
- [ ] ❌ Corrente > 4A
- [ ] ❌ Tensões fora da faixa normal
- [ ] ❌ Ruído elétrico excessivo

### Em Caso de Problema
1. **DESLIGUE** imediatamente a alimentação
2. **DESCONECTE** a fonte
3. **VERIFIQUE** todas as conexões
4. **MEÇA** tensões e continuidades
5. **IDENTIFIQUE** o componente problemático
6. **NÃO RELIGUE** até resolver o problema

---

## ✅ Checklist Final

### Antes de Usar o Sistema
- [ ] Todos os testes anteriores realizados
- [ ] Sistema funcionando por 10 minutos sem problemas
- [ ] Todas as funções testadas (servos, LEDs, sensores)
- [ ] Corrente estável e dentro dos limites
- [ ] Temperaturas normais
- [ ] Código carregado e funcionando
- [ ] Sistema de segurança testado (botões, liberação)

### Documentação
- [ ] Esquema de ligações documentado
- [ ] Fotos do sistema montado
- [ ] Lista de componentes e especificações
- [ ] Procedimentos de teste documentados

---

## 📞 Em Caso de Dúvida

**REGRA DE OURO: Quando em dúvida, NÃO LIGUE!**

1. Consulte novamente o WIRING_GUIDE.md
2. Verifique o datasheet dos componentes
3. Meça tensões e correntes
4. Teste componentes individualmente
5. Peça ajuda se necessário

**É melhor perder tempo verificando do que queimar componentes!**