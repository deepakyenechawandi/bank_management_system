import mysql.connector
import tkinter as tk
from tkinter import *
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
from datetime import date  # for date of account creation when new customer account is created.
from decimal import Decimal


# Backend python functions code starts :

# Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'deepak06',  
    'database': 'bank_management'
}

# Initialize Database and Tables
def initialize_database():
    conn = mysql.connector.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password']            
    )
    cursor = conn.cursor()
    
    try:
        # Create database if not exists
        cursor.execute("CREATE DATABASE IF NOT EXISTS bank_management")
        cursor.execute("USE bank_management")
        
        # Create admin table first
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                admin_id VARCHAR(20) PRIMARY KEY,
                password VARCHAR(50)
            )
        """)
        
        # Create customers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                account_number VARCHAR(20) PRIMARY KEY,
                pin VARCHAR(4) NOT NULL,
                balance DECIMAL(10,2) DEFAULT 0.0,
                creation_date DATE,
                holder_name VARCHAR(100),
                account_type VARCHAR(20),
                date_of_birth DATE,
                mobile_number VARCHAR(15),
                gender VARCHAR(10),
                nationality VARCHAR(50),
                kyc VARCHAR(100)
            )
        """)

        # Add transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INT PRIMARY KEY AUTO_INCREMENT,
                account_number VARCHAR(20),
                transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                transaction_type VARCHAR(20),
                amount DECIMAL(10,2),
                balance DECIMAL(10,2),
                FOREIGN KEY (account_number) REFERENCES customers(account_number)
                ON DELETE CASCADE
            )
        """)
        
        # Now check for default admin and add if not exists
        cursor.execute("SELECT COUNT(*) FROM admins WHERE admin_id = 'admin'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO admins (admin_id, password) 
                VALUES ('admin', 'admin123')
            """)
            
        conn.commit()
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()
        conn.close()


# Database utility functions
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def get_customer_profile(account_number):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT holder_name, mobile_number, nationality 
            FROM customers 
            WHERE account_number = %s
        """, (account_number,))
        
        return cursor.fetchone()
        
    except mysql.connector.Error as err:
        print(f"Error fetching profile: {err}")
        return None
    finally:
        if 'conn' in locals():
            cursor.close()
            conn.close()


def is_valid(customer_account_number):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM customers WHERE account_number = %s", 
                  (customer_account_number,))
    count = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    return count == 0

def check_credentials(identity, password, choice, admin_access=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if choice == 1:  # Admin login
        cursor.execute("SELECT COUNT(*) FROM admins WHERE admin_id = %s AND password = %s",
                      (identity, password))
    else:  # Customer login
        cursor.execute("SELECT COUNT(*) FROM customers WHERE account_number = %s AND pin = %s",
                      (identity, password))
    
    exists = cursor.fetchone()[0] > 0
    
    cursor.close()
    conn.close()
    
    return exists

def display_account_summary(identity, choice):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM customers WHERE account_number = %s", (identity,))
    customer = cursor.fetchone()
    
    if not customer:
        return "\n# No account associated with the entered account number exists! #"
    
    if choice == 1:  # Full summary
        output_message = f"""Account number: {customer[0]}
Current balance: {customer[2]}
Date of account creation: {customer[3]}
Name of account holder: {customer[4]}
Type of account: {customer[5]}
Date of Birth: {customer[6]}
Mobile number: {customer[7]}
Gender: {customer[8]}
Nationality: {customer[9]}
KYC: {customer[10]}"""
    else:  # Balance only
        output_message = f"Current balance: {customer[2]}"
    
    cursor.close()
    conn.close()
    
    return output_message

def delete_customer_account(identity, choice):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM customers WHERE account_number = %s", (identity,))
    rows_affected = cursor.rowcount
    
    conn.commit()
    cursor.close()
    conn.close()
    
    if rows_affected > 0:
        output_message = f"Account with account no.{identity} closed successfully!"
    else:
        output_message = "Account not found!"
    
    if choice == 1:
        adminMenu.printMessage_outside(output_message)
    print(output_message)

def create_admin_account(identity, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO admins (admin_id, password) VALUES (%s, %s)",
                      (identity, password))
        conn.commit()
        output_message = "Admin account created successfully!"
    except mysql.connector.Error as err:
        output_message = f"Error creating admin account: {err}"
    
    adminMenu.printMessage_outside(output_message)
    print(output_message)
    
    cursor.close()
    conn.close()

def update_customer_profile(account_number, **updates):
    """
    Updates customer profile information
    updates can include: holder_name, mobile_number, nationality
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Build the UPDATE query dynamically based on provided fields
        update_fields = []
        values = []
        
        for field, value in updates.items():
            if value:  # Only include fields that have values
                update_fields.append(f"{field} = %s")
                values.append(value)
        
        if not update_fields:  # If no fields to update
            return "No changes requested"
            
        # Add account_number to values
        values.append(account_number)
        
        # Construct and execute the query
        query = f"""
            UPDATE customers 
            SET {', '.join(update_fields)}
            WHERE account_number = %s
        """
        
        cursor.execute(query, values)
        conn.commit()
        
        if cursor.rowcount > 0:
            return "Profile updated successfully!"
        else:
            return "No changes were made"
            
    except mysql.connector.Error as err:
        return f"Error updating profile: {err}"
    finally:
        cursor.close()
        conn.close()


def delete_admin_account(identity):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM admins WHERE admin_id = %s", (identity,))
    rows_affected = cursor.rowcount
    
    conn.commit()
    cursor.close()
    conn.close()
    
    if rows_affected > 0:
        output_message = f"Account with admin id {identity} closed successfully!"
    else:
        output_message = "Account not found :("
    
    adminMenu.printMessage_outside(output_message)
    print(output_message)

def change_PIN(identity, new_PIN):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE customers SET pin = %s WHERE account_number = %s",
                  (new_PIN, identity))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    output_message = "PIN changed successfully."
    customerMenu.printMessage_outside(output_message)
    print(output_message)


def transaction(account_number, amount, type_of_transaction):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn:
            return "Database connection failed"
        
        cursor = conn.cursor(buffered=True)
        
        # Get current balance
        cursor.execute("SELECT balance FROM customers WHERE account_number = %s", 
                      (account_number,))
        result = cursor.fetchone()
        current_balance = float(result[0])
        
        if type_of_transaction == 0:  # Withdrawal
            if amount > current_balance:
                return f"Insufficient funds. Current balance: {current_balance}"
            new_balance = current_balance - amount
            transaction_type = "Withdrawal"
            
        elif type_of_transaction == 1:  # Deposit
            new_balance = current_balance + amount
            transaction_type = "Deposit"
            
        elif type_of_transaction == 2:  # Balance Check
            return f"Current balance: {current_balance}"
            
        # Update balance
        cursor.execute("""
            UPDATE customers 
            SET balance = %s 
            WHERE account_number = %s
        """, (new_balance, account_number))

        # Log the transaction
        print(f"Logging transaction: Account={account_number}, Type={transaction_type}, Amount={amount}, Balance={new_balance}")  # Debug print
        
        cursor.execute("""
            INSERT INTO transactions 
            (account_number, transaction_type, amount, balance)
            VALUES (%s, %s, %s, %s)
        """, (account_number, transaction_type, amount, new_balance))

        conn.commit()
        print("Transaction logged successfully")  # Debug print

        if type_of_transaction == 0:
            return f"Amount of rupees {amount} withdrawn successfully. New balance: {new_balance}"
        else:
            return f"Amount of rupees {amount} deposited successfully. New balance: {new_balance}"

    except Exception as e:
        print(f"Error in transaction: {str(e)}")  # Debug print
        if conn:
            conn.rollback()
        return f"Transaction failed: {str(e)}"
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()



