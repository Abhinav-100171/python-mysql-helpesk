import mysql.connector
from database import get_connection


# ==========================================
# DATABASE HELPER FUNCTIONS
# ==========================================

def add_history(ticket_id, user_id, action):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        query = """
        INSERT INTO ticket_history (ticket_id, user_id, action)
        VALUES (%s, %s, %s)
        """
        cursor.execute(query, (ticket_id, user_id, action))
        connection.commit()
    finally:
        cursor.close()
        connection.close()


def can_access_ticket(ticket_id, user_id, role):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        if role == "admin":
            cursor.execute(
                "SELECT id FROM tickets WHERE id = %s",
                (ticket_id,)
            )
        elif role == "support":
            cursor.execute(
                """
                SELECT id FROM tickets
                WHERE id = %s AND assigned_to = %s
                """,
                (ticket_id, user_id)
            )
        else:
            cursor.execute(
                """
                SELECT id FROM tickets
                WHERE id = %s AND user_id = %s
                """,
                (ticket_id, user_id)
            )

        return cursor.fetchone() is not None
    finally:
        cursor.close()
        connection.close()


# ==========================================
# REGISTRATION AND LOGIN
# ==========================================

def register_user():
    print("\n--- USER REGISTRATION ---")

    username = input("Enter username: ").strip()
    password = input("Enter password: ")
    full_name = input("Enter full name: ").strip()
    email = input("Enter email: ").strip()

    if not username or not password or not full_name:
        print("Username, password, and full name are required.")
        return

    connection = get_connection()
    cursor = connection.cursor()

    try:
        query = """
        INSERT INTO users (username, password, full_name, email)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (username, password, full_name, email or None))
        connection.commit()
        print("\nRegistration successful!")

    except mysql.connector.Error as error:
        print("\nRegistration failed:", error)

    finally:
        cursor.close()
        connection.close()


def login_user():
    print("\n--- LOGIN ---")

    username = input("Enter username: ").strip()
    password = input("Enter password: ")

    connection = get_connection()
    cursor = connection.cursor()

    try:
        query = """
        SELECT id, username, full_name, role
        FROM users
        WHERE username = %s AND password = %s
        """
        cursor.execute(query, (username, password))
        user = cursor.fetchone()

    finally:
        cursor.close()
        connection.close()

    if not user:
        print("\nInvalid username or password.")
        return

    user_id, username, full_name, role = user

    print("\nLogin successful!")
    print("Welcome,", full_name)
    print("Role:", role)

    if role == "user":
        user_menu(user_id)
    elif role == "admin":
        admin_menu(user_id)
    elif role == "support":
        support_menu(user_id)
    else:
        print("Unknown account role.")


# ==========================================
# CREATE AND VIEW USER TICKETS
# ==========================================

def create_ticket(user_id):
    print("\n--- CREATE SUPPORT TICKET ---")

    title = input("Enter problem title: ").strip()
    description = input("Describe your problem: ").strip()

    if not title or not description:
        print("Title and description are required.")
        return

    print("\nSelect Priority:")
    print("1. Low")
    print("2. Medium")
    print("3. High")
    print("4. Critical")

    priorities = {
        "1": "Low",
        "2": "Medium",
        "3": "High",
        "4": "Critical"
    }

    priority = priorities.get(input("Enter priority: "), "Medium")

    connection = get_connection()
    cursor = connection.cursor()

    try:
        query = """
        INSERT INTO tickets (user_id, title, description, priority)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (user_id, title, description, priority))
        connection.commit()
        ticket_id = cursor.lastrowid

        print("\nTicket created successfully!")
        print("Ticket ID:", ticket_id)

    finally:
        cursor.close()
        connection.close()

    add_history(ticket_id, user_id, "Ticket created")


