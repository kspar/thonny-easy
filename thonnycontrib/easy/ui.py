import concurrent.futures
import tkinter as tk
import traceback
from io import BytesIO
from tkinter import ttk, messagebox
from typing import Tuple, List, Optional, Callable, Union
from urllib.request import urlopen

from thonny import tktextext, get_workbench
from thonny.ui_utils import scrollbar_style, lookup_style_option

from .htmltext import FormData, HtmlText, HtmlRenderer

EDITOR_CONTENT_NAME = "$EDITOR_CONTENT"

_images_by_urls = {}


class ExercisesView(ttk.Frame):
    def __init__(self, master, exercise_provider_class):
        self._destroyed = False
        self._poll_scheduler = None
        super().__init__(master, borderwidth=0, relief="flat")

        self._provider = exercise_provider_class(self)
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=self._provider.get_max_threads())
        self._page_future = None  # type: Optional[concurrent.futures.Future]
        self._image_futures = {}

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.vert_scrollbar = ttk.Scrollbar(
            self, orient=tk.VERTICAL, style=scrollbar_style("Vertical")
        )
        self.vert_scrollbar.grid(row=0, column=1, sticky=tk.NSEW, rowspan=2)

        self.hor_scrollbar = ttk.Scrollbar(
            self, orient=tk.HORIZONTAL, style=scrollbar_style("Horizontal")
        )
        self.hor_scrollbar.grid(row=2, column=0, sticky=tk.NSEW)

        tktextext.fixwordbreaks(tk._default_root)
        self.init_header(row=0, column=0)

        spacer = ttk.Frame(self, height=1)
        spacer.grid(row=1, sticky="nsew")

        self._html_widget = HtmlText(
            master=self,
            renderer_class=ExerciseHtmlRenderer,
            link_and_form_handler=self._on_request_new_page,
            image_requester=self._on_request_image,
            read_only=True,
            wrap="word",
            font="TkDefaultFont",
            padx=10,
            pady=0,
            insertwidth=0,
            borderwidth=0,
            highlightthickness=0,
            yscrollcommand=self.vert_scrollbar.set,
            xscrollcommand=self.hor_scrollbar.set,
        )

        self._html_widget.grid(row=1, column=0, sticky="nsew")

        self.vert_scrollbar["command"] = self._html_widget.yview
        self.hor_scrollbar["command"] = self._html_widget.xview

        self._poll_scheduler = None

        # TODO: go to last page from previous session?
        self.go_to("/")
        self._poll_provider_responses()

    def _poll_provider_responses(self):
        if self._destroyed:
            return

        if self._page_future is not None and self._page_future.done():
            # Cancelled futures won't make it here
            assert not self._page_future.cancelled()

            exc = self._page_future.exception()
            if exc is not None:
                self._set_page_html("<pre>%s</pre>" %
                                    "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
                                    )
            else:
                html, breadcrumbs = self._page_future.result()
                self._set_page_html(html)
                self.breadcrumbs_bar.set_links(breadcrumbs)

            self._page_future = None

        remaining_img_futures = {}
        for url, fut in self._image_futures.items():
            if fut.done():
                try:
                    data = fut.result()
                except:
                    traceback.print_exc()
                else:
                    self._update_image(url, fut.result())

            else:
                remaining_img_futures[url] = fut
        self._image_futures = remaining_img_futures

        self._poll_scheduler = self.after(200, self._poll_provider_responses)

    def init_header(self, row, column):
        header_frame = ttk.Frame(self, style="ViewToolbar.TFrame")
        header_frame.grid(row=row, column=column, sticky="nsew")
        header_frame.columnconfigure(0, weight=1)

        self.breadcrumbs_bar = BreadcrumbsBar(header_frame, self._on_request_new_page)

        self.breadcrumbs_bar.grid(row=0, column=0, sticky="nsew")

        # self.menu_button = ttk.Button(header_frame, text="≡ ", style="ViewToolbar.Toolbutton")
        self.menu_button = ttk.Button(
            header_frame, text=" ≡ ", style="ViewToolbar.Toolbutton", command=self.post_button_menu
        )
        self._button_menu = tk.Menu(header_frame, tearoff=False)
        # self.menu_button.grid(row=0, column=1, sticky="ne")
        self.menu_button.place(anchor="ne", rely=0, relx=1)

    def _on_request_new_page(self, target, form_data=None):
        if target.startswith("/"):
            self.go_to(target, form_data=form_data)
        else:
            get_workbench().open_url(target)

    def _on_request_image(self, url):
        assert url is not None

        if url not in self._image_futures:
            self._image_futures[url] = self._executor.submit(self._provider.get_image, url)

    def post_button_menu(self):
        self._button_menu.delete(0, "end")

        items = self._provider.get_menu_items()
        if not items:
            return

        for label, handler in items:
            if label == "-":
                self._button_menu.add_separator()
            else:
                if isinstance(handler, str):
                    def command(url=handler):
                        self.go_to(url)
                else:
                    command = handler

                self._button_menu.add_command(label=label, command=command)

        self._button_menu.tk_popup(
            self.menu_button.winfo_rootx(),
            self.menu_button.winfo_rooty() + self.menu_button.winfo_height(),
        )

    def go_to(self, url, form_data=None):
        if form_data is None:
            form_data = FormData()

        assert url.startswith("/")
        if self._page_future is not None:
            self._page_future.cancel()

        self._page_future = self._executor.submit(
            self._provider.get_html_and_breadcrumbs, url, form_data)
        self._set_page_html("<p>Palun oota...</p>")

    def _set_page_html(self, html):
        self._html_widget.set_html_content(html)

    def _make_tk_image(self, data):
        try:
            from PIL import Image
            from PIL.ImageTk import PhotoImage
            with BytesIO(data) as fp:
                fp.seek(0)
                pil_img = Image.open(fp)

                # Resize while keeping the aspect ratio
                basewidth = 250
                wpercent = (basewidth / float(pil_img.size[0]))
                hsize = int((float(pil_img.size[1]) * float(wpercent)))
                return PhotoImage(pil_img.resize((basewidth, hsize), Image.ANTIALIAS))

        except ImportError:
            return tk.PhotoImage(data=data)

    def _update_image(self, url, data):
        try:
            tk_img = self._make_tk_image(data)
        except:
            traceback.print_exc()
            return

        _images_by_urls[url] = tk_img
        self._html_widget.update_image(url, tk_img)

    def destroy(self):
        if self._poll_scheduler is not None:
            try:
                self.after_cancel(self._poll_scheduler)
                self._poll_scheduler = None
            except:
                pass

        super(ExercisesView, self).destroy()
        self._destroyed = True


