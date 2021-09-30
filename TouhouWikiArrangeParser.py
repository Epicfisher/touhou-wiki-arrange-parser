import os, aiohttp, asyncio, socket, urllib, html.parser, json, jsonpickle
import cloudscraper

scraper = cloudscraper.create_scraper()

jsonpickle.set_preferred_backend('json')
#jsonpickle.set_encoder_options('json', ensure_ascii=False)

current_circles = []

debug_waits = True # Waits for User-Input for certain Major Errors
debug_prints = True # Prints Extra Debug Information
debug_gets = True # Prints the Text Output to Console for every Web Request (Outputs a LOT of text)

class Circle(object):
    name = None
    link = None

    albums = None

class Album(object):
    name = None
    link = None

    tracks = None

class Track(object):
    name = None
    original_name = None
    original_name_english = None

    source = None
    source_english = None

class Source:
    source = None
    source_english = None

def write(file, contents):
    open(os.path.dirname(os.path.realpath(__file__)) + '\\' +  file, 'a').write(contents)

def read(file):
    return open(os.path.dirname(os.path.realpath(__file__)) + '\\' +  file, 'r').read()

def read_raw(file):
    return open (os.path.dirname(os.path.realpath(__file__)) + '\\' +  file, 'rb').read()

def mkdir(directory):
    if os.path.exists(os.path.dirname(os.path.realpath(__file__)) + '\\' + directory):
        return
    else:
         os.makedirs(os.path.dirname(os.path.realpath(__file__)) + '\\' + directory)

def exists(location):
    return os.path.exists(os.path.dirname(os.path.realpath(__file__)) + '\\' + location)

async def get_aio_connector():
    conn = aiohttp.TCPConnector(family=socket.AF_INET, verify_ssl=True)
    return conn

async def get(url):
    global scraper

    while True:
        #async with aiohttp.ClientSession(connector=await get_aio_connector()) as session:
            #async with session.get(url) as resp:
                #return await resp.text()
        text = scraper.get(url).text
        if 'Cloudflare' in text:
            print("Killed by Cloudflare Anti-Spam. Waiting 5 Minutes...")
            await asyncio.sleep(300)
            
            del scraper # Free Old Scraper
            scraper = cloudscraper.create_scraper() # Create New Scraper
        else:
            if debug_gets:
                print(text)
            break
    return text

