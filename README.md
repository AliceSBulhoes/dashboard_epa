# Dashboard EPA - Sistema de Monitoramento Hidrogeológico

## 📋 Visão Geral

Este projeto é um dashboard interativo desenvolvido em **Streamlit** para análise e visualização de dados hidrogeológicos e de remediação ambiental. O sistema permite o upload de arquivos Excel com múltiplas planilhas contendo dados de poços de monitoramento, volumes bombeados, fase livre (FL) e parâmetros hidrogeológicos.

## 🎯 Funcionalidades Principais

- **Autenticação de Usuários**: Sistema de login com credenciais pré-definidas
- **Upload de Dados**: Suporte para arquivos Excel com múltiplas planilhas
- **Visualizações Interativas**: Gráficos dinâmicos usando Plotly
- **Filtros Avançados**: Filtragem por data, categoria, poços e tipos de dados
- **KPIs em Tempo Real**: Cards com métricas importantes
- **Download de Dados**: Exportação de gráficos (HTML/PNG) e dados brutos (Excel)

## 📁 Estrutura do Projeto

```
dashboard_epa/
│
├── app.py                          # Arquivo principal da aplicação
├── requirements.txt                # Dependências do projeto
│
├── pages/                          # Páginas do dashboard
│   ├── login.py                    # Página de autenticação
│   └── dashboard.py                # Página principal com visualizações
│
├── utils/                          # Utilitários e funções auxiliares
│   ├── __init__.py                 # Exportações do módulo utils
│   ├── auth.py                     # Sistema de autenticação
│   ├── date_filters.py             # Funções de filtragem e agregação temporal
│   └── tratando_excel.py           # Processamento e limpeza de dados
│
├── components/                     # Componentes reutilizáveis
│   ├── __init__.py                 # Exportações do módulo components
│   └── btn/                        # Componentes de botão
│       ├── __init__.py             # Exportações do submódulo btn
│       └── btn_download.py         # Botões de download (HTML, PNG, Excel)
│
└── data/                           # Diretório para armazenamento de dados
```

## 🔧 Componentes Detalhados

### **app.py** - Aplicação Principal
O arquivo principal que inicializa e configura a aplicação Streamlit.

**Principais funções:**
- `config_page()`: Configura título, ícone e layout da página
- `navbar()`: Cria barra de navegação dinâmica baseada no estado de autenticação
- `css()`: Aplica estilos personalizados (fonte Mulish)
- `main()`: Função principal que orquestra a aplicação

### **pages/login.py** - Página de Login
Gerencia a interface de autenticação do usuário.

**Funcionalidades:**
- Formulário de login com campos de usuário e senha
- Validação de credenciais
- Redirecionamento após login bem-sucedido
- Mensagens de erro para credenciais inválidas

### **pages/dashboard.py** - Dashboard Principal
Núcleo da aplicação, contendo todas as visualizações e análises.

**Características:**
- **Upload de Arquivos**: Aceita múltiplos arquivos Excel
- **Processamento de Planilhas**: 
  - Volume Bombeado
  - Volume Produto
  - FL (Fase Livre)
  - Hidrômetros
- **Três Modos de Visualização**:
  1. **FL (Fase Livre)**: Análise de níveis de água (NA), óleo (NO) e espessura
  2. **Volume Produto**: Monitoramento de remoção SAO e Bailer
  3. **Volume Bombeado**: Acompanhamento de volumes bombeados

**KPIs Exibidos:**
- Volume Removido SAO/Bailer Atual
- Volume Acumulado
- Dias Sem Registro
- Número de Poços em Operação

### **utils/auth.py** - Sistema de Autenticação
Gerencia autenticação e autorização de usuários.

**Funcionalidades:**
- `verify_credentials()`: Valida usuário e senha
- `require_authentication()`: Verifica se usuário está autenticado
- Credenciais padrão: `username: admin` | `password: admin123`

### **utils/tratando_excel.py** - Processamento de Dados
Funções para limpeza e transformação de DataFrames.

**Funções principais:**
- `tratando_df()`: Remove colunas "Unnamed" e linhas sem data
- `fillna_columns()`: Preenche valores NaN em colunas específicas
- `add_accumulated_column()`: Calcula valores acumulados
- `filter_by_date()`: Filtra dados por intervalo de datas

### **utils/date_filters.py** - Filtros Temporais Avançados
Sistema robusto para manipulação de datas e agregações temporais.

**Funções principais:**
- `ensure_datetime()`: Garante conversão para datetime
- `clamp_date_range()`: Filtragem por intervalo de datas
- `granularity_to_freq()`: Converte granularidades em frequências pandas
- `aggregate_by_period()`: Agrega dados por período (diário, semanal, mensal, anual)
- `add_cumulative()`: Adiciona colunas cumulativas
- `full_period_index()`: Cria índice contínuo de datas

### **components/btn/btn_download.py** - Botões de Download
Componentes para exportação de dados e visualizações.

**Funcionalidades:**
- `btn_download_multiple()`: Download de múltiplos gráficos (HTML/PNG/ZIP)
- `btn_download_excel()`: Export de DataFrames para Excel
- `convert_fig_to_html()`: Converte gráficos Plotly para HTML
- `fig_to_png_bytes()`: Converte gráficos para PNG (requer Kaleido)

