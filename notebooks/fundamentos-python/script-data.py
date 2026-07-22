import time
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
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

# --- Visualizaciones Recomendadas (EDA) ---

# Convertir columnas a tipo numérico para poder graficar
numeric_cols = ['WINDSPD', 'GUST', 'TMPE']
for col in numeric_cols:
    # Extraer solo el número (ej. '12' de '12 kts') y convertir
    df[col] = pd.to_numeric(df[col].astype(str).str.extract('(\d+)', expand=False), errors='coerce')

# 1. Histogramas para entender la distribución de las variables
print("\n✅ Generando histogramas...")
df[numeric_cols].hist(bins=15, figsize=(15, 6), layout=(1, 3))
plt.suptitle("Distribución de Variables Numéricas")
plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.show()

# 2. Box Plots para identificar valores atípicos
print("✅ Generando diagramas de caja (box plots)...")
plt.figure(figsize=(15, 6))
sns.boxplot(data=df[numeric_cols])
plt.title("Diagramas de Caja para Detección de Atípicos")
plt.ylabel("Valores")
plt.show()

# 3. Matriz de Correlación para ver la relación entre variables
print("✅ Generando matriz de correlación...")
correlation_matrix = df[numeric_cols].corr()
plt.figure(figsize=(8, 6))
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt=".2f")
plt.title("Matriz de Correlación")
plt.show()
