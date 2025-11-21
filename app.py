# This is a Python Flask server application demonstrating the secure backend logic 
# and connection to a MySQL database, as required for the Hotel Booking System project.
#
# NOTE: This file is for demonstration and documentation purposes (for your report's 
# Appendix/Chapter 3). It cannot be run on GitHub Pages, which only hosts static HTML.

from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector

app = Flask(__name__)
CORS(app) # Enables cross-origin requests, necessary if UI is hosted separately

# --- Database Configuration (MySQL/SQL Server - Replace with your actual credentials) ---
DB_CONFIG = {
    'user': 'hotel_admin',
    'password': 'secure_password_123',
    'host': 'localhost',
    'database': 'hotel_db',
    'raise_on_warnings': True
}

def get_db_connection():
    """Establishes and returns a database connection."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"Database Connection Error: {err}")
        return None

# --- API Endpoints: Booking Module CRUD Operations ---

@app.route('/api/bookings', methods=['POST'])
def add_booking():
    """
    Objective 2: Enable users to ADD booking records.
    Handles inserting a new reservation into the Booking and potentially Customer tables.
    """
    data = request.json
    guest_name = data.get('guestName')
    room_number = data.get('roomNumber')
    check_in = data.get('checkInDate')
    check_out = data.get('checkOutDate')
    total_cost = data.get('totalCost')
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor()
    try:
        # Step 1: Find/Insert Customer (Simplified logic for demo)
        # In a real system, we'd check for existing customer by email.
        customer_id = data.get('customerId') 

        # Step 2: Insert Booking Record
        booking_sql = """
            INSERT INTO Booking (CustomerID, RoomNumber, CheckInDate, CheckOutDate, TotalCost, BookingDate)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """
        cursor.execute(booking_sql, (customer_id, room_number, check_in, check_out, total_cost))
        booking_id = cursor.lastrowid
        
        # Step 3: Update Room Status (Objective 3: Real-time monitoring)
        status_sql = "UPDATE Room SET Status = 'Occupied' WHERE RoomNumber = %s"
        cursor.execute(status_sql, (room_number,))
        
        conn.commit()
        return jsonify({"message": "Booking successful", "bookingId": booking_id}), 201

    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({"error": "Failed to process booking", "details": str(err)}), 400
    finally:
        cursor.close()
        conn.close()


@app.route('/api/rooms', methods=['GET'])
def get_room_availability():
    """
    Objective 3: Ensure real-time monitoring of room availability.
    Retrieves all room data including status and rate for the UI.
    """
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        # Join to get room details and their type rate
        sql = """
            SELECT r.RoomNumber, rt.TypeName AS RoomType, rt.Rate, r.Status
            FROM Room r
            JOIN RoomType rt ON r.RoomTypeID = rt.RoomTypeID
            ORDER BY r.RoomNumber
        """
        cursor.execute(sql)
        rooms = cursor.fetchall()
        return jsonify(rooms)
    
    except mysql.connector.Error as err:
        return jsonify({"error": "Failed to fetch rooms", "details": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/bookings/<int:booking_id>', methods=['DELETE'])
def cancel_booking(booking_id):
    """
    Objective 2: Enable users to DELETE booking records (cancellation).
    Deletes the booking and updates the room status back to Vacant.
    """
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor()
    try:
        # Step 1: Get room number associated with the booking
        cursor.execute("SELECT RoomNumber FROM Booking WHERE BookingID = %s", (booking_id,))
        result = cursor.fetchone()
        if not result:
            return jsonify({"error": "Booking not found"}), 404
        room_number = result[0]
        
        # Step 2: Delete Booking
        cursor.execute("DELETE FROM Booking WHERE BookingID = %s", (booking_id,))
        
        # Step 3: Update Room Status
        status_sql = "UPDATE Room SET Status = 'Vacant' WHERE RoomNumber = %s"
        cursor.execute(status_sql, (room_number,))
        
        conn.commit()
        return jsonify({"message": f"Booking {booking_id} cancelled successfully. Room {room_number} is now Vacant."}), 200

    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({"error": "Failed to cancel booking", "details": str(err)}), 400
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    # When running locally, Flask runs on http://127.0.0.1:5000/
    app.run(debug=True)
