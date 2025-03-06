import pandas as pd
from datetime import datetime
import time
import random
import gspread
import pickle
import os.path
from oauth2client.service_account import ServiceAccountCredentials
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys

import tkinter as tk
from tkinter import scrolledtext, ttk
from tkinter import messagebox
import threading
from ttkthemes import ThemedStyle

def conectar_google_sheets(precos_ifood):
    """Conecta à API do Google Sheets e retorna a planilha especificada."""
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

    credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(credentials)

    # Abre a planilha específica pelo ID
    spreadsheet_id = '1oGjtfzZ7rhF4qWzEQ-wMPO042AhHo_jACv2L040uXAQ'
    planilha = client.open_by_key(spreadsheet_id)
    worksheet = planilha.get_worksheet(0)  # Pega a primeira aba

    return worksheet


def configurar_driver():
    """Configura e retorna um driver Selenium com configurações aprimoradas (modo visível)."""
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    import os

    # Define um diretório específico para o perfil do Chrome
    user_data_dir = os.path.join(os.getcwd(), 'chrome_profile')
    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir)

    chrome_options = Options()
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    return driver

def configurar_driver_headless():
    """Configura e retorna um driver Selenium em modo headless (segundo plano) com User-Agent."""
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    import os

    # Define um diretório específico para o perfil do Chrome
    user_data_dir = os.path.join(os.getcwd(), 'chrome_profile')
    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir)

    chrome_options = Options()
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options.add_argument("--start-maximized") # Headless doesn't need maximized
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("--headless=new") # Enable headless mode

    # **Set a realistic User-Agent string:**
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" # Example User-Agent (current Chrome)
    chrome_options.add_argument(f"user-agent={user_agent}")


    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    return driver


def salvar_cookies(driver):
    """Salva os cookies atuais do navegador."""
    try:
        pickle.dump(driver.get_cookies(), open("cookies.pkl", "wb"))
        print_to_gui("Cookies salvos com sucesso.")
    except Exception as e:
        print_to_gui(f"Erro ao salvar cookies: {e}")

def carregar_cookies(driver):
    """Carrega cookies salvos anteriormente, se existirem."""
    try:
        if os.path.exists("cookies.pkl"):
            cookies = pickle.load(open("cookies.pkl", "rb"))
            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    print_to_gui(f"Erro ao adicionar cookie: {e}")
            print_to_gui("Cookies carregados com sucesso.")
            return True
        else:
            print_to_gui("Nenhum arquivo de cookies encontrado.")
            return False
    except Exception as e:
        print_to_gui(f"Erro ao carregar cookies: {e}")
        return False

def aceitar_cookies(driver):
    """Tenta aceitar cookies se o aviso aparecer."""
    try:
        # Espera até 0.5 segundos pelo botão de aceitar cookies
        botao_cookies = WebDriverWait(driver, 0.5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Aceitar') or contains(text(), 'aceitar') or contains(text(), 'OK')]"))
        )
        botao_cookies.click()
        print_to_gui("Cookies aceitos com sucesso.")
    except TimeoutException:
        # Se não encontrar o botão, provavelmente não há aviso de cookies
        print_to_gui("Nenhum aviso de cookies detectado ou já foi aceito anteriormente.")
    except Exception as e:
        print_to_gui(f"Erro ao tentar aceitar cookies: {str(e)}")

def fazer_login_ifood(driver):
    """Aguarda o login manual do usuário no iFood."""
    try:
        # Acessa a página principal do iFood
        driver.get("https://www.ifood.com.br/")
        time.sleep(0.5) # Reduced delay

        # Aceita cookies se necessário
        aceitar_cookies(driver)

        # Clica no botão de entrar/login
        try:
            botao_entrar = WebDriverWait(driver, 0.5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Entrar') or contains(@data-test-id, 'login-button')]"))
            )
            botao_entrar.click()

            print_to_gui("Por favor, faça login manualmente na janela do navegador.")
            print_to_gui("Aguardando login... (60 segundos)")

            # Aguarda até que o usuário esteja logado verificando elementos que só aparecem após o login
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(@data-test-id, 'user-menu')]"))
            )

            print_to_gui("Login realizado com sucesso!")
            time.sleep(0.5)
            return True

        except TimeoutException:
            print_to_gui("Tempo excedido para login ou usuário já está logado.")
            return False

    except Exception as e:
        print_to_gui(f"Erro durante o processo de login: {str(e)}")
        return False
