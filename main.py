from flask import Flask
import index
import scheduler

app = Flask(__name__)

@app.route("/generate")
def home():
    a = index.data(academic_year_id=1, department_id=2)
    if a == 1:
        scheduler.main()
    return "success"

if __name__ == "__main__":
    app.run(debug=True)