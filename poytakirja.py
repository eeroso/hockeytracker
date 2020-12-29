
from kivy.app import App
#kivy.require("1.10.1")
import sqlite3
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, WipeTransition
import requests
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.textinput import TextInput
from kivy.properties import BooleanProperty, ListProperty, ObjectProperty, StringProperty, NumericProperty
from kivy.uix.recyclegridlayout import RecycleGridLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.core.image import Image
from kivy.graphics import BorderImage
from kivy.graphics import Color, Rectangle
from kivy.uix.image import AsyncImage
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.scatter import Scatter
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.window import Window

Window.fullscreen = True
Config.set('graphics', 'resizable', True)
Config.write()


class ValikkoScreen(Screen):
    def clear_variables(self):
        App.get_running_app().btn_mode = True
        App.get_running_app().maalit_koti = "0"
        App.get_running_app().maalit_vieras = "0"
        App.get_running_app().koti_porukka = ""
        App.get_running_app().koti_voitolla = False
        App.get_running_app().vieras_voitolla = False
        tasapeli_menos = BooleanProperty(False)
        onko_vv_kaytos = BooleanProperty(False)
        onko_kv_kaytos = BooleanProperty(False)


    def create_table(self):
        connection = sqlite3.connect("poytakirja.db")
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        queries = [""" CREATE TABLE IF NOT EXISTS joukkueet (joukkue_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, nimi TEXT NOT NULL, ottelut INTEGER NOT NULL DEFAULT 0, voitut INTEGER NOT NULL DEFAULT 0, ja_voitot INTEGER NOT NULL DEFAULT 0, ja_haviot INTEGER NOT NULL DEFAULT 0, haviot INTEGER NOT NULL DEFAULT 0, tasapelit INTEGER NOT NULL DEFAULT 0, t_maalit INTEGER NOT NULL DEFAULT 0, p_maalit INTEGER NOT NULL DEFAULT 0, maaliero INTEGER NOT NULL DEFAULT 0, pisteet INTEGER NOT NULL DEFAULT 0);""", """ CREATE TABLE IF NOT EXISTS pelaajat (joukkue_id INT, nimi TEXT, pelinumero INTEGER, maalit INTEGER DEFAULT 0, syotot INTEGER DEFAULT 0, pisteet INTEGER DEFAULT 0, active INTEGER DEFAULT 1, FOREIGN KEY (joukkue_id) REFERENCES joukkueet(joukkue_id) ON DELETE CASCADE);""" ]
        for query in queries:
            cursor.execute(query)

        connection.close()

class AsetusScreen(Screen):
    def vaihda_kieli(self): 
        if App.get_running_app().kielisettings == True:
            App.get_running_app().kielisettings = False
        else:
            App.get_running_app().kielisettings = True

    def nollaa_tilastot(self):
        connection = sqlite3.connect("poytakirja.db")
        cursor = connection.cursor()
        cursor.execute("UPDATE joukkueet SET ottelut = 0, voitut = 0, ja_voitot = 0, ja_haviot = 0, haviot = 0, tasapelit = 0, t_maalit = 0, p_maalit = 0, maaliero = 0, pisteet = 0")
        cursor.execute("UPDATE pelaajat SET maalit = 0, syotot = 0, pisteet = 0, active = 1")
        connection.commit()
        connection.close()

class KaikkipelaajatScreen(Screen): 
    global selectedPlayer
    global playerDetails
    global posse_atm
    data_items_act = ListProperty([])
    data_items_inact = ListProperty([])
    data_items = ListProperty([])
    selected = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        super(KaikkipelaajatScreen, self).__init__(**kwargs)
        self.get_table_column_headings()
        self.get_teams()

 
    def get_table_column_headings(self):
        connection = sqlite3.connect("poytakirja.db")
        with connection:
            cursor = connection.cursor()
            cursor.execute("PRAGMA table_info(pelaajat)")
            col_headings = cursor.fetchall()
            self.total_col_headings = len(col_headings)

    def get_teams(self):
        connection = sqlite3.connect("poytakirja.db")
        cursor = connection.cursor()

        cursor.execute("SELECT nimi FROM joukkueet")
        rows = cursor.fetchall()

        # create list with db column, db primary key, and db column range
        data = []
        low = 0
        high = self.total_col_headings - 1
        # Using database column range for populating the TextInput widgets with values from the row clicked/pressed.
        self.data_items = []
        for row in rows:
            for col in row:
                data.append([col, row[0], [low, high]])
            low += self.total_col_headings
            high += self.total_col_headings


        # create data_items
        self.data_items = [{'text': str(x[0]), 'Index': str(x[1]), 'range': x[2]} for x in data]
    
    def populate_fields(self, instance): # NEW
        columns = self.data_items[instance.index]['range']
        self.player_name_text_input.text = self.data_items[columns[0]]['text']
        self.player_no_text_input.text = self.data_items[columns[1]]['text']

    def set_valittu(self, tieto):
        global selectedPlayer
        global playerDetails
        if tieto == "":
            selectedPlayer = ""
            playerDetails = ""
        else:
            selectedPlayer = tieto.get("text")
            playerDetails = selectedPlayer.split("     ")
            print(playerDetails)

    def get_active_players(self, tieto):
        connection = sqlite3.connect("poytakirja.db")
        cursor = connection.cursor()
        cursor.execute("SELECT joukkue_id FROM joukkueet WHERE nimi = (?)", (tieto,))
        joukkue_id = cursor.fetchone()[0]

        cursor.execute("SELECT nimi, pelinumero FROM pelaajat WHERE active = 1 AND joukkue_id =(?) ORDER BY pelinumero ASC", (joukkue_id,))
        rows = cursor.fetchall()

        # create list with db column, db primary key, and db column range
        data = []
        low = 0
        high = self.total_col_headings - 1
        # Using database column range for populating the TextInput widgets with values from the row clicked/pressed.
        self.data_items_act = []

        # create data_items
        self.data_items_act = [{'text': str(x[0]) +"     "+ str(x[1])} for x in rows]

    def klikattu_joukkue(self, tieto):
        global posse_atm
        posse_atm = tieto
        self.get_inactive_players(tieto)
        self.get_active_players(tieto)

    def get_inactive_players(self, tieto):
        connection = sqlite3.connect("poytakirja.db")
        cursor = connection.cursor()

        cursor.execute("SELECT joukkue_id FROM joukkueet WHERE nimi = (?)", (tieto,))
        joukkue_id = cursor.fetchone()[0]

        cursor.execute("SELECT nimi, pelinumero FROM pelaajat WHERE active = 0 AND joukkue_id =(?) ORDER BY pelinumero ASC", (joukkue_id,))
        rows = cursor.fetchall()
        # create list with db column, db primary key, and db column range
        data = []
        low = 0
        high = self.total_col_headings - 1
        # Using database column range for populating the TextInput widgets with values from the row clicked/pressed.
        self.data_items_inact = []
        # create data_items
        self.data_items_inact = [{'text': str(x[0]) +"     "+ str(x[1])} for x in rows]

    def delete_chosen(self, huutialolhaha):
        connection = sqlite3.connect("poytakirja.db")
        global playerDetails
        global posse_atm

        try:
            cursor = connection.cursor()
            sql_remove_query = "DELETE FROM pelaajat WHERE nimi=(?) AND pelinumero=(?)"
            cursor.execute(sql_remove_query, (playerDetails[0], playerDetails[1]))
            connection.commit()
            connection.close()
        except sqlite3.IntegrityError as e:
                print("Error: ", e)

        self.get_active_players(posse_atm)
        self.get_inactive_players(posse_atm)

    def toggle_active(self, huuuutistbrah):
        global posse_atm
        connection = sqlite3.connect("poytakirja.db")
        global playerDetails
        cursor = connection.cursor()
        if not playerDetails:
            pass
        else:
            cursor.execute("SELECT active FROM pelaajat WHERE nimi=(?) AND pelinumero =(?)", (playerDetails[0], playerDetails[1]))
            ukkeli = cursor.fetchone()[0]
            print(ukkeli)
            if int(ukkeli) == 1:
                ukkeli = 0
            elif int(ukkeli) == 0:
                ukkeli = 1

        
            sql_update_query = "UPDATE pelaajat SET active = (?) WHERE nimi=(?) AND pelinumero=(?)"
            cursor.execute(sql_update_query, (ukkeli, playerDetails[0], playerDetails[1]))
                
            connection.commit()
            connection.close()
            self.get_active_players(posse_atm)
            self.get_inactive_players(posse_atm)


