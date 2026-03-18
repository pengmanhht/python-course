class Person:

    def __init__(self, first_name, last_name):
        self.first_name = first_name
        self.last_name = last_name

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
        


class Student(Person):

    def __init__(self, first_name, last_name, subject):
        super().__init__(first_name, last_name)
        self.subject = subject

    def print_name_subject(self):
        full_name = self.get_full_name()
        print(f"Name: {full_name}, Subject: {self.subject}")


if __name__ == "__main__":
    s = Student("P", "M", "Medicine")
    s.print_name_subject()