def log_transaction(account_number, transaction_type, amount, balance):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO transactions 
            (account_number, transaction_type, amount, balance)
            VALUES (%s, %s, %s, %s)
        """, (account_number, transaction_type, amount, balance))
        
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error logging transaction: {err}")
    finally:
        if 'conn' in locals():
            cursor.close()
            conn.close()





# Initialize database when module is loaded
initialize_database()

class UpdateProfile:
    def __init__(self, window=None):
        self.master = window
        window.geometry("411x400+519+278")
        window.minsize(120, 1)
        window.maxsize(1370, 749)
        window.resizable(0, 0)
        window.title("Update Profile")
        window.configure(background="#f2f3f4")

        # Holder Name Entry
        self.Label1 = tk.Label(window, background="#f2f3f4", 
                              font="-family {Segoe UI} -size 9",
                              text='Holder Name:')
        self.Label1.place(relx=0.146, rely=0.171, height=21, width=124)

        self.name_entry = tk.Entry(window, background="#cae4ff",
                                 font="TkFixedFont",
                                 foreground="#000000")
        self.name_entry.place(relx=0.435, rely=0.171, height=20, relwidth=0.4)

        # Mobile Number Entry
        self.Label2 = tk.Label(window, background="#f2f3f4",
                              font="-family {Segoe UI} -size 9",
                              text='Mobile Number:')
        self.Label2.place(relx=0.146, rely=0.321, height=21, width=124)

        self.mobile_entry = tk.Entry(window, background="#cae4ff",
                                   font="TkFixedFont",
                                   foreground="#000000")
        self.mobile_entry.place(relx=0.435, rely=0.321, height=20, relwidth=0.4)

        # KYC Entry
        self.Label3 = tk.Label(window, background="#f2f3f4",
                              font="-family {Segoe UI} -size 9",
                              text='KYC Status:')
        self.Label3.place(relx=0.146, rely=0.471, height=21, width=124)

        self.kyc_entry = tk.Entry(window, background="#cae4ff",
                                font="TkFixedFont",
                                foreground="#000000")
        self.kyc_entry.place(relx=0.435, rely=0.471, height=20, relwidth=0.4)

        # Load current data
        self.load_current_data()

        # Update Button
        self.Button1 = tk.Button(window, activebackground="#ececec",
                               activeforeground="#000000",
                               background="#004080",
                               foreground="#ffffff",
                               borderwidth="0",
                               text='Update',
                               command=self.update_profile)
        self.Button1.place(relx=0.56, rely=0.671, height=24, width=67)

        # Back Button
        self.Button2 = tk.Button(window, activebackground="#ececec",
                               activeforeground="#000000",
                               background="#004080",
                               foreground="#ffffff",
                               borderwidth="0",
                               text='Back',
                               command=self.back)
        self.Button2.place(relx=0.268, rely=0.671, height=24, width=67)

    def load_current_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Fetch current data
            cursor.execute("""
                SELECT holder_name, mobile_number, kyc 
                FROM customers 
                WHERE account_number = %s
            """, (customer_accNO,))
            
            data = cursor.fetchone()
            if data:
                self.name_entry.insert(0, data[0] if data[0] else '')
                self.mobile_entry.insert(0, data[1] if data[1] else '')
                self.kyc_entry.insert(0, data[2] if data[2] else '')
            
            cursor.close()
            conn.close()
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to load data: {err}")

    def validate_inputs(self):
        # Validate holder name
        holder_name = self.name_entry.get().strip()
        if holder_name and not holder_name.replace(' ', '').isalpha():
            messagebox.showerror("Error", "Name should contain only letters!")
            return False

        # Validate mobile number
        mobile = self.mobile_entry.get().strip()
        if mobile and (not mobile.isdigit() or len(mobile) != 10):
            messagebox.showerror("Error", "Mobile number should be 10 digits!")
            return False

        return True

    def update_profile(self):
        if not self.validate_inputs():
            return

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Build update query dynamically based on filled fields
            update_parts = []
            values = []

            holder_name = self.name_entry.get().strip()
            mobile = self.mobile_entry.get().strip()
            kyc = self.kyc_entry.get().strip()

            if holder_name:
                update_parts.append("holder_name = %s")
                values.append(holder_name)
            if mobile:
                update_parts.append("mobile_number = %s")
                values.append(mobile)
            if kyc:
                update_parts.append("kyc = %s")
                values.append(kyc)

            if not update_parts:
                messagebox.showwarning("Warning", "No fields to update!")
                return

            # Add account number for WHERE clause
            values.append(customer_accNO)

            # Construct and execute update query
            query = f"""
                UPDATE customers 
                SET {', '.join(update_parts)}
                WHERE account_number = %s
            """

            cursor.execute(query, values)
            conn.commit()

            if cursor.rowcount > 0:
                messagebox.showinfo("Success", "Profile updated successfully!")
                self.master.destroy()
            else:
                messagebox.showwarning("Warning", "No changes were made to the profile")

            cursor.close()
            conn.close()

        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"Failed to update profile: {err}")
            if 'conn' in locals():
                conn.rollback()
        finally:
            if 'conn' in locals():
                if 'cursor' in locals():
                    cursor.close()
                conn.close()

    def back(self):
        self.master.destroy()


# class UpdateProfile:
#     def __init__(self, window=None):
#         self.master = window
#         window.geometry("411x400+519+278")
#         window.minsize(120, 1)
#         window.maxsize(1370, 749)
#         window.resizable(0, 0)
#         window.title("Update Profile")
#         window.configure(background="#f2f3f4")

#         # Name Entry
#         self.Label1 = tk.Label(window, background="#f2f3f4", 
#                               font="-family {Segoe UI} -size 9",
#                               text='Name:')
#         self.Label1.place(relx=0.146, rely=0.171, height=21, width=124)

#         self.name_entry = tk.Entry(window, background="#cae4ff",
#                                  font="TkFixedFont",
#                                  foreground="#000000")
#         self.name_entry.place(relx=0.435, rely=0.171, height=20, relwidth=0.4)

#         # Mobile Number Entry
#         self.Label2 = tk.Label(window, background="#f2f3f4",
#                               font="-family {Segoe UI} -size 9",
#                               text='Mobile Number:')
#         self.Label2.place(relx=0.146, rely=0.321, height=21, width=124)

#         self.mobile_entry = tk.Entry(window, background="#cae4ff",
#                                    font="TkFixedFont",
#                                    foreground="#000000")
#         self.mobile_entry.place(relx=0.435, rely=0.321, height=20, relwidth=0.4)

#         # Nationality Entry
#         self.Label3 = tk.Label(window, background="#f2f3f4",
#                               font="-family {Segoe UI} -size 9",
#                               text='Nationality:')
#         self.Label3.place(relx=0.146, rely=0.471, height=21, width=124)

#         self.nationality_entry = tk.Entry(window, background="#cae4ff",
#                                         font="TkFixedFont",
#                                         foreground="#000000")
#         self.nationality_entry.place(relx=0.435, rely=0.471, height=20, relwidth=0.4)

#         # Update Button
#         self.Button1 = tk.Button(window, activebackground="#ececec",
#                                activeforeground="#000000",
#                                background="#004080",
#                                foreground="#ffffff",
#                                borderwidth="0",
#                                text='Update',
#                                command=self.update_profile)
#         self.Button1.place(relx=0.56, rely=0.671, height=24, width=67)

#         # Back Button
#         self.Button2 = tk.Button(window, activebackground="#ececec",
#                                activeforeground="#000000",
#                                background="#004080",
#                                foreground="#ffffff",
#                                borderwidth="0",
#                                text='Back',
#                                command=self.back)
#         self.Button2.place(relx=0.268, rely=0.671, height=24, width=67)

#     def update_profile(self):
#         name = self.name_entry.get().strip()
#         mobile = self.mobile_entry.get().strip()
#         nationality = self.nationality_entry.get().strip()

#         if not any([name, mobile, nationality]):
#             messagebox.showerror("Error", "Please fill at least one field to update")
#             return

#         try:
#             conn = get_db_connection()
#             cursor = conn.cursor()

#             # Build update query dynamically
#             update_parts = []
#             values = []

#             if name:
#                 update_parts.append("holder_name = %s")
#                 values.append(name)
#             if mobile:
#                 update_parts.append("mobile_number = %s")
#                 values.append(mobile)
#             if nationality:
#                 update_parts.append("nationality = %s")
#                 values.append(nationality)

#             values.append(customer_accNO)  # Add account number for WHERE clause

#             query = f"""
#                 UPDATE customers 
#                 SET {', '.join(update_parts)}
#                 WHERE account_number = %s
#             """

#             cursor.execute(query, values)
#             conn.commit()

#             if cursor.rowcount > 0:
#                 messagebox.showinfo("Success", "Profile updated successfully!")
#                 self.master.destroy()
#             else:
#                 messagebox.showwarning("Warning", "No changes were made")

#         except mysql.connector.Error as err:
#             messagebox.showerror("Error", f"Error updating profile: {err}")
#         finally:
#             if 'conn' in locals():
#                 cursor.close()
#                 conn.close()

#     def back(self):
#         self.master.destroy()

