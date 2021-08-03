#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
from typing import ValuesView
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from flask_migrate import Migrate
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.functions import array_agg
from sqlalchemy.sql.sqltypes import ARRAY
from forms import *
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from models import *
from sqlalchemy import desc
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
db = db_setup(app)

#----------------------------------------------------------------------------#
# helper function.
#----------------------------------------------------------------------------#

# return the number of upcoming shows 
def upcoming_shows_count(value):
    
# check if the value is Venue or Artist object
    if isinstance(value, Venue):
        return len(db.session.query(Show).join(Venue).filter(Show.Venue_id == value.id).filter(Show.start_date > datetime.now()).all())
    else:
        return len(db.session.query(Show).join(Artist).filter(Show.Artist_id == value.id).filter(Show.start_date > datetime.now()).all())

# return the number of past shows 
def past_shows_count(value):
    
# check if the value is Venue or Artist object
    if isinstance(value, Venue):
        return len(db.session.query(Show).join(Venue).filter(Show.Venue_id == value.id).filter(Show.start_date < datetime.now()).all())
    else:
        return len(db.session.query(Show).join(Artist).filter(Show.Artist_id == value.id).filter(Show.start_date < datetime.now()).all())

# return the upcoming shows 
def upcoming_shows_func(value):
    if isinstance(value, Venue):
        return db.session.query(Show).join(Venue).filter(Show.Venue_id == value.id).filter(Show.start_date > datetime.now()).all()
    else:
        return db.session.query(Show).join(Artist).filter(Show.Artist_id == value.id).filter(Show.start_date > datetime.now()).all()

# return the past shows 
def past_shows_func(value):
    if isinstance(value, Venue):
        return db.session.query(Show).join(Venue).filter(Show.Venue_id == value.id).filter(Show.start_date < datetime.now()).all()
    else:
        return db.session.query(Show).join(Artist).filter(Show.Artist_id == value.id).filter(Show.start_date < datetime.now()).all()

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

# home page
@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

# returning venues page
@app.route('/venues')
def venues():
    # group venues by city and state 
    venues_states = Venue.query.with_entities(func.count(
        Venue.id), Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
    data = []
    # loop for each venue area and add it in data array
    for area in venues_states:
        venue_area = Venue.query.filter_by(
            state=area.state).filter_by(city=area.city).all()
        venues_data = []
        # loop for each venue in one area and add it in venues_data array
        for venue in venue_area:
            venues_data.append({
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": upcoming_shows_count(venue)
            })

        data.append({
            "city": area.city,
            "state": area.state,
            "venues": venues_data
        })

    return render_template('pages/venues.html', areas=data)


# search for venue by name 
@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get('search_term', '')
    # search for venue name that like a given term
    search = Venue.query.filter(
        Venue.name.ilike('%' + search_term + '%')).all()
    data = []
    for venue in search:
        data.append({
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": upcoming_shows_count(venue),
        })
        # the number of venues that like the search term and the venues objects itself
    response = {
        "count": len(data),
        "data": data
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

    # open venue details with a given id 
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    
    # shows the venue page with the given venue_id
    
    venue = Venue.query.get(venue_id)
    # if venue by venue.id is not available open error page
    if not venue:
        return render_template("errors/404.html")
    past_show = []
    upcoming_shows = []
    for show in past_shows_func(venue):
        past_show.append(
            {
                "artist_id": show.Artist_id,
                "artist_name": show.Artist.name,
                "artist_image_link": show.Artist.image_link,
                "start_time": show.start_date.strftime("%m/%d/%Y, %H:%M:%S")
            })
    for show in upcoming_shows_func(venue):
        upcoming_shows.append(
            {
                "artist_id": show.Artist_id,
                "artist_name": show.Artist.name,
                "artist_image_link": show.Artist.image_link,
                "start_time": show.start_date.strftime("%m/%d/%Y, %H:%M:%S")
            })

    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.looking_for_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": past_show,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": past_shows_count(venue),
        "upcoming_shows_count": upcoming_shows_count(venue),
    }
    return render_template('pages/show_venue.html', venue=data)


#  Create new Venue 
#  ----------------------------------------------------------------

# form page to create new Venue
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)

