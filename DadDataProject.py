import pandas as pd
import bs4 as bs
import requests
import sys
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import os

# https://www.ritchieng.com/pandas-multi-criteria-filtering/
# This is a flask problem but first get the data...
# C:/Users/Schonanderl/Downloads/chromedriver_win32_recent/chromedriver.exe


# driver.set_window_size(1024, 600)
# driver.maximize_window()
driver = webdriver.Chrome(ChromeDriverManager().install())
sys.setrecursionlimit(25000)
default_sleep_time = .5

peru_central_bank = "https://estadisticas.bcrp.gob.pe/estadisticas/series/mensuales/resultados/PN01273PM/html"
argentine_central_bank = "https://www.bcra.gob.ar/PublicacionesEstadisticas/Principales_variables_datos_i.asp?serie=7931&detalle=Monthly%20Inflation"
brazil_central_bank = "https://www3.bcb.gov.br/sgspub/"# "https://www.bcb.gov.br/en/statistics"# "https://www3.bcb.gov.br/sgspub/localizarseries/localizarSeries.do?method=prepararTelaLocalizarSeries"
chile_central_bank = "https://si3.bcentral.cl/Siete/EN/Siete/Cuadro/CAP_PRECIOS/MN_CAP_PRECIOS/IPC_BS_18_VAR_A/637274885701439267"
mexico_central_bank = "https://www.inegi.org.mx/app/api/indicadores/interna_v1_1//ValorIndicador/583752/0700/null/es/null/null/3/pd/0/null/null/null/null/json/563cbaa8-58bb-fef8-6763-1f1dae318f99"# 'https://www.inegi.org.mx/app/indicesdeprecios/Estructura.aspx?idEstructura=112001300030&T=%C3%8Dndices%20de%20Precios%20al%20Consumidor&ST=Inflaci%C3%B3n%20Mensual'
colombia_central_bank = "https://totoro.banrep.gov.co/analytics/saw.dll?Download&Format=excel2007&Extension=.xls&BypassCache=true&lang=es&NQUser=publico&NQPassword=publico123&path=%2Fshared%2FSeries%20Estad%C3%ADsticas_T%2F1.%20IPC%20base%202018%2F1.2.%20Por%20a%C3%B1o%2F1.2.5.IPC_Serie_variaciones"

def get_peru_inflation_stats():
    '''
    Pulls monthly inflation from Peruvian Central Bank
    '''
    peru_data = requests.get(peru_central_bank)
    soup = bs.BeautifulSoup(peru_data.text, 'html.parser')
    table = soup.find_all('table')
    cb_data = pd.read_html(str(table))[1]
    cb_data["Month"] =  cb_data["Fecha"].str.slice(start=0, stop = 3)
    cb_data["Year"] =  cb_data["Fecha"].str.slice(start=3).astype(int)
    cb_data = cb_data[(cb_data.Year == 20) | (cb_data.Year == 19) | (cb_data.Year == 18)]
    cb_data["Date"] = cb_data["Month"].str.cat(cb_data["Year"].astype(str), sep ="/") 
    cb_data['Date'] = '01/' + cb_data['Date'].astype(str)


    return cb_data

def get_argentina_inflation_stats():


    driver.get(argentine_central_bank)
    time.sleep(default_sleep_time)
    
    driver.find_element_by_xpath("/html/body/div/div[2]/div/div/div/div/form/input[1]").send_keys("01012018")
    driver.find_element_by_xpath("/html/body/div/div[2]/div/div/div/div/form/input[2]").send_keys("05312020")
    driver.find_element_by_xpath("/html/body/div/div[2]/div/div/div/div/form/button").click()
    soup = bs.BeautifulSoup(driver.page_source, 'html.parser')
    driver.close()

    table = soup.find_all('table')
    cb_data =  pd.read_html(str(table))[0]
    
    return cb_data

