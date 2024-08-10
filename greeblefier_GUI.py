import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
import os
from PIL import Image, ImageTk, ImageGrab, ImageDraw
import ast
import numpy as np
import random
import math
import pprint
import io
import win32clipboard

def rgb_to_hex(rgb_tuple):
	""" Convert RBG (tuple, list) to HEX (string #RRGGBB) """
	if not isinstance(rgb_tuple, (tuple, list)):
		raise TypeError("Only tuples or lists as input.")
	elif len(rgb_tuple) != 3:
		raise Exception("Only len(input) == 3 allowed.")
	else:
		# return '#%02x%02x%02x' % rgb_tuple
		return f'#{rgb_tuple[0]:02x}{rgb_tuple[1]:02x}{rgb_tuple[2]:02x}'

def hex_to_rgb(hex_string):
	""" Convert HEX (string RRGGBB, #RRGGBB or 0xRRGGBB) to RBG (tuple) """
	if hex_string[0] == "#":
		return tuple([int(hex_string[i:i+2], 16) for i in (1, 3, 5)])
	elif hex_string[0:2].upper() == "0X":
		return tuple([int(hex_string[i:i+2], 16) for i in (2, 4, 6)])
	else:
		return tuple([int(hex_string[i:i+2], 16) for i in (0, 2, 4)])

def is_transparent(img):
	# TODO: USE TO IMPLEMENT RGBA
	""" 
	Check the image mode for transparency.
	Convert LA -> RBGA, P -> RGB.
	Args:
		img: Image.Image object

	Returns:
		bool: True if if alpha channel present
	  """
	if img.mode == "RGBA":
		return True
	elif img.mode == "LA":
		img.convert("RGBA")
		return True
	elif img.mode == "P":
		img.convert("RGB")
		return False
	return False


