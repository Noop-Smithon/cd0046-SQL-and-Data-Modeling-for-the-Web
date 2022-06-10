#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
from time import strftime
from unicodedata import name
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from markupsafe import escape
from flask_migrate import Migrate
from sqlalchemy import exc, and_
from models import app, db, Venue, Artist, Show
db.init_app(app)
moment = Moment(app)
logger = logging.getLogger(__name__)
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):

  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #  num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  
  data = []
  venue_city_states = Venue.query.with_entities(Venue.city, Venue.state).distinct().all()  
  for city_state in venue_city_states:
    city = city_state[0]
    state = city_state[1]
    venues = Venue.query.filter_by(city=city, state=state).all()

    data.append({
      "city": city,
      "state": state,
      "venues": venues
      })
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # search for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  
  search_term = request.form.get('search_term', '')
  venues = Venue.query.filter(Venue.name.ilike('%' + search_term + '%'))
  data = []
  for venue in venues:
    data.append({
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": len(db.session.query(Show).filter(Show.venue_id == venue.id).filter(Show.start_time > datetime.now()).all())
    })
  count = len(data)
  response = {
    "count": count,
    "data": data
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue = Venue.query.get(venue_id)
  shows = Show.query.filter_by(venue_id=venue_id).all()
  our_current_time = datetime.now()
  past_shows = []
  upcoming_shows = []
  for show in shows:
    data = {
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": format_datetime(str(show.start_time))
    }
    if show.start_time > our_current_time:
      upcoming_shows.append(data)
    else:
      past_shows.append(data)
  data = {
  "id": venue.id,
  "name": venue.name,
  "genres": venue.genres,
  "address": venue.address,
  "city": venue.city,
  "state": venue.state,
  "phone": venue.phone,
  "website_link": venue.website_link,
  "facebook_link": venue.facebook_link,
  "seeking_talent": venue.seeking_talent,
  "seeking_description": venue.seeking_description,
  "image_link": venue.image_link,
  "past_shows": past_shows,
  "upcoming_shows": upcoming_shows,
  "past_shows_count": len(past_shows),
  "upcoming_shows_count": len(upcoming_shows),
}  
    
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  
  venue_name = request.form['name']
  error = False
  form = VenueForm()
  if form.validate():
    try:
      city = request.form['city']
      state = request.form['state']
      phone = request.form['phone']
      genres = request.form.getlist('genres')
      image_link = request.form['image_link']
      facebook_link = request.form['facebook_link']
      website_link = request.form['website_link']
      seeking_talent = request.form['seeking_talent']
      seeking_description = request.form['seeking_description']
      address = request.form['address']

      venue = Venue(
        name = venue_name,
        city = city,
        state = state,
        phone = phone,
        genres = genres,
        image_link = image_link,
        facebook_link = facebook_link,
        website_link = website_link,
        seeking_talent = True if seeking_talent == 'y' else False,
        seeking_description = seeking_description,
        address = address
      )

      db.session.add(venue)
      db.session.commit()
      flash(f"Venue {venue_name} was successfully listed.")

    except Exception:
      db.session.rollback()
      error = True
      logging.exception("Error occurred while saving venue")
    finally:
      db.session.close()

  # on successful db insert, flash success
  else:
    flash(f"An error occurred, {venue_name} could not be listed")
  
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  venue = Venue.query.get_or_404(venue_id)
  form = VenueForm()

  try:
    db.session.delete(venue)
    db.session.commit()
    flash(f"Venue {venue_id} was successfully deleted")

    return render_template('pages/home.html')

  except Exception:
    flash(f"Venue {venue_id} could not be deleted")
    return render_template('pages/venues.html', form=form)

  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = []
  artists = Artist.query.distinct().all()  
  for artist in artists:
    id = artist.id
    name = artist.name

    data.append({
      "id": id,
      "name": name
    })
      
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # search for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term = request.form.get('search_term', '')
  artists = Artist.query.filter(Artist.name.ilike('%' + search_term + '%'))
  data = []
  for artist in artists:
    data.append({
      "id": artist.id,
      "name": artist.name
      # "num_upcoming_shows": len(db.session.query(Show).filter(Show.venue_id == artist.id).filter(Show.start_time > datetime.now()).all())
    })
  count = len(data)
  response = {
    "count": count,
    "data": data
  }

  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  data = Artist.query.get(artist_id)
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)

  form.name.data = artist.name
  form.genres.data = artist.genres
  form.city.data = artist.city
  form.state.data = artist.state
  form.phone.data = artist.phone
  form.website_link.data = artist.website_link
  form.facebook_link.data = artist.facebook_link
  form.seeking_venue.data = artist.seeking_venue
  form.seeking_description.data = artist.seeking_description
  form.image_link.data = artist.image_link
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  artist = Artist.query.get(artist_id)
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  form = ArtistForm()
  artist.name = form.name.data
  artist.genres = form.genres.data
  artist.city = form.city.data
  artist.state = form.state.data
  artist.phone = form.phone.data
  artist.website_link = form.website_link.data
  artist.facebook_link = form.facebook_link.data
  artist.seeking_venue = form.seeking_venue.data
  artist.seeking_description = form.seeking_description.data
  artist.image_link = form.image_link.data

  if form.validate():
    try:
      db.session.commit()
      flash ("Artist form submitted successfully")
    except Exception:
      db.session.rollback()
      flash("Artist form submission not successful")
    finally:
      db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  
  form.name.data = venue.name
  form.genres.data = venue.genres
  form.address.data = venue.address
  form.city.data = venue.city
  form.state.data = venue.state
  form.phone.data = venue.phone
  form.website_link.data = venue.website_link
  form.facebook_link.data = venue.facebook_link
  form.seeking_talent.data = venue.seeking_talent
  form.seeking_description.data = venue.seeking_description
  form.image_link.data = venue.image_link
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)

  venue.name = form.name.data
  venue.genres = form.genres.data
  venue.city = form.city.data
  venue.state = form.state.data
  venue.phone = form.phone.data
  venue.website_link = form.website_link.data
  venue.facebook_link = form.facebook_link.data
  venue.seeking_talent = form.seeking_talent.data
  venue.seeking_description = form.seeking_description.data
  venue.image_link = form.image_link.data

  if form.validate():
    try:
      db.session.commit()
      flash("Venue form submitted successfully")
    except Exception:
      db.session.rollback()
      flash("Venue form not submitted successfully")
    finally:
      db.session.close()
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  artist_name = request.form['name']
  error = False
  form = ArtistForm()
  if form.validate():
    try:
      city = request.form['city']
      state = request.form['state']
      phone = request.form['phone']
      genres = request.form.getlist('genres')
      image_link = request.form['image_link']
      facebook_link = request.form['facebook_link']
      website_link = request.form['website_link']
      seeking_venue = request.form['seeking_venue']
      seeking_description = request.form['seeking_description']

      artist = Artist(
        name = artist_name,
        city = city,
        state = state,
        phone = phone,
        genres = genres,
        image_link = image_link,
        facebook_link = facebook_link,
        website_link = website_link,
        seeking_venue = True if seeking_venue == 'y' else False,
        seeking_description = seeking_description
      )

      db.session.add(artist)
      db.session.commit()
      flash('Artist ' + artist_name  + ' was successfully listed!')
    except Exception:
      db.session.rollback()
      error = True
      logging.exception("Error occurred while saving artist")
    finally:
      db.session.close()
  else:
    flash("Artist form submission was invalid")
  # on successful db insert, flash success
  if error:
    flash('An error occurred. Artist ' +  artist_name + ' could not be listed.')
  
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  data = []
  all_shows = Show.query.all()
  for show in all_shows:
    show_venue = Venue.query.get_or_404(show.venue_id)
    show_artist = Artist.query.get_or_404(show.artist_id)

    data.append({
      "venue_id": show_venue.id,
      "venue_name": show_venue.name,
      "artist_id": show_artist.id,
      "artist_name": show_artist.name,
      "artist_image_link" : show_artist.image_link,
      "start_time" : f'{show.start_time}'
    })
 
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  error = False
  form = ShowForm()
  if form.validate():
    try:
      artist_id = request.form['artist_id']
      venue_id = request.form['venue_id']
      start_time = datetime.now()
    
      show = Show(
        artist_id = show.artist_id,
        venue_id = show.venue_id,
        start_time = show.start_time
      )

      db.session.add(show)
      db.session.commit()
      flash('Show was successfully listed!')

    except Exception:
      db.session.rollback()
      error = True
      logging.exception("Error occurred while saving show")
    finally:
      db.session.close()

  # on successful db insert, flash success or error if unsuccessful
  else:
    flash('An error occurred. Show could not be listed.')
  
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
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
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
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
