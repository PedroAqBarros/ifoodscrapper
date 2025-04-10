import tkinter as tk
from tkinter import *
from tkinter import scrolledtext, messagebox
import threading
import pandas as pd
from datetime import datetime
import random
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials

from drivers.selenium_driver import configurar_driver
from utils.helpers import salvar_cookies, carregar_cookies, aceitar_cookies, salvar_screenshot
from scrapers.ifood_scraper import fazer_login_ifood, definir_endereco, buscar_mercado, buscar_produto

class IFoodScraperGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("iFood Price Scraper")
        self.setup_gui()
        self.root.config(background="#444654")
    def setup_gui(self):
        # Cidade Input
        cidade_label = tk.Label(self.root, text="Cidade:")
        cidade_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.cidade_entry = tk.Entry(self.root, width=50)
        self.cidade_entry.grid(row=0, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        self.cidade_entry.insert(0, "Goiânia, GO")

        # Mercados Input
        mercados_label = tk.Label(self.root, text="Mercados (um por linha):")
        mercados_label.grid(row=1, column=0, sticky="nw", padx=5, pady=5)
        self.mercados_entry = scrolledtext.ScrolledText(self.root, height=5, width=50)
        self.mercados_entry.grid(row=1, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        self.mercados_entry.insert(tk.END, "Atacadão\nAssaí\nCarrefour\nBretas")

        # Produtos Input
        produtos_label = tk.Label(self.root, text="Produtos (um por linha):")
        produtos_label.grid(row=2, column=0, sticky="nw", padx=5, pady=5)
        self.produtos_entry = scrolledtext.ScrolledText(self.root, height=5, width=50)
        self.produtos_entry.grid(row=2, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        self.produtos_entry.insert(tk.END, "creme de leite\nleite condensado\nleite\narroz 5kg\nfeijão carioca\naçúcar\nóleo de soja")

        # Start Button
        start_button = tk.Button(self.root, text="Iniciar Coleta de Preços", command=self.start_scraping)
        start_button.grid(row=3, column=0, columnspan=3, pady=10)

        # Output Text Area
        output_label = tk.Label(self.root, text="Log de Saída:")
        output_label.grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.output_text = scrolledtext.ScrolledText(self.root, height=10, width=70, state=tk.DISABLED)
        self.output_text.grid(row=5, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

        self.root.columnconfigure(1, weight=1)

    def print_to_gui(self, text):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, text + "\n")
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)

    def start_scraping(self):
        produtos_str = self.produtos_entry.get("1.0", tk.END).strip()
        mercados_str = self.mercados_entry.get("1.0", tk.END).strip()
        cidade_busca = self.cidade_entry.get().strip()

        produtos = [p.strip() for p in produtos_str.splitlines() if p.strip()]
        mercados_busca = [m.strip() for m in mercados_str.splitlines() if m.strip()]

        if not produtos or not mercados_busca or not cidade_busca:
            messagebox.showerror("Erro", "Por favor, preencha todos os campos (Produtos, Mercados e Cidade).")
            return

        self.output_text.delete("1.0", tk.END)
        self.print_to_gui(f"Iniciando a coleta de preços para os mercados: {', '.join(mercados_busca)}")
        self.print_to_gui(f"Produtos a serem buscados: {', '.join(produtos)}")
        self.print_to_gui(f"Cidade de busca: {cidade_busca}")

        threading.Thread(target=self.run_scraper, args=(produtos, mercados_busca, cidade_busca), daemon=True).start()

    def run_scraper(self, produtos, mercados_busca, cidade_busca):
        try:
            self.coletar_precos(produtos, mercados_busca, cidade_busca)
            self.print_to_gui("Processo de scraping finalizado.")
            messagebox.showinfo("Concluído", "Coleta de preços finalizada com sucesso!")
        except Exception as e:
            self.print_to_gui(f"Erro geral no scraping: {e}")
            messagebox.showerror("Erro", f"Erro durante o scraping: {e}")

    def conectar_google_sheets(self, precos_ifood):
        scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']

        credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(credentials)

        spreadsheet_id = '1oGjtfzZ7rhF4qWzEQ-wMPO042AhHo_jACv2L040uXAQ'
        planilha = client.open_by_key(spreadsheet_id)
        worksheet = planilha.get_worksheet(0)

        return worksheet

    def coletar_precos(self, produtos, mercados_busca, cidade_busca):
        worksheet = None
        try:
            worksheet = self.conectar_google_sheets('Preços iFood Mercados')
            self.print_to_gui("Conectado ao Google Sheets com sucesso.")
        except Exception as e:
            self.print_to_gui(f"Erro ao conectar ao Google Sheets: {str(e)}")
            self.print_to_gui("Continuando sem salvar no Google Sheets.")

        data_coleta = datetime.now().strftime('%d/%m/%Y %H:%M')
        dados_coletados = []
        session_state = {
            'logged_in': False,
            'address_set': False,
            'current_market': None
        }

        driver = configurar_driver()

        try:
            driver.get("https://www.ifood.com.br/")
            time.sleep(0.5)

            if carregar_cookies(driver, self.print_to_gui):
                session_state['logged_in'] = True
                session_state['address_set'] = True
                self.print_to_gui("Sessão anterior restaurada, pulando login e endereço")

                driver.quit()
                driver = configurar_driver(headless=True)
                driver.get("https://www.ifood.com.br/mercados")
                time.sleep(0.5)
                self.print_to_gui("Driver trocado para modo headless.")
            else:
                if fazer_login_ifood(driver, self.print_to_gui):
                    session_state['logged_in'] = True
                    salvar_cookies(driver, self.print_to_gui)

                if not session_state['address_set']:
                    if definir_endereco(driver, cidade_busca, self.print_to_gui):
                        session_state['address_set'] = True
                        salvar_cookies(driver, self.print_to_gui)

                self.print_to_gui("Trocando driver para modo headless após login e endereço.")
                driver.quit()
                driver = configurar_driver(headless=True)
                driver.get("https://www.ifood.com.br/mercados")
                time.sleep(0.5)
                self.print_to_gui("Driver trocado para modo headless.")

            for nome_mercado in mercados_busca:
                if session_state['current_market'] != nome_mercado:
                    mercado = buscar_mercado(driver, cidade_busca, nome_mercado, self.print_to_gui)
                    if mercado:
                        session_state['current_market'] = nome_mercado

                self.print_to_gui(f"\nBuscando mercado: {nome_mercado}")

                if not mercado:
                    self.print_to_gui(f"Não foi possível acessar o mercado {nome_mercado} após várias tentativas. Pulando para o próximo.")
                    salvar_screenshot(driver, f"erro_final_mercado_{nome_mercado}", self.print_to_gui)
                    continue

                self.print_to_gui(f"Mercado encontrado: {mercado['nome']}")
                self.print_to_gui(f"URL: {mercado['url']}")

                for produto in produtos:
                    self.print_to_gui(f"\n  Buscando produto: {produto}")
                    time.sleep(random.uniform(0.5, 1.5))

                    resultados = buscar_produto(driver, produto, self.print_to_gui)

                    if resultados:
                        self.print_to_gui(f"  Encontrados {len(resultados)} resultados para '{produto}':")
                        for resultado in resultados:
                            self.print_to_gui(f"    - {resultado['nome']}")
                            self.print_to_gui(f"      Detalhes: {resultado['detalhes']}")
                            self.print_to_gui(f"      Preço: R$ {resultado['preco']}")

                            dados_coletados.append([
                                data_coleta,
                                mercado['nome'],
                                f"{resultado['nome']} {resultado['detalhes']}".strip(),
                                f"R$ {resultado['preco']}"
                            ])
                    else:
                        self.print_to_gui(f"  Nenhum produto encontrado para: {produto}")
                        salvar_screenshot(driver, f"erro_produto_{nome_mercado}_{produto.replace(' ', '_')}", self.print_to_gui)

                        dados_coletados.append([
                            data_coleta,
                            mercado['nome'],
                            produto,
                            "Não encontrado"
                        ])

                time.sleep(0.5)
                salvar_cookies(driver, self.print_to_gui)

        except Exception as e:
            self.print_to_gui(f"Erro durante a execução: {str(e)}")
            salvar_screenshot(driver, "erro_execucao", self.print_to_gui)
            messagebox.showerror("Erro", f"Ocorreu um erro durante a execução: {str(e)}. Veja o log na interface.")

        finally:
            salvar_cookies(driver, self.print_to_gui)
            driver.quit()

        if worksheet and dados_coletados:
            try:
                worksheet.append_rows(dados_coletados)
                self.print_to_gui("Dados salvos no Google Sheets com sucesso (em lote).")
            except Exception as e:
                self.print_to_gui(f"Erro ao salvar no Google Sheets (em lote): {str(e)}")

        if dados_coletados:
            df = pd.DataFrame(dados_coletados, columns=['Data', 'Mercado', 'Produto', 'Preço'])
            df.to_excel('precos_ifood_backup.xlsx', index=False)
            self.print_to_gui(f"\nColeta finalizada! Dados salvos no arquivo 'precos_ifood_backup.xlsx'")
            return df
        else:
            self.print_to_gui("\nNenhum dado foi coletado durante a execução.")
            return pd.DataFrame(columns=['Data', 'Mercado', 'Produto', 'Preço'])

    def run(self):
        self.root.mainloop() 