class ViewProfile:
    def __init__(self, window=None):
        self.master = window
        window.geometry("411x500+519+278")
        window.minsize(120, 1)
        window.maxsize(1370, 749)
        window.resizable(0, 0)
        window.title("View Profile")
        window.configure(background="#f2f3f4")

        # Create main frame
        self.Frame1 = tk.Frame(window, background="#f2f3f4")
        self.Frame1.place(relx=0.02, rely=0.02, relheight=0.94, relwidth=0.96)

        # Title
        self.Label0 = tk.Label(self.Frame1, background="#f2f3f4",
                              font="-family {Segoe UI} -size 16 -weight bold",
                              text='Profile Details')
        self.Label0.place(relx=0.25, rely=0.05, height=30, width=200)

        # Labels for field names
        labels = [
            ('Account Number:', 0.15),
            ('Name:', 0.23),
            ('Account Type:', 0.31),
            ('Balance:', 0.39),
            ('Mobile Number:', 0.47),
            ('Date of Birth:', 0.55),
            ('Gender:', 0.63),
            ('Nationality:', 0.71),
            ('KYC Status:', 0.79)
        ]

        self.label_widgets = {}
        self.value_labels = {}

        for label_text, rely in labels:
            # Label for field name
            label = tk.Label(self.Frame1, background="#f2f3f4",
                           font="-family {Segoe UI} -size 11",
                           text=label_text)
            label.place(relx=0.1, rely=rely, height=25)
            self.label_widgets[label_text] = label

            # Label for field value
            value_label = tk.Label(self.Frame1, background="#ffffff",
                                 font="-family {Segoe UI} -size 11",
                                 anchor='w')
            value_label.place(relx=0.4, rely=rely, height=25, width=200)
            self.value_labels[label_text] = value_label

        # Back Button
        self.Button1 = tk.Button(self.Frame1,
                               activebackground="#ececec",
                               activeforeground="#000000",
                               background="#004080",
                               foreground="#ffffff",
                               borderwidth="0",
                               text='Back',
                               command=self.back)
        self.Button1.place(relx=0.4, rely=0.88, height=30, width=80)

        # Load profile data
        self.load_profile_data()

    def load_profile_data(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT account_number, holder_name, account_type, balance,
                       mobile_number, date_of_birth, gender, nationality, kyc
                FROM customers 
                WHERE account_number = %s
            """, (customer_accNO,))
            
            data = cursor.fetchone()
            if data:
                # Update value labels with fetched data
                self.value_labels['Account Number:'].config(text=data['account_number'])
                self.value_labels['Name:'].config(text=data['holder_name'])
                self.value_labels['Account Type:'].config(text=data['account_type'])
                self.value_labels['Balance:'].config(text=f"₹ {data['balance']:.2f}")
                self.value_labels['Mobile Number:'].config(text=data['mobile_number'])
                self.value_labels['Date of Birth:'].config(text=data['date_of_birth'])
                self.value_labels['Gender:'].config(text=data['gender'])
                self.value_labels['Nationality:'].config(text=data['nationality'])
                self.value_labels['KYC Status:'].config(text=data['kyc'])
            else:
                messagebox.showerror("Error", "Profile not found!")
                self.master.destroy()
                
        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"Error loading profile: {err}")
            self.master.destroy()
        finally:
            if 'conn' in locals():
                cursor.close()
                conn.close()

    def back(self):
        self.master.destroy()

class TransactionHistory:
    def __init__(self, window=None):
        print("Initializing Transaction History Window")  # Debug print
        self.master = window
        window.geometry("800x600+300+150")
        window.minsize(120, 1)
        window.maxsize(1370, 749)
        window.resizable(0, 0)
        window.title("Transaction History")
        window.configure(background="#f2f3f4")

        # Create main frame
        self.Frame1 = tk.Frame(window, background="#ffffff")
        self.Frame1.place(relx=0.02, rely=0.02, relheight=0.94, relwidth=0.96)

        # Title
        self.Label0 = tk.Label(self.Frame1, background="#ffffff",
                              font="-family {Segoe UI} -size 16 -weight bold",
                              text='Transaction History')
        self.Label0.place(relx=0.35, rely=0.02, height=30, width=250)

        # Create Treeview for transactions
        self.tree = ttk.Treeview(self.Frame1, 
                                columns=("Date", "Type", "Amount", "Balance"), 
                                show='headings')
        
        # Define columns
        self.tree.heading("Date", text="Date & Time")
        self.tree.heading("Type", text="Transaction Type")
        self.tree.heading("Amount", text="Amount")
        self.tree.heading("Balance", text="Balance")

        # Set column widths
        self.tree.column("Date", width=150)
        self.tree.column("Type", width=150)
        self.tree.column("Amount", width=150)
        self.tree.column("Balance", width=150)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.Frame1, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Place the treeview and scrollbar
        self.tree.place(relx=0.02, rely=0.1, relheight=0.75, relwidth=0.94)
        scrollbar.place(relx=0.96, rely=0.1, relheight=0.75)

        # Back Button
        self.Button1 = tk.Button(self.Frame1,
                               activebackground="#ececec",
                               activeforeground="#000000",
                               background="#004080",
                               foreground="#ffffff",
                               borderwidth="0",
                               text='Back',
                               command=self.back)
        self.Button1.place(relx=0.4, rely=0.9, height=30, width=80)

        print(f"Current customer_accNO: {customer_accNO}")  # Debug print
        # Load transaction data
        self.load_transactions()

    def load_transactions(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            print(f"Fetching transactions for account: {customer_accNO}")  # Debug print
            
            # Execute query to get transactions
            query = """
                SELECT transaction_date, transaction_type, amount, balance
                FROM transactions 
                WHERE account_number = %s
                ORDER BY transaction_date DESC
            """
            print(f"Executing query: {query}")  # Debug print
            cursor.execute(query, (customer_accNO,))
            
            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Insert new data
            transactions = cursor.fetchall()
            print(f"Found {len(transactions)} transactions")  # Debug print
            
            for transaction in transactions:
                print(f"Processing transaction: {transaction}")  # Debug print
                # Format amount with ₹ symbol and 2 decimal places
                amount = f"₹ {float(transaction['amount']):.2f}"
                balance = f"₹ {float(transaction['balance']):.2f}"
                
                # Add + sign for deposits
                if transaction['transaction_type'].lower() == 'deposit':
                    amount = f"+{amount}"
                elif transaction['transaction_type'].lower() == 'withdrawal':
                    amount = f"-{amount}"

                self.tree.insert("", "end", values=(
                    transaction['transaction_date'].strftime('%Y-%m-%d %H:%M:%S'),
                    transaction['transaction_type'],
                    amount,
                    balance
                ))
                
        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"Error loading transactions: {err}")
            print(f"Database error: {err}")  # Debug print
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")
            print(f"Unexpected error: {str(e)}")  # Debug print
        finally:
            if 'conn' in locals():
                cursor.close()
                conn.close()

    def back(self):
        self.master.destroy()





# Tkinter GUI code starts :  
class welcomeScreen:
    def __init__(self, window=None):
        self.master = window
        window.geometry("600x450+383+106")
        window.minsize(120, 1)
        window.maxsize(1370, 749)
        window.resizable(0, 0)
        window.title("Welcome to New BANK")
        p1 = PhotoImage(file='./images/bank1.png')
        window.iconphoto(True, p1)
        window.configure(background="#023047")
        window.configure(cursor="arrow")

        self.Canvas1 = tk.Canvas(window, background="#ffff00", borderwidth="0", insertbackground="black",
                                 relief="ridge",
                                 selectbackground="blue", selectforeground="white")
        self.Canvas1.place(relx=0.190, rely=0.228, relheight=0.496, relwidth=0.622)

        self.Button1 = tk.Button(self.Canvas1, command=self.selectEmployee, activebackground="#ececec",
                                 activeforeground="#000000", background="#023047", disabledforeground="#a3a3a3",
                                 foreground="#fbfbfb", borderwidth="0", highlightbackground="#d9d9d9",
                                 highlightcolor="black", pady="0",
                                 text='''EMPLOYEE''')
        self.Button1.configure(font="-family {Segoe UI} -size 10 -weight bold")
        self.Button1.place(relx=0.161, rely=0.583, height=24, width=87)

        self.Button2 = tk.Button(self.Canvas1, command=self.selectCustomer, activebackground="#ececec",
                                 activeforeground="#000000", background="#023047", disabledforeground="#a3a3a3",
                                 foreground="#f9f9f9", borderwidth="0", highlightbackground="#d9d9d9",
                                 highlightcolor="black", pady="0",
                                 text='''CUSTOMER''')
        self.Button2.configure(font="-family {Segoe UI} -size 10 -weight bold")
        self.Button2.place(relx=0.617, rely=0.583, height=24, width=87)

        self.Label1 = tk.Label(self.Canvas1, background="#ffff00", disabledforeground="#a3a3a3",
                               font="-family {Segoe UI} -size 13 -weight bold", foreground="#000000",
                               text='''Please select your role''')
        self.Label1.place(relx=0.241, rely=0.224, height=31, width=194)

    def selectEmployee(self):
        self.master.withdraw()
        adminLogin(Toplevel(self.master))

    def selectCustomer(self):
        self.master.withdraw()
        CustomerLogin(Toplevel(self.master))


class Error:
    def __init__(self, window=None):
        global master
        master = window
        window.geometry("411x117+485+248")
        window.minsize(120, 1)
        window.maxsize(1370, 749)
        window.resizable(0, 0)
        window.title("Error")
        window.configure(background="#f2f3f4")

        global Label2

        self.Button1 = tk.Button(window, background="#d3d8dc", borderwidth="1", disabledforeground="#a3a3a3",
                                 font="-family {Segoe UI} -size 9", foreground="#000000", highlightbackground="#d9d9d9",
                                 highlightcolor="black", pady="0", text='''OK''', command=self.goback)
        self.Button1.place(relx=0.779, rely=0.598, height=24, width=67)

        global _img0
        _img0 = tk.PhotoImage(file="./images/error_image.png")
        self.Label1 = tk.Label(window, background="#f2f3f4", disabledforeground="#a3a3a3", foreground="#000000",
                               image=_img0, text='''Label''')
        self.Label1.place(relx=0.024, rely=0.0, height=81, width=84)

    def setMessage(self, message_shown):
        Label2 = tk.Label(master, background="#f2f3f4", disabledforeground="#a3a3a3",
                          font="-family {Segoe UI} -size 16", foreground="#000000", highlightcolor="#646464646464",
                          text=message_shown)
        Label2.place(relx=0.210, rely=0.171, height=41, width=214)

    def goback(self):
        master.withdraw()


class adminLogin:
    def __init__(self, window=None):
        self.master = window
        window.geometry("743x494+338+92")
        window.minsize(120, 1)
        window.maxsize(1370, 749)
        window.resizable(0, 0)
        window.title("Admin")
        window.configure(background="#ffff00")

        global Canvas1
        Canvas1 = tk.Canvas(window, background="#ffffff", insertbackground="black", relief="ridge",
                            selectbackground="blue", selectforeground="white")
        Canvas1.place(relx=0.108, rely=0.142, relheight=0.715, relwidth=0.798)

        self.Label1 = tk.Label(Canvas1, background="#ffffff", disabledforeground="#a3a3a3",
                               font="-family {Segoe UI} -size 14 -weight bold", foreground="#00254a",
                               text="Admin Login")
        self.Label1.place(relx=0.135, rely=0.142, height=41, width=154)

        global Label2
        Label2 = tk.Label(Canvas1, background="#ffffff", disabledforeground="#a3a3a3", foreground="#000000")
        Label2.place(relx=0.067, rely=0.283, height=181, width=233)
        global _img0
        _img0 = tk.PhotoImage(file="./images/adminLogin1.png")
        Label2.configure(image=_img0)

        self.Entry1 = tk.Entry(Canvas1, background="#e2e2e2", borderwidth="2", disabledforeground="#a3a3a3",
                               font="TkFixedFont", foreground="#000000", highlightbackground="#b6b6b6",
                               highlightcolor="#004080", insertbackground="black")
        self.Entry1.place(relx=0.607, rely=0.453, height=20, relwidth=0.26)

        self.Entry1_1 = tk.Entry(Canvas1, show='*', background="#e2e2e2", borderwidth="2",
                                 disabledforeground="#a3a3a3", font="TkFixedFont", foreground="#000000",
                                 highlightbackground="#d9d9d9", highlightcolor="#004080", insertbackground="black",
                                 selectbackground="blue", selectforeground="white")
        self.Entry1_1.place(relx=0.607, rely=0.623, height=20, relwidth=0.26)

        self.Label3 = tk.Label(Canvas1, background="#ffffff", disabledforeground="#a3a3a3", foreground="#000000")
        self.Label3.place(relx=0.556, rely=0.453, height=21, width=34)
        global _img1
        _img1 = tk.PhotoImage(file="./images/user1.png")
        self.Label3.configure(image=_img1)

        self.Label4 = tk.Label(Canvas1, background="#ffffff", disabledforeground="#a3a3a3", foreground="#000000")
        self.Label4.place(relx=0.556, rely=0.623, height=21, width=34)
        global _img2
        _img2 = tk.PhotoImage(file="./images/lock1.png")
        self.Label4.configure(image=_img2)

        self.Label5 = tk.Label(Canvas1, background="#ffffff", disabledforeground="#a3a3a3", foreground="#000000")
        self.Label5.place(relx=0.670, rely=0.142, height=71, width=74)
        global _img3
        _img3 = tk.PhotoImage(file="./images/bank1.png")
        self.Label5.configure(image=_img3)

        self.Button = tk.Button(Canvas1, text="Login", borderwidth="0", width=10, background="#ffff00",
                                foreground="#00254a",
                                font="-family {Segoe UI} -size 10 -weight bold",
                                command=lambda: self.login(self.Entry1.get(), self.Entry1_1.get()))
        self.Button.place(relx=0.765, rely=0.755)

        self.Button_back = tk.Button(Canvas1, text="Back", borderwidth="0", width=10, background="#ffff00",
                                     foreground="#00254a",
                                     font="-family {Segoe UI} -size 10 -weight bold",
                                     command=self.back)
        self.Button_back.place(relx=0.545, rely=0.755)

        global admin_img
        admin_img = tk.PhotoImage(file="./images/adminLogin1.png")

    def back(self):
        self.master.withdraw()
        welcomeScreen(Toplevel(self.master))

    @staticmethod
    def setImg():
        Label2 = tk.Label(Canvas1, background="#ffffff", disabledforeground="#a3a3a3", foreground="#000000")
        Label2.place(relx=0.067, rely=0.283, height=181, width=233)
        Label2.configure(image=admin_img)

    def login(self, admin_id, admin_password):
        global admin_idNO
        admin_idNO = admin_id
        if check_credentials(admin_id, admin_password, 1, True):
            self.master.withdraw()
            adminMenu(Toplevel(self.master))
        else:
            Error(Toplevel(self.master))
            Error.setMessage(self, message_shown="Invalid Credentials!")
            self.setImg()


class CustomerLogin:
    def __init__(self, window=None):
        self.master = window
        window.geometry("743x494+338+92")
        window.minsize(120, 1)
        window.maxsize(1370, 749)
        window.resizable(0, 0)
        window.title("Customer")
        window.configure(background="#00254a")

        global Canvas1
        Canvas1 = tk.Canvas(window, background="#ffffff", insertbackground="black", relief="ridge",
                            selectbackground="blue", selectforeground="white")
        Canvas1.place(relx=0.108, rely=0.142, relheight=0.715, relwidth=0.798)

        Label1 = tk.Label(Canvas1, background="#ffffff", disabledforeground="#a3a3a3",
                          font="-family {Segoe UI} -size 14 -weight bold", foreground="#00254a",
                          text="Customer Login")
        Label1.place(relx=0.135, rely=0.142, height=41, width=154)

        global Label2
        Label2 = tk.Label(Canvas1, background="#ffffff", disabledforeground="#a3a3a3", foreground="#000000")
        Label2.place(relx=0.067, rely=0.283, height=181, width=233)
        global _img0
        _img0 = tk.PhotoImage(file="./images/customer.png")
        Label2.configure(image=_img0)

        self.Entry1 = tk.Entry(Canvas1, background="#e2e2e2", borderwidth="2", disabledforeground="#a3a3a3",
                               font="TkFixedFont", foreground="#000000", highlightbackground="#b6b6b6",
                               highlightcolor="#004080", insertbackground="black")
        self.Entry1.place(relx=0.607, rely=0.453, height=20, relwidth=0.26)

        self.Entry1_1 = tk.Entry(Canvas1, show='*', background="#e2e2e2", borderwidth="2",
                                 disabledforeground="#a3a3a3", font="TkFixedFont", foreground="#000000",
                                 highlightbackground="#d9d9d9", highlightcolor="#004080", insertbackground="black",
                                 selectbackground="blue", selectforeground="white")
        self.Entry1_1.place(relx=0.607, rely=0.623, height=20, relwidth=0.26)

        self.Label3 = tk.Label(Canvas1, background="#ffffff", disabledforeground="#a3a3a3", foreground="#000000")
        self.Label3.place(relx=0.556, rely=0.453, height=21, width=34)

        global _img1
        _img1 = tk.PhotoImage(file="./images/user1.png")
        self.Label3.configure(image=_img1)

        self.Label4 = tk.Label(Canvas1)
        self.Label4.place(relx=0.556, rely=0.623, height=21, width=34)
        global _img2
        _img2 = tk.PhotoImage(file="./images/lock1.png")
        self.Label4.configure(image=_img2, background="#ffffff")

        self.Label5 = tk.Label(Canvas1, background="#ffffff", disabledforeground="#a3a3a3", foreground="#000000")
        self.Label5.place(relx=0.670, rely=0.142, height=71, width=74)
        global _img3
        _img3 = tk.PhotoImage(file="./images/bank1.png")
        self.Label5.configure(image=_img3)

        self.Button = tk.Button(Canvas1, text="Login", borderwidth="0", width=10, background="#00254a",
                                foreground="#ffffff",
                                font="-family {Segoe UI} -size 10 -weight bold",
                                command=lambda: self.login(self.Entry1.get(), self.Entry1_1.get()))
        self.Button.place(relx=0.765, rely=0.755)

        self.Button_back = tk.Button(Canvas1, text="Back", borderwidth="0", width=10, background="#00254a",
                                     foreground="#ffffff",
                                     font="-family {Segoe UI} -size 10 -weight bold",
                                     command=self.back)
        self.Button_back.place(relx=0.545, rely=0.755)

        global customer_img
        customer_img = tk.PhotoImage(file="./images/customer.png")

    def back(self):
        self.master.withdraw()
        welcomeScreen(Toplevel(self.master))

    @staticmethod
    def setImg():
        settingIMG = tk.Label(Canvas1, background="#ffffff", disabledforeground="#a3a3a3", foreground="#000000")
        settingIMG.place(relx=0.067, rely=0.283, height=181, width=233)
        settingIMG.configure(image=customer_img)

    def login(self, customer_account_number, customer_PIN):
        if check_credentials(customer_account_number, customer_PIN, 2, False):
            global customer_accNO
            customer_accNO = str(customer_account_number)
            self.master.withdraw()
            customerMenu(Toplevel(self.master))
        else:
            Error(Toplevel(self.master))
            Error.setMessage(self, message_shown="Invalid Credentials!")
            self.setImg()


class adminMenu:
    def __init__(self, window=None):
        self.master = window
        window.geometry("743x494+329+153")
        window.minsize(120, 1)
        window.maxsize(1370, 749)
        window.resizable(0, 0)
        window.title("Admin Section")
        window.configure(background="#ffff00")

        self.Labelframe1 = tk.LabelFrame(window, relief='groove', font="-family {Segoe UI} -size 13 -weight bold",
                                         foreground="#001c37", text="Select your option", background="#fffffe")
        self.Labelframe1.place(relx=0.081, rely=0.081, relheight=0.415, relwidth=0.848)

        self.Button1 = tk.Button(self.Labelframe1, activebackground="#ececec", activeforeground="#000000",
                                 background="#00254a", borderwidth="0", disabledforeground="#a3a3a3",
                                 font="-family {Segoe UI} -size 11", foreground="#fffffe",
                                 highlightbackground="#d9d9d9", highlightcolor="black", pady="0",
                                 text="Close bank account", command=self.closeAccount)
        self.Button1.place(relx=0.667, rely=0.195, height=34, width=181, bordermode='ignore')

        self.Button2 = tk.Button(self.Labelframe1, activebackground="#ececec", activeforeground="#000000",
                                 background="#00254a", borderwidth="0", disabledforeground="#a3a3a3",
                                 font="-family {Segoe UI} -size 11", foreground="#fffffe",
                                 highlightbackground="#d9d9d9", highlightcolor="black", pady="0",
                                 text="Create bank account", command=self.createCustaccount)
        self.Button2.place(relx=0.04, rely=0.195, height=34, width=181, bordermode='ignore')

        self.Button3 = tk.Button(self.Labelframe1, activebackground="#ececec", activeforeground="#000000",
                                 background="#00254a", borderwidth="0", disabledforeground="#a3a3a3",
                                 font="-family {Segoe UI} -size 11", foreground="#fffffe",
                                 highlightbackground="#d9d9d9", highlightcolor="black", pady="0", text="Exit",
                                 command=self.exit)
        self.Button3.place(relx=0.667, rely=0.683, height=34, width=181, bordermode='ignore')

        self.Button4 = tk.Button(self.Labelframe1, activebackground="#ececec", activeforeground="#000000",
                                 background="#00254a", borderwidth="0", disabledforeground="#a3a3a3",
                                 font="-family {Segoe UI} -size 11", foreground="#fffffe",
                                 highlightbackground="#d9d9d9", highlightcolor="black", pady="0",
                                 text="Create admin account", command=self.createAdmin)
        self.Button4.place(relx=0.04, rely=0.439, height=34, width=181, bordermode='ignore')

        self.Button5 = tk.Button(self.Labelframe1, activebackground="#ececec", activeforeground="#000000",
                                 background="#00254a", borderwidth="0", disabledforeground="#a3a3a3",
                                 font="-family {Segoe UI} -size 11", foreground="#fffffe",
                                 highlightbackground="#d9d9d9", highlightcolor="black", pady="0",
                                 text="Close admin account", command=self.deleteAdmin)
        self.Button5.place(relx=0.667, rely=0.439, height=34, width=181, bordermode='ignore')

        self.Button6 = tk.Button(self.Labelframe1, activebackground="#ececec", activeforeground="#000000",
                                 background="#00254a", foreground="#fffffe", borderwidth="0",
                                 disabledforeground="#a3a3a3", font="-family {Segoe UI} -size 11",
                                 highlightbackground="#d9d9d9", highlightcolor="black", pady="0",
                                 text="Check account summary", command=self.showAccountSummary)
        self.Button6.place(relx=0.04, rely=0.683, height=34, width=181, bordermode='ignore')

        global Frame1
        Frame1 = tk.Frame(window, relief='groove', borderwidth="2", background="#fffffe")
        Frame1.place(relx=0.081, rely=0.547, relheight=0.415, relwidth=0.848)

    def closeAccount(self):
        CloseAccountByAdmin(Toplevel(self.master))

    def createCustaccount(self):
        createCustomerAccount(Toplevel(self.master))

    def createAdmin(self):
        createAdmin(Toplevel(self.master))

    def deleteAdmin(self):
        deleteAdmin(Toplevel(self.master))

    def showAccountSummary(self):
        checkAccountSummary(Toplevel(self.master))

    def printAccountSummary(identity):
        # clearing the frame
        for widget in Frame1.winfo_children():
            widget.destroy()
        # getting output_message and displaying it in the frame
        output = display_account_summary(identity, 1)
        output_message = Label(Frame1, text=output, background="#fffffe")
        output_message.pack(pady=20)

    def printMessage_outside(output):
        # clearing the frame
        for widget in Frame1.winfo_children():
            widget.destroy()
        # getting output_message and displaying it in the frame
        output_message = Label(Frame1, text=output, background="#fffffe")
        output_message.pack(pady=20)

    def exit(self):
        self.master.withdraw()
        adminLogin(Toplevel(self.master))


class CloseAccountByAdmin:
    def __init__(self, window=None):
        self.master = window
        window.geometry("411x117+498+261")
        window.minsize(120, 1)
        window.maxsize(1370, 749)
        window.resizable(0, 0)
        window.title("Close customer account")
        window.configure(background="#f2f3f4")

        self.Label1 = tk.Label(window, background="#f2f3f4", disabledforeground="#a3a3a3",
                               text='''Enter account number:''')
        self.Label1.place(relx=0.232, rely=0.220, height=20, width=120)

        self.Entry1 = tk.Entry(window, background="#cae4ff", disabledforeground="#a3a3a3", font="TkFixedFont",
                               foreground="#000000", insertbackground="black")
        self.Entry1.place(relx=0.536, rely=0.220, height=20, relwidth=0.232)

        self.Button1 = tk.Button(window, activebackground="#ececec", activeforeground="#000000", borderwidth="0",
                                 background="#004080", disabledforeground="#a3a3a3", foreground="#ffffff",
                                 highlightbackground="#d9d9d9", highlightcolor="black", pady="0", text="Back",
                                 command=self.back)
        self.Button1.place(relx=0.230, rely=0.598, height=24, width=67)

        self.Button2 = tk.Button(window, activebackground="#ececec", activeforeground="#000000", background="#004080",
                                 borderwidth="0", disabledforeground="#a3a3a3", foreground="#ffffff",
                                 highlightbackground="#d9d9d9", highlightcolor="black", pady="0", text="Proceed",
                                 command=lambda: self.submit(self.Entry1.get()))
        self.Button2.place(relx=0.598, rely=0.598, height=24, width=67)

    def back(self):
        self.master.withdraw()
    
    def submit(self, account_number):
        try:
            if not account_number:
                messagebox.showerror("Error", "Please enter an account number")
                return
                
            output = transaction(account_number, Decimal('0'), 2)  # 2 for check balance
            if output.startswith("Current balance"):
                messagebox.showinfo("Balance", output)
                self.master.withdraw()
            else:
                messagebox.showerror("Error", output)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    

class createCustomerAccount:
    def __init__(self, window=None):
        self.master = window
        window.geometry("411x403+437+152")
        window.minsize(120, 1)
        window.maxsize(1370, 749)
        window.resizable(0, 0)
        window.title("Create account")
        window.configure(background="#f2f3f4")
        window.configure(highlightbackground="#d9d9d9")
        window.configure(highlightcolor="black")

        self.Entry1 = tk.Entry(window, background="#cae4ff", disabledforeground="#a3a3a3", font="TkFixedFont",
                               foreground="#000000", highlightbackground="#d9d9d9", highlightcolor="black",
                               insertbackground="black", selectbackground="blue", selectforeground="white")
        self.Entry1.place(relx=0.511, rely=0.027, height=20, relwidth=0.302)

        self.Label1 = tk.Label(window, activebackground="#f9f9f9", activeforeground="black", background="#f2f3f4",
                               disabledforeground="#a3a3a3", foreground="#000000", highlightbackground="#d9d9d9",
                               highlightcolor="black", text='''Account number:''')
        self.Label1.place(relx=0.219, rely=0.025, height=26, width=120)

        self.Label2 = tk.Label(window, activebackground="#f9f9f9", activeforeground="black", background="#f2f3f4",
                               disabledforeground="#a3a3a3", foreground="#000000", highlightbackground="#d9d9d9",
                               highlightcolor="black", text='''Full name:''')
        self.Label2.place(relx=0.316, rely=0.099, height=27, width=75)

        self.Entry2 = tk.Entry(window, background="#cae4ff", disabledforeground="#a3a3a3",
                               font="TkFixedFont", foreground="#000000", highlightbackground="#d9d9d9",
                               highlightcolor="black", insertbackground="black", selectbackground="blue",
                               selectforeground="white")
        self.Entry2.place(relx=0.511, rely=0.099, height=20, relwidth=0.302)

        self.Label3 = tk.Label(window, activebackground="#f9f9f9", activeforeground="black", background="#f2f3f4",
                               disabledforeground="#a3a3a3", foreground="#000000", highlightbackground="#d9d9d9",
                               highlightcolor="black", text='''Account type:''')
        self.Label3.place(relx=0.287, rely=0.169, height=26, width=83)

        global acc_type
        acc_type = StringVar()

        self.Radiobutton1 = tk.Radiobutton(window, activebackground="#ececec", activeforeground="#000000",
                                           background="#f2f3f4", disabledforeground="#a3a3a3", foreground="#000000",
                                           highlightbackground="#d9d9d9", highlightcolor="black", justify='left',
                                           text='''Savings''', variable=acc_type, value="Savings")
        self.Radiobutton1.place(relx=0.511, rely=0.174, relheight=0.057, relwidth=0.151)

        self.Radiobutton1_1 = tk.Radiobutton(window, activebackground="#ececec", activeforeground="#000000",
                                             background="#f2f3f4", disabledforeground="#a3a3a3", foreground="#000000",
                                             highlightbackground="#d9d9d9", highlightcolor="black", justify='left',
                                             text='''Current''', variable=acc_type, value="Current")
        self.Radiobutton1_1.place(relx=0.706, rely=0.174, relheight=0.057, relwidth=0.175)

        self.Radiobutton1.deselect()
        self.Radiobutton1_1.deselect()

        self.Label5 = tk.Label(window, activebackground="#f9f9f9", activeforeground="black", background="#f2f3f4",
                               disabledforeground="#a3a3a3", foreground="#000000",
                               highlightcolor="black", text='''Mobile number:''')
        self.Label5.place(relx=0.268, rely=0.323, height=22, width=85)

        self.Label4 = tk.Label(window, activebackground="#f9f9f9", activeforeground="black", background="#f2f3f4",
                               disabledforeground="#a3a3a3", foreground="#000000",
                               highlightcolor="black", text='''Birth date (DD/MM/YYYY):''')
        self.Label4.place(relx=0.090, rely=0.238, height=27, width=175)

        self.Entry5 = tk.Entry(window, background="#cae4ff", disabledforeground="#a3a3a3", font="TkFixedFont",
                               foreground="#000000", highlightbackground="#d9d9d9", highlightcolor="black",
                               insertbackground="black", selectbackground="blue", selectforeground="white")
        self.Entry5.place(relx=0.511, rely=0.323, height=20, relwidth=0.302)

        self.Entry4 = tk.Entry(window, background="#cae4ff", disabledforeground="#a3a3a3", font="TkFixedFont",
                               foreground="#000000", highlightbackground="#d9d9d9", highlightcolor="black",
                               insertbackground="black", selectbackground="blue", selectforeground="white")
        self.Entry4.place(relx=0.511, rely=0.248, height=20, relwidth=0.302)

        self.Label6 = tk.Label(window, activebackground="#f9f9f9", activeforeground="black", background="#f2f3f4",
                               disabledforeground="#a3a3a3", foreground="#000000",
                               highlightcolor="black", text='''Gender:''')
        self.Label6.place(relx=0.345, rely=0.402, height=15, width=65)

        global gender
        gender = StringVar()

        self.Radiobutton3 = tk.Radiobutton(window, activebackground="#ececec", activeforeground="#000000",
                                           background="#f2f3f4", disabledforeground="#a3a3a3", foreground="#000000",
                                           highlightcolor="black", justify='left',
                                           text='''Male''', variable=gender, value="Male")
        self.Radiobutton3.place(relx=0.481, rely=0.397, relheight=0.055, relwidth=0.175)

        self.Radiobutton4 = tk.Radiobutton(window, activebackground="#ececec", activeforeground="#000000",
                                           background="#f2f3f4", disabledforeground="#a3a3a3", foreground="#000000",
                                           highlightbackground="#d9d9d9", highlightcolor="black", justify='left',
                                           text='''Female''', variable=gender, value="Female")
        self.Radiobutton4.place(relx=0.706, rely=0.397, relheight=0.055, relwidth=0.175)

        self.Radiobutton3.deselect()
        self.Radiobutton4.deselect()

        self.Label7 = tk.Label(window, activebackground="#f9f9f9", activeforeground="black", background="#f2f3f4",
                               disabledforeground="#a3a3a3", foreground="#000000", highlightbackground="#d9d9d9",
                               highlightcolor="black", text='''Nationality:''')
        self.Label7.place(relx=0.309, rely=0.471, height=21, width=75)

        self.Entry7 = tk.Entry(window, background="#cae4ff", disabledforeground="#a3a3a3",
                               font="TkFixedFont", foreground="#000000", highlightbackground="#d9d9d9",
                               highlightcolor="black", insertbackground="black", selectbackground="blue",
                               selectforeground="white")
        self.Entry7.place(relx=0.511, rely=0.471, height=20, relwidth=0.302)

        self.Entry9 = tk.Entry(window, show="*", background="#cae4ff", disabledforeground="#a3a3a3", font="TkFixedFont",
                               foreground="#000000", highlightbackground="#d9d9d9", highlightcolor="black",
                               insertbackground="black", selectbackground="blue", selectforeground="white")
        self.Entry9.place(relx=0.511, rely=0.623, height=20, relwidth=0.302)

        self.Entry10 = tk.Entry(window, show="*", background="#cae4ff", disabledforeground="#a3a3a3",
                                font="TkFixedFont",
                                foreground="#000000", highlightbackground="#d9d9d9", highlightcolor="black",
                                insertbackground="black", selectbackground="blue", selectforeground="white")
        self.Entry10.place(relx=0.511, rely=0.7, height=20, relwidth=0.302)

        self.Entry11 = tk.Entry(window, background="#cae4ff", disabledforeground="#a3a3a3", font="TkFixedFont",
                                foreground="#000000", highlightbackground="#d9d9d9", highlightcolor="black",
                                insertbackground="black", selectbackground="blue", selectforeground="white")
        self.Entry11.place(relx=0.511, rely=0.777, height=20, relwidth=0.302)

        self.Label9 = tk.Label(window, activebackground="#f9f9f9", activeforeground="black", background="#f2f3f4",
                               disabledforeground="#a3a3a3", foreground="#000000", highlightbackground="#d9d9d9",
                               highlightcolor="black", text='''PIN:''')
        self.Label9.place(relx=0.399, rely=0.62, height=21, width=35)

        self.Label10 = tk.Label(window, activebackground="#f9f9f9", activeforeground="black", background="#f2f3f4",
                                disabledforeground="#a3a3a3", foreground="#000000", highlightbackground="#d9d9d9",
                                highlightcolor="black", text='''Re-enter PIN:''')
        self.Label10.place(relx=0.292, rely=0.695, height=21, width=75)

        self.Label11 = tk.Label(window, activebackground="#f9f9f9", activeforeground="black", background="#f2f3f4",
                                disabledforeground="#a3a3a3", foreground="#000000", highlightbackground="#d9d9d9",
                                highlightcolor="black", text='''Initial balance:''')
        self.Label11.place(relx=0.292, rely=0.779, height=21, width=75)

        self.Button1 = tk.Button(window, activebackground="#ececec", activeforeground="#000000", background="#004080",
                                 borderwidth="0", disabledforeground="#a3a3a3", foreground="#ffffff",
                                 highlightbackground="#d9d9d9", highlightcolor="black", pady="0", text='''Back''',
                                 command=self.back)
        self.Button1.place(relx=0.243, rely=0.893, height=24, width=67)

        self.Button2 = tk.Button(window, activebackground="#ececec", activeforeground="#000000", background="#004080",
                                 borderwidth="0", disabledforeground="#a3a3a3", foreground="#ffffff",
                                 highlightbackground="#d9d9d9", highlightcolor="black", pady="0", text='''Proceed''',
                                 command=lambda: self.create_acc(self.Entry1.get(), self.Entry2.get(), acc_type.get(),
                                                                 self.Entry4.get(), self.Entry5.get(), gender.get(),
                                                                 self.Entry7.get(), self.Entry8.get(),
                                                                 self.Entry9.get(), self.Entry10.get(),
                                                                 self.Entry11.get()))
        self.Button2.place(relx=0.633, rely=0.893, height=24, width=67)

        self.Label8 = tk.Label(window, background="#f2f3f4", disabledforeground="#a3a3a3", foreground="#000000",
                               text='''KYC document type:''')
        self.Label8.place(relx=0.18, rely=0.546, height=24, width=122)

        self.Entry8 = tk.Entry(window, background="#cae4ff", disabledforeground="#a3a3a3", font="TkFixedFont",
                               foreground="#000000", insertbackground="black")
        self.Entry8.place(relx=0.511, rely=0.546, height=20, relwidth=0.302)

    def back(self):
        self.master.withdraw()
    
    def create_acc(self, account_number, name, acc_type, dob, mobile, gender, 
                   nationality, kyc, pin, confirm_pin, initial_balance):
        if pin != confirm_pin:
            messagebox.showerror("Error", "PINs do not match!")
            return
    
        # Convert date format
        try:
            # Assuming dob is in DD/MM/YYYY format
            day, month, year = dob.split('/')
            formatted_dob = f"{year}-{month}-{day}"  # Convert to YYYY-MM-DD
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Please use DD/MM/YYYY")
            return
    
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Check if account number already exists
            if not is_valid(account_number):
                messagebox.showerror("Error", "Account number already exists")
                return
                
            # Insert new customer with formatted date
            cursor.execute("""
                INSERT INTO customers 
                (account_number, pin, creation_date, holder_name, account_type, 
                 date_of_birth, mobile_number, gender, nationality, kyc, balance)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (account_number, pin, date.today(), name, acc_type,
                  formatted_dob, mobile, gender, nationality, kyc, initial_balance))
            
            conn.commit()
            messagebox.showinfo("Success", "Account created successfully!")
            self.master.withdraw()  # Close the window after successful creation
            
        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"Error creating account: {err}")
        finally:
            cursor.close()
            conn.close()
    