class Greeblefier(tk.Tk):
	# TODO: IMPLEMENT RGBA
	def __init__(self, default_zoom=4, maximize_window=False, ask_to_exit=True):
		super().__init__()
		self.title("Greeblefier")
		self.configure(bg="lightgrey")
		if maximize_window:
			self.wm_state('zoomed')

		icon = self.create_favicon()
		self.iconphoto(True, icon)
		
		self.bind('<Escape>'   , lambda event: self.exit_GUI(event, ask_to_exit))
		self.bind('<plus>'     , self.zoom_in)
		self.bind('<minus>'    , self.zoom_out)
		self.bind('o'          , self.open_image)
		self.bind('s'          , self.save_image)
		self.bind('l'          , self.load_preset_window)
		self.bind('r'          , self.update_preview)
		self.bind("<Control-c>", self.copy_image_to_clipboard)
		self.bind("<Control-v>", self.insert_image_from_clipboard)
		self.bind("<Left>"     , self.scroll_left)
		self.bind("<Right>"    , self.scroll_right)
		self.bind("<Up>"       , self.scroll_up)
		self.bind("<Down>"     , self.scroll_down)

		self.create_widgets()
		self.bind_widgets()

		self.image = None
		self.image_name = None
		self.photo = None
		self.target_color = None
		self.current_entry = None
		self.greebled_image = None
		self.export_image_data = None
		self.default_zoom_level = min([1, 2, 4, 8, 16], key=lambda x: abs(default_zoom - x))

		self.mainloop()

	def exit_GUI(self, event, ask):
		if ask:
			response = messagebox.askokcancel(title=f"Close Greeblefier", message=f"Are you sure you want to exit?")
			if response:
				self.destroy()
		else:
			self.destroy()

	def create_favicon(self, *args):
		index = random.randint(0, 2)
		icon_data_brown = ImageTk.PhotoImage(file="greeblefier_GUI_files\\icons\\favicon_brown.png")
		icon_data_blue  = ImageTk.PhotoImage(file="greeblefier_GUI_files\\icons\\favicon_blue.png")
		icon_data_green = ImageTk.PhotoImage(file="greeblefier_GUI_files\\icons\\favicon_green.png")
		icon_data = [icon_data_brown, icon_data_blue, icon_data_green]
		return icon_data[index]

	def create_widgets(self):
		font_button       = ('Tahoma', 8, 'bold')
		font_smaller      = ('Tahoma', 8, 'bold')
		font_entry        = ('Tahoma', 10, 'normal')
		self.color_bckgnd = "lightgrey"
		color_image_frame = "grey"
		color_separator   = "dark grey"
		color_sample_w    = 150
		color_sample_h    = 50

		# Create a Frame for the controls (buttons and entry field)
		self.controls_FRAME = tk.Frame(self, bg=self.color_bckgnd)
		self.controls_FRAME.pack(side=tk.TOP, anchor='w', fill=tk.X, pady=5, padx=8)

		# Add top buttons
		self.label_at_checkbox = ttk.Label(self.controls_FRAME, text="Gr.", background=self.color_bckgnd)
		self.label_at_checkbox.grid(row=0, column=1, sticky="sw")
		style = ttk.Style()
		style.configure('TCheckbutton', background=self.color_bckgnd)
		self.checkbox_var = tk.IntVar(value=1)
		self.checkbox = ttk.Checkbutton(self.controls_FRAME, variable=self.checkbox_var)
		self.checkbox.grid(row=1, column=1, sticky="ne")

		style = ttk.Style()
		style.configure('TButton', font=font_button)
		self.open_button = ttk.Button(self.controls_FRAME, text="  Open image  ", command=self.open_image, style="TButton")
		self.save_button = ttk.Button(self.controls_FRAME, text="  Save image  ", command=self.save_image, style="TButton")
		self.open_button.grid(row=0, column=2, sticky="nesw")
		self.save_button.grid(row=1, column=2, sticky="nesw")

		self.zoom_in_button  = ttk.Button(self.controls_FRAME, text="    Zoom +    ", command=self.zoom_in, style="TButton")
		self.zoom_out_button = ttk.Button(self.controls_FRAME, text="    Zoom —    ", command=self.zoom_out, style="TButton")
		self.zoom_in_button.grid( row=0, column=3, sticky="nesw")
		self.zoom_out_button.grid(row=1, column=3, sticky="nesw")

		self.button_load_preset = ttk.Button(self.controls_FRAME, text="     Load preset     ", command=self.load_preset_window, style="TButton")
		self.button_save_preset = ttk.Button(self.controls_FRAME, text="   Save preset   ", command=self.save_preset_dialog, style="TButton")
		self.button_load_preset.grid(row=0, column=4, sticky="nesw")
		self.button_save_preset.grid(row=1, column=4, sticky="nesw")

		# Add entry and frame to show RGB values
		self.label_target_color = tk.Label(self.controls_FRAME, text="Target\ncolor:", bg=self.color_bckgnd, font=font_entry)
		self.label_target_color.grid(row=0, rowspan=2, column=5, padx=5)
		
		self.FRAME_color_display = tk.Frame(self.controls_FRAME, bg="black")
		self.color_display = tk.Frame(self.FRAME_color_display, width=color_sample_w, height=color_sample_h, bg=self.color_bckgnd)
		self.FRAME_color_display.grid(row=0, rowspan=2, column=6, padx=5)
		self.color_display.pack(padx=1, pady=1)

		self.rgb_entry = tk.Entry(self.controls_FRAME, font=font_entry, justify="center")
		self.rgb_entry.grid(row=0, rowspan=2, column=7, padx=5, ipady=4)
		self.rgb_prob_entry = tk.Entry(self.controls_FRAME, font=font_entry, justify="center", width=7)
		self.rgb_prob_entry.grid(row=0, rowspan=2, column=8, padx=0, ipady=4)
		self.rgb_prob_entry.insert(0, "100")
		self.label_target_color_prob = tk.Label(self.controls_FRAME, text="%", bg=self.color_bckgnd, font=font_entry)
		self.label_target_color_prob.grid(row=0, rowspan=2, column=9, padx=5)

		# Add Refresh button
		image = ImageTk.PhotoImage(file="greeblefier_GUI_files\\icons\\icon_refresh.png")
		self.button_refresh = ttk.Button(self.controls_FRAME, image=image, style="TButton", command=self.update_preview)
		self.button_refresh.image = image
		self.button_refresh.grid(row=0, rowspan=2, column=10, padx=10)#, sticky="nesw")

		# Add a label with shortcuts
		self.label_padding = tk.Label(self.controls_FRAME, bg=self.color_bckgnd)
		self.label_padding.grid(row=0, rowspan=2, column=11, padx=10)
		self.label_shortcuts1 = tk.Label(self.controls_FRAME, bg=self.color_bckgnd, justify="left", text="o  ...  open image\ns  ...  save image\n+ / -  ...  zoom\nl  ...  load preset")
		self.label_shortcuts1.grid(row=0, rowspan=2, column=12, padx=5)
		self.label_shortcuts2 = tk.Label(self.controls_FRAME, bg=self.color_bckgnd, justify="left", text="r  ...  re-greeble\nctrl+c ... copy to clipboard\nctrl+v ... paste from clipboard\nescape  ...  quit")
		self.label_shortcuts2.grid(row=0, rowspan=2, column=13, padx=5)

		# Little padding under the controls FRAME
		self.FRAME_padding_under_header = tk.Frame(self, bg=color_separator)
		self.FRAME_padding_under_header.pack(pady=2, ipady=1, fill=tk.X)

		######################################################################################################################################################################

		# Create a Frame for palettes
		self.palettes_FRAME = tk.Frame(self, bg=self.color_bckgnd)
		self.palettes_FRAME.pack(side=tk.LEFT, padx=2, pady=2, anchor='n')

		self.img_DOS_PALETTE = Image.open(os.path.join("greeblefier_GUI_files", "greeblefier_DOS_palette.png")).convert("RGB")
		self.photo_img_DOS_PALETTE = ImageTk.PhotoImage(self.img_DOS_PALETTE)
		self.label_DOS_PALETTE = tk.Label(self.palettes_FRAME, image=self.photo_img_DOS_PALETTE)
		self.label_DOS_PALETTE.pack()

		self.img_RGB_PALETTE = Image.open(os.path.join("greeblefier_GUI_files", "greeblefier_RGB_palette.png"))
		self.photo_img_RGB_PALETTE = ImageTk.PhotoImage(self.img_RGB_PALETTE)
		self.label_RGB_PALETTE = tk.Label(self.palettes_FRAME, image=self.photo_img_RGB_PALETTE)
		self.label_RGB_PALETTE.pack(pady=5)

		# Create a Frame for the greeble colors
		self.FRAME_greeble_colors = tk.Frame(self, bg=self.color_bckgnd)
		self.FRAME_greeble_colors.pack(side=tk.LEFT, padx=2, pady=2, anchor='n')

		######################################################################################################################################################################

		# Create a Frame for the image
		# Add a bit of vertical padding right of FRAME_greeble_colors
		self.FRAME_padding_between = tk.Frame(self, bg=self.color_bckgnd)
		self.FRAME_padding_between.pack(side=tk.LEFT)
		self.label_padding_between = tk.Frame(self.FRAME_padding_between, bg=self.color_bckgnd, width=5)
		self.label_padding_between.pack(side=tk.LEFT)
		self.image_FRAME = tk.Frame(self, width=400, height=400, bg=color_image_frame)
		self.image_FRAME.pack(side=tk.LEFT, padx=5, pady=5, anchor="n")

		######################################################################################################################################################################

		list_padding_frames = []
		for i in range(3):
			frame_padding = tk.Frame(self.FRAME_greeble_colors, bg=self.color_bckgnd, height=25)
			list_padding_frames.append(frame_padding)

		# Little padding above the greeble colors
		frame_padding = tk.Frame(self.FRAME_greeble_colors, bg=self.color_bckgnd, height=10)
		frame_padding.pack()
		self.FRAME_greeble_color_1 = tk.Frame(self.FRAME_greeble_colors, bg="black")
		self.FRAME_greeble_color_2 = tk.Frame(self.FRAME_greeble_colors, bg="black")
		self.FRAME_greeble_color_3 = tk.Frame(self.FRAME_greeble_colors, bg="black")
		self.FRAME_greeble_color_4 = tk.Frame(self.FRAME_greeble_colors, bg="black")
		self.label_greeble_color_1 = tk.Frame(self.FRAME_greeble_color_1, bg=self.color_bckgnd, width=color_sample_w, height=color_sample_h)
		self.label_greeble_color_2 = tk.Frame(self.FRAME_greeble_color_2, bg=self.color_bckgnd, width=color_sample_w, height=color_sample_h)
		self.label_greeble_color_3 = tk.Frame(self.FRAME_greeble_color_3, bg=self.color_bckgnd, width=color_sample_w, height=color_sample_h)
		self.label_greeble_color_4 = tk.Frame(self.FRAME_greeble_color_4, bg=self.color_bckgnd, width=color_sample_w, height=color_sample_h)

		self.FRAME_greeble_entries_1 = tk.Frame(self.FRAME_greeble_colors, bg=self.color_bckgnd)
		self.FRAME_greeble_entries_2 = tk.Frame(self.FRAME_greeble_colors, bg=self.color_bckgnd)
		self.FRAME_greeble_entries_3 = tk.Frame(self.FRAME_greeble_colors, bg=self.color_bckgnd)
		self.FRAME_greeble_entries_4 = tk.Frame(self.FRAME_greeble_colors, bg=self.color_bckgnd)
		self.entry_greeble_color_1 = tk.Entry(self.FRAME_greeble_entries_1, font=font_entry, justify="center", width=16)
		self.entry_greeble_color_2 = tk.Entry(self.FRAME_greeble_entries_2, font=font_entry, justify="center", width=16)
		self.entry_greeble_color_3 = tk.Entry(self.FRAME_greeble_entries_3, font=font_entry, justify="center", width=16)
		self.entry_greeble_color_4 = tk.Entry(self.FRAME_greeble_entries_4, font=font_entry, justify="center", width=16)
		self.entry_greeble_color_prob_1 = tk.Entry(self.FRAME_greeble_entries_1, font=font_entry, justify="center", width=5)
		self.entry_greeble_color_prob_2 = tk.Entry(self.FRAME_greeble_entries_2, font=font_entry, justify="center", width=5)
		self.entry_greeble_color_prob_3 = tk.Entry(self.FRAME_greeble_entries_3, font=font_entry, justify="center", width=5)
		self.entry_greeble_color_prob_4 = tk.Entry(self.FRAME_greeble_entries_4, font=font_entry, justify="center", width=5)

		self.FRAME_greeble_color_1.pack()
		self.label_greeble_color_1.pack(anchor='n', padx=1, pady=1)
		self.FRAME_greeble_entries_1.pack()
		self.entry_greeble_color_1.pack(side=tk.LEFT, anchor='n', pady=10, ipady=4)
		self.entry_greeble_color_prob_1.pack(side=tk.LEFT, anchor='n', pady=10, ipady=4)
		list_padding_frames[0].pack(anchor='n')
		self.FRAME_greeble_color_2.pack()
		self.label_greeble_color_2.pack(anchor='n', padx=1, pady=1)
		self.FRAME_greeble_entries_2.pack()
		self.entry_greeble_color_2.pack(side=tk.LEFT, anchor='n', pady=10, ipady=4)
		self.entry_greeble_color_prob_2.pack(side=tk.LEFT, anchor='n', pady=10, ipady=4)
		list_padding_frames[1].pack(anchor='n')
		self.FRAME_greeble_color_3.pack()
		self.label_greeble_color_3.pack(anchor='n', padx=1, pady=1)
		self.FRAME_greeble_entries_3.pack()
		self.entry_greeble_color_3.pack(side=tk.LEFT, anchor='n', pady=10, ipady=4)
		self.entry_greeble_color_prob_3.pack(side=tk.LEFT, anchor='n', pady=10, ipady=4)
		list_padding_frames[2].pack(anchor='n')
		self.FRAME_greeble_color_4.pack()
		self.label_greeble_color_4.pack(anchor='n', padx=1, pady=1)
		self.FRAME_greeble_entries_4.pack()
		self.entry_greeble_color_4.pack(side=tk.LEFT, anchor='n', pady=10, ipady=4)
		self.entry_greeble_color_prob_4.pack(side=tk.LEFT, anchor='n', pady=10, ipady=4)
		
		######################################################################################################################################################################

		self.list_of_all_entries = [
			self.rgb_entry,
			self.entry_greeble_color_1,
			self.entry_greeble_color_2,
			self.entry_greeble_color_3,
			self.entry_greeble_color_4,
			self.rgb_prob_entry,
			self.entry_greeble_color_prob_1,
			self.entry_greeble_color_prob_2,
			self.entry_greeble_color_prob_3,
			self.entry_greeble_color_prob_4]

		self.list_of_all_color_labels = [
			self.color_display,
			self.label_greeble_color_1,
			self.label_greeble_color_2,
			self.label_greeble_color_3,
			self.label_greeble_color_4]
		######################################################################################################################################################################
		# Default values of greeble colors and probabilities
		[entry.insert(0, "0, 0, 0") for entry in self.list_of_all_entries[1:5]]
		[entry.insert(0, "0") for entry in self.list_of_all_entries[6:]]

	def bind_widgets(self):
		# Name color entries for reference in self.get_palette_rgb
		self.dict_entry_names = {
			self.entry_greeble_color_1: "entry_greeble_color_1",
			self.entry_greeble_color_2: "entry_greeble_color_2",
			self.entry_greeble_color_3: "entry_greeble_color_3",
			self.entry_greeble_color_4: "entry_greeble_color_4",
		}
		# Bind the focus event on each Color Entry widget to self.set_focus function
		[entry.bind("<FocusIn>", self.set_focus) for entry in self.list_of_all_entries[1:5]]

		# Bind the focus event on each Probability Entry widget to focus on corresponding color entry
		def bind_prob_entry_focus_to_color_entry_1(*args):
			self.current_entry = self.list_of_all_entries[1]
		def bind_prob_entry_focus_to_color_entry_2(*args):
			self.current_entry = self.list_of_all_entries[2]
		def bind_prob_entry_focus_to_color_entry_3(*args):
			self.current_entry = self.list_of_all_entries[3]
		def bind_prob_entry_focus_to_color_entry_4(*args):
			self.current_entry = self.list_of_all_entries[4]
		self.list_of_all_entries[6].bind("<FocusIn>", lambda event: bind_prob_entry_focus_to_color_entry_1(event))
		self.list_of_all_entries[7].bind("<FocusIn>", lambda event: bind_prob_entry_focus_to_color_entry_2(event))
		self.list_of_all_entries[8].bind("<FocusIn>", lambda event: bind_prob_entry_focus_to_color_entry_3(event))
		self.list_of_all_entries[9].bind("<FocusIn>", lambda event: bind_prob_entry_focus_to_color_entry_4(event))

		def bind_color_label_to_entry_greeble_color_1(*args):
			self.entry_greeble_color_1.focus_set()
		def bind_color_label_to_entry_greeble_color_2(*args):
			self.entry_greeble_color_2.focus_set()
		def bind_color_label_to_entry_greeble_color_3(*args):
			self.entry_greeble_color_3.focus_set()
		def bind_color_label_to_entry_greeble_color_4(*args):
			self.entry_greeble_color_4.focus_set()
		self.list_of_all_color_labels[1].bind("<Button-1>", lambda event: bind_color_label_to_entry_greeble_color_1(event))
		self.list_of_all_color_labels[2].bind("<Button-1>", lambda event: bind_color_label_to_entry_greeble_color_2(event))
		self.list_of_all_color_labels[3].bind("<Button-1>", lambda event: bind_color_label_to_entry_greeble_color_3(event))
		self.list_of_all_color_labels[4].bind("<Button-1>", lambda event: bind_color_label_to_entry_greeble_color_4(event))
		self.list_of_all_color_labels[1].bind("<Button-3>", lambda event: bind_color_label_to_entry_greeble_color_1(event))
		self.list_of_all_color_labels[2].bind("<Button-3>", lambda event: bind_color_label_to_entry_greeble_color_2(event))
		self.list_of_all_color_labels[3].bind("<Button-3>", lambda event: bind_color_label_to_entry_greeble_color_3(event))
		self.list_of_all_color_labels[4].bind("<Button-3>", lambda event: bind_color_label_to_entry_greeble_color_4(event))

		# Bind Enter to entries to change color label and trigger update
		self.list_of_all_entries[0].bind("<Return>", lambda event: self.update_color_label_target_color(event, self.list_of_all_entries[0], self.list_of_all_color_labels[0]))
		for entry, label in zip(self.list_of_all_entries[1:5], self.list_of_all_color_labels[1:]):
			entry.bind("<Return>", lambda event, entry=entry, label=label: self.update_color_label(event, entry, label))
		for prob_entry in self.list_of_all_entries[5:]:
			prob_entry.bind("<Return>", self.update_preview)

		# Bind mouse clicks to get RGB values from the palettes
		self.label_DOS_PALETTE.bind("<Button-1>", lambda event: self.get_palette_rgb(event, self.img_DOS_PALETTE))
		self.label_DOS_PALETTE.bind("<Button-3>", lambda event: self.get_palette_rgb(event, self.img_DOS_PALETTE))
		self.label_RGB_PALETTE.bind("<Button-1>", lambda event: self.get_palette_rgb(event, self.img_RGB_PALETTE))
		self.label_RGB_PALETTE.bind("<Button-3>", lambda event: self.get_palette_rgb(event, self.img_RGB_PALETTE))

		# Bind keys so shortcuts trigger functions without inputing a letter
		for entry in self.list_of_all_entries:
			entry.bind('<plus>' , self.zoom_in)
			entry.bind('<minus>', self.zoom_out)
			entry.bind('o'      , self.open_image)
			entry.bind('s'      , self.save_image)
			entry.bind('l'      , self.load_preset_window)
			entry.bind('r'      , self.update_preview)

	def open_image(self, *args):
		self.greebled_image = None
		self.export_image_data = None
		file_path = filedialog.askopenfilename(filetypes=[('PNG files', '*.png'), ('All files', '*.*')], initialdir=os.getcwd())
		self.image_name = os.path.splitext(os.path.basename(file_path))[0]
		if file_path:
			try:
				self.image      = Image.open(file_path).convert("RGB")    # TODO: IMPLEMENT RGBA
				# self.image_data = self.image.load()
				self.zoom_level = self.default_zoom_level
				if self.target_color:
					self.update_preview()
				else:
					self.display_image()
			except Exception as e:
				messagebox.showerror("Error", f"Could not open image: {e}")
		return "break"

	def display_image(self):
		if self.image:
			# Resize the image according to the zoom level
			width, height = self.image.size
			new_width, new_height = (int(width * self.zoom_level), int(height * self.zoom_level))
			if self.greebled_image:
				self.resized_image = self.greebled_image.resize((new_width, new_height), Image.NEAREST)
			else:
				self.resized_image = self.image.resize((new_width, new_height), Image.NEAREST)
			self.photo = ImageTk.PhotoImage(self.resized_image)

			# Create or update the label to display the image
			if hasattr(self, 'image_canvas'):
				self.image_canvas.config(width=new_width, height=new_height)
				self.image_canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
				self.image_canvas.config(scrollregion=(0, 0, new_width, new_height))
			else:
				self.image_canvas = tk.Canvas(self.image_FRAME, width=new_width, height=new_height, cursor="tcross")
				self.image_canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
				self.image_canvas.bind("<Button-1>", self.get_pixel_rgb)
				self.image_canvas.bind("<Button-3>", self.get_pixel_rgb)
				self.x_scroll = ttk.Scrollbar(self.image_FRAME, orient=tk.HORIZONTAL, command=self.image_canvas.xview)
				self.y_scroll = ttk.Scrollbar(self.image_FRAME, orient=tk.VERTICAL, command=self.image_canvas.yview)
				self.x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
				self.y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
				self.image_canvas.config(xscrollcommand=self.x_scroll.set, yscrollcommand=self.y_scroll.set)
				self.image_canvas.config(scrollregion=(0, 0, new_width, new_height))
				self.image_canvas.pack()

	def scroll_left(self, event):
		self.image_canvas.xview_scroll(-1, "units")
	def scroll_right(self, event):
		self.image_canvas.xview_scroll(1, "units")
	def scroll_up(self, event):
		self.image_canvas.yview_scroll(-1, "units")
	def scroll_down(self, event):
		self.image_canvas.yview_scroll(1, "units")

	def zoom_in(self, *args):
		if self.image:
			if self.zoom_level < 16:
				self.zoom_level *= 2
				self.display_image()
		return "break"

	def zoom_out(self, *args):
		if self.image:
			if self.zoom_level > 1:
				self.zoom_level /= 2
				self.display_image()
		return "break"

	def get_pixel_rgb(self, event):
		if self.image:
			x = int(event.x + self.image_canvas.xview()[0] * self.image_canvas.bbox("all")[2])
			y = int(event.y + self.image_canvas.yview()[0] * self.image_canvas.bbox("all")[3])
			try:
				pixel = self.resized_image.getpixel((x, y))
				self.target_color = pixel
				rgb   = f"{pixel}"
				self.rgb_entry.delete(0, tk.END)
				self.rgb_entry.insert(0, rgb[1:-1])

				# Update the color display
				hex_color = rgb_to_hex(pixel)
				self.color_display.config(bg=hex_color)
			except Exception as e:
				messagebox.showerror("Error", f"Could not get pixel data: {e}")

			# Update the preview and normalize probabilities if needed
			self.update_preview()

	def get_palette_rgb(self, event, img):
		x, y = event.x, event.y
		try:
			pixel = img.getpixel((x, y))
			rgb = f"{pixel}"
			# Insert the RGB value into the currently focused Entry widget
			if self.current_entry:
				self.current_entry.delete(0, tk.END)
				self.current_entry.insert(0, rgb[1:-1])

				# Update the color display
				hex_color = rgb_to_hex(pixel)
				if self.dict_entry_names[self.current_entry] == "entry_greeble_color_1":
					self.label_greeble_color_1.config(bg=hex_color)
				elif self.dict_entry_names[self.current_entry] == "entry_greeble_color_2":
					self.label_greeble_color_2.config(bg=hex_color)
				elif self.dict_entry_names[self.current_entry] == "entry_greeble_color_3":
					self.label_greeble_color_3.config(bg=hex_color)
				elif self.dict_entry_names[self.current_entry] == "entry_greeble_color_4":
					self.label_greeble_color_4.config(bg=hex_color)
		except Exception as e:
			messagebox.showerror("Error", f"Could not get pixel data: {e}")

		# Update the preview and normalize probabilities if needed
		self.update_preview()

		return "break"

	def set_focus(self, event):
		# Set the currently focused entry widget
		self.current_entry = event.widget

	def normalize_probabilities(self):
		""" Function to round probabilities; normalize to 100 % if needed """
		try:
			probabilities = [float(self.rgb_prob_entry.get()),
							 float(self.entry_greeble_color_prob_1.get()),
							 float(self.entry_greeble_color_prob_2.get()),
							 float(self.entry_greeble_color_prob_3.get()),
							 float(self.entry_greeble_color_prob_4.get())]
		except ValueError:
			return None

		norm_prob = [round(x/sum(probabilities)*100) for x in probabilities]

		for i, prob_entry in enumerate(self.list_of_all_entries[5:]):
			prob_entry.delete(0, tk.END)
			prob_entry.insert(0, norm_prob[i])

		# Get rid of the rounding error
		if 100-sum(norm_prob) != 0:
			norm_prob[0] = norm_prob[0] + 100-sum(norm_prob)
			return norm_prob
		else:
			return norm_prob

	def update_preview(self, *args):
		self.focus_set()
		self.add_greeble_pixels()
		self.display_image()

	def add_greeble_pixels(self):
		colors_of_greeble, probabilities_of_greeble = self.get_all_values()
		if not all([colors_of_greeble, probabilities_of_greeble]):
			return
		if not self.image:
			return

		# Highlight matching color in palette
		self.highlight_color_in_palette(colors_of_greeble[0:6])

		# Convert probs from 0-100 % to 0.00-1.00
		probabilities_of_greeble = [x/100 for x in probabilities_of_greeble]

		self.greebled_image    = self.image.copy()
		greebled_image_data    = self.greebled_image.load()
		self.export_image      = self.image.copy()
		self.export_image_data = []
		for y in range(0, self.image.height):
			for x in range(0, self.image.width):
				if greebled_image_data[x, y] == self.target_color:
					n = np.random.choice(len(colors_of_greeble), p=probabilities_of_greeble)
					greebled_image_data[x, y] = colors_of_greeble[n]
					self.export_image_data.append(colors_of_greeble[n] + (255,))
				else:
					self.export_image_data.append((255, 255, 255, 0))

	def get_tuple_from_str(self, entry):
		s = entry.get()
		if not (s.startswith('(') and s.endswith(')')):
			s = f"({s})"
		try:
			# Try to evaluate the string as a tuple
			result = ast.literal_eval(s)
			# Check if the result is a tuple
			if isinstance(result, tuple):
				return result
		except (ValueError, SyntaxError):
			messagebox.showerror("Error", f'Colors have to be in the format "R, G, B".')
			return False

	def save_image(self, *args):
		if not (self.image and self.greebled_image):
			return "break"
		else:
			if self.checkbox_var.get() == 1:
				export_image = Image.new("RGBA", self.image.size)
				export_image.putdata(self.export_image_data)
				file_path = filedialog.asksaveasfilename(filetypes = [('PNG files', '*.png'), ('All files', '*.*')], defaultextension = '*.png', initialfile=self.image_name+"_")
				if file_path: export_image.save(file_path)
			elif self.checkbox_var.get() == 0:
				file_path = filedialog.asksaveasfilename(filetypes = [('PNG files', '*.png'), ('All files', '*.*')], defaultextension = '*.png', initialfile=self.image_name+"_edited")
				if file_path: self.greebled_image.save(file_path)
		return "break"

	def get_all_values(self, colors=True, probs=True):
		""" Function to get values from all entry widgets
			Returns one or two lists ('None' for each, if the strings are not numbers) """
		if colors and probs:
			colors_of_greeble = [self.get_tuple_from_str(color_entry) for color_entry in self.list_of_all_entries[0:5]]
			if not all(colors_of_greeble):
				return None, None

			probabilities_of_greeble = self.normalize_probabilities()
			if not probabilities_of_greeble:
				return None, None
			return colors_of_greeble, probabilities_of_greeble

		elif colors and not probs:
			colors_of_greeble = [self.get_tuple_from_str(color_entry) for color_entry in self.list_of_all_entries[0:5]]
			if not all(colors_of_greeble):
				return None
			return colors_of_greeble

		elif probs and not colors:
			probabilities_of_greeble = self.normalize_probabilities()
			if not probabilities_of_greeble:
				return None
			return probabilities_of_greeble

	def load_preset_window(self, *args):
		from greeblefier_GUI_files.presets import dict_of_presets
		if len(dict_of_presets) == 0:
			messagebox.showinfo(title="No presets", message="There are no stored presets.")
			return

		def close_preset_window(*args):
			preset_window.destroy()

		preset_window = tk.Toplevel(self)
		preset_window.title("Select a Preset")
		preset_window.configure(bg=self.color_bckgnd)
		preset_window.bind('<Escape>', close_preset_window)
		preset_window.focus_set()
		preset_window.grab_set()
		
		# Dynamically create buttons and labels for each preset
		for i, (preset_name, preset_data) in enumerate(dict_of_presets.items()):
			# Load colors as tuples of RGB, replace  convert them to HEX
			colors = [preset_data['colors'][i] for i in range(len(preset_data['colors']))]
			colors = [color if color != (0, 0, 0) else (211, 211, 211) for color in colors]
			colors = [rgb_to_hex(color) for color in colors]

			# Initialize row and column counters (commented for the option to hardcode no. of rows or columns)
			# current_row = 0
			# current_column = 0
			# ITEMS_PER_COLUMN = 4
			# ITEMS_PER_ROW = 4
			LABEL_WIDTH = 20
			LABEL_HEIGHT = 2
			n = len(dict_of_presets)
			cols = math.ceil(math.sqrt(n))
			rows = math.ceil(n / cols)

			# Create a FRAME for each preset
			preset_FRAME = tk.Frame(preset_window, bg=self.color_bckgnd,
												   highlightbackground="black",
												   highlightcolor="black",
												   highlightthickness=1, bd=2)
			preset_FRAME.grid(row=i // cols, column=i % cols, padx=10, pady=12)
			# Create the button with the preset name, matching the size of color_label_0
			font_presets_button = ('Tahoma', 8)
			style = ttk.Style()
			style.configure('presets.TButton', font=font_presets_button)
			preset_button = ttk.Button(preset_FRAME, text=preset_name,
													 width=LABEL_WIDTH,
													 command=lambda name=preset_name: self.load_preset(name, dict_of_presets, preset_window),
													 style='presets.TButton')
			preset_button.pack(fill="x", pady=4, ipady=LABEL_HEIGHT * 4)
			# Create a top FRAME to hold the top label (full width, 130px) and bottom label FRAME
			top_label_FRAME = tk.Frame(preset_FRAME, bg=self.color_bckgnd)
			top_label_FRAME.pack(pady=4)
			color_label_0 = tk.Label(top_label_FRAME, text=preset_data['probabilities'][0], bg=colors[0], width=LABEL_WIDTH, height=LABEL_HEIGHT)
			color_label_0.pack(fill="x")
			# Bottom label FRAME for the smaller labels. loop through the remaining colors and probabilities to create labels
			bottom_label_FRAME = tk.Frame(top_label_FRAME, width=130, bg=self.color_bckgnd)
			bottom_label_FRAME.pack()
			for i in range(1, 5):
				color_label = tk.Label(bottom_label_FRAME, text=preset_data['probabilities'][i], bg=colors[i], width=5, height=2)
				color_label.pack(side="left", padx=1, pady=5)
			# Add the delete button
			style.configure('delete.TButton', foreground='grey', font=font_presets_button)
			delete_button = ttk.Button(top_label_FRAME, text="Delete",
														command=lambda name=preset_name: self.delete_preset(name, dict_of_presets, preset_window),
														style='delete.TButton')
			delete_button.pack(side="bottom", ipady=LABEL_HEIGHT*0.25, fill=tk.X)

			# # Manage row and column counters to move to a new column after 10 items
			# current_column += 1
			# if (i + 1) % ITEMS_PER_ROW == 0:
			#     current_column = 0
			#     current_row += 1

		return "break"

	def delete_preset(self, preset_name, dict_of_presets, preset_window):
		del(dict_of_presets[preset_name])
		self.save_preset_to_file(dict_of_presets)
		preset_window.destroy()
		self.load_preset_window()

	def load_preset(self, preset_name, dict_of_presets, preset_window):
		selected_preset = dict_of_presets[preset_name]
		preset_window.destroy()
		values = list(selected_preset.values())      # values is two lists [[colors], [probs]]
		values_list_of_strings = [str(item) for list in values for item in list]   # flatten values
		# Insert colors - RGB values without ( )
		counter = 0
		for entry in self.list_of_all_entries[0:5]:
			entry.delete(0, tk.END)
			entry.insert(0, values_list_of_strings[counter][1:-1])
			counter += 1
		# Insert probabilities
		for entry in self.list_of_all_entries[5:]:
			entry.delete(0, tk.END)
			entry.insert(0, values_list_of_strings[counter])
			counter += 1

		# Update color showing labels
		colors = [color if color != (0, 0, 0) else (211, 211, 211) for color in values[0]]
		hex_colors = [rgb_to_hex(color) for color in colors]
		for label, color in zip(self.list_of_all_color_labels, hex_colors):
			label.configure(bg=color)
		self.target_color = colors[0]
		if self.image:
			self.update_preview()

	# def set_all_values(self, values):
	# 	for i, entry in enumerate(self.list_of_all_entries):
	# 		entry.delete(0, tk.END)
	# 		entry.insert(0, values[i])

	def update_color_label(self, event, entry, label):
		self.focus_set()
		s = entry.get()
		color = self.get_tuple_from_str(entry)
		if not color:
			return
		color_as_HEX = rgb_to_hex(color)
		label.configure(bg=color_as_HEX)
		self.update_preview()

	# TODO: DRY? combine --^  and --v
	def update_color_label_target_color(self, event, entry, label):
		self.focus_set()
		s = entry.get()
		color = self.get_tuple_from_str(entry)
		if not color:
			return
		self.target_color = color
		color_as_HEX = rgb_to_hex(color)
		label.configure(bg=color_as_HEX)
		self.update_preview()

	def save_preset_dialog(self, *args):
		colors, probabilities = self.get_all_values(colors=True, probs=True)
		if not colors or not probabilities:
			messagebox.showerror("Error", "Colors have to be tuples of (R,G,B).\nProbabilities have to be integers.")
			return

		name_of_preset = simpledialog.askstring("Name", "Save preset as: (use unaccented characters)")
		if not name_of_preset:
			return

		from greeblefier_GUI_files.presets import dict_of_presets
		if name_of_preset in dict_of_presets:
			response = messagebox.askokcancel(title=f"{name_of_preset}", message=f"'{name_of_preset}' already exists.\nDo you want to overwrite the old preset?")
			if not response:
				return
		
		preset_data = {"colors": colors,
					   "probabilities": probabilities}
		dict_of_presets[name_of_preset] = preset_data

		self.save_preset_to_file(dict_of_presets)

	def save_preset_to_file(self, dict_of_presets):
		# Save the dict of presets as a formatted string
		prefix = """# Dictionary of saved presets.
# You can edit the database manually, but be mindful
# not to disrupt the syntax of round (), square [] and curly brackets{}.

"""
		formatted_dict = pprint.pformat(dict_of_presets, indent=4)
		with open("greeblefier_GUI_files/presets.py", "w") as file:
			file.write(prefix + "dict_of_presets = {" + "\n " +  formatted_dict[1:])

	def copy_image_to_clipboard(self, *args):
		# Save the image to an in-memory file
		output = io.BytesIO()
		if self.checkbox_var.get() == 1:
			if self.image and self.export_image_data:
				image = Image.new("RGBA", self.image.size)
				image.putdata(self.export_image_data)
			else: return
		elif self.checkbox_var.get() == 0:
			if self.greebled_image:
				image = self.greebled_image
			else: return

		image.save(output, format="BMP")
		# Strip BMP header
		data = output.getvalue()[14:]  
		output.close()

		win32clipboard.OpenClipboard()
		win32clipboard.EmptyClipboard()
		win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
		win32clipboard.CloseClipboard()

	def insert_image_from_clipboard(self, *args):
		try:
			clipboard_image = ImageGrab.grabclipboard()
			# Test if image was in clipboard
			if isinstance(clipboard_image, Image.Image):
				self.image = clipboard_image.convert("RGB")		# TODO: IMPLEMENT RGBA
				self.image_name = "new_image"
				self.zoom_level = 2
				self.display_image()
				if self.target_color:
					self.update_preview()
		except Exception as e:
			messagebox.showerror("Error", f"Cannot paste image: {e}")

		return "break"

	def highlight_color_in_palette(self, colors):
		""" Draw a border around the matching color """
		img_copy = self.img_DOS_PALETTE.copy()		# Load again to avoid drawing multiple borders
		pixels = img_copy.load()
		draw = ImageDraw.Draw(img_copy)
		
		# Find and highlight target color
		found_target_color = False
		for y in range(0, img_copy.height, 16):
			for x in range(0, img_copy.width, 16):
				if pixels[x, y] == colors[0]:
					draw.rectangle([(x+0, y+0), (x+15, y+15)], outline="#000000", width=1)
					draw.rectangle([(x+1, y+1), (x+14, y+14)], outline="#00ff00", width=1)
					draw.rectangle([(x+2, y+2), (x+13, y+13)], outline="#000000", width=1)
					found_target_color = True
					break
			if found_target_color:
				break

		# Find and highlight greeble colors
		found_greeble_color = False
		for y in range(0, img_copy.height, 16):
			for x in range(0, img_copy.width, 16):
				if pixels[x, y] == (0, 0, 0):
					continue
				elif pixels[x, y] in colors[1:]:
					draw.rectangle([(x+0, y+0), (x+15, y+15)], outline="#000000", width=1)
					draw.rectangle([(x+1, y+1), (x+14, y+14)], outline="#ffff00", width=1)
					draw.rectangle([(x+2, y+2), (x+13, y+13)], outline="#000000", width=1)
					found_greeble_color = True
					continue

		if found_target_color or found_greeble_color:
			img_tk = ImageTk.PhotoImage(img_copy)
			self.label_DOS_PALETTE.config(image=img_tk)
			self.label_DOS_PALETTE.image = img_tk  			# Keep a reference to avoid garbage collection
		else:
			img_tk = ImageTk.PhotoImage(self.img_DOS_PALETTE)
			self.label_DOS_PALETTE.config(image=img_tk)
			self.label_DOS_PALETTE.image = img_tk
			pass



if __name__ == '__main__':
	Greeblefier(default_zoom=4, maximize_window=True, ask_to_exit=False)




