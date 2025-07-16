from flask import Flask, request, jsonify, render_template, send_file
import pandas as pd
import psycopg2
from fpdf import FPDF
import io
import os
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY","dev-key")  # ✅ Set it immediately after app = Flask(__name__)
import requests
from flask import request, redirect, render_template, flash
from werkzeug.security import generate_password_hash
import secrets
from flask_mail import Mail, Message
from flask import session, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime

@app.route("/")
def home():
    # If user is logged in, show index.html
    if "user_id" in session:
        return render_template("index.html")
    # Otherwise redirect to login
    return redirect(url_for("signup"))


mail = Mail(app)
# Connect to PostgreSQL
import os

conn = psycopg2.connect(
    database=os.environ.get("DB_NAME"),
    user=os.environ.get("DB_USER"),
    password=os.environ.get("DB_PASSWORD"),
    host=os.environ.get("DB_HOST"),
    port=os.environ.get("DB_PORT", 5432),
    sslmode="require"
)
@app.context_processor
def inject_logged_in_user():
    user_email = session.get("user_email")
    username = user_email.split("@")[0] if user_email else None
    return dict(logged_in_user=username)


# Route to render the frontend HTML
@app.route('/main_page')
def index():
    return render_template('index.html')
def log_action(action, client_id, details=""):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO audit_log (action, client_id, details)
        VALUES (%s, %s, %s)
    """, (action, client_id, details))
    conn.commit()
    cur.close()
# Route to get client data as JSON
@app.route('/client/<int:client_id>', methods=['GET'])
def get_client_data(client_id):
    cur = conn.cursor()
    
    # SQL query to fetch basic client details along with compliance details if needed
    query = """
        SELECT cd."Client_id", cd."Date_of_birth", cd."Age", cd."Residency_address", cd."Contact_number", 
               cd."Employment_status", cd."Ic_number", cd."Email_address", cd."Client_profile", 
               cd."Name", cd."Nationality",
               cc."Onboarded_date", cc."Last_periodic_risk_assessment", 
               cc."Next_periodic_risk_assessment", cc."Risk_rating", cc."Relationship_Manager", 
               cc."Service_type", cc."Client_type", cc."Pep"
        FROM client_data AS cd
        LEFT JOIN client_compliance AS cc
        ON cd."Client_id" = cc."Client_id"
        WHERE cd."Client_id" = %s;
    """
    
    # Execute query
    cur.execute(query, (client_id,))
    result = cur.fetchone()
    colnames = [desc[0] for desc in cur.description]
    cur.close()

    if result:
        return jsonify(dict(zip(colnames, result)))
    else:
        return jsonify({"error": "Client not found"}), 404

from flask import request, redirect, url_for
from werkzeug.utils import secure_filename
import psycopg2
import traceback
@app.route("/approve/<int:pending_id>", methods=["POST"])
def approve_pending_client(pending_id):
    try:
        cursor = conn.cursor()

        # 1. Fetch pending client info
        cursor.execute("SELECT * FROM pending WHERE pending_id = %s", (pending_id,))
        pending = cursor.fetchone()
        if not pending:
            return "Pending entry not found", 404

        columns = [desc[0] for desc in cursor.description]
        pending_data = dict(zip(columns, pending))

        # 2. Insert into client_data
        cursor.execute("""
            INSERT INTO client_data (
                "Name", "Nationality", "Residency_address", "Contact_number",
                "Date_of_birth", "Ic_number", "Age", "Client_profile",
                "Employment_status", "Email_address"
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING "Client_id"
        """, (
            pending_data["name"], pending_data["nationality"], pending_data["residency_address"],
            pending_data["contact_number"], pending_data["date_of_birth"], pending_data["ic_number"],
            pending_data["age"], pending_data["client_profile"], pending_data["employment_status"],
            pending_data["email_address"]
        ))
        client_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO client_compliance (
                "Client_id", "Onboarded_date", "Last_periodic_risk_assessment",
                "Next_periodic_risk_assessment", "Risk_rating", "Relationship_Manager",
                "Service_type", "Client_type", "Pep"
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            client_id,
            pending_data.get("onboarded_date"),
            pending_data.get("last_periodic_risk_assessment"),
            pending_data.get("next_periodic_risk_assessment"),
            pending_data.get("risk_rating"),
            pending_data.get("relationship_manager"),
            pending_data.get("service_type"),
            pending_data.get("client_type"),
            pending_data.get("pep")
        ))

        # 4. Transfer associated files
        cursor.execute("SELECT * FROM pending_files WHERE pending_id = %s", (pending_id,))
        files = cursor.fetchall()
        file_cols = [desc[0] for desc in cursor.description]

        for row in files:
            file_record = dict(zip(file_cols, row))
            cursor.execute("""
                INSERT INTO client_files (client_id, file_type_id, file_name, file_data)
                VALUES (%s, %s, %s, %s)
            """, (
                client_id,
                file_record["file_type_id"],
                file_record["file_name"],
                file_record["file_data"]
            ))




        # Optional: Clean up pending_files (not required, but tidy)
        cursor.execute("DELETE FROM pending_files WHERE pending_id = %s", (pending_id,))
        cursor.execute("DELETE FROM pending WHERE pending_id = %s", (pending_id,))

        conn.commit()
        cursor.close()

        return redirect(url_for("pending_page"))

    except Exception as e:
        conn.rollback()
        print("❌ Error approving client:", e)
        return f"Error approving client: {e}", 500

@app.route("/reject/<int:pending_id>", methods=["POST"])
def reject_pending_client(pending_id):
    try:
        comment = request.form.get("comment", "").strip()

        cursor = conn.cursor()
        cursor.execute("""
            UPDATE pending
            SET approval_status = %s,
                comments = %s
            WHERE pending_id = %s
        """, ("Rejected", comment, pending_id))

        conn.commit()
        cursor.close()
        return redirect(url_for("pending_page"))

    except Exception as e:
        conn.rollback()
        print("❌ Error rejecting client:", e)
        return f"Error rejecting client: {e}", 500

@app.route("/submit-pending", methods=["POST"])
def submit_pending():
    try:
        # 🔍 Debug: Print all incoming form fields
        print("🔎 Incoming form data:")
        for key in request.form:
            print(f"  {key}: {request.form[key]}")
        

        # 🔍 Debug: Print file info
        print("\n📁 Incoming files:")
        files = request.files.getlist("client_files")
        for file in files:
            print(f"  Filename: {file.filename}, Content-Type: {file.content_type}, Size: {len(file.read())} bytes")
            file.seek(0)  # Reset pointer for DB insert

        # ✅ Extract form data
        data = request.form
        print("Last assessment:", data.get("last_periodic_risk_assessment"))
        print("Next assessment:", data.get("next_periodic_risk_assessment"))
        submitted_by = session.get("username") 

        cursor = conn.cursor()

        # ✅ Insert into `pending`
        cursor.execute("""
            INSERT INTO pending (
                name, nationality, residency_address, contact_number, date_of_birth,
                ic_number, age, client_profile, employment_status, email_address,
                onboarded_date, last_periodic_risk_assessment, next_periodic_risk_assessment,
                risk_rating, relationship_manager, service_type, client_type, pep,
                submitted_by,submitted_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s,%s)
            RETURNING pending_id
        """, (
            data.get("name"),
            data.get("nationality"),
            data.get("residency_address"),
            data.get("contact_number"),
            data.get("date_of_birth"),
            data.get("ic_number"),
            int(data.get("age")) if data.get("age") else None,
            data.get("client_profile"),
            data.get("employment_status"),
            data.get("email_address"),
            data.get("onboarded_date"),
            data.get("last_periodic_risk_assessment", "").strip() or None,
            data.get("next_periodic_risk_assessment", "").strip() or None,
            data.get("risk_rating"),
            data.get("relationship_manager"),
            data.get("service_type"),
            data.get("client_type"),
            data.get("pep"),
            session.get("username"),
            datetime.now()
        ))

        pending_id = cursor.fetchone()[0]

        # ✅ Save files
        for file in files:
            if file.filename:
                filename = secure_filename(file.filename)
                file_data = file.read()
                file_ext = filename.split('.')[-1].upper()

                cursor.execute("SELECT file_type_id FROM file_types WHERE UPPER(type) = %s", (file_ext,))
                result = cursor.fetchone()
                file_type_id = result[0] if result else None

                cursor.execute("""
                    INSERT INTO pending_files (pending_id, file_type_id, file_name, file_data)
                    VALUES (%s, %s, %s, %s)
                """, (pending_id, file_type_id, filename, psycopg2.Binary(file_data)))

        conn.commit()
        cursor.close()

        return jsonify({"message": "Client submitted for approval with files."}), 200


    except Exception as e:
        conn.rollback()
        print("❌ Error submitting pending client:")
        traceback.print_exc()  # ⬅️ full error trace
        return jsonify({"error": str(e)}), 500
@app.route('/add')
def add_page():
    return render_template('add.html') 
@app.route('/download_page')
def download_page():
    return render_template('download.html') 
@app.route('/update_page')
def update_page():
    return render_template('update.html')
@app.route('/test_update_page')
def test_update_page():
    return render_template('test_update.html')
@app.route('/add_account_page')
def add_account_page():
    return render_template('add_account.html')
@app.route("/view_page")
def view_page():
    return render_template("view.html")
@app.route("/statistics_page")
def statistics_page():
    return render_template("statistics.html")
@app.route("/redeemed_view_page")
def redeemed_view_page():
    return render_template("redeemed_view.html")
@app.route('/to_do')
def to_do():
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks ORDER BY id DESC")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    tasks = [dict(zip(columns, row)) for row in rows]
    cursor.close()
    return render_template("to_do.html", tasks=tasks,)
@app.route('/add_task')
def add_task_page():
    return render_template('add_task.html') 
@app.route("/pending_page")
def pending_page():
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            pending_id,                 -- No.
            onboarded_date,             -- Onboarded Date
            service_type,               -- Service Type
            name,                       -- Name
            nationality,                -- Nationality
            residency_address,          -- Residency Address
            contact_number,             -- Contact No.
            email_address,              -- Email Address
            ic_number,                  -- ID Number
            expiry_date,                -- Expiry Date
            client_type,                -- Client Type
            pep,                        -- PEP (Yes/No)
            risk_rating,                -- Risk Rating
            irpq_rating,                -- IRPQ Rating
            last_periodic_risk_assessment,  -- Last Periodic Risk Assessment
            next_periodic_risk_assessment,  -- Next Periodic Risk Assessment
            relationship_manager,       -- Relationship Manager
            remarks,                    -- Remarks
            client_profile,             -- Client Profile
            employment_status,          -- Employed/Self-Employed
            date_of_birth,              -- Date of Birth
            age,                        -- Age
            submitted_by,
            submitted_at,
            approval_status,
            comments
        FROM pending
        ORDER BY submitted_at DESC
    """)
    pending_entries = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    cursor.close()

    # Convert each row to a dictionary
    pending_clients = [dict(zip(columns, row)) for row in pending_entries]

    return render_template("pending.html", pending_entries=pending_clients)


