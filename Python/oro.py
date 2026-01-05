#%%
"""
This script downloads, processes, and analyzes monthly gold prices in EUR and Spanish general CPI data, then computes the real gold price and its real monthly change since 2000.

Workflow:
1. Fetches monthly gold price data (in EUR, PM fixing, average price) from the LBMA dataset via DBnomics.
2. Filters the gold price data to include only records from January 2000 onwards and saves it as a CSV.
3. Plots the monthly gold price in EUR since 2000.
4. Downloads Spanish general CPI variation rates from INE, processes the date format, and saves as a CSV.
5. Merges gold price and CPI data on the period, computes the real gold price (adjusted for inflation), and calculates the real monthly percentage change in gold price.

Dependencies:
- dbnomics
- pandas
- matplotlib

Outputs:
- 'precio_oro_eur.csv': Gold price data since 2000.
- 'ipc_general.csv': CPI data.
- DataFrame with real gold price and its real monthly increment.
"""
from dbnomics import fetch_series
import pandas as pd
import matplotlib.pyplot as plt

#%%
# Definimos los parámetros de la serie
# Provider: LBMA, Dataset: gold_M
# Dimensions: se pasan como un diccionario de Python
df = fetch_series(
    provider_code='LBMA',
    dataset_code='gold_M',
    dimensions={
        'frequency': ['M'], 
        'unit': ['EUR'], 
        'time': ['PM'], 
        'price': ['AVG']
    }
)

#%%
# La librería ya devuelve un DataFrame con 'period' convertido a datetime
# Solo aplicamos el filtro de fecha
df_oro = df[df['period'] >= '2000-01-01'][['period', 'value']]

plt.figure(figsize=(10, 5))
plt.plot(df_oro['period'], df_oro['value'], marker='o', linestyle='-')
plt.xlabel('Fecha')
plt.ylabel('Precio del oro (EUR)')
plt.title('Precio mensual del oro (EUR) desde 2000')
plt.grid(True)
plt.tight_layout()
plt.show()



# %%
url = "https://www.ine.es/jaxiT3/files/t/csv_bdsc/50911.csv"  # tasa de variación IPC general [web:9]
df_ipc = pd.read_csv(url, sep=';', decimal=',')
df_ipc = df_ipc[df_ipc['Tipo de dato'] == 'Variación mensual'] # nos quedamos solo con la variación mensual

df_ipc['period'] = pd.to_datetime(df_ipc['Periodo'].str.replace('M', '-'), format='mixed')
df_ipc = df_ipc[['period', 'Total']].rename(columns={'Total': 'IPC'})
#%%
df_oro_ipc = pd.merge(df_oro, df_ipc, on='period', how='inner')
#%%
# Calcular el precio real del oro ajustado por IPC (base 100 en el primer mes)
ipc_base = df_oro_ipc['IPC'].iloc[0]
df_oro_ipc['IPC_indice'] = 100 * (1 + df_oro_ipc['IPC'] / 100).cumprod()
df_oro_ipc['value_real'] = df_oro_ipc['value'] * (df_oro_ipc['IPC_indice'].iloc[0] / df_oro_ipc['IPC_indice'])
plt.figure(figsize=(10, 5))
plt.plot(df_oro_ipc['period'], df_oro_ipc['value'], label='Precio nominal del oro (EUR)')
plt.plot(df_oro_ipc['period'], df_oro_ipc['value_real'], label='Precio real del oro (EUR, ajustado IPC)')
plt.xlabel('Fecha')
plt.ylabel('Precio del oro (EUR)')
plt.title('Precio mensual del oro: nominal vs real (ajustado por IPC)')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

#%% 
# Calcular el incremento real en porcentaje mensual
df_oro_ipc['real_monthly_change'] = df_oro_ipc['value_real'].pct_change() * 100

# Calculalar el incremento real en procentaje acumulado desde el inicio
df_oro_ipc['real_cumulative_change'] = (df_oro_ipc['value_real'] / df_oro_ipc['value_real'].iloc[0] - 1) * 100

plt.figure(figsize=(10, 5))
plt.plot(df_oro_ipc['period'], df_oro_ipc['real_cumulative_change'], label='Incremento acumulado real (%)')
plt.xlabel('Fecha')
plt.ylabel('Incremento acumulado real (%)')
plt.title('Incremento acumulado real del precio del oro (ajustado por IPC) desde 2000')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

#%%
# calcular la tasa anualizada del incremento real media
df_oro_ipc['real_annualized_change'] = ((1 + df_oro_ipc['real_monthly_change'] / 100) ** 12 - 1) *  100
plt.figure(figsize=(10, 5))
plt.plot(df_oro_ipc['period'], df_oro_ipc['real_annualized_change'], label='Tasa anualizada del incremento real (%)')
plt.xlabel('Fecha')
plt.ylabel('Tasa anualizada del incremento real (%)')
plt.title('Tasa anualizada del incremento real del precio del oro (ajustado por IPC)')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

#%%
df_oro_ipc.to_csv('precio_oro_eur.csv', index=False)
# %%

#%% Calcular media anualizada del incremento real (CAGR) de cada año
df_oro_ipc['year'] = df_oro_ipc['period'].dt.year
cagr_per_year = {}
for year, group in df_oro_ipc.groupby('year'):
    valor_inicial = group['value_real'].iloc[0]
    valor_final = group['value_real'].iloc[-1]
    n_months = len(group)
    cagr_year = (valor_final / valor_inicial) ** (12 / n_months) - 1
    cagr_per_year[year] = cagr_year * 100


# plotear el CAGR por año
plt.figure(figsize=(10, 5))
plt.bar(cagr_per_year.keys(), cagr_per_year.values())
plt.xlabel('Año')
plt.ylabel('CAGR (%)')
plt.title('CAGR anual del precio real del oro (ajustado por IPC)')
plt.grid(True)
plt.tight_layout()
plt.show()

# Calcular la media anualizada (CAGR) del precio real del oro en todo el periodo
valor_inicial = df_oro_ipc['value_real'].iloc[0]
valor_final = df_oro_ipc['value_real'].iloc[-1]
n_years = (df_oro_ipc['period'].iloc[-1] - df_oro_ipc['period'].iloc[0]).days / 365.25

cagr = (valor_final / valor_inicial) ** (1 / n_years) - 1
print(f"Media anualizada del incremento real (CAGR): {cagr * 100:.2f}%")
# ...existing code...

# %%
