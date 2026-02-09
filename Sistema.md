# Sistema CalhaGest - Especificação Funcional

## 📋 Visão Geral

O **CalhaGest** é um sistema de gestão empresarial especializado em fabricação e instalação de calhas, rufos e pingadeiras. O sistema gerencia todo o ciclo de negócio, desde o cadastro de produtos até a conclusão de instalações.

### Objetivo
Facilitar o gerenciamento de orçamentos, controle de estoque, agendamento de instalações e acompanhamento financeiro para empresas do setor de calhas.

---

## 🎯 Funcionalidades Principais

### 1. Dashboard (Painel Principal)
**Função:** Visão geral do negócio com métricas em tempo real

- Exibir número total de orçamentos cadastrados
- Mostrar quantidade de orçamentos aprovados
- Calcular e exibir faturamento total (orçamentos aprovados + completados)
- Calcular e exibir lucro total
- Listar os 3 orçamentos mais recentes com acesso rápido
- Exibir tendências percentuais (comparação mensal)
- Botão de acesso rápido às configurações
- Nome da empresa personalizável no cabeçalho

**Interações:**
- Clicar em um orçamento recente → Navegar para detalhes do orçamento
- Botão "Ver todos" → Navegar para lista completa de orçamentos
- Ícone de configurações → Abrir página de configurações

---

### 2. Gestão de Produtos

#### 2.1 Listagem de Produtos
**Função:** Exibir todos os produtos cadastrados

- Listar produtos com: nome, tipo, medida, preço por metro
- Busca por nome do produto
- Filtro por tipo (calha, rufo, pingadeira)
- Ordenação por nome ou preço
- Contador de produtos cadastrados
- Botão para adicionar novo produto

#### 2.2 Cadastro de Produtos
**Função:** Registrar novos produtos no catálogo

**Campos obrigatórios:**
- Nome do produto
- Tipo (calha, rufo, pingadeira)
- Medida (em centímetros)
- Preço por metro (R$)

**Campos opcionais:**
- Custo de produção por metro
- Descrição adicional

**Validações:**
- Nome não pode estar vazio
- Preço deve ser maior que zero
- Medida deve ser número positivo

#### 2.3 Edição de Produtos
**Função:** Atualizar informações de produtos existentes

- Permitir edição de todos os campos
- Manter histórico de alterações implicitamente (data de atualização)
- Validações iguais ao cadastro

#### 2.4 Exclusão de Produtos
**Função:** Remover produtos do catálogo

- Confirmação antes de excluir
- Verificar se o produto está em uso em orçamentos ativos
- Alerta se houver dependências

---

### 3. Gestão de Orçamentos

#### 3.1 Listagem de Orçamentos
**Função:** Visualizar todos os orçamentos cadastrados

- Listar orçamentos com: cliente, data, status, valor total
- Busca por nome do cliente ou endereço
- Filtro por status:
  - Rascunho (draft)
  - Enviado (sent)
  - Aprovado (approved)
  - Completado (completed)
- Ordenação por data (mais recente primeiro)
- Indicador visual do status (cores/badges)
- Contador de orçamentos

#### 3.2 Criação de Orçamento
**Função:** Gerar novo orçamento para cliente

**Informações do Cliente:**
- Nome completo (obrigatório)
- Telefone (opcional)
- Endereço completo (opcional)

**Itens do Orçamento:**
- Adicionar produtos do catálogo
- Para cada item:
  - Selecionar produto
  - Definir quantidade em metros
  - Preço automático (produto × metros)
  - Possibilidade de ajuste manual do preço
- Remover itens
- Cálculo automático do total

**Informações Técnicas:**
- Notas técnicas (opcional)
- Termos do contrato (opcional)
- Data de agendamento sugerida (opcional)

**Cálculos Financeiros:**
- Total do orçamento (soma de todos os itens)
- Custo total (se produtos tiverem custo cadastrado)
- Lucro estimado (total - custo)
- Margem de lucro (%)

#### 3.3 Detalhes do Orçamento
**Função:** Visualizar completo de um orçamento

**Exibir:**
- Todas as informações do cliente
- Lista completa de itens com subtotais
- Total, lucro e margem
- Status atual
- Data de criação
- Data de agendamento (se houver)
- Notas técnicas e termos

**Ações disponíveis:**
- Editar orçamento (se não aprovado)
- Excluir orçamento
- Enviar orçamento (mudar status para "enviado")
- Aprovar orçamento (mudar status para "aprovado")
- Completar orçamento (mudar status para "completado")
- Gerar PDF do orçamento
- Compartilhar via WhatsApp

#### 3.4 Geração de PDF
**Função:** Criar documento profissional do orçamento

