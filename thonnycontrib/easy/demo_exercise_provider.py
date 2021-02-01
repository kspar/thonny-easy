import time
import tkinter
from tkinter import messagebox
from typing import Tuple, List, Union, Callable

from thonny import get_workbench
from .ui import ExerciseProvider, FormData, EDITOR_CONTENT_NAME


class DemoExerciseProvider(ExerciseProvider):
    def __init__(self, exercises_view):
        self.exercises_view = exercises_view

    def get_html_and_breadcrumbs(
            self, url: str, form_data: FormData
    ) -> Tuple[str, List[Tuple[str, str]]]:
        time.sleep(1)
        #raise RuntimeError("Not right")
        if url == "/ex1":
            return (self._get_ex_text(1), [("/", "Home"), ("/ex1", "Ülesanne 1")])
        elif url == "/ex2":
            return (self._get_ex_text(2), [("/", "Home"), ("/ex2", "Ülesanne 2")])
        elif url == "/ex1/submit":
            return (self._get_submit_text(form_data), [("/", "Home"), ("/ex1", "Ülesanne 1")])
        elif url == "/ex2/submit":
            return (self._get_submit_text(form_data), [("/", "Home"), ("/ex1", "Ülesanne 1")])
        elif url == "/logout":
            return ("<p>Bye!</p>", [("/", "Home")])
        else:
            return (self._get_benchmark_page2(), [("/", "Home")])

    def _get_ex_list(self):
        return """
            <ul>
                <li><a href="/ex1">Ülesanne 1</a></li>
                <li><a href="/ex2">Ülesanne 2</a></li>
            </ul>
        """

    def _get_benchmark_page1(self):
        return """
<div class="paragraph"> 
 <p>Alates 2014. aastast on Eesti Lepidopteroloogide Selts igal aastal valinud aasta liblika. Tänavune aasta liblikas on <a href="https://et.wikipedia.org/wiki/Teelehe-mosaiikliblikas" target="_blank" rel="noopener noreferrer">teelehe-mosaiikliblikas</a>.</p> 
</div> 
<div class="imageblock"> 
 <div class="content"> 
  <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/5/55/Marsh_fritillary_%28Euphydryas_aurinia%29_male.jpg/1280px-Marsh_fritillary_%28Euphydryas_aurinia%29_male.jpg" alt="euphydryas_aurinia" width="350"> 
 </div> 
</div> 
<div class="paragraph"> 
 <p>Koostada programm, mille</p> 
</div> 
<div class="ulist"> 
 <ul> 
  <li> <p>1. real luuakse muutuja nimega <code>aasta</code> ning antakse sellele väärtuseks <code>2020</code> (arvuna);</p> </li> 
  <li> <p>2. real luuakse muutuja nimega <code>liblikas</code> ning antakse sellele väärtuseks <code>"teelehe-mosaiikliblikas"</code> (sõnena);</p> </li> 
  <li> <p>3. real luuakse muutuja nimega <code>lause_keskosa</code> ning antakse sellele väärtuseks <code>". aasta liblikas on "</code> (sõnena);</p> </li> 
  <li> <p>4. real luuakse muutuja nimega <code>lause</code>, mille väärtuse saamiseks ühendatakse üheks sõnaks muutujad <code>aasta</code>, <code>lause_keskosa</code> ja <code>liblikas</code> (vajadusel tuleb kasutada funktsiooni, mis teisendab arvu sõneks);</p> </li> 
  <li> <p>5. real väljastatakse muutuja <code>lause</code> väärtus ekraanile.</p> </li> 
 </ul> 
</div> 
<div class="paragraph"> 
 <p>Kuigi tegelikult pannakse lause lõppu punkt, siis siin ärge pange. (Automaatkontroll isegi annab punkti või mõne muu üleliigse osa korral veateate.)</p>
 <hr/>
 <p>Peale hr-i</p>
</div>
<details>
<summary class="title">Näited programmi tööst</summary> 
 <div class="content"> 
  <div class="listingblock"> 
   <div class="content"> 
    <pre class="highlightjs highlight"><code data-lang="python" class="language-python hljs">&gt;&gt;&gt; <span class="codehl run">%Run yl1.2.py</span>
  <span class="codehl nohl">2020. aasta liblikas on teelehe-mosaiikliblikas</span></code></pre> 
   </div> 
  </div> 
 </div> 
</details> 
<div class="paragraph"> 
 <p>Kui olete juba hulk aega proovinud ülesannet iseseisvalt lahendada ja see ikka ei õnnestu, siis võib-olla saate abi <a href="https://progtugi.cs.ut.ee#/ts/5e57914b50ad8d0325d312fb/" target="_blank" rel="noopener noreferrer">murelahendajalt</a>. Püütud on tüüpilisemaid probleemseid kohti selgitada ja anda vihjeid.</p> 
</div>        
        """

    def _get_benchmark_page2(self):
        return """
<div>
    <p>2016. aastal registreeriti Eestis 1145 uut mootorratast. Registeeritud mootorrataste andmed on kuude kaupa failis
        <code>mootorrattad.txt</code>, kus esimesel real on jaanuaris registreeritud tsiklite arv, teisel real
        veebruaris registreeritud tsiklite arv jne. Faili võite salvestada <a href="https://courses.cs.ut.ee/MTAT.TK.012/2016_fall/uploads/Main/mootorrattad.txt">siit</a> või koostada ise mõne tekstiredaktoriga.
    </p>
    <p>Koostada programm, mis</p>
    <ol>
        <li>loeb failist registreeritud mootorrataste andmed kuude järgi järjendisse;
            <ul class="browser-default">
                <li>Failist järjendisse saab lugeda järgmise programmijupi abil:
                    <br>
                    <code>fail = open("mootorrattad.txt", encoding="UTF-8")</code>
                    <br>
                    <code>mootorrattad = []</code>
                    <br>
                    <code>for rida in fail:</code>
                    <br>
                    <code>&nbsp;&nbsp;&nbsp;&nbsp;mootorrattad.append(int(rida))</code>
                    <br>
                    <code>fail.close()</code>
                </li>
                Viide: <a href="https://web.htk.tlu.ee/digitaru/programmeerimine/chapter/andmed-failist/">Andmed
                failist</a>
            </ul>
        </li>
        <li>küsib kasutajalt täisarvu, mis tähistab ühe kuu järjekorranumbrit (jaanuar 1, veebruar 2 jne);</li>
        <li>väljastab, mitu uut mootorratast sel kuul registreeriti.</li>
    </ol>

    <p>Näited programmi tööst:</p>
    <img src="https://courses.cs.ut.ee/2017/eprogalkool/fall/uploads/Main/yl5.1.png"/>
    
    <p>Kui olete juba hulk aega<br/>proovinud ülesannet iseseisvalt lahendada ja see ikka ei õnnestu, siis võib-olla saate
        abi <a href="http://progtugi.cs.ut.ee/#/ts/58a1da8ff953770b0ab52569/">murelahendajalt</a>. Püütud on
        tüüpilisemaid probleemseid kohti selgitada ja anda vihjeid.</p>

    
    <img src="https://lh3.googleusercontent.com/proxy/JJ1t0Lmr0dA8EsWIOZgLHfhqH4lezdc-etNQQRDXt9vVyD-fwynb7r4Zku8mglBgA3wHJRA_vFzJkW56hhTlyzeNepDRZZMIUsskTKvfImaJ3DK8Qx_ybKgMbbEks_jNhxtxrJCfTC7lhlJhxpNFe2-ng-bgzjLydSk3ku626nsPZQ2LECoRp70J-w"/>

</div>       

<h2>Viimane esitus</h2>
<br/>
<code>
>>> asdfasdf
123
</code>
<br/>

<form action="/student/courses/{{course_id}}/exercises/{{exercise_id}}/submissions">
    <input type="hidden" name="{{EDITOR_CONTENT_NAME}}"/>
    <input type="submit" value="Esita aktiivse redaktori sisu"/>
</form> 
 """

    def _get_ex_text(self, num):

        return """
    <h1>Ülesanne {num}</h>
    <p>blaa, blah</p>
    <p>blaa, blaa, blah</p>

    <form action="/ex{num}/submit">
    <input type="hidden" name="{editor_content_name}" />
    <input type="submit" value="Esita aktiivse redaktori sisu" />
    </form>

    """.format(
            num=num, editor_content_name=EDITOR_CONTENT_NAME
        )

    def _get_submit_text(self, form_data):
        print("FD", form_data)
        source = form_data.get(EDITOR_CONTENT_NAME)

        return """
        <h1>Esitus</h1>
        <code>
{source}
        </code>
        <h2>Tulemus</h2>
        Priima töö!
        
        <h2>Eelmised esitused</h2>
        <ul>
            <li>2020-09-01 12:12:12</li>
        </ul>
        """.format(
            source=source
        )

    def get_image(self, url):
        from urllib.request import urlopen
        with urlopen(url) as fp:
            return fp.read()

    def get_menu_items(self) -> List[Tuple[str, Union[str, Callable, None]]]:
        return [
            ("Logout", "/logout"),
            ("-", None), # Separator
            ("UI command", self.show_dlg)
        ]

    def show_dlg(self):
        messagebox.showinfo("Yeehaa", "Hi!", parent=get_workbench())