class createAdmin:
    def __init__(self, window=None):
        self.master = window
        window.geometry("411x150+512+237")
        window.minsize(120, 1)
        window.maxsize(1370, 749)
        window.resizable(0, 0)
        window.title("Create admin account")
        window.configure(background="#f2f3f4")

        self.Label1 = tk.Label(window, background="#f2f3f4", disabledforeground="#a3a3a3", foreground="#000000",
                               text='''Enter admin ID:''')
        self.Label1.place(relx=0.219, rely=0.067, height=27, width=104)

        self.Label2 = tk.Label(window, background="#f2f3f4", disabledforeground="#a3a3a3", foreground="#000000",
                               text='''Enter password:''')
        self.Label2.place(relx=0.219, rely=0.267, height=27, width=104)

        self.Entry1 = tk.Entry(window, background="#cae4ff", disabledforeground="#a3a3a3", font="TkFixedFont",
                               foreground="#000000", insertbackground="black")
        self.Entry1.place(relx=0.487, rely=0.087, height=20, relwidth=0.326)

        self.Entry2 = tk.Entry(window, show="*", background="#cae4ff", disabledforeground="#a3a3a3", font="TkFixedFont",
                               foreground="#000000", insertbackground="black")
        self.Entry2.place(relx=0.487, rely=0.287, height=20, relwidth=0.326)

        self.Label3 = tk.Label(window, activebackground="#f9f9f9", activeforeground="black", background="#f2f3f4",
                               disabledforeground="#a3a3a3", foreground="#000000", highlightbackground="#d9d9d9",
                               highlightcolor="black", text='''Confirm password:''')
        self.Label3.place(relx=0.195, rely=0.467, height=27, width=104)

        self.Entry3 = tk.Entry(window, show="*", background="#cae4ff", disabledforeground="#a3a3a3", font="TkFixedFont",
                               foreground="#000000", insertbackground="black")
        self.Entry3.place(relx=0.487, rely=0.487, height=20, relwidth=0.326)

        self.Button1 = tk.Button(window, activebackground="#ececec", activeforeground="#000000", background="#004080",
                                 borderwidth="0", disabledforeground="#a3a3a3", foreground="#ffffff",
                                 highlightbackground="#d9d9d9", highlightcolor="black", pady="0", text="Proceed",
                                 command=lambda: self.create_admin_account(self.Entry1.get(), self.Entry2.get(),
                                                                           self.Entry3.get()))
        self.Button1.place(relx=0.598, rely=0.733, height=24, width=67)

        self.Button2 = tk.Button(window, activebackground="#ececec", activeforeground="#000000", background="#004080",
                                 borderwidth="0", disabledforeground="#a3a3a3", foreground="#ffffff",
                                 highlightbackground="#d9d9d9", highlightcolor="black", pady="0", text="Back",
                                 command=self.back)
        self.Button2.place(relx=0.230, rely=0.733, height=24, width=67)

    def back(self):
        self.master.withdraw()

    def create_admin_account(self, identity, password, confirm_password):
        if check_credentials(identity, "DO_NOT_CHECK_ADMIN", 1, False):
            Error(Toplevel(self.master))
            Error.setMessage(self, message_shown="ID is unavailable!")
        else:
            if password == confirm_password and len(password) != 0:
                create_admin_account(identity, password)
                self.master.withdraw()
            else:
                Error(Toplevel(self.master))
                if password != confirm_password:
                    Error.setMessage(self, message_shown="Password Mismatch!")
                else:
                    Error.setMessage(self, message_shown="Invalid password!")


