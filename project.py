import altair as alt
import altair_saver
import pandas as pd
import numpy as np
import geopandas as gpd # Requires geopandas -- e.g.: conda install -c conda-forge geopandas
import gpdvega
from matplotlib import colors as mcolors


alt.data_transformers.enable('json')
babyNames = pd.read_csv("dpt2020.csv", sep=";")

# file for the departments
path = 'departements-version-simplifiee.geojson'
depts = gpd.read_file(path)

# Remove department from data : 
noDtpNames = babyNames.groupby(['sexe', 'preusuel', 'annais'], as_index=False).agg({'nombre': 'sum'})

""" Visualisation 1 """
# Get number of baby for each year
yearSum = noDtpNames.groupby(['annais'], as_index=False).agg({'nombre': 'sum'})
maxPercentage = 0

# Calculate the percentage of each {gender, name, year} data in relation to the total number of the year
def pourcentageCalculation(onedata) :
    year = onedata['annais']
    totalYear = float(yearSum.nombre[yearSum.annais == year])
    return 100 * float(onedata['nombre']) / totalYear
noDtpNames.loc[:,['pourcentage']] = noDtpNames.apply(lambda onedata: pourcentageCalculation(onedata), axis=1)

maxPercentage = np.max(noDtpNames['pourcentage'])
# interactions
# click
point_vis1 = alt.selection_point()

# search
search_input_Vis1 = alt.param(
    value='',
    bind=alt.binding(
        input='search',
        placeholder="Name",
        name='Search '
    )
)

# slider
slider_vis1 = alt.param(
    value=1.0,
    bind=alt.binding_range(min=0, max=maxPercentage, step=0.01, name='Max pourcentage ')
)

# visualisation
vis1 = alt.Chart(noDtpNames).transform_calculate(
    genre="datum.sexe == 1 ? 'homme' : 'femme'"
).transform_filter(
    (alt.expr.test(alt.expr.regexp(search_input_Vis1, 'i'), alt.datum.preusuel)) &
    (alt.datum.pourcentage <= slider_vis1)
).mark_line().encode(
    x=alt.X('annais:Q', title='Année'),
    y=alt.Y('pourcentage:Q', title='Popularity pourcentage (%)'),
    color=alt.condition(point_vis1, alt.Color('preusuel:N').legend(None), alt.value('lightgray')),
    opacity=alt.condition(point_vis1, alt.value(1), alt.value(0.05)),
    tooltip=[
        alt.Tooltip('preusuel:N', title='Prénom'),
        alt.Tooltip('genre:N', title='Sexe'),
        alt.Tooltip('annais:Q', title='Année'),
        alt.Tooltip('nombre:Q', title='Nombre'),
        alt.Tooltip('pourcentage:Q', title='Pourcentage')
    ],
    detail='sexe:N',
).properties(
    width  = 1000,
    height = 500
).add_params(
    point_vis1, search_input_Vis1, slider_vis1
)

vis1.save('Html/Vis1.html')


""" Visualisation 2"""
vis2 = None
# merge the 2 datasets
names = depts.merge(babyNames, how='right', left_on='code', right_on='dpt')
grouped = names.groupby(['dpt', 'preusuel', 'sexe', 'geometry', 'nom', 'code'], as_index=False).sum()

# on this part, we will take the 3 most popular names of each department and see how they are distributed accross the country

# get the top 3 names in each department
top_3_names = grouped.groupby('dpt').apply(lambda x: x.nlargest(3, 'nombre'))

# randomly select 5 departments for which we will choose the 3 most popular names
num_departments = np.random.randint(1, 96, size=5)

# select the names in those departments and draw the maps
for num in num_departments:
    pop_names = top_3_names[top_3_names.code == str(num)].preusuel.to_list()
    name_dpt = top_3_names[top_3_names.code == str(num)].nom[0]
    charts = []
    for i in range(len(pop_names)):
      # get the rows corresponding to that name
      subset = grouped[grouped.preusuel == pop_names[i]]

      # take the columns we want
      subset_interesting_columns = subset[['nom', 'code', 'geometry', 'nombre']]

      # convert geometries to GeoJSON-like dictionaries
      data = gpd.GeoDataFrame(subset_interesting_columns, geometry='geometry', crs='EPSG:4326')

      # convert to geovega to easy the plotting
      geovega_data = gpdvega.geojson_feature(data, feature='features')

      chart = alt.Chart(geovega_data).mark_geoshape().project().encode(
          tooltip = ['properties.nom:N', 'properties.code:N'],
          color = alt.Color('properties.nombre:Q', scale = alt.Scale(scheme='viridis'))
      ).properties(
          width = 400,
          height = 400,
          title = f'Repartition accross France of one of the most popular name in {name_dpt} : {pop_names[i]}'
      )
      charts.append(chart)
    
    # plot the charts
    vis2_1 = alt.hconcat(charts[0], charts[1], charts[2]).resolve_scale(
        color = 'independent'
    )
    if (vis2 == None) :
        vis2 = vis2_1
    else :
        vis2 = alt.vconcat(vis2, vis2_1).resolve_scale(color='independent')
    vis2_1.save('Html/Vis2_1' + str(num) + '.html')

# on this part, we will take the 3 less popular names of each department and see how they are distributed accross the country

