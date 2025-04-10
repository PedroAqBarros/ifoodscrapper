import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
import re

def fazer_login_ifood(driver, print_func=print):
    """Aguarda o login manual do usuário no iFood."""
    try:
        driver.get("https://www.ifood.com.br/")
        time.sleep(0.5)

        try:
            botao_entrar = WebDriverWait(driver, 0.5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Entrar') or contains(@data-test-id, 'login-button')]"))
            )
            botao_entrar.click()

            print_func("Por favor, faça login manualmente na janela do navegador.")
            print_func("Aguardando login... (60 segundos)")

            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(@data-test-id, 'user-menu')]"))
            )

            print_func("Login realizado com sucesso!")
            time.sleep(0.5)
            return True

        except TimeoutException:
            print_func("Tempo excedido para login ou usuário já está logado.")
            return False

    except Exception as e:
        print_func(f"Erro durante o processo de login: {str(e)}")
        return False

def definir_endereco(driver, cidade, print_func=print):
    """Define um endereço específico ou usa a localização atual."""
    try:
        try:
            texto_tela = WebDriverWait(driver, 1).until(
                EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), 'Onde você quer receber seu pedido?')]"))
            )

            botao_localização = WebDriverWait(driver, 1).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Usar minha localização') or contains(@data-test-id, 'use-location-button')]"))
            )
            botao_localização.click()
            time.sleep(0.5)

            print_func("Usando localização atual. Aceite a permissão no navegador se solicitado.")
            time.sleep(0.5)

            return True
        except TimeoutException:
            try:
                botao_endereco = WebDriverWait(driver, 1).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Escolha um endereço') or contains(@data-test-id, 'address-button')]"))
                )
                botao_endereco.click()
                time.sleep(0.5)

                campo_busca = WebDriverWait(driver, 1).until(
                    EC.element_to_be_clickable((By.XPATH, "//input[contains(@placeholder, 'Buscar endereço') or contains(@data-test-id, 'address-search-input')]"))
                )
                campo_busca.clear()
                campo_busca.send_keys(cidade)
                time.sleep(0.5)

                primeiro_resultado = WebDriverWait(driver, 0.5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@data-test-id, 'address-search-item')]"))
                )
                primeiro_resultado.click()
                time.sleep(0.5)

                return True
            except TimeoutException:
                print_func("Não foi necessário definir um endereço ou elementos não encontrados.")
                return False

    except Exception as e:
        print_func(f"Erro ao definir endereço: {str(e)}")
        return False

def buscar_mercado(driver, cidade, termo_busca, print_func=print):
    """Busca um mercado no iFood."""
    try:
        print_func(f"  Navegando para a página de mercados...")
        driver.get("https://www.ifood.com.br/mercados")
        time.sleep(0.5)

        try:
            print_func(f"  Localizando campo de busca de mercado...")
            campo_busca = WebDriverWait(driver, 0.5).until(
                 EC.presence_of_element_located((By.XPATH, "//input[@data-test-id='search-input-field']"))
            )
            print_func(f"  Campo de busca de mercado encontrado.")
            campo_busca.clear()
            campo_busca.send_keys(termo_busca)
            time.sleep(0.5)
            print_func(f"  Termo de busca '{termo_busca}' digitado.")
            campo_busca.send_keys(Keys.ENTER)

            time.sleep(0.5)
            print_func(f"  Pesquisa de mercado enviada. Aguardando resultados...")

            resultados_container = WebDriverWait(driver, 1).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'merchant-list-v2__wrapper')]"))
            )
            print_func(f"  Container dos resultados de mercado encontrado.")

            mercados = WebDriverWait(driver, 0.5).until(
                EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'merchant-list-v2__wrapper')]//a[contains(@class, 'merchant-v2__link')]"))
            )
            
            mercado_encontrado = None
            
            print_func(f"  Verificando correspondência exata com '{termo_busca}'...")
            for mercado in mercados:
                try:
                    nome_mercado = mercado.find_element(By.XPATH, ".//span[contains(@class, 'merchant-v2__name')]").text.lower()
                    if termo_busca.lower() in nome_mercado:
                        mercado_encontrado = mercado
                        break
                except:
                    continue
            
            if mercado_encontrado:
                nome_mercado = mercado_encontrado.find_element(By.XPATH, ".//span[contains(@class, 'merchant-v2__name')]").text
                print_func(f"  Mercado encontrado: {nome_mercado}")
                
                print_func(f"  Rolando para o elemento do mercado...")
                driver.execute_script("arguments[0].scrollIntoView(true);", mercado_encontrado)
                time.sleep(0.5)
                
                print_func(f"  Clicando no mercado...")
                mercado_encontrado.click()
                time.sleep(0.5)
                print_func(f"  Mercado '{nome_mercado}' acessado.")

                return {
                    "nome": nome_mercado,
                    "url": driver.current_url
                }
            else:
                print_func(f"  Mercado '{termo_busca}' não encontrado exatamente como solicitado.")
                return None

        except TimeoutException:
            print_func(f"  Timeout ao buscar mercado '{termo_busca}'. Mercado não encontrado.")
            return None

    except Exception as e:
        print_func(f"  Erro ao buscar mercado '{termo_busca}': {str(e)}")
        return None

def buscar_produto(driver, nome_produto, print_func=print):
    """Busca um produto dentro do mercado e retorna uma lista de todos os resultados encontrados."""
    try:
        campo_busca_produto = WebDriverWait(driver, 0.5).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@class='market-catalog-search__input' or @placeholder='Busque nesta loja por item']"))
        )
        campo_busca_produto.clear()
        campo_busca_produto.send_keys(nome_produto)
        time.sleep(0.5)
        campo_busca_produto.send_keys(Keys.ENTER)
        time.sleep(0.5)

        produtos_encontrados = []

        cards_produtos = WebDriverWait(driver, 0.5).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'product-card-wrapper')]"))
        )

        for card in cards_produtos:
            try:
                nome_produto = card.find_element(By.XPATH, ".//span[@class='product-card__description']").get_attribute('title')

                try:
                    detalhes = card.find_element(By.XPATH, ".//span[@class='product-card__details']").get_attribute('title')
                except:
                    detalhes = ""

                preco_elemento = card.find_element(By.XPATH, ".//div[@class='product-card__price']")
                preco_texto = preco_elemento.text.strip()

                preco_limpo = re.sub(r'[^\d,]', '', preco_texto)
                preco_limpo = preco_limpo.replace(',', '.')

                produtos_encontrados.append({
                    "nome": nome_produto,
                    "detalhes": detalhes,
                    "preco": preco_limpo
                })

            except Exception as e:
                print_func(f"Erro ao extrair informações de um produto: {str(e)}")
                continue

        return produtos_encontrados

    except Exception as e:
        print_func(f"Erro ao buscar produtos '{nome_produto}': {str(e)}")
        return None 