import pandas as pd
from sklearn.datasets import fetch_openml
import os

# Fetch data / Pobranie danych
data = fetch_openml("credit-g", version=1, as_frame=True)
df = data.frame.copy()

# Recode target / Zamiana targetu
df['class'] = df['class'].map({'good': 0, 'bad': 1})

# Resolve script directory / Ścieżka do folderu skryptu
script_dir = os.path.dirname(os.path.abspath(__file__))

# Build full CSV path / Pełna ścieżka do pliku CSV
output_path = os.path.join(script_dir, "credit_data.csv")

# Write file / Zapis
df.to_csv(output_path, index=False)

print("Saved file to:")
print(output_path)