class JoukkueScreen(Screen):
    kotinippu = ''
    vierasnippu = ''
    joukkiot = ListProperty([])
    def get_teams(self):
        joukkiot=[]
        connection = sqlite3.connect("poytakirja.db")
        cursor = connection.cursor()

        cursor.execute("SELECT nimi FROM joukkueet")
        rows = cursor.fetchall()
        self.joukkiot = [str(t[0]) for t in rows]
        connection.close()

    def lambda_l(self):
        pass

    def animate_it_home(self, widget):
        anim = Animation(background_color=(0,0,1,1), duration=0.6)
        anim.start(widget)
   
    def animate_it_away(self, widget):
        anim = Animation(background_color=(1,0,0,1), duration=0.6)
        anim.start(widget)

    def get_home(self):
        self.kotinippu = self.ids.koti.text
         #pitää todennäköisesti vaihtaa globaliksi

    def get_away(self):
        self.vierasnippu = self.ids.vieras.text
        

    

class UusiJoukkueScreen(Screen):
    data_items = ListProperty([])
    delBtn = BooleanProperty(True)
    global valittuPosse

    def __init__(self, **kwargs):
        super(UusiJoukkueScreen, self).__init__(**kwargs)
        self.get_table_column_headings()
        self.get_teams()
        
    

    def get_table_column_headings(self):
        connection = sqlite3.connect("poytakirja.db")
        with connection:
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("PRAGMA table_info(joukkueet)")
            col_headings = cursor.fetchall()
            self.total_col_headings = len(col_headings)

    def populate_fields(self, instance): # NEW
        columns = self.data_items[instance.index]['range']
        self.team_name_text_input.text = self.data_items[columns[0]]['text']

    def save_refresh(self):
        self.save()
        self.get_teams()

    def set_valittu(self, tieto):
        global valittuPosse
        valittuPosse = tieto.get("text")
    
    def delete_chosen(self):
        connection = sqlite3.connect("poytakirja.db")
        global valittuPosse
        print(valittuPosse)

        try:
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            sql_remove_query = "DELETE FROM joukkueet WHERE nimi=?"
            cursor.execute(sql_remove_query, (valittuPosse,))
            connection.commit()
            connection.close()
        except sqlite3.IntegrityError as e:
                print("Error: ", e)


        App.get_running_app().btn_mode = True
        self.get_teams()


    def save(self):
        dupeList = []
        connection = sqlite3.connect("poytakirja.db")
        cursor = connection.cursor()
        j_nimi = self.team_name_text_input.text
        for x in self.data_items:
            dupeList.append(x.get("text"))

        if(j_nimi == ''): #jos tyhjä
            self.TyhjaPopup() 
        elif(j_nimi in dupeList): #jos duplikaatti
            self.DuplikaattiPopup()
        else:
            try:
                save_sql = "INSERT INTO joukkueet (nimi) VALUES (?)"
                connection.execute(save_sql, (j_nimi,))
                connection.commit()
                connection.close()
            except sqlite3.IntegrityError as e:
                print("Error: ", e)

    
    def save_player(self):
        connection = sqlite3.connect("poytakirja.db")
        cursor = connection.cursor()

        joukkue_id = self.team_name_text_input.text
        nimi = self.player_name_text_input.text
        pelinumero = self.player_no_text_input.text
        maalit = 0
        syotot = 0
        pisteet = 0

        try:
            save_player = "INSERT INTO pelaajat (joukkue_id, nimi, pelinumero,maalit,syotot,pisteet) VALUES (?,?,?,?,?,?)"
            connection.execute(save_player, (joukkue_id, nimi, pelinumero, maalit, syotot, pisteet))
            connection.commit()
            connection.close()
        except sqlite3.IntegrityError as e:
            print("Error: ", e)

    

    def get_teams(self):
        connection = sqlite3.connect("poytakirja.db")
        cursor = connection.cursor()

        cursor.execute("SELECT nimi FROM joukkueet")
        rows = cursor.fetchall()

        # create list with db column, db primary key, and db column range
        data = []
        low = 0
        high = self.total_col_headings - 1
        # Using database column range for populating the TextInput widgets with values from the row clicked/pressed.
        self.data_items = []
        for row in rows:
            for col in row:
                data.append([col, row[0], [low, high]])
            low += self.total_col_headings
            high += self.total_col_headings


        # create data_items
        self.data_items = [{'text': str(x[0]), 'Index': str(x[1]), 'range': x[2]} for x in data]

    
    def TyhjaPopup(self):
        ahh = self.ids.j_nimi
        anim = Animation(background_color=(1,0,0,0.7), duration=0.6) + Animation(background_color=(1,1,1,1), duration=0.7)
        anim.start(ahh)

        pop = MyPopup2()
        pop.open()
    
    def DuplikaattiPopup(self):
        ahh = self.ids.j_nimi
        anim = Animation(background_color=(1,0,0,0.7), duration=0.6) + Animation(background_color=(1,1,1,1), duration=0.7)
        anim.start(ahh)
        pop = MyPopup3()
        pop.open()