async def populate_circles():
    global current_circles

    song_translations = json.loads((await get("https://en.touhouwiki.net/index.php?title=Touhou_Wiki:SongSource.json&action=raw&ctype=application/json")).replace('　', ' ').replace('？', '?'))
    raw_html = await get('https://en.touhouwiki.net/wiki/List_by_Groups')
    raw_html_page = 1
    combined_circles = False
    change_combined_circles = False
    while True:
        #html = html[html.index('<h2>Contents</h2></div>') + 23:]
        #html = html[html.index('</div>') + 7:]
        #html = html[html.index('</h2>') + 5:]
        while True:
            if change_combined_circles:
                if debug_prints:
                    print("Found Combined Circles Region! No longer accepting double-circle circles.")
                if debug_waits:
                    input()
                combined_circles = True
                change_combined_circles = False
            closing_h3 = raw_html.index('</h3>')
            circle = raw_html[raw_html.index('<h3>') + 4:closing_h3]
            if combined_circles == False:
                raw_html_comparison = raw_html[closing_h3 + 5:]
                if '<h3>' in raw_html_comparison:
                    raw_html_comparison = raw_html_comparison[:raw_html_comparison.index('<h3>')]
                    if 'id="Combined_Circles"' in raw_html_comparison:
                        change_combined_circles = True

            valid_circle = True
            if not circle.count('title="') == 2 or combined_circles == False:
                if 'title="' in circle:
                    circle_link = circle[circle.index('href="') + 12:]
                    circle_link = circle_link[:circle_link.index('"')]
                    circle = circle[circle.index('title="') + 7:]
                    circle = circle[:circle.index('"')]
                else:
                    circle = circle[:circle.rfind('</span>')]
                    if '</a>' in circle:
                        circle = circle[:circle.rfind('</a>')]
                    circle = circle[circle.rfind('>') + 1:]

                    circle_link = circle.replace(' ', '_')
                    if debug_prints:
                        print("Guessing Circle Link From Name!")
                    #circle_link = None
                circle = urllib.parse.unquote(circle)
                circle = html.parser.unescape(circle)
                circle_has_content = False
                current_circle = Circle()
                if debug_prints:
                    print("Circle: '" + circle + "'")
                else:
                    print("Got Circle")
                current_circle.name = circle
                if not circle_link == None:
                    if debug_prints:
                        print("Circle Link: '" + circle_link + "'")
                    current_circle.link = circle_link
            else:
                print('Invalid Double-Circle Circle "' + circle + '"')
                valid_circle = False
                if debug_waits:
                    input()

            if circle == "" or circle == None:
                print("Blank Circle!")
                valid_circle = False
                if debug_waits:
                    input()

            if valid_circle:
                raw_html = raw_html[raw_html.index('</h3>') + 10:]
                albums = raw_html[:raw_html.index('</ul>')]
                current_albums = []
                bad_albums = []
                while len(albums) > 1:
                    album = albums[albums.index('<li>') + 4:albums.index('</li>')]
                    #print(album)
                    #album_name = album[album.index('title="') + 7:]
                    #album_name = album_name[:album_name.index('"')]
                    album_link = album[album.index('a href="') + 8:]
                    if not album_link.startswith("/index.php?"): # Missing/Empty page
                        album_link = album_link[:album_link.index('"')]
                        album_link = album_link[6:]
                        #print("Album Link: " + album_link)

                        album_name = album[:album.rfind('</a>')]
                        album_name = album_name[album_name.index('">') + 2:]
                        album_name = album_name.replace('</span>', '')
                        album_name = album_name.replace('<span lang="ja">', '')
                        
                        if album_name.endswith(')') and '(' in album_name:
                            album_name = album_name[:album_name.index('(')]
                            if album_name.endswith(' '):
                                album_name = album_name[:-1]
                        current_album = Album()
                        #print("Album Name: " + album_name)
                        current_album.name = album_name
                        current_album.link = album_link
                        current_albums.append(current_album)

                    albums = albums[albums.index('</li>') + 5:] # Next Album

                if not circle_link == None:
                    circle_albums = await get('https://en.touhouwiki.net/wiki/' + circle_link)
                    if 'There is currently no text in this page.' in circle_albums:
                        if debug_prints:
                            print("Empty Circle Page!")
                        current_circle.link = None
                    else:
                        if 'id="Discography"' in circle_albums:
                            if debug_prints:
                                print("Searching Circle's Page for Additional Albums...")
                            new_albums = 0
                            circle_albums = circle_albums[circle_albums.index('id="Discography"') + 16:]
                            #circle_albums = circle_albums[:circle_albums.index('</table>')] # Or '</tbody>'
                            try:
                                circle_albums = circle_albums[:circle_albums.index('<!-- \nNewPP limit report')] # Maybe Re-enable This?
                            except:
                                pass
                            if '<a href="' in circle_albums:
                                if '<img' in circle_albums:
                                    images = True
                                else:
                                    images = False

                                circle_albums = circle_albums[circle_albums.index('<a href="'):]
                                circle_albums = circle_albums.replace('\n', '') # Maybe get rid of this
                                while True:
                                    if images:
                                        try:
                                            circle_album = circle_albums[circle_albums.index('<b>') + 3:]
                                        except:
                                            break
                                        circle_album = circle_album[circle_album.index('<a href="') + 9:]
                                        circle_album = circle_album[:circle_album.index('</tr>')]
                                    else:
                                        try:
                                            circle_album = circle_albums[circle_albums.index('<a href="') + 9:]
                                            circle_album = circle_album[:circle_album.index('</dt>')]
                                        except:
                                            break
                                    circle_album_link = circle_album
                                    #circle_album_name = circle_album[circle_album.index('title="') + 7:]
                                    #circle_album_name = circle_album_name[:circle_album_name.index('"')]
                                    if not circle_album_link.startswith('/index.php?'):
                                        circle_album_name = circle_album[:circle_album.index('</a>')]
                                        circle_album_name = circle_album_name[circle_album_name.index('">') + 2:]
                                        circle_album_name = circle_album_name.replace('</span>', '')
                                        circle_album_name = circle_album_name.replace('<span lang="ja">', '')
                                        if circle_album_name.startswith('<span title="'):
                                            circle_album_name = circle_album_name[circle_album_name.index('title="') + 7:]
                                            circle_album_name = circle_album_name[:circle_album_name.index('"')]
                                        current_album = Album()
                                        #print('Album Name: ' + circle_album_name)
                                        current_album.name = circle_album_name
                                        circle_album_link = circle_album[6:circle_album.index('"')]
                                        #print('Album Link: ' + circle_album_link)
                                        current_album.link = circle_album_link
                                        already_exists = False
                                        for current_album_check in current_albums:
                                            if current_album_check.name == current_album.name or current_album_check.link == current_album.link:
                                                already_exists = True
                                                break

                                        if not already_exists:
                                            #print('Album Name: ' + circle_album_name)
                                            #print('Album Link: ' + circle_album_link)
                                            current_albums.append(current_album)
                                            new_albums = new_albums + 1

                                    if images:
                                        circle_albums = circle_albums[circle_albums.index('</tr>') + 5:]
                                    else:
                                        circle_albums = circle_albums[circle_albums.index('</dt>') + 5:]

                                    if circle_albums.startswith('</tbody>') or circle_albums.startswith('</table>') or circle_albums.startswith('<!-- NewPP limit report'): # Maybe change this to just startswith('\n\n')
                                        break

                                print("Retrieved " + str(new_albums) + " new albums from Circle page!")
                                if new_albums == 0:
                                    current_circle.link = None
                            else:
                                if debug_prints:
                                    print("Empty Circle Page!")
                                current_circle.link = None
                        else:
                            if debug_prints:
                                print("Empty Circle Page!")
                            current_circle.link = None

                for current_album in current_albums:
                    album_link = current_album.link
                    #album_link = '%E3%82%86%E3%81%86%E3%81%8B%E3%82%8A%E3%82%93%E3%81%AE%E6%B8%A9%E6%B3%89%E6%97%85%E9%A4%A8'
                    #album_link = '%E6%9C%88%E3%81%AE%E8%BF%BD%E6%86%B6'
                    #album_link = '%E5%B9%BD%E3%80%85%E9%96%91%E3%80%85'
                    #album_link = '%E6%81%90%E6%80%96%E3%81%AE%E5%B9%BB%E6%83%B3%E6%94%B9%E9%9D%A9_genso_salad_surgery'
                    current_tracks = []

                    album_has_content = False
                    album_songs = await get("https://en.touhouwiki.net/wiki/" + album_link)
                    if 'Tracks</span>' in album_songs:
                        album_tracks = album_songs[album_songs.index('Tracks</span>') + 18:]
                        if 'id="Unlisted_Tracks' in album_tracks:
                            album_tracks = album_tracks[:album_tracks.index('id="Unlisted_Tracks')]
                        #print(album_tracks)
                        track_number = 1
                        if debug_prints:
                            print("Getting Album Tracks From " + current_album.name + " From Link: " + album_link)
                            print('==========')
                        else:
                            print("Got Album")

                        while True:
                            track_has_content = False

                            album_tracks_index = album_tracks.index('</li></ul>')
                            album_track_test = album_tracks[album_tracks.index('</li></ul>') + 10:]
                            while album_track_test.startswith('</li></ul>'):
                                album_track_test = album_track_test[10:]
                            if album_track_test.startswith('\n'):
                                album_track_test = album_track_test[1:]
                            if album_track_test.startswith('<p>') or album_track_test.startswith('&amp;') or album_track_test.startswith('</p>'):
                                if 'original_title:' in album_track_test:
                                    #print(album_track_test)
                                    album_tracks_index = album_track_test.index('</li></ul>') + (len(album_track_test) - len(album_tracks))

                            album_track = album_tracks[:album_tracks_index]
                            try:
                                album_track_title = album_track[album_track.index('<b>') + 3:]
                            except:
                                break
                            album_track_title = album_track_title[:album_track_title.index('</b>')]
                            album_track_title = album_track_title.replace('</span>', '')
                            #if '<span ' in album_track_title:
                                #album_track_title = album_track_title[album_track_title.index('>') + 1:]
                            if album_track_title.endswith('</a>'):
                                album_track_title = album_track_title[:- 4]
                                album_track_title = album_track_title[album_track_title.rfind('">') + 2:]
                            album_track_title = album_track_title.replace('<span lang="ja">', '')
                            if not album_track_title == '' and not album_track_title == None and not album_track_title.endswith(')'):
                                #bad_title_tags = ['mix', 'remix' 'instrumental', 'inst', 'vocal', 'version', 'ver.']
                                track_has_content = True

                                current_track = Track()
                                if debug_prints:
                                    print("Album Track Title: " + album_track_title)
                                #else:
                                    #print('Got Track')
                                    #pass
                                current_track.name = album_track_title
                            else:
                                pass
                                #if debug_prints:
                                    #print("Bad Album Track Title: " + album_track_title)
                                #if debug_waits:
                                    #input()

                            if track_has_content:
                                sources = []
                                album_track_for_sources = album_track
                                while 'source:' in album_track_for_sources:
                                    album_track_source = album_track_for_sources[album_track_for_sources.index('source:') + 8:]
                                    album_track_for_sources = album_track_source
                                    album_track_source = album_track_source.replace('</span>', '')
                                    album_track_source = album_track_source.replace('<span lang="ja">', '')
                                    album_track_source = album_track_source.replace('<i>', '').replace('</i>', '')
                                    if album_track_source.lower().startswith('original'):
                                        album_track_source = None
                                        track_has_content = False # For now I'm going to ignore original compositions, and only parse actual arranges
                                        if debug_prints:
                                            print("Album Track Source: Original")
                                    else:
                                        if album_track_source.startswith('<a href="'):
                                            album_track_source = album_track_source[:album_track_source.index('</a>')]
                                            album_track_source_english = album_track_source[album_track_source.index('title="') + 7:]
                                            album_track_source_english = album_track_source_english[:album_track_source_english.index('"')]

                                            album_track_source = album_track_source[album_track_source.rfind('">') + 2:]
                                            while album_track_source.endswith(' ') or album_track_source.endswith('　'):
                                                album_track_source = album_track_source[:-1]

                                            source = Source()
                                            source.source = album_track_source
                                            source.source_english = album_track_source_english

                                            sources.append(source)
                                        else:
                                            if album_track_source == '' or album_track_source.lower() == 'undefined' or album_track_source.lower() == 'touhou':
                                                if debug_prints:
                                                    print("Album Track Source: None")
                                            else:
                                                if debug_prints:
                                                    print("Album Track Source: External (" + album_track_source + ")")
                                                #if debug_waits:
                                                    #input()
                                            album_track_source = None
                                            track_has_content = False
                                else:
                                    if len(sources) < 1:
                                        album_track_source = None
                                        track_has_content = False

                            if track_has_content:
                                album_track_for_sources = album_track
                                attempt = 0
                                while 'original title:' in album_track_for_sources:
                                    album_track_original_title = album_track_for_sources[album_track_for_sources.index('original title:') + 16:]
                                    album_track_for_sources = album_track_original_title
                                    if album_track_original_title.startswith('/li>'):
                                        track_has_content = False
                                        break
                                    #print("original title 2: " + album_track_original_title + "\n")
                                    if not '</li' in album_track_original_title:
                                        break
                                    album_track_original_title = album_track_original_title[:album_track_original_title.index('</li>')]
                                    album_track_original_title = album_track_original_title.replace('</span>', '')
                                    #if '<span' in album_track_original_title:
                                        #album_track_original_title = album_track_original_title[album_track_original_title.index('>') + 1:]
                                    album_track_original_title = album_track_original_title.replace('<span lang="ja">', '')
                                    #album_track_original_title = album_track_original_title.replace(' ～', '　～')
                                    album_track_original_title = album_track_original_title.replace('？', '?')
                                    while album_track_original_title.endswith(' ') or album_track_original_title.endswith('　'):
                                        album_track_original_title = album_track_original_title[:-1]

                                    #for i in range(0 + attempt, len(sources)):
                                    for i in range(0 + attempt, 1):
                                        album_track_source = sources[i].source
                                        album_track_source_english = sources[i].source_english

                                        try:
                                            song_translations[album_track_source.replace('　', ' ')][album_track_original_title.replace('　', ' ')]

                                            if debug_prints:
                                                print("Album Track Original Title: " + album_track_original_title)
                                            current_track.original_name = album_track_original_title

                                            if debug_prints:
                                                print("Album Track Source: " + album_track_source)
                                            current_track.source = album_track_source

                                            if debug_prints:
                                                print("Album Track Source English: " + album_track_source_english)
                                            current_track.source_english = album_track_source_english

                                            break
                                        except:
                                            print("Bad Source: '" + album_track_source + "'")
                                            #if debug_waits:
                                                #input()

                                    if not current_track.original_name == None:
                                        break

                                    attempt = attempt + 1
                                else:
                                    print('Album Track Original Title: Missing')
                                    album_track_original_title = None
                                    track_has_content = False
                                    #if debug_waits:
                                        #input()

                            if track_has_content:
                                try:
                                    album_track_original_title_english = song_translations[album_track_source.replace('　', ' ')][album_track_original_title.replace('　', ' ')]
                                except:
                                    album_track_original_title_english = None

                                if album_track_original_title_english == None:
                                    if debug_prints:
                                        print('Album Track Original Title English: Missing')
                                    track_has_content = False
                                else:
                                    if album_track_original_title_english.startswith('['):
                                        album_track_original_title_english = None
                                        if debug_prints:
                                            print('Album Track Original Title English: Unneccecary')
                                    else:
                                        album_track_original_title_english = album_track_original_title_english[:album_track_original_title_english.rfind('[') - 1]
                                        if debug_prints:
                                            print("Album Track Original Title English: " + album_track_original_title_english)
                                        current_track.original_name_english = album_track_original_title_english

                            if track_has_content:
                                circle_has_content = True
                                album_has_content = True

                                current_tracks.append(current_track)
                            else:
                                if debug_prints:
                                    #print("Discarded Track '" + str(current_track.name) + "'!")
                                    print("Discarded Track '" + str(album_track_title) + "'!")
                                else:
                                    print("Bad Track")
                                #if debug_waits:
                                    #input()

                            track_number = track_number + 1
                            track_number_string = str(track_number)
                            if len(track_number_string) == 1:
                                track_number_string = '0' + track_number_string
                            #album_tracks = album_tracks[album_tracks.index('</ul>') + 5:] # Next Track
                            if debug_prints:
                                print('==========')
                            try:
                                album_tracks = album_tracks[album_tracks.index('<li>' + track_number_string + ". ") + 6 + len(track_number_string):] # Next Track
                            except:
                                break
                            #print(album_tracks)
                            if album_tracks.startswith('</li></ul>\n<p><br />\n</p>'):
                                break

                    #print("Finished Album At Link " + album_link + "")
                    if album_has_content:
                        current_album.tracks = current_tracks
                    else:
                        if debug_prints:
                            print("Discarding Album '" + current_album.name + "'")
                        else:
                            print("Bad Album")
                        bad_albums.append(current_album)
                        #del current_album
                        #if debug_waits:
                            #input()

                if circle_has_content:
                    for bad_album in bad_albums:
                        current_albums.remove(bad_album)
                    current_circle.albums = current_albums
                    current_circles.append(current_circle)
                else:
                    if debug_prints:
                        print("Discarding Circle '" + current_circle.name + "'")
                    else:
                        print("Bad Circle")
                    #if debug_waits:
                        #input()

            raw_html = raw_html[raw_html.index('</ul>') + 5:]
            if debug_prints:
                print("Next Circle!")
            if raw_html[2:].startswith('<!--'):
                break

            #break # Skips to next page after every Circle, for Debug purposes. Remove me.

        #break # Returns after every Page, for Debug purposes. Remove me.

        if debug_prints:
            print("Finished Page " + str(raw_html_page) + "!")
        raw_html_page = raw_html_page + 1
        raw_html = await get('https://en.touhouwiki.net/wiki/List_by_Groups_' + str(raw_html_page))
        if 'There is currently no text in this page.' in raw_html:
            break
        if debug_prints:
            print("Now moving onto Page " + str(raw_html_page) + "!")

    print("Finished in 'current_circles' Array!\nNow saving JSON....")
    json_output = jsonpickle.encode(current_circles, unpicklable=False)
    json_output_pickle = jsonpickle.encode(current_circles, unpicklable=True)
    write('circles.json', json_output)
    write('circles_pickle.json', json_output_pickle)
    #print(json_output)
    #print("Finished!\nNow creating 'Sort by Song' HTML Structure in 'root'...")
    #populate_tree()
    print("Finished!")

