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
    """Configura e retorna um driver Selenium com configurações aprimoradas."""
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

def salvar_cookies(driver):
    """Salva os cookies atuais do navegador."""
    try:
        pickle.dump(driver.get_cookies(), open("cookies.pkl", "wb"))
        print("Cookies salvos com sucesso.")
    except Exception as e:
        print(f"Erro ao salvar cookies: {e}")

def carregar_cookies(driver):
    """Carrega cookies salvos anteriormente, se existirem."""
    try:
        if os.path.exists("cookies.pkl"):
            cookies = pickle.load(open("cookies.pkl", "rb"))
            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    print(f"Erro ao adicionar cookie: {e}")
            print("Cookies carregados com sucesso.")
            return True
        else:
            print("Nenhum arquivo de cookies encontrado.")
            return False
    except Exception as e:
        print(f"Erro ao carregar cookies: {e}")
        return False

def aceitar_cookies(driver):
    """Tenta aceitar cookies se o aviso aparecer."""
    try:
        # Espera até 5 segundos pelo botão de aceitar cookies
        botao_cookies = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Aceitar') or contains(text(), 'aceitar') or contains(text(), 'OK')]"))
        )
        botao_cookies.click()
        print("Cookies aceitos com sucesso.")
        time.sleep(1)
    except TimeoutException:
        # Se não encontrar o botão, provavelmente não há aviso de cookies
        print("Nenhum aviso de cookies detectado ou já foi aceito anteriormente.")
    except Exception as e:
        print(f"Erro ao tentar aceitar cookies: {str(e)}")

def fazer_login_ifood(driver):
    """Aguarda o login manual do usuário no iFood."""
    try:
        # Acessa a página principal do iFood
        driver.get("https://www.ifood.com.br/")
        time.sleep(3)
        
        # Aceita cookies se necessário
        aceitar_cookies(driver)
        
        # Clica no botão de entrar/login
        try:
            botao_entrar = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Entrar') or contains(@data-test-id, 'login-button')]"))
            )
            botao_entrar.click()
            
            print("Por favor, faça login manualmente na janela do navegador.")
            print("Aguardando login... (60 segundos)")
            
            # Aguarda até que o usuário esteja logado verificando elementos que só aparecem após o login
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(@data-test-id, 'user-menu')]"))
            )
            
            print("Login realizado com sucesso!")
            time.sleep(2)
            return True
            
        except TimeoutException:
            print("Tempo excedido para login ou usuário já está logado.")
            return False
            
    except Exception as e:
        print(f"Erro durante o processo de login: {str(e)}")
        return False
def definir_endereco(driver, cidade):
    """Define um endereço específico ou usa a localização atual."""
    try:
        # Procura pela tela de endereço que apareceu no screenshot
        try:
            # Verifica se a tela de "Onde você quer receber seu pedido?" está presente
            texto_tela = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), 'Onde você quer receber seu pedido?')]"))
            )
            
            # Tenta usar a opção "Usar minha localização"
            botao_localização = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Usar minha localização') or contains(@data-test-id, 'use-location-button')]"))
            )
            botao_localização.click()
            time.sleep(3)
            
            # Se pedir permissão para acessar localização, aceitar no browser
            print("Usando localização atual. Aceite a permissão no navegador se solicitado.")
            time.sleep(3)
            
            return True
        except TimeoutException:
            # Se não encontrar a tela de localização atual, tente buscar o endereço
            try:
                # Clique no botão de escolher endereço no topo da página
                botao_endereco = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Escolha um endereço') or contains(@data-test-id, 'address-button')]"))
                )
                botao_endereco.click()
                time.sleep(2)
                
                # Preenche o campo de busca de endereço
                campo_busca = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//input[contains(@placeholder, 'Buscar endereço') or contains(@data-test-id, 'address-search-input')]"))
                )
                campo_busca.clear()
                campo_busca.send_keys(cidade)
                time.sleep(2)
                
                # Seleciona o primeiro resultado
                primeiro_resultado = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@data-test-id, 'address-search-item')]"))
                )
                primeiro_resultado.click()
                time.sleep(3)
                
                return True
            except TimeoutException:
                print("Não foi necessário definir um endereço ou elementos não encontrados.")
                return False
                
    except Exception as e:
        print(f"Erro ao definir endereço: {str(e)}")
        salvar_screenshot(driver, "erro_endereco")
        return False