class deleteAdmin:
    def __init__(self, window=None):
        self.master = window
        window.geometry("411x117+504+268")
        window.minsize(120, 1)
        window.maxsize(1370, 749)
        window.resizable(0, 0)
        window.title("Delete admin account")
        window.configure(background="#f2f3f4")

        self.Entry1 = tk.Entry(window, background="#cae4ff", disabledforeground="#a3a3a3", font="TkFixedFont",
                               foreground="#000000", insertbackground="black")
        self.Entry1.place(relx=0.487, rely=0.092, height=20, relwidth=0.277)

        self.Label1 = tk.Label(window, background="#f2f3f4", disabledforeground="#a3a3a3", foreground="#000000",
                               text='''Enter admin ID:''')
        self.Label1.place(relx=0.219, rely=0.092, height=21, width=104)

        self.Label2 = tk.Label(window, background="#f2f3f4", disabledforeground="#a3a3a3", foreground="#000000",
                               text='''Enter password:''')
        self.Label2.place(relx=0.209, rely=0.33, height=21, width=109)

        self.Entry1_1 = tk.Entry(window, show="*", background="#cae4ff", disabledforeground="#a3a3a3",
                                 font="TkFixedFont",
                                 foreground="#000000", highlightbackground="#d9d9d9", highlightcolor="black",
                                 insertbackground="black", selectbackground="blue", selectforeground="white")
        self.Entry1_1.place(relx=0.487, rely=0.33, height=20, relwidth=0.277)

        self.Button1 = tk.Button(window, activebackground="#ececec", activeforeground="#000000", background="#004080",
                                 borderwidth="0", disabledforeground="#a3a3a3", foreground="#ffffff",
                                 highlightbackground="#d9d9d9", highlightcolor="black", pady="0", text='''Back''',
                                 command=self.back)
        self.Button1.place(relx=0.243, rely=0.642, height=24, width=67)

        self.Button2 = tk.Button(window, activebackground="#ececec", activeforeground="#000000", background="#004080",
                                 borderwidth="0", disabledforeground="#a3a3a3", foreground="#ffffff",
                                 highlightbackground="#d9d9d9", highlightcolor="black", pady="0", text='''Proceed''',
                                 command=lambda: self.delete_admin(self.Entry1.get(), self.Entry1_1.get()))
        self.Button2.place(relx=0.608, rely=0.642, height=24, width=67)

    def delete_admin(self, admin_id, password):
        if admin_id == "aayush" or admin_id == admin_idNO:
            Error(Toplevel(self.master))
            Error.setMessage(self, message_shown="Operation Denied!")
            return
        if check_credentials(admin_id, password, 1, True):
            delete_admin_account(admin_id)
            self.master.withdraw()
        else:
            Error(Toplevel(self.master))
            Error.setMessage(self, message_shown="Invalid Credentials!")

    def back(self):
        self.master.withdraw()


