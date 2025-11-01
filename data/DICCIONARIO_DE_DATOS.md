## Diccionario de datos

Este documento resume las columnas, tipos inferidos, valores de ejemplo y notas para los archivos dentro de la carpeta `data/`.

---

### 1) `Bank_Price_Data_China new.csv`

- Ruta: `data/Bank_Price_Data_China new.csv`
- Descripción: Series temporales (diarias) de precios/valores por localidades/códigos (probablemente precios o índices regionales).
- Formato de fecha: Día/Mes/Año (ej. `24/01/2017`).

Columnas (ordenadas):

`Date`, `LS_ny`, `LS_jt`, `LS_gs`, `LS_js`, `LS_zg`, `JC_pa`, `JC_pf`, `JC_hx`, `JC_ms`, `JC_zs`, `JC_xy`, `JC_gd`, `JC_zx`, `CC_nb`, `CC_js`, `CC_hz`, `CC_nj`, `CC_bj`, `CC_sh`, `CC_gy`, `RC_jy`, `RC_zjg`, `RC_wx`, `RC_cs`, `RC_sn`

Tipo (inferido):

- `Date`: string / fecha (DD/MM/YYYY). Recomendado: convertir a tipo datetime.
- Las demás columnas: numéricas (float). Algunas muestran ceros a la izquierda o formatos con dos dígitos antes del punto (ej. `04.06`) — limpiar si fuera necesario.

Ejemplo (primera fila de datos):

- `Date`: `24/01/2017`
- `LS_ny`: `3.18`
- `LS_jt`: `5.98`
- `JC_pa`: `9.27`
- `RC_sn`: `13.39`

Notas / observaciones:

- Valores separados por comas, sin cabeceras duplicadas.
- Algunos valores muestran ceros y formatos inconsistentes (p. ej. `04.06`, `06.02`) — verificar que no sean artefactos de importación.
- Verificar valores nulos y vacíos antes de procesar (no se detectaron NAs directos en la muestra leída, pero es necesario un escaneo completo).

---

### 2) `final_dataset_tata_motors.csv`

- Ruta: `data/final_dataset_tata_motors.csv`
- Descripción: Dataset intradiario (timestamps con zona horaria) con precios OHLC, volumen y múltiples indicadores técnicos.

Columnas (ordenadas):

`timestamp`, `open`, `high`, `low`, `close`, `volume`, `RSI`, `MACD`, `MACD_signal`, `MACD_hist`, `Doji`, `date`, `sentiment`, `ema_50`, `ema_200`, `rsi`, `MACD_12_26_9`, `MACDh_12_26_9`, `MACDs_12_26_9`, `avg_volume_10d`, `avg_volume_50d`, `volume_ratio`, `master_score`, `52_week_high`, `distance_from_high`

Tipo (inferido):

- `timestamp`: string / datetime con zona (ej. `2025-07-14 09:15:00+05:30`). Recomendado: parsear a datetime aware.
- `open`, `high`, `low`, `close`: numérico (float).
- `volume`, `avg_volume_10d`, `avg_volume_50d`: numérico entero o float (volúmenes grandes).
- `RSI`, `MACD`, `MACD_*`, `rsi`, `volume_ratio`, `master_score`: numérico (float).
- `Doji`: aparentemente binario/flag (ej. `0` o `100` en muestra) — confirmar semántica.
- `date`: string (fecha sin hora), puede duplicar la información en `timestamp`.
- `sentiment`: float (en la muestra aparece `0.0` y muchas celdas vacías) — revisar origen.

Ejemplo (primeras filas):

- `timestamp`: `2025-07-14 09:15:00+05:30`
- `open`: `680.8`, `high`: `680.95`, `low`: `677.1`, `close`: `678.2`, `volume`: `169414`
- `RSI`: `0.0` (varios registros con 0.0; más adelante valores reales como `63.1479` aparecen)

Notas / observaciones:

- Hay columnas duplicadas de indicadores (por ejemplo varias variantes de MACD) — confirmar cuáles son necesarias para análisis.
- Se observan muchos valores vacíos en columnas calculadas (p. ej. `ema_200` aparece vacío en muchas filas).
- `timestamp` incluye zona `+05:30` (probablemente India). Tener cuidado con conversiones de zona horario si se fusiona con otras fuentes.

