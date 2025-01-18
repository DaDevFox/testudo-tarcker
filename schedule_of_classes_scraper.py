from bs4 import BeautifulSoup
from time import sleep
from csv import reader
import requests
import json


def is_time(s: str) -> bool:
    return s.count("am") + s.count("pm") == 2


class SectionTime:
    def __init__(self, days, time, building, room_number):
        self.days = days
        self.time = time
        self.building = building
        self.room_number = room_number

    def __str__(self):
        return f"\nDays: {self.days}\nTimes: {self.time}\nBuilding: {self.building}\nRoom number: {self.room_number}"

    def encode(self) -> dict:
        return {"days": self.days, "time": self.time, "building": self.building,
                "room_number": self.room_number}


class Section:
    def __init__(self, class_id, data_frame, approved_course_dict, location="f2f", credits=3, desc=""):
        self.class_id = class_id
        self.credits = credits
        self.location = location

        self.section_number = data_frame[0]
        self.description = desc

        self.teacher = data_frame[1]
        self.total_seats = int(data_frame[data_frame.index("(Total:") + 1].replace(",", ""))
        self.open_seats = int(data_frame[data_frame.index("Open:") + 1].replace(",", ""))
        self.wait_list = int(data_frame[data_frame.index("Waitlist:") + 1])

        self.times = []

        for x in range(len(data_frame)):
            if is_time(data_frame[x]):
                if data_frame[x+1] != "TBA":
                    day = "TBA"
                    time = data_frame[x]
                    building = "TBA"
                elif data_frame[x+1] == "ONLINE":
                    day = data_frame[x - 1]
                    time = data_frame[x]
                    building = "ONLINE"
                else:
                    day = data_frame[x - 1]
                    time = data_frame[x]
                    building = data_frame[x + 1]

                try:
                    room_number = data_frame[x + 2]
                except IndexError:
                    room_number = -1
                    print("Error when processing", x, class_id, data_frame)
                self.times += [SectionTime(day, time, building, room_number)]

        # self.times = []
        # Approved_course_dict
        self.prerequisite = approved_course_dict["Prerequisite"]
        self.formerly = approved_course_dict["Formerly"]
        self.restriction = approved_course_dict["Restriction"]

        for line in data_frame:
            if "restricted" in line:
                self.restriction += f", {line}"

        self.credit_only_granted_for = approved_course_dict["Credit only granted for"]
        self.additional_information = approved_course_dict["Additional information"]

    def __str__(self):
        nl = "\n"
        return (f"{self.class_id} section: {self.section_number}\n"
                f"Credits: {self.credits}\n"
                f"Location: {self.location}\n"
                f"Prerequisite: {self.prerequisite}\n"
                f"Restriction: {self.restriction}\n"
                f"Description: {self.description}\n"
                f"Teacher: {self.teacher}\n"
                f"Seats: {self.total_seats}\n"
                f"Open seats: {self.total_seats}\n"
                f"Wait list: {self.wait_list}\n"
                f"Times: \n{nl.join(map(str, self.times))}")

    def is_open(self) -> bool:
        return self.open_seats >= 1

    def has_restriction(self) -> bool:
        return len(self.restriction) >= 2

    def json_encoding(self):
        return {"class_id": self.class_id,
                "section_number": self.section_number,
                "credits": self.credits,
                "location": self.location,
                "prerequisites": self.prerequisite,
                "restriction": self.restriction,
                "description": self.description,
                "teacher": self.teacher,
                "total_seats": self.total_seats,
                "open_seats": self.total_seats,
                "wait_list": self.wait_list,
                "times": [time.encode() for time in self.times]}


class SectionEncoder(json.JSONEncoder):
    def default(self, obj: Section) -> dict:
        return {"class_id": obj.class_id,
                "section_number": obj.section_number,
                "teacher": obj.teacher,
                "total_seats": obj.total_seats,
                "open_seats": obj.open_seats,
                "wait_list": obj.wait_list,
                "times": [time.encode() for time in obj.times]}


