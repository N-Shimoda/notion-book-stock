import customtkinter as ctk
from tkinter import messagebox
import cv2
from PIL import Image, ImageTk, ImageOps
from pyzbar.pyzbar import decode

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

        # start video capturing
        self.vcap = cv2.VideoCapture(0)
        self.vwidth = self.vcap.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.vheight = self.vcap.get(cv2.CAP_PROP_FRAME_HEIGHT)

        # create GUI
        self.create_frames()
        self.create_widgets()
        self.delay = 15 #[mili seconds]
        self.update()

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
            # image=pil_image.transpose(Image.FLIP_LEFT_RIGHT)
            image=pil_image
        )
        self.canvas.create_image(canvas_width/2, canvas_height/2, image=self.photo)
        
        # check for ISBN
        isbn = self.check_isbn(frame)
        if isbn:
            print(isbn)
            messagebox.showinfo(title="Infomation!", message=f"ISBN detected ({isbn})")
    
        self.after(self.delay, self.update)

    def check_isbn(self, frame):
        isbn = None
        for barcode in decode(frame):
            value = barcode.data.decode('utf-8')
            if is_valid_ISBN13(value):
                isbn = value
        
        return isbn
    

if __name__ == "__main__":
    app = App()
    app.mainloop()