class customerMenu:
    def __init__(self, window=None):
        self.master = window
        window.geometry("743x494+329+153")
        window.minsize(120, 1)
        window.maxsize(1370, 749)
        window.resizable(0, 0)
        window.title("Customer Section")
        window.configure(background="#00254a")

        self.Labelframe1 = tk.LabelFrame(window, relief='groove', font="-family {Segoe UI} -size 13 -weight bold",
                                         foreground="#000000", text='''Select your option''', background="#fffffe")
        self.Labelframe1.place(relx=0.081, rely=0.081, relheight=0.415, relwidth=0.848)

        self.Button1 = tk.Button(self.Labelframe1, command=self.selectWithdraw, activebackground="#ececec",
                                 activeforeground="#000000", background="#39a9fc", borderwidth="0",
                                 disabledforeground="#a3a3a3", font="-family {Segoe UI} -size 11", foreground="#fffffe",
                                 highlightbackground="#d9d9d9", highlightcolor="black", pady="0", text='''Withdraw''')
        self.Button1.place(relx=0.667, rely=0.195, height=34, width=181, bordermode='ignore')

        self.Button2 = tk.Button(self.Labelframe1, command=self.selectDeposit, activebackground="#ececec",
                                 activeforeground="#000000", background="#39a9fc", borderwidth="0",
                                 disabledforeground="#a3a3a3", font="-family {Segoe UI} -size 11", foreground="#fffffe",
                                 highlightbackground="#d9d9d9", highlightcolor="black", pady="0", text='''Deposit''')
        self.Button2.place(relx=0.04, rely=0.195, height=34, width=181, bordermode='ignore')

        self.Button3 = tk.Button(self.Labelframe1, command=self.exit, activebackground="#ececec",
                                 activeforeground="#000000",
                                 background="#39a9fc",
                                 borderwidth="0", disabledforeground="#a3a3a3", font="-family {Segoe UI} -size 11",
                                 foreground="#fffffe", highlightbackground="#d9d9d9", highlightcolor="black", pady="0",
                                 text='''Exit''')
        self.Button3.place(relx=0.667, rely=0.683, height=34, width=181, bordermode='ignore')

        self.Button4 = tk.Button(self.Labelframe1, command=self.selectChangePIN, activebackground="#ececec",
                                 activeforeground="#000000", background="#39a9fc", borderwidth="0",
                                 disabledforeground="#a3a3a3", font="-family {Segoe UI} -size 11", foreground="#fffffe",
                                 highlightbackground="#d9d9d9", highlightcolor="black", pady="0", text='''Change PIN''')
        self.Button4.place(relx=0.04, rely=0.439, height=34, width=181, bordermode='ignore')

        self.Button5 = tk.Button(self.Labelframe1, command=self.selectCloseAccount, activebackground="#ececec",
                                 activeforeground="#000000", background="#39a9fc", borderwidth="0",
                                 disabledforeground="#a3a3a3", font="-family {Segoe UI} -size 11", foreground="#fffffe",
                                 highlightbackground="#d9d9d9", highlightcolor="black", pady="0",
                                 text='''Close account''')
        self.Button5.place(relx=0.667, rely=0.439, height=34, width=181, bordermode='ignore')

        self.Button6 = tk.Button(self.Labelframe1, activebackground="#ececec", activeforeground="#000000",
                                 background="#39a9fc", borderwidth="0", disabledforeground="#a3a3a3",
                                 font="-family {Segoe UI} -size 11", foreground="#fffffe",
                                 highlightbackground="#d9d9d9", highlightcolor="black", pady="0",
                                 text='''Check your balance''', command=self.checkBalance)
        self.Button6.place(relx=0.04, rely=0.683, height=34, width=181, bordermode='ignore')

        # Add this button with your other buttons in the Labelframe1
        # Update Profile Button (adjusted rely value to create space)
        self.Button7 = tk.Button(self.Labelframe1, command=self.selectUpdateProfile, 
                                activebackground="#ececec",
                                activeforeground="#000000", 
                                background="#39a9fc", 
                                borderwidth="0",
                                disabledforeground="#a3a3a3", 
                                font="-family {Segoe UI} -size 11", 
                                foreground="#fffffe",
                                highlightbackground="#d9d9d9", 
                                highlightcolor="black", 
                                pady="0", 
                                text='Update Profile')
        self.Button7.place(relx=0.353, rely=0.683, height=34, width=181, bordermode='ignore')
        
        # View Profile Button
        self.Button8 = tk.Button(self.Labelframe1, command=self.selectViewProfile,
                                activebackground="#ececec",
                                activeforeground="#000000",
                                background="#39a9fc",
                                borderwidth="0",
                                disabledforeground="#a3a3a3",
                                font="-family {Segoe UI} -size 11",
                                foreground="#fffffe",
                                highlightbackground="#d9d9d9",
                                highlightcolor="black",
                                pady="0",
                                text='View Profile')
        self.Button8.place(relx=0.353, rely=0.2, height=34, width=181, bordermode='ignore')
        
        

        # Add this button with your other buttons in the Labelframe1
        self.Button9 = tk.Button(self.Labelframe1, command=self.selectTransactionHistory,
                                activebackground="#ececec",
                                activeforeground="#000000",
                                background="#39a9fc",
                                borderwidth="0",
                                disabledforeground="#a3a3a3",
                                font="-family {Segoe UI} -size 11",
                                foreground="#fffffe",
                                highlightbackground="#d9d9d9",
                                highlightcolor="black",
                                pady="0",
                                text='Transaction History')
        self.Button9.place(relx=0.353, rely=0.433, height=34, width=181, bordermode='ignore')
        
        
        
        

        global Frame1_1_2
        Frame1_1_2 = tk.Frame(window, relief='groove', borderwidth="2", background="#fffffe")
        Frame1_1_2.place(relx=0.081, rely=0.547, relheight=0.415, relwidth=0.848)

    def selectDeposit(self):
        depositMoney(Toplevel(self.master))

    def selectWithdraw(self):
        withdrawMoney(Toplevel(self.master))

    def selectChangePIN(self):
        changePIN(Toplevel(self.master))

    def selectCloseAccount(self):
        self.master.withdraw()
        closeAccount(Toplevel(self.master))

    # In your customer menu window/class
    def create_customer_menu(account_number):
        # ... (your existing customer menu code)
        
        # Add Update Profile button
        update_profile_btn = Button(
            customer_window,
            text="Update Profile",
            command=lambda: show_update_profile_window(account_number),
            bg="blue",
            fg="white",
            width=20
        )
        update_profile_btn.pack(pady=10)
        
        # ... (rest of your customer menu code)
    

    def exit(self):
        self.master.withdraw()
        CustomerLogin(Toplevel(self.master))

    def checkBalance(self):
        output = display_account_summary(customer_accNO, 2)
        self.printMessage(output)
        print("check balance function called.")

    def printMessage(self, output):
        # clearing the frame
        for widget in Frame1_1_2.winfo_children():
            widget.destroy()
        # getting output_message and displaying it in the frame
        output_message = Label(Frame1_1_2, text=output, background="#fffffe")
        output_message.pack(pady=20)

    def printMessage_outside(output):
        # clearing the frame
        for widget in Frame1_1_2.winfo_children():
            widget.destroy()
        # getting output_message and displaying it in the frame
        output_message = Label(Frame1_1_2, text=output, background="#fffffe")
        output_message.pack(pady=20)

    def selectUpdateProfile(self):
        UpdateProfile(Toplevel(self.master))

    def selectViewProfile(self):
        ViewProfile(Toplevel(self.master))

    def selectTransactionHistory(self):
        TransactionHistory(Toplevel(self.master))
    
    
    


