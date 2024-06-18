import altair as alt
import altair_saver
import pandas as pd
alt.data_transformers.enable('json')
babyNames = pd.read_csv("dpt2020.csv", sep=";")

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
vis2 = vis1

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