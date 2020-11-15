import os
import sys
from fetcher import StudentFetcher, ProjectInfoFetcher, GenreFormer, Fetcher, FlockFetcher
from io_utils import safe_mkdir, DocxInsertionWriter
from checker import NameChecker, GenderChecker, PlaceholderChecker, CheckSummarizer


class Controller:
    def __init__(self, genre_former: GenreFormer, student_fetcher: Fetcher, program_fetcher: Fetcher):
        self.genre_former = genre_former
        self.student_fetcher = student_fetcher
        self.program_fetcher = program_fetcher

        self.genre = genre_former.get_genre()
        self.genre.entry_separator = "\n\n"
        self.student_data = student_fetcher.fetch()
        self.program_data = program_fetcher.fetch(verbatim=True)

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

    def check_texts(self, output="stderr"):
        all_first_names = [row["first_name"].eval().serialize() for row in self.student_data]
        all_last_names = [row["last_name"].eval().serialize() for row in self.student_data]

        summarizer = CheckSummarizer()

        placeholder_checker = PlaceholderChecker(summarizers=[summarizer])
        gender_checker = GenderChecker(summarizers=[summarizer])
        name_checker = NameChecker(all_first_names, all_last_names, summarizers=[summarizer])

        for content, row in zip(self.get_texts(), self.student_data):
            first_name = row['first_name'].eval().serialize()
            last_name = row['last_name'].eval().serialize()
            filename = f"{first_name} {last_name}"
            print(f"Checking {filename}", end="\t")
            placeholder_checker.check(filename, content)
            gender_checker.check(filename, content)
            name_checker.check(filename, content, target_first_name=first_name, target_last_name=last_name)

        summaries = summarizer.get_summaries()
        if summaries is not None:
            summaries = f"{len(summaries)} warning(s) found:" + "\n\n".join(summaries)
            if output == "raise":
                raise ValueError(summaries)
            elif output == "stderr":
                print(summaries, file=sys.stderr)
            elif output == "stdout":
                print(summaries)
            else:
                print("unrecognized output format")
                print(summaries)


if __name__ == '__main__':
    flock_fetcher = FlockFetcher("./flock")
    program_fetcher = ProjectInfoFetcher("./program_info")
    student_fetcher = StudentFetcher(root_dir=".", name_list_path="eval.csv", flock_fetcher=flock_fetcher)
    former = GenreFormer("./genre")

    writer = DocxInsertionWriter(template_path="./style.docx", pre_para_id=0)

    controller = Controller(genre_former=former, student_fetcher=student_fetcher, program_fetcher=program_fetcher)
    controller.check_texts()
    controller.write_to_disk(writer=writer, output_dir="./letters")