class depositMoney:
    def __init__(self, window=None):
        self.master = window
        window.geometry("411x117+519+278")
        window.minsize(120, 1)
        window.maxsize(1370, 749)
        window.resizable(0, 0)
        window.title("Deposit money")
        p1 = PhotoImage(file='./images/deposit_icon.png')
        window.iconphoto(True, p1)
        window.configure(borderwidth="2")
        window.configure(background="#f2f3f4")

        self.Label1 = tk.Label(window, background="#f2f3f4", disabledforeground="#a3a3a3",
                               font="-family {Segoe UI} -size 9", foreground="#000000", borderwidth="0",
                               text='''Enter amount to deposit :''')
        self.Label1.place(relx=0.146, rely=0.171, height=21, width=164)

        self.Entry1 = tk.Entry(window, background="#cae4ff", disabledforeground="#a3a3a3", font="TkFixedFont",
                               foreground="#000000", insertbackground="black", selectforeground="#ffffffffffff")
        self.Entry1.place(relx=0.535, rely=0.171, height=20, relwidth=0.253)

        self.Button1 = tk.Button(window, activebackground="#ececec", activeforeground="#000000", background="#004080",
                                 disabledforeground="#a3a3a3", borderwidth="0", foreground="#ffffff",
                                 highlightbackground="#000000",
                                 highlightcolor="black", pady="0", text='''Proceed''',
                                 command=lambda: self.submit(self.Entry1.get()))
        self.Button1.place(relx=0.56, rely=0.598, height=24, width=67)

        self.Button2 = tk.Button(window, activebackground="#ececec", activeforeground="#000000", background="#004080",
                                 disabledforeground="#a3a3a3", font="-family {Segoe UI} -size 9", foreground="#ffffff",
                                 highlightbackground="#d9d9d9", borderwidth="0", highlightcolor="black", pady="0",
                                 text='''Back''',
                                 command=self.back)
        self.Button2.place(relx=0.268, rely=0.598, height=24, width=67)

    def submit(self, amount):
        if amount.isnumeric():
            if 25000 >= float(amount) > 0:
                output = transaction(customer_accNO, float(amount), 1)
            else:
                Error(Toplevel(self.master))
                if float(amount) > 25000:
                    Error.setMessage(self, message_shown="Limit exceeded!")
                else:
                    Error.setMessage(self, message_shown="Positive value expected!")
                return
        else:
            Error(Toplevel(self.master))
            Error.setMessage(self, message_shown="Invalid amount!")
            return
        if output == -1:
            Error(Toplevel(self.master))
            Error.setMessage(self, message_shown="Transaction failed!")
            return
        else:
            output = "Amount of rupees " + str(amount) + " deposited successfully.\nUpdated balance : " + str(output)
            customerMenu.printMessage_outside(output)
            self.master.withdraw()

    def back(self):
        self.master.withdraw()


