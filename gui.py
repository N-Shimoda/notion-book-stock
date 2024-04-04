import tkinter as tk
import customtkinter as ctk
import os
import cv2
from PIL import Image, ImageTk, ImageOps
from pyzbar.pyzbar import decode
from src.google_books import search_isbn
from src.notion import add_book_info

def is_valid_ISBN13(num: int) -> bool:
    """Function to validate if a given value is ISBN-13."""
    num_str = str(num)
    return (num_str[0:3]=="978" or num_str[0:3]=="979")

class App(ctk.CTk):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # settings
        self.title("Notion Book Stock")
        self.geometry("920x550")

        # variables
        self.notion_api_key = self.get_notion_api_key()
        self.radio_val = tk.IntVar(     # variable for radio button (appearance mode)
            value = ["Light", "Dark"].index(ctk.get_appearance_mode())
        )

        # start video capturing
        self.vcap = cv2.VideoCapture(0)
        self.vwidth = self.vcap.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.vheight = self.vcap.get(cv2.CAP_PROP_FRAME_HEIGHT)

        # create GUI
        # self.create_menubar()
        self.create_frames()
        self.create_widgets()
        self.delay = 5 #[mili seconds]
        self.update()

    def create_menubar(self):
        # ---- Define menus ----
        self.menubar = tk.Menu(self)
        self.menu_view = tk.Menu(self.menubar)
        self.menu_appearance_mode = tk.Menu(self.menubar, tearoff=False)

        # ---- Menu hierarchy ----
        self.menubar.add_cascade(label="View", menu=self.menu_view)
        self.config(menu=self.menubar)

        # ---- View menu ----
        self.menu_view.add_cascade(label="Change theme", menu=self.menu_appearance_mode)
        self.menu_appearance_mode.add_radiobutton(
            label="light",
            command=lambda: ctk.set_appearance_mode("light"),
            variable=self.radio_val,
            value=0
        )
        self.menu_appearance_mode.add_radiobutton(
            label="dark",
            command=lambda: ctk.set_appearance_mode("dark"),
            variable=self.radio_val,
            value=1
        )

    def create_frames(self):
        """Method to create frames."""
        self.side_frame = ctk.CTkFrame(self, fg_color="gray")
        self.cam_frame = ctk.CTkFrame(self, width=self.vwidth, height=self.vheight, fg_color="cyan")

        self.side_frame.pack(side="left", fill="y")
        self.cam_frame.pack(side="left", expand=True, fill="both")

    def create_widgets(self):
        # side bar
        button = ctk.CTkButton(self.side_frame, text="Register")
        button.pack(anchor="center")

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
            # image=pil_image
        )
        self.canvas.create_image(canvas_width/2, canvas_height/2, image=self.photo)
        
        # check for ISBN
        isbn = self.check_isbn(frame)
        if isbn:
            # print(isbn)
            # messagebox.showinfo(title="Infomation!", message=f"ISBN detected ({isbn})")
            title, date, thumbnail = search_isbn(isbn)
            add_book_info(title, date, thumbnail)
    
        self.after(self.delay, self.update)

    def check_isbn(self, frame):
        isbn = None
        for barcode in decode(frame):
            value = barcode.data.decode('utf-8')
            if is_valid_ISBN13(value):
                isbn = value
        return isbn
    
    def get_notion_api_key(self):
        api_key = os.environ.get("NOTION_API_KEY")
        if api_key is None:
            dialog = ctk.CTkInputDialog(text="Enter Notion API key:", title="auth")
            api_key = dialog.get_input()
            os.environ["NOTION_API_KEY"] = api_key

        return api_key

if __name__ == "__main__":
    app = App()
    app.mainloop()