# iFood Scraper

Um aplicativo para extrair informações de restaurantes do iFood.

## Descrição

Este projeto é um scraper para o iFood que permite extrair informações de restaurantes, incluindo cardápios, preços e avaliações.

## Estrutura do Projeto

```
ifoodscrapper/
├── src/
│   ├── drivers/     # Drivers para automação
│   ├── gui/         # Interface gráfica (Tkinter)
│   ├── scrapers/    # Lógica de scraping
│   ├── utils/       # Utilitários
│   └── main.py      # Ponto de entrada da aplicação
├── .gitignore
└── README.md
```

## Requisitos

- Python 3.8+
- Tkinter (incluído na instalação padrão do Python)
- Selenium (automação de navegador)
- Pandas (manipulação de dados)
- Gspread e OAuth2Client (integração com Google Sheets)
- Outras dependências listadas em requirements.txt

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/ifoodscrapper.git
cd ifoodscrapper
```

2. Crie um ambiente virtual e ative-o:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure o acesso ao Google Sheets (opcional):
   - Crie credenciais de serviço no Google Cloud Platform
   - Baixe o arquivo JSON de credenciais
   - Renomeie-o para `credentials.json` e coloque-o no diretório raiz do projeto

## Uso

Execute o arquivo main.py:
```bash
python src/main.py
```

A interface gráfica será aberta, permitindo que você:
1. Defina a cidade para a busca
2. Liste os mercados a serem buscados
3. Liste os produtos a serem pesquisados
4. Inicie a coleta de preços

Os resultados serão salvos em um arquivo Excel (`precos_ifood_backup.xlsx`) e, se configurado, também no Google Sheets.

## Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes. 