class Birds:
    def __init__(self):
        self.members = ["Eagle", "Falcon", "Barred Owl"]

    def print_members(self):
        print("printing members of the Birds class")
        for member in self.members:
            print(f"\t{member}")


if __name__ == "__main__":
    birds = Birds()
    birds.print_members()