def definir_endereco(driver, cidade):
    """Define um endereço específico ou usa a localização atual."""
    try:
        # Procura pela tela de endereço que apareceu no screenshot
        try:
            # Verifica se a tela de "Onde você quer receber seu pedido?" está presente
            texto_tela = WebDriverWait(driver, 1).until(
                EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), 'Onde você quer receber seu pedido?')]"))
            )

            # Tenta usar a opção "Usar minha localização"
            botao_localização = WebDriverWait(driver, 1).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Usar minha localização') or contains(@data-test-id, 'use-location-button')]"))
            )
            botao_localização.click()
            time.sleep(0.5) # Reduced delay

            # Se pedir permissão para acessar localização, aceitar no browser
            print_to_gui("Usando localização atual. Aceite a permissão no navegador se solicitado.")
            time.sleep(0.5) # Reduced delay

            return True
        except TimeoutException:
            # Se não encontrar a tela de localização atual, tente buscar o endereço
            try:
                # Clique no botão de escolher endereço no topo da página
                botao_endereco = WebDriverWait(driver, 1).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Escolha um endereço') or contains(@data-test-id, 'address-button')]"))
                )
                botao_endereco.click()
                time.sleep(0.5) # Reduced delay

                # Preenche o campo de busca de endereço
                campo_busca = WebDriverWait(driver, 1).until(
                    EC.element_to_be_clickable((By.XPATH, "//input[contains(@placeholder, 'Buscar endereço') or contains(@data-test-id, 'address-search-input')]"))
                )
                campo_busca.clear()
                campo_busca.send_keys(cidade)
                time.sleep(0.5) # Reduced delay

                # Seleciona o primeiro resultado
                primeiro_resultado = WebDriverWait(driver, 0.5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@data-test-id, 'address-search-item')]"))
                )
                primeiro_resultado.click()
                time.sleep(0.5) # Reduced delay

                return True
            except TimeoutException:
                print_to_gui("Não foi necessário definir um endereço ou elementos não encontrados.")
                return False

    except Exception as e:
        print_to_gui(f"Erro ao definir endereço: {str(e)}")
        salvar_screenshot(driver, "erro_endereco")
        return False

