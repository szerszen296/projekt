from flask import Flask, render_template, request, send_from_directory
from datetime import datetime, timedelta
import requests
import pandas as pd
import matplotlib.pyplot as plt
import os

app = Flask(__name__)

CURRENCIES = {
    'USD': 'Dolar amerykański',
    'EUR': 'Euro',
    'DKK': 'Korona duńska',
    'GBP': 'Funt brytyjski',
    'CHF': 'Frank szwajcarski',
    'JPY': 'Jen japoński',
    'CAD': 'Dolar kanadyjski',
    'AUD': 'Dolar australijski',
    'NOK': 'Korona norweska',
    'CZK': 'Korona czeska'
}

@app.route('/')
def index():
    code = request.args.get('currency', 'EUR').upper()
    if code not in CURRENCIES:
        code = 'EUR'

    weeks = int(request.args.get('time', 1))
    end_date = datetime.today().date()
    start_date = end_date - timedelta(weeks=weeks)

    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    url = f'https://api.nbp.pl/api/exchangerates/rates/A/{code}/{start_str}/{end_str}/?format=json'
    response = requests.get(url)

    if response.status_code != 200:
        return render_template('index.html', 
                               tbody_html='', 
                               chart_img=None, 
                               code=code, 
                               currencies=CURRENCIES, 
                               error=f"Błąd pobierania danych dla {code}")

    data = response.json()
    rates = [{'date': r['effectiveDate'], 'mid': r['mid']} for r in data['rates']]

    df = pd.DataFrame(rates)
    df['date'] = pd.to_datetime(df['date'])

    excel_path = f'{code}_data.xlsx'
    df.to_excel(excel_path, index=False)

    img_path = os.path.join('static', 'charts', f'{code}_chart.png')
    os.makedirs(os.path.dirname(img_path), exist_ok=True)

    plt.figure(figsize=(12, 6))
    plt.plot(df['date'], df['mid'], marker='o', linestyle='-', color='b')

    plt.title(f'Kurs {code} - ostatnie {weeks} tygodni')
    plt.xlabel('Data')
    plt.ylabel('Kurs (PLN)')

    plt.xticks(rotation=45, ha='right')

    plt.grid(True, linestyle='--', alpha=0.7)

    plt.tight_layout()

    plt.savefig(img_path)
    plt.close()

    tbody_html = ''.join(
        f"<tr><td>{row['date'].date()}</td><td>{row['mid']:.4f}</td></tr>"
        for _, row in df.iterrows()
    )

    return render_template('index.html',
                           tbody_html=tbody_html,
                           chart_img=f'charts/{code}_chart.png',
                           code=code,
                           currencies=CURRENCIES,
                           error=None)


@app.route('/download/excel')
def download_excel():
    code = request.args.get('currency', 'EUR').upper()
    filename = f'{code}_data.xlsx'
    if not os.path.exists(filename):
        return "Plik nie istnieje", 404
    return send_from_directory('.', filename, as_attachment=True)

@app.route('/download/chart')
def download_chart():
    code = request.args.get('currency', 'EUR').upper()
    filename = f'{code}_chart.png'
    filepath = os.path.join('static', 'charts', filename)
    if not os.path.exists(filepath):
        return "Plik nie istnieje", 404
    return send_from_directory('static/charts', filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=1111)
