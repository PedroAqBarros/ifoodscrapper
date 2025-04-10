import pickle
import os
from datetime import datetime
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

def salvar_cookies(driver, print_func=print):
    """Salva os cookies atuais do navegador."""
    try:
        pickle.dump(driver.get_cookies(), open("cookies.pkl", "wb"))
        print_func("Cookies salvos com sucesso.")
    except Exception as e:
        print_func(f"Erro ao salvar cookies: {e}")

def carregar_cookies(driver, print_func=print):
    """Carrega cookies salvos anteriormente, se existirem."""
    try:
        if os.path.exists("cookies.pkl"):
            cookies = pickle.load(open("cookies.pkl", "rb"))
            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    print_func(f"Erro ao adicionar cookie: {e}")
            print_func("Cookies carregados com sucesso.")
            return True
        else:
            print_func("Nenhum arquivo de cookies encontrado.")
            return False
    except Exception as e:
        print_func(f"Erro ao carregar cookies: {e}")
        return False

def aceitar_cookies(driver, print_func=print):
    """Tenta aceitar cookies se o aviso aparecer."""
    try:
        botao_cookies = WebDriverWait(driver, 0.5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Aceitar') or contains(text(), 'aceitar') or contains(text(), 'OK')]"))
        )
        botao_cookies.click()
        print_func("Cookies aceitos com sucesso.")
    except TimeoutException:
        print_func("Nenhum aviso de cookies detectado ou já foi aceito anteriormente.")
    except Exception as e:
        print_func(f"Erro ao tentar aceitar cookies: {str(e)}")

def salvar_screenshot(driver, nome_arquivo, print_func=print):
    """Salva um screenshot para debug."""
    try:
        driver.save_screenshot(f"{nome_arquivo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        print_func(f"Screenshot salvo como {nome_arquivo}.png")
    except Exception as e:
        print_func(f"Erro ao salvar screenshot: {str(e)}") 