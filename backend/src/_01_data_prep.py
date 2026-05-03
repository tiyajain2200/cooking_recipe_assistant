import pandas as pd
import os

# Build paths relative to this file's location
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def clean_data(df):
    print('cleaning the dataset!')
    
    # Selecting relevant columns
    df = df[['title', 'ingredients', 'directions']]
    
    df = df.dropna()
    
    output_path = os.path.join(os.path.dirname(BASE_DIR), 'dataset', '_02_cleaned', 'recipes_cleaned.csv')
    df.to_csv(output_path, index=False)
    
    print('cleaned the dataset successfully!')

if __name__ == '__main__':
    input_path = os.path.join(os.path.dirname(BASE_DIR), 'dataset', '_01_raw', 'recipes.csv')
    
    # Loading first 1000 rows for demo purposes as the full dataset is 2GB
    print(f"Loading data from {input_path}...")
    df = pd.read_csv(input_path, nrows=1000)
    clean_data(df)