async def populate_tree():
    mkdir('root')
    print("Getting Sources List...")
    song_translations = json.loads((await get("https://en.touhouwiki.net/index.php?title=Touhou_Wiki:SongSource.json&action=raw&ctype=application/json")).replace('　', ' ').replace('？', '?'))
    print("Now fetching Sources...")
    ordering_names = []
    ordering_names_english = []
    ordering_numbers = []

    sources = []
    sources_songs = []

    ordering_raw = await get('https://en.touhouwiki.net/wiki/ZUN')
    ordering_raw = ordering_raw[ordering_raw.index('id="Works"') + 10:]
    ordering_raw = ordering_raw[:ordering_raw.index('id="Biography"') + 14:]
    ordering_games = ordering_raw[ordering_raw.index('id="Games"') + 10:]
    ordering_games = ordering_games[ordering_games.index('<li>') + 4:]
    #ordering_games = ordering_games[:ordering_games.index('<h3>')]
    while True:
        valid_game = False

        ordering_game = ordering_games[ordering_games.index('<a href="') + 9:ordering_games.index('</li>')]
        ordering_game_link = ordering_game[:ordering_game.index('"')]
        if not 'http' in ordering_game_link:
            #print(ordering_game_link)
            print("http://en.touhouwiki.net" + ordering_game_link + "/Music")
            game_page = await get("http://en.touhouwiki.net" + ordering_game_link + "/Music")

            song_titles = []
            song_titles_english = []
            #print(game_page)
            if 'id="Music_List">' in game_page:
                valid_game = True

                game_page = game_page[game_page.index('id="Music_List">') + 16:]
                game_page = game_page[:game_page.index('<h2>')]
                while True:
                    #print(game_page)
                    game_page = game_page[game_page.index('<tbody><tr>') + 11:]
                    game_song = game_page[:game_page.index('</tr>')]
                    if '</td>' in game_song:
                        game_song = game_song[game_song.index('</td>') + 5:]
                    else:
                        break
                    game_song = game_song[game_song.index('">') + 2:]
                    game_song_title = game_song[:game_song.index('</td>') - 1]
                    game_song_title = game_song_title.replace('<span lang="en">', '').replace('</span>', '').replace('</a>', '').replace('</sup>', '')
                    if '<font size="' in game_song_title:
                        game_song_title = game_song_title[:game_song_title.index('<font size="')]
                    if '<sup' in game_song_title:
                        game_song_title = game_song_title[:game_song_title.index('<sup')]
                    if '">' in game_song_title:
                        game_song_title = game_song_title[game_song_title.index('">') + 2:]
                    while game_song_title.endswith(' '):
                        game_song_title = game_song_title[:-1]
                    #print(game_song_title)
                    game_song_title_english = game_song[game_song.index('</td>') + 5:]
                    if '">' in game_song_title_english:
                        game_song_title_english = game_song_title_english[game_song_title_english.index('">') + 2:]
                        game_song_title_english = game_song_title_english[:game_song_title_english.index('</td>') - 1]
                        game_song_title_english = game_song_title_english.replace('<i>', '').replace('</i>', '').replace('</a>', '').replace('<span lang="en">', '').replace('</span>', '').replace('</sup>', '')
                        if '<font size="' in game_song_title_english:
                            game_song_title_english = game_song_title_english[:game_song_title_english.index('<font size="')]
                        if '<sup' in game_song_title_english:
                            game_song_title_english = game_song_title_english[:game_song_title_english.index('<sup')]
                        if '">' in game_song_title_english:
                            game_song_title_english = game_song_title_english[game_song_title_english.index('">') + 2:]
                        while game_song_title_english.endswith(' '):
                            game_song_title_english = game_song_title_english[:-1]
                        #print(game_song_title_english)
                        song_titles.append(game_song_title)
                        song_titles_english.append(game_song_title_english)
                        #print("Discovering " + game_song_title + " - " + game_song_title_english)
                    if not '<tbody><tr>' in game_page:
                        break

        if valid_game and len(song_titles) > 0:
            ordering_game_name = ordering_game.replace('</span>', '')
            ordering_game_name = ordering_game_name[:ordering_game_name.rfind('(')]
            #print(ordering_game_name)
            if '</a>' in ordering_game_name:
                ordering_game_name = ordering_game_name[:ordering_game_name.index('</a>')]
            ordering_game_name = ordering_game_name.replace('<span lang="ja">', '')
            ordering_game_name = ordering_game_name[ordering_game_name.rfind('">') + 2:]
            if ordering_game_name.startswith(' '):
                ordering_game_name = ordering_game_name[1:]
            #print(ordering_game_name)
            #try:
                #if not song_translations[ordering_game_name.replace('　', ' ').replace('？', '?')] == None:
                    #pass
            #except:
                #valid_game = False
                #print("Invalid Game '" + ordering_game_name.replace('　', ' ').replace('？', '?') + "'")

            ordering_names.append(ordering_game_name)

            try:
                ordering_game_number = await get('https://en.touhouwiki.net' + ordering_game_link)
            except:
                ordering_game_number = ""

            if 'infobox' in ordering_game_number and not 'There is currently no text in this page.' in ordering_game_number:
                ordering_game_number = ordering_game_number[ordering_game_number.index('infobox') + 7:]
                if '<a href="/wiki/File:' in ordering_game_number:
                    ordering_game_number = ordering_game_number[ordering_game_number.index('<a href="/wiki/File:') + 20:]
                    ordering_game_number = ordering_game_number[:ordering_game_number.index('"')]
                    ordering_game_number = ordering_game_number.lower() # Make it simpler to parse, especially for getting rid of those pesky TH and TOUHOU prefixes for the cover filenames.
                    valid_game_number = False
                    if ordering_game_number.startswith('th'):
                        ordering_game_number = ordering_game_number[2:]
                        valid_game_number = True
                    if ordering_game_number.startswith('touhou'):
                        ordering_game_number = ordering_game_number[6:]
                        valid_game_number = True
                else:
                    valid_game_number = False
            else:
                valid_game_number = False

            if valid_game_number:
                ordering_game_number = ordering_game_number[:-4] # Remove the .jpg file extension
                ordering_game_number = ordering_game_number.replace('_', '.')
                i = 0
                while ordering_game_number[i].isdigit() or ordering_game_number[i] == '.':
                    if i == len(ordering_game_number) - 1:
                        i = i + 1
                        break
                    i = i + 1
                ordering_game_number = ordering_game_number[:i]
                if ordering_game_number.endswith('.'):
                    ordering_game_number = ordering_game_number[:-1]
                if not '.' in ordering_game_number:
                    if len(ordering_game_number) > 2:
                        ordering_game_number = ordering_game_number[:2] + '.' + ordering_game_number[2:]
                    if ordering_game_number.startswith('0'):
                        ordering_game_number = ordering_game_number[1:]
                if ordering_game_number == "":
                    ordering_game_number = None
                else:
                    #print(ordering_game_number)
                    pass
            else:
                ordering_game_number = None
            ordering_numbers.append(ordering_game_number)

            ordering_game_name_english = ordering_game[ordering_game.index('title="') + 7:]
            ordering_game_name_english = ordering_game_name_english[:ordering_game_name_english.index('"')]
            ordering_game_name_english = html.parser.unescape(ordering_game_name_english)
            if ordering_game_name_english.startswith('wikipedia:'):
                ordering_game_name_english = ordering_game_name_english[10:]
            while '(' in ordering_game_name_english:
                ordering_game_name_english = ordering_game_name_english[:ordering_game_name_english.index('(')]
            if ordering_game_name_english.startswith(' '):
                ordering_game_name_english = ordering_game_name_english[1:]
            #print(ordering_game_name_english)
            if ordering_game_number == None:
                print(ordering_game_name + " | " + ordering_game_name_english)
            else:
                print(ordering_game_number + " | " + ordering_game_name + " | " + ordering_game_name_english)
            ordering_names_english.append(ordering_game_name_english)
            #input()

            #print("Writing Work Listing...")
            source = ordering_game_name.replace('?', '？').replace('.', '․').replace('　', ' ').replace('"', "'")
            sources.append(source.lower())
            mkdir('root\\' + source)
            number = ordering_game_number
            if number == None:
                number = ""
            else:
                number = number + ' '

            write('root\\index.html', '<li>' + number + '<a href="' + source.encode('ascii', 'xmlcharrefreplace').decode('ascii') + '/index.html">' + ordering_game_name.encode('ascii', 'xmlcharrefreplace').decode('ascii') + '</a> &bull; <i>' + ordering_game_name_english + '</i></li>\n')
            for i in range(0, len(song_titles)):
                song_source = song_titles[i].replace('?', '？').replace('.', '․').replace('　', ' ').replace('"', "'").replace('  ', ' ').replace('佐渡の二ッ岩', '佐渡のニッ岩').replace('幻想郷の二ッ岩', '幻想郷のニッ岩').replace('空に浮かぶ物体Ｘ', '空に浮かぶ物体X')
                sources_songs.append(song_source.lower())

                write('root\\' + source + "\\index.html", '<li><a href="' + song_source.encode('ascii', 'xmlcharrefreplace').decode('ascii') + '/index.html">' + song_titles[i].encode('ascii', 'xmlcharrefreplace').decode('ascii') + '</a> &bull; <i>' + song_titles_english[i].encode('ascii', 'xmlcharrefreplace').decode('ascii') + '</i></li>\n')
                #print("Writing " + song_titles[i] + " - " + song_titles_english[i])
                print(song_source + " - " + song_titles_english[i])
        if not '<li>' in ordering_games:
            break
        ordering_games = ordering_games[ordering_games.index('<li>') + 4:]

    #print("Writing Games in Order...")
    #for i in range(0, len(ordering_names)):
        #source = ordering_names[i].replace('?', '？').replace('.', '․').replace('　', ' ').replace('"', "'")
        #if not source in sources:
            #mkdir('root\\' + source)
            #number = ordering_numbers[i]
            #if number == None:
                #number = ""
            #else:
                #number = number + ' '
            #write('root\\index.html', '<li>' + number + '<a href="' + source.encode('ascii', 'xmlcharrefreplace').decode('ascii') + '/index.html">' + ordering_names[i].encode('ascii', 'xmlcharrefreplace').decode('ascii') + '</a> ' + ordering_names_english[i] + '</li>\n')
            #sources.append(source)
    print("Now Populating...")
    for circle in current_circles:
        for album in circle.albums:
            print("Album Link: " + album.link)
            for track in album.tracks:
                #source = track.source.replace('\u3000', ' ')
                source = track.source.replace('?', '？').replace('.', '․').replace('　', ' ').replace('"', "'")
                #original_name = track.original_name.replace('\u3000', ' ')
                original_name = track.original_name.replace('?', '？').replace('.', '․').replace('　', ' ').replace('"', "'").replace('  ', ' ').replace('佐渡の二ッ岩', '佐渡のニッ岩').replace('幻想郷の二ッ岩', '幻想郷のニッ岩').replace('空に浮かぶ物体Ｘ', '空に浮かぶ物体X')

                #mkdir('root\\' + source)
                if source.lower() in sources:
                    if original_name.lower() in sources_songs:
                        mkdir('root\\' + source + '\\' + original_name)
                        print('root\\' + source + '\\' + original_name + '\\index.html')
                        write('root\\' + source + '\\' + original_name + '\\index.html', '<li><b>' + circle.name.encode('ascii', 'xmlcharrefreplace').decode('ascii') + '</b> &bull; ' + track.name.encode('ascii', 'xmlcharrefreplace').decode('ascii') + ' &bull; <a href="https://en.touhouwiki.net/wiki/' + album.link + '">' + album.name.encode('ascii', 'xmlcharrefreplace').decode('ascii') + '</a></li>\n')
                    else:
                        input("Bad Song '" + original_name + "' In Source '" + source + "'")
                        input()
                else:
                    print("Bad Source '" + original_name + "' (Song '" + original_name + "')")
                    #input()
                #if not source in sources:
                    ##if track.source_english == None:
                        ##source_english = ""
                    ##else:
                        ##source_english = " &bull; <i>" + track.source_english + '</i>'
                    ##write('root\\index.html', '<li><a href="' + source.encode('ascii', 'xmlcharrefreplace').decode('ascii') + '/index.html">' + track.source.encode('ascii', 'xmlcharrefreplace').decode('ascii') + '</a>' + source_english + '</li>\n')
                    #sources.append(source)
                    #sources_original.append(track.source)
                #if not original_name in original_names:
                    #if track.original_name_english == None:
                        #original_name_english = ""
                    #else:
                        #original_name_english = ' &bull; <i>' + track.original_name_english + '</i>'
                    #write('root\\' + source + '\\index.html', '<li><a href="' + original_name.encode('ascii', 'xmlcharrefreplace').decode('ascii') + '/index.html">' + track.original_name.encode('ascii', 'xmlcharrefreplace').decode('ascii') + '</a> &bull; <i>' + original_name_english + '</i></li>\n')
                    #original_names.append(original_name)
                #input()
                #print(track.name)
    #populate_listing()
    #print("Now Writing Ordered Games Index...")
    #for i in range(0, len(ordering_names)):
        #source = ordering_names[i].replace('?', '？').replace('.', '․').replace('　', ' ').replace('"', "'")
        #if source in sources:
            #mkdir('root\\' + source)
            #number = ordering_numbers[i]
            #if number == None:
                #number = ""
            #else:
                #number = number + ' '
            #write('root\\index.html', '<li>' + number + '<a href="' + source.encode('ascii', 'xmlcharrefreplace').decode('ascii') + '/index.html">' + ordering_names[i].encode('ascii', 'xmlcharrefreplace').decode('ascii') + '</a> ' + ordering_names_english[i] + '</li>\n')
    print("Finished!")

