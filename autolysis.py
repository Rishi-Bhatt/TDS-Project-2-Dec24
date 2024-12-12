# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "httpx",
#   "pandas",
#   "seaborn",
#   "matplotlib",
#   "chardet",
# ]
# ///

import os
import sys
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import httpx
import chardet

# Constants
API_URL = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
AIPROXY_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIxZjEwMDAzMzBAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.XSVDp41zlfdMKES0EyGYXUrd78d76RuzJxgfL20axo4"

def load_data(file_path):
    """Load CSV data with encoding detection."""
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' does not exist.")
        sys.exit(1)
    
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    encoding = result['encoding']
    print(f"Detected encoding: {encoding}")
    
    return pd.read_csv(file_path, encoding=encoding)

def analyze_data(df):
    """Perform basic data analysis."""
    print("Performing data analysis...")
    numeric_df = df.select_dtypes(include=['number'])
    analysis = {
        'summary': df.describe(include='all').to_dict(),
        'missing_values': df.isnull().sum().to_dict(),
        'correlation': numeric_df.corr().to_dict(),
        'data_types': df.dtypes.apply(str).to_dict()
    }
    return analysis

def visualize_data(df):
    """Generate and save visualizations."""
    print("Generating visualizations...")
    sns.set(style="whitegrid")
    numeric_columns = df.select_dtypes(include=['number']).columns
    
    # Generate distribution plots
    for column in numeric_columns:
        plt.figure()
        sns.histplot(df[column].dropna(), kde=True)
        plt.title(f'Distribution of {column}')
        plt.savefig(f'{column}_distribution.png')
        plt.close()
        print(f"Saved {column}_distribution.png")
    
    # Generate correlation heatmap
    if len(numeric_columns) > 1:
        plt.figure(figsize=(10, 8))
        sns.heatmap(df[numeric_columns].corr(), annot=True, cmap="coolwarm")
        plt.title("Correlation Heatmap")
        plt.savefig("correlation_heatmap.png")
        plt.close()
        print("Saved correlation_heatmap.png")

def generate_narrative(analysis):
    """Generate narrative using LLM."""
    print("Generating narrative with LLM...")
    
    if not AIPROXY_TOKEN:
        print("Error: AIPROXY_TOKEN environment variable is not set.")
        sys.exit(1)

    headers = {
        'Authorization': f'Bearer {AIPROXY_TOKEN}',
        'Content-Type': 'application/json'
    }
    prompt = (
        "Provide a detailed analysis based on the following data summary:\n"
        f"{analysis}"
    )
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        response = httpx.post(API_URL, headers=headers, json=data, timeout=30.0)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e}")
    except httpx.RequestError as e:
        print(f"Request error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return "Narrative generation failed due to an error."

def main(file_path):
    print(f"Processing file: {file_path}")
    df = load_data(file_path)
    analysis = analyze_data(df)
    visualize_data(df)
    narrative = generate_narrative(analysis)
    
    output_file = 'README.md'
    with open(output_file, 'w') as f:
        f.write(narrative)
    
    print(f"Narrative saved to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: uv run autolysis.py <dataset.csv>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    main(file_path)