def buscar_mercado(driver, cidade, termo_busca):
    """Busca um mercado no iFood baseado no código HTML fornecido (ajustado para headless, rendering issues, e increased delay)."""
    try:
        print_to_gui(f"  Navegando para a página de mercados (headless-aware + UA)...")
        driver.get("https://www.ifood.com.br/mercados")
        time.sleep(0.5) # Slightly reduced initial delay

        aceitar_cookies(driver)
        definir_endereco(driver, cidade)
        time.sleep(0.5) # Slightly reduced address delay

        try:
            print_to_gui(f"  Localizando campo de busca de mercado (headless-aware + UA)...")
            campo_busca = WebDriverWait(driver, 0.5).until(
                EC.presence_of_element_located((By.XPATH, "//input[@data-test-id='search-input-field']"))
            )
            print_to_gui(f"  Campo de busca de mercado encontrado.")
            campo_busca.clear()
            campo_busca.send_keys(termo_busca)
            time.sleep(0.5)
            print_to_gui(f"  Termo de busca '{termo_busca}' digitado.")
            campo_busca.send_keys(Keys.ENTER)

            # **AGGRESSIVELY INCREASED DELAY AFTER SEARCH (Headless Specific):**
            time.sleep(0.5) # Increased to 15 seconds - give JS extra time to render results!
            print_to_gui(f"  Pesquisa de mercado enviada. Aguardando resultados (Headless DELAY 15s)...")


            # Wait for the CONTAINER of market results to be present first (headless-aware)
            print_to_gui(f"  Aguardando container dos resultados de mercado (headless-aware)...")
            resultados_container = WebDriverWait(driver, 1).until( # Increased timeout for container
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'merchant-list-v2__wrapper')]"))
            )
            print_to_gui(f"  Container dos resultados de mercado encontrado.")

            # Now wait for the LINK inside the container to be VISIBLE (headless-aware)
            print_to_gui(f"  Aguardando VISIBILIDADE do link do primeiro mercado (headless-aware)...")
            primeiro_mercado = WebDriverWait(driver, 0.5).until( # Increased timeout again, and using visibility
                EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'merchant-list-v2__wrapper')]//a[contains(@class, 'merchant-v2__link')]"))
            )
            print_to_gui(f"  Link do primeiro mercado VISÍVEL.")


            # Scroll to the element to ensure it's fully loaded and interactable (headless-aware)
            print_to_gui(f"  Rolando para o elemento do primeiro mercado (headless-aware)...")
            driver.execute_script("arguments[0].scrollIntoView(true);", primeiro_mercado)
            time.sleep(0.5) # Small delay after scroll
            print_to_gui(f"  Rolagem completa.")


            # Wait for it to be CLICKABLE (headless-aware)
            print_to_gui(f"  Aguardando CLICKABILIDADE do link do primeiro mercado (headless-aware)...")
            primeiro_mercado = WebDriverWait(driver, 0.5).until( # Increased timeout, and using clickability
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'merchant-list-v2__wrapper')]//a[contains(@class, 'merchant-v2__link')]"))
            )
            print_to_gui(f"  Link do primeiro mercado CLICÁVEL.")


            try:
                nome_mercado = primeiro_mercado.find_element(By.XPATH, ".//span[contains(@class, 'merchant-v2__name')]").text
            except:
                nome_mercado = termo_busca

            print_to_gui(f"  Clicando no primeiro mercado: {nome_mercado}")
            primeiro_mercado.click()
            time.sleep(0.5)
            print_to_gui(f"  Mercado '{nome_mercado}' acessado.")

            return {
                "nome": nome_mercado,
                "url": driver.current_url
            }

        except TimeoutException:
            print_to_gui(f"  Timeout EXCEPTION ao buscar mercado '{termo_busca}' (headless-aware + UA). Mercado não encontrado.")
            salvar_screenshot(driver, f"erro_mercado_nao_encontrado_{termo_busca.replace(' ', '_')}") # Save screenshot on Timeout
            return None

    except Exception as e:
        print_to_gui(f"  Erro GERAL ao buscar mercado '{termo_busca}' (headless-aware + UA): {str(e)}")
        salvar_screenshot(driver, f"erro_geral_buscar_mercado_{termo_busca.replace(' ', '_')}") # Save screenshot on general error
        return None

def buscar_produto(driver, nome_produto):
    """Busca um produto dentro do mercado e retorna uma lista de todos os resultados encontrados."""
    try:
        # Procura e preenche o campo de busca de produtos
        campo_busca_produto = WebDriverWait(driver, 0.5).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@class='market-catalog-search__input' or @placeholder='Busque nesta loja por item']"))
        )
        campo_busca_produto.clear()
        campo_busca_produto.send_keys(nome_produto)
        time.sleep(0.5) # Reduced delay
        campo_busca_produto.send_keys(Keys.ENTER)
        time.sleep(0.5) # Reduced delay from 5

        # Busca todos os produtos na página
        produtos_encontrados = []

        # Localiza todos os cards de produtos
        cards_produtos = WebDriverWait(driver, 0.5).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'product-card-wrapper')]"))
        )

        for card in cards_produtos:
            try:
                # Extrai nome/marca do produto
                nome_produto = card.find_element(By.XPATH, ".//span[@class='product-card__description']").get_attribute('title')

                # Extrai detalhes adicionais (como peso/volume)
                try:
                    detalhes = card.find_element(By.XPATH, ".//span[@class='product-card__details']").get_attribute('title')
                except:
                    detalhes = ""

                # Extrai o preço
                preco_elemento = card.find_element(By.XPATH, ".//div[@class='product-card__price']")
                preco_texto = preco_elemento.text.strip()

                # Limpa o texto do preço
                import re
                preco_limpo = re.sub(r'[^\d,]', '', preco_texto)
                preco_limpo = preco_limpo.replace(',', '.')

                produtos_encontrados.append({
                    "nome": nome_produto,
                    "detalhes": detalhes,
                    "preco": preco_limpo
                })

            except Exception as e:
                print_to_gui(f"Erro ao extrair informações de um produto: {str(e)}")
                continue

        return produtos_encontrados

    except Exception as e:
        print_to_gui(f"Erro ao buscar produtos '{nome_produto}': {str(e)}")
        return None