**Conteúdo do PDF:**
- Cabeçalho com nome da empresa
- Número/ID do orçamento
- Data de emissão
- Dados do cliente
- Tabela de itens (produto, medida, qtd metros, preço unit., subtotal)
- Total geral destacado
- Notas técnicas (se houver)
- Termos do contrato (se houver)
- Informações de contato da empresa

**Recursos:**
- Download do PDF
- Visualização antes de salvar
- Nome do arquivo: `Orcamento_{Cliente}_{Data}.pdf`

#### 3.5 Edição de Orçamento
**Função:** Modificar orçamento existente

- Permitir edição apenas se status for "rascunho" ou "enviado"
- Bloquear edição de orçamentos aprovados/completados
- Atualizar automaticamente totais e cálculos
- Salvar histórico de modificações (data de atualização)

#### 3.6 Exclusão de Orçamento
**Função:** Remover orçamento do sistema

- Confirmação obrigatória
- Verificar se há instalação agendada vinculada
- Remover também itens relacionados

---

### 4. Gestão de Estoque/Inventário

#### 4.1 Listagem de Itens
**Função:** Visualizar estoque de materiais

- Listar todos os itens: nome, tipo, quantidade, unidade, estoque mínimo
- Busca por nome
- Filtro por tipo de material
- Indicador visual de estoque baixo (quantidade < mínimo)
- Alerta de itens em falta
- Contador de itens no estoque

#### 4.2 Cadastro de Item
**Função:** Adicionar material ao estoque

**Campos:**
- Nome do material (obrigatório)
- Tipo (chapa, selante, parafuso, etc.)
- Quantidade inicial (obrigatório)
- Unidade de medida (unidades, tubos, rolos)
- Estoque mínimo (para alertas)

#### 4.3 Atualização de Estoque
**Função:** Ajustar quantidade de materiais

- Adicionar entrada de estoque (compra)
- Registrar saída de estoque (uso)
- Ajuste manual de quantidade
- Histórico de movimentações

#### 4.4 Alertas de Estoque
**Função:** Notificar sobre materiais em falta

- Destacar visualmente itens abaixo do mínimo
- Badge com quantidade de alertas
- Lista de materiais para compra

---

### 5. Gestão de Instalações/Agenda

#### 5.1 Listagem de Instalações
**Função:** Visualizar agendamentos de instalação

- Listar instalações com: cliente, endereço, data, status
- Filtro por status:
  - Pendente (pending)
  - Em progresso (in-progress)
  - Completada (completed)
  - Cancelada (cancelled)
- Ordenação por data (próximas primeiro)
- Calendário visual (opcional)
- Contador de instalações

#### 5.2 Criação de Instalação
**Função:** Agendar nova instalação

**Informações:**
- Vincular a um orçamento aprovado (obrigatório)
- Cliente (herdado do orçamento)
- Endereço (herdado ou novo)
- Data e hora agendada (obrigatório)
- Notas adicionais (opcional)
- Status inicial: "pendente"

#### 5.3 Detalhes da Instalação
**Função:** Visualizar informações completas

**Exibir:**
- Dados do cliente
- Endereço completo
- Data/hora agendada
- Orçamento vinculado (com link)
- Itens a serem instalados
- Notas técnicas
- Status atual

**Ações:**
- Editar data/hora
- Alterar status
- Marcar como completada
- Cancelar instalação
- Ver mapa/localização (integração futura)

#### 5.4 Atualização de Status
**Função:** Acompanhar progresso da instalação

- Pendente → Em progresso → Completada
- Possibilidade de cancelar em qualquer etapa
- Ao completar, atualizar automaticamente orçamento para "completado"

---

### 6. Configurações do Sistema

#### 6.1 Informações da Empresa
**Função:** Personalizar dados da empresa

**Campos editáveis:**
- Nome da empresa
- Logotipo (upload de imagem)
- Telefone de contato
- E-mail
- Endereço
- CNPJ/CPF

**Uso:**
- Nome aparece no dashboard e PDFs
- Dados de contato aparecem nos orçamentos

#### 6.2 Informações do Sistema
**Função:** Exibir detalhes técnicos

- Versão atual do aplicativo
- Tipo de armazenamento (SQLite Local)
- Plataforma (Desktop)
- Última verificação de atualizações

#### 6.3 Gestão de Dados
**Função:** Controle de dados do sistema

**Recursos:**
- Backup do banco de dados
- Restaurar backup
- Exportar dados (CSV/JSON)
- Limpar todos os dados (com confirmação)
- Local do arquivo de banco de dados

---

## 🗄️ Modelo de Dados

### Tabelas Principais

