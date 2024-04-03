from typing import Tuple
import customtkinter as ctk
import cv2
import PIL

class App(ctk.CTk):
    def __init__(self, fg_color: str | Tuple[str, str] | None = None, **kwargs):
        super().__init__(fg_color, **kwargs)

        # settings
        self.title("Notion Book Stock")
        self.geometry("920x550")

        # opencv
        self.vcap = cv2.VideoCapture(0)
        self.vwidth = self.vcap.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.vheight = self.vcap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print(self.vwidth, self.vheight)

        # create GUI
        self.create_frames()
        self.create_widgets()
        self.delay = 15 #[mili seconds]
        self.update()

    def create_frames(self):
        self.side_frame = ctk.CTkFrame(self, fg_color="gray")
        self.cam_frame = ctk.CTkFrame(self, width=self.vwidth, height=self.vheight, fg_color="cyan")

        self.side_frame.pack(side="left", fill="y")
        self.cam_frame.pack(side="left", expand=True, fill="both")

    def create_widgets(self):
        # side bar
        label = ctk.CTkLabel(self.side_frame, text="Hello world.")
        label.pack()
        button = ctk.CTkButton(self.side_frame, text="Register")
        button.pack()

        # right frame
        self.canvas = ctk.CTkCanvas(self.cam_frame)
        self.canvas.pack(expand=True, fill="both")

    def update(self):
        # Get a frame from the video source
        _, frame = self.vcap.read()

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))

        # self.photo -> Canvas
        self.canvas.create_image(0, 0, image=self.photo, anchor=ctk.NW)

        self.after(self.delay, self.update)

if __name__ == "__main__":
    app = App()
    app.mainloop()