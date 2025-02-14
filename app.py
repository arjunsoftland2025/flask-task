from flask import Flask, render_template, request, jsonify
import json

app = Flask(__name__)

def load_data():
    with open("data.json", "r") as file:
        return json.load(file)

def save_data(data):
    with open("data.json", "w") as file:
        json.dump(data, file, indent=4)
        
@app.route('/')
def home():
    return render_template('index.html')
        
@app.route('/add_students_page')
def add_students_page():
    return render_template("add_student.html")

@app.route('/list_of_all_students')
def list_of_all_students():
    data = load_data()
    return render_template('list_of_all_students.html', students=data['students'])
        
@app.route("/get_classes", methods=["GET"])
def get_classes():
    data = load_data()
    class_list = [{"class_name": class_name_selection["class_name"]} for class_name_selection in data["classes"]]
    return jsonify({"classes": class_list})

@app.route("/get_subjects/<class_name>", methods=["GET"])
def get_subjects(class_name):
    data = load_data()
    
    class_data = next((class_name_match for class_name_match in data["classes"] if class_name_match["class_name"] == class_name), None)
    if not class_data:
        return jsonify({"error": "Class not found"}), 400

    return jsonify({"subjects": class_data["subjects"]})

@app.route("/add_student", methods=["POST"])
def add_student():
    data = load_data()
    req_data = request.json
    student_name = req_data.get("name")
    student_class = req_data.get("class")

    class_data = next((collect_class for collect_class in data["classes"] if collect_class["class_name"] == student_class), None)
    
    if not class_data:
        return jsonify({"error": "Class not found"}), 400

    subjects = {}
    for subject in class_data["subjects"]:
        sem1_marks = req_data.get("subjects", {}).get(subject, {}).get("sem1", 0)
        sem2_marks = req_data.get("subjects", {}).get(subject, {}).get("sem2", 0)
        subjects[subject] = {"sem1": sem1_marks, "sem2": sem2_marks}
    
    new_student = {
        "id": len(data["students"]) + 1,
        "name": student_name,
        "class": student_class,
        "subjects": subjects
    }
    
    data["students"].append(new_student)
    save_data(data)
    print("sudent updated")
    return jsonify({"message": "Student added successfully", "student": new_student})

if __name__ == "__main__":
    app.run(debug=True)