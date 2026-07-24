from flask import Flask, render_template, request, redirect, flash
from database import (
    init_database,
    get_all_pages,
    add_page,
    delete_page
)

app = Flask(__name__)
app.secret_key = "nexora_ai_secret"

# Initialize Database
init_database()


# --------------------------
# Login
# --------------------------

@app.route("/")
def login():
    return render_template("login.html")


# --------------------------
# Dashboard
# --------------------------

@app.route("/dashboard")
def dashboard():

    pages = get_all_pages()

    return render_template(
        "index.html",
        page_count=len(pages)
    )


# --------------------------
# Facebook Pages Manager
# --------------------------

@app.route("/facebook")
def facebook():

    pages = get_all_pages()

    return render_template(
        "facebook.html",
        pages=pages
    )


# --------------------------
# Add Facebook Page
# --------------------------

@app.route("/facebook/add", methods=["POST"])
def facebook_add():

    page_name = request.form.get("page_name", "").strip()

    page_id = request.form.get("page_id", "").strip()

    access_token = request.form.get("access_token", "").strip()

    niche = request.form.get("niche", "").strip()

    if not page_name or not page_id or not access_token:

        flash("Please fill all required fields.", "danger")

        return redirect("/facebook")

    success, message = add_page(
        page_name,
        page_id,
        access_token,
        niche
    )

    if success:

        flash(message, "success")

    else:

        flash(message, "danger")

    return redirect("/facebook")


# --------------------------
# Delete Facebook Page
# --------------------------

@app.route("/facebook/delete/<page_id>")
def facebook_delete(page_id):

    delete_page(page_id)

    flash("Facebook Page deleted successfully.", "success")

    return redirect("/facebook")


# --------------------------
# Run App
# --------------------------

if __name__ == "__main__":
    app.run(debug=True)