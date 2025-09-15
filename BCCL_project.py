import mysql.connector

# Step 1: Connect to MySQL Database
db = mysql.connector.connect(
    host="localhost",      
    user="root",           
    password="simran",   
    database="bccl"        
)

cursor = db.cursor()

print("Database connected successfully!")

# Step 2: Chatbot function
def chatbot():
    print("\n Welcome to BCCL Mining Data Chatbot 🤖")
    print("You can ask me questions about mining data.")
    print("Example queries: 'total production', 'highest dispatch', 'rejection'")
    print("Type 'exit' to quit.\n")

    while True:
        query = input("You: ").lower()

        if query == "exit":
            print("Chatbot: Thank you See you again!")
            break

        elif "total production" in query:
            cursor.execute("SELECT Year, SUM(ProductionTons) FROM mine_data GROUP BY Year;")
            results = cursor.fetchall()
            print("Total Production per Year:")
            for row in results:
                print(f"   Year {row[0]}: {row[1]} tons")

        elif "highest dispatch" in query:
            cursor.execute("""
                SELECT MineID, SUM(DispatchTons) AS total_dispatch
                FROM mine_data
                GROUP BY MineID
                ORDER BY total_dispatch DESC
                LIMIT 1;
            """)
            row = cursor.fetchone()
            print(f"Mine with Highest Dispatch: {row[0]} ({row[1]} tons)")

        elif "rejection" in query:
            cursor.execute("""
                SELECT MineID, 
                       (SUM(RejectionTons)/SUM(ProductionTons))*100 AS rejection_percent
                FROM mine_data
                GROUP BY MineID;
            """)
            results = cursor.fetchall()
            print("📉 Rejection Percentage per Mine:")
            for row in results:
                print(f"   Mine {row[0]}: {row[1]:.2f}%")

        else:
            print("Chatbot: Sorry, I didn't understand. Try: 'total production', 'highest dispatch', 'rejection'")

# Step 3: Run chatbot
chatbot()