#### Produtos
- `id` - Identificador único
- `name` - Nome do produto
- `type` - Tipo (calha/rufo/pingadeira)
- `measure` - Medida em cm
- `price_per_meter` - Preço por metro
- `cost` - Custo de produção (opcional)
- `created_at` - Data de criação
- `updated_at` - Data de atualização

#### Orçamentos
- `id` - Identificador único
- `client_name` - Nome do cliente
- `client_phone` - Telefone
- `client_address` - Endereço
- `total` - Valor total
- `status` - Status (draft/sent/approved/completed)
- `technical_notes` - Notas técnicas
- `contract_terms` - Termos do contrato
- `profit` - Lucro calculado
- `profitability` - Margem de lucro (%)
- `scheduled_date` - Data de agendamento
- `created_at` - Data de criação
- `updated_at` - Data de atualização

#### Itens do Orçamento
- `id` - Identificador único
- `quote_id` - Referência ao orçamento
- `product_id` - Referência ao produto
- `product_name` - Nome do produto (snapshot)
- `measure` - Medida do produto
- `meters` - Quantidade em metros
- `price_per_meter` - Preço por metro (snapshot)
- `total` - Subtotal do item
- `cost_per_meter` - Custo por metro (opcional)
- `cost_total` - Custo total do item

#### Inventário
- `id` - Identificador único
- `name` - Nome do material
- `type` - Tipo de material
- `quantity` - Quantidade atual
- `unit` - Unidade de medida
- `min_stock` - Estoque mínimo
- `created_at` - Data de criação
- `updated_at` - Data de atualização

#### Instalações
- `id` - Identificador único
- `quote_id` - Referência ao orçamento
- `client_name` - Nome do cliente
- `address` - Endereço da instalação
- `scheduled_date` - Data agendada
- `status` - Status (pending/in-progress/completed/cancelled)
- `notes` - Notas adicionais
- `created_at` - Data de criação
- `updated_at` - Data de atualização

---

## 🔄 Fluxos de Trabalho Principais

### Fluxo 1: Criação de Orçamento → Instalação
1. Cliente solicita orçamento
2. Usuário cria novo orçamento (status: rascunho)
3. Adiciona produtos e quantidades
4. Revisa e envia ao cliente (status: enviado)
5. Cliente aprova (status: aprovado)
6. Sistema cria instalação vinculada
7. Instalação é agendada
8. Instalação é realizada (status: em progresso)
9. Instalação completada
10. Orçamento atualizado (status: completado)

### Fluxo 2: Gestão de Estoque
1. Usuário cadastra materiais necessários
2. Define estoque mínimo para cada item
3. Sistema monitora quantidades
4. Alerta quando estoque está baixo
5. Usuário registra compras (entrada)
6. Usuário registra uso em instalações (saída)

### Fluxo 3: Geração de PDF
1. Usuário visualiza orçamento
2. Clica em "Gerar PDF"
3. Sistema compila dados do orçamento
4. Formata documento profissional
5. Exibe preview
6. Usuário baixa ou compartilha

---

## 🎨 Requisitos de Interface

### Princípios de Design
- Interface limpa e moderna
- Responsiva (adaptável a diferentes tamanhos de tela)
- Navegação intuitiva
- Feedback visual claro
- Cores profissionais
- Ícones consistentes

### Componentes Visuais Necessários
- Cards para estatísticas
- Tabelas para listagens
- Formulários de cadastro
- Modais de confirmação
- Botões de ação
- Badges de status
- Alertas e notificações
- Barra de navegação
- Campos de busca
- Filtros e ordenação