# redirect to home page for venue creation
@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    
    # try to add new venue object to the database
    try:
        venue = Venue(
            name=request.form.get('name'),
            genres=request.form.getlist('genres'),
            address=request.form.get('address'),
            city=request.form.get('city'),
            state=request.form.get('state'),
            phone=request.form.get('phone'),
            website=request.form.get('website'),
            facebook_link=request.form.get('facebook_link'),
            looking_for_talent=bool(request.form.get('looking_for_talent')),
            seeking_description=request.form.get('seeking_description'),
            image_link=request.form.get('image_link'),
        )

        db.session.add(venue)
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
        # if we got this far, it means that the venue was successfully added!''
        
        # if we had an error adding the venue to the database then roollback the request
    except SQLAlchemyError as e:
        db.session.rollback()
        flash('An error occurred. Venue ' +
              request.form['name'] + ' could not be listed.')
    finally:
        db.session.close()

    return render_template('pages/home.html')


# delete the venue from the database by its id 
@app.route('/venues/<venue_id>/delete', methods=['GET', 'POST'])
def delete_venue(venue_id):
    
    # try to delete venue object with the id passed from the database
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
        
    # if we had an error deleteing the venue from the database then roollback the request
    except SQLAlchemyError as e:
        db.session.rollback()
    finally:
        db.session.close()
    return redirect(url_for('index'))




#  Artists
#  ----------------------------------------------------------------

# open artists page for viewing
@app.route('/artists')
def artists():
    # retrieve artists objects from the database order by artist id 
    artists = Artist.query.order_by(Artist.id).all()
    data = []
    
 # loop for each artist in artists objects and add data array
    for artist in artists:
        data.append({
            "id": artist.id,
            "name": artist.name,
        }
        )
    return render_template('pages/artists.html', artists=data)

# search for artist by name 
@app.route('/artists/search', methods=['POST'])
def search_artists():
    
    search_term = request.form.get('search_term', '')
    
 # search for artist name that like a given term
    artists_search = Artist.query.filter(
        Artist.name.ilike('%' + search_term + '%')).all()
    
    data = []
    for artist in artists_search:
        data.append({
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_shows": upcoming_shows_count(artist),
        })
        
   # the number of artist.name that like the search term and the artists objects 
    response = {
        "count": len(data),
        "data": data
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


 # open artist details with a given id 
@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    
    artist = Artist.query.get(artist_id)
    
  # if artist by artist.id is not available open error page
    if not artist:
        return render_template('errors/404.html')

    past_show = []
    upcoming_shows = []
    for show in past_shows_func(artist):
        past_show.append(
            {
                "venue_id": show.Venue_id,
                "venue_name": show.Venue.name,
                "venue_image_link": show.Venue.image_link,
                "start_time": show.start_date.strftime("%m/%d/%Y, %H:%M:%S")
            })
    for show in upcoming_shows_func(artist):
        upcoming_shows.append(
            {
                "venue_id": show.Venue_id,
                "venue_name": show.Venue.name,
                "venue_image_link": show.Venue.image_link,
                "start_time": show.start_date.strftime("%m/%d/%Y, %H:%M:%S")
            })
    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.looking_for_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": past_show,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": past_shows_count(artist),
        "upcoming_shows_count": upcoming_shows_count(artist),
    }
    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------

# edit artists details form with a given id
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.get(artist_id)
    form = ArtistForm(obj=artist)
    return render_template('forms/edit_artist.html', form=form, artist=artist)

# edit artist details with a given id
@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    
# try updateing the artist data of the givin id 
    try:
        artist = Artist.query.get(artist_id)
        setattr(artist, 'name', request.form.get('name'))
        setattr(artist, 'genres', request.form.getlist('genres'))
        setattr(artist, 'address', request.form.get('address'))
        setattr(artist, 'city', request.form.get('city'))
        setattr(artist, 'state', request.form.get('state'))
        setattr(artist, 'phone', request.form.get('phone'))
        setattr(artist, 'website', request.form.get('website'))
        setattr(artist, 'facebook_link', request.form.get('facebook_link'))
        setattr(artist, 'looking_for_venue', bool(
            request.form.get('looking_for_venue')))
        setattr(artist, 'seeking_description',
                request.form.get('seeking_description'))
        setattr(artist, 'image_link', request.form.get('image_link'))
        db.session.commit()
        flash('artist ' + request.form['name'] + ' was successfully edited!')

# throw error if something goes wrong and rollback
    except SQLAlchemyError as e:
        db.session.rollback()
        flash('An error occurred. Artist ' +
              request.form['name'] + ' could not be edited.')

    finally:
        db.session.close()

    return redirect(url_for('show_artist', artist_id=artist_id))


