import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, simpledialog
import os
import cv2
from PIL import Image, ImageTk, ImageOps
from pyzbar.pyzbar import decode
from src.google_books import search_isbn
from src.notion import add_book_info

def is_valid_ISBN13(num: int) -> bool:
    """Function to validate if a given integer is ISBN-13."""
    num_str = str(num)
    return (num_str[0:3]=="978" or num_str[0:3]=="979")

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

        # set API key as environmental variable
        self.get_notion_api_key()

        # start video capturing
        self.vcap = cv2.VideoCapture(0)
        self.vwidth = self.vcap.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.vheight = self.vcap.get(cv2.CAP_PROP_FRAME_HEIGHT)

        # --- create GUI ---
        self.create_frames()
        self.create_widgets()
        self.delay = 5 # [mili seconds]
        self.update()

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
            text_color="orange"
        )
        loc_label.pack(pady=10)
        self.cmbbox.pack(padx=20)

        # right frame
        self.canvas = ctk.CTkCanvas(self.cam_frame)
        self.canvas.pack(expand=True, fill="both")

    def update(self):
        # Get a frame from the video source
        _, frame = self.vcap.read()

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # show current frame
        pil_image = ImageOps.pad(Image.fromarray(frame), (canvas_width, canvas_height))
        self.photo = ImageTk.PhotoImage(
            image=pil_image.transpose(Image.FLIP_LEFT_RIGHT)
        )
        self.canvas.create_image(canvas_width/2, canvas_height/2, image=self.photo)
        
        # check for ISBN
        isbn = self.scan_isbn(frame)

        # check API call history
        if isbn in self.history:
            add_book = messagebox.askyesno("Book already added", "This book has been added. Are you sure to upload ISBN {} again?".format(isbn))
        else:
            add_book = (isbn is not None)

        if add_book:
            self.upload_book(isbn)

        # scan next frame
        self.after(self.delay, self.update)

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
            value = barcode.data.decode('utf-8')
            if is_valid_ISBN13(value):
                isbn = value
        return isbn
    
    def get_notion_api_key(self):
        """Method to set Notion API key as environment variable."""
        api_key = os.environ.get("NOTION_API_KEY")
        if api_key is None:
            api_key = simpledialog.askstring("Auth", "Enter Notion API key:", show='*')
            os.environ["NOTION_API_KEY"] = api_key

if __name__ == "__main__":
    app = App()
    app.mainloop()