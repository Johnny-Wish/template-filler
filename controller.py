import os
import sys
from fetcher import StudentFetcher, ProjectInfoFetcher, GenreFormer, Fetcher, FlockFetcher
from io_utils import safe_mkdir, DocxInsertionWriter, TxtWriter, stdio_yn
from typing import Sequence
from checker import NameChecker, GenderChecker, PlaceholderChecker, CheckSummarizer, ApostropheChecker, \
    SecondPersonChecker
from post_process import PostProcessor, compose, ApostrophePostProcessor, EnglishDialectPostProcessor
import argparse
import language_tool_python as langtool


class Controller:
    def __init__(
            self,
            genre_former: GenreFormer,
            student_fetcher: Fetcher,
            program_fetcher: Fetcher,
            post_processors: Sequence[PostProcessor] = None
    ):
        self.genre_former = genre_former
        self.student_fetcher = student_fetcher
        self.program_fetcher = program_fetcher

        self.genre = genre_former.get_genre()
        self.genre.entry_separator = "\n\n"
        self.student_data = student_fetcher.fetch()
        self.program_data = program_fetcher.fetch(verbatim=True)

        self.articles = [self.genre.fill(program_fetcher.fetch()).fill(student) for student in student_fetcher.fetch()]
        self.post_processor = compose(*(post_processors or []))
        self._texts = None

    def get_articles(self):
        return self.articles

    def get_texts(self, force_rerun=False):
        if force_rerun or self._texts is None:
            self._texts = [self.post_processor(article.serialize()) for article in self.get_articles()]
        return self._texts

    def write_to_disk(self, output_writer, output_dir, language_tool=None, grammar_writer=None, match_policy='all'):
        safe_mkdir(output_dir)

        for content, row in zip(self.get_texts(), self.student_data):
            first_name = row['first_name'].eval().serialize()
            last_name = row['last_name'].eval().serialize()
            propose_fname = f"{first_name}-{last_name}-path-letter"
            propose_fname = os.path.join(output_dir, propose_fname)
            output_writer.write(content=content, fname=propose_fname)
            if language_tool and grammar_writer:
                matches = language_tool.check(content)
                if match_policy == 'ask':
                    applied_matches = []
                    unapplied_matches = []
                    for m in matches:
                        if stdio_yn(str(m) + '\nAccept the above suggestion?'):
                            applied_matches.append(m)
                        else:
                            unapplied_matches.append(m)
                elif match_policy == 'all':
                    applied_matches = matches
                    unapplied_matches = []
                elif match_policy == 'none':
                    applied_matches = []
                    unapplied_matches = matches
                else:
                    raise RuntimeError(f"Unknown matches policy: {match_policy}")

                if applied_matches:
                    correction = langtool.utils.correct(content, applied_matches)
                    output_writer.write(content=correction, fname=propose_fname + '-correction')
                    grammar_writer.write(
                        content='\n\n'.join(str(m) for m in applied_matches),
                        fname=propose_fname + '-applied-matches.txt',
                    )
                if unapplied_matches:
                    grammar_writer.write(
                        content='\n\n'.join(str(m) for m in unapplied_matches),
                        fname=propose_fname + '-unapplied-matches.txt',
                    )

    def check_texts(self, output="stderr"):
        all_first_names = [row["first_name"].eval().serialize() for row in self.student_data]
        all_last_names = [row["last_name"].eval().serialize() for row in self.student_data]

        summarizer = CheckSummarizer()

        placeholder_checker = PlaceholderChecker(summarizers=[summarizer])
        gender_checker = GenderChecker(summarizers=[summarizer])
        name_checker = NameChecker(all_first_names, all_last_names, summarizers=[summarizer])
        apostrophe_checker = ApostropheChecker(summarizers=[summarizer])
        # second_person_checker = SecondPersonChecker(summarizers=[summarizer])

        for content, row in zip(self.get_texts(), self.student_data):
            first_name = row['first_name'].eval().serialize()
            last_name = row['last_name'].eval().serialize()
            filename = f"{first_name} {last_name}"
            print(f"Checking {filename}", end="\t")
            placeholder_checker.check(filename, content)
            gender_checker.check(filename, content)
            name_checker.check(filename, content, target_first_name=first_name, target_last_name=last_name)
            apostrophe_checker.check(filename, content)
            # second_person_checker.check(filename, content)

        summaries = summarizer.get_summaries()
        if summaries is not None:
            summaries = f"{len(summaries)} warning(s) found:\n" + "\n".join(summaries)
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
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--pre_para_id', default=0, type=int)
    arg_parser.add_argument('--insert_before', default=True, type=bool)
    arg_parser.add_argument('--apostrophe', default='curly', type=str)
    arg_parser.add_argument('--dialect', default=None, type=str)
    arg_parser.add_argument('--langtool_server', default=None, type=str)
    arg_parser.add_argument('--new_spellings', default='', type=str)
    arg_parser.add_argument('--match_policy', default='ask', type=str)
    args = arg_parser.parse_args()
    post_processors = []
    if args.dialect:
        post_processors.append(EnglishDialectPostProcessor(args.dialect))
    if args.apostrophe:
        post_processors.append(ApostrophePostProcessor(args.apostrophe))

    flock_fetcher = FlockFetcher("./flock")
    program_fetcher = ProjectInfoFetcher("./program_info")
    student_fetcher = StudentFetcher(root_dir=".", name_list_path="eval.csv", flock_fetcher=flock_fetcher)
    former = GenreFormer("./genre")

    writer = DocxInsertionWriter(template_path="./style.docx", pre_para_id=args.pre_para_id,
                                 insert_before=args.insert_before)

    if args.langtool_server:
        if args.dialect is None or args.dialect == 'ame':
            language = 'en-US'
        else:
            language = 'en-GB'
        student_fetcher.set_cache()
        names = set(student_fetcher.cache.first_name).union(set(student_fetcher.cache.last_name))
        new_spellings = args.new_spellings.split() + list(names)
        print('new spellings:', new_spellings)
        tool = langtool.LanguageTool(language=language, remote_server=args.langtool_server, newSpellings=new_spellings)
        grammar_writer = TxtWriter()
    else:
        tool, grammar_writer = None, None

    controller = Controller(genre_former=former, student_fetcher=student_fetcher, program_fetcher=program_fetcher,
                            post_processors=post_processors)
    controller.check_texts()
    controller.write_to_disk(output_writer=writer, output_dir="./letters", language_tool=tool,
                             grammar_writer=grammar_writer, match_policy=args.match_policy)
