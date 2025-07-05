# Explicação dos Gráficos do Simulador

## Visão Geral dos Gráficos

O simulador exibe 4 gráficos principais que mostram o comportamento do sistema de estabilização em tempo real:

### 1. **Gráfico Superior Esquerdo: Atitude (Roll/Pitch)**
```
Título: "Atitude (Roll/Pitch)"
Eixo Y: Ângulo (°)
Eixo X: Tempo (s)
Linhas: Azul (Roll) e Vermelha (Pitch)
```

**O que representa:**
- **Roll (Azul)**: Rotação do planador em torno do eixo longitudinal (frente-trás)
  - Valores positivos = asa direita para baixo
  - Valores negativos = asa esquerda para baixo
  - Ideal: próximo de 0° (planador nivelado)

- **Pitch (Vermelho)**: Rotação do planador em torno do eixo lateral (esquerda-direita)
  - Valores positivos = nariz para cima
  - Valores negativos = nariz para baixo
  - Ideal: próximo de 0° (planador em voo nivelado)

**Como interpretar:**
- Oscilações pequenas (±5°) = sistema estável
- Oscilações grandes (±20°) = sistema instável ou perturbações fortes
- Tendência crescente = sistema perdendo controle
- Convergência para zero = sistema se estabilizando

### 2. **Gráfico Superior Direito: Yaw Rate**
```
Título: "Yaw Rate"
Eixo Y: °/s (graus por segundo)
Eixo X: Tempo (s)
Linha: Verde
```

**O que representa:**
- **Yaw Rate**: Velocidade de rotação do planador em torno do eixo vertical
  - Valores positivos = girando para a direita
  - Valores negativos = girando para a esquerda
  - Ideal: próximo de 0°/s (sem rotação)

**Como interpretar:**
- Picos altos = rotações bruscas (pode indicar instabilidade)
- Valores constantes diferentes de zero = planador girando continuamente
- Oscilações rápidas = sistema tentando corrigir o curso

### 3. **Gráfico Inferior Esquerdo: Servos - Flaps**
```
Título: "Servos - Flaps"
Eixo Y: Ângulo (°)
Eixo X: Tempo (s)
Linhas: Azul (Esquerdo) e Vermelha (Direito)
```

**O que representa:**
- **Flaps Esquerdo/Direito**: Posição dos flaps (ailerons) para controle de roll
  - 90° = posição neutra
  - < 90° = flap para baixo
  - > 90° = flap para cima

**Como interpretar:**
- Movimentos opostos = correção de roll (um sobe, outro desce)
- Movimentos iguais = não há correção de roll necessária
- Amplitude grande = correções fortes (sistema lutando contra perturbações)
- Movimentos suaves = sistema bem calibrado

### 4. **Gráfico Inferior Direito: Servos - Elevator/Rudder**
```
Título: "Servos - Elevator/Rudder"
Eixo Y: Ângulo (°)
Eixo X: Tempo (s)
Linhas: Verde (Elevator) e Magenta (Rudder)
```

**O que representa:**
- **Elevator (Verde)**: Controla pitch (subida/descida)
  - 90° = posição neutra
  - < 90° = nariz para baixo
  - > 90° = nariz para cima

- **Rudder (Magenta)**: Controla yaw (direção)
  - 90° = posição neutra
  - < 90° = cauda para a esquerda (nariz para direita)
  - > 90° = cauda para a direita (nariz para esquerda)

**Como interpretar:**
- Elevator oscilando = sistema corrigindo altitude/pitch
- Rudder oscilando = sistema corrigindo direção
- Ambos estáveis em 90° = voo nivelado sem correções

## Padrões Típicos de Comportamento

### 🟢 **Sistema Estável (Ideal)**
- Atitude: Oscilações pequenas (±2°) convergindo para zero
- Yaw Rate: Próximo de zero com pequenas variações
- Servos: Pequenos movimentos em torno de 90°

### 🟡 **Sistema em Correção**
- Atitude: Oscilações médias (±10°) com tendência decrescente
- Yaw Rate: Picos seguidos de retorno ao zero
- Servos: Movimentos mais amplos mas coordenados

### 🔴 **Sistema Instável**
- Atitude: Oscilações crescentes (>±15°)
- Yaw Rate: Valores altos e erráticos
- Servos: Movimentos extremos e descoordenados

## Controladores Interativos

### **RC Signal (Controle Remoto)**
- **1500**: Posição neutra (sem comando)
- **< 1500**: Comando de liberação (exemplo: 1000)
- **> 1500**: Reservado para futuras funções

### **Perturbação**
- **0**: Sem perturbações externas
- **5**: Perturbação leve (vento suave)
- **10**: Perturbação média (turbulência)
- **20**: Perturbação forte (rajadas)

## Análise de Performance

### **Frequência de Loop**
- **50Hz**: Ideal para controle em tempo real
- **30-40Hz**: Aceitável, mas pode haver atraso
- **< 30Hz**: Muito lento, controle comprometido

### **Integral PID**
- Valores próximos de zero = sistema bem calibrado
- Valores crescentes = erro acumulado (requer atenção)
- Valores oscilantes = ganhos PID desbalanceados

## Cenários de Teste

### **1. Voo Normal**
```bash
make sim
```
- Perturbações mínimas
- Sistema deve se estabilizar rapidamente
- Servos com movimentos suaves

### **2. Voo com Perturbações**
```bash
make sim-disturbance
```
- Perturbações externas simuladas
- Sistema deve corrigir continuamente
- Servos com movimentos mais ativos

### **3. Teste de Liberação RC**
```bash
make sim-release
```
- Simula comando de liberação
- Sistema deve manter estabilidade
- Servo de liberação deve ativar

## Interpretação dos LEDs

### **Status LEDs no Simulador**
- **Sistema (Verde)**: Sistema ativo e operacional
- **Alerta (Amarelo)**: Aviso de instabilidade ou problema
- **Liberação (Azul)**: Comando RC de liberação ativo

## Dicas de Análise

1. **Olhe primeiro a atitude**: Se roll/pitch estão estáveis, o sistema está funcionando
2. **Observe a correlação**: Movimento no roll deve gerar movimento nos flaps
3. **Verifique a frequência**: Deve manter próximo de 50Hz
4. **Analise as correções**: Servos devem responder rapidamente às mudanças de atitude
5. **Monitore os integrais**: Valores crescentes indicam erro sistemático

## Ajustes Recomendados

Se observar instabilidade:
- Diminuir ganhos PID (arquivo `config.py`)
- Aumentar limites de integral
- Verificar frequência de loop
- Analisar amplitude das perturbações

Se observar resposta lenta:
- Aumentar ganhos proporcionais
- Reduzir ganhos derivativos
- Verificar se não há saturação dos servos