class TilastoScreen(Screen):
    data_items = ListProperty([])
    
    def __init__(self, **kwargs):
        super(TilastoScreen, self).__init__(**kwargs)
        self.get_table_column_headings()
        self.get_teams()
    
    def get_table_column_headings(self):
        connection = sqlite3.connect("poytakirja.db")
        with connection:
            cursor = connection.cursor()
            cursor.execute("PRAGMA table_info(joukkueet)")
            col_headings = cursor.fetchall()
            self.total_col_headings = len(col_headings)


    
    def populate_fields(self, instance): # NEW
        columns = self.data_items[instance.index]['range']
        self.player_name_text_input.text = self.data_items[columns[0]]['text']
        self.player_no_text_input.text = self.data_items[columns[1]]['text']
        self.player_goal_text_input.text = self.data_items[columns[2]]['text']


    def get_teams(self):
        connection = sqlite3.connect("poytakirja.db")
        cursor = connection.cursor()

        cursor.execute("SELECT nimi, ottelut, voitut,tasapelit,ja_voitot,ja_haviot,haviot,t_maalit,p_maalit,maaliero,pisteet FROM joukkueet ORDER BY pisteet Desc")
        rows = cursor.fetchall()

        # create list with db column, db primary key, and db column range
        data = []
        low = 0
        high = self.total_col_headings - 1
        # Using database column range for populating the TextInput widgets with values from the row clicked/pressed.
        self.data_items = []
        for row in rows:
            for col in row:
                data.append([col, row[0], [low, high]])
            low += self.total_col_headings
            high += self.total_col_headings


        # create data_items
        self.data_items = [{'text': str(x[0]), 'Index': str(x[1]), 'range': x[2]} for x in data]

class PisteporssiScreen(Screen):
    
    
    data_items = ListProperty([])
    goalscounter=0
    assistcounter=0
    pointscounter=0

    jarjestys_text = StringProperty()
    jarjestys_text_english = StringProperty()

    def __init__(self, **kwargs):
        super(PisteporssiScreen, self).__init__(**kwargs)
        self.get_table_column_headings()
        self.get_players()
        self.jarjestys_text = str("Järjestetty: Pisteet laskevasti")
        self.jarjestys_text_english = str("Sorted: Points decreasing")

    def maalit_nouseva(self):
        self.jarjestys_text = str("Järjestetty: Maalit nousevasti")
        self.jarjestys_text_english = str("Sorted: Goals ascending")
    def maalit_laskeva(self):
        self.jarjestys_text = str("Järjestetty: Maalit laskevasti")
        self.jarjestys_text_english = str("Sorted: Goals decreasing")
    def syotot_nouseva(self):
        self.jarjestys_text = str("Järjestetty: Syötöt nousevasti")
        self.jarjestys_text_english = str("Sorted: Passes ascending")
    def syotot_laskeva(self):
        self.jarjestys_text = str("Järjestetty: Syötöt laskevasti")
        self.jarjestys_text_english = str("Sorted: Passes decreasing")
    def pisteet_nouseva(self):
        self.jarjestys_text = str("Järjestetty: Pisteet nousevasti")
        self.jarjestys_text_english = str("Sorted: Points ascending")
    def pisteet_laskeva(self):
        self.jarjestys_text = str("Järjestetty: Pisteet laskevasti")
        self.jarjestys_text_english = str("Sorted: Points decreasing")
    
    def get_table_column_headings(self):
        connection = sqlite3.connect("poytakirja.db")
        with connection:
            cursor = connection.cursor()
            cursor.execute("PRAGMA table_info(pelaajat)")
            col_headings = cursor.fetchall()
            self.total_col_headings = len(col_headings)


    
    def populate_fields(self, instance): # NEW
        columns = self.data_items[instance.index]['range']
        self.player_name_text_input.text = self.data_items[columns[0]]['text']
        self.player_no_text_input.text = self.data_items[columns[1]]['text']
        self.player_goal_text_input.text = self.data_items[columns[2]]['text']


    def get_players(self):
        connection = sqlite3.connect("poytakirja.db")
        cursor = connection.cursor()

        cursor.execute("SELECT nimi, pelinumero, maalit, syotot, pisteet FROM pelaajat ORDER BY pisteet DESC")
        rows = cursor.fetchall()

        # create list with db column, db primary key, and db column range
        data = []
        low = 0
        high = self.total_col_headings - 1
        # Using database column range for populating the TextInput widgets with values from the row clicked/pressed.
        self.data_items = []
        for row in rows:
            for col in row:
                data.append([col, row[0], [low, high]])
            low += self.total_col_headings
            high += self.total_col_headings


        # create data_items
        self.data_items = [{'text': str(x[0]), 'Index': str(x[1]), 'range': x[2]} for x in data]

    def sort_goals(self):
        connection = sqlite3.connect("poytakirja.db")
        cursor = connection.cursor()
        
        
        if(self.goalscounter%2==0):
            cursor.execute("SELECT nimi, pelinumero, maalit,syotot,pisteet FROM pelaajat ORDER BY maalit ASC")
            self.goalscounter = self.goalscounter+1
            self.maalit_nouseva()
        else:
            cursor.execute("SELECT nimi, pelinumero, maalit,syotot,pisteet FROM pelaajat ORDER BY maalit DESC")
            self.goalscounter = self.goalscounter+1
            self.maalit_laskeva()
        rows = cursor.fetchall()
        data = []
        low = 0
        high = self.total_col_headings - 1
        self.data_items = []
        for row in rows:
            for col in row:
                data.append([col, row[0], [low, high]])
            low += self.total_col_headings
            high += self.total_col_headings

        self.data_items = [{'text': str(x[0]), 'Index': str(x[1]), 'range': x[2]} for x in data]


    def sort_assists(self):
        connection = sqlite3.connect("poytakirja.db")
        cursor = connection.cursor()
        
        if(self.assistcounter%2==0):
            cursor.execute("SELECT nimi, pelinumero, maalit,syotot,pisteet FROM pelaajat ORDER BY syotot ASC")
            self.assistcounter = self.assistcounter+1
            self.syotot_nouseva()
        else:
            cursor.execute("SELECT nimi, pelinumero, maalit,syotot,pisteet FROM pelaajat ORDER BY syotot DESC")
            self.assistcounter = self.assistcounter+1
            self.syotot_laskeva()
        rows = cursor.fetchall()
        data = []
        low = 0
        high = self.total_col_headings - 1
        self.data_items = []
        for row in rows:
            for col in row:
                data.append([col, row[0], [low, high]])
            low += self.total_col_headings
            high += self.total_col_headings

        self.data_items = [{'text': str(x[0]), 'Index': str(x[1]), 'range': x[2]} for x in data]


    def sort_points(self):
        connection = sqlite3.connect("poytakirja.db")
        cursor = connection.cursor()
        
        
        if(self.pointscounter%2==0):
            cursor.execute("SELECT nimi, pelinumero, maalit,syotot,pisteet FROM pelaajat ORDER BY pisteet ASC")
            self.pointscounter = self.pointscounter+1
            self.pisteet_nouseva()
        else:
            cursor.execute("SELECT nimi, pelinumero, maalit,syotot,pisteet FROM pelaajat ORDER BY pisteet DESC")
            self.pointscounter = self.pointscounter+1
            self.pisteet_laskeva()
        rows = cursor.fetchall()
        data = []
        low = 0
        high = self.total_col_headings - 1
        self.data_items = []
        for row in rows:
            for col in row:
                data.append([col, row[0], [low, high]])
            low += self.total_col_headings
            high += self.total_col_headings

        self.data_items = [{'text': str(x[0]), 'Index': str(x[1]), 'range': x[2]} for x in data]

