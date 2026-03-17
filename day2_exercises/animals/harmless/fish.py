
class Fish:
    def __init__(self):
        self.members = ["Tuna", "Salmon", "Coral Throut"]

    def print_members(self):
        print("printing members of the Fish class")
        for member in self.members:
            print(f"\t{member}")



if __name__ == "__main__":
    fish = Fish()
    fish.print_members()
