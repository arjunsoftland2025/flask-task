from flask import Flask, render_template, request, jsonify
import json
import re

app = Flask(__name__)


class StudentManager:
    def __init__(self, data):
        self.data = data

    def find_student(self, search_value, by_id=False):
        if by_id:
            return next((student for student in self.data["students"] if student["id"] == search_value), None)
        return next((student for student in self.data["students"] if student["name"].lower() == search_value.lower()), None)

def name_regex_check(input_str):
    return bool(re.match(r'^[A-Za-z]{3,}(?: [A-Za-z]{1,})*$', input_str))

def class_check(input_class):
    return bool(re.match(r'^(1[0-2]|[1-9])[A-Z]$', input_class))

def get_valid_number(prompt_number, is_int=False):
    while True:
        try:
            user_input = input(prompt_number).strip()
            if is_int:
                return int(user_input)
            return float(user_input)
        except ValueError:
            print("Please enter a valid number.")

def get_valid_input(prompt_input, validation_func,):
    while True:
        user_input = input(prompt_input).strip()
        if validation_func(user_input):
            return user_input
        return None


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

@app.route("/add_class_page")
def add_class_page():
    return render_template("add_class_page.html")

@app.route('/add_class', methods=['POST'])
def add_class():
    data = load_data()
    req_data = request.json
    errors = []
    class_name = req_data.get('class_name')
    subjects = req_data.get('subjects')

    if not class_name or not subjects:
        errors.append("Class name and subjects are required")
    
    class_data = next((cls for cls in data["classes"] if cls["class_name"] == class_name), None)
    if class_data:
        errors.append("Class not found")
    
    if not class_check(class_name):
        errors.append("Invalid class format. Example: '10A'.")
        
    if errors:
        return jsonify({"error": "<br>".join(errors)}), 400
    
    new_class = {'class_name': class_name, 'subjects': subjects}

    data["classes"].append(new_class)
    save_data(data)

    return jsonify({'message': 'Class added successfully!', "classes": new_class})

@app.route("/add_student", methods=["POST"])
def add_student():
    data = load_data()
    req_data = request.json
    errors = []
    student_id = req_data.get("id")
    student_name = req_data.get("name")
    student_class = req_data.get("class")
    try:
        student_id = int(student_id)
    except (ValueError, TypeError):
        errors.append("Student ID must be a valid number.")
        
    if any(student["id"] == student_id for student in data["students"]):
        errors.append("A student with this ID already exists.")

    if not name_regex_check(student_name):
        errors.append("Invalid name format. Name must have at least 3 letters.")

    if not class_check(student_class):
        errors.append("Invalid class format. Example: '10A'.")

    class_data = next((cls for cls in data["classes"] if cls["class_name"] == student_class), None)
    if not class_data:
        errors.append("Class not found.")

    subjects = {}
    for subject in class_data["subjects"]:
        sem1_marks = req_data.get("subjects", {}).get(subject, {}).get("sem1", 0)
        sem2_marks = req_data.get("subjects", {}).get(subject, {}).get("sem2", 0)

        try:
            sem1_marks = int(sem1_marks)
            sem2_marks = int(sem2_marks)
        except ValueError:
            errors.append(f"Marks for {subject} must be numbers.")

        if not (0 <= sem1_marks <= 100):
            errors.append(f"{subject} Sem 1 marks must be between 0 and 100.")
        if not (0 <= sem2_marks <= 100):
            errors.append(f"{subject} Sem 2 marks must be between 0 and 100.")

        subjects[subject] = {"sem1": sem1_marks, "sem2": sem2_marks}

    if errors:
        return jsonify({"error": "<br>".join(errors)}), 400

    new_student = {
        "id": student_id,
        "name": student_name,
        "class": student_class,
        "subjects": subjects
    }

    data["students"].append(new_student)
    save_data(data)

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
    
    if not class_check(class_name):
        return jsonify({"error": "Invalid class format. Use format like '10A'."}), 400
    
    class_data = next((cls for cls in data["classes"] if cls["class_name"] == class_name), None)
    if not class_data:
        return jsonify({"error": "Class not found"}), 404

    students_in_class = [student for student in data["students"] if student["class"] == class_name]

    students_with_marks = []
    for student in students_in_class:
        students_with_marks.append({
            "id": student["id"],
            "name": student["name"],
            "subjects": student["subjects"]
        })

    return jsonify({
        "class_name": class_data["class_name"],
        "subjects": class_data["subjects"],
        "students": students_with_marks
    })

@app.route("/average_of_student")
def average_of_student():
    return render_template("average_of_student.html")

@app.route('/calculate_average', methods=['GET'])
def calculate_average():
    student_name = request.args.get("name", "").strip()
    subject_name = request.args.get("subject", "").strip()
    data = load_data()

    student = next((student for student in data["students"] if student["name"].lower() == student_name.lower()), None)
    if not student:
        return jsonify({"error": "Student not found"}), 404

    subject_marks = student["subjects"].get(subject_name)
    if not subject_marks:
        return jsonify({"error": f"{subject_name} marks not found for {student_name}"}), 404

    sem1 = subject_marks.get("sem1", 0)
    sem2 = subject_marks.get("sem2", 0)
    average = (sem1 + sem2) / 2

    return jsonify({
        "student_name": student["name"],
        "subject": subject_name,
        "sem1": sem1,
        "sem2": sem2,
        "average": round(average, 2)
    })

@app.route("/total_average_of_students")
def total_average_of_students():
    return render_template("total_average_of_students.html")

@app.route('/calculate_total_average', methods=['GET'])
def calculate_total_average():
    student_name = request.args.get("name", "").strip()
    data = load_data()

    student = next((student for student in data["students"] if student["name"].lower() == student_name.lower()), None)
    if not student:
        return jsonify({"error": "Student not found"}), 404

    total_marks = 0
    subject_count = 0

    for subject, marks in student["subjects"].items():
        sem1 = marks.get("sem1", 0)
        sem2 = marks.get("sem2", 0)
        total_marks += sem1 + sem2
        subject_count += 2

    if subject_count == 0:
        return jsonify({"error": "No subjects found for the student"}), 404

    total_average = total_marks / subject_count

    return jsonify({
        "student_name": student["name"],
        "total_average": round(total_average, 2)
    })


if __name__ == "__main__":
    app.run(debug=True)