class withdrawMoney:
    def __init__(self, window=None):
        self.master = window
        window.geometry("411x117+519+278")
        window.minsize(120, 1)
        window.maxsize(1370, 749)
        window.resizable(0, 0)
        window.title("Withdraw money")
        p1 = PhotoImage(file='./images/withdraw_icon.png')
        window.iconphoto(True, p1)
        window.configure(borderwidth="2")
        window.configure(background="#f2f3f4")

        self.Label1 = tk.Label(window, background="#f2f3f4", disabledforeground="#a3a3a3",
                               font="-family {Segoe UI} -size 9", foreground="#000000",
                               text='''Enter amount to withdraw :''')
        self.Label1.place(relx=0.146, rely=0.171, height=21, width=164)

        self.Entry1 = tk.Entry(window, background="#cae4ff", disabledforeground="#a3a3a3", font="TkFixedFont",
                               foreground="#000000", insertbackground="black", selectforeground="#ffffffffffff")
        self.Entry1.place(relx=0.535, rely=0.171, height=20, relwidth=0.253)

        self.Button1 = tk.Button(window, activebackground="#ececec", activeforeground="#000000", background="#004080",
                                 disabledforeground="#a3a3a3", borderwidth="0", foreground="#ffffff",
                                 highlightbackground="#000000",
                                 highlightcolor="black", pady="0", text='''Proceed''',
                                 command=lambda: self.submit(self.Entry1.get()))
        self.Button1.place(relx=0.56, rely=0.598, height=24, width=67)

        self.Button2 = tk.Button(window, activebackground="#ececec", activeforeground="#000000", background="#004080",
                                 disabledforeground="#a3a3a3", borderwidth="0", font="-family {Segoe UI} -size 9",
                                 foreground="#ffffff",
                                 highlightbackground="#d9d9d9", highlightcolor="black", pady="0", text='''Back''',
                                 command=self.back)
        self.Button2.place(relx=0.268, rely=0.598, height=24, width=67)

    def submit(self, amount):
        if amount.isnumeric():
            if 25000 >= float(amount) > 0:
                output = transaction(customer_accNO, float(amount), 2)
            else:
                Error(Toplevel(self.master))
                if float(amount) > 25000:
                    Error.setMessage(self, message_shown="Limit exceeded!")
                else:
                    Error.setMessage(self, message_shown="Positive value expected!")
                return
        else:
            Error(Toplevel(self.master))
            Error.setMessage(self, message_shown="Invalid amount!")
            return
        if output == -1:
            Error(Toplevel(self.master))
            Error.setMessage(self, message_shown="Transaction failed!")
            return
        else:
            output = "Amount of rupees " + str(amount) + " withdrawn successfully.\nUpdated balance : " + str(output)
            customerMenu.printMessage_outside(output)
            self.master.withdraw()

    def back(self):
        self.master.withdraw()


class changePIN:
    def __init__(self, window=None):
        self.master = window
        window.geometry("411x111+505+223")
        window.minsize(120, 1)
        window.maxsize(1370, 749)
        window.resizable(0, 0)
        window.title("Change PIN")
        window.configure(background="#f2f3f4")

        self.Label1 = tk.Label(window, background="#f2f3f4", disabledforeground="#a3a3a3", foreground="#000000",
                               text='''Enter new PIN:''')
        self.Label1.place(relx=0.243, rely=0.144, height=21, width=93)

        self.Label2 = tk.Label(window, background="#f2f3f4", disabledforeground="#a3a3a3", foreground="#000000",
                               text='''Confirm PIN:''')
        self.Label2.place(relx=0.268, rely=0.414, height=21, width=82)

        self.Entry1 = tk.Entry(window, show="*", background="#cae4ff", disabledforeground="#a3a3a3", font="TkFixedFont",
                               foreground="#000000", insertbackground="black")
        self.Entry1.place(relx=0.528, rely=0.144, height=20, relwidth=0.229)

        self.Entry2 = tk.Entry(window, show="*", background="#cae4ff", disabledforeground="#a3a3a3", font="TkFixedFont",
                               foreground="#000000", insertbackground="black")
        self.Entry2.place(relx=0.528, rely=0.414, height=20, relwidth=0.229)

        self.Button1 = tk.Button(window, activebackground="#ececec", activeforeground="#000000", background="#004080",
                                 disabledforeground="#a3a3a3", foreground="#ffffff", borderwidth="0",
                                 highlightbackground="#d9d9d9",
                                 highlightcolor="black", pady="0", text='''Proceed''',
                                 command=lambda: self.submit(self.Entry1.get(), self.Entry2.get()))
        self.Button1.place(relx=0.614, rely=0.721, height=24, width=67)

        self.Button2 = tk.Button(window, activebackground="#ececec", activeforeground="#000000", background="#004080",
                                 disabledforeground="#a3a3a3", foreground="#ffffff", borderwidth="0",
                                 highlightbackground="#d9d9d9",
                                 highlightcolor="black", pady="0", text="Back", command=self.back)
        self.Button2.place(relx=0.214, rely=0.721, height=24, width=67)

    def submit(self, new_PIN, confirm_new_PIN):
        if new_PIN == confirm_new_PIN and str(new_PIN).__len__() == 4 and new_PIN.isnumeric():
            change_PIN(customer_accNO, new_PIN)
            self.master.withdraw()
        else:
            Error(Toplevel(self.master))
            if new_PIN != confirm_new_PIN:
                Error.setMessage(self, message_shown="PIN mismatch!")
            elif str(new_PIN).__len__() != 4:
                Error.setMessage(self, message_shown="PIN length must be 4!")
            else:
                Error.setMessage(self, message_shown="Invalid PIN!")
            return

    def back(self):
        self.master.withdraw()


class closeAccount:
    def __init__(self, window=None):
        self.master = window
        window.geometry("411x117+498+261")
        window.minsize(120, 1)
        window.maxsize(1370, 749)
        window.resizable(0, 0)
        window.title("Close Account")
        window.configure(background="#f2f3f4")

        self.Label1 = tk.Label(window, background="#f2f3f4", disabledforeground="#a3a3a3", foreground="#000000",
                               text='''Enter your PIN:''')
        self.Label1.place(relx=0.268, rely=0.256, height=21, width=94)

        self.Entry1 = tk.Entry(window, show="*", background="#cae4ff", disabledforeground="#a3a3a3", font="TkFixedFont",
                               foreground="#000000", insertbackground="black")
        self.Entry1.place(relx=0.511, rely=0.256, height=20, relwidth=0.229)

        self.Button1 = tk.Button(window, activebackground="#ececec", activeforeground="#000000", background="#004080",
                                 disabledforeground="#a3a3a3", foreground="#ffffff", borderwidth="0",
                                 highlightbackground="#d9d9d9",
                                 highlightcolor="black", pady="0", text='''Proceed''',
                                 command=lambda: self.submit(self.Entry1.get()))
        self.Button1.place(relx=0.614, rely=0.712, height=24, width=67)

        self.Button2 = tk.Button(window, activebackground="#ececec", activeforeground="#000000", background="#004080",
                                 disabledforeground="#a3a3a3", foreground="#ffffff", borderwidth="0",
                                 highlightbackground="#d9d9d9",
                                 highlightcolor="black", pady="0", text="Back", command=self.back)
        self.Button2.place(relx=0.214, rely=0.712, height=24, width=67)

    def submit(self, PIN):
        print("Submit pressed.")
        print(customer_accNO, PIN)
        if check_credentials(customer_accNO, PIN, 2, False):
            print("Correct accepted.")
            delete_customer_account(customer_accNO, 2)
            self.master.withdraw()
            CustomerLogin(Toplevel(self.master))
        else:
            print("Incorrect accepted.")
            Error(Toplevel(self.master))
            Error.setMessage(self, message_shown="Invalid PIN!")

    def back(self):
        self.master.withdraw()
        customerMenu(Toplevel(self.master))


class checkAccountSummary:
    def __init__(self, window=None):
        self.master = window
        window.geometry("411x117+498+261")
        window.minsize(120, 1)
        window.maxsize(1370, 749)
        window.resizable(0, 0)
        window.title("Check Account Summary")
        window.configure(background="#f2f3f4")

        self.Label1 = tk.Label(window, background="#f2f3f4", disabledforeground="#a3a3a3", foreground="#000000",
                               text='''Enter ID :''')
        self.Label1.place(relx=0.268, rely=0.256, height=21, width=94)

        self.Entry1 = tk.Entry(window, background="#cae4ff", disabledforeground="#a3a3a3", font="TkFixedFont",
                               foreground="#000000", insertbackground="black")
        self.Entry1.place(relx=0.511, rely=0.256, height=20, relwidth=0.229)

        self.Button1 = tk.Button(window, activebackground="#ececec", activeforeground="#000000", background="#004080",
                                 disabledforeground="#a3a3a3", foreground="#ffffff", borderwidth="0",
                                 highlightbackground="#d9d9d9",
                                 highlightcolor="black", pady="0", text='''Proceed''',
                                 command=lambda: self.submit(self.Entry1.get()))
        self.Button1.place(relx=0.614, rely=0.712, height=24, width=67)

        self.Button2 = tk.Button(window, activebackground="#ececec", activeforeground="#000000", background="#004080",
                                 disabledforeground="#a3a3a3", foreground="#ffffff", borderwidth="0",
                                 highlightbackground="#d9d9d9",
                                 highlightcolor="black", pady="0", text="Back", command=self.back)
        self.Button2.place(relx=0.214, rely=0.712, height=24, width=67)

    def back(self):
        self.master.withdraw()

    def submit(self, identity):
        if not is_valid(identity):
            adminMenu.printAccountSummary(identity)
        else:
            Error(Toplevel(self.master))
            Error.setMessage(self, message_shown="Id doesn't exist!")
            return
        self.master.withdraw()





root = tk.Tk()
top = welcomeScreen(root)
root.mainloop()

# Tkinter GUI code ends.
