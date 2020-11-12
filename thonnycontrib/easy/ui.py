import concurrent.futures
import tkinter as tk
import traceback
from tkinter import ttk, messagebox
from typing import Tuple, List, Optional

from thonny import tktextext, get_workbench
from thonny.ui_utils import scrollbar_style, lookup_style_option

from .htmltext import FormData, HtmlText, HtmlRenderer

EDITOR_CONTENT_NAME = "$EDITOR_CONTENT"


class ExercisesView(ttk.Frame):
    def __init__(self, master, exercise_provider_class):
        self._destroyed = False
        super().__init__(master, borderwidth=0, relief="flat")

        self._provider = exercise_provider_class(self)
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=self._provider.get_max_threads())
        self._page_future = None  # type: Optional[concurrent.futures.Future]

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.vert_scrollbar = ttk.Scrollbar(
            self, orient=tk.VERTICAL, style=scrollbar_style("Vertical")
        )
        self.vert_scrollbar.grid(row=0, column=1, sticky=tk.NSEW, rowspan=3)

        tktextext.fixwordbreaks(tk._default_root)
        self.init_header(row=0, column=0)

        spacer = ttk.Frame(self, height=1)
        spacer.grid(row=1, sticky="nsew")

        self._html_widget = HtmlText(
            master=self,
            renderer_class=ExerciseHtmlRenderer,
            link_and_form_handler=self._on_request_new_page,
            read_only=True,
            wrap="word",
            font="TkDefaultFont",
            padx=10,
            pady=0,
            insertwidth=0,
            borderwidth=0,
            highlightthickness=0,
            yscrollcommand=self.vert_scrollbar.set
        )

        self._html_widget.grid(row=1, column=0, sticky="nsew")

        self.vert_scrollbar["command"] = self._html_widget.yview

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
        # self.menu_button.grid(row=0, column=1, sticky="ne")
        self.menu_button.place(anchor="ne", rely=0, relx=1)

    def _on_request_new_page(self, target, form_data=None):
        if target.startswith("/"):
            self.go_to(target, form_data=form_data)
        else:
            get_workbench().open_url(target)

    def post_button_menu(self):
        """
        self.refresh_menu(context="button")
        self.menu.tk_popup(
            self.menu_button.winfo_rootx(),
            self.menu_button.winfo_rooty() + self.menu_button.winfo_height(),
        )
        """

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
        return get_workbench().get_image(name)


class ExerciseProvider:
    def get_html_and_breadcrumbs(self, url: str, form_data: FormData) -> Tuple[str, List[Tuple[str, str]]]:
        raise NotImplementedError()

    def get_image(self, url):
        raise NotImplementedError()

    def get_max_threads(self):
        return 10
