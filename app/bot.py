import discord
import asyncio

class MoviesBot:
    """
        @token String -> the api token for the Discord API
        @movies_provider -> allows searching movies
    """
    def __init__(self, token, movies_provider, subtitles_provider):
        self.__token = token
        self.__movies_provider = movies_provider
        self.__subtitles_provider = subtitles_provider
        self.__client = discord.Client()

        @self.__client.event
        async def on_ready(): await self.handle_ready()

        @self.__client.event
        async def on_message(message): await self.handle_message(message)

    @staticmethod
    def __get_embed_for_query_result(movie, subs, also=[]):
        # Title and Description
        formatted_title = '{} | {}'.format(movie.title, str(movie.year))
        
        description = movie.description + '\n'
        description += "View on [IMDB](https://www.imdb.com/title/{})".format(movie.imdb_id)
        
        embed = discord.Embed(title=formatted_title, description=description)
        
        # Thumbnail
        embed.set_thumbnail(url=movie.thumbnail)

        # Download Links
        for download in movie.downloads:
            download_link = "[Download]({})".format(download['url'])
            embed.add_field(name=download['title'], value=download_link, inline=False)
        
        if subs:
            embed.add_field(name="{} Subtitles".format(subs.language), value="[Download Subs]({})".format(subs.download_url))

        # Footer (Other search options)
        if len(also) > 0:
            other_options = ', '.join(['{} ({})'.format(m.title, m.year) for m in also])
            embed.set_footer(text="Did you mean:\n" + other_options)

        return embed

    async def handle_ready(self):
        # Log
        print('Logged in as')
        print(self.__client.user.name)
        print(self.__client.user.id)
        print('------')

    @staticmethod
    def is_movies_request(message):
        content = message.content
        # Check if keyword matches
        for keyword in ['!movie', '!movies', '!moviebot', '!moviesbot']:
            # If found a match, return True
            if content.startswith(keyword + ' ') and len(content) > len(keyword + ' '):
                return True

        # Return False in case no keyword matched
        return False

    @staticmethod
    def get_query_from_command(message):
        content = message.content
        # Remove first word
        words = content.split(' ')
        return ' '.join(words[1:])
    
    async def discord_response_for_query(self, query):
        movies = await self.__movies_provider.search_movies(query)
        # If no movies were found
        if len(movies) == 0:
            # present message
            return "Sorry, I didn't find anything.", None
        
        selected_movie = movies[0]
        subtitles = await self.__subtitles_provider.search_subtitles(selected_movie)
        # If only found one movie, return it as single result
        if len(movies) == 1:
            # construct message and present it
            embed = self.__get_embed_for_query_result(selected_movie, subs=subtitles)
            return 'Got It!', embed
        # If found multiple movies, return the best one and other as hints
        elif len(movies) > 1:
            alsoFound = movies[1:]
            # construct message and present it
            embed = self.__get_embed_for_query_result(selected_movie, subs=subtitles, also=alsoFound)
            return'Found some, here is the best one', embed

    async def handle_message(self, message):
        if self.is_movies_request(message):
            # Query movies
            query = self.get_query_from_command(message)
            tmp = await self.__client.send_message(message.channel, 'Proccessing...')
            try:
                body, embed = await self.discord_response_for_query(query)
            except:
                print("Error Occured")
                body, embed = "Oops. Something went wrong.", None
            
            await self.__client.edit_message(tmp, body, embed=embed)

    def start(self):
        # start the bot
        self.__client.run(self.__token)