#def populate_listing():
    #print("Finished Creating Arrange Lists!\nNow Creating Generic HTML Directory Listings...")
    #for base_directory in os.listdir(os.path.dirname(os.path.realpath(__file__)) + '\\root'):
        #if not base_directory.endswith('.html'):
            #write('root\\index.html', '<li><a href="' + base_directory.encode('ascii', 'xmlcharrefreplace').decode('ascii') + '/index.html">' + base_directory.encode('ascii', 'xmlcharrefreplace').decode('ascii') + '</a></li>')
            #for directory in os.listdir(os.path.dirname(os.path.realpath(__file__)) + '\\root\\' + base_directory):
                #if not directory.endswith('.html'):
                    #write('root\\' + base_directory + '\\index.html', '<li><a href="' + directory.encode('ascii', 'xmlcharrefreplace').decode('ascii') + '/index.html">' + directory.encode('ascii', 'xmlcharrefreplace').decode('ascii') + '</a> &bull; ' + song_translations[base_directory.replace('　', ' ').replace('․', '.')][directory.replace('　', ' ').replace('․', '.')] + '</li>')
    #print("Finished!")

async def start():
    global current_circles

    if os.path.exists(os.path.dirname(os.path.realpath(__file__)) + '\\circles_pickle.json'):
        print("Using existing Circles JSON File!")
        current_circles = read('circles_pickle.json')
        #.decode('unicode-escape')
        #i = 16324
        current_circles = jsonpickle.decode(current_circles)
        print("Populating 'Sort by Song' HTML Structure in 'root' in 5 seconds...")
        await asyncio.sleep(5)
        print("Now creating 'Sort by Song' HTML Structure in 'root'...")
        await populate_tree()
    else:
        await populate_circles()

loop = asyncio.get_event_loop()
loop.run_until_complete(start())  
loop.close()
