from flask import Flask,render_template,request,redirect,flash,session
from functools import wraps
from database import init_database,get_all_pages,add_page,delete_page,verify_user,save_ai_post,get_ai_posts,count_ai_posts

app=Flask(__name__)
app.secret_key="nexora_ai_secret"
init_database()
def login_required(f):
 from functools import wraps
 @wraps(f)
 def w(*a,**k):
  if "user" not in session:return redirect("/")
  return f(*a,**k)
 return w
@app.route("/",methods=["GET","POST"])
def login():
 if request.method=="POST":
  u=verify_user(request.form.get("email",""),request.form.get("password",""))
  if u:
   session["user"]=u["email"];session["name"]=u["full_name"];return redirect("/dashboard")
  flash("Invalid email or password.","danger")
 return render_template("login.html")
@app.route("/logout")
def logout(): session.clear();return redirect("/")
@app.route("/dashboard")
@login_required
def dashboard(): return render_template("index.html",page_count=len(get_all_pages()),ai_count=count_ai_posts())
@app.route("/facebook")
@login_required
def facebook(): return render_template("facebook.html",pages=get_all_pages())
@app.route("/facebook/add",methods=["POST"])
@login_required
def facebook_add():
 ok,msg=add_page(request.form["page_name"],request.form["page_id"],request.form["access_token"],request.form.get("niche",""))
 flash(msg,"success" if ok else "danger");return redirect("/facebook")
@app.route("/facebook/delete/<page_id>")
@login_required
def facebook_delete(page_id): delete_page(page_id);return redirect("/facebook")
@app.route("/ai-generator")
@login_required
def ai_generator(): return render_template("ai_generator.html",generated=None)
@app.route("/ai-generator/generate",methods=["POST"])
@login_required
def generate():
 p=request.form.get("prompt","");plat=request.form.get("platform","Facebook");tone=request.form.get("tone","Professional");lang=request.form.get("language","English")
 g=f"Demo AI Post\n\nPlatform: {plat}\nTone: {tone}\nLanguage: {lang}\n\n{p}"
 save_ai_post(p,plat,tone,lang,g)
 return render_template("ai_generator.html",generated=g)
@app.route("/ai-history")
@login_required
def hist(): return {"posts":[dict(x) for x in get_ai_posts()]}
if __name__=="__main__": app.run(debug=True)