### Paleta de Cores Sugerida
- Primária: Azul profissional (#2563eb)
- Sucesso: Verde (#10b981)
- Alerta: Amarelo (#f59e0b)
- Erro: Vermelho (#ef4444)
- Neutros: Cinzas para backgrounds e textos

---

## ⚙️ Requisitos Técnicos

### Tecnologia Recomendada (Python)

#### Banco de Dados
- **SQLite** para armazenamento local
- Biblioteca: `sqlite3` (nativa) ou `SQLAlchemy` (ORM)
- Arquivo único de banco de dados
- Suporte a transações
- Backup automático

#### Interface Gráfica

**CustomTkinter** (Implementado na v2.0)
- Tkinter modernizado com renderização CPU (sem problemas com GPU)
- Temas dark/light integrados
- Widgets customizados e visual moderno
- Performance excelente e estabilidade comprovada
- Não depende de engines externas (Flutter, Chromium)

> **Motivo da mudança (v2.0):** O Flet (Flutter) causava crashes do driver GPU
> e reinício do monitor em caso de erros. O CustomTkinter usa renderização CPU
> nativa do sistema operacional, eliminando completamente esse problema.

#### Geração de PDF
- Biblioteca: `reportlab` ou `fpdf2`
- Templates personalizáveis
- Suporte a imagens e tabelas
- Fontes customizadas

#### Utilitários
- `python-dotenv` - Configurações
- `pillow` - Manipulação de imagens
- `qrcode` - Geração de QR codes (opcional)

---

## 📱 Recursos Adicionais (Futuros)

### Integrações
- WhatsApp Business API (envio de orçamentos)
- Google Maps (localização de instalações)
- E-mail SMTP (envio automático de PDFs)
- Backup em nuvem (Google Drive, Dropbox)

### Recursos Avançados
- Multiusuário com permissões
- Sincronização entre dispositivos
- Relatórios gerenciais avançados
- Gráficos de evolução financeira
- Previsão de demanda
- Controle de fornecedores
- Histórico de comunicação com clientes

### Mobile
- Versão mobile para consultas rápidas
- Checklist de instalação offline
- Captura de fotos da obra
- Assinatura digital do cliente

---

## 📊 Métricas e Relatórios

### Dashboard Metrics
- Total de orçamentos por período
- Taxa de conversão (enviados → aprovados)
- Ticket médio
- Faturamento mensal
- Lucro mensal
- Produtos mais vendidos

### Relatórios Geráveis
- Orçamentos por status
- Instalações agendadas
- Faturamento por período
- Produtos mais utilizados
- Clientes frequentes
- Evolução de vendas

---

## 🔐 Segurança e Privacidade

### Dados
- Banco de dados local (sem exposição online)
- Backup automático periódico
- Criptografia de dados sensíveis (opcional)
- Política de retenção de dados

### Controle de Acesso (Futuro)
- Login com senha
- Diferentes níveis de permissão
- Log de atividades
- Bloqueio após tentativas falhas

---

## 📝 Validações e Regras de Negócio

### Produtos
- Nome único (não duplicar produtos idênticos)
- Preço sempre positivo
- Alerta ao excluir produto usado em orçamentos

### Orçamentos
- Pelo menos 1 item obrigatório
- Total sempre maior que zero
- Status segue fluxo: draft → sent → approved → completed
- Não pode editar orçamentos aprovados
- Ao completar instalação, marcar orçamento como completado

### Estoque
- Quantidade não pode ser negativa
- Alerta quando abaixo do mínimo
- Sugestão de compra baseada em histórico

### Instalações
- Sempre vinculada a orçamento aprovado
- Data agendada no futuro
- Não agendar múltiplas instalações no mesmo horário

---

## 🚀 Roadmap de Implementação Sugerido

### Fase 1: MVP (Minimum Viable Product)
1. Cadastro de produtos
2. Criação de orçamentos
3. Geração de PDF básico
4. Dashboard simples
5. Banco de dados SQLite

### Fase 2: Gestão Completa
1. Estoque/inventário
2. Agendamento de instalações
3. Filtros e buscas avançadas
4. Melhorias no PDF

### Fase 3: Automação
1. Cálculos automáticos de lucro
2. Alertas de estoque
3. Backup automático
4. Exportação de dados

### Fase 4: Recursos Avançados
1. Relatórios gerenciais
2. Gráficos e métricas
3. Integrações (WhatsApp, Email)
4. Multiusuário

---

## 📖 Conclusão

Este documento descreve um sistema completo de gestão para empresas de calhas. A implementação em Python com SQLite e um framework moderno de UI proporcionará uma solução nativa, rápida e profissional, sem dependência de servidores externos ou conexão com internet.

**Próximos Passos:**
1. ~~Escolher framework de UI~~ ✅ CustomTkinter (v2.0 - substituiu Flet por instabilidade GPU)
2. ~~Configurar ambiente Python~~ ✅
3. ~~Criar estrutura de banco de dados SQLite~~ ✅
4. ~~Implementar módulos seguindo as funcionalidades descritas~~ ✅
5. Testar e iterar

### Histórico de Versões

#### v2.0 - Migração para CustomTkinter
- **Mudança principal:** Framework de UI migrado de Flet (Flutter) para CustomTkinter
- **Motivo:** Flet/Flutter causava crash do driver GPU e reinício do monitor em erros
- **Benefícios:** Renderização CPU nativa, estabilidade total, sem dependência de engine gráfica externa
- **Estrutura mantida:** Banco de dados (SQLite), gerador de PDF (fpdf2), gráficos (matplotlib)
- **Todas as funcionalidades preservadas:** Dashboard, Produtos, Orçamentos, Estoque, Instalações, Relatórios, Configurações

#### v1.0 - Versão Inicial
- Interface com Flet (Flutter para Python)
- Todas as funcionalidades base implementadas
- Problema: instabilidade GPU em algumas máquinas
