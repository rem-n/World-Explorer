import tkinter as tk
import geopandas as gpd
import matplotlib


matplotlib.use("TkAgg")  #rasm kharita f tk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import sqlite3


conn = sqlite3.connect("world.db")#connect 
cursor = conn.cursor()


#------------------------------------
# 9arat
cursor.execute("""
CREATE TABLE IF NOT EXISTS continents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
)
""") 

# money
cursor.execute("""
CREATE TABLE IF NOT EXISTS currencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    code TEXT,
    symbol TEXT
)
""")

# dawla country
cursor.execute("""
CREATE TABLE IF NOT EXISTS countries (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    capital TEXT,
    continent_id INTEGER,
    area REAL,
    population INTEGER,
    currency_id INTEGER,

    FOREIGN KEY (continent_id)
    REFERENCES continents(id),

    FOREIGN KEY (currency_id)
    REFERENCES currencies(id)
)
""")

# lang loghat 
cursor.execute("""
CREATE TABLE IF NOT EXISTS languages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL
)
""")

# logha kola dawla 
cursor.execute("""
CREATE TABLE IF NOT EXISTS country_languages (
    country_id INTEGER,
    language_id INTEGER,

    PRIMARY KEY (country_id, language_id),

    FOREIGN KEY (country_id)
    REFERENCES countries(id),

    FOREIGN KEY (language_id)
    REFERENCES languages(id)
)
""")

conn.commit()


# ----------------------win
win = tk.Tk()

win.title("WORLD INFO")
win.geometry("1200x600")
win.configure(bg="white")
win.iconbitmap("logo.ico")


# frame 
info_frame = tk.Frame(win, bg="white", bd=1, relief="sunken")

info_frame.place(x=20,y=20,width=300,height=360)

country_title = tk.Label(info_frame,text="Select a country",
                         font=("Arial", 20, "bold"),
                         bg="white",
                         fg="black"
)

country_title.pack(
    pady=(20, 15)
)

country_info = tk.Label(
    info_frame,
    text="",
    font=("Arial", 13),
    bg="white",
    fg="black",
    justify="left",
    anchor="w"
)

country_info.pack(
    padx=20,
    fill="x"
)



# الخريطة
countries = gpd.read_file(
    "ne_110m_admin_0_countries.geojson"
)

fig, ax = plt.subplots()

countries.plot(
    ax=ax,
    color="gray",
    edgecolor="black"  # 7odod 
)

ax.axis("off")


canvas = FigureCanvasTkAgg(
    fig,
    win
)

canvas.get_tk_widget().pack(
    fill="both",
    expand=True
)


# variables الخريطة
dragging = False
start_x = 0
start_y = 0
hovered_country = None


# bidayat l7araka
def start_move(event):
    global dragging
    global start_x
    global start_y
    if event.button == 1:
        dragging = True
        start_x = event.x
        start_y = event.y


# حركة الماوس
def move(event):
    global start_x
    global start_y
    global hovered_country

    # hnaya ila sa7b
    if dragging:
        dx = event.x - start_x
        dy = event.y - start_y

        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()
        # tol 3ard
        width = canvas.get_tk_widget().winfo_width()
        height = canvas.get_tk_widget().winfo_height()

        if width == 0 or height == 0:
            return

        ax.set_xlim(
            xmin - dx * (xmax - xmin) / width,
            xmax - dx * (xmax - xmin) / width
        )

        ax.set_ylim(
            ymin - dy * (ymax - ymin) / height,
            ymax - dy * (ymax - ymin) / height
        )

        start_x = event.x
        start_y = event.y

        canvas.draw_idle()  # rasm lkharita man jdid
        return

    
    # Hover ila ma7araknach return
    if event.xdata is None or event.ydata is None:
        return

    point = gpd.GeoSeries.from_xy(
        [event.xdata],
        [event.ydata],
        crs=countries.crs
    )[0]

    # wach no9ta kayna wast chi dawla true false
    inside = countries.geometry.contains(point)

    # ila no9ta wast man dawla true + index
    index = inside.idxmax() if inside.any() else None

    if index == hovered_country:
        return

    hovered_country = index

    # 7ifd l7odo
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()

    # mas7
    ax.clear()
    #  3awd irsam lkharita 
    countries.plot(
        ax=ax,
        color="gray",
        edgecolor="black"
    )

    #ila kan fo9 chi dawla 
    if index is not None:
        # kanlawnoha bla7mar
        countries.iloc[[index]].plot(
            ax=ax,
            color="red",
            edgecolor="black"
        )

    # rasm l7odo mara khra
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)

    ax.set_aspect("auto")
    ax.set_autoscale_on(False)
    ax.axis("off")

    canvas.draw_idle()



