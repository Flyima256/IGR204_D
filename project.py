import altair as alt
import altair_saver
import pandas as pd
import numpy as np
import geopandas as gpd # Requires geopandas -- e.g.: conda install -c conda-forge geopandas
import gpdvega

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

# Calculate the percentage of each {gender, name, year} data in relation to the total number of the year
def pourcentageCalculation(onedata) :
    year = onedata['annais']
    totalYear = float(yearSum.nombre[yearSum.annais == year])
    return 100 * float(onedata['nombre']) / totalYear
noDtpNames.loc[:,['pourcentage']] = noDtpNames.apply(lambda onedata: pourcentageCalculation(onedata), axis=1)

# click interaction
point = alt.selection_point()

# visualisation
vis1 = alt.Chart(noDtpNames).transform_calculate(
    genre="datum.sexe == 1 ? 'homme' : 'femme'"
).mark_line().encode(
    x=alt.X('annais:Q', title='Année'),
    y=alt.Y('pourcentage:Q', title='Popularity pourcentage (%)'),
    color=alt.condition(point, alt.Color('preusuel:N').legend(None), alt.value('lightgray')),
    opacity=alt.condition(point, alt.value(1), alt.value(0.05)),
    tooltip=[
        alt.Tooltip('preusuel:N', title='Prénom'),
        alt.Tooltip('genre:N', title='Sexe'),
        alt.Tooltip('annais:Q', title='Année'),
        alt.Tooltip('nombre:Q', title='Nombre')
    ],
    detail='sexe:N',
).properties(
    width  = 1000,
    height = 500
).add_params(
    point
)

vis1.save('Vis1.html')


""" Visualisation 2"""

# merge the 2 datasets
names = depts.merge(names, how='right', left_on='code', right_on='dpt')
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

vis2_1.save('Vis2_1.html')
vis2_2.save('Vis2_2.html')

""" Visualisation 3"""

most_common_names = noDtpNames.loc[noDtpNames.groupby(['sexe', 'annais'])['nombre'].idxmax()]

# percentage 
total_by_year = noDtpNames.groupby(['sexe', 'annais'])['nombre'].sum().reset_index()
most_common_names = most_common_names.merge(total_by_year, on=['sexe', 'annais'], suffixes=('', '_total'))
most_common_names['pourcentage'] = most_common_names['nombre'] / most_common_names['nombre_total'] * 100

#male_names = most_common_names[most_common_names['sexe'] == 1]

#male
male = alt.Chart(most_common_names).mark_bar().encode(
    x=alt.X('pourcentage:Q', title='Proportion nom masculin (%)', scale=alt.Scale(reverse=True)),
    y=alt.Y('annais:O', title='Année', sort=alt.EncodingSortField(field='annais', order='descending'), axis=None)
).transform_filter(
    alt.datum.sexe == 1
).properties(height=alt.Step(20))

textmale = male.mark_text(
    align='right',
    baseline='middle',
    dx=-3  
).encode(
    text='preusuel:N'
)
male_chart = male + textmale

#female
female = alt.Chart(most_common_names).mark_bar().encode(
    x=alt.X('pourcentage:Q', title='Proportion nom feminin (%)'),
    y=alt.Y('annais:O', title='Année', sort=alt.EncodingSortField(field='annais', order='descending'))
).transform_filter(
    alt.datum.sexe == 2
).properties(height=alt.Step(20))

textfemale = female.mark_text(
    align='left',
    baseline='middle',
    dx=3  
).encode(
    text='preusuel:N'
)
female_chart = female + textfemale


# showing graph
vis3 = alt.hconcat(male_chart, female_chart).resolve_scale(y='shared')

vis3.save('Vis3.html')

""" All Visualisation """


allVis = alt.vconcat(vis1, vis2, vis3).resolve_scale(
    color='independent'
)



allVis.save('index.html')
