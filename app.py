from flask import Flask, render_template, request, jsonify
import json

app = Flask(__name__)


def load_data():
    with open("data.json", "r") as file:
        return json.load(file)


def save_data(data):
    with open("data.json", "w") as file:
        json.dump(data, file, indent=4)
        
@app.route("/")
def home():
    return render_template("index.html")
        
@app.route("/get_classes", methods=["GET"])
def get_classes():
    data = load_data()
    class_list = [{"class_name": c["class_name"]} for c in data["classes"]]
    return jsonify({"classes": class_list})

@app.route("/get_subjects/<class_name>", methods=["GET"])
def get_subjects(class_name):
    data = load_data()
    class_data = next((c for c in data["classes"] if c["class_name"] == class_name), None)

    if not class_data:
        return jsonify({"error": "Class not found"}), 400

    return jsonify({"subjects": class_data["subjects"]})

@app.route("/add_student", methods=["POST"])
def add_student():
    data = load_data()
    
    req_data = request.json
    student_name = req_data.get("name")
    student_class = req_data.get("class")


    class_data = next((c for c in data["classes"] if c["class_name"] == student_class), None)

    if not class_data:
        return jsonify({"error": "Class not found"}), 400

    subjects = {subj: {"sem1": 0, "sem2": 0} for subj in class_data["subjects"]}

    new_student = {
        "id": len(data["students"]) + 1,
        "name": student_name,
        "class": student_class,
        "subjects": subjects
    }
    
    data["students"].append(new_student)
    save_data(data)

    return jsonify({"message": "Student added successfully", "student": new_student})

if __name__ == "__main__":
    app.run(debug=True)
