# 🚨 SmartEvac: SIMULADOR DE EVACUAÇÃO URBANA BASEADO EM IA
**Projeto FECART — Smart Cities / Cidades Inteligentes**

> Otimização de rotas de fuga em tempo real utilizando o Algoritmo A*, arquitetura de backend escalável com Multiprocessing, e simulação de sensores IoT para gestão de crises urbanas.

---

## 📌 Visão Geral do Projeto
O **SmartEvac** é uma plataforma interativa de simulação urbana projetada para testar e validar rotas de evacuação em situações de emergência (**Incêndios**, **Enchentes** e **Acidentes Industriais com Gás Tóxico**). O sistema utiliza Inteligência Artificial para redirecionar agentes (população) dinamicamente, evitando gargalos e reduzindo o tempo total de fuga em relação a decisões manuais ou ingênuas.

---

## ✒️ Autores
* **Pedro Souza Oliveira**
* **Angelo Hugo Olivares Bassi**
* **Gabriel Mourisco Vanny de Oliveira da Silva**

---

## 🎯 Objetivos do Sistema
- **Otimização de Fluxo (IA A*)**: Aplicação do algoritmo de busca A* em grafos dirigidos com cálculo formal do custo dinâmico das vias em tempo real.
- **Demonstração Comparativa**: Confronto direto da evacuação otimizada por IA contra a escolha ingênua humana (rota mais curta geométrica sem considerar trânsito ou perigo acumulado).
- **Gestão de Crises em Smart Cities**: Integração de APIs backend REST (FastAPI), banco de dados SQLite persistente, transmissão de telemetria via WebSockets e suporte a alertas de sensores de rua via IoT.
- **Arquitetura de Alta Performance**: Utilização de `multiprocessing.Process` para isolar a API FastAPI em um núcleo de CPU dedicado (evitando a contenção do GIL no Pygame) e `multiprocessing.Queue` para envio assíncrono de métricas sem micro-congelamentos.

---

## ⚙️ Fórmula Formal de Custo Dinâmico das Vias $W(e)$

A impedância de cada trecho viário $e$ é formalmente calculada por:

$$W(e) = \frac{\text{length}}{\text{base\_speed}} \times \left( 1 + \alpha \left( \frac{N_{\text{current}}}{C_{\text{capacity}}} \right)^2 \right) \times (1 + \beta \cdot H_{\text{hazard}})$$

Onde:
- $N_{\text{current}}$: quantidade de agentes presentes na rua no instante atual.
- $C_{\text{capacity}}$: capacidade máxima de fluxo da via.
- $H_{\text{hazard}} \in [0, 1]$: intensidade do risco ambiental/desastre no trecho.
- Se a via for bloqueada por desastre ($H_{\text{hazard}} \ge 1.0$), $W(e) = \infty$.

---

## 🖼️ Interface Visual e Módulos (Pygame)

A interface gráfica de 1280x720 é dividida em três módulos principais:

1. **Painel Central (Grade do Mapa)**: Renderização gráfica 2D da malha viária, agentes coloridos por perfil demográfico, pontos de abrigo com iluminação pulsante, áreas de desastre dinâmicas e árvore de busca A* em tempo real para **transparência algorítmica**.
2. **Painel Lateral (Controles)**: Botões para seleção do desastre (Incêndio, Enchente, Gás Tóxico), slider de densidade populacional (10 a 500 agentes), alternador de modo (IA vs Sem IA), controles de execução e botão de **Simulação de Alerta IoT**.
3. **Painel Inferior (Métricas em Tempo Real)**: Cards dinâmicos exibindo:
   - **Tempo Total de Evacuação** (s)
   - **Tempo Médio por Agente** (s/agente)
   - **Taxa de Congestionamento** (%)
   - **Desempenho da IA** (% ganho de eficiência em relação ao modo ingênuo)

---

## 🛠️ Tecnologias Utilizadas
- **Linguagem**: Python 3.x
- **Interface Gráfica**: Pygame
- **IA & Algoritmos**: Algoritmo A* (`heapq`), Recálculo Assíncrono Guiado por Eventos, Atualizações Escaladas (Staggered Updates, máx 15 agentes/frame)
- **Backend**: FastAPI / Uvicorn (Processo Separado via `multiprocessing`)
- **Persistência**: SQLite3 assíncrono via `multiprocessing.Queue`
- **Comunicação**: REST & WebSockets Telemetry

---

## 🚀 Como Executar o Projeto

### 1. Clonar ou Entrar no Repositório
```bash
cd C:\Users\26012248\Documents\GitHub\fecaart
```

### 2. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 3. Executar o Simulador Integrado
```bash
python main.py
```

---

## 📡 API Endpoints (Backend REST / IoT)

- `GET http://127.0.0.1:8000/`: Health check da API.
- `GET http://127.0.0.1:8000/api/simulations`: Histórico de simulações salvas no banco de dados SQLite.
- `POST http://127.0.0.1:8000/api/iot/alert`: Disparo remoto de alerta de bloqueio de via por sensor IoT de rua.
  ```json
  {
    "u": 12,
    "v": 13,
    "hazard_type": "ALERT_RUA_BLOQUEADA"
  }
  ```
- `WS ws://127.0.0.1:8000/ws/telemetry`: Transmissão de telemetria em tempo real.

---

## 🛡️ Governança, Ética e Acessibilidade
- **Transparência Algorítmica**: Exibição visual dos nós explorados pelo algoritmo A* durante a simulação.
- **Equidade e Mobilidade Reduzida**: Priorização e velocidade diferenciada para agentes idosos, crianças e pessoas com mobilidade reduzida (PCD).
- **Supervisão Humana**: Ferramenta projetada como suporte à tomada de decisão para a Defesa Civil.
