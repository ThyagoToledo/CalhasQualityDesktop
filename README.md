<div align="center">

<img src="icon/CaLHAS.png" width="120" alt="CalhaGest Logo">

# CalhaGest - Sistema de Gestão de Calhas

**Aplicativo desktop profissional para gestão de orçamentos, instalações, estoque e produtos para empresas de calhas.**

[![Windows](https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/ThyagoToledo/CalhasQualityDesktop/releases/latest)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

---

</div>

##  Funcionalidades

| Módulo | Descrição |
|--------|-----------|
| **Dashboard** | Visão geral com estatísticas e indicadores do negócio |
| **Orçamentos** | Criar, editar e gerar PDFs profissionais de orçamentos |
| **Produtos** | Catálogo de produtos com preços por metro |
| **Estoque** | Controle de materiais com alerta de estoque mínimo |
| **Instalações** | Agendamento com calendário visual e histórico |
| **Analíticos** | Gráficos de faturamento, evolução financeira e filtros por período |
| **Configurações** | Dados da empresa e alternância de tema claro/escuro |

##  Screenshots

### PDF Profissional
- Layout inspirado no fazerorcamento.com
- Header azul com logo da empresa
- Tabela de preços com badges verdes
- Ícones Bootstrap para métodos de pagamento
- Assinaturas e data por extenso

##  Instalação

### Rodar via Python
```bash
# Clone o repositório
git clone https://github.com/ThyagoToledo/CalhasQualityDesktop.git
cd CalhasQualityDesktop

# Instale as dependências
pip install -r requirements.txt

# Execute
python main.py
```

##  Tecnologias

- **Python 3.11** — Linguagem principal
- **CustomTkinter** — Interface gráfica moderna (renderização CPU)
- **SQLite** — Banco de dados local
- **fpdf2** — Geração de PDFs profissionais
- **Matplotlib** — Gráficos e analíticos
- **Pillow** — Processamento de imagens
- **Bootstrap Icons** — Ícones SVG para PDFs

## 📁 Estrutura do Projeto

```
CalhasQualityDesktop/
├── main.py                 # Ponto de entrada
├── requirements.txt        # Dependências
├── database/
│   └── db.py              # CRUD SQLite
├── views/
│   ├── dashboard.py       # Painel principal
│   ├── quotes.py          # Orçamentos
│   ├── products.py        # Produtos
│   ├── inventory.py       # Estoque
│   ├── installations.py   # Instalações + Calendário
│   ├── analytics.py       # Gráficos + Filtros
│   └── settings.py        # Configurações
├── components/
│   ├── cards.py           # Cards e badges
│   ├── dialogs.py         # DateEntry, TimeEntry
│   └── navigation.py     # Sidebar
├── services/
│   └── pdf_generator.py   # Gerador de PDF
├── analytics/
│   └── charts.py          # Gráficos matplotlib
└── icon/
    ├── CaLHAS.png         # Logo
    └── payment/           # Ícones de pagamento SVG
```

##  Licença

Este projeto é de uso privado da **Calhas Quality**.

---

<div align="center">

**Desenvolvido com ❤️ para Calhas Quality**

</div>
