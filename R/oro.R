# Cargamos las librerías necesarias
library(rdbnomics)
library(tidyverse)
library(lubridate)
library(scales)

# 1. Obtener datos de precio del oro desde DBnomics
# Provider: LBMA, Dataset: gold_M
df_oro_raw <- rdb(
  provider_code = 'LBMA',
  dataset_code = 'gold_M',
  mask = 'M.EUR.PM.AVG'
)

# 2. Procesar datos del oro
df_oro <- df_oro_raw %>%
  filter(period >= as.Date("2000-01-01")) %>%
  select(period, value) %>%
  drop_na()

# Gráfico: Precio Nominal
ggplot(df_oro, aes(x = period, y = value)) +
  geom_line(color = "blue") +
  geom_point(size = 1) +
  labs(title = "Precio mensual del oro (EUR) desde 2000",
       x = "Fecha", y = "Precio del oro (EUR)") +
  theme_minimal()

# 3. Descargar y procesar datos del IPC (INE España)
url_ipc <- "https://www.ine.es/jaxiT3/files/t/csv_bdsc/50911.csv"
df_ipc_raw <- read_delim(url_ipc, delim = ";", locale = locale(decimal_mark = ","))

df_ipc <- df_ipc_raw %>%
  filter(`Tipo de dato` == "Variación mensual") %>%
  mutate(
    # Reemplazamos 'M' por '-' para convertir a fecha
    period_str = str_replace(Periodo, "M", "-"),
    period = ym(period_str)
  ) %>%
  select(period, IPC = Total)

# 4. Merge y cálculos de precio real
df_oro_ipc <- inner_join(df_oro, df_ipc, by = "period") %>%
  arrange(period)

# Calcular índice IPC y valor real
df_oro_ipc <- df_oro_ipc %>%
  mutate(
    # El primer valor del índice se basa en la primera variación
    IPC_indice = 100 * cumprod(1 + IPC / 100),
    value_real = value * (first(IPC_indice) / IPC_indice)
  )

# Gráfico: Nominal vs Real
ggplot(df_oro_ipc) +
  geom_line(aes(x = period, y = value, color = "Nominal")) +
  geom_line(aes(x = period, y = value_real, color = "Real (Ajustado IPC)")) +
  labs(title = "Precio mensual del oro: nominal vs real",
       x = "Fecha", y = "Precio (EUR)", color = "Tipo") +
  theme_minimal()

# 5. Incrementos y cambios acumulados
df_oro_ipc <- df_oro_ipc %>%
  mutate(
    real_monthly_change = (value_real / lag(value_real) - 1) * 100,
    real_cumulative_change = (value_real / first(value_real) - 1) * 100,
    real_annualized_change = ((1 + real_monthly_change / 100)^12 - 1) * 100
  )

# Gráfico: Incremento acumulado
ggplot(df_oro_ipc, aes(x = period, y = real_cumulative_change)) +
  geom_line(color = "darkgreen") +
  labs(title = "Incremento acumulado real del precio del oro desde 2000",
       x = "Fecha", y = "Incremento acumulado (%)") +
  theme_minimal()

# 6. Cálculo de CAGR anual (por año)
cagr_per_year <- df_oro_ipc %>%
  group_by(year = year(period)) %>%
  summarise(
    valor_inicial = first(value_real),
    valor_final = last(value_real),
    n_months = n(),
    cagr_year = ((valor_final / valor_inicial)^(12 / n_months) - 1) * 100
  )

# Gráfico: CAGR por año
ggplot(cagr_per_year, aes(x = year, y = cagr_year)) +
  geom_col(fill = "steelblue") +
  labs(title = "CAGR anual del precio real del oro",
       x = "Año", y = "CAGR (%)") +
  theme_minimal()

# 7. CAGR total del periodo
valor_inicial_tot <- first(df_oro_ipc$value_real)
valor_final_tot <- last(df_oro_ipc$value_real)
n_years <- as.numeric(difftime(last(df_oro_ipc$period), first(df_oro_ipc$period), units = "days")) / 365.25

cagr_total <- ((valor_final_tot / valor_inicial_tot)^(1/n_years) - 1) * 100
cat(sprintf("Media anualizada del incremento real (CAGR): %.2f%%\n", cagr_total))

# Guardar CSV
write_csv(df_oro_ipc, "precio_oro_eur_r.csv")