---

### 3) `pool_swaps.csv`

- Ruta: `data/pool_swaps.csv`
- Descripción: Registros de swaps en pools (probablemente DeFi / blockchain). Incluye identificadores de transacción, mints de tokens, cantidades, precios y métricas de pool (TVL, utilización, fees, etc.).

Columnas (extraídas de la cabecera):

`slot`, `block_time`, `tx_signature`, `token_mint_a`, `token_mint_b`, `token_vault_a`, `token_vault_b`, `num_swaps`, `token_amount_a`, `token_amount_b`, `pre_balance_a`, `pre_balance_b`, `post_balance_a`, `post_balance_b`, `decimals_a`, `decimals_b`, `token_price_a`, `token_price_b`, `token_ema_a`, `token_ema_b`, `pool_address`, `fee_tier`, `token_amount_a_ui`, `token_amount_b_ui`, `volume_usd`, `fee_usd`, `lp_fee_usd`, `date`, `price_ratio`, `tvl_usd`, `tvl_utilization`, `balance_ratio`, `balance_imbalance`

Tipo (inferido):

- `slot`: entero (bloque/slot de la cadena).
- `block_time`, `date`: datetime / string (ej. `2025-10-14 16:20:42`).
- `tx_signature`, `token_mint_a/b`, `token_vault_a/b`, `pool_address`: strings (identificadores hex/base58).
- `num_swaps`: entero.
- `token_amount_a`, `token_amount_b`, `pre_balance_*`, `post_balance_*`, `token_amount_*_ui`, `volume_usd`, `fee_usd`, `lp_fee_usd`, `tvl_usd`: numéricos (enteros o floats). Observado en la muestra: valores grandes (p. ej. `3010327305`, `24669982850`) y también valores con formato de miles/decimales.
- `decimals_a`, `decimals_b`: enteros (p. ej. `9`, `6`).
- `token_price_a`, `token_price_b`, `token_ema_a/b`, `price_ratio`, `tvl_utilization`, `balance_ratio`, `balance_imbalance`: numéricos (float; algunos en notación científica en muestra).

Ejemplo (fila de muestra):

- `slot`: `373348755`
- `block_time/date`: `2025-10-14 16:20:42`
- `tx_signature`: `4uPbbFd37Rqyy8QFSw6Kiv...` (truncado)
- `token_amount_a`: `2795627`
- `token_amount_b`: `22913485`
- `token_amount_a_ui`: `0.002795627` (en otra fila aparece `3.010327305` — revisa la conversión UI)
- `volume_usd`: `22.913485` (ejemplo)

Notas / observaciones:

- Archivo muy grande; la muestra recuperada contiene filas donde algunos campos pueden ser `0` (posible señal de operaciones cero o placeholders).
- Los identificadores de token usan formatos típicos de cadena (base58/hex). Verificar normalización si se unen con otros datasets.
- `token_amount_*` (sin `_ui`) parecen en unidades base (token base), mientras que `_ui` indica cantidad normalizada (según `decimals_*`). Confirmar la interpretación con el origen.

---

## Recomendaciones generales

- Normalizar formatos de fecha/tiempo (convertir `Date` y `timestamp` a datetime). Establecer zona horaria clara.
- Revisar y unificar separadores decimales si hay inconsistencias.
- Detectar y registrar filas con valores nulos/faltantes antes de análisis o modelado.
- Para `pool_swaps.csv`, consideren calcular columnas derivadas estandarizadas (p. ej. `token_amount_a_ui` a partir de `token_amount_a` / 10\*\*`decimals_a`) si no están confiables.
- Validar claves únicas y duplicados (por ejemplo: `timestamp` + `tx_signature` o `slot` + `tx_signature`).

Si quieres, puedo:

- Generar un CSV/JSON con el resumen de columnas y tipos detectados.
- Ejecutar un escaneo rápido en cada archivo para contar valores nulos y tipos reales (rápido pero puede tardar en `pool_swaps.csv`).

---

Archivo creado automáticamente: `data/DICCIONARIO_DE_DATOS.md` — puedes editarlo si quieres descripciones más detalladas para columnas específicas.
