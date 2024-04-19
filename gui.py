import os

os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"
from tkinter import messagebox, simpledialog

import customtkinter as ctk
import cv2
from dotenv import load_dotenv
from PIL import Image, ImageOps, ImageTk
from pyzbar.pyzbar import decode

from src.github import get_latest_tag
from src.google_books import search_isbn
from src.notion import NotionDB

# modify these values when creating new release
VERSION = "v1.3"
RELEASED_DATE = "2024-04-16"


def is_valid_ISBN(value: str) -> bool:
    """Function to validate if a given str is ISBN."""
    try:
        int(value)
        if len(value) == 13:
            return value[0:3] == "978" or value[0:3] == "979"
        elif len(value) == 10:
            return True
        else:
            return False
    except:
        return False


class App(ctk.CTk):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # --- settings ---
        self.title("Notion Book Stock")
        ctk.set_appearance_mode("dark")
        self.geometry("1024x640")

        # --- variables ---
        self.db = NotionDB(databse_id="3dacfb355eb34f0b9d127a988539809a")
        self.history = self.db.get_isbn_list()
        self.loc_choice = self.db.get_location_tags()

        try:
            # create '.env' file if not exists
            if not load_dotenv():
                self.create_dotenv()
                self.set_api()

            assert os.getenv("NOTION_API_KEY") is not None, "Environment variable 'NOTION_API_KEY' doesn't exist."

            # get available camera(s)
            self.available_cam = []
            for i in range(5):
                try:
                    print(f"Checking camera {i} is available...")
                    cap = cv2.VideoCapture(i)
                    if cap is None or not cap.isOpened():
                        raise IndexError("Camera index out of range.")
                    else:
                        self.available_cam.append(i)
                    cap.release()
                except IndexError:
                    cap.release()
                    break
            assert len(self.available_cam) != 0, "No video source detected."

            # start video capturing
            self.vcap = cv2.VideoCapture(self.available_cam[0])
            self.vwidth = self.vcap.get(cv2.CAP_PROP_FRAME_WIDTH)
            self.vheight = self.vcap.get(cv2.CAP_PROP_FRAME_HEIGHT)

            # --- create GUI ---
            self.create_frames()
            self.create_widgets()

            # --- check updates ---
            if not self.check_latest_release():
                raise ValueError(
                    "Please get the latest version from GitHub (https://github.com/N-Shimoda/notion-book-stock)."
                )

            # --- display camera frame ---
            self.delay = 40  # ms
            self.update_canvas()
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
        """Method to create wedgets in each frame."""
        # --- side frame ---
        # small frames
        self.loc_frame = ctk.CTkFrame(self.side_frame, fg_color="transparent")
        self.camsrc_frame = ctk.CTkFrame(self.side_frame, fg_color="transparent")
        self.loc_frame.pack(pady=20)
        self.camsrc_frame.pack(side="bottom", pady=30)

        # location pulldown
        loc_label = ctk.CTkLabel(self.loc_frame, text="Location", font=ctk.CTkFont(size=20))
        self.cmbbox = ctk.CTkComboBox(
            self.loc_frame,
            values=self.loc_choice,
            text_color="orange",
            font=ctk.CTkFont(size=16),
            state="readonly",
        )
        self.cmbbox.set("新着図書")
        loc_button = ctk.CTkButton(self.loc_frame, text="Add location", command=self.add_location_Cb, width=100)

        loc_label.pack(pady=5)
        self.cmbbox.pack(padx=20)
        loc_button.pack(padx=20, pady=10, anchor="e")

        # camera pulldown
        self.cam_label = ctk.CTkLabel(self.camsrc_frame, text="Camera source", font=ctk.CTkFont(size=20))
        self.cam_cmbbox = ctk.CTkComboBox(
            self.camsrc_frame,
            values=list(map("Camera {}".format, self.available_cam)),
            text_color="orange",
            font=ctk.CTkFont(size=16),
            state="readonly",
            command=self.switch_source,
        )
        self.cam_cmbbox.set(f"Camera {self.available_cam[0]}")
        self.cam_label.pack(pady=5)
        self.cam_cmbbox.pack(padx=20)

        # --- right frame ---
        self.canvas = ctk.CTkCanvas(self.cam_frame, highlightthickness=0)
        self.canvas.pack(expand=True, fill="both")

    def update_canvas(self):
        # Get a frame from the video source
        _, frame = self.vcap.read()

        self.canvas_width = self.canvas.winfo_width()
        self.canvas_height = self.canvas.winfo_height()

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # show current frame
        pil_image = ImageOps.pad(Image.fromarray(frame), (self.canvas_width, self.canvas_height))
        self.photo = ImageTk.PhotoImage(image=pil_image.transpose(Image.FLIP_LEFT_RIGHT))
        self.canvas.create_image(self.canvas_width / 2, self.canvas_height / 2, image=self.photo)

        # scan frame for ISBN
        isbn = self.scan_isbn(frame)

        # check existing books
        if isbn in self.history:
            add_book = messagebox.askyesno(
                "Book already added",
                "This book has been added. Are you sure to upload ISBN {} again?".format(isbn),
            )
        else:
            add_book = isbn is not None

        if add_book:
            self.upload_book(isbn)

        self.after(self.delay, self.update_canvas)

    def switch_source(self, value: str):
        video_src = 0
        for c in value:
            if c.isdigit():
                video_src = int(c)
                break
        self.vcap.release()
        self.vcap = cv2.VideoCapture(video_src)
        self.vwidth = self.vcap.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.vheight = self.vcap.get(cv2.CAP_PROP_FRAME_HEIGHT)

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
                res = self.db.create_book_page(**bookdata)
                if res.status_code == 200:
                    print("Successfully added.")
                    self.history.append(isbn)
                if res.status_code != 200:
                    print("Request failed. Maybe API key is outdated.")
                    print(f"Response Status Code: {res.status_code}")
                if res.status_code == 401:
                    self.set_api(prompt="Update API key of Notion:")
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
            if is_valid_ISBN(value):
                isbn = int(value)
                break
        return isbn

    def create_dotenv(self):
        """Method to create .env file initially."""
        dotenv_path = ".env"
        assert not os.path.exists(dotenv_path), "'.env' file already exists."
        with open(dotenv_path, "w", encoding="utf-8") as f:
            f.write("")
        print("Created '.env' file successfully.")

    def set_api(self, title="API key config", prompt="Enter API key of Notion:"):
        """
        Method to set API key via a dialog window.
        """
        if os.getenv("NOTION_API_KEY") is not None:
            print("Environment variable 'NOTION_API_KEY' already exists.")
        api_key = simpledialog.askstring(title, prompt, show="*")
        if api_key is not None:
            with open(".env", "w", encoding="utf-8") as f:
                f.write(f"NOTION_API_KEY={api_key}")
            load_dotenv(override=True)
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
                        "Newer version is available. Please update the application.\n{} → {}".format(
                            VERSION, latest_tag
                        ),
                    )
                    return False
            else:
                messagebox.showwarning("No release found", "Please check if the remote repository exists.")
                return False
        except BaseException as e:
            print(type(e))
            print(e)
            messagebox.showerror(
                "Versioning failed", "Failed in version validation. Please check the repository and network connection"
            )
            return False

    def add_location_Cb(self):
        """Method to add new shelf to option of locations."""
        # wait for input
        dialog = ctk.CTkInputDialog(title="Enter location name", text="Enter the name of new location.")
        item = dialog.get_input().split()[0]

        # update combobox
        self.loc_choice.append(item)
        self.cmbbox.configure(values=self.loc_choice)
        self.cmbbox.set(item)

        print("Current locations: {}".format(self.loc_choice))


if __name__ == "__main__":
    app = App()
    app.mainloop()
