from flask import Flask
import index
import scheduler

app = Flask(__name__)

@app.route("/generate/department/<id>")
def home(id):
    a = index.data(department_id=id)
    if a == 1:
        scheduler.main()
    return "success"

if __name__ == "__main__":
    app.run(debug=True)