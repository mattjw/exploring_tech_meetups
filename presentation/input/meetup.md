# Exploring the Geography and Composition of Technology Meetup Communities in the UK

– *Matthew Williams* –

[Meetup](http://www.meetup.com/) provides a rich dataset for the study the composition of tech communities in the UK, and in other counties across the world.

As a regular user of Meetup, I have experience first-hand its value in discovering communities and keeping in touch with them. For organisers and community leaders, Meetup is an extremely useful tool for managing events.

For researchers and data scientists interested in the UK's technology landscape, Meetup can give us insight into what kind of skills are dominant in an area, and what makes a community successful, as demonstrated in this [recent post](http://www.nesta.org.uk/blog/using-meetup-data-explore-uk-digital-tech-landscape) on Nesta's blog.

In this blog post, I present an initial look at two related questions regarding the UK's tech communities:

* How does geography shape the interactions between different communities?
* What is the composition of the tech community in each city? How do they compare across the UK?

Technical details on the methods used in this analysis can be found in the [Supplementary Technical Notes](#suppmat) at the end of the post. 
All scripts and code (including the Markdown for this blog post) are available at the following Github repository: [`https://github.com/mattjw/exploring_tech_meetups`](https://github.com/mattjw/exploring_tech_meetups).





## The data

Using Meetup's [open API](http://www.meetup.com/meetup_api/) I collected a dataset of all Meetup groups in the UK belonging to the 'Tech' category, including their recent events and member profiles. These groups were obtained for the top 200 most-populated cities and towns in the UK, resulting in an initial dataset of 1,588 groups. Given the age of Meetup (almost 13 years old!), many of these groups may be defunct. To focus only on active communities, any groups that don't have at least one event with two or more attendees in the last three years were discarded.

Rather than using Meetup's own city designations, we determine the metropolitan area each group belongs to by using the Eurostat's Functional Urban Areas (FUA) boundary data. This gives us with a consistent definition of an urban area across the UK (and even Europe, if we wanted to expand our study later), and comes with population statistics. For the rest of this post we'll use the FUA definition of city.

The resulting dataset consists of 932 active groups. We further filter the data down by discarding cities with too few groups (four or fewer) for any meaningful analysis, giving 880 groups across 18 cities, and totalling 69,510 users.

Unsurprisingly, London has the most active community, with 588 groups. As noted [previously](http://www.nesta.org.uk/blog/using-meetup-data-explore-uk-digital-tech-landscape), it would be interesting to compare Meetup activity with population size. As we see in the following chart, while London is among the most-active tech communities in the UK, Edinburgh and Cambridge are both ahead in density.

<p align=center>
	<img width="423" src="uk_choropleth.png"/>
</p>


## How are communities shared between cities?

To answer this question we can look at how many attendees each city has in common. Our dataset includes the list of members who RSVPd to each event in a city, and so we can quantify how many attendees a pair of cities has in common.

In the following charts, we visualise the strength of integration among pairs of cities. The intensity of a link between two cities indicates the amount of overlap in their communities – the thicker the link the more in common. For many pairs of cities there are very few shared members, so we only visualise the top quartile of connections.

<p align=center>
	<img width="717" src="uk_covisitors.png"/>
</p>

The network in the left-hand figure shows the total number of users in common. London emerges as a hub, having strong connections to most other cities. This isn't surprising – London has very good transport links (both land and air) with the rest of the UK, and hosts many unique speakers and events that would attract attendees from across the country.

Also, by simply being a large city with many active Meetup users, London has more users to have potentially visited other cities. We can think of this in terms of the [Gravity model of trade and migration](https://en.wikipedia.org/wiki/Gravity_model_of_trade) – each city has a mass (its number of local users), and larger cities have more potential to attract visitors from other cities.

The right-hand figure shows the network after we normalise by the masses of the two respective cities. London's role is now diminished, and its remaining significant interactions are with Cambridge and Oxford (let's not forget the [Golden Triangle](https://en.wikipedia.org/wiki/Golden_triangle_(universities), with many highly skilled STEM professionals, plus extremely good transport access), and Brighton (also an established tech hub).

Some key pairs of neighbouring cities merge: Cardiff and Bristol; Nottingham and Leicester; Glasgow and Edinburgh. We also see a cluster of interacting communities in the midlands. It is likely that due to their smaller size, these communities rely on one another. This contrasts with London, which has a very well-developed self-contained tech scene: residents of London are able to find tech communities to suit their needs without leaving the city.

*Note: An alternative approach to this analysis would be to associate each user with a home city and then study their visits to other locations. Although the API provides the current city for a user, it does not provide historical location information. For further analysis in this direction we'd need to also check, possibly based on changes in their attendance pattern, that a user has not moved home town.*



## What is the composition of each community?

The visualisation below shows the similarities and differences in tech communities across the UK. This is a visual representation of the similarity (or lack thereof) between each city in terms of their communities' interest areas. Two cities that are positioned close together in the chart are more similar.

<p align=center>
	<img width="529" src="cities_mds_similarity.png"/>
</p>

For example, the two most-distant cities are Nottingham and Tyneside, and we can see in the previous figure that their proportions of group types are also very different: Nottingham is 60% `DevOps, NoSQL, & Cloud` whereas Tyneside is 0%. The composition of each city according to its distribution of groups is shown in the following figure.
 
<p align=center>
	<img width="722" src="uk_num_groups_bar_charts.png"/>
</p>

How was the similarity map obtained? Full details can be found [below](#suppmat), but the basic idea is that we can use [https://en.wikipedia.org/wiki/Latent_semantic_analysis](Latent Semantic Analysis) to reduce the 2,068 unique keywords used by Meetup organisers to tag their groups to a (hidden) semantic space of only 150-200 hidden topics. This is because there is a lot of redundancy in keyword selection; for example, the `Web Technology` tag rarely appears without `Web Design`, and both could be more-simply described as simply the Web. Using this simpler semantic space we can then cluster similar groups together, allowing us to identify groups that have the same (single) specialism. We can then inspect these clusters to see what their groups have in common. In this initial analysis seven specialisms were identified.

By assigning only one specialism to a group we can profile each city according to the relative distribution of groups in each specialty. For example, we see that Leeds and Liverpool are very similar, having very similar distributions of specialties, whereas Leicester's large proportion of `Web & Mobile` sets it apart from Cardiff.

We should take this analysis with a pinch of salt because some cities have very low number of groups. This means there are few opportunities for comparison between cities within the UK.
However, we might later extend this analysis to automatically identify counterpart cities in other countries. For example, there is an abundance of very active cities in the US. A follow-up analysis could examine other features of these matched cities' innovation ecosystems to compare the influence of differences in policy, resources, governance, and other interventions (e.g., as with a [quasi-experiment study](https://en.wikipedia.org/wiki/Quasi-experiment)). In other words, we could automatically identify comparable international cities on a large scale in order to help understand our own economy.


## Conclusions and Outlook

laying the foundation for possible future extension to comparison with other countries and cities.

analysis of communities outside London to see what drives clustering of cities.

This has been a first exploration of the tech communities across the UK. Raising some intersting questions for futher analysis.

**Can we match the ecosystem of each UK city with a counterpart in the US?** <br/>
As we've seen, the UK doesn't have a large number of cities for us to compare and contrast, but here are many cities in the US we might compare against. For a particular UK city we could match it with one or more US cities of a similar size and set of interests (e.g., extending group clustering we applied here).

**What drives clusters of cities?**<br/>
For example, in our analysis of integration between cities, we saw that there are places outside of London that have strong connections, such as the Bristol-Cardiff community, and midlands. Bristol and Cardiff are disimilar in their make-up -- does this drive the travel between them? Do small local communities have to travel more, to access specialists in other fields? Drive innovation in regions outsie of London.

Relative to the the number of active users in London, very few people leave. This is not surprising -- London has an abundance of most tech areas. Other places, however, become more specialised.

Match communities in different countries, e.g., the US. Then compare other features of their local innovation ecosystems to see if there are any differences, and potentially compare different policy implications.




# Supplementary Technical Notes
<a name="suppmat"></a>

The following notes give further detail on the methods used in this analysis.

## Collecting Groups

The Meetup API provides a method for querying groups that belong to a particular city or are in proximity to a particular location. [Geonames](http://www.geonames.org/export/) provides an open global gazetteer of cities with populations above 1,000 people. The crawler was seeded with the 200 most-populated cities in the UK according to Geonames. Groups in proximity to these cities were crawled. Duplicate groups (e.g., due to nearby cities) were discarded.

## City/Regional Divisions

There are [many ways](https://theidpblog.files.wordpress.com/2014/08/hierarchical_representation_of_uk_statistical_geographies_july_2014.pdf) to divide the UK into regions (also called 'spatial units'), and many ways we might define a city.

Ideally, we want to choose a definition of region/city for which we also have population statistics available, which will allow us to compare Meetup activity with the area's inhabitants. Plus, we want the definition to be consistently applied throughout the UK.

Fortunately, the European Union [ESPON](http://database.espon.eu/db2/home) project undertook the task of defining [metropolitan regions](https://en.wikipedia.org/wiki/List_of_metropolitan_areas_in_the_United_Kingdom) across 29 EU countries, including the UK. In particular, they define '*Functional Urban Areas*' (FUAs). An FUA consists of an urban core, plus surrounding regions who have a strong commuter relationship with the core. This is a very convenient definition for our analysis, since it describes regions in which Meetup usrse are likely to travel to visit an event. (Incidentally, the US Census Bureau's definition of [Core-based Statistical Areas](https://www.census.gov/geo/reference/gtc/gtc_cbsa.html) is very similar, so we could extend this analysis to the US quite easily.)

The full list of the 46 FUAs in the UK, including their constituent regions, can be found [here](https://en.wikipedia.org/wiki/List_of_metropolitan_areas_in_the_United_Kingdom). The source data files, including boundaries and populations, can be found [here](http://database.espon.eu/db2/resource?idCat=43) under 'Functional Urban Areas database' . Most of the urban regions are intuitively grouped.

The FUA population statistics are estimates from 2006.

## Labelling and Clustering Groups

A latent topic space was learnt on the whole dataset of 1,588 groups UK Meetups groups using Latest Semantic Analysis. Different numbers of features were compared, and good performance was found around 150-200 topics (up to 75% of variance explained). The number of clusters was decided using the Elbow Method (using intra-cluster MSE), resulting in seven clusters. Each of the seven clusters was then manually labelled according to the keyword patterns found in each cluster. Clusters without a clear theme were marked as 'Unclassified'.