# get edit Venue details form with a given id and populate it with the Venue data
@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    venue = Venue.query.get(venue_id)
    form = VenueForm(obj=venue)
    return render_template('forms/edit_venue.html', form=form, venue=venue)


# edit venue details with a given id
@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

# try updateing the venue data of the givin id 
    try:
        venue = Venue.query.get(venue_id)
        setattr(venue, 'name', request.form.get('name'))
        setattr(venue, 'genres', request.form.getlist('genres'))
        setattr(venue, 'address', request.form.get('address'))
        setattr(venue, 'city', request.form.get('city'))
        setattr(venue, 'state', request.form.get('state'))
        setattr(venue, 'phone', request.form.get('phone'))
        setattr(venue, 'website', request.form.get('website'))
        setattr(venue, 'facebook_link', request.form.get('facebook_link'))
        setattr(venue, 'looking_for_talent', bool(
            request.form.get('looking_for_talent')))
        setattr(venue, 'seeking_description',
                request.form.get('seeking_description'))
        setattr(venue, 'image_link', request.form.get('image_link'))
        db.session.commit()
        flash('venue ' + request.form['name'] + ' was successfully edited!')

# throw error if something goes wrong and rollback
    except SQLAlchemyError as e:
        db.session.rollback()
        flash('An error occurred. venue ' +
              request.form['name'] + ' could not be edited.')

    finally:
        db.session.close()

    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

# get Artist form page to create artist
@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)

# create new artist and add it to the database 
@app.route('/artists/create', methods=['POST'])
def create_artist_submission():

# try to create a new artist and add it to the database 
    try:
        artist = Artist(
            name=request.form.get('name'),
            genres=request.form.getlist('genres'),
            city=request.form.get('city'),
            state=request.form.get('state'),
            phone=request.form.get('phone'),
            website=request.form.get('website'),
            facebook_link=request.form.get('facebook_link'),
            looking_for_venue=bool(request.form.get('looking_for_venue')),
            seeking_description=request.form.get('seeking_description'),
            image_link=request.form.get('image_link'),
        )
        db.session.add(artist)
        db.session.commit()
        flash('artist ' + request.form['name'] +
              ' was successfully listed!')
        
    # throw an error if we couldn't add artist  and roollback'
    except SQLAlchemyError as e:
        db.session.rollback()
        flash('An error occurred. artist ' +
              request.form['name'] + ' could not be listed.')
    finally:
        db.session.close()
    return render_template('pages/home.html')


# delete artist  with a given id
@app.route('/artists/<int:artist_id>/delete', methods=['GET', 'POST'])
def delete_artist(artist_id):

    try:
        artist = Artist.query.get(artist_id)
        db.session.delete(artist)
        db.session.commit()
    except SQLAlchemyError as e:
        flash('An error occurred. artist ' )
        db.session.rollback()
    finally:
        db.session.close()
    return redirect(url_for('index'))


#  Shows
#  ----------------------------------------------------------------

# open shows page and populate it with shows object from the database
@app.route('/shows')
def shows():
    
    # retrieve all shows from the database order by date 
    Shows = Show.query.order_by(desc(Show.start_date)).all()
    
    data = []
    # check if there no shows redirect to home page 
    if not Shows:
        flash(' there are no shows available')
        return redirect(url_for('index'))
    
    # loop through all shows and append them to data array 
    for show in Shows:
        data.append(
            {
                "venue_id": show.Venue_id,
                "venue_name": show.Venue.name,
                "artist_id": show.Artist_id,
                "artist_name": show.Artist.name,
                "artist_image_link": show.Artist.image_link,
                "start_time": show.start_date.strftime("%m/%d/%Y, %H:%M:%S")
            })

    return render_template('pages/shows.html', shows=data)

# get the show form data to create a new show
@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)

# create a new show and add it to the database
@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    try:
        show = Show(
            Venue_id=request.form.get('venue_id'),
            Artist_id=request.form.get('artist_id'),
            start_date=request.form.get('start_time'),
        )
        db.session.add(show)
        db.session.commit()
        flash('Show was successfully listed!')

    except SQLAlchemyError as e:
        db.session.rollback()
        flash('An error occurred. Show ' +
              request.form['start_time'] + ' could not be listed.')
    finally:
        db.session.close()

    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
