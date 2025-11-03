import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# Configuración de Chrome en modo headless
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Ruta al driver de Chrome
service = Service("/opt/homebrew/bin/chromedriver")
driver = webdriver.Chrome(service=service, options=chrome_options)

URL = "https://www.windguru.cz/187487"
driver.get(URL)

# Esperar a que cargue la tabla
time.sleep(5)

# Localizar todas las filas de la tabla
rows = driver.find_elements(By.CSS_SELECTOR, "#tabid_0_content_div > table > tbody > tr")

data = {}
headers = []

for row in rows:
    row_id = row.get_attribute("id")
    cols = [c.text.strip().replace("\n", " ") for c in row.find_elements(By.TAG_NAME, "td")]

    if row_id == "tabid_0_0_dates":
        headers = cols  # guardar las fechas/horas como cabeceras
    elif row_id in [
        "tabid_0_0_WINDSPD",
        "tabid_0_0_GUST",
        "tabid_0_0_SMER",
        "tabid_0_0_TMPE",
        "tabid_0_0_CDC",
        "tabid_0_0_APCP1s",
        "tabid_0_0_RATING",
        "tabid_0_0_tides"
    ]:
        var_name = row_id.replace("tabid_0_0_", "")  # nombre limpio de variable
        data[var_name] = cols

driver.quit()

# Crear DataFrame
# Crear DataFrame transpuesto
df = pd.DataFrame.from_dict(data, orient="index", columns=headers)

# Transponer para que las fechas sean filas
df = df.transpose().reset_index().rename(columns={"index": "Hora"})

print("✅ Datos organizados:")
print(df.head())

df.to_csv("calima_windguru_limpio.csv", index=False)
