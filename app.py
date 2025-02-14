from flask import Flask, render_template, request, jsonify
import json
import re

app = Flask(__name__)


class StudentManager:
    def __init__(self, data):
        self.data = data  # The entire data object (including students and classes)

    def find_student(self, search_value, by_id=False):
        """Find student by ID or Name."""
        # Search in the students data
        if by_id:
            return next((student for student in self.data["students"] if student["id"] == search_value), None)
        return next((student for student in self.data["students"] if student["name"].lower() == search_value.lower()), None)

def name_regex_check(input_str):
    return bool(re.match(r'^[A-Za-z]{3,}(?: [A-Za-z]{1,})*$', input_str))

def class_check(input_class):
    return bool(re.match(r'^(1[0-2]|[1-9])[A-Z]$', input_class))

def get_valid_number(prompt_number, is_int=False):
    """Prompt for a valid number (int or float)."""
    while True:
        try:
            user_input = input(prompt_number).strip()
            if is_int:
                return int(user_input)  # Parse as integer if is_int is True
            return float(user_input)  # Otherwise, parse as float
        except ValueError:
            print("Please enter a valid number.")

def get_valid_input(prompt_input, validation_func,):
    """Prompt for valid input based on the validation function."""
    while True:
        user_input = input(prompt_input).strip()
        if validation_func(user_input):  # Apply custom validation function
            return user_input
        return None  # Show error if validation fails


def load_data():
    with open("data.json", "r") as file:
        return json.load(file)

def save_data(data):
    with open("data.json", "w") as file:
        json.dump(data, file, indent=4)
        
@app.route('/')
def home():
    data = load_data()
    return render_template('index.html', students=data['students'])
        
@app.route('/add_students_page')
def add_students_page():
    return render_template("add_student.html")

@app.route('/search_students')
def search_students():
    return render_template('search_students.html')
        
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
    student_id = req_data.get("id")
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
        "id": student_id,
        "name": student_name,
        "class": student_class,
        "subjects": subjects
    }
    
    data["students"].append(new_student)
    save_data(data)
    print("sudent updated")
    return jsonify({"message": "Student added successfully", "student": new_student})


@app.route("/find_student", methods=["GET"])
def find_student_route():
    student_name = request.args.get("name", "").strip()
    data = load_data()

    student_manager = StudentManager(data)
    student = student_manager.find_student(student_name)

    if not student:
        return jsonify({"error": "Student not found"}), 404

    return jsonify({
        "id": student["id"],
        "name": student["name"],
        "class": student["class"],
        "subjects": student["subjects"]
    })
    
@app.route("/search_class")
def search_class():
    return render_template("search_class.html")

@app.route("/find_class", methods=["GET"])
def find_class_route():
    class_name = request.args.get("class_name", "").strip()
    data = load_data()

    class_data = next((cls for cls in data["classes"] if cls["class_name"] == class_name), None)
    if not class_data:
        return jsonify({"error": "Class not found"}), 404

    # Get students belonging to the class
    students_in_class = [student for student in data["students"] if student["class"] == class_name]

    return jsonify({
        "class_name": class_data["class_name"],
        "subjects": class_data["subjects"],
        "students": [{"id": s["id"], "name": s["name"]} for s in students_in_class]
    })


if __name__ == "__main__":
    app.run(debug=True)