def stop_move(event):

    global dragging
    # sa7b done
    dragging = False

    if event.xdata is None or event.ydata is None:
        return

    point = gpd.GeoSeries.from_xy(
        [event.xdata],
        [event.ydata],
        crs=countries.crs
    )[0]
    inside = countries.geometry.contains(point)

    if not inside.any():
        country_title.config(text="Unknown")
        country_info.config(text="Country information not found")
        return
    index = inside.idxmax()


    # country name from map
    if "ADMIN" in countries.columns:
        name = countries.loc[index, "ADMIN"]

    elif "NAME" in countries.columns:
        name = countries.loc[index, "NAME"]

    else:
        name = "Unknown"

    # country informations database
    cursor.execute("""
        SELECT
            countries.name, 
            countries.capital, 
            continents.name, 
            countries.area,
            countries.population, 
            currencies.name,
            currencies.code,
            currencies.symbol,
            GROUP_CONCAT(languages.name, ', ')
        FROM countries

        LEFT JOIN continents
        ON countries.continent_id = continents.id

        LEFT JOIN currencies
        ON countries.currency_id = currencies.id

        LEFT JOIN country_languages
        ON countries.id = country_languages.country_id

        LEFT JOIN languages
        ON country_languages.language_id = languages.id

        WHERE countries.name = ?

        GROUP BY countries.id
    """, (name,))

    country = cursor.fetchone()

    if not country:
        country_title.config(
            text=name
        )

        country_info.config(
            text="Country information not found."
        )
        return

    country_title.config(
        text=country[0]
    )

    country_info.config(
        text=f"""
Capital:     {country[1]}

Continent:   {country[2]}

Area:        {country[3]:,.0f} km²

Population:  {country[4]:,}

Currency:    {country[5]} ({country[6]})

Language:    {country[8]}
"""
    )

    info_frame.lift()


# التكبير
def zoom_in():
    # 7odod l7alia
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    # 7isab lmarkaz
    x = (xmin + xmax) / 2
    y = (ymin + ymax) / 2

    
    factor = 0.7

    ax.set_xlim(
        x - (x - xmin) * factor,
        x + (xmax - x) * factor
    )

    ax.set_ylim(
        y - (y - ymin) * factor,
        y + (ymax - y) * factor
    )

    canvas.draw_idle()

# التصغير
def zoom_out():

    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()

    x = (xmin + xmax) / 2
    y = (ymin + ymax) / 2

    factor = 1.4

    ax.set_xlim(
        x - (x - xmin) * factor,
        x + (xmax - x) * factor
    )

    ax.set_ylim(
        y - (y - ymin) * factor,
        y + (ymax - y) * factor
    )

    canvas.draw_idle()


# button
button_plus = tk.Button(
    win,
    text="+",
    font=("Arial", 18, "bold"),
    width=3,
    bg="green",
    command=zoom_in
)

button_plus.place(
    x=1100,
    y=40
)


button_minus = tk.Button(
    win,
    text="−",
    font=("Arial", 18, "bold"),
    width=3,
    bg="red",
    command=zoom_out
)

button_minus.place(
    x=1100,
    y=90
)


# daght 
canvas.mpl_connect(
    "button_press_event",
    start_move
)
# move 
canvas.mpl_connect(
    "motion_notify_event",
    move
)
# raf3 zir 
canvas.mpl_connect(
    "button_release_event",
    stop_move
)


win.mainloop()

conn.close()