def view_my_tickets(user_id):
    print("\n--- MY TICKETS ---")

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT id, title, priority, status, created_at
            FROM tickets
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (user_id,)
        )
        tickets = cursor.fetchall()

        if not tickets:
            print("You have no tickets.")
            return

        for ticket in tickets:
            print("\n----------------------------")
            print("Ticket ID :", ticket[0])
            print("Title     :", ticket[1])
            print("Priority  :", ticket[2])
            print("Status    :", ticket[3])
            print("Created   :", ticket[4])

    finally:
        cursor.close()
        connection.close()


def view_ticket_details(user_id):
    print("\n--- TICKET DETAILS ---")
    ticket_id = input("Enter Ticket ID: ").strip()

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT id, title, description, priority, status,
                   assigned_to, created_at, updated_at
            FROM tickets
            WHERE id = %s AND user_id = %s
            """,
            (ticket_id, user_id)
        )
        ticket = cursor.fetchone()

        if not ticket:
            print("Ticket not found or you don't have permission.")
            return

        print("\nTicket ID   :", ticket[0])
        print("Title       :", ticket[1])
        print("Description :", ticket[2])
        print("Priority    :", ticket[3])
        print("Status      :", ticket[4])
        print("Assigned To :", ticket[5])
        print("Created     :", ticket[6])
        print("Updated     :", ticket[7])

    finally:
        cursor.close()
        connection.close()


# ==========================================
# COMMENTS
# ==========================================

def add_comment(user_id, role):
    print("\n--- ADD TICKET COMMENT ---")

    ticket_id = input("Enter Ticket ID: ").strip()

    if not can_access_ticket(ticket_id, user_id, role):
        print("Ticket not found or you don't have permission.")
        return

    comment = input("Enter your comment: ").strip()

    if not comment:
        print("Comment cannot be empty.")
        return

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO comments (ticket_id, user_id, comment)
            VALUES (%s, %s, %s)
            """,
            (ticket_id, user_id, comment)
        )
        connection.commit()
        print("Comment added successfully!")

    finally:
        cursor.close()
        connection.close()

    add_history(ticket_id, user_id, "Comment added")


def view_comments(ticket_id, user_id, role):
    print("\n--- TICKET COMMENTS ---")

    if not can_access_ticket(ticket_id, user_id, role):
        print("Ticket not found or you don't have permission.")
        return

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT comments.comment, users.username, comments.created_at
            FROM comments
            JOIN users ON comments.user_id = users.id
            WHERE comments.ticket_id = %s
            ORDER BY comments.created_at ASC
            """,
            (ticket_id,)
        )
        comments = cursor.fetchall()

        if not comments:
            print("No comments found.")
            return

        for comment in comments:
            print("\n----------------------------")
            print("User    :", comment[1])
            print("Comment :", comment[0])
            print("Time    :", comment[2])

    finally:
        cursor.close()
        connection.close()


# ==========================================
# TICKET HISTORY
# ==========================================

def view_ticket_history(ticket_id, user_id, role):
    print("\n--- TICKET HISTORY ---")

    if not can_access_ticket(ticket_id, user_id, role):
        print("Ticket not found or you don't have permission.")
        return

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT ticket_history.action,
                   users.username,
                   ticket_history.created_at
            FROM ticket_history
            JOIN users ON ticket_history.user_id = users.id
            WHERE ticket_history.ticket_id = %s
            ORDER BY ticket_history.created_at ASC
            """,
            (ticket_id,)
        )
        history = cursor.fetchall()

        if not history:
            print("No history found.")
            return

        for record in history:
            print("\n----------------------------")
            print("Action :", record[0])
            print("User   :", record[1])
            print("Time   :", record[2])

    finally:
        cursor.close()
        connection.close()


# ==========================================
# ADMIN FUNCTIONS
# ==========================================

