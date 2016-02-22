{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "version 1.0.1\n",
    "#![Spark Logo](http://spark-mooc.github.io/web-assets/images/ta_Spark-logo-small.png) + ![Python Logo](http://spark-mooc.github.io/web-assets/images/python-logo-master-v3-TM-flattened_small.png)\n",
    "# **Introduction to Machine Learning with Apache Spark**\n",
    "## **Predicting Movie Ratings**\n",
    "#### One of the most common uses of big data is to predict what users want.  This allows Google to show you relevant ads, Amazon to recommend relevant products, and Netflix to recommend movies that you might like.  This lab will demonstrate how we can use Apache Spark to recommend movies to a user.  We will start with some basic techniques, and then use the [Spark MLlib][mllib] library's Alternating Least Squares method to make more sophisticated predictions.\n",
    "#### For this lab, we will use a subset dataset of 500,000 ratings we have included for you into your VM (and on Databricks) from the [movielens 10M stable benchmark rating dataset](http://grouplens.org/datasets/movielens/). However, the same code you write will work for the full dataset, or their latest dataset of 21 million ratings.\n",
    "#### In this lab:\n",
    "#### *Part 0*: Preliminaries\n",
    "#### *Part 1*: Basic Recommendations\n",
    "#### *Part 2*: Collaborative Filtering\n",
    "#### *Part 3*: Predictions for Yourself\n",
    "#### As mentioned during the first Learning Spark lab, think carefully before calling `collect()` on any datasets.  When you are using a small dataset, calling `collect()` and then using Python to get a sense for the data locally (in the driver program) will work fine, but this will not work when you are using a large dataset that doesn't fit in memory on one machine.  Solutions that call `collect()` and do local analysis that could have been done with Spark will likely fail in the autograder and not receive full credit.\n",
    "[mllib]: https://spark.apache.org/mllib/"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Code\n",
    "#### This assignment can be completed using basic Python and pySpark Transformations and Actions.  Libraries other than math are not necessary. With the exception of the ML functions that we introduce in this assignment, you should be able to complete all parts of this homework using only the Spark functions you have used in prior lab exercises (although you are welcome to use more features of Spark if you like!)."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 1,
   "metadata": {
    "collapsed": false
   },
   "outputs": [],
   "source": [
    "import sys\n",
    "import os\n",
    "from test_helper import Test\n",
    "\n",
    "baseDir = os.path.join('data')\n",
    "inputPath = os.path.join('cs100', 'lab4', 'small')\n",
    "\n",
    "ratingsFilename = os.path.join(baseDir, inputPath, 'ratings.dat.gz')\n",
    "moviesFilename = os.path.join(baseDir, inputPath, 'movies.dat')"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### **Part 0: Preliminaries**\n",
    "#### We read in each of the files and create an RDD consisting of parsed lines.\n",
    "#### Each line in the ratings dataset (`ratings.dat.gz`) is formatted as:\n",
    "####   `UserID::MovieID::Rating::Timestamp`\n",
    "#### Each line in the movies (`movies.dat`) dataset is formatted as:\n",
    "####   `MovieID::Title::Genres`\n",
    "#### The `Genres` field has the format\n",
    "####   `Genres1|Genres2|Genres3|...`\n",
    "#### The format of these files is uniform and simple, so we can use Python [`split()`](https://docs.python.org/2/library/stdtypes.html#str.split) to parse their lines.\n",
    "#### Parsing the two files yields two RDDS\n",
    "* #### For each line in the ratings dataset, we create a tuple of (UserID, MovieID, Rating). We drop the timestamp because we do not need it for this exercise.\n",
    "* #### For each line in the movies dataset, we create a tuple of (MovieID, Title). We drop the Genres because we do not need them for this exercise."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 2,
   "metadata": {
    "collapsed": false
   },
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "There are 487650 ratings and 3883 movies in the datasets\n",
      "Ratings: [(1, 1193, 5.0), (1, 914, 3.0), (1, 2355, 5.0)]\n",
      "Movies: [(1, u'Toy Story (1995)'), (2, u'Jumanji (1995)'), (3, u'Grumpier Old Men (1995)')]\n"
     ]
    }
   ],
   "source": [
    "numPartitions = 2\n",
    "rawRatings = sc.textFile(ratingsFilename).repartition(numPartitions)\n",
    "rawMovies = sc.textFile(moviesFilename)\n",
    "\n",
    "def get_ratings_tuple(entry):\n",
    "    \"\"\" Parse a line in the ratings dataset\n",
    "    Args:\n",
    "        entry (str): a line in the ratings dataset in the form of UserID::MovieID::Rating::Timestamp\n",
    "    Returns:\n",
    "        tuple: (UserID, MovieID, Rating)\n",
    "    \"\"\"\n",
    "    items = entry.split('::')\n",
    "    return int(items[0]), int(items[1]), float(items[2])\n",
    "\n",
    "\n",
    "def get_movie_tuple(entry):\n",
    "    \"\"\" Parse a line in the movies dataset\n",
    "    Args:\n",
    "        entry (str): a line in the movies dataset in the form of MovieID::Title::Genres\n",
    "    Returns:\n",
    "        tuple: (MovieID, Title)\n",
    "    \"\"\"\n",
    "    items = entry.split('::')\n",
    "    return int(items[0]), items[1]\n",
    "\n",
    "\n",
    "ratingsRDD = rawRatings.map(get_ratings_tuple).cache()\n",
    "moviesRDD = rawMovies.map(get_movie_tuple).cache()\n",
    "\n",
    "ratingsCount = ratingsRDD.count()\n",
    "moviesCount = moviesRDD.count()\n",
    "\n",
    "print 'There are %s ratings and %s movies in the datasets' % (ratingsCount, moviesCount)\n",
    "print 'Ratings: %s' % ratingsRDD.take(3)\n",
    "print 'Movies: %s' % moviesRDD.take(3)\n",
    "\n",
    "assert ratingsCount == 487650\n",
    "assert moviesCount == 3883\n",
    "assert moviesRDD.filter(lambda (id, title): title == 'Toy Story (1995)').count() == 1\n",
    "assert (ratingsRDD.takeOrdered(1, key=lambda (user, movie, rating): movie)\n",
    "        == [(1, 1, 5.0)])"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### In this lab we will be examining subsets of the tuples we create (e.g., the top rated movies by users). Whenever we examine only a subset of a large dataset, there is the potential that the result will depend on the order we perform operations, such as joins, or how the data is partitioned across the workers. What we want to guarantee is that we always see the same results for a subset, independent of how we manipulate or store the data.\n",
    "#### We can do that by sorting before we examine a subset. You might think that the most obvious choice when dealing with an RDD of tuples would be to use the [`sortByKey()` method][sortbykey]. However this choice is problematic, as we can still end up with different results if the key is not unique.\n",
    "#### Note: It is important to use the [`unicode` type](https://docs.python.org/2/howto/unicode.html#the-unicode-type) instead of the `string` type as the titles are in unicode characters.\n",
    "#### Consider the following example, and note that while the sets are equal, the printed lists are usually in different order by value, *although they may randomly match up from time to time.*\n",
    "#### You can try running this multiple times.  If the last assertion fails, don't worry about it: that was just the luck of the draw.  And note that in some environments the results may be more deterministic.\n",
    "[sortbykey]: https://spark.apache.org/docs/latest/api/python/pyspark.html#pyspark.RDD.sortByKey"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 4,
   "metadata": {
    "collapsed": false
   },
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "[(1, u'alpha'), (1, u'epsilon'), (1, u'delta'), (2, u'alpha'), (2, u'beta'), (3, u'alpha')]\n",
      "[(1, u'delta'), (1, u'epsilon'), (1, u'alpha'), (2, u'alpha'), (2, u'beta'), (3, u'alpha')]\n"
     ]
    }
   ],
   "source": [
    "tmp1 = [(1, u'alpha'), (2, u'alpha'), (2, u'beta'), (3, u'alpha'), (1, u'epsilon'), (1, u'delta')]\n",
    "tmp2 = [(1, u'delta'), (2, u'alpha'), (2, u'beta'), (3, u'alpha'), (1, u'epsilon'), (1, u'alpha')]\n",
    "\n",
    "oneRDD = sc.parallelize(tmp1)\n",
    "twoRDD = sc.parallelize(tmp2)\n",
    "oneSorted = oneRDD.sortByKey(True).collect()\n",
    "twoSorted = twoRDD.sortByKey(True).collect()\n",
    "print oneSorted\n",
    "print twoSorted\n",
    "assert set(oneSorted) == set(twoSorted)     # Note that both lists have the same elements\n",
    "assert twoSorted[0][0] < twoSorted.pop()[0] # Check that it is sorted by the keys\n",
    "assert oneSorted[0:2] != twoSorted[0:2]     # Note that the subset consisting of the first two elements does not match"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### Even though the two lists contain identical tuples, the difference in ordering *sometimes* yields a different ordering for the sorted RDD (try running the cell repeatedly and see if the results change or the assertion fails). If we only examined the first two elements of the RDD (e.g., using `take(2)`), then we would observe different answers - **that is a really bad outcome as we want identical input data to always yield identical output**. A better technique is to sort the RDD by *both the key and value*, which we can do by combining the key and value into a single string and then sorting on that string. Since the key is an integer and the value is a unicode string, we can use a function to combine them into a single unicode string (e.g., `unicode('%.3f' % key) + ' ' + value`) before sorting the RDD using [sortBy()][sortby].\n",
    "[sortby]: https://spark.apache.org/docs/latest/api/python/pyspark.html#pyspark.RDD.sortBy"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 5,
   "metadata": {
    "collapsed": false
   },
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "[(1, u'alpha'), (1, u'delta'), (1, u'epsilon'), (2, u'alpha'), (2, u'beta'), (3, u'alpha')]\n",
      "[(1, u'alpha'), (1, u'delta'), (1, u'epsilon'), (2, u'alpha'), (2, u'beta'), (3, u'alpha')]\n"
     ]
    }
   ],
   "source": [
    "def sortFunction(tuple):\n",
    "    \"\"\" Construct the sort string (does not perform actual sorting)\n",
    "    Args:\n",
    "        tuple: (rating, MovieName)\n",
    "    Returns:\n",
    "        sortString: the value to sort with, 'rating MovieName'\n",
    "    \"\"\"\n",
    "    key = unicode('%.3f' % tuple[0])\n",
    "    value = tuple[1]\n",
    "    return (key + ' ' + value)\n",
    "\n",
    "\n",
    "print oneRDD.sortBy(sortFunction, True).collect()\n",
    "print twoRDD.sortBy(sortFunction, True).collect()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### If we just want to look at the first few elements of the RDD in sorted order, we can use the [takeOrdered][takeordered] method with the `sortFunction` we defined.\n",
    "[takeordered]: https://spark.apache.org/docs/latest/api/python/pyspark.html#pyspark.RDD.takeOrdered"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 6,
   "metadata": {
    "collapsed": false
   },
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "one is [(1, u'alpha'), (1, u'delta'), (1, u'epsilon'), (2, u'alpha'), (2, u'beta'), (3, u'alpha')]\n",
      "two is [(1, u'alpha'), (1, u'delta'), (1, u'epsilon'), (2, u'alpha'), (2, u'beta'), (3, u'alpha')]\n"
     ]
    }
   ],
   "source": [
    "oneSorted1 = oneRDD.takeOrdered(oneRDD.count(),key=sortFunction)\n",
    "twoSorted1 = twoRDD.takeOrdered(twoRDD.count(),key=sortFunction)\n",
    "print 'one is %s' % oneSorted1\n",
    "print 'two is %s' % twoSorted1\n",
    "assert oneSorted1 == twoSorted1"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### **Part 1: Basic Recommendations**\n",
    "#### One way to recommend movies is to always recommend the movies with the highest average rating. In this part, we will use Spark to find the name, number of ratings, and the average rating of the 20 movies with the highest average rating and more than 500 reviews. We want to filter our movies with high ratings but fewer than or equal to 500 reviews because movies with few reviews may not have broad appeal to everyone."
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### **(1a) Number of Ratings and Average Ratings for a Movie**\n",
    "#### Using only Python, implement a helper function `getCountsAndAverages()` that takes a single tuple of (MovieID, (Rating1, Rating2, Rating3, ...)) and returns a tuple of (MovieID, (number of ratings, averageRating)). For example, given the tuple `(100, (10.0, 20.0, 30.0))`, your function should return `(100, (3, 20.0))`"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 11,
   "metadata": {
    "collapsed": false
   },
   "outputs": [],
   "source": [
    "# TODO: Replace <FILL IN> with appropriate code\n",
    "\n",
    "# First, implement a helper function `getCountsAndAverages` using only Python\n",
    "def getCountsAndAverages(IDandRatingsTuple):\n",
    "    \"\"\" Calculate average rating\n",
    "    Args:\n",
    "        IDandRatingsTuple: a single tuple of (MovieID, (Rating1, Rating2, Rating3, ...))\n",
    "    Returns:\n",
    "        tuple: a tuple of (MovieID, (number of ratings, averageRating))\n",
    "    \"\"\"\n",
    "    movie_id, rating_tup = IDandRatingsTuple\n",
    "    num_ratings = len(rating_tup)\n",
    "    averageRating = sum(rating_tup)/float(num_ratings)\n",
    "    \n",
    "    return (movie_id,(num_ratings,averageRating))"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 12,
   "metadata": {
    "collapsed": false
   },
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "1 test passed.\n",
      "1 test passed.\n",
      "1 test passed.\n"
     ]
    }
   ],
   "source": [
    "# TEST Number of Ratings and Average Ratings for a Movie (1a)\n",
    "\n",
    "Test.assertEquals(getCountsAndAverages((1, (1, 2, 3, 4))), (1, (4, 2.5)),\n",
    "                            'incorrect getCountsAndAverages() with integer list')\n",
    "Test.assertEquals(getCountsAndAverages((100, (10.0, 20.0, 30.0))), (100, (3, 20.0)),\n",
    "                            'incorrect getCountsAndAverages() with float list')\n",
    "Test.assertEquals(getCountsAndAverages((110, xrange(20))), (110, (20, 9.5)),\n",
    "                            'incorrect getCountsAndAverages() with xrange')"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### **(1b) Movies with Highest Average Ratings**\n",
    "#### Now that we have a way to calculate the average ratings, we will use the `getCountsAndAverages()` helper function with Spark to determine movies with highest average ratings.\n",
    "#### The steps you should perform are:\n",
    "* #### Recall that the `ratingsRDD` contains tuples of the form (UserID, MovieID, Rating). From `ratingsRDD` create an RDD with tuples of the form (MovieID, Python iterable of Ratings for that MovieID). This transformation will yield an RDD of the form: `[(1, <pyspark.resultiterable.ResultIterable object at 0x7f16d50e7c90>), (2, <pyspark.resultiterable.ResultIterable object at 0x7f16d50e79d0>), (3, <pyspark.resultiterable.ResultIterable object at 0x7f16d50e7610>)]`. Note that you will only need to perform two Spark transformations to do this step.\n",
    "* #### Using `movieIDsWithRatingsRDD` and your `getCountsAndAverages()` helper function, compute the number of ratings and average rating for each movie to yield tuples of the form (MovieID, (number of ratings, average rating)). This transformation will yield an RDD of the form: `[(1, (993, 4.145015105740181)), (2, (332, 3.174698795180723)), (3, (299, 3.0468227424749164))]`. You can do this step with one Spark transformation\n",
    "* #### We want to see movie names, instead of movie IDs. To `moviesRDD`, apply RDD transformations that use `movieIDsWithAvgRatingsRDD` to get the movie names for `movieIDsWithAvgRatingsRDD`, yielding tuples of the form (average rating, movie name, number of ratings). This set of transformations will yield an RDD of the form: `[(1.0, u'Autopsy (Macchie Solari) (1975)', 1), (1.0, u'Better Living (1998)', 1), (1.0, u'Big Squeeze, The (1996)', 3)]`. You will need to do two Spark transformations to complete this step: first use the `moviesRDD` with `movieIDsWithAvgRatingsRDD` to create a new RDD with Movie names matched to Movie IDs, then convert that RDD into the form of (average rating, movie name, number of ratings). These transformations will yield an RDD that looks like: `[(3.6818181818181817, u'Happiest Millionaire, The (1967)', 22), (3.0468227424749164, u'Grumpier Old Men (1995)', 299), (2.882978723404255, u'Hocus Pocus (1993)', 94)]`"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 22,
   "metadata": {
    "collapsed": false
   },
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "movieIDsWithRatingsRDD: [(2, <pyspark.resultiterable.ResultIterable object at 0xb0bcf7ac>), (4, <pyspark.resultiterable.ResultIterable object at 0xb0bcf84c>), (6, <pyspark.resultiterable.ResultIterable object at 0xb0bcf86c>)]\n",
      "\n",
      "movieIDsWithAvgRatingsRDD: [(2, (332, 3.174698795180723)), (4, (71, 2.676056338028169)), (6, (442, 3.7918552036199094))]\n",
      "\n",
      "movieNameWithAvgRatingsRDD: [(3.5671641791044775, u'Great Mouse Detective, The (1986)', 67), (3.763948497854077, u'Moonstruck (1987)', 466), (2.676056338028169, u'Waiting to Exhale (1995)', 71)]\n",
      "\n"
     ]
    }
   ],
   "source": [
    "# TODO: Replace <FILL IN> with appropriate code\n",
    "\n",
    "# From ratingsRDD with tuples of (UserID, MovieID, Rating) create an RDD with tuples of\n",
    "# the (MovieID, iterable of Ratings for that MovieID)\n",
    "movieIDsWithRatingsRDD = (ratingsRDD.map(lambda x : (x[1],x[2])).groupByKey())\n",
    "print 'movieIDsWithRatingsRDD: %s\\n' % movieIDsWithRatingsRDD.take(3)\n",
    "\n",
    "# Using `movieIDsWithRatingsRDD`, compute the number of ratings and average rating for each movie to\n",
    "# yield tuples of the form (MovieID, (number of ratings, average rating))\n",
    "movieIDsWithAvgRatingsRDD = movieIDsWithRatingsRDD.map(getCountsAndAverages)\n",
    "print 'movieIDsWithAvgRatingsRDD: %s\\n' % movieIDsWithAvgRatingsRDD.take(3)\n",
    "\n",
    "# To `movieIDsWithAvgRatingsRDD`, apply RDD transformations that use `moviesRDD` to get the movie\n",
    "# names for `movieIDsWithAvgRatingsRDD`, yielding tuples of the form\n",
    "# (average rating, movie name, number of ratings)\n",
    "movieNameWithAvgRatingsRDD = (moviesRDD\n",
    "                              .join(movieIDsWithAvgRatingsRDD).map(lambda x: (x[1][1][1],x[1][0],x[1][1][0])))\n",
    "print 'movieNameWithAvgRatingsRDD: %s\\n' % movieNameWithAvgRatingsRDD.take(3)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 23,
   "metadata": {
    "collapsed": false
   },
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "1 test passed.\n",
      "1 test passed.\n",
      "1 test passed.\n",
      "1 test passed.\n",
      "1 test passed.\n",
      "1 test passed.\n",
      "1 test passed.\n",
      "1 test passed.\n"
     ]
    }
   ],
   "source": [
    "# TEST Movies with Highest Average Ratings (1b)\n",
    "\n",
    "Test.assertEquals(movieIDsWithRatingsRDD.count(), 3615,\n",
    "                'incorrect movieIDsWithRatingsRDD.count() (expected 3615)')\n",
    "movieIDsWithRatingsTakeOrdered = movieIDsWithRatingsRDD.takeOrdered(3)\n",
    "Test.assertTrue(movieIDsWithRatingsTakeOrdered[0][0] == 1 and\n",
    "                len(list(movieIDsWithRatingsTakeOrdered[0][1])) == 993,\n",
    "                'incorrect count of ratings for movieIDsWithRatingsTakeOrdered[0] (expected 993)')\n",
    "Test.assertTrue(movieIDsWithRatingsTakeOrdered[1][0] == 2 and\n",
    "                len(list(movieIDsWithRatingsTakeOrdered[1][1])) == 332,\n",
    "                'incorrect count of ratings for movieIDsWithRatingsTakeOrdered[1] (expected 332)')\n",
    "Test.assertTrue(movieIDsWithRatingsTakeOrdered[2][0] == 3 and\n",
    "                len(list(movieIDsWithRatingsTakeOrdered[2][1])) == 299,\n",
    "                'incorrect count of ratings for movieIDsWithRatingsTakeOrdered[2] (expected 299)')\n",
    "\n",
    "Test.assertEquals(movieIDsWithAvgRatingsRDD.count(), 3615,\n",
    "                'incorrect movieIDsWithAvgRatingsRDD.count() (expected 3615)')\n",
    "Test.assertEquals(movieIDsWithAvgRatingsRDD.takeOrdered(3),\n",
    "                [(1, (993, 4.145015105740181)), (2, (332, 3.174698795180723)),\n",
    "                 (3, (299, 3.0468227424749164))],\n",
    "                'incorrect movieIDsWithAvgRatingsRDD.takeOrdered(3)')\n",
    "\n",
    "Test.assertEquals(movieNameWithAvgRatingsRDD.count(), 3615,\n",
    "                'incorrect movieNameWithAvgRatingsRDD.count() (expected 3615)')\n",
    "Test.assertEquals(movieNameWithAvgRatingsRDD.takeOrdered(3),\n",
    "                [(1.0, u'Autopsy (Macchie Solari) (1975)', 1), (1.0, u'Better Living (1998)', 1),\n",
    "                 (1.0, u'Big Squeeze, The (1996)', 3)],\n",
    "                 'incorrect movieNameWithAvgRatingsRDD.takeOrdered(3)')"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### **(1c) Movies with Highest Average Ratings and more than 500 reviews**\n",
    "#### Now that we have an RDD of the movies with highest averge ratings, we can use Spark to determine the 20 movies with highest average ratings and more than 500 reviews.\n",
    "#### Apply a single RDD transformation to `movieNameWithAvgRatingsRDD` to limit the results to movies with ratings from more than 500 people. We then use the `sortFunction()` helper function to sort by the average rating to get the movies in order of their rating (highest rating first). You will end up with an RDD of the form: `[(4.5349264705882355, u'Shawshank Redemption, The (1994)', 1088), (4.515798462852263, u\"Schindler's List (1993)\", 1171), (4.512893982808023, u'Godfather, The (1972)', 1047)]`"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 24,
   "metadata": {
    "collapsed": false
   },
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "Movies with highest ratings: [(4.5349264705882355, u'Shawshank Redemption, The (1994)', 1088), (4.515798462852263, u\"Schindler's List (1993)\", 1171), (4.512893982808023, u'Godfather, The (1972)', 1047), (4.510460251046025, u'Raiders of the Lost Ark (1981)', 1195), (4.505415162454874, u'Usual Suspects, The (1995)', 831), (4.457256461232604, u'Rear Window (1954)', 503), (4.45468509984639, u'Dr. Strangelove or: How I Learned to Stop Worrying and Love the Bomb (1963)', 651), (4.43953006219765, u'Star Wars: Episode IV - A New Hope (1977)', 1447), (4.4, u'Sixth Sense, The (1999)', 1110), (4.394285714285714, u'North by Northwest (1959)', 700), (4.379506641366224, u'Citizen Kane (1941)', 527), (4.375, u'Casablanca (1942)', 776), (4.363975155279503, u'Godfather: Part II, The (1974)', 805), (4.358816276202219, u\"One Flew Over the Cuckoo's Nest (1975)\", 811), (4.358173076923077, u'Silence of the Lambs, The (1991)', 1248), (4.335826477187734, u'Saving Private Ryan (1998)', 1337), (4.326241134751773, u'Chinatown (1974)', 564), (4.325383304940375, u'Life Is Beautiful (La Vita \\ufffd bella) (1997)', 587), (4.324110671936759, u'Monty Python and the Holy Grail (1974)', 759), (4.3096, u'Matrix, The (1999)', 1250)]\n"
     ]
    }
   ],
   "source": [
    "# TODO: Replace <FILL IN> with appropriate code\n",
    "\n",
    "# Apply an RDD transformation to `movieNameWithAvgRatingsRDD` to limit the results to movies with\n",
    "# ratings from more than 500 people. We then use the `sortFunction()` helper function to sort by the\n",
    "# average rating to get the movies in order of their rating (highest rating first)\n",
    "movieLimitedAndSortedByRatingRDD = (movieNameWithAvgRatingsRDD\n",
    "                                    .filter(lambda x: x[2]>500)\n",
    "                                    .sortBy(sortFunction, False))\n",
    "print 'Movies with highest ratings: %s' % movieLimitedAndSortedByRatingRDD.take(20)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 25,
   "metadata": {
    "collapsed": false
   },
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "1 test passed.\n",
      "1 test passed.\n"
     ]
    }
   ],
   "source": [
    "# TEST Movies with Highest Average Ratings and more than 500 Reviews (1c)\n",
    "\n",
    "Test.assertEquals(movieLimitedAndSortedByRatingRDD.count(), 194,\n",
    "                'incorrect movieLimitedAndSortedByRatingRDD.count()')\n",
    "Test.assertEquals(movieLimitedAndSortedByRatingRDD.take(20),\n",
    "              [(4.5349264705882355, u'Shawshank Redemption, The (1994)', 1088),\n",
    "               (4.515798462852263, u\"Schindler's List (1993)\", 1171),\n",
    "               (4.512893982808023, u'Godfather, The (1972)', 1047),\n",
    "               (4.510460251046025, u'Raiders of the Lost Ark (1981)', 1195),\n",
    "               (4.505415162454874, u'Usual Suspects, The (1995)', 831),\n",
    "               (4.457256461232604, u'Rear Window (1954)', 503),\n",
    "               (4.45468509984639, u'Dr. Strangelove or: How I Learned to Stop Worrying and Love the Bomb (1963)', 651),\n",
    "               (4.43953006219765, u'Star Wars: Episode IV - A New Hope (1977)', 1447),\n",
    "               (4.4, u'Sixth Sense, The (1999)', 1110), (4.394285714285714, u'North by Northwest (1959)', 700),\n",
    "               (4.379506641366224, u'Citizen Kane (1941)', 527), (4.375, u'Casablanca (1942)', 776),\n",
    "               (4.363975155279503, u'Godfather: Part II, The (1974)', 805),\n",
    "               (4.358816276202219, u\"One Flew Over the Cuckoo's Nest (1975)\", 811),\n",
    "               (4.358173076923077, u'Silence of the Lambs, The (1991)', 1248),\n",
    "               (4.335826477187734, u'Saving Private Ryan (1998)', 1337),\n",
    "               (4.326241134751773, u'Chinatown (1974)', 564),\n",
    "               (4.325383304940375, u'Life Is Beautiful (La Vita \\ufffd bella) (1997)', 587),\n",
    "               (4.324110671936759, u'Monty Python and the Holy Grail (1974)', 759),\n",
    "               (4.3096, u'Matrix, The (1999)', 1250)], 'incorrect sortedByRatingRDD.take(20)')"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### Using a threshold on the number of reviews is one way to improve the recommendations, but there are many other good ways to improve quality. For example, you could weight ratings by the number of ratings."
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## **Part 2: Collaborative Filtering**\n",
    "#### In this course, you have learned about many of the basic transformations and actions that Spark allows us to apply to distributed datasets.  Spark also exposes some higher level functionality; in particular, Machine Learning using a component of Spark called [MLlib][mllib].  In this part, you will learn how to use MLlib to make personalized movie recommendations using the movie data we have been analyzing.\n",
    "#### We are going to use a technique called [collaborative filtering][collab]. Collaborative filtering is a method of making automatic predictions (filtering) about the interests of a user by collecting preferences or taste information from many users (collaborating). The underlying assumption of the collaborative filtering approach is that if a person A has the same opinion as a person B on an issue, A is more likely to have B's opinion on a different issue x than to have the opinion on x of a person chosen randomly. You can read more about collaborative filtering [here][collab2].\n",
    "#### The image below (from [Wikipedia][collab]) shows an example of predicting of the user's rating using collaborative filtering. At first, people rate different items (like videos, images, games). After that, the system is making predictions about a user's rating for an item, which the user has not rated yet. These predictions are built upon the existing ratings of other users, who have similar ratings with the active user. For instance, in the image below the system has made a prediction, that the active user will not like the video.\n",
    "![collaborative filtering](https://courses.edx.org/c4x/BerkeleyX/CS100.1x/asset/Collaborative_filtering.gif)\n",
    "[mllib]: https://spark.apache.org/mllib/\n",
    "[collab]: https://en.wikipedia.org/?title=Collaborative_filtering\n",
    "[collab2]: http://recommender-systems.org/collaborative-filtering/"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### For movie recommendations, we start with a matrix whose entries are movie ratings by users (shown in red in the diagram below).  Each column represents a user (shown in green) and each row represents a particular movie (shown in blue).\n",
    "#### Since not all users have rated all movies, we do not know all of the entries in this matrix, which is precisely why we need collaborative filtering.  For each user, we have ratings for only a subset of the movies.  With collaborative filtering, the idea is to approximate the ratings matrix by factorizing it as the product of two matrices: one that describes properties of each user (shown in green), and one that describes properties of each movie (shown in blue).\n",
    "![factorization](http://spark-mooc.github.io/web-assets/images/matrix_factorization.png)\n",
    "#### We want to select these two matrices such that the error for the users/movie pairs where we know the correct ratings is minimized.  The [Alternating Least Squares][als] algorithm does this by first randomly filling the users matrix with values and then optimizing the value of the movies such that the error is minimized.  Then, it holds the movies matrix constrant and optimizes the value of the user's matrix.  This alternation between which matrix to optimize is the reason for the \"alternating\" in the name.\n",
    "#### This optimization is what's being shown on the right in the image above.  Given a fixed set of user factors (i.e., values in the users matrix), we use the known ratings to find the best values for the movie factors using the optimization written at the bottom of the figure.  Then we \"alternate\" and pick the best user factors given fixed movie factors.\n",
    "#### For a simple example of what the users and movies matrices might look like, check out the [videos from Lecture 8][videos] or the [slides from Lecture 8][slides]\n",
    "[videos]: https://courses.edx.org/courses/BerkeleyX/CS100.1x/1T2015/courseware/00eb8b17939b4889a41a6d8d2f35db83/3bd3bba368be4102b40780550d3d8da6/\n",
    "[slides]: https://courses.edx.org/c4x/BerkeleyX/CS100.1x/asset/Week4Lec8.pdf\n",
    "[als]: https://en.wikiversity.org/wiki/Least-Squares_Method"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### **(2a) Creating a Training Set**\n",
    "#### Before we jump into using machine learning, we need to break up the `ratingsRDD` dataset into three pieces:\n",
    "* #### A training set (RDD), which we will use to train models\n",
    "* #### A validation set (RDD), which we will use to choose the best model\n",
    "* #### A test set (RDD), which we will use for our experiments\n",
    "#### To randomly split the dataset into the multiple groups, we can use the pySpark [randomSplit()](https://spark.apache.org/docs/latest/api/python/pyspark.html#pyspark.RDD.randomSplit) transformation. `randomSplit()` takes a set of splits and and seed and returns multiple RDDs."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 51,
   "metadata": {
    "collapsed": false
   },
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "Training: 292716, validation: 96902, test: 98032\n",
      "\n",
      "[(1, 914, 3.0), (1, 2355, 5.0), (1, 595, 5.0)]\n",
      "[(1, 1287, 5.0), (1, 594, 4.0), (1, 1270, 5.0)]\n",
      "[(1, 1193, 5.0), (1, 2398, 4.0), (1, 1035, 5.0)]\n"
     ]
    }
   ],
   "source": [
    "trainingRDD, validationRDD, testRDD = ratingsRDD.randomSplit([6, 2, 2], seed=0L)\n",
    "\n",
    "print 'Training: %s, validation: %s, test: %s\\n' % (trainingRDD.count(),\n",
    "                                                    validationRDD.count(),\n",
    "                                                    testRDD.count())\n",
    "print trainingRDD.take(3)\n",
    "print validationRDD.take(3)\n",
    "print testRDD.take(3)\n",
    "\n",
    "assert trainingRDD.count() == 292716\n",
    "assert validationRDD.count() == 96902\n",
    "assert testRDD.count() == 98032\n",
    "\n",
    "assert trainingRDD.filter(lambda t: t == (1, 914, 3.0)).count() == 1\n",
    "assert trainingRDD.filter(lambda t: t == (1, 2355, 5.0)).count() == 1\n",
    "assert trainingRDD.filter(lambda t: t == (1, 595, 5.0)).count() == 1\n",
    "\n",
    "assert validationRDD.filter(lambda t: t == (1, 1287, 5.0)).count() == 1\n",
    "assert validationRDD.filter(lambda t: t == (1, 594, 4.0)).count() == 1\n",
    "assert validationRDD.filter(lambda t: t == (1, 1270, 5.0)).count() == 1\n",
    "\n",
    "assert testRDD.filter(lambda t: t == (1, 1193, 5.0)).count() == 1\n",
    "assert testRDD.filter(lambda t: t == (1, 2398, 4.0)).count() == 1\n",
    "assert testRDD.filter(lambda t: t == (1, 1035, 5.0)).count() == 1"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### After splitting the dataset, your training set has about 293,000 entries and the validation and test sets each have about 97,000 entries (the exact number of entries in each dataset varies slightly due to the random nature of the `randomSplit()` transformation."
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### **(2b) Root Mean Square Error (RMSE)**\n",
    "#### In the next part, you will generate a few different models, and will need a way to decide which model is best. We will use the [Root Mean Square Error](https://en.wikipedia.org/wiki/Root-mean-square_deviation) (RMSE) or Root Mean Square Deviation (RMSD) to compute the error of each model.  RMSE is a frequently used measure of the differences between values (sample and population values) predicted by a model or an estimator and the values actually observed. The RMSD represents the sample standard deviation of the differences between predicted values and observed values. These individual differences are called residuals when the calculations are performed over the data sample that was used for estimation, and are called prediction errors when computed out-of-sample. The RMSE serves to aggregate the magnitudes of the errors in predictions for various times into a single measure of predictive power. RMSE is a good measure of accuracy, but only to compare forecasting errors of different models for a particular variable and not between variables, as it is scale-dependent.\n",
    "####  The RMSE is the square root of the average value of the square of `(actual rating - predicted rating)` for all users and movies for which we have the actual rating. Versions of Spark MLlib beginning with Spark 1.4 include a [RegressionMetrics](https://spark.apache.org/docs/latest/api/python/pyspark.mllib.html#pyspark.mllib.evaluation.RegressionMetrics) modiule that can be used to compute the RMSE. However, since we are using Spark 1.3.1, we will write our own function.\n",
    "#### Write a function to compute the sum of squared error given `predictedRDD` and `actualRDD` RDDs. Both RDDs consist of tuples of the form (UserID, MovieID, Rating)\n",
    "#### Given two ratings RDDs, *x* and *y* of size *n*, we define RSME as follows: $ RMSE = \\sqrt{\\frac{\\sum_{i = 1}^{n} (x_i - y_i)^2}{n}}$\n",
    "#### To calculate RSME, the steps you should perform are:\n",
    "* #### Transform `predictedRDD` into the tuples of the form ((UserID, MovieID), Rating). For example, tuples like `[((1, 1), 5), ((1, 2), 3), ((1, 3), 4), ((2, 1), 3), ((2, 2), 2), ((2, 3), 4)]`. You can perform this step with a single Spark transformation.\n",
    "* #### Transform `actualRDD` into the tuples of the form ((UserID, MovieID), Rating). For example, tuples like `[((1, 2), 3), ((1, 3), 5), ((2, 1), 5), ((2, 2), 1)]`. You can perform this step with a single Spark transformation.\n",
    "* #### Using only RDD transformations (you only need to perform two transformations), compute the squared error for each *matching* entry (i.e., the same (UserID, MovieID) in each RDD) in the reformatted RDDs - do *not* use `collect()` to perform this step. Note that not every (UserID, MovieID) pair will appear in both RDDs - if a pair does not appear in both RDDs, then it does not contribute to the RMSE. You will end up with an RDD with entries of the form $ (x_i - y_i)^2$ You might want to check out Python's [math](https://docs.python.org/2/library/math.html) module to see how to compute these values\n",
    "* #### Using an RDD action (but **not** `collect()`), compute the total squared error: $ SE = \\sum_{i = 1}^{n} (x_i - y_i)^2 $\n",
    "* #### Compute *n* by using an RDD action (but **not** `collect()`), to count the number of pairs for which you computed the total squared error\n",
    "* #### Using the total squared error and the number of pairs, compute the RSME. Make sure you compute this value as a [float](https://docs.python.org/2/library/stdtypes.html#numeric-types-int-float-long-complex).\n",
    "#### Note: Your solution must only use transformations and actions on RDDs. Do _not_ call `collect()` on either RDD."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 30,
   "metadata": {
    "collapsed": false
   },
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "Error for test dataset (should be 1.22474487139): 1.22474487139\n",
      "Error for test dataset2 (should be 3.16227766017): 3.16227766017\n",
      "Error for testActual dataset (should be 0.0): 0.0\n"
     ]
    }
   ],
   "source": [
    "# TODO: Replace <FILL IN> with appropriate code\n",
    "import math\n",
    "\n",
    "def computeError(predictedRDD, actualRDD):\n",
    "    \"\"\" Compute the root mean squared error between predicted and actual\n",
    "    Args:\n",
    "        predictedRDD: predicted ratings for each movie and each user where each entry is in the form\n",
    "                      (UserID, MovieID, Rating)\n",
    "        actualRDD: actual ratings where each entry is in the form (UserID, MovieID, Rating)\n",
    "    Returns:\n",
    "        RSME (float): computed RSME value\n",
    "    \"\"\"\n",
    "    # Transform predictedRDD into the tuples of the form ((UserID, MovieID), Rating)\n",
    "    predictedReformattedRDD = predictedRDD.map(lambda x : ((x[0],x[1]),x[2]))\n",
    "\n",
    "    # Transform actualRDD into the tuples of the form ((UserID, MovieID), Rating)\n",
    "    actualReformattedRDD = actualRDD.map(lambda x : ((x[0],x[1]),x[2]))\n",
    "\n",
    "    # Compute the squared error for each matching entry (i.e., the same (User ID, Movie ID) in each\n",
    "    # RDD) in the reformatted RDDs using RDD transformtions - do not use collect()\n",
    "    squaredErrorsRDD = predictedReformattedRDD.join(actualReformattedRDD).map(lambda x:(x[1][0]-x[1][1])**2)\n",
    "\n",
    "    # Compute the total squared error - do not use collect()\n",
    "    totalError = squaredErrorsRDD.reduce(lambda x,y: x+y)\n",
    "\n",
    "    # Count the number of entries for which you computed the total squared error\n",
    "    numRatings = squaredErrorsRDD.count()\n",
    "\n",
    "    # Using the total squared error and the number of entries, compute the RSME\n",
    "    return math.sqrt(totalError/float(numRatings))\n",
    "\n",
    "\n",
    "# sc.parallelize turns a Python list into a Spark RDD.\n",
    "testPredicted = sc.parallelize([\n",
    "    (1, 1, 5),\n",
    "    (1, 2, 3),\n",
    "    (1, 3, 4),\n",
    "    (2, 1, 3),\n",
    "    (2, 2, 2),\n",
    "    (2, 3, 4)])\n",
    "testActual = sc.parallelize([\n",
    "     (1, 2, 3),\n",
    "     (1, 3, 5),\n",
    "     (2, 1, 5),\n",
    "     (2, 2, 1)])\n",
    "testPredicted2 = sc.parallelize([\n",
    "     (2, 2, 5),\n",
    "     (1, 2, 5)])\n",
    "testError = computeError(testPredicted, testActual)\n",
    "print 'Error for test dataset (should be 1.22474487139): %s' % testError\n",
    "\n",
    "testError2 = computeError(testPredicted2, testActual)\n",
    "print 'Error for test dataset2 (should be 3.16227766017): %s' % testError2\n",
    "\n",
    "testError3 = computeError(testActual, testActual)\n",
    "print 'Error for testActual dataset (should be 0.0): %s' % testError3"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 32,
   "metadata": {
    "collapsed": false
   },
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "1 test passed.\n",
      "1 test passed.\n",
      "1 test passed.\n"
     ]
    }
   ],
   "source": [
    "# TEST Root Mean Square Error (2b)\n",
    "Test.assertTrue(abs(testError - 1.22474487139) < 0.00000001,\n",
    "                'incorrect testError (expected 1.22474487139)')\n",
    "Test.assertTrue(abs(testError2 - 3.16227766017) < 0.00000001,\n",
    "                'incorrect testError2 result (expected 3.16227766017)')\n",
    "Test.assertTrue(abs(testError3 - 0.0) < 0.00000001,\n",
    "                'incorrect testActual result (expected 0.0)')"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### **(2c) Using ALS.train()**\n",
    "#### In this part, we will use the MLlib implementation of Alternating Least Squares, [ALS.train()](https://spark.apache.org/docs/latest/api/python/pyspark.mllib.html#pyspark.mllib.recommendation.ALS). ALS takes a training dataset (RDD) and several parameters that control the model creation process. To determine the best values for the parameters, we will use ALS to train several models, and then we will select the best model and use the parameters from that model in the rest of this lab exercise.\n",
    "#### The process we will use for determining the best model is as follows:\n",
    "* #### Pick a set of model parameters. The most important parameter to `ALS.train()` is the *rank*, which is the number of rows in the Users matrix (green in the diagram above) or the number of columns in the Movies matrix (blue in the diagram above). (In general, a lower rank will mean higher error on the training dataset, but a high rank may lead to [overfitting](https://en.wikipedia.org/wiki/Overfitting).)  We will train models with ranks of 4, 8, and 12 using the `trainingRDD` dataset.\n",
    "* #### Create a model using `ALS.train(trainingRDD, rank, seed=seed, iterations=iterations, lambda_=regularizationParameter)` with three parameters: an RDD consisting of tuples of the form (UserID, MovieID, rating) used to train the model, an integer rank (4, 8, or 12), a number of iterations to execute (we will use 5 for the `iterations` parameter), and a regularization coefficient (we will use 0.1 for the `regularizationParameter`).\n",
    "* #### For the prediction step, create an input RDD, `validationForPredictRDD`, consisting of (UserID, MovieID) pairs that you extract from `validationRDD`. You will end up with an RDD of the form: `[(1, 1287), (1, 594), (1, 1270)]`\n",
    "* #### Using the model and `validationForPredictRDD`, we can predict rating values by calling [model.predictAll()](https://spark.apache.org/docs/latest/api/python/pyspark.mllib.html#pyspark.mllib.recommendation.MatrixFactorizationModel.predictAll) with the `validationForPredictRDD` dataset, where `model` is the model we generated with ALS.train().  `predictAll` accepts an RDD with each entry in the format (userID, movieID) and outputs an RDD with each entry in the format (userID, movieID, rating).\n",
    "* #### Evaluate the quality of the model by using the `computeError()` function you wrote in part (2b) to compute the error between the predicted ratings and the actual ratings in `validationRDD`.\n",
    "####  Which rank produces the best model, based on the RMSE with the `validationRDD` dataset?\n",
    "#### Note: It is likely that this operation will take a noticeable amount of time (around a minute in our VM); you can observe its progress on the [Spark Web UI](http://localhost:4040). Probably most of the time will be spent running your `computeError()` function, since, unlike the Spark ALS implementation (and the Spark 1.4 [RegressionMetrics](https://spark.apache.org/docs/latest/api/python/pyspark.mllib.html#pyspark.mllib.evaluation.RegressionMetrics) module), this does not use a fast linear algebra library and needs to run some Python code for all 100k entries."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 33,
   "metadata": {
    "collapsed": false
   },
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "For rank 4 the RMSE is 0.901241353926\n",
      "For rank 8 the RMSE is 0.887031659461\n",
      "For rank 12 the RMSE is 0.892111420368\n",
      "The best model was trained with rank 8\n"
     ]
    }
   ],
   "source": [
    "# TODO: Replace <FILL IN> with appropriate code\n",
    "from pyspark.mllib.recommendation import ALS\n",
    "\n",
    "validationForPredictRDD = validationRDD.map(lambda x : (x[0],x[1]))\n",
    "\n",
    "seed = 5L\n",
    "iterations = 5\n",
    "regularizationParameter = 0.1\n",
    "ranks = [4, 8, 12]\n",
    "errors = [0, 0, 0]\n",
    "err = 0\n",
    "tolerance = 0.02\n",
    "\n",
    "minError = float('inf')\n",
    "bestRank = -1\n",
    "bestIteration = -1\n",
    "for rank in ranks:\n",
    "    model = ALS.train(trainingRDD, rank, seed=seed, iterations=iterations,\n",
    "                      lambda_=regularizationParameter)\n",
    "    predictedRatingsRDD = model.predictAll(validationForPredictRDD)\n",
    "    error = computeError(predictedRatingsRDD, validationRDD)\n",
    "    errors[err] = error\n",
    "    err += 1\n",
    "    print 'For rank %s the RMSE is %s' % (rank, error)\n",
    "    if error < minError:\n",
    "        minError = error\n",
    "        bestRank = rank\n",
    "\n",
    "print 'The best model was trained with rank %s' % bestRank"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 34,
   "metadata": {
    "collapsed": false
   },
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "1 test passed.\n",
      "1 test passed.\n",
      "1 test passed.\n",
      "1 test passed.\n",
      "1 test passed.\n",
      "1 test passed.\n"
     ]
    }
   ],
   "source": [
    "# TEST Using ALS.train (2c)\n",
    "Test.assertEquals(trainingRDD.getNumPartitions(), 2,\n",
    "                  'incorrect number of partitions for trainingRDD (expected 2)')\n",
    "Test.assertEquals(validationForPredictRDD.count(), 96902,\n",
    "                  'incorrect size for validationForPredictRDD (expected 96902)')\n",
    "Test.assertEquals(validationForPredictRDD.filter(lambda t: t == (1, 1907)).count(), 1,\n",
    "                  'incorrect content for validationForPredictRDD')\n",
    "Test.assertTrue(abs(errors[0] - 0.883710109497) < tolerance, 'incorrect errors[0]')\n",
    "Test.assertTrue(abs(errors[1] - 0.878486305621) < tolerance, 'incorrect errors[1]')\n",
    "Test.assertTrue(abs(errors[2] - 0.876832795659) < tolerance, 'incorrect errors[2]')"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### **(2d) Testing Your Model**\n",
    "#### So far, we used the `trainingRDD` and `validationRDD` datasets to select the best model.  Since we used these two datasets to determine what model is best, we cannot use them to test how good the model is - otherwise we would be very vulnerable to [overfitting](https://en.wikipedia.org/wiki/Overfitting).  To decide how good our model is, we need to use the `testRDD` dataset.  We will use the `bestRank` you determined in part (2c) to create a model for predicting the ratings for the test dataset and then we will compute the RMSE.\n",
    "#### The steps you should perform are:\n",
    "* #### Train a model, using the `trainingRDD`, `bestRank` from part (2c), and the parameters you used in in part (2c): `seed=seed`, `iterations=iterations`, and `lambda_=regularizationParameter` - make sure you include **all** of the parameters.\n",
    "* #### For the prediction step, create an input RDD, `testForPredictingRDD`, consisting of (UserID, MovieID) pairs that you extract from `testRDD`. You will end up with an RDD of the form: `[(1, 1287), (1, 594), (1, 1270)]`\n",
    "* #### Use [myModel.predictAll()](https://spark.apache.org/docs/latest/api/python/pyspark.mllib.html#pyspark.mllib.recommendation.MatrixFactorizationModel.predictAll) to predict rating values for the test dataset.\n",
    "* #### For validation, use the `testRDD`and your `computeError` function to compute the RMSE between `testRDD` and the `predictedTestRDD` from the model.\n",
    "* #### Evaluate the quality of the model by using the `computeError()` function you wrote in part (2b) to compute the error between the predicted ratings and the actual ratings in `testRDD`."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 35,
   "metadata": {
    "collapsed": false
   },
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "The model had a RMSE on the test set of 0.8891071528\n"
     ]
    }
   ],
   "source": [
    "# TODO: Replace <FILL IN> with appropriate code\n",
    "myModel = ALS.train(trainingRDD, bestRank, seed=seed, iterations=iterations,\n",
    "                      lambda_=regularizationParameter)\n",
    "testForPredictingRDD = testRDD.map(lambda x : (x[0],x[1]))\n",
    "predictedTestRDD = myModel.predictAll(testForPredictingRDD)\n",
    "testRMSE = computeError(testRDD, predictedTestRDD)\n",
    "\n",
    "print 'The model had a RMSE on the test set of %s' % testRMSE"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 36,
   "metadata": {
    "collapsed": false
   },
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "1 test passed.\n"
     ]
    }
   ],
   "source": [
    "# TEST Testing Your Model (2d)\n",
    "Test.assertTrue(abs(testRMSE - 0.87809838344) < tolerance, 'incorrect testRMSE')"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### **(2e) Comparing Your Model**\n",
    "#### Looking at the RMSE for the results predicted by the model versus the values in the test set is one way to evalute the quality of our model. Another way to evaluate the model is to evaluate the error from a test set where every rating is the average rating for the training set.\n",
    "#### The steps you should perform are:\n",
    "* #### Use the `trainingRDD` to compute the average rating across all movies in that training dataset.\n",
    "* #### Use the average rating that you just determined and the `testRDD` to create an RDD with entries of the form (userID, movieID, average rating).\n",
    "* #### Use your `computeError` function to compute the RMSE between the `testRDD` validation RDD that you just created and the `testForAvgRDD`."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 38,
   "metadata": {
    "collapsed": false
   },
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "The average rating for movies in the training set is 3.57409571052\n",
      "The RMSE on the average set is 1.12036693569\n"
     ]
    }
   ],
   "source": [
    "# TODO: Replace <FILL IN> with appropriate code\n",
    "\n",
    "trainingAvgRating = trainingRDD.map(lambda x : x[2]).reduce(lambda x,y :x+y)/trainingRDD.count()\n",
    "print 'The average rating for movies in the training set is %s' % trainingAvgRating\n",
    "\n",
    "testForAvgRDD = testRDD.map(lambda x : (x[0],x[1],trainingAvgRating))\n",
    "testAvgRMSE = computeError(testRDD, testForAvgRDD)\n",
    "print 'The RMSE on the average set is %s' % testAvgRMSE"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 39,
   "metadata": {
    "collapsed": false
   },
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "1 test passed.\n",
      "1 test passed.\n"
     ]
    }
   ],
   "source": [
    "# TEST Comparing Your Model (2e)\n",
    "Test.assertTrue(abs(trainingAvgRating - 3.57409571052) < 0.000001,\n",
    "                'incorrect trainingAvgRating (expected 3.57409571052)')\n",
    "Test.assertTrue(abs(testAvgRMSE - 1.12036693569) < 0.000001,\n",
    "                'incorrect testAvgRMSE (expected 1.12036693569)')"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### You now have code to predict how users will rate movies!"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## **Part 3: Predictions for Yourself**\n",
    "#### The ultimate goal of this lab exercise is to predict what movies to recommend to yourself.  In order to do that, you will first need to add ratings for yourself to the `ratingsRDD` dataset."
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### **(3a) Your Movie Ratings**\n",
    "#### To help you provide ratings for yourself, we have included the following code to list the names and movie IDs of the 50 highest-rated movies from `movieLimitedAndSortedByRatingRDD` which we created in part 1 the lab."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 40,
   "metadata": {
    "collapsed": false
   },
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "Most rated movies:\n",
      "(average rating, movie name, number of reviews)\n",
      "(4.5349264705882355, u'Shawshank Redemption, The (1994)', 1088)\n",
      "(4.515798462852263, u\"Schindler's List (1993)\", 1171)\n",
      "(4.512893982808023, u'Godfather, The (1972)', 1047)\n",
      "(4.510460251046025, u'Raiders of the Lost Ark (1981)', 1195)\n",
      "(4.505415162454874, u'Usual Suspects, The (1995)', 831)\n",
      "(4.457256461232604, u'Rear Window (1954)', 503)\n",
      "(4.45468509984639, u'Dr. Strangelove or: How I Learned to Stop Worrying and Love the Bomb (1963)', 651)\n",
      "(4.43953006219765, u'Star Wars: Episode IV - A New Hope (1977)', 1447)\n",
      "(4.4, u'Sixth Sense, The (1999)', 1110)\n",
      "(4.394285714285714, u'North by Northwest (1959)', 700)\n",
      "(4.379506641366224, u'Citizen Kane (1941)', 527)\n",
      "(4.375, u'Casablanca (1942)', 776)\n",
      "(4.363975155279503, u'Godfather: Part II, The (1974)', 805)\n",
      "(4.358816276202219, u\"One Flew Over the Cuckoo's Nest (1975)\", 811)\n",
      "(4.358173076923077, u'Silence of the Lambs, The (1991)', 1248)\n",
      "(4.335826477187734, u'Saving Private Ryan (1998)', 1337)\n",
      "(4.326241134751773, u'Chinatown (1974)', 564)\n",
      "(4.325383304940375, u'Life Is Beautiful (La Vita \\ufffd bella) (1997)', 587)\n",
      "(4.324110671936759, u'Monty Python and the Holy Grail (1974)', 759)\n",
      "(4.3096, u'Matrix, The (1999)', 1250)\n",
      "(4.309457579972183, u'Star Wars: Episode V - The Empire Strikes Back (1980)', 1438)\n",
      "(4.30379746835443, u'Young Frankenstein (1974)', 553)\n",
      "(4.301346801346801, u'Psycho (1960)', 594)\n",
      "(4.296438883541867, u'Pulp Fiction (1994)', 1039)\n",
      "(4.286535303776683, u'Fargo (1996)', 1218)\n",
      "(4.282367447595561, u'GoodFellas (1990)', 811)\n",
      "(4.27943661971831, u'American Beauty (1999)', 1775)\n",
      "(4.268053855569155, u'Wizard of Oz, The (1939)', 817)\n",
      "(4.267774699907664, u'Princess Bride, The (1987)', 1083)\n",
      "(4.253333333333333, u'Graduate, The (1967)', 600)\n",
      "(4.236263736263736, u'Run Lola Run (Lola rennt) (1998)', 546)\n",
      "(4.233807266982622, u'Amadeus (1984)', 633)\n",
      "(4.232558139534884, u'Toy Story 2 (1999)', 860)\n",
      "(4.232558139534884, u'This Is Spinal Tap (1984)', 516)\n",
      "(4.228494623655914, u'Almost Famous (2000)', 744)\n",
      "(4.2250755287009065, u'Christmas Story, A (1983)', 662)\n",
      "(4.216757741347905, u'Glory (1989)', 549)\n",
      "(4.213358070500927, u'Apocalypse Now (1979)', 539)\n",
      "(4.20992028343667, u'L.A. Confidential (1997)', 1129)\n",
      "(4.204733727810651, u'Blade Runner (1982)', 845)\n",
      "(4.1886120996441285, u'Sling Blade (1996)', 562)\n",
      "(4.184615384615385, u'Braveheart (1995)', 1300)\n",
      "(4.184168012924071, u'Butch Cassidy and the Sundance Kid (1969)', 619)\n",
      "(4.182509505703422, u'Good Will Hunting (1997)', 789)\n",
      "(4.166969147005445, u'Taxi Driver (1976)', 551)\n",
      "(4.162767039674466, u'Terminator, The (1984)', 983)\n",
      "(4.157545605306799, u'Reservoir Dogs (1992)', 603)\n",
      "(4.153333333333333, u'Jaws (1975)', 750)\n",
      "(4.149840595111583, u'Alien (1979)', 941)\n",
      "(4.145015105740181, u'Toy Story (1995)', 993)\n"
     ]
    }
   ],
   "source": [
    "print 'Most rated movies:'\n",
    "print '(average rating, movie name, number of reviews)'\n",
    "for ratingsTuple in movieLimitedAndSortedByRatingRDD.take(50):\n",
    "    print ratingsTuple"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### The user ID 0 is unassigned, so we will use it for your ratings. We set the variable `myUserID` to 0 for you. Next, create a new RDD `myRatingsRDD` with your ratings for at least 10 movie ratings. Each entry should be formatted as `(myUserID, movieID, rating)` (i.e., each entry should be formatted in the same way as `trainingRDD`).  As in the original dataset, ratings should be between 1 and 5 (inclusive). If you have not seen at least 10 of these movies, you can increase the parameter passed to `take()` in the above cell until there are 10 movies that you have seen (or you can also guess what your rating would be for movies you have not seen)."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 42,
   "metadata": {
    "collapsed": false
   },
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "My movie ratings: [(0, 914, 3.0), (0, 2355, 5.0), (0, 595, 5.0), (0, 2321, 3.0), (0, 1545, 4.0), (0, 2294, 4.0), (0, 1566, 4.0), (0, 1, 5.0), (0, 260, 4.0), (0, 2028, 5.0)]\n"
     ]
    }
   ],
   "source": [
    "# TODO: Replace <FILL IN> with appropriate code\n",
    "myUserID = 0\n",
    "\n",
    "# Note that the movie IDs are the *last* number on each line. A common error was to use the number of ratings as the movie ID.\n",
    "myRatedMovies = [\n",
    " (0, 914, 3.0), (0, 2355, 5.0), (0, 595, 5.0), (0, 2321, 3.0), (0, 1545, 4.0), (0, 2294, 4.0), (0, 1566, 4.0), (0, 1, 5.0), (0, 260, 4.0), (0, 2028, 5.0)\n",
    "    ]\n",
    "myRatingsRDD = sc.parallelize(myRatedMovies)\n",
    "print 'My movie ratings: %s' % myRatingsRDD.take(10)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### **(3b) Add Your Movies to Training Dataset**\n",
    "#### Now that you have ratings for yourself, you need to add your ratings to the `training` dataset so that the model you train will incorporate your preferences.  Spark's [union()](http://spark.apache.org/docs/latest/api/python/pyspark.rdd.RDD-class.html#union) transformation combines two RDDs; use `union()` to create a new training dataset that includes your ratings and the data in the original training dataset."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 44,
   "metadata": {
    "collapsed": false
   },
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "The training dataset now has 10 more entries than the original training dataset\n"
     ]
    }
   ],
   "source": [
    "# TODO: Replace <FILL IN> with appropriate code\n",
    "trainingWithMyRatingsRDD = trainingRDD.union(myRatingsRDD)\n",
    "\n",
    "print ('The training dataset now has %s more entries than the original training dataset' %\n",
    "       (trainingWithMyRatingsRDD.count() - trainingRDD.count()))\n",
    "assert (trainingWithMyRatingsRDD.count() - trainingRDD.count()) == myRatingsRDD.count()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### **(3c) Train a Model with Your Ratings**\n",
    "#### Now, train a model with your ratings added and the parameters you used in in part (2c): `bestRank`, `seed=seed`, `iterations=iterations`, and `lambda_=regularizationParameter` - make sure you include **all** of the parameters."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 45,
   "metadata": {
    "collapsed": false
   },
   "outputs": [],
   "source": [
    "# TODO: Replace <FILL IN> with appropriate code\n",
    "myRatingsModel = ALS.train(trainingWithMyRatingsRDD, bestRank,  seed=seed, iterations=iterations, lambda_=regularizationParameter)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### **(3d) Check RMSE for the New Model with Your Ratings**\n",
    "#### Compute the RMSE for this new model on the test set.\n",
    "* #### For the prediction step, we reuse `testForPredictingRDD`, consisting of (UserID, MovieID) pairs that you extracted from `testRDD`. The RDD has the form: `[(1, 1287), (1, 594), (1, 1270)]`\n",
    "* #### Use `myRatingsModel.predictAll()` to predict rating values for the `testForPredictingRDD` test dataset, set this as `predictedTestMyRatingsRDD`\n",
    "* #### For validation, use the `testRDD`and your `computeError` function to compute the RMSE between `testRDD` and the `predictedTestMyRatingsRDD` from the model."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 47,
   "metadata": {
    "collapsed": false
   },
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "The model had a RMSE on the test set of 0.893244000952\n"
     ]
    }
   ],
   "source": [
    "# TODO: Replace <FILL IN> with appropriate code\n",
    "predictedTestMyRatingsRDD = myRatingsModel.predictAll(testForPredictingRDD) \n",
    "testRMSEMyRatings = computeError(testRDD, predictedTestMyRatingsRDD)\n",
    "print 'The model had a RMSE on the test set of %s' % testRMSEMyRatings"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### **(3e) Predict Your Ratings**\n",
    "#### So far, we have only used the `predictAll` method to compute the error of the model.  Here, use the `predictAll` to predict what ratings you would give to the movies that you did not already provide ratings for.\n",
    "#### The steps you should perform are:\n",
    "* #### Use the Python list `myRatedMovies` to transform the `moviesRDD` into an RDD with entries that are pairs of the form (myUserID, Movie ID) and that does not contain any movies that you have rated. This transformation will yield an RDD of the form: `[(0, 1), (0, 2), (0, 3), (0, 4)]`. Note that you can do this step with one RDD transformation.\n",
    "* #### For the prediction step, use the input RDD, `myUnratedMoviesRDD`, with myRatingsModel.predictAll() to predict your ratings for the movies."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 48,
   "metadata": {
    "collapsed": false
   },
   "outputs": [],
   "source": [
    "# TODO: Replace <FILL IN> with appropriate code\n",
    "\n",
    "# Use the Python list myRatedMovies to transform the moviesRDD into an RDD with entries that are pairs of the form (myUserID, Movie ID) and that does not contain any movies that you have rated.\n",
    "myUnratedMoviesRDD = (moviesRDD\n",
    "                      .map(lambda x:(myUserID,x[0])))\n",
    "\n",
    "# Use the input RDD, myUnratedMoviesRDD, with myRatingsModel.predictAll() to predict your ratings for the movies\n",
    "predictedRatingsRDD = myRatingsModel.predictAll(myUnratedMoviesRDD)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### **(3f) Predict Your Ratings**\n",
    "#### We have our predicted ratings. Now we can print out the 25 movies with the highest predicted ratings.\n",
    "#### The steps you should perform are:\n",
    "* #### From Parts (1b) and (1c), we know that we should look at movies with a reasonable number of reviews (e.g., more than 75 reviews). You can experiment with a lower threshold, but fewer ratings for a movie may yield higher prediction errors. Transform `movieIDsWithAvgRatingsRDD` from Part (1b), which has the form (MovieID, (number of ratings, average rating)), into an RDD of the form (MovieID, number of ratings): `[(2, 332), (4, 71), (6, 442)]`\n",
    "* #### We want to see movie names, instead of movie IDs. Transform `predictedRatingsRDD` into an RDD with entries that are pairs of the form (Movie ID, Predicted Rating): `[(3456, -0.5501005376936687), (1080, 1.5885892024487962), (320, -3.7952255522487865)]`\n",
    "* #### Use RDD transformations with `predictedRDD` and `movieCountsRDD` to yield an RDD with tuples of the form (Movie ID, (Predicted Rating, number of ratings)): `[(2050, (0.6694097486155939, 44)), (10, (5.29762541533513, 418)), (2060, (0.5055259373841172, 97))]`\n",
    "* #### Use RDD transformations with `predictedWithCountsRDD` and `moviesRDD` to yield an RDD with tuples of the form (Predicted Rating, Movie Name, number of ratings), _for movies with more than 75 ratings._ For example: `[(7.983121900375243, u'Under Siege (1992)'), (7.9769201864261285, u'Fifth Element, The (1997)')]`"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 50,
   "metadata": {
    "collapsed": false
   },
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "My highest rated movies as predicted (for movies with more than 75 reviews):\n",
      "(4.7858929265779695, u'Shawshank Redemption, The (1994)', 1088)\n",
      "(4.722670107247972, u\"Schindler's List (1993)\", 1171)\n",
      "(4.641649268086726, u'Life Is Beautiful (La Vita \\ufffd bella) (1997)', 587)\n",
      "(4.637534343884257, u'Godfather, The (1972)', 1047)\n",
      "(4.587452371500987, u'Christmas Story, A (1983)', 662)\n",
      "(4.57864977684544, u'Sixth Sense, The (1999)', 1110)\n",
      "(4.574314180061562, u'Silence of the Lambs, The (1991)', 1248)\n",
      "(4.558566788175257, u'American Beauty (1999)', 1775)\n",
      "(4.541045675769093, u'Usual Suspects, The (1995)', 831)\n",
      "(4.516384207360893, u'Saving Private Ryan (1998)', 1337)\n",
      "(4.5078492513205815, u'Maltese Falcon, The (1941)', 476)\n",
      "(4.505512289154003, u'Glory (1989)', 549)\n",
      "(4.5023888466567605, u'Bridge on the River Kwai, The (1957)', 481)\n",
      "(4.497171968333099, u'Toy Story (1995)', 993)\n",
      "(4.49502683167134, u'Close Shave, A (1995)', 318)\n",
      "(4.495021028086445, u'Raiders of the Lost Ark (1981)', 1195)\n",
      "(4.466365738687774, u'Wrong Trousers, The (1993)', 425)\n",
      "(4.4644983467996555, u'Jean de Florette (1986)', 93)\n",
      "(4.464386436691404, u'Toy Story 2 (1999)', 860)\n",
      "(4.455786004815446, u'Good Will Hunting (1997)', 789)\n"
     ]
    }
   ],
   "source": [
    "# TODO: Replace <FILL IN> with appropriate code\n",
    "\n",
    "# Transform movieIDsWithAvgRatingsRDD from part (1b), which has the form (MovieID, (number of ratings, average rating)), into and RDD of the form (MovieID, number of ratings)\n",
    "movieCountsRDD = movieIDsWithAvgRatingsRDD.map(lambda x : (x[0],x[1][0]))\n",
    "\n",
    "# Transform predictedRatingsRDD into an RDD with entries that are pairs of the form (Movie ID, Predicted Rating)\n",
    "predictedRDD = predictedRatingsRDD.map(lambda x : (x[1],x[2]))\n",
    "\n",
    "# Use RDD transformations with predictedRDD and movieCountsRDD to yield an RDD with tuples of the form (Movie ID, (Predicted Rating, number of ratings))\n",
    "predictedWithCountsRDD  = (predictedRDD\n",
    "                           .join(movieCountsRDD))\n",
    "\n",
    "# Use RDD transformations with PredictedWithCountsRDD and moviesRDD to yield an RDD with tuples of the form (Predicted Rating, Movie Name, number of ratings), for movies with more than 75 ratings\n",
    "ratingsWithNamesRDD = (predictedWithCountsRDD\n",
    "                       .join(moviesRDD).map(lambda x : (x[1][0][0],x[1][1],x[1][0][1]))).filter(lambda x: x[2]>75)\n",
    "\n",
    "predictedHighestRatedMovies = ratingsWithNamesRDD.takeOrdered(20, key=lambda x: -x[0])\n",
    "print ('My highest rated movies as predicted (for movies with more than 75 reviews):\\n%s' %\n",
    "        '\\n'.join(map(str, predictedHighestRatedMovies)))"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": []
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 2",
   "language": "python",
   "name": "python2"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 2
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython2",
   "version": "2.7.6"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 0
}
