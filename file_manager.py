import os
import shutil
from fetcher import FlockFetcher, ProjectInfoFetcher, GenreFormer, StudentFetcher
from controller import Controller
from io_utils import safe_mkdir, extract_zip, zipdir, DocxInsertionWriter
from global_utils import rreplace, get_time_str


class FileSystemManager:
    def __init__(self, zip_dir, extracted_dir, download_dir):
        safe_mkdir(zip_dir)
        safe_mkdir(extracted_dir)
        safe_mkdir(download_dir)

        self.ZIP_DIR = zip_dir
        self.EXTRACTED_DIR = extracted_dir
        self.DOWNLOAD_DIR = download_dir

    def save_uploaded(self, file, filename):
        uploaded_zip_path = os.path.join(self.ZIP_DIR, filename)
        file.save(uploaded_zip_path)
        return uploaded_zip_path

    @staticmethod
    def get_controller(project_root):
        flock_fetcher = FlockFetcher(os.path.join(project_root, "flock"))
        program_fetcher = ProjectInfoFetcher(os.path.join(project_root, "program_info"))
        student_fetcher = StudentFetcher(root_dir=project_root, name_list_path="eval.csv", flock_fetcher=flock_fetcher)
        former = GenreFormer(os.path.join(project_root, "genre"))
        return Controller(genre_former=former, student_fetcher=student_fetcher, program_fetcher=program_fetcher)

    @staticmethod
    def run_controller(project_root, controller, pre_para_id):
        writer = DocxInsertionWriter(template_path=os.path.join(project_root, "style.docx"), pre_para_id=pre_para_id)
        letter_dir = os.path.join(project_root, "letters")
        controller.write_to_disk(writer, output_dir=letter_dir)
        return letter_dir

    def handle(self, file, filename, pre_para_id, check=True):
        # save uploaded zip, and get the dir
        filename = f"{get_time_str()}_{filename}"
        uploaded_zip_path = self.save_uploaded(file, filename)

        # extract zip to a new folder
        extracted_path = os.path.join(self.EXTRACTED_DIR, rreplace(filename, ".zip", ""))
        extract_zip(src=uploaded_zip_path, dest=extracted_path)
        os.remove(uploaded_zip_path)

        # instantiate a controller to handle the extracted folder
        controller = self.get_controller(extracted_path)
        if check:
            controller.check_texts(output="raise")

        # run the controller and generator docs, optionally gather error, info, debug
        letter_dir = self.run_controller(extracted_path, controller, pre_para_id=pre_para_id)

        # zip the docs folder and return download path
        download_path = os.path.join(self.DOWNLOAD_DIR, filename)
        zipdir(letter_dir, download_path)
        shutil.rmtree(extracted_path)

        return filename