class BreadcrumbsBar(tktextext.TweakableText):
    def __init__(self, master, click_handler):
        super(BreadcrumbsBar, self).__init__(
            master,
            borderwidth=0,
            relief="flat",
            height=1,
            font="TkDefaultFont",
            wrap="word",
            padx=6,
            pady=5,
            insertwidth=0,
            highlightthickness=0,
            background=lookup_style_option("ViewToolbar.TFrame", "background"),
            read_only=True,
        )

        self._changing = False
        self.bind("<Configure>", self.update_height, True)

        self.tag_configure("_link", foreground=lookup_style_option("Url.TLabel", "foreground"))
        self.tag_configure("_underline", underline=True)
        self.tag_bind("_link", "<1>", self._link_click)
        self.tag_bind("_link", "<Enter>", self._link_enter)
        self.tag_bind("_link", "<Leave>", self._link_leave)
        self.tag_bind("_link", "<Motion>", self._link_motion)

        self._click_handler = click_handler

    def set_links(self, links):
        try:
            self._changing = True

            self.direct_delete("1.0", "end")
            if not links:
                return

            # remove trailing newline
            links = links[:]
            links[-1] = (links[-1][0], links[-1][1].rstrip("\r\n"))

            for key, label in links:
                self.direct_insert("end", "/\xa0")
                if not label.endswith("\n"):
                    label += " "

                self.direct_insert("end", label, ("_link", key))
        finally:
            self._changing = False
            self.update_height()

    def update_height(self, event=None):
        if self._changing:
            return
        height = self.tk.call((self, "count", "-update", "-displaylines", "1.0", "end"))
        self.configure(height=height)

    def _link_click(self, event):
        mouse_index = self.index("@%d,%d" % (event.x, event.y))
        user_tags = [
            tag for tag in self.tag_names(mouse_index) if tag not in ["_link", "_underline"]
        ]
        if len(user_tags) == 1:
            self._click_handler(user_tags[0])

    def _get_link_range(self, event):
        mouse_index = self.index("@%d,%d" % (event.x, event.y))
        return self.tag_prevrange("_link", mouse_index + "+1c")

    def _link_motion(self, event):
        self.tag_remove("_underline", "1.0", "end")
        dir_range = self._get_link_range(event)
        if dir_range:
            range_start, range_end = dir_range
            self.tag_add("_underline", range_start, range_end)

    def _link_enter(self, event):
        self.config(cursor="hand2")

    def _link_leave(self, event):
        self.config(cursor="")
        self.tag_remove("_underline", "1.0", "end")


class ExerciseHtmlRenderer(HtmlRenderer):
    def _expand_field_value(self, value_holder, attrs):
        if attrs["type"] == "hidden" and attrs["name"] == EDITOR_CONTENT_NAME:
            value = get_workbench().get_editor_notebook().get_current_editor_content()
            if value is None:
                messagebox.showerror("Ei saa esitada", "Puudub aktiivne redaktor. Ei ole midagi esitada.", master=self)
                return False
            else:
                return value
        else:
            return super(ExerciseHtmlRenderer, self)._expand_field_value(value_holder, attrs)

    def _get_image(self, name):
        # Previously seen images can be given synchronously
        if name in _images_by_urls:
            return _images_by_urls[name]

        if self._image_requester is not None:
            # others should be requested asynchronously
            self._image_requester(name)

        return None


class ExerciseProvider:
    def get_html_and_breadcrumbs(self, url: str, form_data: FormData) -> Tuple[str, List[Tuple[str, str]]]:
        raise NotImplementedError()

    def get_image(self, url) -> bytes:
        return urlopen(url).read()

    def get_max_threads(self) -> int:
        return 10

    def get_menu_items(self) -> List[Tuple[str, Union[str, Callable, None]]]:
        """
        This will be called each time the user clicks on the menu button.

        First item in each pair is Text of the menu item ("-" if you want to create a separator)
        Second item:
            str is interpreted as a provider url, fetched in a thread (just like clicking on a link)
            None means the item is not available at this moment
            a callable is executed in UI thread (without arguments)
        """
        return []