def view_all_tickets():
    print("\n--- ALL SUPPORT TICKETS ---")

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT tickets.id, tickets.title, tickets.priority,
                   tickets.status, users.username, tickets.created_at
            FROM tickets
            JOIN users ON tickets.user_id = users.id
            ORDER BY tickets.created_at DESC
            """
        )
        tickets = cursor.fetchall()

        if not tickets:
            print("No tickets found.")
            return

        for ticket in tickets:
            print("\n----------------------------")
            print("Ticket ID :", ticket[0])
            print("Title     :", ticket[1])
            print("Priority  :", ticket[2])
            print("Status    :", ticket[3])
            print("Created By:", ticket[4])
            print("Created   :", ticket[5])

    finally:
        cursor.close()
        connection.close()


def manage_ticket(admin_id):
    print("\n--- MANAGE TICKET ---")
    ticket_id = input("Enter Ticket ID: ").strip()

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT id FROM tickets WHERE id = %s", (ticket_id,))
        if not cursor.fetchone():
            print("Ticket not found.")
            return

        print("\n1. Change Status")
        print("2. Change Priority")
        print("3. Assign Support Staff")

        choice = input("Enter your choice: ")

        if choice == "1":
            statuses = {
                "1": "Open",
                "2": "In Progress",
                "3": "Resolved",
                "4": "Closed"
            }

            print("1. Open")
            print("2. In Progress")
            print("3. Resolved")
            print("4. Closed")

            status = statuses.get(input("Select status: "))

            if not status:
                print("Invalid status.")
                return

            cursor.execute(
                "UPDATE tickets SET status = %s WHERE id = %s",
                (status, ticket_id)
            )
            connection.commit()
            action = "Status changed to " + status

        elif choice == "2":
            priorities = {
                "1": "Low",
                "2": "Medium",
                "3": "High",
                "4": "Critical"
            }

            print("1. Low")
            print("2. Medium")
            print("3. High")
            print("4. Critical")

            priority = priorities.get(input("Select priority: "))

            if not priority:
                print("Invalid priority.")
                return

            cursor.execute(
                "UPDATE tickets SET priority = %s WHERE id = %s",
                (priority, ticket_id)
            )
            connection.commit()
            action = "Priority changed to " + priority

        elif choice == "3":
            support_username = input("Enter support staff username: ").strip()

            cursor.execute(
                """
                SELECT id FROM users
                WHERE username = %s AND role = 'support'
                """,
                (support_username,)
            )
            support_user = cursor.fetchone()

            if not support_user:
                print("Support staff not found.")
                return

            cursor.execute(
                "UPDATE tickets SET assigned_to = %s WHERE id = %s",
                (support_user[0], ticket_id)
            )
            connection.commit()
            action = "Ticket assigned to " + support_username

        else:
            print("Invalid choice.")
            return

        print("Ticket updated successfully!")

    finally:
        cursor.close()
        connection.close()

    add_history(ticket_id, admin_id, action)


# ==========================================
# SUPPORT STAFF FUNCTIONS
# ==========================================

def view_assigned_tickets(support_id):
    print("\n--- ASSIGNED TICKETS ---")

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT tickets.id, tickets.title, tickets.description,
                   tickets.priority, tickets.status, users.username,
                   tickets.created_at
            FROM tickets
            JOIN users ON tickets.user_id = users.id
            WHERE tickets.assigned_to = %s
            ORDER BY tickets.created_at DESC
            """,
            (support_id,)
        )
        tickets = cursor.fetchall()

        if not tickets:
            print("No tickets assigned to you.")
            return

        for ticket in tickets:
            print("\n----------------------------")
            print("Ticket ID  :", ticket[0])
            print("Title      :", ticket[1])
            print("Description:", ticket[2])
            print("Priority   :", ticket[3])
            print("Status     :", ticket[4])
            print("Created By :", ticket[5])
            print("Created    :", ticket[6])

    finally:
        cursor.close()
        connection.close()