class MyPopup(Popup):
    pass

class MyPopup2(Popup):
    pass

class MyPopup3(Popup):
    pass
class MyPopup4(Popup):
    pass
class MyPopup5(Popup):
    pass
class MyPopup6(Popup):
    pass
class MyPopup7(Popup):
    pass

class MyPopup15(Popup):
    pass

class PoytakirjaScreen(Screen):

    data_pelaajat_koti = ListProperty([])
    data_pelaajat_vieras = ListProperty([])

    jokupaska = BooleanProperty(True)
    
    paketti= []
    paketti2= []
    kotinippu1= ''
    vierasnippu1 = ''

    def __init__(self, **kwargs):
        super(PoytakirjaScreen, self).__init__(**kwargs)
        self.get_table_column_headings()
        
    def get_jengit(self):
        self.kotinippu1 = self.manager.get_screen('joukkuescreen').kotinippu
        self.vierasnippu1 = self.manager.get_screen('joukkuescreen').vierasnippu
        print(self.kotinippu1)
        print(self.vierasnippu1)

        if(self.kotinippu1 == self.vierasnippu1 or self.kotinippu1 == '' or self.vierasnippu1 == ''):
            self.show_popup()

    def poistaTiedot(self):
        for child in self.ids.ylaInputit.children:
            if isinstance(child, TextInput):
                child.text = ""

        for child in self.ids.kotiInputit.children:
            if isinstance(child, TextInput):
                child.text = ""

        for child in self.ids.vierasInputit.children:
            if isinstance(child, TextInput):
                child.text = ""

        

    

    def show_popup(self):
        popuppi = MyPopup()
        popuppi.open()
    
    def nimea_jengit(self, kotijengi, vierasjengi):
        self.ids.kotilabel.text = (kotijengi)
        self.ids.vieraslabel.text = vierasjengi

    def ota_ss(self):
        self.ids.valikkobtn.visible = False
        self.ids.ssbtn.visible = False
        self.ids.takasin.visible = False
        self.jokupaska = False
        Clock.schedule_once(lambda dt: self.palauta_widgetit(), 0.5)

    def palauta_widgetit(self):
        Window.screenshot(name='screenshot{:04d}.png')
        Clock.schedule_once(lambda dt: self.ajastettu_toiminta(), 0.5)
        
    
    def ajastettu_toiminta(self):
        self.ids.valikkobtn.visible = True
        self.ids.ssbtn.visible = True
        self.ids.takasin.visible = True
        self.jokupaska = True

    
    
    def maalit_koti(self, maali1, maali2, maali3, maali4, maali5, maali6, maali7, maali8, maali9):
        kusi = []
        if maali1 == '':
            maali1 = 0
        if maali2 == '':
            maali2 = 0
        if maali3 == '':
            maali3 = 0
        if maali4 == '':
            maali4 = 0
        if maali5 == '':
            maali5 = 0
        if maali6 == '':
            maali6 = 0
        if maali7 == '':
            maali7 = 0
        if maali8 == '':
            maali8 = 0
        if maali9 == '':
            maali9 = 0
        kusi.append(int(maali1))
        kusi.append(int(maali2))
        kusi.append(int(maali3))
        kusi.append(int(maali4))
        kusi.append(int(maali5))
        kusi.append(int(maali6))
        kusi.append(int(maali7))
        kusi.append(int(maali8))
        kusi.append(int(maali9))
        print(str(max(kusi)))
        App.get_running_app().maalit_koti = str(max(kusi))

    def maalit_vieras(self, maali1, maali2, maali3, maali4, maali5, maali6, maali7, maali8, maali9):
        kusi = []
        if maali1 == '':
            maali1 = 0
        if maali2 == '':
            maali2 = 0
        if maali3 == '':
            maali3 = 0
        if maali4 == '':
            maali4 = 0
        if maali5 == '':
            maali5 = 0
        if maali6 == '':
            maali6 = 0
        if maali7 == '':
            maali7 = 0
        if maali8 == '':
            maali8 = 0
        if maali9 == '':
            maali9 = 0
        kusi.append(int(maali1))
        kusi.append(int(maali2))
        kusi.append(int(maali3))
        kusi.append(int(maali4))
        kusi.append(int(maali5))
        kusi.append(int(maali6))
        kusi.append(int(maali7))
        kusi.append(int(maali8))
        kusi.append(int(maali9))
        print(str(max(kusi)))
        App.get_running_app().maalit_vieras = str(max(kusi))


    def maalintekijat_koti(self, joukkue, maalimies1, maalimies2, maalimies3, maalimies4, maalimies5, maalimies6, maalimies7, maalimies8, maalimies9):
        connection = sqlite3.connect("poytakirja.db")
        cursor = connection.cursor()
        self.paketti = []
        maalimiehet = []
        maalimiehet.append(maalimies1)
        maalimiehet.append(maalimies2)
        maalimiehet.append(maalimies3)
        maalimiehet.append(maalimies4)
        maalimiehet.append(maalimies5)
        maalimiehet.append(maalimies6)
        maalimiehet.append(maalimies7)
        maalimiehet.append(maalimies8)
        maalimiehet.append(maalimies9)

        for i in range(9):
            if not maalimiehet[i] == '' and maalimiehet[i].isdigit:
                cursor.execute("SELECT joukkue_id FROM joukkueet WHERE nimi = (?)", (joukkue,))
                joukkue_id = cursor.fetchone()[0]
                cursor.execute("UPDATE pelaajat SET maalit = maalit + 1, pisteet = pisteet + 1 WHERE pelinumero = (?) and joukkue_id = (?)", (maalimiehet[i], joukkue_id))
                print("updatettu")
                self.paketti.append(maalimiehet[i])
                
        if self.paketti:
            PistetulosScreen.home_scores(PistetulosScreen, self.paketti, joukkue_id)
        else:
            PistetulosScreen.home_scores(PistetulosScreen, self.paketti, "")
        connection.commit()
        connection.close()

    def maalintekijat_vieras(self, joukkue, maalimies1, maalimies2, maalimies3, maalimies4, maalimies5, maalimies6, maalimies7, maalimies8, maalimies9):
        connection = sqlite3.connect("poytakirja.db")
        cursor = connection.cursor()
        self.paketti2 = []
        maalimiehet = []
        maalimiehet.append(maalimies1)
        maalimiehet.append(maalimies2)
        maalimiehet.append(maalimies3)
        maalimiehet.append(maalimies4)
        maalimiehet.append(maalimies5)
        maalimiehet.append(maalimies6)
        maalimiehet.append(maalimies7)
        maalimiehet.append(maalimies8)
        maalimiehet.append(maalimies9)

        for i in range(9):
            if not maalimiehet[i] == '' and maalimiehet[i].isdigit:
                cursor.execute("SELECT joukkue_id FROM joukkueet WHERE nimi = (?)", (joukkue,))
                joukkue_id = cursor.fetchone()[0]
                cursor.execute("UPDATE pelaajat SET maalit = maalit + 1, pisteet = pisteet + 1 WHERE pelinumero = (?) and joukkue_id = (?)", (maalimiehet[i], joukkue_id))
                print("updatettu")
                self.paketti2.append(maalimiehet[i])
                
        if self.paketti2:        
            PistetulosScreen.away_scores(PistetulosScreen, self.paketti2, joukkue_id)
        else:
            PistetulosScreen.away_scores(PistetulosScreen, self.paketti2, "")
        connection.commit()
        connection.close()



    def syottajat_vieras(self, joukkue, syottomies1, syottomies2, syottomies3, syottomies4, syottomies5, syottomies6, syottomies7, syottomies8, syottomies9, syottomies10, syottomies11, syottomies12, syottomies13, syottomies14, syottomies15, syottomies16, syottomies17, syottomies18):
        connection = sqlite3.connect("poytakirja.db")
        cursor = connection.cursor()
        syottomiehet = []
        syottomiehet.append(syottomies1)
        syottomiehet.append(syottomies2)
        syottomiehet.append(syottomies3)
        syottomiehet.append(syottomies4)
        syottomiehet.append(syottomies5)
        syottomiehet.append(syottomies6)
        syottomiehet.append(syottomies7)
        syottomiehet.append(syottomies8)
        syottomiehet.append(syottomies9)
        syottomiehet.append(syottomies10)
        syottomiehet.append(syottomies11)
        syottomiehet.append(syottomies12)
        syottomiehet.append(syottomies13)
        syottomiehet.append(syottomies14)
        syottomiehet.append(syottomies15)
        syottomiehet.append(syottomies16)
        syottomiehet.append(syottomies17)
        syottomiehet.append(syottomies18)

        for i in range(18):
            if not syottomiehet[i] == '' and syottomiehet[i].isdigit:
                cursor.execute("SELECT joukkue_id FROM joukkueet WHERE nimi = (?)", (joukkue,))
                joukkue_id = cursor.fetchone()[0]
                cursor.execute("UPDATE pelaajat SET syotot = syotot + 1, pisteet = pisteet + 1 WHERE pelinumero = (?) and joukkue_id = (?)", (syottomiehet[i], joukkue_id))

        connection.commit()
        connection.close()

    def syottajat_koti(self, joukkue, syottomies1, syottomies2, syottomies3, syottomies4, syottomies5, syottomies6, syottomies7, syottomies8, syottomies9, syottomies10, syottomies11, syottomies12, syottomies13, syottomies14, syottomies15, syottomies16, syottomies17, syottomies18):
        connection = sqlite3.connect("poytakirja.db")
        cursor = connection.cursor()
        syottomiehet = []
        syottomiehet.append(syottomies1)
        syottomiehet.append(syottomies2)
        syottomiehet.append(syottomies3)
        syottomiehet.append(syottomies4)
        syottomiehet.append(syottomies5)
        syottomiehet.append(syottomies6)
        syottomiehet.append(syottomies7)
        syottomiehet.append(syottomies8)
        syottomiehet.append(syottomies9)
        syottomiehet.append(syottomies10)
        syottomiehet.append(syottomies11)
        syottomiehet.append(syottomies12)
        syottomiehet.append(syottomies13)
        syottomiehet.append(syottomies14)
        syottomiehet.append(syottomies15)
        syottomiehet.append(syottomies16)
        syottomiehet.append(syottomies17)
        syottomiehet.append(syottomies18)

        for i in range(18):
            if not syottomiehet[i] == '' and syottomiehet[i].isdigit:
                cursor.execute("SELECT joukkue_id FROM joukkueet WHERE nimi = (?)", (joukkue,))
                joukkue_id = cursor.fetchone()[0]
                cursor.execute("UPDATE pelaajat SET syotot = syotot + 1, pisteet = pisteet + 1 WHERE pelinumero = (?) and joukkue_id = (?)", (syottomiehet[i], joukkue_id))

        connection.commit()
        connection.close()


    def get_table_column_headings(self):
        connection = sqlite3.connect("poytakirja.db")
        with connection:
            cursor = connection.cursor()
            cursor.execute("PRAGMA table_info(pelaajat)")
            col_headings = cursor.fetchall()
            self.total_col_headings = len(col_headings)

    
    def get_players_koti(self, joukkue_nimi):
        connection = sqlite3.connect("poytakirja.db")
        cursor = connection.cursor()


        if not joukkue_nimi == '': 
            cursor.execute("""SELECT joukkue_id from joukkueet WHERE nimi = ? """, (joukkue_nimi,))
            joukkue_id = cursor.fetchone()[0]
            print(joukkue_id)

            cursor.execute("""SELECT pelinumero, nimi FROM pelaajat WHERE joukkue_id = ? AND active = 1 ORDER BY pelinumero ASC""", (joukkue_id,))
            rows = cursor.fetchall()

            print("koti"+str(rows))
            data = []
            low = 0
            high = self.total_col_headings - 1
        # Using database column range for populating the TextInput widgets with values from the row clicked/pressed.
            self.data_pelaajat_koti = []
            for row in rows:
                for col in row:
                    data.append([col, row[0], [low, high]])
                low += self.total_col_headings
                high += self.total_col_headings
        # create data_items
            self.data_pelaajat_koti = [{'text': str(x[0]) +"   "+ str(x[1])} for x in rows]


    def get_players_vieras(self, joukkue_nimi):
        connection = sqlite3.connect("poytakirja.db")
        cursor = connection.cursor()


        if not joukkue_nimi == '': 
            cursor.execute("""SELECT joukkue_id from joukkueet WHERE nimi = ? """, (joukkue_nimi,))
            joukkue_id = cursor.fetchone()[0]
            print(joukkue_id)

            cursor.execute("""SELECT pelinumero, nimi FROM pelaajat WHERE joukkue_id = ? AND active = 1 ORDER BY pelinumero ASC""", (joukkue_id,))
            rows = cursor.fetchall()

            print("koti"+str(rows))
            data = []
            low = 0
            high = self.total_col_headings - 1
        # Using database column range for populating the TextInput widgets with values from the row clicked/pressed.
            self.data_pelaajat_vieras = []
            for row in rows:
                for col in row:
                    data.append([col, row[0], [low, high]])
                low += self.total_col_headings
                high += self.total_col_headings
        # create data_items
            self.data_pelaajat_vieras = [{'text': str(x[0]) +"   "+ str(x[1])} for x in rows]

    #def siirra_tietoa(self, inteksi):
        ##

