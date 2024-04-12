import os
import threading
from tkinter import messagebox, simpledialog

import customtkinter as ctk
import cv2
from dotenv import load_dotenv
from PIL import Image, ImageOps, ImageTk
from pyzbar.pyzbar import decode

from src.google_books import search_isbn
from src.notion import add_book_info
from src.github import get_latest_tag

# modify these values when creating new release
VERSION = "v1.1"
RELEASED_DATE = "2024-04-12"


def is_valid_ISBN13(num: int) -> bool:
    """Function to validate if a given integer is ISBN-13."""
    num_str = str(num)
    return num_str[0:3] == "978" or num_str[0:3] == "979"


class AuthentificationFailedException(BaseException):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class App(ctk.CTk):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # --- settings ---
        self.title("Notion Book Stock")
        ctk.set_appearance_mode("dark")
        self.geometry("1024x640")

        # --- variables ---
        self.history = []
        self.cmbbox = None

        try:
            # create '.env' file if not exists
            if not load_dotenv():
                self.create_dotenv()
                self.set_api()

            assert os.getenv("NOTION_API_KEY") is not None, "Environment variable 'NOTION_API_KEY' doesn't exist."

            # start video capturing
            self.vcap = cv2.VideoCapture(0)
            self.vwidth = self.vcap.get(cv2.CAP_PROP_FRAME_WIDTH)
            self.vheight = self.vcap.get(cv2.CAP_PROP_FRAME_HEIGHT)

            # --- create GUI ---
            self.create_frames()
            self.create_widgets()

            # --- check updates ---
            self.update()
            if not self.check_latest_release():
                raise ValueError(
                    "Please get the latest version from GitHub (https://github.com/N-Shimoda/notion-book-stock)."
                )

            canvas_thread = threading.Thread(target=self.update_canvas)
            canvas_thread.start()

        except BaseException as e:
            print(type(e))
            print(e)
            exit()

    def create_frames(self):
        """Method to create frames."""
        self.side_frame = ctk.CTkFrame(self)
        self.cam_frame = ctk.CTkFrame(self, width=self.vwidth, height=self.vheight)

        self.side_frame.pack(side="left", fill="y")
        self.cam_frame.pack(side="left", expand=True, fill="both")

    def create_widgets(self):
        """Method to create wedgets in frames"""
        # side frame
        loc_label = ctk.CTkLabel(self.side_frame, text="Location", font=ctk.CTkFont(size=16))
        self.cmbbox = ctk.CTkComboBox(
            self.side_frame,
            values=["新着図書", "N1", "N2", "N3", "N4", "N5", "N6", "W"],
            text_color="orange",
            state="readonly",
        )
        self.cmbbox.set("新着図書")
        loc_label.pack(pady=10)
        self.cmbbox.pack(padx=20)

        # right frame
        self.canvas = ctk.CTkCanvas(self.cam_frame)
        self.canvas.pack(expand=True, fill="both")

    def update_canvas(self):
        while True:
            # Get a frame from the video source
            _, frame = self.vcap.read()

            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # show current frame
            pil_image = ImageOps.pad(Image.fromarray(frame), (canvas_width, canvas_height))
            self.photo = ImageTk.PhotoImage(image=pil_image.transpose(Image.FLIP_LEFT_RIGHT))
            self.canvas.create_image(canvas_width / 2, canvas_height / 2, image=self.photo)

            # check for ISBN
            isbn = self.scan_isbn(frame)

            # check API call history
            if isbn in self.history:
                add_book = messagebox.askyesno(
                    "Book already added", "This book has been added. Are you sure to upload ISBN {} again?".format(isbn)
                )
            else:
                add_book = isbn is not None

            if add_book:
                self.upload_book(isbn)

    def upload_book(self, isbn: int):
        """
        Method to upload given book (ISBN) to Notion databse.

        Parameters
        ----------
        isbn: int
        """
        bookdata = search_isbn(isbn)

        if bookdata:
            bookdata["location"] = self.cmbbox.get()
            print(bookdata)
            conf = messagebox.askokcancel("Confirmation", "Upload '{}'?".format(bookdata["title"]))
            if conf:
                add_book_info(**bookdata)
                self.history.append(isbn)
        else:
            messagebox.showerror(message="No book found for ISBN: {}".format(isbn))

    def scan_isbn(self, frame) -> int | None:
        """
        Method to scan ISBN barcode in given frame.

        Parameters
        ----------
        frame: numpy.ndarray

        Return
        ------
        isbn: int | None
            ISBN value found in the frame.
        """
        isbn = None
        for barcode in decode(frame):
            value = barcode.data.decode("utf-8")
            if is_valid_ISBN13(value):
                isbn = value
        return isbn

    def create_dotenv(self):
        """Method to create .env file initially."""
        dotenv_path = ".env"
        assert not os.path.exists(dotenv_path), "'.env' file already exists."
        with open(dotenv_path, "w", encoding="utf-8") as f:
            f.write("")
        print("Created '.env' file successfully.")

    def set_api(self):
        """
        Method to set API key via a dialog window.
        """
        assert os.getenv("NOTION_API_KEY") is None, "Environment variable 'NOTION_API_KEY' already exists."
        api_key = simpledialog.askstring(title="API key config", prompt="Enter API key of Notion:", show="*")
        if api_key is not None:
            with open(".env", "w", encoding="utf-8") as f:
                f.write(f"NOTION_API_KEY={api_key}")
            load_dotenv()
            print("API key has been successfully set.")
        else:
            print("Canceled.")
            exit()

    def check_latest_release(self) -> bool:
        """Function to check if the app is up-to-date with the newest release."""
        try:
            latest_tag, release_date = get_latest_tag("N-Shimoda", "notion-book-stock")
            if latest_tag:
                if (latest_tag, release_date) == (VERSION, RELEASED_DATE):
                    return True
                else:
                    messagebox.showinfo(
                        "Newer version available", 
                        "Newer version is available. Please update the application.\n{} → {}".format(VERSION, latest_tag)
                    )
                    return False
            else:
                messagebox.showwarning("No release found", "Please check if the remote repository exists.")
                return False
        except:
            messagebox.showerror("Versioning failed", "Failed in version validation. Please check the repository and network connection")
            return False
    
if __name__ == "__main__":
    
    app = App()
    app.mainloop()