def get_brazil_inflation_stats():
    
    #     driver.find_element_by_xpath('//*[@id="dataInicio"]').send_keys("01012018")
    driver.get(brazil_central_bank) # warning, i-frame
    time.sleep(default_sleep_time)
    
    driver.implicitly_wait(100)
    driver.switch_to.frame(driver.find_element_by_tag_name("iframe"))
    driver.find_element_by_xpath("/html/body/table/tbody/tr[1]/td[1]/div/b/a").click()
    driver.find_element_by_xpath('//*[@id="Camada1"]/ul/li[3]/a/img').click()
    driver.find_element_by_xpath('//*[@id="Camada10"]/ul/li[2]/a/span').click()
    driver.find_element_by_xpath('//*[@id="tabelaSeries"]/tbody/tr[1]/td[1]/input').click()
    driver.switch_to.default_content()
    driver.find_element_by_xpath('/html/body/form/center/span/center/table/tbody/tr/td[4]/div/input').click()

    driver.find_element_by_xpath('/html/body/center/form/div[2]/input[2]').click()
    driver.find_element_by_xpath('//*[@id="valoresSeries"]/tbody/tr[1]/td/span/span[2]/div/table/tbody/tr/td/a[6]').click()

    soup = bs.BeautifulSoup(driver.page_source, 'html.parser')
    driver.close()

    table = soup.find(id = 'valoresSeries')
    cb_data =  pd.read_html(str(table))[0]
    cb_data = cb_data.iloc[3:98]

    return cb_data

def get_chile_inflation_stats():
    chile_data = requests.get(chile_central_bank)
    soup = bs.BeautifulSoup(chile_data.text, 'html.parser')
    table = soup.find_all('table')

    cb_data = pd.read_html(str(table))[0]
    cb_data = cb_data.drop(columns=['Sel.'])
    cb_data = cb_data.set_index('Serie').transpose()
    cb_data['Serie'] = cb_data.index
    cb_data['Date'] = '01.' + cb_data['Serie'].astype(str)

    
    return cb_data

def get_mexico_inflation_stats():
    mexico_data = requests.get(mexico_central_bank)
    mexico_data  = mexico_data.json()
    inflation_value = mexico_data["value"]
    date_values = mexico_data["dimension"]["periods"]["category"]["label"]
    mexico_df = pd.DataFrame.from_records(date_values)
    mexico_df["inflation"] = inflation_value

    return mexico_df

def get_colombia_inflation_stats():
    # if os.path.exists("C:/Users/Schonanderl/Downloads/1.2.5.IPC_Serie_variaciones.xlsx"):
    #    os.remove("C:/Users/Schonanderl/Downloads/1.2.5.IPC_Serie_variaciones.xlsx")

    driver.get("https://www.banrep.gov.co/es/estadisticas/indice-precios-consumidor-ipc") # warning, i-frame
    time.sleep(default_sleep_time)
    driver.find_element_by_xpath("/html/body/div[3]/main/div/div/div[1]/div[1]/ul/li[1]/a").click()
    
    df = pd.read_excel('C:/Users/Schonanderl/Downloads/1.2.5.IPC_Serie_variaciones.xlsx', sheet_name='Sheet1', skiprows=12)
    df = df[df['Inflación anual %'].notna()]
    df["Year"] =  df["Año(aaaa)-Mes(mm)"].astype(str).str.slice(start=0, stop = 4)
    df["Month"] =  df["Año(aaaa)-Mes(mm)"].astype(str).str.slice(start=4, stop = 6)

    df["Date"] = df["Month"].str.cat(df["Year"].astype(str), sep ="/") 
    df['Date'] = '01/' + df['Date'].astype(str)

    df = df[(df.Year.astype(int) == 2020) | (df.Year.astype(int) == 2019) | (df.Year.astype(int) == 2018)]
    
    return df
    

def load_peru_inflation_stats():
    data = get_peru_inflation_stats()
    data.to_csv("Dad_Peru_Inflation.csv", encoding='utf-8', index=False)

def load_argentina_inflation_stats():
    data = get_argentina_inflation_stats()
    data.to_csv("Dad_Argentina_Inflation.csv", encoding='utf-8', index=False)

def load_brazil_inflation_stats():
    data = get_brazil_inflation_stats()
    data.to_csv("Dad_Brazil_Inflation.csv", encoding='utf-8', index=False)

def load_chile_inflation_stats():
    data = get_chile_inflation_stats()
    data.to_csv("Dad_Chile_Inflation.csv", encoding='utf-8', index=False)

def load_mexico_inflation_stats():
    data = get_mexico_inflation_stats()
    data.to_csv("Dad_Mexico_Inflation.csv", encoding='utf-8', index=False)

def load_colombia_inflation_stats():
    data = get_colombia_inflation_stats()
    data.to_csv("Dad_Colombia_Inflation.csv", encoding='utf-8', index=False)



# load_peru_inflation_stats()
# load_argentina_inflation_stats()
# load_brazil_inflation_stats()
# load_chile_inflation_stats()
# load_mexico_inflation_stats()
# load_colombia_inflation_stats()