import os
from fetcher import StudentFetcher, ProjectInfoFetcher, GenreFormer, Fetcher, FlockFetcher
from io_utils import safe_mkdir, DocxInsertionWriter
from checker import NameChecker, GenderChecker, PlaceholderChecker


class Controller:
    def __init__(self, genre_former: GenreFormer, student_fetcher: Fetcher, program_fetcher: Fetcher):
        self.genre_former = genre_former
        self.student_fetcher = student_fetcher
        self.program_fetcher = program_fetcher

        self.genre = genre_former.get_genre()
        self.genre.entry_separator = "\n\n"
        self.student_data = student_fetcher.fetch()
        self.program_data = program_fetcher.fetch()

        self.articles = [self.genre.fill(program_fetcher.fetch()).fill(student) for student in student_fetcher.fetch()]
        # self.articles = []
        # for student_data in student_fetcher.fetch():
        #     blob = self.genre.fill(program_fetcher.fetch())
        #     blob = blob.fill(student_data)
        #     self.articles.append(blob)

    def get_articles(self):
        return self.articles

    def get_texts(self):
        return [article.serialize() for article in self.get_articles()]

    def write_to_disk(self, writer, output_dir):
        safe_mkdir(output_dir)

        for content, row in zip(self.get_texts(), self.student_data):
            first_name = row['first_name'].eval().serialize()
            last_name = row['last_name'].eval().serialize()
            propose_fname = f"{first_name}-{last_name}-path-letter"
            propose_fname = os.path.join(output_dir, propose_fname)
            writer.write(content=content, fname=propose_fname)

    def check_texts(self):
        all_first_names = [row["first_name"].eval().serialize() for row in self.student_data]
        all_last_names = [row["last_name"].eval().serialize() for row in self.student_data]
        placeholder_checker = PlaceholderChecker()
        gender_checker = GenderChecker()
        name_checker = NameChecker(all_first_names, all_last_names)

        print("list of names to check:")
        for fn, ln in zip(all_first_names, all_last_names):
            print(fn, ln)
        print()

        for content, row in zip(self.get_texts(), self.student_data):
            first_name = row['first_name'].eval().serialize()
            last_name = row['last_name'].eval().serialize()
            print(f"Checking {first_name} {last_name}")
            placeholder_checker.check(content)
            gender_checker.check(content)
            name_checker.check(content, target_first_name=first_name, target_last_name=last_name)
            print()


if __name__ == '__main__':
    flock_fetcher = FlockFetcher("./flock")
    program_fetcher = ProjectInfoFetcher("./program_info")
    student_fetcher = StudentFetcher(root_dir=".", name_list_path="eval.csv", flock_fetcher=flock_fetcher)
    former = GenreFormer("./genre")

    writer = DocxInsertionWriter(template_path="./style.docx", pre_para_id=0)

    controller = Controller(genre_former=former, student_fetcher=student_fetcher, program_fetcher=program_fetcher)
    controller.check_texts()
    controller.write_to_disk(writer=writer, output_dir="./letters")