def update_assigned_ticket(support_id):
    print("\n--- UPDATE ASSIGNED TICKET ---")
    ticket_id = input("Enter Ticket ID: ").strip()

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT id FROM tickets
            WHERE id = %s AND assigned_to = %s
            """,
            (ticket_id, support_id)
        )

        if not cursor.fetchone():
            print("This ticket is not assigned to you.")
            return

        statuses = {
            "1": "Open",
            "2": "In Progress",
            "3": "Resolved",
            "4": "Closed"
        }

        print("1. Open")
        print("2. In Progress")
        print("3. Resolved")
        print("4. Closed")

        status = statuses.get(input("Select new status: "))

        if not status:
            print("Invalid status.")
            return

        cursor.execute(
            """
            UPDATE tickets SET status = %s
            WHERE id = %s AND assigned_to = %s
            """,
            (status, ticket_id, support_id)
        )
        connection.commit()
        print("Ticket status updated successfully!")

    finally:
        cursor.close()
        connection.close()

    add_history(ticket_id, support_id, "Status changed to " + status)


# ==========================================
# USER DASHBOARD
# ==========================================

def user_menu(user_id):
    while True:
        print("\n========== USER MENU ==========")
        print("1. Create Ticket")
        print("2. View My Tickets")
        print("3. View Ticket Details")
        print("4. Add Comment")
        print("5. View Comments")
        print("6. View Ticket History")
        print("7. Logout")

        choice = input("Enter your choice: ")

        if choice == "1":
            create_ticket(user_id)
        elif choice == "2":
            view_my_tickets(user_id)
        elif choice == "3":
            view_ticket_details(user_id)
        elif choice == "4":
            add_comment(user_id, "user")
        elif choice == "5":
            ticket_id = input("Enter Ticket ID: ").strip()
            view_comments(ticket_id, user_id, "user")
        elif choice == "6":
            ticket_id = input("Enter Ticket ID: ").strip()
            view_ticket_history(ticket_id, user_id, "user")
        elif choice == "7":
            print("Logged out.")
            break
        else:
            print("Invalid choice.")


# ==========================================
# ADMIN DASHBOARD
# ==========================================

def admin_menu(admin_id):
    while True:
        print("\n========== ADMIN DASHBOARD ==========")
        print("1. View All Tickets")
        print("2. Manage Ticket")
        print("3. View Ticket Comments")
        print("4. View Ticket History")
        print("5. Logout")

        choice = input("Enter your choice: ")

        if choice == "1":
            view_all_tickets()
        elif choice == "2":
            manage_ticket(admin_id)
        elif choice == "3":
            ticket_id = input("Enter Ticket ID: ").strip()
            view_comments(ticket_id, admin_id, "admin")
        elif choice == "4":
            ticket_id = input("Enter Ticket ID: ").strip()
            view_ticket_history(ticket_id, admin_id, "admin")
        elif choice == "5":
            print("Admin logged out.")
            break
        else:
            print("Invalid choice.")


# ==========================================
# SUPPORT STAFF DASHBOARD
# ==========================================

def support_menu(support_id):
    while True:
        print("\n====== SUPPORT STAFF DASHBOARD ======")
        print("1. View Assigned Tickets")
        print("2. Update Ticket Status")
        print("3. Add Comment")
        print("4. View Comments")
        print("5. View Ticket History")
        print("6. Logout")

        choice = input("Enter your choice: ")

        if choice == "1":
            view_assigned_tickets(support_id)
        elif choice == "2":
            update_assigned_ticket(support_id)
        elif choice == "3":
            add_comment(support_id, "support")
        elif choice == "4":
            ticket_id = input("Enter Ticket ID: ").strip()
            view_comments(ticket_id, support_id, "support")
        elif choice == "5":
            ticket_id = input("Enter Ticket ID: ").strip()
            view_ticket_history(ticket_id, support_id, "support")
        elif choice == "6":
            print("Support staff logged out.")
            break
        else:
            print("Invalid choice.")


# ==========================================
# MAIN PROGRAM
# ==========================================

def main():
    while True:
        print("\n================================")
        print("           IT HELP DESK")
        print("================================")
        print("1. Register")
        print("2. Login")
        print("3. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            register_user()
        elif choice == "2":
            login_user()
        elif choice == "3":
            print("Thank you for using IT Help Desk!")
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
