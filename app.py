from flask import Flask, render_template, jsonify, send_from_directory
from datetime import datetime, timedelta
import requests
import pandas as pd
import matplotlib.pyplot as plt
import os

app = Flask(__name__)

@app.route('/')
def index():
    code = 'EUR'
    table = 'A'
    end_date = datetime.today().date()
    start_date = end_date - timedelta(days=7)

    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    url = f'https://api.nbp.pl/api/exchangerates/rates/{table}/{code}/{start_str}/{end_str}/'
    response = requests.get(url)

    if response.status_code != 200:
        return render_template('index.html', tbody_html='', error="Błąd pobierania danych")

    data = response.json()
    rates = [{'date': r['effectiveDate'], 'mid': r['mid']} for r in data['rates']]
    
    df = pd.DataFrame(rates)
    df['date'] = pd.to_datetime(df['date'])

    excel_path = 'eur_data.xlsx'
    df.to_excel(excel_path, index=False)

    img_path = os.path.join('static', 'charts', 'eur_chart.png')
    os.makedirs(os.path.dirname(img_path), exist_ok=True)
    
    plt.figure(figsize=(8, 4))
    plt.plot(df['date'], df['mid'], marker='o')
    plt.title('Kurs EUR - ostatnie 7 dni')
    plt.xlabel('Data')
    plt.ylabel('Kurs (PLN)')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(img_path)
    plt.close()

    tbody_html = ''.join(
        f"<tr><td>{row['date'].date()}</td><td>{row['mid']:.4f}</td></tr>"
        for _, row in df.iterrows()
    )

    return render_template('index.html', tbody_html=tbody_html, chart_img='charts/eur_chart.png')


if __name__ == '__main__':
    app.run(debug=True, port=1111)
