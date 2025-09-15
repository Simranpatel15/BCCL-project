from flask import Flask, request, render_template_string, redirect, url_for
import mysql.connector
import pandas as pd
import plotly.graph_objs as go
import plotly.offline as pyo
from fuzzywuzzy import process

app = Flask(__name__)

# MySQL Connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="simran",  
    database="BCCL"
)
cursor = db.cursor()

# Predefined options
options = [
    "Total production per year",
    "Mine with highest dispatch",
    "Average rejection"
]

# Flask Routes
@app.route("/", methods=["GET", "POST"])
def databot():
    response_list = []
    chart_html = ""
    if request.method == "POST":
        query = request.form.get("query", "").lower()
        selected_mine = request.form.get("mine", "")
        selected_year = request.form.get("year", "")

        # Fuzzy matching with predefined options
        best_match = process.extractOne(query, options)
        if best_match:
            query = best_match[0].lower()

        # Total production per year
        if "total production" in query:
            sql = "SELECT Year, SUM(ProductionTons) FROM mine_data"
            if selected_mine:
                sql += f" WHERE MineID='{selected_mine}'"
            if selected_year:
                sql += " AND" if "WHERE" in sql else " WHERE"
                sql += f" Year={selected_year}"
            sql += " GROUP BY Year;"
            cursor.execute(sql)
            results = cursor.fetchall()
            for r in results:
                response_list.append(f"Year {r[0]}: {r[1]} tons")

            # Plot line chart
            years = [r[0] for r in results]
            production = [r[1] for r in results]
            fig = go.Figure(data=go.Scatter(x=years, y=production, mode='lines+markers'))
            fig.update_layout(title='Total Production per Year', xaxis_title='Year', yaxis_title='Production (Tons)')
            chart_html = pyo.plot(fig, output_type='div', include_plotlyjs=False)

        # Mine with highest dispatch
        elif "highest dispatch" in query:
            sql = "SELECT MineID, SUM(DispatchTons) AS total_dispatch FROM mine_data GROUP BY MineID ORDER BY total_dispatch DESC LIMIT 1;"
            cursor.execute(sql)
            row = cursor.fetchone()
            response_list.append(f"Mine with highest dispatch: {row[0]} ({row[1]} tons)")

        # Average rejection
        elif "average rejection" in query:
            sql = "SELECT AVG((RejectionTons/ProductionTons)*100) FROM mine_data"
            if selected_mine:
                sql += f" WHERE MineID='{selected_mine}'"
            if selected_year:
                sql += " AND" if "WHERE" in sql else " WHERE"
                sql += f" Year={selected_year}"
            cursor.execute(sql)
            avg = cursor.fetchone()[0]
            response_list.append(f"Average rejection: {avg:.2f}%")

        else:
            response_list.append("Sorry, I didn’t understand your question.")

    # Get unique mines and years for dropdowns
    cursor.execute("SELECT DISTINCT MineID FROM mine_data;")
    mines = [r[0] for r in cursor.fetchall()]
    cursor.execute("SELECT DISTINCT Year FROM mine_data;")
    years = [r[0] for r in cursor.fetchall()]

    # Generate buttons HTML
    buttons_html = "".join([f'<button type="submit" name="query" value="{o}" class="px-4 py-2 bg-blue-500 text-white rounded m-1 hover:bg-blue-600">{o}</button>' for o in options])

    # Tailwind + Chat interface template
    template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>BCCL Mining DataBot 🤖</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100 min-h-screen p-6">
        <div class="max-w-3xl mx-auto bg-white p-6 rounded shadow">
            <h1 class="text-2xl font-bold mb-4">BCCL Mining DataBot 🤖</h1>
            <form method="post" class="mb-4">
                <div class="mb-2">{buttons_html}</div>
                <div class="flex space-x-2 mb-2">
                    <input type="text" name="query" placeholder="Or type your question..." class="flex-1 px-3 py-2 border rounded">
                    <select name="mine" class="px-2 border rounded">
                        <option value="">All Mines</option>
                        {''.join([f'<option value="{m}">{m}</option>' for m in mines])}
                    </select>
                    <select name="year" class="px-2 border rounded">
                        <option value="">All Years</option>
                        {''.join([f'<option value="{y}">{y}</option>' for y in years])}
                    </select>
                    <button type="submit" class="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600">Ask</button>
                </div>
            </form>
            <div class="space-y-2">
                {"".join([f'<div class="p-2 bg-gray-200 rounded">{r}</div>' for r in response_list])}
            </div>
            <div class="mt-4">{chart_html}</div>
        </div>
    </body>
    </html>
    """
    return render_template_string(template)

# CSV Upload Route
@app.route("/upload", methods=["GET", "POST"])
def upload_csv():
    message = ""
    if request.method == "POST":
        file = request.files.get("file")
        if file:
            df = pd.read_csv(file)
            for _, row in df.iterrows():
                cursor.execute("""
                    INSERT INTO mine_data (MineID, Year, Month, ProductionTons, DispatchTons, RejectionTons)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (row['MineID'], int(row['Year']), int(row['Month']), int(row['ProductionTons']), int(row['DispatchTons']), int(row['RejectionTons'])))
            db.commit()
            message = "CSV data uploaded successfully!"
    return f"""
    <h2>Upload CSV Data</h2>
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="file">
        <input type="submit" value="Upload">
    </form>
    <p>{message}</p>
    <a href="/">Go back to DataBot</a>
    """

if __name__ == "__main__":
    app.run(debug=True)