def buscar_mercado(driver, cidade, termo_busca):
    """Busca um mercado no iFood baseado no código HTML fornecido."""
    try:
        driver.get("https://www.ifood.com.br/mercados")
        time.sleep(5)
        
        aceitar_cookies(driver)
        definir_endereco(driver, cidade)
        time.sleep(3)
        
        try:
            campo_busca = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//input[@data-test-id='search-input-field']"))
            )
            campo_busca.clear()
            campo_busca.send_keys(termo_busca)
            time.sleep(2)
            campo_busca.send_keys(Keys.ENTER)
            time.sleep(7)
            
            # Novo seletor baseado na estrutura HTML fornecida
            primeiro_mercado = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'merchant-list-v2__wrapper')]//a[contains(@class, 'merchant-v2__link')]"))
            )
            
            try:
                nome_mercado = primeiro_mercado.find_element(By.XPATH, ".//span[contains(@class, 'merchant-v2__name')]").text
            except:
                nome_mercado = termo_busca
            
            primeiro_mercado.click()
            time.sleep(5)
            
            return {
                "nome": nome_mercado,
                "url": driver.current_url
            }
        
        except TimeoutException:
            print(f"Mercado '{termo_busca}' não encontrado")
            return None
    
    except Exception as e:
        print(f"Erro ao buscar mercado '{termo_busca}': {str(e)}")
        return None

