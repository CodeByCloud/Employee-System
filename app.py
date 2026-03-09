from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json, os

app = Flask(__name__)
app.secret_key = "change_this_secret_key"

# ==========================
#  PATHS TO JSON DATABASES
# ==========================
EMP_FILE = "data/employees.json"
USERS_FILE = "data/users.json"


# ==========================
#  GENERIC JSON LOAD/SAVE
# ==========================
def load_json(path):
    """Loads JSON file. If file doesn't exist, create an empty list."""
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump([], f)
    with open(path, "r") as f:
        return json.load(f)


def save_json(path, data):
    """Saves Python list/dict into JSON file."""
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


# ==========================
#  HOME REDIRECT
# ==========================
@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("employees_page"))
    return redirect(url_for("login"))


# ==========================
#  SIGNUP
# ==========================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        users = load_json(USERS_FILE)

        # Check if user already exists
        if any(u["username"] == username for u in users):
            return render_template("signup.html", error="Username already exists. Please choose another.", hide_logout=True), 400

        # Save new user
        users.append({"username": username, "password": password})
        save_json(USERS_FILE, users)

        return redirect(url_for("login"))

    return render_template("signup.html", hide_logout=True)


# ==========================
#  LOGIN
# ==========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        users = load_json(USERS_FILE)

        # Validate credentials
        user = next((u for u in users if u["username"] == username and u["password"] == password), None)

        if user:
            session["user"] = user
            return redirect(url_for("employees_page"))

        return render_template("login.html", error="Invalid username or password.", hide_logout=True), 401

    return render_template("login.html", hide_logout=True)


# ==========================
#  LOGOUT
# ==========================
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


# ==========================
#  LOGIN REQUIRED DECORATOR
# ==========================
def require_login(func):
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapper


# ==========================
#  EMPLOYEES PAGE (UI)
# ==========================
@app.route("/employees")
@require_login
def employees_page():
    """Loads the UI page. Data is fetched via API using fetch()."""
    return render_template("employees.html")


# ==========================
#  API: GET EMPLOYEES
# ==========================
@app.route("/api/employees", methods=["GET"])
@require_login
def get_employees():
    employees = load_json(EMP_FILE)
    return jsonify(employees)


# ==========================
#  API: ADD EMPLOYEE
# ==========================
@app.route("/api/employees", methods=["POST"])
@require_login
def add_employee():
    data = request.get_json()
    employees = load_json(EMP_FILE)

    # Duplicate email check
    if any(e["email"] == data["email"] for e in employees):
        return jsonify({"error": "Email already exists"}), 400

    # Duplicate ID check
    if any(e["id"] == data["id"] for e in employees):
        return jsonify({"error": "ID already exists"}), 400

    new_emp = {
        "id": data["id"],
        "name": data["name"],
        "email": data["email"],
        "position": data["position"]
    }

    employees.append(new_emp)
    save_json(EMP_FILE, employees)

    return jsonify(new_emp), 201


# ==========================
#  API: DELETE EMPLOYEE
# ==========================
@app.route("/api/employees/<int:emp_id>", methods=["DELETE"])
@require_login
def delete_employee(emp_id):
    employees = load_json(EMP_FILE)
    employees = [e for e in employees if e["id"] != emp_id]
    save_json(EMP_FILE, employees)
    return "", 204


# ==========================
#  API: EDIT EMPLOYEE
# ==========================
@app.route("/api/employees/<int:emp_id>", methods=["PUT"])
@require_login
def edit_employee(emp_id):
    data = request.get_json()
    employees = load_json(EMP_FILE)

    for emp in employees:
        if emp["id"] == emp_id:

            # Check duplicate email (except same employee)
            if any(e["email"] == data["email"] and e["id"] != emp_id for e in employees):
                return jsonify({"error": "Email already exists"}), 400

            emp["name"] = data["name"]
            emp["email"] = data["email"]
            emp["position"] = data["position"]

            save_json(EMP_FILE, employees)
            return jsonify(emp), 200

    return jsonify({"error": "Employee not found"}), 404


# ==========================
#  RUN APP
# ==========================
if __name__ == "__main__":
    app.run(debug=True)
