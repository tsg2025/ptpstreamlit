import streamlit as st
import yfinance as yf
import json
from datetime import datetime

# Title of the app
st.title("Stock Price Database with IndexedDB")

# Fetch stock data from Yahoo Finance
def fetch_stock_data(ticker):
    stock = yf.Ticker(ticker)
    data = stock.history(period="1mo")  # Fetch 1 month of historical data
    # Convert DataFrame to a list of dictionaries and serialize dates
    data = data.reset_index()
    data["Date"] = data["Date"].dt.strftime("%Y-%m-%d")  # Convert Timestamp to string
    return data.to_dict(orient="records")  # Convert to list of dictionaries

# HTML and JavaScript to interact with IndexedDB
html_code = """
<!DOCTYPE html>
<html>
<head>
    <title>Stock Price Database</title>
</head>
<body>
    <h2>Stock Price Database</h2>
    <button onclick="downloadData()">Download Data</button>
    <button onclick="viewData()">View Data</button>
    <button onclick="deleteData()">Delete Data</button>
    <p id="status"></p>
    <pre id="output"></pre>

    <script>
        let db;
        const dbName = "StockDB";
        const storeName = "StockStore";

        function openDB() {
            return new Promise((resolve, reject) => {
                const request = indexedDB.open(dbName, 1);

                request.onupgradeneeded = function(event) {
                    db = event.target.result;
                    if (!db.objectStoreNames.contains(storeName)) {
                        db.createObjectStore(storeName, { keyPath: "id" });
                        console.log("Database created and store initialized.");
                    }
                };

                request.onsuccess = function(event) {
                    db = event.target.result;
                    console.log("Database opened successfully.");
                    resolve(db);
                };

                request.onerror = function(event) {
                    console.error("Error opening database:", event.target.error);
                    reject("Error opening database.");
                };
            });
        }

        function downloadData() {
            console.log("Download Data button clicked.");
            const stockData = JSON.parse('{{ stock_data | tojson | safe }}');
            console.log("Stock data received:", stockData);

            openDB().then(db => {
                const transaction = db.transaction([storeName], "readwrite");
                const store = transaction.objectStore(storeName);

                stockData.forEach((data, index) => {
                    data.id = `${data.symbol}_${index}`; // Add a unique ID for each record
                    const request = store.put(data);
                    request.onsuccess = () => {
                        console.log(`Data saved: ${data.id}`);
                        document.getElementById("status").innerText = "Data downloaded and saved successfully.";
                    };
                    request.onerror = () => {
                        console.error(`Error saving data: ${data.id}`);
                        document.getElementById("status").innerText = "Error saving data.";
                    };
                });
            }).catch(error => {
                console.error("Error:", error);
                document.getElementById("status").innerText = error;
            });
        }

        function viewData() {
            console.log("View Data button clicked.");
            openDB().then(db => {
                const transaction = db.transaction([storeName], "readonly");
                const store = transaction.objectStore(storeName);
                const request = store.getAll();

                request.onsuccess = () => {
                    console.log("Data retrieved:", request.result);
                    document.getElementById("output").innerText = JSON.stringify(request.result, null, 2);
                };

                request.onerror = () => {
                    console.error("Error reading data.");
                    document.getElementById("output").innerText = "Error reading data.";
                };
            }).catch(error => {
                console.error("Error:", error);
                document.getElementById("status").innerText = error;
            });
        }

        function deleteData() {
            console.log("Delete Data button clicked.");
            const request = indexedDB.deleteDatabase(dbName);

            request.onsuccess = () => {
                console.log("Database deleted successfully.");
                document.getElementById("status").innerText = "Database deleted successfully.";
                document.getElementById("output").innerText = "";
            };

            request.onerror = () => {
                console.error("Error deleting database.");
                document.getElementById("status").innerText = "Error deleting database.";
            };
        }
    </script>
</body>
</html>
"""

# Fetch stock data for Apple, Google, and Microsoft
tickers = ["AAPL", "GOOGL", "MSFT"]
stock_data = []
for ticker in tickers:
    data = fetch_stock_data(ticker)
    for entry in data:
        entry["symbol"] = ticker  # Add symbol to each entry
    stock_data.extend(data)

# Debug: Print stock data to the terminal
print("Stock Data:", json.dumps(stock_data, indent=2))

# Display the HTML in the Streamlit app
st.components.v1.html(html_code.replace("{{ stock_data | tojson | safe }}", json.dumps(stock_data)), height=600)