def buscar_produto(driver, nome_produto):
    """Busca um produto dentro do mercado e retorna uma lista de todos os resultados encontrados."""
    try:
        # Procura e preenche o campo de busca de produtos
        campo_busca_produto = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@class='market-catalog-search__input' or @placeholder='Busque nesta loja por item']"))
        )
        campo_busca_produto.clear()
        campo_busca_produto.send_keys(nome_produto)
        time.sleep(1)
        campo_busca_produto.send_keys(Keys.ENTER)
        time.sleep(5)
        
        # Busca todos os produtos na página
        produtos_encontrados = []
        
        # Localiza todos os cards de produtos
        cards_produtos = WebDriverWait(driver, 10).until(
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
                print(f"Erro ao extrair informações de um produto: {str(e)}")
                continue
        
        return produtos_encontrados
        
    except Exception as e:
        print(f"Erro ao buscar produtos '{nome_produto}': {str(e)}")
        return None
def salvar_screenshot(driver, nome_arquivo):
    """Salva um screenshot para debug."""
    try:
        driver.save_screenshot(f"{nome_arquivo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        print(f"Screenshot salvo como {nome_arquivo}.png")
    except Exception as e:
        print(f"Erro ao salvar screenshot: {str(e)}")

def precificador_ifood_gsheets(email=None, senha=None):
    """Função principal que busca preços no iFood e salva no Google Sheets."""
    # Lista de mercados para buscar
    mercados_busca = ["Atacadão", "Assaí", "Carrefour", "Bretas"]
    
    # Cidade para busca
    cidade_busca = "Goiânia, GO"
    
    # Lista de produtos para buscar
    produtos = ["creme de leite", "leite condensado", "leite", "arroz 5kg", "feijão carioca", "açúcar", "óleo de soja"]
    
    # Conecta ao Google Sheets
    try:
        worksheet = conectar_google_sheets('Preços iFood Mercados')
        print("Conectado ao Google Sheets com sucesso.")
    except Exception as e:
        print(f"Erro ao conectar ao Google Sheets: {str(e)}")
        print("Continuando sem salvar no Google Sheets.")
        worksheet = None
    
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
    
    # Configura o driver do Selenium
    driver = configurar_driver()
    
    try:
        driver.get("https://www.ifood.com.br/")
        
        # Check for existing cookies first
        if carregar_cookies(driver):
            session_state['logged_in'] = True
            session_state['address_set'] = True
            print("Sessão anterior restaurada, pulando login e endereço")
        else:
            # Only login if needed
            if email and senha:
                if fazer_login_ifood(driver, email, senha):
                    session_state['logged_in'] = True
                    salvar_cookies(driver)
            
            # Only set address if needed
            if not session_state['address_set']:
                if definir_endereco(driver, cidade_busca):
                    session_state['address_set'] = True
                    salvar_cookies(driver)
        
        # Optimize market navigation
        for nome_mercado in mercados_busca:
            if session_state['current_market'] != nome_mercado:
                mercado = buscar_mercado(driver, cidade_busca, nome_mercado)
                if mercado:
                    session_state['current_market'] = nome_mercado
            
            print(f"\nBuscando mercado: {nome_mercado}")
            
            if not mercado:
                print(f"Não foi possível acessar o mercado {nome_mercado} após várias tentativas. Pulando para o próximo.")
                salvar_screenshot(driver, f"erro_final_mercado_{nome_mercado}")
                continue
            
            print(f"Mercado encontrado: {mercado['nome']}")
            print(f"URL: {mercado['url']}")
            
            # Para cada produto na lista
            for produto in produtos:
                print(f"\n  Buscando produto: {produto}")
                
                # Adiciona um delay aleatório para simular comportamento humano
                time.sleep(random.uniform(1, 3))
                
                # Busca o produto
                resultados = buscar_produto(driver, produto)
                
                if resultados:
                    print(f"  Encontrados {len(resultados)} resultados para '{produto}':")
                    for resultado in resultados:
                        print(f"    - {resultado['nome']}")
                        print(f"      Detalhes: {resultado['detalhes']}")
                        print(f"      Preço: R$ {resultado['preco']}")
                        
                        # Adiciona à lista de dados
                        dados_coletados.append([
                            data_coleta,
                            mercado['nome'],
                            f"{resultado['nome']} {resultado['detalhes']}".strip(),
                            f"R$ {resultado['preco']}"
                        ])
                else:
                    print(f"  Nenhum produto encontrado para: {produto}")
                    salvar_screenshot(driver, f"erro_produto_{nome_mercado}_{produto.replace(' ', '_')}")
                    
                    # Adiciona à lista de dados como não encontrado
                    dados_coletados.append([
                        data_coleta,
                        mercado['nome'],
                        produto,
                        "Não encontrado"
                    ])            
            # Volta para a página inicial para buscar o próximo mercado
            driver.get("https://www.ifood.com.br/mercados")
            time.sleep(3)
            
            # Save state before moving to next market
            salvar_cookies(driver)
    
    except Exception as e:
        print(f"Erro durante a execução: {str(e)}")
        salvar_screenshot(driver, "erro_execucao")
    
    finally:
        # Salva os cookies antes de fechar
        salvar_cookies(driver)
        
        # Fecha o driver
        driver.quit()
    
    # Salva os dados no Google Sheets
    if worksheet and dados_coletados:
        try:
            for linha in dados_coletados:
                worksheet.append_row(linha)
            print("Dados salvos no Google Sheets com sucesso.")
        except Exception as e:
            print(f"Erro ao salvar no Google Sheets: {str(e)}")
    
    # Salva também em um arquivo Excel local como backup
    if dados_coletados:
        df = pd.DataFrame(dados_coletados, columns=['Data', 'Mercado', 'Produto', 'Preço'])
        df.to_excel('precos_ifood_backup.xlsx', index=False)
        print(f"\nColeta finalizada! Dados salvos no arquivo 'precos_ifood_backup.xlsx'")
        return df
    else:
        print("\nNenhum dado foi coletado durante a execução.")

        return pd.DataFrame(columns=['Data', 'Mercado', 'Produto', 'Preço'])

if __name__ == "__main__":
    precificador_ifood_gsheets()
    precificador_ifood_gsheets()