class TextInputPopup(Popup):
    obj = ObjectProperty(None)
    obj_text = StringProperty("")

    def __init__(self, obj, **kwargs):
        super(TextInputPopup, self).__init__(**kwargs)
        self.obj = obj
        self.obj_text = obj.text

class ConfirmationPopup(Popup):
    pass


class PistetulosScreen(Screen):

    data_items_koti = ListProperty([])
    data_items_vieras = ListProperty([])
    kotinippu1= ''
    vierasnippu1 = ''
    kotivoitto = BooleanProperty(False)
    vierasvoitto = BooleanProperty(False)
    jatkoaika = BooleanProperty(False)
    data = []
    data1 = []
    def __init__(self, **kwargs):
        super(PistetulosScreen, self).__init__(**kwargs)
        self.get_table_column_headings()

    def get_jengit(self):
        self.kotinippu1 = self.manager.get_screen('joukkuescreen').kotinippu
        self.vierasnippu1 = self.manager.get_screen('joukkuescreen').vierasnippu
        App.get_running_app().koti_porukka = self.kotinippu1
        print(self.kotinippu1)
        print(self.vierasnippu1)

    def nimea_jengit(self, kotijengi, vierasjengi):
        self.ids.kotilabel.text = kotijengi
        self.ids.vieraslabel.text = vierasjengi

    def get_goals(self):
        if int(App.get_running_app().maalit_koti) > int(App.get_running_app().maalit_vieras):
            App.get_running_app().koti_voitolla = True
            App.get_running_app().onko_vv_kaytos = True
            App.get_running_app().onko_kv_kaytos = False
        elif int(App.get_running_app().maalit_koti) < int(App.get_running_app().maalit_vieras):
            App.get_running_app().vieras_voitolla = True
            App.get_running_app().onko_kv_kaytos = True
            App.get_running_app().onko_vv_kaytos = False
        else:
            App.get_running_app().tasapeli_menos = True
            App.get_running_app().onko_vv_kaytos = True
            App.get_running_app().onko_kv_kaytos = True


    def get_table_column_headings(self):
        connection = sqlite3.connect("poytakirja.db")
        with connection:
            cursor = connection.cursor()
            cursor.execute("PRAGMA table_info(pelaajat)")
            col_headings = cursor.fetchall()
            self.total_col_headings = len(col_headings)


    def get_players_koti(self):
        # create data_items
        if(len(self.data)==0):
            self.data_items_koti=[]
        self.data_items_koti = [{'text': str(x[0]) +"     "+ str(x[1]) +"     "+ str(x[2])} for x in self.data]

    def tallenna_tiedot(self, koti, vieras):
        connection = sqlite3.connect("poytakirja.db")
        cursor = connection.cursor()

        print(str(App.get_running_app().maalit_koti))
        print(str(App.get_running_app().maalit_vieras))
        print(koti)
        print(vieras)
        cursor.execute("UPDATE joukkueet SET ottelut = ottelut + 1 WHERE nimi = (?) or nimi = (?)", (koti, vieras))



        if self.kotivoitto == False and self.vierasvoitto == False and self.jatkoaika == False:
            print("virheellistä settii")
        elif self.kotivoitto == True and self.vierasvoitto == False and self.jatkoaika == False:
            #koti suoravoittosetit
            cursor.execute("UPDATE joukkueet SET voitut = voitut + 1, t_maalit = t_maalit + (?), p_maalit = p_maalit + (?), maaliero = maaliero + (?), pisteet = pisteet + 3 WHERE nimi = (?)", (App.get_running_app().maalit_koti, App.get_running_app().maalit_vieras, (int(App.get_running_app().maalit_koti) - int(App.get_running_app().maalit_vieras)), koti))
            cursor.execute("UPDATE joukkueet SET haviot = haviot + 1, t_maalit = t_maalit + (?), p_maalit = p_maalit + (?), maaliero = maaliero + (?) WHERE nimi = (?)", (App.get_running_app().maalit_vieras, App.get_running_app().maalit_koti, (int(App.get_running_app().maalit_vieras) - int(App.get_running_app().maalit_koti)), vieras))
            print("kotisuora")
        elif self.kotivoitto == True and self.vierasvoitto == False and self.jatkoaika == True:
            #koti JA-voitto setit
            print(App.get_running_app().maalit_koti)
            cursor.execute("UPDATE joukkueet SET ja_voitot = ja_voitot + 1, t_maalit = (?), p_maalit = (?), maaliero = (?), pisteet = pisteet + 2 WHERE nimi = (?)", (App.get_running_app().maalit_koti, App.get_running_app().maalit_vieras, (int(App.get_running_app().maalit_koti) - int(App.get_running_app().maalit_vieras)), koti))
            cursor.execute("UPDATE joukkueet SET ja_haviot = ja_haviot + 1, t_maalit = t_maalit + (?), p_maalit = p_maalit + (?), maaliero = maaliero + (?), pisteet = pisteet+1 WHERE nimi = (?)", (App.get_running_app().maalit_vieras, App.get_running_app().maalit_koti, (int(App.get_running_app().maalit_vieras) - int(App.get_running_app().maalit_koti)), vieras))
            print("koti ja")
        elif self.kotivoitto == False and self.vierasvoitto == True and self.jatkoaika == False:
            cursor.execute("UPDATE joukkueet SET voitut = voitut + 1, t_maalit = t_maalit + (?), p_maalit = p_maalit + (?), maaliero = maaliero + (?), pisteet = pisteet + 3 WHERE nimi = (?)", (App.get_running_app().maalit_vieras, App.get_running_app().maalit_koti, (int(App.get_running_app().maalit_vieras) - int(App.get_running_app().maalit_koti)), vieras))
            cursor.execute("UPDATE joukkueet SET haviot = haviot + 1, t_maalit = t_maalit + (?), p_maalit = p_maalit + (?), maaliero = maaliero + (?) WHERE nimi = (?)", (App.get_running_app().maalit_koti, App.get_running_app().maalit_vieras, (int(App.get_running_app().maalit_koti) - int(App.get_running_app().maalit_vieras)), koti))
            print("vieras suora")
        elif self.kotivoitto == False and self.vierasvoitto == True and self.jatkoaika == True:
            #vieras JA-settings
            cursor.execute("UPDATE joukkueet SET ja_voitot = ja_voitot + 1, t_maalit = (?), p_maalit = (?), maaliero = (?), pisteet = pisteet + 2 WHERE nimi = (?)", (App.get_running_app().maalit_vieras, App.get_running_app().maalit_koti, (int(App.get_running_app().maalit_vieras) - int(App.get_running_app().maalit_koti)), vieras))
            cursor.execute("UPDATE joukkueet SET ja_haviot = ja_haviot + 1, t_maalit = t_maalit + (?), p_maalit = p_maalit + (?), maaliero = maaliero + (?), pisteet = pisteet+1 WHERE nimi = (?)", (App.get_running_app().maalit_koti, App.get_running_app().maalit_vieras, (int(App.get_running_app().maalit_koti) - int(App.get_running_app().maalit_vieras)), koti))
            print("vieras ja")
        elif self.kotivoitto == False and self.vierasvoitto == False and self.jatkoaika == True:
            print("testings :D")
            cursor.execute("UPDATE joukkueet SET tasapelit = tasapelit + 1, pisteet = pisteet + 1 WHERE nimi = (?) or nimi = (?)", (koti, vieras))
        connection.commit()
        connection.close()
    

    def home_scores(self, maalaajat, joukkue_id):
        if maalaajat:
            connection = sqlite3.connect("poytakirja.db")
            cursor = connection.cursor()
            self.data = []
            tekijat_ja_maarat = {}
            for i in maalaajat: 
                if str(i) in tekijat_ja_maarat:
                    tekijat_ja_maarat[str(i)] += 1
                else:
                    tekijat_ja_maarat[str(i)] = 1
            
            
            for key in tekijat_ja_maarat:
                cursor.execute("SELECT nimi FROM pelaajat WHERE pelinumero = (?) AND joukkue_id = (?)", (key, joukkue_id))
                self.data.append([cursor.fetchone()[0], key, "Maaleja: "+ str(tekijat_ja_maarat[key])])
            
            connection.close()
        else:
            self.data=[]

    def away_scores(self, maalaajat, joukkue_id):
        if maalaajat:
            connection = sqlite3.connect("poytakirja.db")
            cursor = connection.cursor()
            self.data1 = []
            tekijat_ja_maarat = {}
            for i in maalaajat: 
                if str(i) in tekijat_ja_maarat:
                    tekijat_ja_maarat[str(i)] += 1
                else:
                    tekijat_ja_maarat[str(i)] = 1
            
            
            for key in tekijat_ja_maarat:
                cursor.execute("SELECT nimi FROM pelaajat WHERE pelinumero = (?) AND joukkue_id = (?)", (key, joukkue_id))
                self.data1.append([cursor.fetchone()[0], key, "Maaleja: "+ str(tekijat_ja_maarat[key])])
            
            connection.close()
        else:
            self.data1=[]


    def get_players_vieras(self):
        self.data_items_vieras = [{'text': str(x[0]) +"     "+ str(x[1]) +"     "+ str(x[2])} for x in self.data1]

    def on_press_popup(self):
        popup = ConfirmationPopup()
        popup.open()
    