## 🚀 Como Executar

### Pré-requisitos
- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

### Instalação

1. Clone o repositório ou baixe os arquivos:
```bash
cd dashboard_epa
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

### Executar a Aplicação

```bash
streamlit run app.py
```

O dashboard será aberto automaticamente no navegador padrão (geralmente em `http://localhost:8501`).

## 📦 Dependências

```
streamlit>=1.33        # Framework web para data apps
pandas>=2.0            # Manipulação de dados
numpy>=1.24            # Computação numérica
plotly>=5.18           # Gráficos interativos
openpyxl>=3.1          # Leitura de arquivos Excel
matplotlib>=3.7        # Visualizações estáticas
seaborn>=0.12          # Visualizações estatísticas
xlsxwriter             # Escrita de arquivos Excel
```

## 🔐 Autenticação

**Credenciais padrão:**
- **Usuário**: `admin`
- **Senha**: `admin123`

⚠️ **Nota de Segurança**: Para ambientes de produção, recomenda-se:
- Usar variáveis de ambiente para credenciais
- Implementar hash de senhas
- Integrar com sistemas de autenticação externos (OAuth, LDAP, etc.)

## 📊 Formato dos Dados de Entrada

O sistema espera arquivos Excel (.xlsx) com as seguintes planilhas:

### 1. **Volume Bombeado**
- `Data`: Data da medição
- `Volume Bombeado (L)`: Volume em litros

### 2. **Volume Produto**
- `Data`: Data da medição
- `Volume Removido SAO (L)`: Volume removido via SAO
- `Volume Removido Bailer (L)`: Volume removido via Bailer

### 3. **FL (Fase Livre)**
- `Data`: Data da medição
- `Poço`: Identificação do poço
- `NA (m)`: Nível de água em metros
- `NO (m)`: Nível de óleo em metros
- `Esp. (m)`: Espessura de óleo em metros

### 4. **Hidrômetros**
- `Data`: Data da medição
- Outras colunas específicas de hidrômetros

## 🎨 Funcionalidades de Visualização

### Gráficos FL (Fase Livre)
- Gráficos de barras agrupados por poço
- Filtros por poço e tipo de medição
- Comparação de NA, NO e Espessura

### Gráficos Volume Produto
- Gráfico de linha para volume acumulado
- Gráficos de barras para volumes removidos
- KPIs de performance

### Gráficos Volume Bombeado
- Gráfico de linha para volume acumulado
- Gráfico de barras para volume bombeado
- Indicadores de operação

## 📥 Exportação de Dados

### Formatos Disponíveis:
1. **HTML**: Gráficos interativos em um único arquivo
2. **PNG**: Imagens dos gráficos em arquivo ZIP (requer Kaleido)
3. **Excel**: Dados brutos filtrados em formato .xlsx

## 🛠️ Personalização

### Alterar Credenciais
Edite o arquivo `utils/auth.py`:
```python
PREDEFINED_CREDENTIALS = {
    "username": "seu_usuario",
    "password": "sua_senha",
}
```

### Alterar Logo
Modifique a URL no `app.py` e `pages/login.py`:
```python
st.logo("URL_DO_SEU_LOGO")
```

### Modificar Cores dos Cards
No arquivo `pages/dashboard.py`, função `card()`:
```python
card("Título", valor, "emoji", color="#HEX_COLOR")
```

## 🐛 Solução de Problemas

### Erro ao fazer upload de arquivos
- Verifique se o arquivo possui as planilhas corretas
- Certifique-se de que as colunas obrigatórias existem
- Verifique se há dados válidos na coluna 'Data'

### Gráficos não aparecem
- Verifique se selecionou pelo menos uma opção nos filtros
- Confirme se há dados no intervalo de datas selecionado

### PNG não disponível
- Instale o Kaleido: `pip install kaleido`
- Caso esteja no Streamlit Cloud, use download em HTML

## 📝 Notas de Desenvolvimento

- **Sessão do Streamlit**: O sistema usa `st.session_state` para gerenciar autenticação
- **Cache**: Não há cache implementado - considerar adicionar `@st.cache_data` para melhor performance
- **Dados Temporários**: Arquivos são processados em memória, não são salvos permanentemente

## 🔮 Melhorias Futuras

- [ ] Implementar cache para dados processados
- [ ] Adicionar suporte para mais formatos de arquivo (CSV, JSON)
- [ ] Criar visualizações de mapas geoespaciais
- [ ] Implementar relatórios automáticos em PDF
- [ ] Adicionar análises estatísticas avançadas
- [ ] Criar API REST para integração com outros sistemas
- [ ] Implementar testes automatizados
- [ ] Adicionar logs de auditoria

## 👥 Contribuindo

Para contribuir com o projeto:
1. Faça um fork do repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto é propriedade do Grupo EPA.

## 📧 Contato

Para dúvidas ou suporte, entre em contato através do site: [https://grupoepa.net.br](https://grupoepa.net.br)

---

**Desenvolvido com ❤️ para o Grupo EPA**