def url_format(title: str) -> str:
    return f"https://app.testudo.umd.edu/soc/search?courseId={title}&sectionId=&termId=202401&_openSectionsOnly=on&creditCompare=%3E%3D&credits=0.0&courseLevelFilter=ALL&instructor=&_facetoface=on&_blended=on&_online=on&courseStartCompare=&courseStartHour=&courseStartMin=&courseStartAM=&courseEndHour=&courseEndMin=&courseEndAM=&teachingCenter=ALL&_classDay1=on&_classDay2=on&_classDay3=on&_classDay4=on&_classDay5=on"


def format_section_info(text):
    divs = ['Prerequisite:', "Formerly:", 'Restriction:', 'Credit only granted for:', 'Additional information:', "Cross-listed with:"]

    div_indexes = []
    for div in divs:
        if div in text:
            div_indexes += [(div, text.index(div))]

    div_indexes.sort(key=lambda x: x[1])
    div_indexes += [("", len(text))]

    approved_course_dict = dict()

    for x in range(len(div_indexes) - 1):
        div_value = div_indexes[x][0][:-1]
        div_index = div_indexes[x][1]
        next_div_index = div_indexes[x + 1][1]

        approved_course_dict[div_value] = text[div_index + len(div_value) + 1: next_div_index].strip()

    # sets all un-included divs to empty strings
    for div in divs:
        if div[:-1] not in approved_course_dict.keys():
            approved_course_dict[div[:-1]] = ""

    assert len(divs) == len(approved_course_dict.keys())

    return approved_course_dict


def get_sections(class_id: str) -> list[Section]:
    approved_course_dict = None

    # Make a GET request to the website
    response = requests.get(url_format(class_id))

    # print(response.content)
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, "html.parser")

    sections = []
    description = ""
    divs = ['Prerequisite:', "Formerly:", 'Restriction:', 'Credit only granted for:', 'Additional information:', "Cross-listed with:"]

    for element in soup.find_all("div", class_="approved-course-text"):
        temp = [line.strip() for line in element.get_text().splitlines() if line.strip()][0]
        if any(div in temp for div in divs):
            approved_course_dict = format_section_info(temp)
        else:
            description = temp

    if approved_course_dict is None:
        print(f"Warning: no approved course dict made for {class_id}")
        approved_course_dict = {div[:-1]: "" for div in divs}

    class_types = ["f2f", "online", "blended"]

    for class_type in class_types:
        for element in soup.find_all("div", class_=f"delivery-{class_type}"):
            data_frame = [line.strip() for line in element.get_text().splitlines() if line.strip()]
            new_sections = [Section(class_id, data_frame, approved_course_dict, location=class_type, desc=description)]
            print("Added", str(new_sections[0]))
            sections += new_sections

    print("_" * 40)

    return sections


def calculate_teacher_easiness(grade_list) -> float:
    # Define the grade weights (you can adjust these as needed)
    grade_weights = {
        'A+': 4.0,
        'A': 4.0,
        'A-': 3.7,
        'B+': 3.3,
        'B': 3.0,
        'B-': 2.7,
        'C+': 2.3,
        'C': 2.0,
        'C-': 1.7,
        'D+': 1.3,
        'D': 1.0,
        'D-': 0.7,
        'F': 0.0,
        'W': 0.0,  # Withdrawals don't count towards easiness
        'Other': 0.0  # Other grades don't count towards easiness
    }

    # Calculate the weighted sum of grades
    total_weighted_grades = sum(float(grade_list[x]) * weight for x, weight in enumerate(grade_weights.values()))

    # Calculate the total number of graded students
    total_students = sum(map(int, grade_list))

    # Calculate the teacher easiness score
    if total_students > 0:
        teacher_easiness_score = total_weighted_grades / total_students
    else:
        teacher_easiness_score = 0.0  # No graded students

    return teacher_easiness_score


# returns a list of Section Classes with all sections
def get_all_sections(input_file: str) -> list:
    with open(input_file, "r") as in_file:
        all_classes = list(filter(len, in_file.read().split("\n")))

    classes_list = []

    for class_ in all_classes:
        classes_list += get_sections(class_)

    return classes_list


def sections_to_json(list_of_classes: list[Section], output_file: str) -> None:
    with open(output_file, "w+") as out_file:
        json.dump({"classes": [section.json_encoding() for section in list_of_classes]}, out_file, indent=4)

sections_to_json(get_all_sections(r"classes.txt"), "sections.json")