class UusiPelaajaScreen(Screen):
    data_items = ListProperty([])
    
    global valittuPelaaja

    def __init__(self, **kwargs):
        super(UusiPelaajaScreen, self).__init__(**kwargs)
        self.get_table_column_headings()
        self.get_teams()
    
    def get_table_column_headings(self):
        connection = sqlite3.connect("poytakirja.db")
        with connection:
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("PRAGMA table_info(joukkueet)")
            col_headings = cursor.fetchall()
            self.total_col_headings = len(col_headings)


    
    def populate_fields(self, instance): # NEW
        columns = self.data_items[instance.index]['range']

    def set_valittu(self, tieto):
        global valittuPelaaja
        valittuPelaaja = tieto
        print(valittuPelaaja)
        self.ids.j_nimi.text = valittuPelaaja


    def get_teams(self):
        connection = sqlite3.connect("poytakirja.db")
        cursor = connection.cursor()

        cursor.execute("SELECT nimi FROM joukkueet")
        rows = cursor.fetchall()

        # create list with db column, db primary key, and db column range
        data = []
        low = 0
        high = self.total_col_headings - 1
        # Using database column range for populating the TextInput widgets with values from the row clicked/pressed.
        self.data_items = []
        for row in rows:
            for col in row:
                data.append([col, row[0], [low, high]])
            low += self.total_col_headings
            high += self.total_col_headings


        # create data_items
        self.data_items = [{'text': str(x[0]), 'Index': str(x[1]), 'range': x[2]} for x in data]

    def tyhjennasetit(self):
        self.ids.playername.text =""
        self.ids.playerno.text=""

    
    def save_player(self):
        connection = sqlite3.connect("poytakirja.db")
        cursor = connection.cursor()


        joukkuenimi = self.team_name_text_input.text
        cursor.execute('''SELECT joukkue_id FROM joukkueet WHERE nimi IN (?)''', (joukkuenimi,))
        joukkue_id = int(cursor.fetchone()[0])


        nimi = self.player_name_text_input.text
        pelinumero = self.player_no_text_input.text
        maalit = 0
        syotot = 0
        pisteet = 0


        cursor.execute("SELECT * FROM pelaajat WHERE joukkue_id IN (?) AND pelinumero IN (?) AND nimi IN (?)", (joukkue_id, pelinumero, nimi))
        rowsAll = cursor.fetchall()
        print(rowsAll)

        cursor.execute("SELECT * FROM pelaajat WHERE joukkue_id IN (?) AND pelinumero IN (?)", (joukkue_id, pelinumero))
        rowsNbr = cursor.fetchall()
        print(rowsNbr)

        
        #Jos jaksaa niin joku vois siistiä tämän, näyttää iha yrjikseltä tää (mut toimii kyllä)
        if not pelinumero.isdigit() and not nimi or not nimi and int(pelinumero) > 99 or not nimi and int(pelinumero) < 0 or not nimi and len(rowsNbr) > 0:
            self.molemmatPopup()
        elif pelinumero.isdigit() and len(rowsAll)==0 and int(pelinumero) < 100 and int(pelinumero) > -1 and nimi and len(rowsNbr)==0:
            try:
                save_player = "INSERT INTO pelaajat (joukkue_id, nimi, pelinumero,maalit,syotot,pisteet) VALUES (?,?,?,?,?,?)"
                connection.execute(save_player, (joukkue_id, nimi, pelinumero, maalit, syotot, pisteet))
                connection.commit()
                connection.close()
            except sqlite3.IntegrityError as e:
                print("Error: ", e) 
            self.TallennettuPopup()
            self.player_name_text_input.text = "" 
            self.player_no_text_input.text = "" 
        elif not pelinumero.isdigit():
            self.PelinroPopup()
        elif len(rowsAll) > 0:
            self.duplicatePopup()
        elif int(pelinumero) < 0:
            self.PelinroPopup()
        elif int(pelinumero) > 99:
            self.PelinroPopup()
        elif len(rowsNbr) > 0:
            self.duplicateNbrPopup()
        else:
            self.TyhjaPopup()
        

    def TyhjaPopup(self):
        ahh = self.ids.playername
        anim = Animation(background_color=(1,0,0,0.7), duration=0.6) + Animation(background_color=(1,1,1,1), duration=0.7)
        anim.start(ahh)

        pop = MyPopup4()
        pop.open()

    def PelinroPopup(self):
        ahh = self.ids.playerno
        anim = Animation(background_color=(1,0,0,0.7), duration=0.6) + Animation(background_color=(1,1,1,1), duration=0.7)
        anim.start(ahh)

        pop = MyPopup5()
        pop.open()

    def molemmatPopup(self):
        ahh = self.ids.playerno
        ahh1 = self.ids.playername
        anim = Animation(background_color=(1,0,0,0.7), duration=0.6) + Animation(background_color=(1,1,1,1), duration=0.7)
        anim1 = Animation(background_color=(1,0,0,0.7), duration=0.6) + Animation(background_color=(1,1,1,1), duration=0.7)
        anim.start(ahh)
        anim1.start(ahh1)
        pop = MyPopup6()
        pop.open()

    def duplicatePopup(self):
        ahh = self.ids.playerno
        ahh1 = self.ids.playername
        anim = Animation(background_color=(1,0,0,0.7), duration=0.6) + Animation(background_color=(1,1,1,1), duration=0.7)
        anim1 = Animation(background_color=(1,0,0,0.7), duration=0.6) + Animation(background_color=(1,1,1,1), duration=0.7)
        anim.start(ahh)
        anim1.start(ahh1)
        pop = MyPopup7()
        pop.open()
    
    def TallennettuPopup(self):
        ahh = self.ids.playerno
        ahh1 = self.ids.playername
        anim = Animation(background_color=(0,0,0,0.7), duration=0.6) + Animation(background_color=(1,1,1,1), duration=0.7)
        anim1 = Animation(background_color=(0,0,0,0.7), duration=0.6) + Animation(background_color=(1,1,1,1), duration=0.7)
        anim.start(ahh)
        anim1.start(ahh1)
        pop = MyPopup15()
        pop.open()

    def duplicateNbrPopup(self):
        ahh = self.ids.playerno
        anim = Animation(background_color=(1,0,0,0.7), duration=0.6) + Animation(background_color=(1,1,1,1), duration=0.7)
        anim.start(ahh)
        pop = MyPopup7()
        pop.open()

