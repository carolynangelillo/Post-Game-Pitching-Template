import pandas as pd # csv management
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter # creating pdf
import matplotlib.pyplot as plt # plotting tables
from datetime import date # for getting current date

"""
Directories for saving reports, plots, and images to.

The r before the quotations indicates that these are raw strings, which allow the "\"
character to be used in the directory path without causing an error.
"""
report_directory = r"" 
plot_directory = r""
image_directory = r"" 

trackman = pd.read_csv(filepath) # import postgame trackman csv

pitcher_filter = trackman["PitcherTeam"] == "TEAM_CODE"
trackman = trackman[pitcher_filter] # filter csv to just team pitchers

pitchers = list(trackman["Pitcher"].unique()) # get the list of all pitchers in game
date = str(date.today()) # calculate date for saving file
 

total_b_s = []
for row in trackman["PitchCall"]:
    if row == ("BallCalled"):
        total_b_s.append("Ball")
    elif row == ("HitByPitch"):
        total_b_s.append("Ball")
    elif row == ("BallinDirt"):
        total_b_s.append("Ball")
    else:
        total_b_s.append("Strike")
trackman["TotalBallStrikes"] = total_b_s # mark every pitch as a ball or a strike

'''
Calculates if a pitch was in the zone.

Args:
    x (DataFrame Column): Distance from the y-axis to the ball as it crosses the front of home plate.
    y (DataFram Column): The height of the ball relative to home plate as it crosses the front of the plate.
    xmin(float): The minimum horizontal border of the strike zone.
    xmax(float): The The maximum horizontal border of the strike zone.
    ymin(float): The minimum vertical border of the strike zone.
    ymax(float): The maximum vertical border of the strike zone.

Returns:
    (bool): True if in zone, False if not.

'''
def in_zone(x, y, xmin, xmax, ymin, ymax):
            if xmin <= x <= xmax and ymin <= y <= ymax:
                return True
            else:
                return False

"""

Calcuates an average.

Args:
    x(float): Dividend.
    y(float): Divisor.

Returns:
    (float): x divided by y.

"""
def avg(x, y):
    return x/y

"""

Checks if a pitch was swung at.

Args:
    x(DataFrame Column): Pitch call.

Returns:
    (bool): True if swung at, false if not.

"""
def swing(x):
    if x == "StrikeSwinging":
        return True
    elif x == "InPlay":
        return True
    else:
        return False

trackman["InZone"] = trackman.apply(lambda row: in_zone(row["PlateLocSide"], row["PlateLocHeight"],
                                                        -0.72, 0.72, 1.63, 3.55), axis=1)

trackman["Swings"] = trackman.apply(lambda x: swing(x["PitchCall"]), axis = 1)

outs_gained = []
strikeouts = trackman["KorBB"].tolist()
pitcher_outs = []
field_outs = trackman["OutsOnPlay"].tolist()
for play in strikeouts:
    if play == "Strikeout":
        pitcher_outs.append(1)
    else:
        pitcher_outs.append(0)
for x in range(0, len(strikeouts)):
    outs_gained.append(pitcher_outs[x] + field_outs[x])
trackman["OutsGained"] = outs_gained # Calculate total number of outs at every pitch.

for pitcher in pitchers: # loop through all pitchers
    
    pitcher_filter = trackman["Pitcher"] == pitcher
    cur_pitcher = trackman[pitcher_filter] # filter csv to just current pitcher
    
    pitches = list(cur_pitcher["AutoPitchType"].unique()) # get list of all pitch types
    
    stats_table = pd.DataFrame(columns=('Four-Seam', 'Sinker', 'Cutter', 'Slider', 'Curveball',
                                      'Sweeping Slider', 'Changeup', 'Splitter', 'Side-Arm Slider'))
    stats_table = stats_table[stats_table.columns.intersection(pitches)] # create a table with pitch types as columns

    outs_gained = sum(cur_pitcher["OutsGained"].tolist())
    innings_pitched = outs_gained // 3 + (outs_gained % 3) / 10

    for pitch in pitches: # loop through all pitch types
        
        pitch_filter = cur_pitcher["AutoPitchType"] == pitch
        cur_pitch = cur_pitcher[pitch_filter] # filter to current pitch type

        avg_velo = avg((sum(list(cur_pitch["RelSpeed"]))), len(cur_pitch))
        avg_spin = avg((sum(list(cur_pitch["SpinRate"]))), len(cur_pitch))
        overall_usage = len(cur_pitch) / len(cur_pitcher)
        stats_table.loc["Usage", pitch] = f'{overall_usage :.2f}'
        stats_table.loc["Avg Velo", pitch] = f'{avg_velo :.2f}'
        stats_table.loc["Avg Spin", pitch] = f'{avg_spin :.2f}'

        zone_pitches = list(cur_pitch["InZone"]) # calculating zone %
        if len(zone_pitches) == 1: # covers pitch types that only have one pitch
            if zone_pitches[0] == True:
                stats_table.loc["Zone%", pitch] = 100
            else:
                stats_table.loc["Zone%", pitch] = 0
        elif False not in zone_pitches: # checks if every pitch was in the zone
            zone_rate = 1.00
        else: # all other cases
            in_zone_pitch = cur_pitch['InZone'].value_counts()[False]
            zone_rate = (len(cur_pitch) - in_zone_pitch) / len(cur_pitch)
            zone_rate = f"{zone_rate:.2f}"
        stats_table.loc["Zone%", pitch] = zone_rate # adds zone rate to the table

        swings = cur_pitch["Swings"].tolist() # checks swing %
        if True in swings:
            swing_per = cur_pitch["Swings"].value_counts()[True] / len(cur_pitch)
        else:
            swing_per = 0
        stats_table.loc["Swing%", pitch] = f'{swing_per : .2f}' # adds swing % to table
        
    fig, ax = plt.subplots()
    ax.axis('off')
    t= ax.table(cellText=stats_table.values, colLabels=stats_table.columns, rowLabels=stats_table.index,
                cellLoc='left', loc='center', edges='closed') # plotting the stat table
    if len(pitches) == 1:
        t.scale(1,2)
    elif len(pitches) == 2:
        t.scale(1,1.25)
    elif len(pitches) == 3:
        t.scale(1.4, 1.25)
    elif len(pitches) == 4:
        t.scale(1.4, 1.4)
    elif len(pitches) == 5:
        t.scale(1.5, 1)
    elif len(pitches) == 6:
        t.scale(1, 1) # scales table based on number of pitches
    t.set_fontsize(14)
    plt.margins(x=0)
    fig.set_dpi(1000)
     
    plt.savefig(plot_directory + pitcher + '_stat_table.png', bbox_inches='tight') # saves table for use in report

    w, h = letter # define pdf parameters as letter size
    c = canvas.Canvas(report_directory + date + pitcher + r"_postgame_report.pdf", pagesize = letter) # creates pdf

    c.drawImage(image_directory + "placeholder.jpg", 40, h - 175, width = 150, height = 150)

    text = c.beginText(w - 250, h - 85)
    text.setFont("Times-Roman", 20)
    text.textLine(pitcher)
    text.setFont("Times-Roman", 16)
    text.textLine("Post-Game Pitching Report")
    text.textLine("Innings Pitched: " + str(innings_pitched))
    text.setFont("Times-Roman", 14)
    text.textLine(date)
    c.drawText(text)

    c.setFont("Times-Roman", 16)
    c.drawString(130, h-200, "Stats Table")
    c.drawImage(plot_directory + pitcher + "_stat_table.png", 40, h- 350, width = 250, height = 150)

    c.save()

