
class Mammals:
    def __init__(self):
        self.members = ["Dog", "Elephant", "Kitty"]

    def print_members(self):
        print("printing members of the Mammals class")
        for member in self.members:
            print(f"\t{member}")


if __name__ == "__main__":
    mammal = Mammals()
    mammal.print_members()