@app.route("/login_page")
def login_page():
    return render_template("login.html")
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
@app.route("/download", methods=["GET", "POST"])
def download_table():
    table = request.form.get("table")
    file_format = request.form.get("format")
    sort_by = request.form.get("sort_by")
    sort_order = request.form.get("sort_order", "ASC").upper()

    valid_sort_orders = ["ASC", "DESC"]
    sort_clause = ""

    if sort_by:
        # Whitelist to avoid SQL injection
        allowed_columns = [
            "Client_id", "Name", "Date_of_birth", "Age"
            # Add more allowed columns here if needed
        ]
        if sort_by in allowed_columns and sort_order in valid_sort_orders:
            sort_clause = f' ORDER BY "{sort_by}" {sort_order}'

    cur = conn.cursor()

    if table == "all":
        query = f"""
            SELECT cd.*, cc."Onboarded_date", cc."Last_periodic_risk_assessment", 
                   cc."Next_periodic_risk_assessment", cc."Risk_rating", 
                   cc."Relationship_Manager", cc."Service_type", 
                   cc."Client_type", cc."Pep"
            FROM client_data cd
            LEFT JOIN client_compliance cc ON cd."Client_id" = cc."Client_id"
            {sort_clause};
        """
    else:
        query = f'SELECT * FROM {table} {sort_clause}'

    cur.execute(query)
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    df = pd.DataFrame(rows, columns=columns)
    cur.close()

    if table == "all":
        df.drop_duplicates(subset=["Client_id"], keep="first", inplace=True)

    if file_format == "excel":
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False)
        output.seek(0)
        return send_file(output, as_attachment=True, download_name="data.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    elif file_format == "pdf":
        pdf = FPDF(orientation='L', unit='mm', format='A4')  # Landscape
        pdf.set_auto_page_break(auto=True, margin=10)
        pdf.add_page()

        pdf.set_font("Arial", size=7)

        # Adjust column width (max total width = 277mm in landscape A4)
        page_width = pdf.w - 2 * pdf.l_margin
        max_col_width = 50  # prevent overly wide columns
        col_width = min(page_width / len(columns), max_col_width)

        # Header row
        pdf.set_font("Arial", style='B', size=4)
        for col in columns:
            header_text = str(col)[:30]
            pdf.cell(col_width, 7, header_text, border=1, align='C')
        pdf.ln()

        # Data rows
        pdf.set_font("Arial", size=7)
        for row in rows:
            y_start = pdf.get_y()
            x_start = pdf.l_margin
            max_y = y_start

            cell_heights = []

            # First pass: determine max height for this row
            for idx, item in enumerate(row):
                text = str(item) if item is not None else ''
                lines = pdf.multi_cell(col_width, 4, text, border=0, align='L', split_only=True)
                cell_heights.append(len(lines) * 4)

            row_height = max(cell_heights)

            # Second pass: draw each cell with uniform row height
            for idx, item in enumerate(row):
                text = str(item) if item is not None else ''
                x = x_start + idx * col_width
                pdf.set_xy(x, y_start)
                pdf.multi_cell(col_width, 4, text, border=1, align='L')

            pdf.set_y(y_start + row_height)


        pdf_bytes = pdf.output(dest="S").encode("latin-1")
        pdf_output = io.BytesIO(pdf_bytes)

        return send_file(
            pdf_output,
            as_attachment=True,
            download_name="document.pdf",
            mimetype="application/pdf"
        )



    return "Invalid request", 400

@app.route('/update-client', methods=['POST'])
def update_client():
    data = request.get_json()

    if not data or "Client_id" not in data:
        return jsonify({"error": "Client ID is required"}), 400

    client_id = data["Client_id"]

    try:
        cur = conn.cursor()

        # Update client_data
        cur.execute("""
            UPDATE client_data SET
                "Name" = %s,
                "Nationality" = %s,
                "Residency_address" = %s,
                "Contact_number" = %s,
                "Date_of_birth" = %s,
                "Ic_number" = %s,
                "Age" = %s,
                "Client_profile" = %s,
                "Employment_status" = %s,
                "Email_address" = %s
            WHERE "Client_id" = %s
        """, (
            data["Name"], data["Nationality"], data["Residency_address"],
            data["Contact_number"], data["Date_of_birth"], data["IC_number"],
            data["Age"], data["Client_profile"], data["Employment_status"],
            data["Email_address"], client_id
        ))

        # Check if compliance record exists
        cur.execute('SELECT 1 FROM client_compliance WHERE "Client_id" = %s', (client_id,))
        exists = cur.fetchone()

        if exists:
            cur.execute("""
                UPDATE client_compliance SET
                    "Onboarded_date" = %s,
                    "Last_periodic_risk_assessment" = %s,
                    "Next_periodic_risk_assessment" = %s,
                    "Risk_rating" = %s,
                    "Relationship_Manager" = %s,
                    "Service_type" = %s,
                    "Client_type" = %s,
                    "Pep" = %s
                WHERE "Client_id" = %s
            """, (
                data.get("Onboarded_date"), data.get("Last_periodic_risk_assessment"),
                data.get("Next_periodic_risk_assessment"), data.get("Risk_rating"),
                data.get("Relationship_Manager"), data.get("Service_type"),
                data.get("Client_type"), data.get("Pep"), client_id
            ))
        else:
            # Insert only if any compliance field is provided
            compliance_values = [
                data.get("Onboarded_date"), data.get("Last_periodic_risk_assessment"),
                data.get("Next_periodic_risk_assessment"), data.get("Risk_rating"),
                data.get("Relationship_Manager"), data.get("Service_type"),
                data.get("Client_type"), data.get("Pep")
            ]
            if any(compliance_values):
                cur.execute("""
                    INSERT INTO client_compliance (
                        "Client_id", "Onboarded_date", "Last_periodic_risk_assessment",
                        "Next_periodic_risk_assessment", "Risk_rating", "Relationship_Manager",
                        "Service_type", "Client_type", "Pep"
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (client_id, *compliance_values))
        log_action("Update", client_id, f"Updated client: {data.get('Name', '')}")

        conn.commit()
        cur.close()
        return jsonify({"message": "Client updated successfully"}), 200

    except Exception as e:
        conn.rollback()
        print("Update failed:", e)
        return jsonify({"error": "Update failed"}), 500

@app.route("/view_table", methods=['GET', 'POST'])
def view_table():
    
    table = request.form.get("table")
    if not table:
        table = "client_data"
    sort_fields = request.form.getlist("sort_by[]")
    sort_orders = request.form.getlist("sort_order[]")

    allowed_columns = [
        "Name", "Client_id", "Age",
        "Risk_rating", "Relationship_Manager", "Service_type",
        "Client_type", "Pep", "Nationality"
    ]
    valid_sort_orders = ["ASC", "DESC"]

    order_clauses = []
    for field, direction in zip(sort_fields, sort_orders):
        if field in allowed_columns and direction in valid_sort_orders:
            order_clauses.append(f'"{field}" {direction}')

    sort_clause = f"ORDER BY {', '.join(order_clauses)}" if order_clauses else ""

    cur = conn.cursor()

    # Get data rows
    if table == "all":
        query = f"""
            SELECT cd.*, cc."Onboarded_date", cc."Last_periodic_risk_assessment",
                   cc."Next_periodic_risk_assessment", cc."Risk_rating", 
                   cc."Relationship_Manager", cc."Service_type", 
                   cc."Client_type", cc."Pep"
            FROM client_data cd
            LEFT JOIN client_compliance cc ON cd."Client_id" = cc."Client_id"
            {sort_clause};
        """
    else:
        query = f'SELECT * FROM {table} {sort_clause}'

    cur.execute(query)
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]

    # Fetch file data if applicable
    files_by_client = {}
    if table in ("client_data", "all"):
        client_ids = [row[columns.index("Client_id")] for row in rows if row[columns.index("Client_id")] is not None]
        if client_ids:
            format_ids = tuple(client_ids)
            query_files = """
                SELECT client_id, file_id, file_name 
                FROM client_files 
                WHERE client_id IN %s
            """
            cur.execute(query_files, (format_ids,))
            for client_id, file_id, file_name in cur.fetchall():
                files_by_client.setdefault(client_id, []).append({
                    "file_id": file_id,
                    "file_name": file_name
                })

    cur.close()

    return render_template(
        "view.html",
        columns=columns,
        rows=rows,
        selected_table=table,
        files_by_client=files_by_client
    )
@app.route('/get-all-clients', methods=['GET'])
def get_all_clients():
    try:
        cur = conn.cursor()

        # Get combined client and compliance data
        cur.execute("""
            SELECT 
                d."Client_id", d."Name", d."Nationality", d."Residency_address",
                d."Contact_number", d."Date_of_birth", d."Ic_number", d."Age",
                d."Client_profile", d."Employment_status", d."Email_address",
                c."Onboarded_date", c."Last_periodic_risk_assessment",
                c."Next_periodic_risk_assessment", c."Risk_rating",
                c."Relationship_Manager", c."Service_type",
                c."Client_type", c."Pep"
            FROM client_data d
            LEFT JOIN client_compliance c ON d."Client_id" = c."Client_id"
        """)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        clients = [dict(zip(columns, row)) for row in rows]

        # Get all files for all clients
        cur.execute("""
            SELECT client_id, file_id, file_name 
            FROM client_files
        """)
        file_rows = cur.fetchall()

        # Organize files by client_id
        files_by_client = {}
        for client_id, file_id, file_name in file_rows:
            files_by_client.setdefault(client_id, []).append({
                "file_id": file_id,
                "file_name": file_name,
                "url": url_for('view_file', file_id=file_id)
            })

        # Attach files to each client record
        for client in clients:
            cid = client["Client_id"]
            client["files"] = files_by_client.get(cid, [])

        cur.close()
        return jsonify(clients), 200

    except Exception as e:
        print("Error fetching clients and files:", e)
        return jsonify({"error": "Failed to retrieve client data"}), 500

@app.route("/redeemed_view", methods=['GET', 'POST'])
def redeemed_view():
    table = "redeemed"
    sort_fields = request.form.getlist("sort_by[]")
    sort_orders = request.form.getlist("sort_order[]")

    allowed_columns = [
    "name", "client_id", "age",
    "risk_rating", "relationship_manager", "service_type",
    "client_type", "pep", "nationality"
]
    valid_sort_orders = ["ASC", "DESC"]

    order_clauses = []
    for field, direction in zip(sort_fields, sort_orders):
        if field in allowed_columns and direction in valid_sort_orders:
            order_clauses.append(f'"{field}" {direction}')

    sort_clause = f"ORDER BY {', '.join(order_clauses)}" if order_clauses else ""

    cur = conn.cursor()

    # Get data from redeemed table
    query = f'SELECT * FROM redeemed {sort_clause}'
    cur.execute(query)
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]

    # Get associated files from redeemed_files table
    redeemed_files_by_client = {}
    client_ids = [row[columns.index("client_id")] for row in rows if row[columns.index("client_id")] is not None]
    if client_ids:
        format_ids = tuple(client_ids)
        query_files = """
            SELECT client_id, file_id, file_name 
            FROM redeemed_files 
            WHERE client_id IN %s
        """
        cur.execute(query_files, (format_ids,))
        for client_id, file_id, file_name in cur.fetchall():
            redeemed_files_by_client.setdefault(client_id, []).append({
                "file_id": file_id,
                "file_name": file_name
            })

    cur.close()

    return render_template(
        "redeemed_view.html",
        columns=columns,
        rows=rows,
        selected_table="redeemed",
        redeemed_files_by_client=redeemed_files_by_client
    )
@app.route("/view_redeemed_file/<int:file_id>")
def view_redeemed_file(file_id):
    cur = conn.cursor()
    cur.execute("SELECT file_data, file_name, file_type_id FROM redeemed_files WHERE file_id = %s", (file_id,))
    file = cur.fetchone()
    cur.close()

    if file:
        file_data, file_name, file_type_id = file
        # Guess MIME type from extension or use a mapping from your file_types table
        cur = conn.cursor()
        cur.execute("SELECT extension FROM file_types WHERE file_type_id = %s", (file_type_id,))
        result = cur.fetchone()
        cur.close()

        if result:
            extension = result[0].lower()
            mimetypes = {
                "pdf": "application/pdf",
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "png": "image/png",
                "gif": "image/gif"
            }
            mimetype = mimetypes.get(extension, "application/octet-stream")
        else:
            mimetype = "application/octet-stream"

        return Response(file_data, mimetype=mimetype, headers={
            "Content-Disposition": f"inline; filename={file_name}"
        })
    else:
        return "File not found", 404

import io
import mimetypes

@app.route('/view-file/<int:file_id>')
def view_file(file_id):
    cur = conn.cursor()
    query = """
        SELECT cf.file_name, cf.file_data, ft.type
        FROM client_files cf
        JOIN file_types ft ON cf.file_type_id = ft.file_type_id
        WHERE cf.file_id = %s
    """
    cur.execute(query, (file_id,))
    result = cur.fetchone()
    cur.close()

    if not result:
        return abort(404, description="File not found")

    file_name, file_data, file_type = result

    # Determine MIME type from extension
    extension = file_name.rsplit(".", 1)[-1].lower()
    mime_type = mimetypes.types_map.get(f".{extension}", "application/octet-stream")

    return send_file(
        io.BytesIO(file_data),
        mimetype=mime_type,
        download_name=file_name,
        as_attachment=False  # 👈 Display inline (for images, PDFs, etc.)
    )

@app.route('/delete-client/<int:client_id>', methods=['DELETE'])
def delete_client(client_id):
    try:
        cur = conn.cursor()

        # Delete from compliance first (due to foreign key constraints)
        cur.execute('DELETE FROM client_compliance WHERE "Client_id" = %s', (client_id,))
        cur.execute('DELETE FROM client_data WHERE "Client_id" = %s', (client_id,))
        log_action("Delete", client_id, f"Deleted client with ID {client_id}")

        conn.commit()
        cur.close()

        return jsonify({"message": "Client deleted successfully."}), 200

    except Exception as e:
        conn.rollback()
        print("Delete failed:", e)
        return jsonify({"error": "Failed to delete client"}), 500
@app.route("/log_page")
def view_log():
    print("✅ log_page route called")
    cur = conn.cursor()
    cur.execute("SELECT * FROM audit_log ORDER BY timestamp DESC")
    logs = cur.fetchall()
    colnames = [desc[0] for desc in cur.description]
    cur.close()

    print("DEBUG - columns:", colnames)
    print("DEBUG - rows:", logs[:1])  # Show first row

    return render_template("log.html", rows=logs, columns=colnames)
import re
@app.route("/submit_task", methods=["POST"]) 
def submit_task():
    try:
        print("📨 Form data received:")
        for k, v in request.form.items():
            print(f"{k}: {v}")
        print("📎 Documents:", request.form.getlist("documents[]"))
        
        cur = conn.cursor()
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'tasks'")
        db_columns = [row[0] for row in cur.fetchall()]
        print("📋 Columns in 'tasks' table:", db_columns)
        client_name = request.form.get("client_name")
        rm = request.form.get("rm")
        doc_link = request.form.get("doc_link")
        ema_ima = request.form.get("ema_ima")
        assigned_to = request.form.get("assigned_to")
        comments = request.form.get("comments")
        email = session.get("user_email", "")
        username = email.split("@")[0]  # take part before @
        username = re.sub(r'\W+', '', username)  # remove all non-alphanumeric characters
        assigned_from = username 

        documents = request.form.getlist("documents[]")

        cur = conn.cursor()
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'tasks'")
        print("🔍 Columns in 'tasks':")
        for col in cur.fetchall():
            print(col)
        cur.execute("""
            INSERT INTO tasks (
                client_name, rm, documents, doc_link, ema_ima,assigned_to, assigned_from, comments
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            client_name, rm, documents, doc_link, ema_ima,
            assigned_to, assigned_from, comments
        ))

        conn.commit()
        cur.close()
        return redirect("/to_do")

    except Exception as e:
        print("❌ Error inserting task:")
        traceback.print_exc()  # shows detailed error line
        return "Error inserting task", 500

@app.route("/api/stats_by/<field>")
def stats_by_field(field):
    cur = conn.cursor()

    if field == "age_group":
        # Age buckets: 0–10, 11–20, ..., 91–100
        cur.execute("""
            SELECT
                CASE
                    WHEN "Age" BETWEEN 0 AND 10 THEN '0–10'
                    WHEN "Age" BETWEEN 11 AND 20 THEN '11–20'
                    WHEN "Age" BETWEEN 21 AND 30 THEN '21–30'
                    WHEN "Age" BETWEEN 31 AND 40 THEN '31–40'
                    WHEN "Age" BETWEEN 41 AND 50 THEN '41–50'
                    WHEN "Age" BETWEEN 51 AND 60 THEN '51–60'
                    WHEN "Age" BETWEEN 61 AND 70 THEN '61–70'
                    WHEN "Age" BETWEEN 71 AND 80 THEN '71–80'
                    WHEN "Age" BETWEEN 81 AND 90 THEN '81–90'
                    WHEN "Age" BETWEEN 91 AND 100 THEN '91–100'
                    ELSE 'Unknown'
                END AS age_group,
                COUNT(*) as count
            FROM client_data
            GROUP BY age_group
            ORDER BY age_group;
        """)
    else:
        # Default handling
        if field not in [
            "Nationality", "Employment_status", "Pep",
            "Risk_rating", "Relationship_Manager",
            "Service_type", "Client_type"
        ]:
            return jsonify({"error": "Invalid field"}), 400

        # Choose correct table
        table = "client_compliance" if field in ["Risk_rating", "Relationship_Manager", "Service_type", "Client_type", "Pep"] else "client_data"
        query = f'SELECT "{field}" AS label, COUNT(*) FROM {table} GROUP BY "{field}" ORDER BY COUNT(*) DESC;'
        cur.execute(query)

    rows = cur.fetchall()
    cur.close()

    results = []
    for row in rows:
        label = row[0] if row[0] is not None else "Unknown"
        results.append({"label": label, "count": row[1]})

    return jsonify(results)

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "remuspostgres@gmail.com"
app.config["MAIL_PASSWORD"] = "xtch ldrm yger vhzb"  # from App Passwords
app.config["MAIL_DEFAULT_SENDER"] = "remuseah@gmail.com"

mail = Mail(app)
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        if not email or not password:
            return render_template("signup.html", error="Please fill all fields")

        hashed_pw = generate_password_hash(password)
        token = secrets.token_urlsafe(16)

        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO users (email, password_hash, is_verified, verification_token)
                VALUES (%s, %s, FALSE, %s)
            """, (email, hashed_pw, token))
            conn.commit()
            cur.close()

            # Send email
            send_verification_email(email, token)

            return render_template("signup.html", message="Check your email to verify your account.")
        except psycopg2.Error as e:
            conn.rollback()
            return render_template("signup.html", error="Email already in use or invalid.")

    return render_template("signup.html")
@app.route("/test_email")
def test_email():
    msg = Message("Test", recipients=["Latias1463@gmail.com"], body="This is a test")
    mail.send(msg)
    return "Email sent!"
from flask import Response
@app.route("/verify/<token>")
def verify_email(token):
    print("🔍 Received token:", token)

    cur = conn.cursor()
    cur.execute("""
        SELECT email FROM users
        WHERE verification_token = %s AND is_verified = FALSE
    """, (token,))
    result = cur.fetchone()
    print("✅ DB result:", result)

    if result:
        cur.execute("""
            UPDATE users
            SET is_verified = TRUE, verification_token = NULL
            WHERE verification_token = %s
        """, (token,))
        conn.commit()
        cur.close()
        return Response("<h3>✅ Email verified successfully. You may now <a href='/login'>log in</a>.</h3>", mimetype='text/html')
    else:
        cur.close()
        return Response("<h3>❌ Invalid or expired verification link.</h3>", mimetype='text/html')

from flask_mail import Message

def send_verification_email(email, token):
    verify_link = f"https://client-interface-24am.onrender.com/verify/{token}"
    subject = "Verify Your Email"

    html = f"""
    <html>
    <body>
        <p>Hello,</p>
        <p>Please verify your email by clicking the button below:</p>
        <p><a href="{verify_link}" style="padding:10px 15px;background-color:#4CAF50;color:white;text-decoration:none;">Verify Email</a></p>
        <p>If the button doesn't work, copy this link into your browser:</p>
        <p>{verify_link}</p>
        <p>Thanks!</p>
    </body>
    </html>
    """

    # ✅ Send only the HTML version
    msg = Message(subject=subject, recipients=[email], html=html)
    mail.send(msg)


from werkzeug.security import check_password_hash

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        try:
            cur = conn.cursor()
            cur.execute("SELECT id, password_hash, is_verified FROM users WHERE email = %s", (email,))
            result = cur.fetchone()
            cur.close()
        except Exception as e:
            conn.rollback()  # 🛠️ This clears the failed transaction state
            print("❌ Login DB error:", e)
            return render_template("login.html", error="Database error. Please try again.")

        if result:
            user_id, password_hash, is_verified = result
            if not is_verified:
                return render_template("login.html", error="Please verify your email first.")
            if check_password_hash(password_hash, password):
                session["user_id"] = user_id
                session["user_email"] = email
                return redirect("/main_page")
            else:
                return render_template("login.html", error="Incorrect password.")
        else:
            return render_template("login.html", error="Email not found.")
    
    return render_template("login.html")
@app.route("/update_task_status/<int:task_id>", methods=["POST"])
def update_task_status(task_id):
    try:
        new_status = request.json.get("status")  # "Complete" or "Incomplete"
        print(f"🔁 Updating task {task_id} to {new_status}")  # 🔍
        if new_status not in ["Complete", "Incomplete"]:
            return {"error": "Invalid status"}, 400

        cursor = conn.cursor()
        cursor.execute("""
            UPDATE tasks SET completion_status = %s WHERE id = %s
        """, (new_status, task_id))
        conn.commit()
        cursor.close()
        return {"success": True}, 200
    except Exception as e:
        print("❌ Error updating task status:", e)
        return {"error": str(e)}, 500

@app.route('/redeem_single', methods=['POST'])
def redeem_single():
    client_id = request.form.get('client_id')

    if not client_id:
        return "No client_id provided", 400

    cur = conn.cursor()

    # 1. Fetch data from JOINed client_data + client_compliance
    cur.execute('''
        SELECT 
            d."Client_id", d."Name", d."Nationality", d."Residency_address", d."Contact_number",
            d."Date_of_birth", d."Ic_number", d."Age", d."Client_profile", d."Employment_status", d."Email_address",
            c."Onboarded_date", c."Risk_rating", c."Relationship_Manager", c."Service_type", 
            c."Client_type", c."Pep"
        FROM client_data d
        JOIN client_compliance c ON d."Client_id" = c."Client_id"
        WHERE d."Client_id" = %s
    ''', (client_id,))
    
    row = cur.fetchone()

    if not row:
        cur.close()
        return "Client not found", 404

    # 2. Columns (must match SELECT order)
    redeemed_columns = [
        "Client_id", "Name", "Nationality", "Residency_address", "Contact_number",
        "Date_of_birth", "Ic_number", "Age", "Client_profile", "Employment_status", "Email_address",
        "Onboarded_date", "Risk_rating", "Relationship_Manager", "Service_type",
        "Client_type", "Pep"
    ]

    # 3. Build INSERT into `redeemed`
    col_placeholders = ', '.join(col.lower() for col in redeemed_columns)
    placeholders = ', '.join(['%s'] * len(redeemed_columns))
    insert_sql = f'''
        INSERT INTO redeemed ({col_placeholders})
        VALUES ({placeholders})
        ON CONFLICT (client_id) DO NOTHING
    '''

    # 4. Prepare values
    col_to_val = {col.lower(): val for col, val in zip(redeemed_columns, row)}
    values = [col_to_val[col.lower()] for col in redeemed_columns]

    # 5. Insert into redeemed
    cur.execute(insert_sql, values)

    # 6. Copy files to redeemed_files
    cur.execute('''
        INSERT INTO redeemed_files (client_id, file_type_id, file_name, file_data, uploaded_at)
        SELECT client_id, file_type_id, file_name, file_data, uploaded_at
        FROM client_files
        WHERE client_id = %s
    ''', (client_id,))

    # 7. Delete from original tables
    cur.execute('DELETE FROM client_compliance WHERE "Client_id" = %s', (client_id,))
    cur.execute('DELETE FROM client_data WHERE "Client_id" = %s', (client_id,))

    conn.commit()
    cur.close()

    flash("Client successfully redeemed and removed.", "success")
    return redirect(url_for('view_table'))  # or 'redeemed_view' if that's more relevant
@app.route('/get-address-from-postal', methods=['POST'])
def get_address_from_postal():
    data = request.get_json()
    print("Received data:", data)

    postal_code = data.get('postal_code')
    if not postal_code:
        return jsonify({'error': 'Postal code is required'}), 400

    try:
        print("Sending request to OneMap public API...")
        url = f"https://www.onemap.gov.sg/api/common/elastic/search?searchVal={postal_code}&returnGeom=Y&getAddrDetails=Y&pageNum=1"
        response = requests.get(url)

        print("Response status:", response.status_code)
        print("Response text:", response.text)  # <- This will help us debug non-JSON responses

        # Check if response is JSON before parsing
        if response.headers.get("Content-Type", "").startswith("application/json"):
            return jsonify(response.json())
        else:
            return jsonify({
                "error": "Response was not JSON",
                "status_code": response.status_code,
                "raw_response": response.text
            }), 500

    except Exception as e:
        print("Error in lookup:", e)
        return jsonify({"error": str(e)}), 500
@app.route("/add-account-and-value", methods=["POST"])
def add_account_and_value():
    try:
        data = request.get_json()
        client_id = int(data["client_id"])
        account_name = data["account_name"]
        account_number = data["account_number"]
        amount = float(data["amount"])
        month = data["month"]

        cursor = conn.cursor()

        # Check if client has existing account
        cursor.execute("SELECT account_id FROM client_accounts WHERE client_id = %s", (client_id,))
        result = cursor.fetchone()

        if result:
            account_id = result[0]
        else:
            # Get next available account_id
            cursor.execute("SELECT COALESCE(MAX(account_id), 0) + 1 FROM client_accounts")
            account_id = cursor.fetchone()[0]

            cursor.execute("""
                INSERT INTO client_accounts (account_id, client_id, account_name,account_number)
                VALUES (%s, %s, %s, %s)
            """, (account_id, client_id, account_name,account_number))
        
        # Insert into account_monthly_values
        amount = float(data["amount"])
        month = data["month"] + "-01"  # 🔧 Fix here

        cursor.execute("""
            INSERT INTO account_monthly_values (account_id, amount, month)
            VALUES (%s, %s, %s)
        """, (account_id, amount, month))

        conn.commit()
        cursor.close()
        return jsonify({"message": "✅ Account and value added successfully."})

    except Exception as e:
        conn.rollback()
        print("❌ Error in /add-account-and-value:", e)  # Log the actual error
        return jsonify({"error": str(e)}), 500

@app.route("/get-client-name/<int:client_id>")
def get_client_name(client_id):
    cursor = conn.cursor()

    # Get client name
    cursor.execute('SELECT "Name" FROM client_data WHERE "Client_id" = %s', (client_id,))
    name_row = cursor.fetchone()
    name = name_row[0] if name_row else None

    # Check for existing account_id
    cursor.execute("SELECT account_id FROM client_accounts WHERE client_id = %s", (client_id,))
    acc_row = cursor.fetchone()

    if acc_row:
        account_id = acc_row[0]
    else:
        cursor.execute("SELECT COALESCE(MAX(account_id), 0) + 1 FROM client_accounts")
        account_id = cursor.fetchone()[0]

    cursor.close()

    return jsonify({"name": name, "account_id": account_id})
@app.route("/get-account-values-by-client/<int:client_id>")
def get_account_values_by_client(client_id):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.account_id, a.account_name, v.month, v.amount
        FROM client_accounts a
        JOIN account_monthly_values v ON a.account_id = v.account_id
        WHERE a.client_id = %s
        ORDER BY v.month DESC
    """, (client_id,))
    results = cursor.fetchall()
    cursor.close()

    return jsonify([
        {
            "account_id": row[0],
            "account_name": row[1],
            "month": row[2],
            "amount": row[3]
        }
        for row in results
    ])

@app.route("/get-available-months")
def get_available_months():
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT month FROM account_monthly_values ORDER BY month DESC")
    months = [r[0] for r in cur.fetchall()]
    cur.close()
    return jsonify(months)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Get port from environment
    app.run(host="0.0.0.0", port=port, debug=True)