# get the top 3 names in each department
last_3_names = grouped.groupby('dpt').apply(lambda x: x.nsmallest(3, 'nombre'))

# select the names in those departments and draw the maps
for num in num_departments:
    last_names = last_3_names[last_3_names.code == str(num)].preusuel.to_list()
    name_dpt = last_3_names[last_3_names.code == str(num)].nom[0]
    charts = []
    for i in range(len(last_names)):
      # get the rows corresponding to that name
      subset = grouped[grouped.preusuel == last_names[i]]

      # take the columns we want
      subset_interesting_columns = subset[['nom', 'code', 'geometry', 'nombre']]

      # convert geometries to GeoJSON-like dictionaries
      data = gpd.GeoDataFrame(subset_interesting_columns, geometry='geometry', crs='EPSG:4326')

      # convert to geovega to easy the plotting
      geovega_data = gpdvega.geojson_feature(data, feature='features')

      chart = alt.Chart(geovega_data).mark_geoshape().project().encode(
          tooltip = ['properties.nom:N', 'properties.code:N'],
          color = alt.condition(alt.datum['properties.nombre'] == None, alt.value('grey'), 'properties.nombre:Q', scale = alt.Scale(scheme='viridis')) 
      ).properties(
          width = 400,
          height = 400,
          title = f'Repartition accross France of one of the less popular name in {name_dpt} : {last_names[i]}'
      )
      charts.append(chart)
    
    # plot the charts
    vis2_2 = alt.hconcat(charts[0], charts[1], charts[2]).resolve_scale(
        color = 'independent'
    )
    vis2 = alt.vconcat(vis2, vis2_2).resolve_scale(color='independent')
    vis2_2.save('Html/Vis2_2' + str(num) + '.html')

vis2.save('Html/Vis2.html')
""" Visualisation 3"""

cleaned_babyNames = babyNames[babyNames['preusuel'] != '_PRENOMS_RARES']

noDtpNames = cleaned_babyNames.groupby(['sexe', 'preusuel', 'annais'], as_index=False).agg({'nombre': 'sum'})

most_common_names = noDtpNames.loc[noDtpNames.groupby(['sexe', 'annais'])['nombre'].idxmax()]

# percentage 
total_by_year = noDtpNames.groupby(['sexe', 'annais'])['nombre'].sum().reset_index()
most_common_names = most_common_names.merge(total_by_year, on=['sexe', 'annais'], suffixes=('', '_total'))
most_common_names['pourcentage'] = most_common_names['nombre'] / most_common_names['nombre_total'] * 100
filtered_data = most_common_names[most_common_names['annais'].str.contains(r'^\d+$', na=False)]
most_common_names =filtered_data
x_domain = [0, most_common_names['pourcentage'].max()]


#male_names = most_common_names[most_common_names['sexe'] == 1]

#cell for attribution of colors for each names

def generate_hex_colors(n):
    hsv_tuples = [(x*1.0/n, 0.5, 0.5) for x in range(n)]
    hex_colors = [mcolors.hsv_to_rgb(hsv) for hsv in hsv_tuples]
    return [mcolors.rgb2hex(rgb) for rgb in hex_colors]

def create_color_mapping(data):
    names_colors = {}
    for sexe, group in data.groupby('sexe'):
        unique_names = group['preusuel'].unique()
        colors = generate_hex_colors(len(unique_names))
        np.random.shuffle(colors)  
        names_colors[sexe] = dict(zip(unique_names, colors))
    return names_colors

color_mappings = create_color_mapping(most_common_names)

def add_text_to_bars(chart, sex):
    if(sex ==1):
        dx_val = -3
        return chart.mark_text(align=('right'), baseline='middle', dx=dx_val).encode(
        text='preusuel:N'
    )
    else:
        dx_val = 3
        return chart.mark_text(align=('left'), baseline='middle', dx=dx_val).encode(
            text='preusuel:N'
        )
def chart_for_sex(sex):
    filtered_data = most_common_names[most_common_names['sexe'] == sex]
    colors = color_mappings[sex]
    return alt.Chart(filtered_data).mark_bar().encode(
        x=alt.X('pourcentage:Q', title=f'Proportion nom {"masculin" if sex == 1 else "féminin"} (%)', scale=alt.Scale(domain=x_domain, reverse=(sex==1))),
        y= alt.Y('annais:O', title='Année', sort=alt.EncodingSortField(field='annais', order='descending'),  axis=None) if sex==1 else alt.Y('annais:O', title='Année', sort=alt.EncodingSortField(field='annais', order='descending')) ,
        color=alt.Color('preusuel:N', title='prénom', scale=alt.Scale(domain=list(colors.keys()), range=list(colors.values())), legend=None),
        tooltip=[alt.Tooltip('preusuel:N', title='prénom'), 'pourcentage:Q']
    ).properties(height=alt.Step(20))


male_chart = chart_for_sex(1)
textmale = add_text_to_bars(male_chart, 1)

female_chart = chart_for_sex(2)
textfemale = add_text_to_bars(female_chart, 2)


female = female_chart + textfemale
male = male_chart + textmale

# showing graph
vis3 = alt.hconcat(male, female).resolve_scale(y='shared')

vis3.save('Html/Vis3.html')



""" All Visualisations """

allVis = alt.vconcat(vis1, vis2, vis3).resolve_scale(
    color='independent'
)

allVis.save('Html/index.html')