class SelectableRecycleGridLayout(FocusBehavior, LayoutSelectionBehavior,
                                  RecycleGridLayout):
    ''' Adds selection and focus behaviour to the view. '''
    touch_deselect_last = BooleanProperty(True) 

class CustomButton(Button):
    ''' testicustombutton '''

class SelectableButton(RecycleDataViewBehavior, Button):
    ''' Add selection support to the Button '''

    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        return super(SelectableButton, self).refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(SelectableButton, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected
            


class SelectableLabel(RecycleDataViewBehavior, Label):
    ''' Add selection support to the Button '''

    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)



    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index

        return super(SelectableLabel, self).refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(SelectableLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected
        if is_selected:
            UusiJoukkueScreen.set_valittu(self, rv.data[index])
            App.get_running_app().btn_mode = False
        else:
            App.get_running_app.btn_mode = True

class SelectableLabel1(RecycleDataViewBehavior, Label):
    ''' Add selection support to the Button '''

    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)



    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index

        return super(SelectableLabel1, self).refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(SelectableLabel1, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected
        if is_selected:
            KaikkipelaajatScreen.set_valittu(self, rv.data[index])
        else:
            KaikkipelaajatScreen.set_valittu(self, "")



class SelectableButton1(RecycleDataViewBehavior, Button):
    ''' Add selection support to the Button '''
    global ptsPelimies
    global ptsPelimiesSplit

    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)



    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index

        return super(SelectableButton1, self).refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(SelectableButton1, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected
    
    def on_press(self):
        popup = TextInputPopup(self)
        popup.open()

    def update_changes(self, maalit, syotot, pelaaja):
        global ptsPelimies
        connection = sqlite3.connect("poytakirja.db")
        cursor = connection.cursor()
        if not maalit.isdigit() or maalit=='':
            maalit = 0
        if not syotot.isdigit() or syotot=='':
            syotot = 0
        ptsPelimies = pelaaja.split("     ")
        cursor.execute("SELECT joukkue_id FROM joukkueet WHERE nimi = (?)", (App.get_running_app().koti_porukka,))
        joukkue_id = cursor.fetchone()[0]

        cursor.execute("SELECT * FROM pelaajat WHERE joukkue_id = (?) AND nimi =(?) AND pelinumero = (?)", (joukkue_id, ptsPelimies[1], ptsPelimies[0]))
        onkoonkoonko = cursor.fetchall()

        if len(onkoonkoonko) == 1:   
            App.get_running_app().maalit_koti = str(int(App.get_running_app().maalit_koti) + int(maalit))
        elif len(onkoonkoonko) == 0:
            App.get_running_app().maalit_vieras = str(int(App.get_running_app().maalit_vieras) + int(maalit))

        if int(App.get_running_app().maalit_koti) > int(App.get_running_app().maalit_vieras):
            App.get_running_app().vieras_voitolla= False
            App.get_running_app().koti_voitolla= True
        elif int(App.get_running_app().maalit_koti) < int(App.get_running_app().maalit_vieras):
            App.get_running_app().koti_voitolla= False
            App.get_running_app().vieras_voitolla= True
        else:
            App.get_running_app().koti_voitolla= False
            App.get_running_app().vieras_voitolla= False
        
        
        pts = int(maalit)+int(syotot)
        
        cursor.execute("UPDATE pelaajat SET maalit = maalit + (?),  syotot = syotot + (?), pisteet = pisteet + (?) WHERE nimi = (?) AND pelinumero = (?)", (int(maalit), int(syotot), pts, ptsPelimies[1], ptsPelimies[0]))
        connection.commit()
        connection.close()


class SelectableButton2(RecycleDataViewBehavior, Button):
    ''' Add selection support to the Button '''
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)


    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index

        return super(SelectableButton2, self).refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(SelectableButton2, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected

    

            

        
Window.fullscreen = "auto"


class PoytakirjaKivy(App):
    btn_mode = BooleanProperty(True)
    maalit_koti = StringProperty("0")
    maalit_vieras = StringProperty("0")
    koti_porukka = StringProperty("")
    koti_voitolla = BooleanProperty(False)
    vieras_voitolla = BooleanProperty(False)
    tasapeli_menos = BooleanProperty(False)
    onko_vv_kaytos = BooleanProperty(False)
    onko_kv_kaytos = BooleanProperty(False)
    kielisettings = BooleanProperty(True)

    

    def build(self):


        self.screen_setup()

        return self.sm


    def load_widgets(self):
        widgets = ['valikkoscreen', 'pisteporssiscreen', 'tilastoscreen',
                        'joukkuescreen', 'uusijoukkuescreen', 'poytakirjascreen', 'uusipelaajascreen', 'kaikkipelaajatscreen', 'pistetulosscreen', 'asetusscreen']
        for widget in widgets:
            Builder.load_file('kv/{}.kv'.format(widget))

    def screen_setup(self):
        self.load_widgets()

        self.sm = ScreenManager()

        

        self.sm.add_widget(ValikkoScreen(name='valikkoscreen'))
        self.sm.add_widget(PisteporssiScreen(name='pisteporssiscreen'))
        self.sm.add_widget(TilastoScreen(name='tilastoscreen'))
        self.sm.add_widget(JoukkueScreen(name='joukkuescreen'))
        self.sm.add_widget(UusiJoukkueScreen(name='uusijoukkuescreen'))
        self.sm.add_widget(PoytakirjaScreen(name='poytakirjascreen'))
        self.sm.add_widget(UusiPelaajaScreen(name='uusipelaajascreen'))
        self.sm.add_widget(KaikkipelaajatScreen(name='kaikkipelaajatscreen'))
        self.sm.add_widget(PistetulosScreen(name='pistetulosscreen'))
        self.sm.add_widget(AsetusScreen(name='asetusscreen'))

        self.sm.current = 'valikkoscreen'


if __name__ == "__main__":
    PoytakirjaKivy().run()