def salvar_screenshot(driver, nome_arquivo):
    """Salva um screenshot para debug."""
    try:
        driver.save_screenshot(f"{nome_arquivo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        print_to_gui(f"Screenshot salvo como {nome_arquivo}.png")
    except Exception as e:
        print_to_gui(f"Erro ao salvar screenshot: {e}")

def precificador_ifood_gsheets(produtos, mercados_busca, cidade_busca, email=None, senha=None):
    """Função principal que busca preços no iFood e salva no Google Sheets (com Headless e Batch Write)."""

    # Conecta ao Google Sheets
    worksheet = None
    try:
        worksheet = conectar_google_sheets('Preços iFood Mercados')
        print_to_gui("Conectado ao Google Sheets com sucesso.")
    except Exception as e:
        print_to_gui(f"Erro ao conectar ao Google Sheets: {str(e)}")
        print_to_gui("Continuando sem salvar no Google Sheets.")

    # Data da coleta
    data_coleta = datetime.now().strftime('%d/%m/%Y %H:%M')

    # Lista para armazenar os dados coletados
    dados_coletados = []

    # Add session state tracking
    session_state = {
        'logged_in': False,
        'address_set': False,
        'current_market': None
    }

    # Configura o driver do Selenium (inicialmente visível)
    driver = configurar_driver() # Start with visible driver

    try:
        driver.get("https://www.ifood.com.br/")
        time.sleep(0.5) # Reduced initial delay

        # Check for existing cookies first
        if carregar_cookies(driver):
            session_state['logged_in'] = True
            session_state['address_set'] = True
            print_to_gui("Sessão anterior restaurada, pulando login e endereço")

            # Switch to headless mode now that session is restored
            driver.quit() # Close the visible driver
            driver = configurar_driver_headless() # Create headless driver
            driver.get("https://www.ifood.com.br/mercados") # Need to navigate again in new driver
            time.sleep(0.5) # Reduced delay after navigation in headless
            print_to_gui("Driver trocado para modo headless.")


        else:
            # Only login if needed
            if email and senha:
                if fazer_login_ifood(driver): # Removed email and senha parameters as they are not used in the function
                    session_state['logged_in'] = True
                    salvar_cookies(driver)

            # Only set address if needed
            if not session_state['address_set']:
                if definir_endereco(driver, cidade_busca):
                    session_state['address_set'] = True
                    salvar_cookies(driver)

            # Switch to headless mode after login and address setup
            print_to_gui("Trocando driver para modo headless após login e endereço.")
            driver.quit() # Close the visible driver
            driver = configurar_driver_headless() # Create headless driver
            driver.get("https://www.ifood.com.br/mercados") # Navigate again in new driver
            time.sleep(0.5) # Reduced delay after navigation in headless
            print_to_gui("Driver trocado para modo headless.")


        # Optimize market navigation
        for nome_mercado in mercados_busca:
            if session_state['current_market'] != nome_mercado:
                mercado = buscar_mercado(driver, cidade_busca, nome_mercado)
                if mercado:
                    session_state['current_market'] = mercado

            print_to_gui(f"\nBuscando mercado: {nome_mercado}")

            if not mercado:
                print_to_gui(f"Não foi possível acessar o mercado {nome_mercado} após várias tentativas. Pulando para o próximo.")
                salvar_screenshot(driver, f"erro_final_mercado_{nome_mercado}")
                continue

            print_to_gui(f"Mercado encontrado: {mercado['nome']}")
            print_to_gui(f"URL: {mercado['url']}")

            # Para cada produto na lista
            for produto in produtos:
                print_to_gui(f"\n  Buscando produto: {produto}")

                # Adiciona um delay aleatório para simular comportamento humano
                time.sleep(random.uniform(0.5, 1.5)) # Reduced random delay

                # Busca o produto
                resultados = buscar_produto(driver, produto)

                if resultados:
                    print_to_gui(f"  Encontrados {len(resultados)} resultados para '{produto}':")
                    for resultado in resultados:
                        print_to_gui(f"    - {resultado['nome']}")
                        print_to_gui(f"      Detalhes: {resultado['detalhes']}")
                        print_to_gui(f"      Preço: R$ {resultado['preco']}")

                        # Adiciona à lista de dados
                        dados_coletados.append([
                            data_coleta,
                            mercado['nome'],
                            f"{resultado['nome']} {resultado['detalhes']}".strip(),
                            f"R$ {resultado['preco']}"
                        ])
                else:
                    print_to_gui(f"  Nenhum produto encontrado para: {produto}")
                    salvar_screenshot(driver, f"erro_produto_{nome_mercado}_{produto.replace(' ', '_')}")

                    # Adiciona à lista de dados como não encontrado
                    dados_coletados.append([
                        data_coleta,
                        mercado['nome'],
                        produto,
                        "Não encontrado"
                    ])
            # Volta para a página inicial para buscar o próximo mercado (mercados page already loaded in headless switch)
            # driver.get("https://www.ifood.com.br/mercados") # No need to reload markets page
            time.sleep(0.5) # Reduced delay

            # Save state before moving to next market
            salvar_cookies(driver)

    except Exception as e:
        print_to_gui(f"Erro durante a execução: {str(e)}")
        salvar_screenshot(driver, "erro_execucao")
        messagebox.showerror("Erro", f"Ocorreu um erro durante a execução: {str(e)}. Veja o log na interface.")

    finally:
        # Salva os cookies antes de fechar
        salvar_cookies(driver)

        # Fecha o driver
        driver.quit()

    # Salva os dados no Google Sheets (Batch Write)
    if worksheet and dados_coletados:
        try:
            worksheet.append_rows(dados_coletados) # Use append_rows for batch writing
            print_to_gui("Dados salvos no Google Sheets com sucesso (em lote).")
        except Exception as e:
            print_to_gui(f"Erro ao salvar no Google Sheets (em lote): {str(e)}")

    # Salva também em um arquivo Excel local como backup
    if dados_coletados:
        df = pd.DataFrame(dados_coletados, columns=['Data', 'Mercado', 'Produto', 'Preço'])
        df.to_excel('precos_ifood_backup.xlsx', index=False)
        print_to_gui(f"\nColeta finalizada! Dados salvos no arquivo 'precos_ifood_backup.xlsx'")
        return df
    else:
        print_to_gui("\nNenhum dado foi coletado durante a execução.")
        return pd.DataFrame(columns=['Data', 'Mercado', 'Produto', 'Preço'])

# --- GUI Section ---
def start_scraping():
    produtos_str = produtos_entry.get("1.0", tk.END).strip()
    mercados_str = mercados_entry.get("1.0", tk.END).strip()
    cidade_busca = cidade_entry.get().strip()

    produtos = [p.strip() for p in produtos_str.splitlines() if p.strip()]
    mercados_busca = [m.strip() for m in mercados_str.splitlines() if m.strip()]

    if not produtos or not mercados_busca or not cidade_busca:
        messagebox.showerror("Erro", "Por favor, preencha todos os campos (Produtos, Mercados e Cidade).")
        return

    output_text.delete("1.0", tk.END) # Clear previous output
    print_to_gui(f"Iniciando a coleta de preços para os mercados: {', '.join(mercados_busca)}")
    print_to_gui(f"Produtos a serem buscados: {', '.join(produtos)}")
    print_to_gui(f"Cidade de busca: {cidade_busca}")

    threading.Thread(target=run_scraper, args=(produtos, mercados_busca, cidade_busca), daemon=True).start()

def run_scraper(produtos, mercados_busca, cidade_busca):
    try:
        precificador_ifood_gsheets(produtos, mercados_busca, cidade_busca)
        print_to_gui("Processo de scraping finalizado.")
        messagebox.showinfo("Concluído", "Coleta de preços finalizada com sucesso!")
    except Exception as e:
        print_to_gui(f"Erro geral no scraping: {e}")
        messagebox.showerror("Erro", f"Erro durante o scraping: {e}")

def print_to_gui(text):
    output_text.config(state=tk.NORMAL) # Allow editing
    output_text.insert(tk.END, text + "\n")
    output_text.see(tk.END) # Scroll to the bottom
    output_text.config(state=tk.DISABLED) # Disable editing

root = tk.Tk()
root.title("iFood Price Scraper")

# --- Styling ---
style = ttk.Style(root)
style.theme_use('clam')  # Choose a theme: clam, alt, default, classic

# --- Fonts and Colors ---
fonte_titulo = ("Helvetica", 14, "bold")
fonte_texto = ("Arial", 10)
cor_fundo = '#f0f0f0'  # Light gray background
cor_label = '#333333'   # Dark gray labels
cor_entry_bg = 'white'
cor_entry_fg = 'black'
cor_button_bg = '#4CAF50' # Green button
cor_button_fg = 'white'
cor_output_bg = 'white'
cor_output_fg = 'black'

root.configure(bg=cor_fundo)

# --- Cidade Input ---
cidade_label = ttk.Label(root, text="Cidade:", font=fonte_texto, foreground=cor_label, background=cor_fundo)
cidade_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
cidade_entry = ttk.Entry(root, width=50, font=fonte_texto, background=cor_entry_bg, foreground=cor_entry_fg)
cidade_entry.grid(row=0, column=1, columnspan=2, sticky="ew", padx=10, pady=5)
cidade_entry.insert(0, "Goiânia, GO") # Default city

# --- Mercados Input ---
mercados_label = ttk.Label(root, text="Mercados (um por linha):", font=fonte_texto, foreground=cor_label, background=cor_fundo)
mercados_label.grid(row=1, column=0, sticky="nw", padx=10, pady=5)
mercados_entry = scrolledtext.ScrolledText(root, height=5, width=50, font=fonte_texto, bg=cor_entry_bg, fg=cor_entry_fg)
mercados_entry.grid(row=1, column=1, columnspan=2, sticky="ew", padx=10, pady=5)
mercados_entry.insert(tk.END, "Atacadão\nAssaí\nCarrefour\nBretas") # Default markets

# --- Produtos Input ---
produtos_label = ttk.Label(root, text="Produtos (um por linha):", font=fonte_texto, foreground=cor_label, background=cor_fundo)
produtos_label.grid(row=2, column=0, sticky="nw", padx=10, pady=5)
produtos_entry = scrolledtext.ScrolledText(root, height=5, width=50, font=fonte_texto, bg=cor_entry_bg, fg=cor_entry_fg)
produtos_entry.grid(row=2, column=1, columnspan=2, sticky="ew", padx=10, pady=5)
produtos_entry.insert(tk.END, "creme de leite\nleite condensado\nleite\narroz 5kg\nfeijão carioca\naçúcar\nóleo de soja") # Default products

# --- Start Button ---
start_button = ttk.Button(root, text="Iniciar Coleta de Preços", command=start_scraping, style='Accent.TButton')
start_button.grid(row=3, column=0, columnspan=3, pady=15)
style.configure('Accent.TButton', font=fonte_titulo, foreground=cor_button_fg, background=cor_button_bg, padding=10)

# --- Output Text Area ---
output_label = ttk.Label(root, text="Log de Saída:", font=fonte_texto, foreground=cor_label, background=cor_fundo)
output_label.grid(row=4, column=0, sticky="w", padx=10, pady=5)
output_text = scrolledtext.ScrolledText(root, height=10, width=70, state=tk.DISABLED, font=fonte_texto, bg=cor_output_bg, fg=cor_output_fg) # Disabled initially
output_text.grid(row=5, column=0, columnspan=3, sticky="ew", padx=10, pady=5)

root.columnconfigure(1, weight=1) # Make column 1 expandable

root.mainloop()