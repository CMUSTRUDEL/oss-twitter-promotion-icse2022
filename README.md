# Overview
This research artifact accompanies our ICSE 2022 paper "'This Is Damn Slick!' Estimating the Impact of Tweets on Open Source Project Popularity and New Contributors". If you use the artifact, please consider citing:


The artifact consists of three main parts:
- Data

   The dataset is used to generate table 2, table 3 and appendix figure 2 in the paper , which contains the following 6 csv files:
   - *parallel_star.csv*: The dynamic change of added stargazers for repositories in control and treatment group, shortly before and after the time of treatment. Used to generate figure 2(a) in the appendix.
   - *parallel_commit.csv*: The dynamic change of new committers for repositories in control and treatment group, shortly before and after the time of treatment. Used to generate figure 2(b) in the appendix.
   - *regression_attraction_effect.csv*: The number of star and new committers for repositories in treatment/control group, before and after the treatment, as well as the independent variables for those repositories at the same time. Used to generate table 2.
   - *regression_dif_committer_non_committer_downsample.csv*: The characteristics of users either attracted by the tweet to commit, or exposed to the same tweet but not attracted. Used to generate model VII in table 3.
   - *regression_dif_tw_non_tw.csv*: The characteristics of repositories mentioned by tweet and users attracted by tweets as new committers, with their activity level after their first commit to the repository. Used to generate model VIII in table 3.
   - *survival_dif_tw_non_tw.csv*: The characteristics of repositories mentioned by tweet and users attracted by tweets as new committers, with their engagement duration. Used to generate model IX in table 3.

   All data is compressed in data.zip, due to space limit, please unzip before use.
- R script

   *analysis_publish_release.Rmd* contains the script used to generate result and figures, you can find more detailed instructions in the script.
- Figure

   Folder figure contains the pdfs for figure 2 in the appendix, you can also generate them yourself by using the *analysis_publish_release.Rmd* script
